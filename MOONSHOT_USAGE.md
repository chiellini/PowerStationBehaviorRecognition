# Moonshot API 视频分析使用说明

## 重要说明

Kimi 的视频分析功能**只在 Moonshot 官方 API 支持**，OpenRouter 不支持此功能。

## 获取 API 密钥

1. 访问 [Moonshot 开放平台](https://platform.moonshot.cn/)
2. 注册账号
3. 进入控制台创建 API Key
4. 复制 API Key（格式：`...`）

## 设置环境变量

**Windows PowerShell:**
```powershell
$env:MOONSHOT_API_KEY="你的 Moonshot API 密钥"
```

**永久设置:**
```powershell
[System.Environment]::SetEnvironmentVariable("MOONSHOT_API_KEY", "你的 Moonshot API 密钥", "User")
```

**或编辑配置文件:**
```bash
# 编辑 configs/.env
MOONSHOT_API_KEY=你的 Moonshot API 密钥
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 分析单个视频

```bash
python moonshot_analyze.py --video sources_video/video.mp4
```

### 批量分析目录

```bash
# 所有视频保存到一个文件
python moonshot_analyze.py --video_dir sources_video

# 每个视频保存为单独文件（推荐）
python moonshot_analyze.py --video_dir sources_video --one_file_per_video
```

### 断点续传

```bash
python moonshot_analyze.py --video_dir sources_video --resume --one_file_per_video
```

### 指定模型

```bash
python moonshot_analyze.py --video_dir sources_video --model kimi-k2.5
```

## 输出

### 输出文件

- `output/视频文件名.json` - 单个视频分析结果
- `output/results.jsonl` - 所有视频结果（如果未使用 --one_file_per_video）
- `output/summary.json` - 汇总报告

### 输出示例

```json
{
  "video_path": "sources_video\\video.mp4",
  "model": "kimi-k2.5",
  "annotation": {
    "ppe": {
      "helmet": true,
      "insulating_clothing": true,
      "insulating_gloves": true
    },
    "actions": [...],
    "grounding_switch": true,
    "warning_sign": true,
    "sequence_valid": true
  },
  "scene_description": "一名工作人员佩戴安全头盔...",
  "report": {...}
}
```

## 与 OpenRouter 版本的区别

| 特性 | Moonshot API | OpenRouter |
|------|-------------|------------|
| 视频支持 | ✅ 支持 | ❌ 不支持 |
| API 密钥 | MOONSHOT_API_KEY | OPENROUTER_API_KEY |
| 价格 | 官方定价 | 可能略有不同 |
| 稳定性 | 官方支持 | 第三方代理 |

## 故障排除

### 错误：缺少 MOONSHOT_API_KEY

**解决：**
```bash
# 设置环境变量
$env:MOONSHOT_API_KEY="你的密钥"
```

### 错误：API 密钥无效

**解决：**
- 检查 API 密钥是否正确
- 确保在 Moonshot 平台已激活
- 检查是否有足够的余额

### 错误：视频上传失败

**解决：**
- 检查视频文件格式（支持 MP4, MOV, WebM 等）
- 检查视频大小（限制 80MB）
- 检查网络连接

## 价格说明

Moonshot 官方定价（截至 2024 年）：
- Kimi K2.5：约 ¥0.012/千 tokens
- 单个视频分析成本：约 ¥0.1-0.5（取决于视频长度）

## 下一步

1. 获取 Moonshot API 密钥
2. 设置环境变量
3. 运行 `python moonshot_analyze.py --video_dir sources_video --one_file_per_video`

---

**提示：** Moonshot API 是官方支持的视频分析方案，推荐使用！