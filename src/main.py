"""
电力高压柜安全操作视频分析系统
使用 VLM（视觉语言模型）分析高压柜操作视频，检测安全违规并生成场景描述
"""
import os
import sys
import json
import base64
import argparse
import mimetypes
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import requests
from tqdm import tqdm

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from scene_description import generate_scene_description, generate_detailed_report
from config import (
    OPENROUTER_URL,
    API_KEY,
    DEFAULT_MODEL,
    MAX_VIDEO_SIZE_MB,
    API_TIMEOUT_SECONDS,
    MAX_RETRIES,
    SUPPORTED_VIDEO_EXTENSIONS,
)


SYSTEM_PROMPT = """你是一名电力高压柜安全操作分析专家模型。

任务：分析视频中的高压柜操作过程，提取所有关键信息。

你必须完成以下分析：

1. 个人防护装备（PPE）检测：
   - 安全头盔：是否佩戴
   - 绝缘服：是否穿着
   - 绝缘手套：是否佩戴

2. 动作序列识别（按时间顺序）：
   - pick（捡起）：捡起工具或物品
   - insert（插入）：将工具插入插口
   - rotate（旋转）：旋转操作，需识别方向和圈数
   - place（放置）：放下工具
   - open（打开）：打开柜门
   - close（关闭）：关闭柜门
   - toggle（拨动）：拨动开关
   - hang（悬挂）：悬挂标识牌
   - press（按压）：按压按钮

3. 特殊操作检测：
   - 接地刀闸操作：是否执行
   - 标识牌悬挂：是否执行

4. 安全规范判断：
   - 根据 PPE 穿戴情况和操作顺序判断是否符合安全规范

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
      "rotation_count": 数字或 null
    }
  ],
  "grounding_switch": true/false,
  "warning_sign": true/false,
  "sequence_valid": true/false
}

规则：

- 动作必须按时间顺序排列。
- direction 仅对 rotate 动作有效，其他动作填 null。
- rotation_count 仅对 rotate 动作有效，表示旋转圈数，无法确定时填 null。
- object 使用中文描述具体对象，如"断路器手车摇柄"、"上开关柜门"、"二次开关"等。
- 如果没有执行接地刀闸，grounding_switch 为 false。
- 如果没有挂标识牌，warning_sign 为 false。
- 如果存在 PPE 缺失或顺序违规，sequence_valid 必须为 false。
- 严格返回 JSON，不要添加任何额外文本或解释。
"""


def guess_mime(path: Path) -> str:
    """猜测视频文件的 MIME 类型"""
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "video/mp4"


