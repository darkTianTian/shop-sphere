# 阿里云OSS集成说明

## 概述

本项目已集成阿里云OSS（Object Storage Service）用于视频文件存储。当配置了OSS时，上传的视频文件将自动存储到阿里云OSS，否则将降级到本地存储。

## 配置步骤

### 1. 获取阿里云OSS访问凭证

1. 登录阿里云控制台
2. 创建或选择一个OSS Bucket
3. 创建RAM用户并获取AccessKey ID和AccessKey Secret
4. 为RAM用户授予OSS相关权限

### 2. 配置环境变量

在你的环境中设置以下环境变量：

```bash
# 阿里云访问凭证
export ALIBABA_CLOUD_ACCESS_KEY_ID="your_access_key_id"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your_access_key_secret"

# OSS配置
export OSS_ENDPOINT="https://oss-cn-hangzhou.aliyuncs.com"  # 根据你的区域调整
export OSS_BUCKET_NAME="your_bucket_name"
```

### 3. Docker环境配置

在 `deploy/docker` 目录下创建 `.env` 文件：

```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name
```

### 4. 重新构建和启动容器

```bash
cd deploy/docker
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml build
docker-compose -f docker-compose.local.yml up -d
```

## 功能特性

### 自动上传到OSS

- 上传的视频文件会自动存储到阿里云OSS
- 生成唯一的文件名，格式：`videos/{YYYYMMDD}_{8位UUID}.{扩展名}`
- 返回OSS的公网访问URL

### 降级机制

- 如果OSS配置不完整或服务不可用，自动降级到本地存储
- 确保服务的可用性

### 文件管理

- 支持的视频格式：`.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.mkv`, `.m4v`
- 最大文件大小：500MB（可在配置中调整）
- 自动检查文件格式和大小

### 数据库字段

新增了以下字段到 `video_material` 表：

- `oss_object_key`: OSS对象键名
- `file_size`: 文件大小（字节）

## API响应变化

上传成功后，API响应中会包含以下新字段：

```json
{
  "success": true,
  "message": "视频素材上传并处理成功",
  "video_material_id": 123,
  "video_material_info": {
    "id": 123,
    "name": "example.mp4",
    "url": "https://your-bucket.oss-cn-hangzhou.aliyuncs.com/videos/20250617_abc12345.mp4",
    "oss_object_key": "videos/20250617_abc12345.mp4",
    "file_size": 10485760,
    "is_oss_stored": true,
    // ... 其他字段
  }
}
```

## 配置选项

在 `app/config/oss_config.py` 中可以调整以下配置：

- `VIDEO_PREFIX`: 视频文件在OSS中的前缀路径（默认：`videos/`）
- `MAX_FILE_SIZE`: 最大文件大小（默认：500MB）
- `ALLOWED_VIDEO_EXTENSIONS`: 允许的视频格式

## 故障排除

### 1. OSS上传失败

检查以下项目：
- AccessKey ID和Secret是否正确
- Bucket名称是否正确
- Endpoint是否正确（注意区域）
- RAM用户是否有OSS权限
- 网络连接是否正常

### 2. 查看日志

```bash
# 查看应用日志
docker-compose -f docker-compose.local.yml logs web

# 查看错误日志
tail -f logs/supervisor/fastapi-error.log
```

### 3. 测试OSS连接

可以在容器中执行以下命令测试OSS连接：

```python
from app.services.oss_service import OSSService
oss = OSSService()
print(f"OSS可用: {oss.is_available()}")
```

## 安全建议

1. **不要在代码中硬编码AccessKey**
2. **使用环境变量或密钥管理服务**
3. **定期轮换AccessKey**
4. **为RAM用户设置最小权限**
5. **考虑使用STS临时凭证**

## 成本优化

1. **设置生命周期规则**：自动删除或转储旧文件
2. **使用合适的存储类型**：标准、低频访问、归档等
3. **开启CDN加速**：提高访问速度，降低OSS流量费用 