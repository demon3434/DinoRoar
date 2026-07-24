FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.11-slim



WORKDIR /app

# Use Aliyun mirror for Debian packages
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list || true
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources; fi


# Install system dependencies: ffmpeg is required to decode various audio formats to 16kHz Mono WAV
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

COPY . .

EXPOSE 18000

# Download the model first on container start, then run the app
CMD python model_downloader.py && uvicorn main:app --host 0.0.0.0 --port 18000

