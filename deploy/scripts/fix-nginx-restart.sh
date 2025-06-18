#!/bin/bash

echo "🛠️  修复 Nginx 重启问题"
echo "======================="

# 进入项目目录
cd /opt/shop-sphere || exit 1

echo "1️⃣ 停止所有服务..."
docker-compose -f docker-compose.prod.yml down

echo "2️⃣ 清理旧容器和网络..."
docker system prune -f
docker network prune -f

echo "3️⃣ 检查端口占用..."
if netstat -tulpn | grep -q ':80\s'; then
    echo "⚠️  端口 80 被占用，尝试释放..."
    sudo fuser -k 80/tcp 2>/dev/null || true
fi

if netstat -tulpn | grep -q ':8000\s'; then
    echo "⚠️  端口 8000 被占用，尝试释放..."
    sudo fuser -k 8000/tcp 2>/dev/null || true
fi

echo "4️⃣ 创建必要的目录..."
mkdir -p logs/nginx logs/supervisor uploads
chmod -R 755 logs uploads

echo "5️⃣ 检查配置文件..."
if [ ! -f nginx/nginx.conf ]; then
    echo "❌ nginx.conf 文件不存在！"
    exit 1
fi

echo "6️⃣ 重新启动服务（分步启动）..."
echo "   启动 web 服务..."
docker-compose -f docker-compose.prod.yml up -d web

echo "   等待 web 服务启动..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T web curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Web 服务启动成功"
        break
    fi
    echo "   等待中... ($i/30)"
    sleep 2
done

echo "   启动 nginx 服务..."
docker-compose -f docker-compose.prod.yml up -d nginx

echo "7️⃣ 等待服务稳定..."
sleep 10

echo "8️⃣ 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

echo "9️⃣ 测试连接..."
echo "测试 nginx 健康检查..."
curl -I http://localhost/nginx-health 2>/dev/null || echo "❌ Nginx 健康检查失败"

echo "测试应用健康检查..."
curl -I http://localhost/health 2>/dev/null || echo "❌ 应用健康检查失败"

echo "🔟 显示最新日志..."
echo "Nginx 日志："
docker-compose -f docker-compose.prod.yml logs --tail=10 nginx

echo ""
echo "Web 日志："
docker-compose -f docker-compose.prod.yml logs --tail=10 web

echo ""
echo "✅ 修复脚本执行完成！"
echo ""
echo "📋 接下来的检查："
echo "1. 检查服务状态：docker-compose -f docker-compose.prod.yml ps"
echo "2. 查看实时日志：docker-compose -f docker-compose.prod.yml logs -f"
echo "3. 测试访问：curl http://localhost/docs" 