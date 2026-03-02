"""
电力高压柜安全操作视频分析系统
使用 Moonshot API 和 Kimi 模型进行视频分析
用于电力站视频辨识 Benchmark：输出 JSON 标注 + 自然语言场景描述
"""
import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# 加载 .env 文件（在导入 OpenAI 之前）
try:
    from dotenv import load_dotenv
    _project_root = Path(__file__).parent
    for _env_path in [_project_root / ".env", _project_root / "configs" / ".env"]:
        if _env_path.exists():
            load_dotenv(dotenv_path=_env_path)
            break
except ImportError:
    pass

# 导入场景描述生成器（将 JSON 标注转为自然语言）
_src_path = Path(__file__).parent / "src"
if _src_path.exists():
    sys.path.insert(0, str(_src_path))
try:
    from scene_description import generate_scene_description, generate_detailed_report
except ImportError:
    generate_scene_description = None
    generate_detailed_report = None

from openai import OpenAI


def _get_api_key() -> str:
    return os.environ.get("MOONSHOT_API_KEY", "").strip()


# 使用 Moonshot 官方 API（延迟初始化，确保先加载 .env）
def _get_client():
    return OpenAI(
        api_key=_get_api_key(),
        base_url="https://api.moonshot.cn/v1",
    )


# 工业级 Prompt（中文理解 + 英文结构输出，用于电力站视频辨识 Benchmark）
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

