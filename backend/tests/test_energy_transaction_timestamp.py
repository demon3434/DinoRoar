import os
import sys
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 确保 backend 路径在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import models, schemas
from app.database import Base
from app.services.energy_service import EnergyEngineService
from app.services.system_init import seed_energy_and_checkin_defaults
from app.services.log_service import sync_logs_service
from app.services.energy_repair import repair_inverted_log_reward_timestamps


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # 初始化恐龙配置与能量元数据
    seed_energy_and_checkin_defaults(db)
    dino = models.DinoConfig(
        id=1,
        legacy_key="triceratops",
        name="快乐三角龙",
        mood_label="快乐",
        image_url="/static/images/dinosaurs/triceratops.png",
        is_active=True
    )
    db.add(dino)
    
    # 创建测试用户
    user = models.User(
        id=1,
        username="test_user",
        hashed_password="fake",
        egg_energy=1201
    )
    db.add(user)
    db.commit()

    yield db
    db.close()


def test_log_reward_timestamp_uses_server_time_not_incident_date(test_db):
    """
    验证日记奖励流水的时间戳严格使用服务端实时物理时间，而不是日记的历史 incident_date
    """
    user = test_db.query(models.User).filter(models.User.id == 1).first()
    
    # 构造一篇历史日期（例如 3 天前）的日记
    past_incident_date = datetime.datetime.now() - datetime.timedelta(days=3)
    log_data = schemas.LogCreate(
        uuid="log_test_uuid_001",
        title="过去的日记",
        incident_date=past_incident_date,
        mood_dino_id=1,
        content="这是一篇补记的日记",
        own_thoughts="",
        updated_at=datetime.datetime.now()
    )

    before_time = datetime.datetime.now() - datetime.timedelta(seconds=1)
    sync_logs_service(test_db, user, schemas.LogSyncPayload(logs=[log_data]))
    after_time = datetime.datetime.now() + datetime.timedelta(seconds=1)

    # 查询生成的日记记录与流水
    log = test_db.query(models.Log).filter(models.Log.uuid == "log_test_uuid_001").first()
    assert log is not None
    assert log.incident_date == past_incident_date

    tx = test_db.query(models.EggEnergyTransaction).filter(
        models.EggEnergyTransaction.target_type_id == 3,
        models.EggEnergyTransaction.target_id == log.id
    ).first()

    assert tx is not None
    assert tx.change_amount == 10
    assert tx.balance_after == 1211
    # 核心断言：交易时间戳必须是当前实时物理时间，绝不能是 3 天前的 incident_date
    assert before_time <= tx.created_at <= after_time
    assert (tx.created_at - past_incident_date).total_seconds() > 86400 * 2


def test_media_bonus_and_base_reward_order_consistency(test_db):
    """
    验证日记基础奖励与附件加成奖励的时间戳和自增ID单调递增，倒序查询时加成排在上方，结余自洽
    """
    user = test_db.query(models.User).filter(models.User.id == 1).first()

    # 1. 客户端同步日记（基础奖励 +10）
    log_data = schemas.LogCreate(
        uuid="log_test_uuid_002",
        title="带图日记",
        incident_date=datetime.datetime.now(),
        mood_dino_id=1,
        content="今天拍了美美的照片",
        own_thoughts="",
        updated_at=datetime.datetime.now()
    )
    sync_logs_service(test_db, user, schemas.LogSyncPayload(logs=[log_data]))
    log = test_db.query(models.Log).filter(models.Log.uuid == "log_test_uuid_002").first()

    # 2. 客户端随后上传附件（补发加成奖励 +20）
    EnergyEngineService.apply_transaction(
        db=test_db,
        user_id=user.id,
        event_type_id=201,
        change_amount=20,
        target_type_id=3,
        target_id=log.id,
        request_uuid=f"log_media_reward_{log.uuid}",
        commit=True
    )

    # 3. 校验两笔流水
    txs = test_db.query(models.EggEnergyTransaction).filter(
        models.EggEnergyTransaction.user_id == user.id,
        models.EggEnergyTransaction.target_id == log.id
    ).order_by(models.EggEnergyTransaction.created_at.desc(), models.EggEnergyTransaction.id.desc()).all()

    assert len(txs) == 2
    # 倒序第一条应为加成奖励 (+20)，结余为 1231
    assert txs[0].request_uuid.startswith("log_media_reward_")
    assert txs[0].change_amount == 20
    assert txs[0].balance_after == 1231

    # 倒序第二条应为基础奖励 (+10)，结余为 1211
    assert txs[1].request_uuid.startswith("log_reward_")
    assert txs[1].change_amount == 10
    assert txs[1].balance_after == 1211

    # 时钟和ID单调性
    assert txs[0].created_at >= txs[1].created_at
    assert txs[0].id > txs[1].id


def test_repair_inverted_log_reward_timestamps(test_db):
    """
    验证历史存量时序倒挂（基础奖励时间晚于加成奖励）的自愈修复逻辑
    """
    user = test_db.query(models.User).filter(models.User.id == 1).first()

    log = models.Log(
        id=99,
        user_id=user.id,
        uuid="log_inverted_test",
        title="倒挂日记测试",
        incident_date=datetime.datetime(2026, 10, 8, 20, 28, 54),
        mood_dino_id=1,
        content="内容",
        media_rewarded=True
    )
    test_db.add(log)
    test_db.flush()

    # 模拟真实线上倒挂数据：加成奖励时间为 20:28:52，基础奖励时间为 20:28:54
    tx_base = models.EggEnergyTransaction(
        id=101,
        user_id=user.id,
        event_type_id=201,
        change_amount=10,
        balance_after=1211,
        target_type_id=3,
        target_id=log.id,
        request_uuid=f"log_reward_{log.uuid}",
        created_at=datetime.datetime(2026, 10, 8, 20, 28, 54)
    )
    tx_media = models.EggEnergyTransaction(
        id=102,
        user_id=user.id,
        event_type_id=201,
        change_amount=20,
        balance_after=1231,
        target_type_id=3,
        target_id=log.id,
        request_uuid=f"log_media_reward_{log.uuid}",
        created_at=datetime.datetime(2026, 10, 8, 20, 28, 52)  # 比 base 还要早 2 秒
    )
    test_db.add(tx_base)
    test_db.add(tx_media)
    test_db.commit()

    # 执行自愈修复
    res = repair_inverted_log_reward_timestamps(test_db)
    assert res["fixed_count"] == 1

    # 刷新查询
    test_db.refresh(tx_media)
    test_db.refresh(tx_base)

    # 修复后：加成奖励的时间戳必须大于基础奖励
    assert tx_media.created_at > tx_base.created_at
    assert tx_media.created_at == tx_base.created_at + datetime.timedelta(seconds=2)

    # 验证倒序查询顺序恢复正常
    ordered_txs = test_db.query(models.EggEnergyTransaction).filter(
        models.EggEnergyTransaction.target_id == log.id
    ).order_by(models.EggEnergyTransaction.created_at.desc(), models.EggEnergyTransaction.id.desc()).all()

    # 第一行加成奖励 (+20, 结余 1231)
    assert ordered_txs[0].id == tx_media.id
    assert ordered_txs[0].balance_after == 1231
    # 第二行基础奖励 (+10, 结余 1211)
    assert ordered_txs[1].id == tx_base.id
    assert ordered_txs[1].balance_after == 1211
