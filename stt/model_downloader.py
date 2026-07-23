import os
import sys
import urllib.request
import tarfile
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ModelDownloader")

MODEL_URLS = [
    "https://ghfast.top/https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2",
    "https://ghproxy.net/https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2",
    "https://ghproxy.cc/https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2",
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
]
MODELS_DIR = os.environ.get("MODELS_DIR", "/app/models")  # Mapped path inside Docker
ARCHIVE_NAME = "sensevoice.tar.bz2"
TARGET_DIR_NAME = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"

def download_progress(block_num, block_size, total_size):
    """
    Hook to display download progress in logs.
    """
    if total_size > 0:
        percent = (block_num * block_size * 100) / total_size
        if block_num % 1000 == 0:  # Log every ~8MB to avoid spamming the log files
            logger.info(f"Downloading: {percent:.1f}% ({block_num * block_size / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB)")

def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    target_path = os.path.join(MODELS_DIR, TARGET_DIR_NAME)
    archive_path = os.path.join(MODELS_DIR, ARCHIVE_NAME)

    # Check if target model files exist
    if os.path.exists(os.path.join(target_path, "model.onnx")) and os.path.exists(os.path.join(target_path, "tokens.txt")):
        logger.info(f"SenseVoice model already exists at: {target_path}. Skipping download.")
        return

    download_success = False
    for idx, url in enumerate(MODEL_URLS, 1):
        logger.info(f"Trying download mirror [{idx}/{len(MODEL_URLS)}]: {url}")
        try:
            # Custom Request with User-Agent header to bypass basic blocking
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=30) as response, open(archive_path, 'wb') as out_file:
                total_size = int(response.info().get('Content-Length', 0))
                block_size = 8192
                block_num = 0
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    out_file.write(buffer)
                    block_num += 1
                    download_progress(block_num, block_size, total_size)
            
            logger.info("Download completed. Extracting model archive...")
            with tarfile.open(archive_path, "r:bz2") as tar:
                tar.extractall(path=MODELS_DIR)
            
            logger.info(f"Extraction complete! Model files placed in: {target_path}")
            download_success = True
            break
        except Exception as e:
            logger.warning(f"Mirror [{idx}] failed: {e}. Trying next mirror...")
            if os.path.exists(archive_path):
                try:
                    os.remove(archive_path)
                except Exception:
                    pass

    if not download_success:
        logger.error("All download mirrors failed. Model download was unsuccessful.")
        sys.exit(1)
    else:
        if os.path.exists(archive_path):
            try:
                os.remove(archive_path)
            except Exception:
                pass
            logger.info("Cleaned up download archive file.")

if __name__ == "__main__":
    main()
