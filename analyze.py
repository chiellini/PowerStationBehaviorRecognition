#!/usr/bin/env python
"""
电力高压柜安全操作视频分析系统 - 命令行入口
支持单视频和批量分析，带重试机制和断点续传功能
"""
import sys
import argparse
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 添加 src 目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from main import main as run_analysis


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="电力高压柜安全操作视频分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析单个视频
  python analyze.py --video video.mp4
  
  # 分析整个目录（所有视频保存到一个文件）
  python analyze.py --video_dir ./sources_video
  
  # 每个视频保存为单独的文件
  python analyze.py --video_dir ./sources_video --one_file_per_video
  
  # 断点续传
  python analyze.py --video_dir ./sources_video --resume
  
  # 指定模型
  python analyze.py --video_dir ./sources_video --model kimi-vision
  
  # 安静模式（仅输出错误）
  python analyze.py --video_dir ./sources_video --quiet
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
    
    # 调用主程序
    run_analysis()


if __name__ == "__main__":
    main()