USER_PROMPT_TEXT = """请分析提供的视频。

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
      "object": string,
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


def upload_video(video_path: Path) -> str:
    """
    上传视频到 Moonshot
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        文件 ID（格式：ms://...）
    """
    print(f"  上传视频：{video_path.name}")
    file_object = _get_client().files.create(file=video_path, purpose="video")
    return f"ms://{file_object.id}"


def analyze_video(video_path: Path, model: str = "kimi-k2.5") -> Dict[str, Any]:
    """
    分析单个视频
    
    Args:
        video_path: 视频文件路径
        model: 模型名称
        
    Returns:
        分析结果字典
    """
    try:
        # 上传视频
        video_url = upload_video(video_path)
        
        # 调用 API
        print(f"  分析视频：{video_path.name}")
        completion = _get_client().chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "video_url",
                            "video_url": {"url": video_url}
                        },
                        {
                            "type": "text",
                            "text": USER_PROMPT_TEXT
                        }
                    ]
                }
            ]
        )
        
        # 解析响应
        raw_response = completion.choices[0].message.content
        
        # 提取 JSON（支持被 markdown 或说明文字包裹）
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(raw_response)
        
        # 生成自然语言场景描述（Benchmark 最终回答格式）
        result = {
            "video_path": str(video_path),
            "model": model,
            "annotation": parsed,
            "raw_response": raw_response,
            "timestamp": datetime.now().isoformat(),
        }
        if generate_scene_description and generate_detailed_report:
            try:
                result["scene_description"] = generate_scene_description(parsed)
                result["report"] = generate_detailed_report(parsed, str(video_path))
            except Exception as e:
                result["scene_description_error"] = str(e)
        
        return result
    except Exception as e:
        return {
            "video_path": str(video_path),
            "model": model,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def analyze_directory(
    video_dir: Path,
    output_dir: Path,
    model: str = "kimi-k2.5",
    one_file_per_video: bool = False,
    resume: bool = False,
) -> List[Dict[str, Any]]:
    """
    分析目录中的所有视频
    
    Args:
        video_dir: 视频目录路径
        output_dir: 输出目录路径
        model: 模型名称
        one_file_per_video: 每个视频保存为一个文件
        resume: 断点续传
        
    Returns:
        所有分析结果列表
    """
    from tqdm import tqdm
    
    video_extensions = {".mp4", ".mov", ".webm", ".mpeg", ".mpg", ".m4v", ".avi"}
    videos = [p for p in video_dir.rglob("*") if p.suffix.lower() in video_extensions]
    
    if not videos:
        print(f"警告：在 {video_dir} 中未找到视频文件")
        return []
    
    # 断点续传
    processed_videos = set()
    if resume:
        if one_file_per_video:
            for video_path in videos:
                output_file = output_dir / f"{video_path.stem}.json"
                if output_file.exists():
                    processed_videos.add(str(video_path))
        else:
            results_file = output_dir / "results.jsonl"
            if results_file.exists():
                with results_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                record = json.loads(line)
                                if "video_path" in record:
                                    processed_videos.add(record["video_path"])
                            except Exception:
                                pass
        if processed_videos:
            print(f"断点续传：已跳过 {len(processed_videos)} 个已处理的视频")
    
    videos_to_process = [v for v in videos if str(v) not in processed_videos]
    
    if not videos_to_process:
        print("所有视频已处理完成")
        return []
    
    results = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with tqdm(videos_to_process, desc="分析视频") as pbar:
        for video_path in pbar:
            pbar.set_postfix({"video": video_path.name[:30]})
            
            result = analyze_video(video_path, model)
            results.append(result)
            
            # 保存结果
            if one_file_per_video:
                output_file = output_dir / f"{video_path.stem}.json"
                with output_file.open("w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            else:
                results_file = output_dir / "results.jsonl"
                with results_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="电力高压柜安全操作视频分析系统（Moonshot API）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析单个视频
  python moonshot_analyze.py --video video.mp4
  
  # 分析整个目录
  python moonshot_analyze.py --video_dir sources_video
  
  # 每个视频保存为单独的文件
  python moonshot_analyze.py --video_dir sources_video --one_file_per_video
  
  # 断点续传
  python moonshot_analyze.py --video_dir sources_video --resume
  
  # 指定模型
  python moonshot_analyze.py --video_dir sources_video --model kimi-k2.5
        """,
    )
    
    parser.add_argument("--video", type=str, help="单个视频文件路径")
    parser.add_argument("--video_dir", type=str, help="视频目录路径")
    parser.add_argument("--out_dir", type=str, default="output", help="输出目录路径")
    parser.add_argument("--summary", type=str, default="output/summary.json", help="汇总报告路径")
    parser.add_argument(
        "--one_file_per_video",
        action="store_true",
        help="每个视频保存为一个单独的文件",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="kimi-k2.5",
        help="Moonshot 模型名称（默认：kimi-k2.5）",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="断点续传",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式",
    )
    
    args = parser.parse_args()
    
    # 检查 API 密钥
    api_key = _get_api_key()
    if not api_key:
        raise SystemExit(
            "错误：缺少 MOONSHOT_API_KEY。\n"
            "请任选其一：\n"
            "  1. 在 configs/.env 中填写 MOONSHOT_API_KEY=你的密钥\n"
            "  2. 或设置环境变量：$env:MOONSHOT_API_KEY=\"你的密钥\"\n"
            "获取密钥：https://platform.moonshot.cn/"
        )
    
    # 单个视频分析
    if args.video:
        video_path = Path(args.video)
        if not video_path.exists():
            raise SystemExit(f"错误：视频文件不存在：{video_path}")
        
        if not args.quiet:
            print(f"\n分析视频：{video_path}")
        
        result = analyze_video(video_path, args.model)
        
        # 输出结果
        if args.one_file_per_video:
            output_file = Path(args.out_dir) / f"{video_path.stem}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            if not args.quiet:
                print(f"\n结果已保存至：{output_file}")
        else:
            output_file = Path(args.out_dir) / "results.jsonl"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
            if not args.quiet:
                print(f"\n结果已保存至：{output_file}")
        
        # 打印场景描述
        if "scene_description" in result and not args.quiet:
            print(f"\n场景描述:\n{result['scene_description']}")
        
        if "error" in result and not args.quiet:
            print(f"\n错误：{result['error']}")
    
    # 目录批量分析
    elif args.video_dir:
        video_dir = Path(args.video_dir)
        if not video_dir.exists():
            raise SystemExit(f"错误：视频目录不存在：{video_dir}")
        
        output_dir = Path(args.out_dir)
        
        if not args.quiet:
            print(f"\n分析目录：{video_dir}")
            print(f"输出目录：{output_dir}")
            print(f"使用模型：{args.model}")
        
        results = analyze_directory(
            video_dir=video_dir,
            output_dir=output_dir,
            model=args.model,
            one_file_per_video=args.one_file_per_video,
            resume=args.resume,
        )
        
        if not results:
            print("没有视频需要处理")
            return
        
        # 生成汇总报告
        total = len(results)
        successful = sum(1 for r in results if "error" not in r)
        failed = sum(1 for r in results if "error" in r)
        
        summary = {
            "summary": {
                "total_videos": total,
                "successful_analyses": successful,
                "failed_analyses": failed,
                "success_rate": f"{successful/total*100:.1f}%" if total > 0 else "0%",
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        summary_path = Path(args.summary)
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        if not args.quiet:
            print(f"\n结果已保存至：{output_dir}")
            print(f"汇总报告：{summary_path}")
            print(f"\n统计:\n{json.dumps(summary['summary'], ensure_ascii=False, indent=2)}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    # 修复 Windows 控制台编码
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    
    main()