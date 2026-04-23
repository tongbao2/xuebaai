$ErrorActionPreference = "Continue"
Set-Location "C:\Users\iMac\.qclaw\workspace-agent-7ec9d5d2\study-ai"
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }

Write-Host "[PyInstaller] 打包中（约 2-5 分钟）..." -ForegroundColor Cyan
pyinstaller `
    --name "学霸帝AI" `
    --onefile `
    --windowed `
    --distpath "dist" `
    --workpath "build" `
    --add-data "config.py;." `
    --add-data "llama_client.py;." `
    --hidden-import requests `
    --hidden-import customtkinter `
    --collect-all customtkinter `
    --exclude-module torch `
    --exclude-module torchvision `
    --exclude-module transformers `
    --exclude-module tensorflow `
    --exclude-module tensorboard `
    --exclude-module sympy `
    --exclude-module matplotlib `
    --exclude-module scipy `
    --exclude-module scikit-learn `
    --exclude-module sklearn `
    --exclude-module paddle `
    --exclude-module paddleocr `
    --noconfirm `
    "app.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] PyInstaller exit $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "[OK] 打包完成，复制运行时文件..." -ForegroundColor Green

$DIST = "C:\Users\iMac\.qclaw\workspace-agent-7ec9d5d2\study-ai\dist"
$LLAMA = "C:\Users\iMac\.qclaw\workspace-agent-7ec9d5d2\study-ai\llama.cpp"

Copy-Item $LLAMA "$DIST\llama.cpp" -Recurse -Force
New-Item -ItemType Directory -Path "$DIST\models" -Force | Out-Null
Copy-Item "config.py" "$DIST\" -Force
Copy-Item "llama_client.py" "$DIST\" -Force

$readme = @"
学霸帝AI - 使用说明
=========================

【首次使用】
1. 运行 学霸帝AI.exe
2. 点击「下载模型」下载 GGUF 模型（约 3GB）
3. 点击「加载模型」（首次约 30 秒）
4. 开始对话！

【手动下载模型】
将 GGUF 文件放到 dist\models\ 文件夹中：
  Gemma: https://www.modelscope.cn/models/unsloth/gemma-4-E2B-it-GGUF/resolve/master/gemma-4-E2B-it-Q4_K_M.gguf
  Qwen:  https://www.modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_k_m.gguf

【显卡加速】
下载 CUDA 版 llama-server.exe 替换 dist\llama.cpp\llama-server.exe
  https://github.com/ggml-org/llama.cpp/releases

【快捷键】
  Ctrl+Enter 发送
  ⏹ 停止生成
"@
$readme | Out-File -FilePath "$DIST\使用说明.txt" -Encoding UTF8

$exe = "$DIST\学霸帝AI.exe"
if (Test-Path $exe) {
    $sz = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  构建完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  EXE: $exe" -ForegroundColor Cyan
    Write-Host "  大小: $sz MB" -ForegroundColor Cyan
    Write-Host ""
    explorer $DIST
} else {
    Write-Host "[ERROR] 未找到 EXE" -ForegroundColor Red
}
