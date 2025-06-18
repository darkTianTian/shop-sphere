#!/bin/bash

echo "🔍 测试Podman环境下docker-compose的兼容性..."

# 检查Podman是否可用
if ! command -v podman &> /dev/null; then
    echo "❌ Podman未安装"
    exit 1
fi

echo "✅ Podman版本: $(podman --version)"

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装"
    exit 1
fi

echo "✅ docker-compose版本: $(docker-compose --version)"

# 启动Podman socket服务
echo "🔌 启动Podman socket服务..."
sudo systemctl enable --now podman.socket || {
    echo "⚠️ 系统级socket启动失败，尝试用户级socket..."
    systemctl --user enable --now podman.socket || {
        echo "❌ 无法启动Podman socket服务"
        exit 1
    }
}

sleep 3

# 检查socket文件
echo "🔍 检查socket文件..."
if sudo test -S /run/podman/podman.sock; then
    echo "✅ 系统级socket文件存在: /run/podman/podman.sock"
    SOCKET_PATH="/run/podman/podman.sock"
elif test -S "/run/user/$(id -u)/podman/podman.sock"; then
    echo "✅ 用户级socket文件存在: /run/user/$(id -u)/podman/podman.sock"
    SOCKET_PATH="/run/user/$(id -u)/podman/podman.sock"
else
    echo "❌ 找不到Podman socket文件"
    exit 1
fi

# 测试通过DOCKER_HOST连接
echo "🧪 测试通过DOCKER_HOST环境变量连接..."
export DOCKER_HOST="unix://$SOCKET_PATH"
if docker-compose version; then
    echo "✅ docker-compose可以通过DOCKER_HOST连接Podman"
    DOCKER_HOST_WORKS=true
else
    echo "⚠️ docker-compose无法通过DOCKER_HOST连接"
    DOCKER_HOST_WORKS=false
fi

# 测试通过socket链接连接
echo "🧪 测试通过socket链接连接..."
unset DOCKER_HOST
sudo mkdir -p /var/run
sudo ln -sf "$SOCKET_PATH" /var/run/docker.sock || true

if docker-compose version; then
    echo "✅ docker-compose可以通过socket链接连接Podman"
    SOCKET_LINK_WORKS=true
else
    echo "⚠️ docker-compose无法通过socket链接连接"
    SOCKET_LINK_WORKS=false
fi

# 总结
echo ""
echo "📊 测试结果总结:"
echo "- Podman socket路径: $SOCKET_PATH"
echo "- DOCKER_HOST方式: $([ "$DOCKER_HOST_WORKS" = true ] && echo "✅ 可用" || echo "❌ 不可用")"
echo "- Socket链接方式: $([ "$SOCKET_LINK_WORKS" = true ] && echo "✅ 可用" || echo "❌ 不可用")"

if [ "$DOCKER_HOST_WORKS" = true ] || [ "$SOCKET_LINK_WORKS" = true ]; then
    echo ""
    echo "🎉 至少有一种方式可用，部署应该能够成功！"
    
    # 推荐的配置
    if [ "$DOCKER_HOST_WORKS" = true ]; then
        echo "💡 推荐使用DOCKER_HOST方式: export DOCKER_HOST=\"unix://$SOCKET_PATH\""
    else
        echo "💡 推荐使用socket链接方式（已配置）"
    fi
    exit 0
else
    echo ""
    echo "❌ 两种方式都不可用，需要进一步调试"
    exit 1
fi 