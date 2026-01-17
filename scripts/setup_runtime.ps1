param(
    [string]$InstallDir = (Get-Location).Path,
    [string]$ModelCacheDir = ""
)

$ErrorActionPreference = "Stop"
$LogPath = Join-Path $InstallDir "install.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Out-File -FilePath $LogPath -Encoding UTF8 -Append
}

Write-Log "InstallDir: $InstallDir"
Write-Host "检查运行环境..."

# 1. 优先检查自带的 .venv
$bundledVenvPython = Join-Path $InstallDir ".venv\Scripts\python.exe"
if (Test-Path $bundledVenvPython) {
    Write-Log "Found bundled venv at $bundledVenvPython"
    Write-Host "发现内置运行环境，跳过 Python 安装。"
    
    # 2. 检查模型是否齐全
    if ([string]::IsNullOrWhiteSpace($ModelCacheDir)) {
        $ModelCacheDir = Join-Path $InstallDir "models"
    }
    
    # 简单的存在性检查 (如果 models 目录存在且不为空)
    if ((Test-Path $ModelCacheDir) -and (Get-ChildItem $ModelCacheDir).Count -gt 0) {
        Write-Log "Models directory exists and is not empty. Skipping download."
        Write-Host "发现内置模型，跳过下载。"
    } else {
        Write-Log "Models directory missing or empty. Downloading..."
        Write-Host "未检测到模型，准备下载..."
        $env:MODELSCOPE_CACHE = $ModelCacheDir
        & $bundledVenvPython (Join-Path $InstallDir "scripts\predownload_models.py")
    }
    
    Write-Log "Setup completed (Bundled Mode)."
    Write-Host "环境验证完成。"
    exit 0
}

# --- 以下旧逻辑仅作为 fallback (备用)，但在全打包模式下通常不会走到这里 ---

[System.Windows.Forms.MessageBox]::Show(
    "安装包似乎损坏：未找到内置运行环境 (.venv)。请重新下载安装包。",
    "环境缺失",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Error
) | Out-Null
exit 1
