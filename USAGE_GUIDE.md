# 电力高压柜安全操作视频分析系统

## 项目概览

这是一个基于视觉语言模型（VLM）的电力系统安全分析工具，专门用于分析高压开关柜操作视频，自动检测安全违规行为并生成自然语言描述。

## 核心能力

### 1. 安全装备检测
- ✅ 安全头盔佩戴检测
- ✅ 绝缘服穿着检测
- ✅ 绝缘手套佩戴检测

### 2. 动作序列识别
- ✅ 工具操作（捡起、插入、旋转、放置）
- ✅ 柜门操作（打开、关闭）
- ✅ 开关操作（拨动、按压）
- ✅ 特殊操作（接地刀闸、标识牌悬挂）

### 3. 参数识别
- ✅ 旋转方向（顺时针/逆时针）
- ✅ 旋转圈数统计
- ✅ 操作顺序验证

### 4. 智能描述生成
- ✅ 自然语言场景描述
- ✅ 违规行为报告
- ✅ 合规性判断

## 快速开始

### 3 步安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 API 密钥
$env:OPENROUTER_API_KEY="sk-or-..."  # Windows PowerShell

# 3. 运行分析
python analyze.py --video_dir sources_video
```

### 使用示例

```bash
# 分析单个视频
python analyze.py --video video.mp4

# 批量分析（支持断点续传）
python analyze.py --video_dir sources_video --resume

# 使用不同模型
python analyze.py --video_dir sources_video --model kimi
```

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

## 主要特性

### 🔧 技术特性
- **重试机制**：API 请求失败自动重试（指数退避）
- **断点续传**：支持中断后继续处理
- **多模型支持**：Kimi、Gemini、Claude 等
- **实时进度**：显示处理进度和统计信息
- **错误处理**：完善的异常捕获和报告

### 📊 分析功能
- **批量处理**：支持目录批量分析
- **统计分析**：生成汇总报告和统计数据
- **结果导出**：支持 JSONL、JSON、CSV 格式
- **详细报告**：包含 PPE 分析、违规记录、动作统计

### 🎯 业务价值
- **自动化**：替代人工观看视频
- **标准化**：统一的安全规范判断
- **可追溯**：完整的分析记录
- **高效率**：批量处理，节省时间

## 项目结构

```
PowerStationBehaviorRecognition/
├── src/                          # 源代码
│   ├── main.py                   # 主程序
│   ├── config.py                 # 配置
│   └── scene_description.py      # 场景描述
├── scripts/                      # 工具
│   └── analyze_results.py        # 结果分析
├── analyze.py                    # CLI 入口
├── vlm_kimi_video_label.py       # 兼容脚本
├── test_project.py               # 测试脚本
├── requirements.txt              # 依赖
└── README.md                     # 文档
```

## 支持的模型

| 模型 | 名称 | 说明 |
|------|------|------|
| Kimi K2.5 | `kimi` | 推荐，性价比高 |
| Kimi Vision | `kimi-vision` | 视觉增强版 |
| Gemini Flash | `gemini-flash` | 快速处理 |
| Gemini Pro | `gemini-pro` | 高质量分析 |
| Claude 3.5 | `claude` | 强理解能力 |
| GPT-4V | `gpt4v` | 多模态模型 |

## 支持的视频格式

MP4, MOV, WebM, MPEG, M4V, AVI

## 系统要求

- Python 3.8+
- Windows / Linux / Mac
- 稳定的网络连接
- OpenRouter API 密钥

## 测试

运行测试脚本验证系统：

```bash
python test_project.py
```

测试内容包括：
- ✅ 场景描述生成
- ✅ 配置加载
- ✅ JSON 解析
- ✅ 错误处理

## 文档

- 📘 **README.md** - 完整项目文档
- 🚀 **QUICKSTART.md** - 快速入门指南
- 📝 **PROJECT_SUMMARY.md** - 项目优化总结
- 📋 **USAGE_GUIDE.md** - 使用指南（本文件）

## 常见问题

### Q: 如何获取 API 密钥？
访问 [OpenRouter](https://openrouter.ai/) 注册并创建 API Key

### Q: 费用如何？
Kimi K2.5 约 $0.25/百万 tokens，单个视频分析成本极低

### Q: 视频大小有限制吗？
默认 80MB，可通过 `--max_mb` 参数调整

### Q: 支持离线使用吗？
需要网络连接调用 VLM API，不支持完全离线

### Q: 如何批量处理？
使用 `--video_dir` 参数指定目录，支持 `--resume` 断点续传

## 技术支持

如有问题，请查看：
1. README.md 完整文档
2. QUICKSTART.md 快速入门
3. 运行 `python analyze.py --help` 查看帮助

## 许可证

MIT License

---

**让电力安全分析更智能、更高效！** ⚡