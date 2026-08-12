FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.11-slim



WORKDIR /workspace

# 替换 Debian 软件源为阿里云镜像（DEB822 格式，Trusted: yes 跳过 GPG 校验）
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    printf 'Types: deb\nURIs: http://mirrors.aliyun.com/debian\nSuites: bookworm bookworm-updates\nComponents: main\nTrusted: yes\n\nTypes: deb\nURIs: http://mirrors.aliyun.com/debian-security\nSuites: bookworm-security\nComponents: main\nTrusted: yes\n' > /etc/apt/sources.list.d/debian.sources


# Install system dependencies if any library needs compiling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
