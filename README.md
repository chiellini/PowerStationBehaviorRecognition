# 电力高压柜安全操作视频分析系统

基于视觉语言模型（VLM）的电力高压柜安全操作视频分析系统，使用 **OpenRouter 的 Kimi 多模态模型**自动识别操作人员的个人防护装备（PPE）穿戴情况、动作序列、安全违规，并生成自然语言场景描述。

## 功能特性

- **PPE 检测**：自动识别安全头盔、绝缘服、绝缘手套的穿戴情况
- **动作识别**：按时间顺序提取操作动作（捡起、插入、旋转、打开、关闭等）
- **旋转参数识别**：识别旋转方向（顺时针/逆时针）和圈数
- **特殊操作检测**：检测接地刀闸操作和标识牌悬挂
- **安全规范判断**：根据 PPE 和操作顺序判断是否符合安全规范
- **自然语言场景描述**：生成流畅的中文场景描述文本
- **批量处理**：支持单视频和目录批量处理
- **断点续传**：支持中断后继续处理
- **重试机制**：自动重试失败的 API 请求

## 支持的模型

| 模型 | 说明 | 价格 |
|------|------|------|
| **kimi** (推荐) | Kimi K2.5，性价比高 | ~$0.25/百万 tokens |
| **kimi-vision** | Kimi 视觉增强版 | ~$0.50/百万 tokens |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

**获取 API 密钥：**
1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册账号
3. 创建 API Key

**设置密钥：**

```powershell
# Windows PowerShell
$env:OPENROUTER_API_KEY="sk-or-你的密钥"

# 或编辑配置文件
cp configs/.env.example configs/.env
# 编辑 configs/.env，填入 OPENROUTER_API_KEY
```

### 3. 运行分析

**分析单个视频：**
```bash
python analyze.py --video sources_video/video.mp4
```

**批量分析目录：**
```bash
python analyze.py --video_dir sources_video
```

**断点续传：**
```bash
python analyze.py --video_dir sources_video --resume
```

**使用 Kimi Vision：**
```bash
python analyze.py --video_dir sources_video --model kimi-vision
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--video` | 单个视频文件路径 | - |
| `--video_dir` | 视频目录路径 | - |
| `--out` | 输出结果文件路径 | output/results.jsonl |
| `--summary` | 汇总报告输出路径 | output/summary.json |
| `--model` | 模型（kimi 或 kimi-vision） | kimi |
| `--api_key` | OpenRouter API 密钥 | 环境变量 |
| `--max_mb` | 最大视频文件大小（MB） | 80 |
| `--timeout` | API 请求超时时间（秒） | 300 |
| `--retries` | 最大重试次数 | 3 |
| `--resume` | 断点续传 | False |
| `--quiet` | 安静模式 | False |

## 输出示例

### 场景描述

**不规范操作：**
```
一名男子未佩戴安全头盔、未穿着绝缘服、绝缘手套，穿着不规范。弯腰捡起断路器手车摇柄，
将手车摇柄插进摇柄插口，顺时针旋转 9 圈后，拔出手车摇柄放置在地上。起身后，向前伸手。
打开上开关柜门。用右手拨动柜内的二次开关。关闭上开关柜门。
```

**规范操作：**
```
一名工作人员佩戴安全头盔、穿戴绝缘服与绝缘手套，穿着规范。弯腰捡起断路器手车摇柄，
将手车摇柄插进摇柄插口，逆时针旋转 7 圈后，拔出手车摇柄放置在地上。起身后，向前伸手。
打开上开关柜门。用右手拨动柜内的二次开关。关闭上开关柜门。接着弯腰捡起接地开关操作手柄，
将手柄插进中门右下侧六角孔内，顺时针下压合上接地刀闸，将手柄放置于地上。
捡起地上的标识牌悬挂在上柜门。
```

### JSON 输出

```json
{
  "video_path": "sources_video/video.mp4",
  "model": "moonshotai/kimi-k2.5",
  "annotation": {
    "ppe": {
      "helmet": false,
      "insulating_clothing": false,
      "insulating_gloves": false
    },
    "actions": [...],
    "grounding_switch": false,
    "warning_sign": false,
    "sequence_valid": false
  },
  "scene_description": "一名男子未佩戴安全头盔...",
  "report": {
    "violations": ["未佩戴安全头盔", "未穿着绝缘服", "未佩戴绝缘手套"],
    "overall_compliant": false
  }
}
```

## 结果分析工具

```bash
# 查看统计信息
python scripts/analyze_results.py --input output/results.jsonl

# 导出 CSV
python scripts/analyze_results.py --input output/results.jsonl --export_csv output/results.csv
```

## 兼容模式

保留原始脚本，完全兼容：

```bash
# 基本用法
python vlm_kimi_video_label.py --video_dir sources_video

# 启用场景描述
python vlm_kimi_video_label.py --video_dir sources_video --with_scene_desc
```

## 支持的视频格式

MP4, MOV, WebM, MPEG, M4V, AVI

## 注意事项

1. **API 密钥**：需要有效的 OpenRouter API 密钥
2. **视频大小**：默认限制 80MB，可通过 `--max_mb` 调整
3. **网络连接**：需要稳定的网络连接
4. **费用**：Kimi K2.5 约 $0.25/百万 tokens，单个视频成本极低

## 项目结构

```
PowerStationBehaviorRecognition/
├── src/
│   ├── main.py                   # 主程序
│   ├── config.py                 # 配置（仅 Kimi）
│   └── scene_description.py      # 场景描述生成器
├── scripts/
│   └── analyze_results.py        # 结果分析工具
├── configs/
│   └── .env.example              # 环境变量模板
├── sources_video/                # 视频源目录
├── output/                       # 输出结果目录
├── analyze.py                    # 命令行入口
├── vlm_kimi_video_label.py       # 兼容脚本
├── test_project.py               # 测试脚本
├── requirements.txt              # 依赖
└── README.md                     # 项目说明
```

## 常见问题

### Q: 如何获取 API 密钥？
访问 [OpenRouter](https://openrouter.ai/) 注册并创建 API Key

### Q: 费用如何？
Kimi K2.5 约 $0.25/百万 tokens，单个视频分析成本极低（约几分钱）

### Q: 两个模型有什么区别？
- **kimi** (Kimi K2.5)：性价比高，推荐用于常规分析
- **kimi-vision**：视觉增强版，对细节识别更准确

### Q: 视频太大怎么办？
使用 `--max_mb` 参数调整限制：
```bash
python analyze.py --video_dir sources_video --max_mb 100
```

### Q: 如何断点续传？
```bash
python analyze.py --video_dir sources_video --resume
```

## 测试

```bash
python test_project.py
```

## 许可证

MIT License