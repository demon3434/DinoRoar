# DinoRoar 高性能 SQLite 数据库架构与查询优化指南

> **适用场景**：本文档针对基于 **SQLite + Python (SQLAlchemy / FastAPI) 或 Android (Room)** 的端云一体化应用。旨在为未来 5~10 年数据规模（数万至数十万条日记、数百万条能量流水、富文本与音频附件）提供**响应速度 < 5ms、存储 I/O 极低、高并发写不互斥、生产迁移零损毁**的数据库架构与查询设计范本。

---

## 目录

- [一、 为什么选择 SQLite 以及面临的核心挑战](#一-为什么选择-sqlite-以及面临的核心挑战)
- [二、 运行时参数调优 (PRAGMA Stack)](#二-运行时参数调优-pragma-stack)
- [三、 高频事实流水账本设计 (Energy Ledger)](#三-高频事实流水账本设计-energy-ledger)
- [四、 大文本大字段与溢出页 I/O 隔离 (Column Pruning)](#四-大文本大字段与溢出页-io-隔离-column-pruning)
- [五、 日期时间检索与 B-Tree 索引规范](#五-日期时间检索与-b-tree-索引规范)
- [六、 统计分析与首页聚合加速 (Daily Summary 预聚合模式)](#六-统计分析与首页聚合加速-daily-summary-预聚合模式)
- [七、 生产环境数据零损毁平滑升级与回滚范式](#七-生产环境数据零损毁平滑升级与回滚范式)

---

## 一、 为什么选择 SQLite 以及面临的核心挑战

SQLite 是一款极轻量、单文件、零运维成本的嵌入式关系型数据库，非常适合作为中小型应用、家庭服务器和私有云的核心存储。然而，在默认配置下，随着系统运行多年、数据量不断增长，开发者极易踩入以下四大性能与稳定性陷阱：

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SQLite 默认陷阱与优化方案                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. 锁争用冲突 : 默认 Rollback Journal 写阻塞读 ──▶ 开启 WAL + 5000ms 超时│
│ 2. 深度翻页慢 : 传统 OFFSET 导致线性性能劣化 ──▶ 基于自增主键的游标分页  │
│ 3. 磁盘 I/O 暴增 : 大文本正文触发溢出页读取 ────▶ 列表查询 ORM 排除大字段 │
│ 4. 索引彻底失效 : LIKE '%YYYY-MM%' 模糊匹配 ───▶ 前闭后开区间范围比对   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 二、 运行时参数调优 (PRAGMA Stack)

SQLite 的默认参数偏向极端保守的安全级别，严重制约了并发读写与磁盘吞吐。在应用初始化连接时，必须执行以下核心运行时配置：

```python
# FastAPI / SQLAlchemy 连接时标准配置范式
@event.listens_for(engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # 1. 强制 UTF-8 编码，杜绝跨语言/多端字符集乱码
    cursor.execute("PRAGMA encoding = 'UTF-8';")
    
    # 2. 开启 WAL (Write-Ahead Logging) 模式
    # 原理：读操作从主 db 和 wal 读取快照，写操作追加写入 wal 文件，实现读写互不互斥
    cursor.execute("PRAGMA journal_mode = WAL;")
    
    # 3. 设置 synchronous = NORMAL
    # 原理：在 WAL 模式下，NORMAL 能够完全保证断电不损坏数据库文件，且写事务耗时降低 2~3 倍
    cursor.execute("PRAGMA synchronous = NORMAL;")
    
    # 4. 关键：设置 busy_timeout = 5000 (毫秒)
    # 原理：当多线程并发写入冲突时，SQLite 不会立刻抛出 "database is locked"，而是在 5 秒内自动轮询重试
    cursor.execute("PRAGMA busy_timeout = 5000;")
    
    # 5. 开启外键级联检查 (SQLite 默认关闭外键约束)
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.close()
```

同时，在 `create_engine` 时配置：
```python
connect_args = {
    "check_same_thread": False,
    "timeout": 15  # 驱动级超时熔断保护
}
```

---

## 三、 高频事实流水账本设计 (Energy Ledger)

在积分、代币、蛋能量等高频变动业务中，流水记录表是膨胀最快的数据集。

### 1. 拒绝实时 SUM 计算当前余额
- **反模式**：每次获取用户当前余额时执行 `SELECT SUM(change_amount) FROM transactions WHERE user_id = ?`。随着流水积累至 10 万条，单次获取余额需遍历全部流水行，耗时呈线性膨胀。
- **优秀实践**：
  1. 在 `users` 主表保留物理快照字段 `egg_energy`；
  2. 在同一个原子事务内执行：
     ```python
     # 1. 插入流水事实
     tx = EggEnergyTransaction(user_id=uid, change_amount=delta, balance_after=new_bal, ...)
     db.add(tx)
     # 2. 更新用户快照
     user.egg_energy = new_bal
     db.add(user)
     db.commit()
     ```
  3. 查询余额直接读取 `user.egg_energy`，时间复杂度保持绝对的 $O(1)$。

### 2. 拒绝在应用内存中对全量流水做循环统计
- **反模式**：
  ```python
  # ❌ 危险操作：把用户历史 10 万条流水全部加载到 Python 内存中计算收支
  all_txs = db.query(EggEnergyTransaction).filter_by(user_id=uid).all()
  for t in all_txs: ...
  ```
- **优秀实践**：下沉到 SQLite 原生单次条件聚合，耗时 < 1ms 且内存占用为 0：
  ```python
  stats = db.query(
      func.coalesce(func.sum(case((and_(tx.created_at >= month_start, tx.change_amount > 0), tx.change_amount), else_=0)), 0).label("month_income"),
      func.coalesce(func.sum(case((and_(tx.created_at >= month_start, tx.change_amount < 0), func.abs(tx.change_amount)), else_=0)), 0).label("month_expense")
  ).filter(tx.user_id == uid).first()
  ```

### 3. 基于自增主键的覆盖索引与游标分页
- **覆盖索引**：
  ```sql
  CREATE INDEX idx_energy_tx_user_id_desc ON egg_energy_transactions (user_id, id DESC);
  ```
- **游标分页（Cursor-based Pagination）**：
  深度翻页（如翻到第 500 页）使用 `OFFSET 10000` 会迫使 SQLite 扫描并丢弃前 10000 条索引记录。改用基于上一页锚点主键 `id` 的游标比对：
  ```sql
  SELECT id, change_amount, balance_after, created_at
  FROM egg_energy_transactions
  WHERE user_id = :userId AND (:lastId IS NULL OR id < :lastId)
  ORDER BY id DESC
  LIMIT :pageSize;
  ```

---

## 四、 大文本大字段与溢出页 I/O 隔离 (Column Pruning)

### 1. 什么是 SQLite 溢出页（Overflow Pages）？
SQLite 以 B-Tree 页（默认大小为 4KB）为最小物理存储单元。当单行数据包含长篇富文本、语音转文字（STT）或大字段时，单页容纳不下整行，SQLite 会将多出的文本拆分存储到连续的**溢出页（Overflow Pages）**。

```
B-Tree 数据页 (4KB)
┌─────────────────────────────────┐
│ id | user_id | incident_date    │
│ content_ptr ───▶ 溢出页 1 (4KB) ───▶ 溢出页 2 (4KB)
└─────────────────────────────────┘
```

如果在列表页、日历打点或搜索摘要中直接 `SELECT *`，SQLite 会为了拼装用不到的大文本字段，去磁盘上按链表顺序读取所有溢出页，导致翻页产生大量无意义的物理 I/O 与内存反序列化。

### 2. ORM 列裁剪解决方案
在列表接口中显式延迟加载大字段（`defer`）：
```python
# 日记列表接口：排除 content 与 own_thoughts 大字段
items = db_query.order_by(desc(Log.incident_date))\
    .offset(offset).limit(limit)\
    .options(
        defer(Log.content),
        defer(Log.own_thoughts),
        selectinload(Log.attachments)
    ).all()
```
单篇详情接口（`/api/logs/detail/{uuid}`）再完整加载全文。实测列表查询吞吐提升 5~10 倍。

---

## 五、 日期时间检索与 B-Tree 索引规范

### 1. 禁用 LIKE 模糊前缀匹配
- **反模式**：
  ```python
  # ❌ 导致 incident_date 上的任何 B-tree 索引彻底失效，引发逐行全表扫描
  query.filter(Log.incident_date.like(f"%{month}%"))
  ```
- **优秀实践**：
  使用严格的**前闭后开（Closed-Open Interval）**区间比对：
  ```python
  # 检索 2026 年 10 月：[2026-10-01 00:00:00, 2026-11-01 00:00:00)
  start_dt = datetime.datetime(2026, 10, 1)
  next_month_dt = datetime.datetime(2026, 11, 1)
  
  query.filter(
      Log.incident_date >= start_dt,
      Log.incident_date < next_month_dt
  )
  ```
配合联合索引 `Index("idx_logs_user_incident_date", "user_id", "is_deleted", "incident_date DESC")`，查询时间始终在 1~2 毫秒内完成。

---

## 六、 统计分析与首页聚合加速 (Daily Summary 预聚合模式)

### 1. 核心矛盾
移动端与 Web 端首页通常包含“总坚持天数”、“本周获得能量”、“近30天心情热力图”等统计挂件。若每次唤醒首页都在数万条日记与附件之间执行关联与聚合，主线程会遭遇严重的等待。

### 2. 设计规范：按日事实预聚合表
建立极简的 `daily_summary` 聚合表：
```sql
CREATE TABLE IF NOT EXISTS daily_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date_str VARCHAR(10) NOT NULL,       -- "2026-10-23"
    diary_count INTEGER NOT NULL DEFAULT 0,
    energy_gained INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date_str)
);
CREATE INDEX idx_daily_summary_user_date ON daily_summary (user_id, date_str);
```
- **写入时**：用户每天保存日记或签到时，在同一事务内更新当日的那 1 行；
- **读取时**：一年仅 365 行，十年仅 3650 行。查询“总记日记天数”只需 `COUNT(*)`，查询近 30 天热力图仅读 30 行，实现真正的极速毫秒级输出。

---

## 七、 生产环境数据零损毁平滑升级与回滚范式

在对存量实机服务器升级时，面对孩子或用户珍贵的历史心血数据，**零容错、零损毁**是第一准则。必须遵循以下自动化防护时序：

```
[执行升级]
   │
   ▼
1. 暂停后端容器 (docker compose stop app) ──▶ 确保 WAL checkpoint 落盘，杜绝写入冲突
   │
   ▼
2. 双重冷热备份 ──▶ A. 全目录 tar.gz 冷备包；B. 独立快照 .db 物理副本
   │
   ▼
3. 前置完整性与数据行数校验 ──▶ PRAGMA integrity_check + 记录 users, logs, transactions 初始行数
   │
   ▼
4. 开启显式事务 (BEGIN TRANSACTION)
   ├── 仅执行加法 DDL (CREATE INDEX IF NOT EXISTS, CREATE TABLE IF NOT EXISTS)
   └── 执行历史数据 Backfill 回填 (从 logs 聚合并填充 daily_summary)
   │
   ▼
5. 后置严密校验 ──▶ 再次执行 integrity_check，比对核心表行数 100% 对齐
   ├── 校验一致 ──▶ COMMIT 事务 ──▶ docker compose up -d 启动新容器 ──▶ [升级成功]
   └── 发现异常 ──▶ 自动触发 ROLLBACK ──▶ 还原备份文件 ──▶ 恢复原系统 ──▶ [无损中止]
```

配套自动化运维脚本位于仓库：[`scripts/migrate_194_db.py`](file:///e:/code/DinoRoar/scripts/migrate_194_db.py)。

---

## 总结：高性能 SQLite 架构设计心法

1. **配置先行**：WAL 模式 + synchronous=NORMAL + busy_timeout=5000 是高并发写防锁死基石。
2. **读写分离**：热点余额读快照字段，明细写流水事实表，拒绝实时 SUM。
3. **裁剪大字段**：善用 ORM 的 `defer`，杜绝列表翻页读取磁盘溢出页。
4. **范围代替模糊**：用闭开区间比对取代 `LIKE`，让 B-Tree 索引始终全速工作。
5. **小表胜大表**：使用按日事实预聚合表收敛历史统计计算。
6. **敬畏数据**：每一次生产升级必须具备多重快照、行数对齐校验与秒级原子回滚能力。
