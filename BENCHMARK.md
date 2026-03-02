# 电力站高压柜操作视频辨识 Benchmark

## 目标

对室内高压开关柜操作视频进行自动分析，输出：
1. **结构化标注（JSON）**：PPE、动作序列、接地刀闸、标识牌、顺序合规性
2. **自然语言场景描述**：可直接作为 Benchmark 的「标准回答」或评估参考

## Prompt 设计（工业级）

- **System Prompt**：中文语义强化，明确五项任务（PPE、动作、旋转、接地/标识牌、顺序合规）
- **User Prompt**：中英混合强约束，严格 JSON schema，便于解析与评估

Prompt 已内置在 `moonshot_analyze.py` 中，与上述设计一致。

## 输出格式

### 1. 结构化标注（annotation）

```json
{
  "ppe": {
    "helmet": true/false,
    "insulating_clothing": true/false,
    "insulating_gloves": true/false
  },
  "actions": [
    {
      "action": "pick|insert|rotate|toggle|open|close|lock|hang|place|press",
      "object": "string",
      "direction": "clockwise|counter_clockwise|null",
      "rotation_count": number|null
    }
  ],
  "grounding_switch": true/false,
  "warning_sign": true/false,
  "sequence_valid": true/false
}
```

### 2. 自然语言场景描述（scene_description，最终回答）

**不规范操作示例：**

一名男子未佩戴安全头盔、未穿着绝缘服、绝缘手套，穿着不规范。弯腰捡起断路器手车摇柄，将手车摇柄插进摇柄插口，顺时针旋转9圈后，拔出手车摇柄放置在地上。起身后，向前伸手打开上开关柜门。用右手拨动柜内的二次开关后，关闭上开关柜门。

**规范操作示例：**

一名工作人员佩戴安全头盔、穿戴绝缘服与绝缘手套，穿着规范。弯腰捡起断路器手车摇柄，插入摇柄插口，逆时针旋转7圈后，拔出手车摇柄放置在地上。打开上开关柜门后用右手拨动柜内的二次开关，之后关闭上开关柜门。接着弯腰捡起接地开关操作手柄，将手柄插进中门右下侧六角孔内，顺时针下压合上接地刀闸，将手柄放置于地上，并捡起地上的标识牌悬挂在上柜门。

## 运行方式

```bash
# 使用 Moonshot API（支持视频）
python moonshot_analyze.py --video_dir sources_video --one_file_per_video
```

每个视频会生成一个 JSON 文件，内含 `annotation`、`scene_description`、`report` 等字段；其中 **`scene_description`** 即上述自然语言「最终回答」，可用于 Benchmark 标注或评估。

## 文件说明

| 文件 | 作用 |
|------|------|
| `moonshot_analyze.py` | 使用工业级 Prompt 调用 Moonshot 视频 API，并生成 scene_description |
| `src/scene_description.py` | 将 annotation JSON 转为自然语言场景描述 |
| `configs/.env` | 配置 `MOONSHOT_API_KEY` |
