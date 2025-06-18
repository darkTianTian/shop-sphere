#!/bin/bash

echo "🔍 Nginx 诊断脚本"
echo "=================="

# 检查容器状态
echo "📋 检查容器状态..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🔍 检查 Nginx 容器日志（最近50行）..."
docker-compose -f docker-compose.prod.yml logs --tail=50 nginx

echo ""
echo "🔍 检查 Web 容器日志（最近50行）..."
docker-compose -f docker-compose.prod.yml logs --tail=50 web

echo ""
echo "🔍 检查 Nginx 配置语法..."
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

echo ""
echo "🔍 检查端口占用情况..."
netstat -tulpn | grep -E ':(80|443|8000)\s'

echo ""
echo "🔍 检查 Docker 网络..."
docker network ls
docker network inspect $(docker-compose -f docker-compose.prod.yml config --services | head -1 | xargs -I {} docker inspect {}_{}_1 --format '{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}' 2>/dev/null || echo "shopsphere-network")

echo ""
echo "🔍 尝试内部连接测试..."
docker-compose -f docker-compose.prod.yml exec nginx wget -qO- --timeout=5 http://web:8000/health 2>&1 || echo "❌ 无法连接到 web:8000"

echo ""
echo "🔍 检查 Nginx 进程..."
docker-compose -f docker-compose.prod.yml exec nginx ps aux | grep nginx

echo ""
echo "🔍 检查系统资源..."
echo "内存使用："
free -h
echo "磁盘使用："
df -h
echo "CPU 负载："
uptime

echo ""
echo "✅ 诊断完成！"
echo ""
echo "🛠️  常见解决方案："
echo "1. 重启服务：docker-compose -f docker-compose.prod.yml restart"
echo "2. 重新构建：docker-compose -f docker-compose.prod.yml up -d --force-recreate"
echo "3. 检查防火墙：sudo ufw status"
echo "4. 检查 SELinux：sestatus" 