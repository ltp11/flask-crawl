#!/bin/bash

PROJECT_DIR="/home/ops/flask-crawl"
GIT_REPO="https://github.com/ltp11/flask-crawl.git"
IMAGE_NAME="flask-crawl4ai-app"
CONTAINER_NAME="flask-crawl4ai-app"
EXPOSE_PORT=8000

echo "=== 开始部署 ==="

if [ ! -d "$PROJECT_DIR" ]; then
    echo "项目目录不存在，开始clone仓库"
    git clone $GIT_REPO $PROJECT_DIR || { echo "git clone 失败"; exit 1; }
fi

cd $PROJECT_DIR || { echo "进入项目目录失败"; exit 1; }

echo "拉取最新代码..."
git pull || { echo "git pull 失败"; exit 1; }

echo "正在构建Docker镜像..."
docker build -t $IMAGE_NAME . || { echo "构建失败"; exit 1; }

# 强制删除所有占用8000端口的容器
PORT_CONTAINERS=$(docker ps -a --filter "publish=$EXPOSE_PORT" --format "{{.ID}}")
if [ -n "$PORT_CONTAINERS" ]; then
    echo "删除占用$EXPOSE_PORT端口的容器: $PORT_CONTAINERS"
    docker rm -f $PORT_CONTAINERS || true
fi

# 强制删除所有和 CONTAINER_NAME 同名的容器
NAME_CONTAINERS=$(docker ps -a --filter "name=^/${CONTAINER_NAME}$" --format "{{.ID}}")
if [ -n "$NAME_CONTAINERS" ]; then
    echo "删除同名容器 $CONTAINER_NAME: $NAME_CONTAINERS"
    docker rm -f $NAME_CONTAINERS || true
fi

echo "启动新容器..."
docker run -d --name $CONTAINER_NAME -p $EXPOSE_PORT:8000 $IMAGE_NAME || { echo "容器启动失败"; exit 1; }

echo "=== 部署完成！==="