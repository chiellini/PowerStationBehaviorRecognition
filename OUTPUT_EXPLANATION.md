# 输出文件说明

## 输出位置

所有分析结果默认保存在 `output/` 目录。

## 两种输出模式

### 模式 1：所有视频保存到一个文件（默认）

```bash
python analyze.py --video_dir sources_video
```

**输出文件：**
- `output/results.jsonl` - 所有视频的分析结果（每行一个视频）
- `output/summary.json` - 汇总统计报告

**优点：**
- 便于批量处理和统计分析
- 文件数量少，易于管理

**缺点：**
- 需要解析整个文件才能查看单个视频结果

### 模式 2：每个视频保存为单独文件（推荐）

```bash
python analyze.py --video_dir sources_video --one_file_per_video
```

**输出文件：**
- `output/视频文件名 1.json` - 第一个视频的分析结果
- `output/视频文件名 2.json` - 第二个视频的分析结果
- `...`
- `output/summary.json` - 汇总统计报告

**优点：**
- 每个视频独立文件，易于查找和分享
- 可以直接打开查看，无需解析
- 文件名与视频名对应，一目了然

**缺点：**
- 文件数量多

## 输出文件示例

### 单个视频文件（模式 2）

文件名：`output/67140af4acc5009e5dbd2be57ae8474a.json`

内容结构：
```json
{
  "video_path": "sources_video\\67140af4acc5009e5dbd2be57ae8474a.mp4",
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

### 汇总文件（两种模式都有）

文件名：`output/summary.json`

内容结构：
```json
{
  "summary": {
    "total_videos": 2,
    "successful_analyses": 2,
    "failed_analyses": 0,
    "skipped_videos": 0,
    "success_rate": "100.0%"
  },
  "ppe_compliance": {
    "helmet": "1/2",
    "insulating_clothing": "1/2",
    "insulating_gloves": "1/2"
  },
  "sequence_compliance": "1/2",
  "violations": [...],
  "timestamp": "2026-03-02T15:36:41.800Z"
}
```

## 使用建议

### 推荐模式 2（每个视频一个文件）的场景：
- ✅ 需要单独查看某个视频的分析结果
- ✅ 需要将结果分享给其他人
- ✅ 视频数量不多（< 100 个）
- ✅ 需要长期保存分析结果

### 推荐模式 1（所有视频一个文件）的场景：
- ✅ 需要进行批量统计分析
- ✅ 视频数量非常多（> 100 个）
- ✅ 只需要汇总报告，不需要查看单个视频
- ✅ 临时分析，不需要长期保存

## 查看结果

### 查看单个视频结果

```bash
# Windows PowerShell
Get-Content output/视频文件名.json | ConvertFrom-Json

# 或使用文本编辑器直接打开
notepad output/视频文件名.json
```

### 查看汇总报告

```bash
# Windows PowerShell
Get-Content output/summary.json | ConvertFrom-Json | Format-List
```

### 使用分析工具

```bash
# 查看统计信息
python scripts/analyze_results.py --input output/results.jsonl

# 导出 CSV
python scripts/analyze_results.py --input output/results.jsonl --export_csv output/results.csv
```

## 断点续传

两种模式都支持断点续传：

```bash
# 模式 1 续传
python analyze.py --video_dir sources_video --resume

# 模式 2 续传
python analyze.py --video_dir sources_video --one_file_per_video --resume
```

程序会自动检测已处理的视频并跳过。

## 清理输出

```bash
# 删除所有输出文件
Remove-Item output\* -Recurse -Force

# 只删除 JSONL 文件
Remove-Item output\results.jsonl -Force

# 只删除单独的视频文件
Remove-Item output\*.json -Force
```

---

**提示：** 默认推荐使用 **模式 2**（每个视频一个文件），更直观易管理！