"""
视频帧提取工具
将视频转换为关键帧图片，用于 VLM 分析
"""
import subprocess
from pathlib import Path
from typing import List, Optional


def extract_frames(
    video_path: Path,
    output_dir: Path,
    fps: float = 0.5,  # 每秒提取的帧数
    max_frames: int = 20,
) -> List[Path]:
    """
    从视频中提取关键帧
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        fps: 每秒提取的帧数（默认 0.5，即每 2 秒 1 帧）
        max_frames: 最大帧数
        
    Returns:
        提取的帧文件路径列表
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成输出文件名模式
    output_pattern = output_dir / f"{video_path.stem}_%03d.jpg"
    
    # 使用 ffmpeg 提取帧
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-q:v", "2",  # 高质量 JPEG
        "-frames:v", str(max_frames),
        "-y",  # 覆盖已存在的文件
        str(output_pattern),
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # 返回提取的帧文件
        frames = sorted(output_dir.glob(f"{video_path.stem}_*.jpg"))
        return list(frames)[:max_frames]
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg 错误：{e.stderr}")
        raise
    except FileNotFoundError:
        raise RuntimeError(
            "未找到 ffmpeg。请安装 ffmpeg:\n"
            "  Windows: choco install ffmpeg\n"
            "  Linux: sudo apt install ffmpeg\n"
            "  Mac: brew install ffmpeg"
        )


def get_video_duration(video_path: Path) -> float:
    """获取视频时长（秒）"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"FFprobe 错误：{e}")
        return 0.0


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python extract_frames.py <video_file>")
        sys.exit(1)
    
    video_path = Path(sys.argv[1])
    if not video_path.exists():
        print(f"视频文件不存在：{video_path}")
        sys.exit(1)
    
    output_dir = video_path.parent / "frames"
    
    print(f"视频时长：{get_video_duration(video_path):.2f} 秒")
    frames = extract_frames(video_path, output_dir)
    print(f"提取了 {len(frames)} 帧")
    print(f"输出目录：{output_dir}")