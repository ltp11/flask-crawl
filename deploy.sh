#!/bin/bash

# 项目配置
PROJECT_DIR="/home/ops/flask-crawl"      # 项目目录，根据你实际填写
GIT_REPO="https://github.com/ltp11/flask-crawl.git"  # 仓库地址
IMAGE_NAME="flask-crawl4ai-app"
CONTAINER_NAME="flask-crawl4ai-app"
EXPOSE_PORT=8000

# 1. 拉取最新代码
if [ ! -d "$PROJECT_DIR" ]; then
    echo "项目目录不存在，开始clone仓库"
    git clone $GIT_REPO $PROJECT_DIR || { echo "git clone 失败"; exit 1; }
else
    echo "项目目录已存在，进入后拉取最新代码"
    cd $PROJECT_DIR || exit 1
    git pull || { echo "git pull 失败"; exit 1; }
fi

cd $PROJECT_DIR

# 2. 构建镜像
echo "正在构建Docker镜像..."
docker build -t $IMAGE_NAME . || { echo "构建失败"; exit 1; }

# 3. 停止并删除旧容器（如果存在）
if docker ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "停止旧容器..."
    docker stop $CONTAINER_NAME
    echo "删除旧容器..."
    docker rm $CONTAINER_NAME
fi

# 4. 启动新容器
echo "启动新容器..."
docker run -d --name $CONTAINER_NAME -p $EXPOSE_PORT:8000 $IMAGE_NAME

echo "部署完成！"