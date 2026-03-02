#!/bin/bash
# 电力高压柜安全操作视频分析系统 - Linux/Mac 启动脚本

echo "========================================"
echo "电力高压柜安全操作视频分析系统"
echo "========================================"
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 检查依赖
if ! python3 -c "import requests" 2>/dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 检查 API 密钥
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "警告: 未设置 OPENROUTER_API_KEY 环境变量"
    echo "请设置环境变量或在命令行中使用 --api_key 参数"
fi

# 运行分析
echo
echo "使用方法:"
echo "  单个视频: ./run.sh --video video.mp4"
echo "  目录批量: ./run.sh --video_dir ./sources_video"
echo
echo "完整参数说明请运行: ./run.sh --help"
echo

if [ $# -eq 0 ]; then
    echo "显示帮助信息:"
    python3 src/main.py --help
else
    python3 src/main.py "$@"
fi