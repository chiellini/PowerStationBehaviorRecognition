"""
电力高压柜 VLM 视频标注工具（兼容版本）
使用 OpenRouter API 和 Kimi 模型进行视频分析标注

此脚本保留了原始功能，同时集成了场景描述生成功能
"""
import os
import sys
import json
import base64
import argparse
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional

import requests
from tqdm import tqdm

# 尝试导入场景描述生成模块
try:
    from scene_description import generate_scene_description, generate_detailed_report
    SCENE_DESCRIPTION_ENABLED = True
except ImportError:
    SCENE_DESCRIPTION_ENABLED = False
    print("警告：scene_description 模块未找到，场景描述功能将被禁用")


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """你是一名电力高压柜安全操作分析模型。

任务：分析视频中的高压柜操作过程。

你必须完成：

1. 判断是否佩戴：
   - 安全头盔
   - 绝缘服
   - 绝缘手套

2. 按时间顺序提取全部动作。

3. 识别：
   - 旋转方向（顺时针或逆时针）
   - 旋转圈数（若无法确定返回 null）

4. 判断是否执行：
   - 接地刀闸操作
   - 标识牌悬挂

5. 判断操作顺序是否符合电力安全规范。

⚠️ 仅输出 JSON。
⚠️ 不要输出解释。
⚠️ 不要输出额外文本。
⚠️ 所有布尔值必须使用 true 或 false。
⚠️ 严格按照给定 schema。
"""


USER_PROMPT = """请分析提供的视频。

场景：室内高压开关柜操作。

输出必须为以下 JSON 结构：

{
  "ppe": {
    "helmet": true/false,
    "insulating_clothing": true/false,
    "insulating_gloves": true/false
  },
  "actions": [
    {
      "action": "pick|insert|rotate|toggle|open|close|lock|hang|place|press",
      "object": "对象名称（中文）",
      "direction": "clockwise|counter_clockwise|null",
      "rotation_count": number|null
    }
  ],
  "grounding_switch": true/false,
  "warning_sign": true/false,
  "sequence_valid": true/false
}

规则：

- 动作必须按时间顺序。
- 如果没有执行接地刀闸，grounding_switch 为 false。
- 如果没有挂标识牌，warning_sign 为 false。
- 如果存在 PPE 缺失或顺序违规，sequence_valid 必须为 false。
- 严格返回 JSON。
"""


def guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "video/mp4"


def encode_video_to_data_url(path: Path) -> str:
    mime = guess_mime(path)
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def call_openrouter_kimi(
    api_key: str,
    model: str,
    video_data_url: str,
    timeout_s: int = 300,
    extra_headers: Optional[Dict[str, str]] = None,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "HV-SwitchCabinet-VLM-Benchmark-Labeler",
    }
    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {
                        "type": "video_url",
                        "videoUrl": {"url": video_data_url},
                    },
                ],
            },
        ],
        "stream": False,
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def robust_json_loads(s: str) -> Any:
    """
    Best-effort JSON parsing:
    - If model returns fenced code block, strip it.
    - If it returns leading/trailing text, try to extract the first JSON object.
    """
    s = s.strip()

    # Strip markdown fences if present
    if s.startswith("```"):
        s = s.strip("`")
        # Some models output ```json ... ```
        # remove possible "json" first line
        lines = s.splitlines()
        if lines and lines[0].strip().lower() in ("json", "javascript"):
            s = "\n".join(lines[1:]).strip()

    # Direct parse
    try:
        return json.loads(s)
    except Exception:
        pass

    # Extract first {...} block (simple brace matching)
    start = s.find("{")
    if start == -1:
        raise ValueError("No JSON object start found.")
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = s[start : i + 1]
                return json.loads(candidate)

    raise ValueError("Failed to parse JSON from model output.")


def main():
    parser = argparse.ArgumentParser(
        description="电力高压柜 VLM 视频标注工具（兼容版本）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基本用法（与原版兼容）
  python vlm_kimi_video_label.py --video_dir ./sources_video --api_key YOUR_KEY
  
  # 启用场景描述生成
  python vlm_kimi_video_label.py --video_dir ./sources_video --with_scene_desc --api_key YOUR_KEY
  
  # 指定模型
  python vlm_kimi_video_label.py --video_dir ./sources_video --model moonshotai/kimi-k2.5 --api_key YOUR_KEY
        """,
    )
    parser.add_argument("--video_dir", type=str, required=True, help="Folder containing videos")
    parser.add_argument("--out", type=str, default="annotations.jsonl", help="Output JSONL path")
    parser.add_argument(
        "--model",
        type=str,
        default="moonshotai/kimi-k2.5",
        help="OpenRouter model id (recommended: moonshotai/kimi-k2.5)",
    )
    parser.add_argument("--api_key", type=str, default=os.getenv("OPENROUTER_API_KEY", ""), help="OpenRouter API key")
    parser.add_argument("--max_mb", type=int, default=80, help="Skip videos larger than this size (MB)")
    parser.add_argument("--timeout", type=int, default=300, help="API timeout in seconds")
    parser.add_argument(
        "--with_scene_desc",
        action="store_true",
        help="Enable scene description generation (requires scene_description module)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint (skip already processed videos)",
    )
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing API key. Set OPENROUTER_API_KEY env var or pass --api_key.")

    video_dir = Path(args.video_dir)
    if not video_dir.exists():
        raise SystemExit(f"video_dir not found: {video_dir}")

    exts = {".mp4", ".mov", ".webm", ".mpeg", ".mpg", ".m4v", ".avi"}
    videos = [p for p in video_dir.rglob("*") if p.suffix.lower() in exts]

    if not videos:
        raise SystemExit(f"No video files found in {video_dir} (extensions: {sorted(exts)})")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 加载已处理的视频（断点续传）
    processed_videos = set()
    if args.resume and out_path.exists():
        with out_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        if "video_path" in record:
                            processed_videos.add(record["video_path"])
                    except Exception:
                        pass
        print(f"Resuming: skipping {len(processed_videos)} already processed videos")

    # 过滤已处理的视频
    if args.resume:
        videos = [v for v in videos if str(v) not in processed_videos]

    file_mode = "a" if args.resume and processed_videos else "w"
    
    with out_path.open(file_mode, encoding="utf-8") as f:
        for vp in tqdm(videos, desc="Labeling videos"):
            size_mb = vp.stat().st_size / (1024 * 1024)
            if size_mb > args.max_mb:
                record = {
                    "video_path": str(vp),
                    "skipped": True,
                    "reason": f"file too large: {size_mb:.1f} MB > {args.max_mb} MB",
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                continue

            try:
                video_data_url = encode_video_to_data_url(vp)
                raw = call_openrouter_kimi(
                    api_key=args.api_key,
                    model=args.model,
                    video_data_url=video_data_url,
                    timeout_s=args.timeout,
                )
                parsed = robust_json_loads(raw)

                record = {
                    "video_path": str(vp),
                    "model": args.model,
                    "annotation": parsed,
                    "raw": raw,
                }

                # 如果启用了场景描述生成
                if args.with_scene_desc and SCENE_DESCRIPTION_ENABLED:
                    try:
                        scene_desc = generate_scene_description(parsed)
                        detailed_report = generate_detailed_report(parsed, str(vp))
                        record["scene_description"] = scene_desc
                        record["report"] = detailed_report
                    except Exception as e:
                        record["scene_desc_error"] = str(e)

            except Exception as e:
                record = {
                    "video_path": str(vp),
                    "model": args.model,
                    "error": str(e),
                }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Done. Wrote: {out_path.resolve()}")


if __name__ == "__main__":
    main()
