# 使用说明

## 第一次使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 获取 API 密钥

1. 访问 https://openrouter.ai/
2. 注册账号
3. 创建 API Key（格式：`sk-or-...`）
4. 建议充值 $5-10 即可使用很长时间

### 3. 配置密钥

**Windows PowerShell:**
```powershell
$env:OPENROUTER_API_KEY="sk-or-你的密钥"
```

**永久设置（推荐）:**
```powershell
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-你的密钥", "User")
```

## 开始分析

### 方法 1：使用分析脚本（推荐）

```bash
# 分析单个视频
python analyze.py --video sources_video/你的视频.mp4

# 分析整个目录
python analyze.py --video_dir sources_video
```

### 方法 2：使用兼容脚本

```bash
# 基本用法
python vlm_kimi_video_label.py --video_dir sources_video

# 带场景描述
python vlm_kimi_video_label.py --video_dir sources_video --with_scene_desc
```

## 查看结果

### 分析结果

结果保存在 `output/` 目录：
- `results.jsonl` - 详细分析结果
- `summary.json` - 汇总报告

### 使用分析工具

```bash
# 查看统计
python scripts/analyze_results.py --input output/results.jsonl

# 导出 CSV
python scripts/analyze_results.py --input output/results.jsonl --export_csv output/results.csv
```

## 常用命令

### 断点续传

```bash
python analyze.py --video_dir sources_video --resume
```

### 使用 Kimi Vision

```bash
python analyze.py --video_dir sources_video --model kimi-vision
```

### 调整参数

```bash
# 增加文件大小限制到 100MB
python analyze.py --video_dir sources_video --max_mb 100

# 增加超时时间到 10 分钟
python analyze.py --video_dir sources_video --timeout 600
```

### 安静模式

```bash
python analyze.py --video_dir sources_video --quiet
```

## 输出说明

### 场景描述

每个视频会生成类似以下的描述：

```
一名工作人员佩戴安全头盔、穿戴绝缘服与绝缘手套，穿着规范。
弯腰捡起断路器手车摇柄，将手车摇柄插进摇柄插口，逆时针旋转 7 圈后，
拔出手车摇柄放置在地上。起身后，向前伸手。打开上开关柜门。
用右手拨动柜内的二次开关。关闭上开关柜门。
接着弯腰捡起接地开关操作手柄，将手柄插进中门右下侧六角孔内，
顺时针下压合上接地刀闸，将手柄放置于地上。
捡起地上的标识牌悬挂在上柜门。
```

### JSON 结果

```json
{
  "video_path": "sources_video/video.mp4",
  "model": "moonshotai/kimi-k2.5",
  "scene_description": "场景描述...",
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
  "report": {
    "violations": [],
    "overall_compliant": true
  }
}
```

## 故障排除

### 问题：找不到 API 密钥

**解决：**
```bash
# 检查是否设置
echo $env:OPENROUTER_API_KEY

# 重新设置
$env:OPENROUTER_API_KEY="sk-or-..."
```

### 问题：视频文件过大

**解决：**
```bash
python analyze.py --video_dir sources_video --max_mb 100
```

### 问题：API 请求超时

**解决：**
```bash
python analyze.py --video_dir sources_video --timeout 600
```

### 问题：依赖安装失败

**解决：**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 重新安装
pip install -r requirements.txt --force-reinstall
```

## 获取帮助

```bash
# 查看帮助
python analyze.py --help
```

## 下一步

- 阅读 `README.md` 了解完整文档
- 阅读 `QUICKSTART.md` 快速入门
- 运行 `python test_project.py` 测试系统

---

**祝您使用愉快！** ⚡