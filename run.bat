@echo off
REM 电力高压柜安全操作视频分析系统 - Windows 启动脚本

echo ========================================
echo 电力高压柜安全操作视频分析系统
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
pip show requests >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

REM 检查 API 密钥
if "%OPENROUTER_API_KEY%"=="" (
    echo 警告: 未设置 OPENROUTER_API_KEY 环境变量
    echo 请设置环境变量或在命令行中使用 --api_key 参数
)

REM 运行分析
echo.
echo 使用方法:
echo   单个视频: run.bat --video video.mp4
echo   目录批量: run.bat --video_dir ./sources_video
echo.
echo 完整参数说明请运行: run.bat --help
echo.

if "%~1"=="" (
    echo 显示帮助信息:
    python src\main.py --help
) else (
    python src\main.py %*
)