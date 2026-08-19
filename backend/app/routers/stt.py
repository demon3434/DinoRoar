import logging
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ..config import settings


logger = logging.getLogger("STTProxy")
router = APIRouter(prefix="/api/stt", tags=["STT"])

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    代理客户端的音频文件并透传至 SenseVoice STT 引擎进行转译。
    支持 WAV、MP3、AAC、M4A 等常见音频格式。
    """
    target_url = settings.stt_api_url or "http://stt:18000/api/transcribe"
    logger.info(f"转发 STT 音频转译请求至: {target_url}")
    
    try:
        content = await file.read()
        files = {
            "file": (file.filename or "audio.m4a", content, file.content_type or "audio/m4a")
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(target_url, files=files)
            except httpx.RequestError:
                # 容器外宿主机 IP 或端口阻断时，降级直连 Docker 内网域名 stt:18000
                fallback_url = "http://stt:18000/api/transcribe"
                if target_url != fallback_url:
                    logger.warning(f"主 STT 地址 ({target_url}) 连接失败，降级尝试 Docker 内网地址 ({fallback_url})")
                    response = await client.post(fallback_url, files=files)
                else:
                    raise
            
        if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="语音识别 AI 模型尚在后台下载或加载中（全新部署约需 1~2 分钟），请稍候重试"
            )
        elif response.status_code != status.HTTP_200_OK:
            logger.error(f"STT 远程引擎异常 [{response.status_code}]: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"STT 转译引擎响应异常: {response.text}"
            )
            
        return response.json()
    except httpx.RequestError as exc:
        logger.error(f"无法连接到 STT 引擎 ({target_url}): {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"网络连接失败，无法连接至 STT 引擎，请检查 STT 容器及 18000 端口状态"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"STT 代理透传过程发生未知错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STT 服务处理失败: {str(e)}"
        )
