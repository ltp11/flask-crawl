FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制代码和依赖
COPY app.py /app/
COPY requirements.txt /app/

# 安装依赖（推荐国内pip镜像，加速）
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir -r requirements.txt

# Playwright依赖浏览器，用官方命令安装
RUN python -m playwright install --with-deps

# 暴露端口
EXPOSE 8000

# 启动Flask
CMD ["python", "app.py"]