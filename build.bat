@echo off
chcp 65001 >nul
echo ==========================================
echo   学霸帝AI - 构建脚本 (PyInstaller)
echo ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.9+
    echo   下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 确认在项目目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "PROJECT_DIR=%CD%"

echo [INFO] 项目目录: %PROJECT_DIR%
echo [INFO] Python:
python --version
echo.

:: ── Step 1: 安装 Python 依赖 ──────────────────────────
echo [Step 1/4] 安装 Python 依赖...
pip install --quiet requests customtkinter pyinstaller
if errorlevel 1 (
    echo [ERROR] 依赖安装失败，尝试 pip install requests customtkinter pyinstaller
    pause
    exit /b 1
)
echo [OK] 依赖安装完成
echo.

:: ── Step 2: 下载 llama.cpp CPU 版 ────────────────────
echo [Step 2/4] 检查 llama-server.exe...
set "LLAMA_DIR=%PROJECT_DIR%\llama.cpp"
set "LLAMA_EXE=%LLAMA_DIR%\llama-server.exe"

if exist "%LLAMA_EXE%" (
    echo [OK] llama-server.exe 已存在
) else (
    echo [Download] 正在下载 llama.cpp b8855 CPU版 (~15 MB)...
    if not exist "%LLAMA_DIR%" mkdir "%LLAMA_DIR%"
    
    :: 尝试 GitHub 源
    set "URL=https://github.com/ggml-org/llama.cpp/releases/download/b8855/llama-b8855-bin-win-cpu-x64.zip"
    echo   来源: %URL%
    
    curl.exe -L -o "%PROJECT_DIR%\llama-cpu.zip" --connect-timeout 30 --max-time 600 "%URL%"
    if errorlevel 1 (
        echo [WARNING] GitHub 下载失败，尝试 HuggingFace...
        curl.exe -L -o "%PROJECT_DIR%\llama-cpu.zip" --connect-timeout 30 --max-time 600 "https://huggingface.co/ggerganov/llama.cpp/resolve/b8855/llama-b8855-bin-win-cpu-x64.zip"
        if errorlevel 1 (
            echo [ERROR] llama.cpp 下载失败
            echo   请手动下载并解压到: %LLAMA_DIR%
            echo   链接: https://github.com/ggml-org/llama.cpp/releases
            pause
            exit /b 1
        )
    )
    
    echo [Extract] 解压 llama.cpp...
    powershell -Command "Expand-Archive -Path '%PROJECT_DIR%\llama-cpu.zip' -DestinationPath '%LLAMA_DIR%' -Force"
    del /f /q "%PROJECT_DIR%\llama-cpu.zip"
    
    :: 找解压后的 llama-server.exe
    for /r "%LLAMA_DIR%" %%f in (llama-server.exe) do (
        if not exist "%LLAMA_DIR%\llama-server.exe" (
            move "%%~dpfllama-server.exe" "%LLAMA_DIR%\" >nul 2>&1
        )
    )
    
    :: 整理目录：llama-server.exe 提到 llama.cpp 根目录
    for /r "%LLAMA_DIR%" %%f in (llama-server.exe) do (
        if /i not "%%~dpfx"=="%LLAMA_EXE%" (
            copy /y "%%f" "%LLAMA_DIR%\llama-server.exe" >nul 2>&1
        )
    )
)

if not exist "%LLAMA_EXE%" (
    echo [ERROR] 未找到 llama-server.exe
    echo   请手动下载并放到: %LLAMA_DIR%
    pause
    exit /b 1
)
echo [OK] llama-server.exe 就绪
echo.

:: ── Step 3: 运行 PyInstaller ─────────────────────────
echo [Step 3/4] 打包为 EXE（首次约2-3分钟）...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

pyinstaller ^
    --name "学霸帝AI" ^
    --onefile ^
    --windowed ^
    --icon NONE ^
    --add-data "%PROJECT_DIR%\config.py;." ^
    --add-data "%PROJECT_DIR%\llama_client.py;." ^
    --hidden-import requests ^
    --hidden-import customtkinter ^
    --collect-all customtkinter ^
    --noconfirm ^
    --distpath "%PROJECT_DIR%\dist" ^
    "%PROJECT_DIR%\app.py"

if errorlevel 1 (
    echo [ERROR] PyInstaller 打包失败
    pause
    exit /b 1
)
echo.

:: ── Step 4: 复制运行时文件到 dist ────────────────────
echo [Step 4/4] 复制运行时文件...
set "DIST_DIR=%PROJECT_DIR%\dist"

:: 复制 llama.cpp 目录
if exist "%DIST_DIR%\llama.cpp" rmdir /s /q "%DIST_DIR%\llama.cpp"
xcopy /e /i /y "%LLAMA_DIR%" "%DIST_DIR%\llama.cpp\" >nul 2>&1

:: 复制 models 目录结构
if not exist "%DIST_DIR%\models" mkdir "%DIST_DIR%\models"

:: 复制 config.py 和 llama_client.py
copy /y "%PROJECT_DIR%\config.py" "%DIST_DIR%\" >nul 2>&1
copy /y "%PROJECT_DIR%\llama_client.py" "%DIST_DIR%\" >nul 2>&1

:: 写入说明
(
echo 学霸帝AI  -  使用说明
echo ================================
echo.
echo 1. 【下载模型（请选择一个放入 models/ 目录）】
echo    - Qwen2.5-0.5B-IT Q4_K_M (~400MB)
echo      https://www.modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_k_m.gguf
echo    - DeepSeek-R1-Distill-Qwen-1.5B Q4_K_M (~900MB)
echo      https://www.modelscope.cn/models/unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/resolve/master/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf
echo.
echo 2. 【下载说明】
echo    如果自动下载失败，请复制上方链接手动下载
echo    将 .gguf 文件放到 models/ 目录中
echo.
echo 3. 【加载模型】
echo    模型下载完成后，点击"加载模型"
echo    首次加载约需 20-60 秒
echo.
echo 4. 【开始对话】
echo    模型加载完成后，直接输入问题即可
echo    Ctrl+Enter 也可发送消息
echo.
echo 5. 【显卡加速】
echo    如有 NVIDIA 显卡，可下载 CUDA 版 llama.cpp：
echo    llama-b8855-bin-win-cuda-12.4-x64.zip
echo    替换 llama.cpp 目录中的 llama-server.exe
echo.
) > "%DIST_DIR%\使用说明.txt"

echo.
echo ==========================================
echo   构建完成！
echo ==========================================
echo   EXE 路径: %DIST_DIR%\学霸帝AI.exe
echo   运行时文件: %DIST_DIR%\llama.cpp\
echo   模型目录: %DIST_DIR%\models\
echo.
echo   【首次使用必读】
echo   1. 启动 学霸帝AI.exe
echo   2. 下载模型到 models/ 目录（Qwen~400MB / DeepSeek~900MB）
echo   3. 模型下载完成后点击"加载模型"
echo   4. 开始对话！
echo ==========================================

explorer "%DIST_DIR%"
