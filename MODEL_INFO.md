# 模型选择说明

## 当前支持的模型

### ✅ Kimi K2.5（默认，推荐）

**模型 ID:** `moonshotai/kimi-k2.5`

**特点:**
- 性价比高（约 $0.25/百万 tokens）
- 支持多模态（图片 + 文本）
- 中文理解能力强

**限制:**
- ⚠️ **不支持视频输入**（截至 2024 年初）
- 只支持图片格式

**适用场景:**
- 图片分析
- 文本理解
- 需要中文支持的场景

### ✅ Kimi Vision

**模型 ID:** `moonshotai/kimi-vision`

**特点:**
- 视觉增强版
- 对图片细节识别更准确

**限制:**
- ⚠️ **不支持视频输入**
- 价格略高于 K2.5

**适用场景:**
- 需要精确视觉识别的场景

## ❌ 不支持的模型

### Gemini Flash

**模型 ID:** `google/gemini-2.0-flash-001`

**问题:**
- 需要额外的 API 权限
- 普通 OpenRouter API 密钥无法访问（403 Forbidden）
- 可能需要单独申请或企业账户

**建议:**
- 如果你有 Gemini API 权限，可以手动修改配置使用
- 否则请使用 Kimi 模型

## 视频分析解决方案

由于 Kimi 模型不支持视频输入，有以下解决方案：

### 方案 1：提取视频关键帧（推荐）

1. **安装 ffmpeg**
   ```bash
   choco install ffmpeg  # Windows
   sudo apt install ffmpeg  # Linux
   brew install ffmpeg  # Mac
   ```

2. **提取关键帧**
   ```bash
   python src/extract_frames.py sources_video/video.mp4
   ```

3. **分析提取的帧图片**
   - 将提取的图片作为输入
   - Kimi 模型可以分析这些图片

### 方案 2：使用支持视频的 API

- Google Cloud Video AI
- Azure Video Analyzer
- AWS Rekognition Video

这些服务专门用于视频分析，但价格较高。

### 方案 3：手动截图

对于少量视频：
1. 播放视频
2. 截取关键操作瞬间
3. 使用 Kimi 分析截图

## 当前推荐配置

**对于高压柜视频分析：**

```bash
# 使用 Kimi K2.5（默认）
python analyze.py --video_dir sources_video --one_file_per_video

# 如果有 ffmpeg，先提取帧
python src/extract_frames.py sources_video/video.mp4
# 然后分析提取的图片
```

## 未来计划

1. **实现视频帧自动提取** - 在分析前自动提取关键帧
2. **多帧分析** - 分析多个关键帧后生成完整描述
3. **时序理解** - 理解动作的时间顺序

---

**总结：** 目前使用 **Kimi K2.5** 模型，配合**视频帧提取**功能是最佳方案。