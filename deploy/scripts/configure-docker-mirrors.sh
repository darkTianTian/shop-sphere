#!/bin/bash

# Docker镜像源配置脚本
# 解决ECS服务器访问Docker Hub慢或失败的问题

echo "🔧 配置Docker镜像源..."

# 创建Docker daemon配置目录
sudo mkdir -p /etc/docker

# 配置Docker镜像源
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
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
  }
}
EOF

echo "✅ Docker镜像源配置完成"

# 重启Docker服务
echo "🔄 重启Docker服务..."
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置
echo "🔍 验证Docker配置..."
sudo docker info | grep -A 10 "Registry Mirrors"

echo "✅ Docker镜像源配置完成！"
echo "📋 配置的镜像源："
echo "  - 中科大镜像：https://docker.mirrors.ustc.edu.cn"
echo "  - 网易镜像：https://hub-mirror.c.163.com"
echo "  - 百度镜像：https://mirror.baidubce.com"
echo "  - DockerProxy：https://dockerproxy.com" 