# 视频上传API文档

## 概述

这个API提供了视频文件上传和元数据提取功能，使用FFmpeg自动分析视频文件并将信息保存到数据库中。

## 功能特性

- ✅ 视频文件上传
- ✅ 自动提取视频元数据（分辨率、时长、比特率、帧率等）
- ✅ 自动提取音频元数据（格式、通道数、采样率等）
- ✅ 数据库存储
- ✅ RESTful API接口
- ✅ 完整的错误处理

## API端点

### 1. 上传视频文件

**POST** `/api/v1/videos/upload`

上传视频文件并自动提取元数据保存到数据库。

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| video_file | File | ✅ | 视频文件 |
| item_id | String | ✅ | 商品ID |
| sku_id | String | ❌ | SKU ID，如果不提供则使用item_id |
| platform | String | ❌ | 平台，默认为"web" |
| author_id | String | ❌ | 作者ID |
| owner_id | String | ❌ | 所有者ID |
| source | String | ❌ | 来源，默认为"upload" |

#### 响应示例

```json
{
  "success": true,
  "message": "视频上传并处理成功",
  "video_id": 1,
  "video_info": {
    "id": 1,
    "file_id": "test_video.mp4",
    "url": "/uploads/videos/test_video.mp4",
    "item_id": "test_item_123",
    "sku_id": "test_sku_456",
    "width": 1920,
    "height": 1080,
    "duration": 30000,
    "format": "h264",
    "bitrate": 2000000,
    "frame_rate": 30,
    "audio_format": "aac",
    "audio_bitrate": 128000,
    "audio_channels": 2,
    "platform": "web",
    "source": "upload"
  }
}
```

#### cURL示例

```bash
curl -X POST "http://localhost:8000/api/v1/videos/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "video_file=@test_video.mp4" \
  -F "item_id=test_item_123" \
  -F "sku_id=test_sku_456" \
  -F "platform=web"
```

### 2. 获取视频信息

**GET** `/api/v1/videos/{video_id}`

根据视频ID获取详细的视频信息。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "id": 1,
    "file_id": "test_video.mp4",
    "url": "/uploads/videos/test_video.mp4",
    "item_id": "test_item_123",
    "sku_id": "test_sku_456",
    "width": 1920,
    "height": 1080,
    "duration": 30000,
    "format": "h264",
    "bitrate": 2000000,
    "frame_rate": 30,
    "colour_primaries": "BT.709",
    "matrix_coefficients": "BT.709",
    "transfer_characteristics": "BT.709",
    "rotation": 0,
    "audio_bitrate": 128000,
    "audio_channels": 2,
    "audio_duration": 30000,
    "audio_format": "aac",
    "audio_sampling_rate": 44100,
    "cover_file_id": "",
    "cover_url": "",
    "cover_width": 1920,
    "cover_height": 1080,
    "platform": "web",
    "source": "upload",
    "create_time": "2024-01-01T12:00:00",
    "update_time": "2024-01-01T12:00:00"
  }
}
```

### 3. 获取商品视频列表

**GET** `/api/v1/videos/item/{item_id}`

根据商品ID获取该商品的所有视频列表。

#### 响应示例

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "file_id": "test_video.mp4",
      "url": "/uploads/videos/test_video.mp4",
      "sku_id": "test_sku_456",
      "width": 1920,
      "height": 1080,
      "duration": 30000,
      "format": "h264",
      "bitrate": 2000000,
      "frame_rate": 30,
      "platform": "web",
      "source": "upload",
      "create_time": "2024-01-01T12:00:00"
    }
  ],
  "count": 1
}
```

## 启动服务

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动FastAPI服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问API文档

启动后可以访问以下地址查看自动生成的API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

### 使用测试脚本

```bash
python test_video_api.py
```

注意：运行测试前需要准备一个测试视频文件 `test_video.mp4`。

### 使用Postman或其他工具

1. 设置请求类型为 POST
2. URL: `http://localhost:8000/api/v1/videos/upload`
3. 在Body中选择form-data
4. 添加文件字段 `video_file` 并选择视频文件
5. 添加其他必要的文本字段

## 支持的视频格式

API支持所有FFmpeg能够处理的视频格式，包括但不限于：

- MP4 (H.264, H.265)
- AVI
- MOV
- WMV
- FLV
- WebM
- MKV

## 提取的元数据字段

### 视频信息
- 宽度和高度
- 时长（毫秒）
- 格式/编码器
- 比特率
- 帧率
- 色彩空间信息
- 旋转角度

### 音频信息
- 格式/编码器
- 比特率
- 通道数
- 采样率
- 时长

## 错误处理

API提供完整的错误处理，常见错误码：

- `400`: 请求参数错误（如文件不是视频格式）
- `404`: 资源不存在
- `500`: 服务器内部错误（如FFmpeg处理失败）

## 注意事项

1. 上传的文件必须是视频格式
2. 大文件上传可能需要较长时间处理
3. 确保系统已安装FFmpeg
4. 临时文件会在处理完成后自动清理
5. 实际项目中建议将文件上传到云存储服务

## 数据库模型

视频信息存储在 `video` 表中，包含以下主要字段：

```sql
CREATE TABLE video (
    id INT PRIMARY KEY AUTO_INCREMENT,
    file_id VARCHAR(255),
    url VARCHAR(255),
    item_id VARCHAR(255),
    sku_id VARCHAR(255),
    width INT,
    height INT,
    duration INT,
    format VARCHAR(50),
    bitrate INT,
    frame_rate INT,
    -- ... 更多字段
    create_time DATETIME,
    update_time DATETIME
);
``` 