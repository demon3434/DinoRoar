FROM python:3.11-slim



WORKDIR /workspace

# Use Aliyun mirror for Debian packages
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list || true
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources; fi


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