def encode_video_to_data_url(path: Path) -> str:
    """将视频文件编码为 base64 data URL"""
    mime = guess_mime(path)
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def call_vlm_api(
    api_key: str,
    model: str,
    video_data_url: str,
    timeout_s: int = 300,
    max_retries: int = 3,
) -> str:
    """
    调用 VLM API 进行视频分析（带重试机制）
    
    Args:
        api_key: OpenRouter API 密钥
        model: 模型 ID
        video_data_url: Base64 编码的视频 data URL
        timeout_s: 超时时间（秒）
        max_retries: 最大重试次数
        
    Returns:
        模型返回的原始文本
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "HV-SwitchCabinet-Safety-Analyzer",
    }

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

    # 重试机制
    for attempt in range(max_retries):
        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout_s)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                print(f"\nAPI 请求失败，{wait_time}秒后重试（{attempt + 1}/{max_retries}）: {str(e)}")
                time.sleep(wait_time)
            else:
                raise
    
    raise RuntimeError("API 请求失败，已达到最大重试次数")


def robust_json_loads(s: str) -> Any:
    """
    健壮的 JSON 解析
    处理模型返回的 markdown 代码块或包含额外文本的情况
    """
    s = s.strip()

    # 移除 markdown 代码块标记
    if s.startswith("```"):
        s = s.strip("`")
        lines = s.splitlines()
        if lines and lines[0].strip().lower() in ("json", "javascript"):
            s = "\n".join(lines[1:]).strip()

    # 直接解析
    try:
        return json.loads(s)
    except Exception:
        pass

    # 提取第一个 JSON 对象
    start = s.find("{")
    if start == -1:
        raise ValueError("未找到 JSON 对象起始位置")
    
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = s[start : i + 1]
                return json.loads(candidate)

    raise ValueError("无法从模型输出中解析 JSON")


def load_processed_videos(output_path: Path) -> set:
    """加载已处理的视频路径（用于断点续传）"""
    processed = set()
    
    if not output_path.exists():
        return processed
    
    try:
        with output_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    if "video_path" in record:
                        processed.add(record["video_path"])
    except Exception:
        pass
    
    return processed


def analyze_video(
    video_path: Path,
    api_key: str,
    model: str,
    max_mb: int = 80,
    timeout_s: int = 300,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    分析单个视频文件
    
    Args:
        video_path: 视频文件路径
        api_key: API 密钥
        model: 模型 ID
        max_mb: 最大文件大小（MB）
        timeout_s: 超时时间（秒）
        max_retries: 最大重试次数
        
    Returns:
        分析结果字典
    """
    size_mb = video_path.stat().st_size / (1024 * 1024)
    
    if size_mb > max_mb:
        return {
            "video_path": str(video_path),
            "skipped": True,
            "reason": f"文件过大：{size_mb:.1f} MB > {max_mb} MB",
        }
    
    try:
        video_data_url = encode_video_to_data_url(video_path)
        raw_response = call_vlm_api(
            api_key=api_key,
            model=model,
            video_data_url=video_data_url,
            timeout_s=timeout_s,
            max_retries=max_retries,
        )
        parsed = robust_json_loads(raw_response)
        
        # 生成场景描述和详细报告
        scene_description = generate_scene_description(parsed)
        detailed_report = generate_detailed_report(parsed, str(video_path))
        
        return {
            "video_path": str(video_path),
            "model": model,
            "annotation": parsed,
            "scene_description": scene_description,
            "report": detailed_report,
            "raw_response": raw_response,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "video_path": str(video_path),
            "model": model,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def analyze_directory(
    video_dir: Path,
    api_key: str,
    model: str,
    output_dir: Path,
    one_file_per_video: bool = False,
    max_mb: int = 80,
    timeout_s: int = 300,
    max_retries: int = 3,
    resume: bool = False,
) -> List[Dict[str, Any]]:
    """
    分析目录中的所有视频文件
    
    Args:
        video_dir: 视频目录路径
        api_key: API 密钥
        model: 模型 ID
        output_dir: 输出目录路径
        one_file_per_video: 每个视频保存为一个文件
        max_mb: 最大文件大小（MB）
        timeout_s: 超时时间（秒）
        max_retries: 最大重试次数
        resume: 是否断点续传
        
    Returns:
        所有分析结果列表
    """
    videos = [p for p in video_dir.rglob("*") if p.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS]
    
    if not videos:
        print(f"警告：在 {video_dir} 中未找到视频文件")
        return []
    
    # 断点续传：加载已处理的视频
    processed_videos = set()
    if resume:
        if one_file_per_video:
            # 检查输出目录中已存在的文件
            for video_path in videos:
                output_file = output_dir / f"{video_path.stem}.json"
                if output_file.exists():
                    processed_videos.add(str(video_path))
        else:
            # 检查 results.jsonl 文件
            results_file = output_dir / "results.jsonl"
            if results_file.exists():
                processed_videos = load_processed_videos(results_file)
        if processed_videos:
            print(f"断点续传：已跳过 {len(processed_videos)} 个已处理的视频")
    
    # 过滤已处理的视频
    videos_to_process = [v for v in videos if str(v) not in processed_videos]
    
    if not videos_to_process:
        print("所有视频已处理完成")
        return []
    
    results = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with tqdm(videos_to_process, desc="分析视频") as pbar:
        for video_path in pbar:
            pbar.set_postfix({"video": video_path.name[:30]})
            
            result = analyze_video(
                video_path=video_path,
                api_key=api_key,
                model=model,
                max_mb=max_mb,
                timeout_s=timeout_s,
                max_retries=max_retries,
            )
            results.append(result)
            
            # 保存结果
            if one_file_per_video:
                # 每个视频保存为一个单独的文件
                output_file = output_dir / f"{video_path.stem}.json"
                with output_file.open("w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            else:
                # 所有视频保存到一个文件
                results_file = output_dir / "results.jsonl"
                with results_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    return results


def generate_summary_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    生成汇总报告
    
    Args:
        results: 所有分析结果
        
    Returns:
        汇总报告字典
    """
    total = len(results)
    successful = sum(1 for r in results if "error" not in r and not r.get("skipped"))
    failed = sum(1 for r in results if "error" in r)
    skipped = sum(1 for r in results if r.get("skipped"))
    
    # 统计违规情况
    all_violations = []
    ppe_compliance = {"helmet": 0, "insulating_clothing": 0, "insulating_gloves": 0}
    sequence_compliance = 0
    
    for r in results:
        if "report" in r:
            report = r["report"]
            
            # PPE 统计
            ppe = r.get("annotation", {}).get("ppe", {})
            if ppe.get("helmet"):
                ppe_compliance["helmet"] += 1
            if ppe.get("insulating_clothing"):
                ppe_compliance["insulating_clothing"] += 1
            if ppe.get("insulating_gloves"):
                ppe_compliance["insulating_gloves"] += 1
            
            # 顺序合规统计
            if report.get("sequence_valid"):
                sequence_compliance += 1
            
            # 违规记录
            if report.get("violations"):
                all_violations.append({
                    "video": r["video_path"],
                    "violations": report["violations"],
                })
    
    return {
        "summary": {
            "total_videos": total,
            "successful_analyses": successful,
            "failed_analyses": failed,
            "skipped_videos": skipped,
            "success_rate": f"{successful/total*100:.1f}%" if total > 0 else "0%",
        },
        "ppe_compliance": {
            "helmet": f"{ppe_compliance['helmet']}/{successful}",
            "insulating_clothing": f"{ppe_compliance['insulating_clothing']}/{successful}",
            "insulating_gloves": f"{ppe_compliance['insulating_gloves']}/{successful}",
        },
        "sequence_compliance": f"{sequence_compliance}/{successful}",
        "violations": all_violations,
        "timestamp": datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(
        description="电力高压柜安全操作视频分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析单个视频
  python main.py --video video.mp4 --api_key YOUR_KEY
  
  # 分析整个目录
  python main.py --video_dir ./videos --api_key YOUR_KEY
  
  # 断点续传
  python main.py --video_dir ./videos --resume --api_key YOUR_KEY
  
  # 指定模型
  python main.py --video_dir ./videos --model kimi --api_key YOUR_KEY
        """,
    )
    
    parser.add_argument("--video", type=str, help="单个视频文件路径")
    parser.add_argument("--video_dir", type=str, help="视频目录路径")
    parser.add_argument("--out_dir", type=str, default="output", help="输出目录路径")
    parser.add_argument("--summary", type=str, default="output/summary.json", help="汇总报告路径")
    parser.add_argument(
        "--one_file_per_video",
        action="store_true",
        help="每个视频保存为一个单独的文件（默认：所有视频保存到一个文件）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="kimi",
        help="模型名称（kimi 或 kimi-vision）",
    )
    parser.add_argument("--api_key", type=str, default="", help="OpenRouter API 密钥")
    parser.add_argument("--max_mb", type=int, default=80, help="最大视频文件大小（MB）")
    parser.add_argument("--timeout", type=int, default=300, help="API 请求超时时间（秒）")
    parser.add_argument("--retries", type=int, default=3, help="最大重试次数")
    parser.add_argument(
        "--output_format",
        type=str,
        choices=["jsonl", "json"],
        default="jsonl",
        help="输出格式：jsonl 或 json",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="断点续传（跳过已处理的视频）",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式（仅输出错误信息）",
    )
    
    args = parser.parse_args()
    
    # 获取 API 密钥
    api_key = args.api_key or API_KEY
    if not api_key:
        raise SystemExit("错误：缺少 API 密钥。请设置 OPENROUTER_API_KEY 环境变量或使用 --api_key 参数。")
    
    if not args.video and not args.video_dir:
        raise SystemExit("错误：请指定 --video 或 --video_dir 参数。")
    
    # 解析模型名称
    from config import AVAILABLE_MODELS
    model = args.model
    if model in AVAILABLE_MODELS:
        model = AVAILABLE_MODELS[model]
    
    if not args.quiet:
        print(f"使用模型：{model}")
        print(f"API 密钥：{'*' * 8}{api_key[-4:] if len(api_key) > 4 else api_key}")
    
    # 单个视频分析
    if args.video:
        video_path = Path(args.video)
        if not video_path.exists():
            raise SystemExit(f"错误：视频文件不存在：{video_path}")
        
        if not args.quiet:
            print(f"\n分析视频：{video_path}")
        
        result = analyze_video(
            video_path=video_path,
            api_key=api_key,
            model=model,
            max_mb=args.max_mb,
            timeout_s=args.timeout,
            max_retries=args.retries,
        )
        
        # 输出结果
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        if not args.quiet:
            print(f"\n结果已保存至：{output_path}")
            
            # 打印场景描述
            if "scene_description" in result:
                print(f"\n场景描述:\n{result['scene_description']}")
            
            if "error" in result:
                print(f"\n错误：{result['error']}")
    
    # 目录批量分析
    else:
        video_dir = Path(args.video_dir)
        if not video_dir.exists():
            raise SystemExit(f"错误：视频目录不存在：{video_dir}")
        
        output_dir = Path(args.out_dir)
        summary_path = Path(args.summary)
        
        if not args.quiet:
            print(f"\n分析目录：{video_dir}")
            print(f"输出目录：{output_dir}")
        
        # 分析目录
        results = analyze_directory(
            video_dir=video_dir,
            api_key=api_key,
            model=model,
            output_dir=output_dir,
            one_file_per_video=args.one_file_per_video,
            max_mb=args.max_mb,
            timeout_s=args.timeout,
            max_retries=args.retries,
            resume=args.resume,
        )
        
        if not results:
            print("没有视频需要处理")
            return
        
        # 生成汇总报告
        summary = generate_summary_report(results)
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        if not args.quiet:
            print(f"\n结果已保存至：{output_dir}")
            print(f"汇总报告：{summary_path}")
            print(f"\n统计:\n{json.dumps(summary['summary'], ensure_ascii=False, indent=2)}")
            print(f"\nPPE 合规:\n{json.dumps(summary['ppe_compliance'], ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    # 修复 Windows 控制台编码问题
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    
    main()
