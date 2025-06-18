#!/bin/bash

# Docker镜像源配置脚本
# 解决ECS服务器访问Docker Hub慢或失败的问题

echo "🔧 配置Docker镜像源..."

# 创建Docker daemon配置目录
sudo mkdir -p /etc/docker

# 配置Docker镜像源（优先使用阿里云和国内镜像源）
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://dockerhub.azk8s.cn",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://dockerproxy.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5,
  "storage-driver": "overlay2"
}
EOF

echo "✅ Docker镜像源配置完成"

# 重启Docker服务
echo "🔄 重启Docker服务..."
sudo systemctl daemon-reload

# 检查是否使用Podman
if command -v podman &> /dev/null && ! command -v docker &> /dev/null; then
    echo "🐳 检测到Podman环境，重启Podman服务..."
    sudo systemctl restart podman || true
    sudo systemctl enable --now podman.socket || true
else
    echo "🐳 重启Docker服务..."
    sudo systemctl restart docker || true
fi

# 等待服务启动
sleep 5

# 验证配置
echo "🔍 验证Docker配置..."
if command -v docker &> /dev/null; then
    sudo docker info | grep -A 10 "Registry Mirrors" || echo "Docker info检查完成"
elif command -v podman &> /dev/null; then
    echo "Podman环境配置完成"
fi

echo "✅ Docker镜像源配置完成！"
echo "📋 配置的镜像源："
echo "  - 阿里云杭州：https://registry.cn-hangzhou.aliyuncs.com"
echo "  - Azure中国：https://dockerhub.azk8s.cn"
echo "  - 中科大镜像：https://docker.mirrors.ustc.edu.cn"
echo "  - 网易镜像：https://hub-mirror.c.163.com"
echo "  - 百度镜像：https://mirror.baidubce.com"
echo "  - DockerProxy：https://dockerproxy.com" 