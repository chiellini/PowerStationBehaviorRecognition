# 快速入门指南

## 1. 安装

```bash
pip install -r requirements.txt
```

## 2. 获取 API 密钥

1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册账号
3. 创建 API Key（格式：`sk-or-...`）
4. 充值（Kimi 很便宜，约 $0.25/百万 tokens）

## 3. 配置

**方式 1：环境变量（推荐）**
```powershell
# Windows PowerShell
$env:OPENROUTER_API_KEY="sk-or-..."

# 永久设置
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-...", "User")
```

**方式 2：配置文件**
```bash
cp configs/.env.example configs/.env
# 编辑 configs/.env，填入 OPENROUTER_API_KEY
```

**方式 3：命令行参数**
```bash
python analyze.py --api_key sk-or-...
```

## 4. 运行

### 分析单个视频

```bash
python analyze.py --video sources_video/视频文件名.mp4
```

### 批量分析目录

```bash
python analyze.py --video_dir sources_video
```

### 断点续传

```bash
python analyze.py --video_dir sources_video --resume
```

### 使用 Kimi Vision

```bash
python analyze.py --video_dir sources_video --model kimi-vision
```

## 5. 查看结果

### 结果文件

- `output/results.jsonl` - 详细分析结果（每行一个视频）
- `output/summary.json` - 汇总报告

### 使用分析工具

```bash
# 查看统计信息
python scripts/analyze_results.py --input output/results.jsonl

# 导出 CSV
python scripts/analyze_results.py --input output/results.jsonl --export_csv output/results.csv
```

## 6. 输出示例

### 控制台输出

```
使用模型：moonshotai/kimi-k2.5
API 密钥：************abcd

分析目录：sources_video

分析视频：100%|████████| 2/2

结果已保存至：output\results.jsonl
汇总报告：output\summary.json

统计:
{
  "total_videos": 2,
  "successful_analyses": 2,
  "failed_analyses": 0,
  "skipped_videos": 0,
  "success_rate": "100.0%"
}
```

### 场景描述

```
一名工作人员佩戴安全头盔、穿戴绝缘服与绝缘手套，穿着规范。
弯腰捡起断路器手车摇柄，将手车摇柄插进摇柄插口，逆时针旋转 7 圈后，
拔出手车摇柄放置在地上。起身后，向前伸手。打开上开关柜门。
用右手拨动柜内的二次开关。关闭上开关柜门。
接着弯腰捡起接地开关操作手柄，将手柄插进中门右下侧六角孔内，
顺时针下压合上接地刀闸，将手柄放置于地上。
捡起地上的标识牌悬挂在上柜门。
```

## 7. 常用命令

### 调整文件大小限制

```bash
python analyze.py --video_dir sources_video --max_mb 100
```

### 增加超时时间

```bash
python analyze.py --video_dir sources_video --timeout 600
```

### 安静模式

```bash
python analyze.py --video_dir sources_video --quiet
```

### 查看帮助

```bash
python analyze.py --help
```

## 8. 故障排除

### 问题：找不到 API 密钥

```bash
# 检查是否设置
echo $env:OPENROUTER_API_KEY

# 重新设置
$env:OPENROUTER_API_KEY="sk-or-..."
```

### 问题：依赖安装失败

```bash
# 升级 pip
python -m pip install --upgrade pip

# 重新安装
pip install -r requirements.txt --force-reinstall
```

### 问题：API 请求超时

```bash
python analyze.py --video_dir sources_video --timeout 600 --retries 5
```

## 9. 下一步

- 阅读 `README.md` 了解完整文档
- 运行 `python test_project.py` 测试系统
- 开始分析你的视频！

---

**祝您使用愉快！** ⚡