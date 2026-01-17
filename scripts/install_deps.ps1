param(
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
}

$Py = Join-Path $VenvPath "Scripts\python.exe"

& $Py -m pip install --upgrade pip

Write-Host "Checking NVIDIA driver (nvidia-smi) ..."
$hasNvidia = $false
try {
    $null = & nvidia-smi 2>$null
    $hasNvidia = $true
} catch {
    $hasNvidia = $false
}

if (-not $hasNvidia) {
    Write-Host "No NVIDIA driver detected. CUDA build may fail, will fall back to CPU."
}

Write-Host "Installing PyTorch (CUDA 11.8) ..."
$cudaOk = $true
try {
    & $Py -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
} catch {
    $cudaOk = $false
}

if (-not $cudaOk) {
    Write-Host "CUDA build failed, falling back to CPU build ..."
    & $Py -m pip install torch torchaudio
}

& $Py -m pip install funasr modelscope

Write-Host "Installing sentencepiece (stable version) ..."
& $Py -m pip install sentencepiece==0.1.99

Write-Host "Verifying torch cuda availability ..."
try {
    & $Py - << 'PY'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
PY
} catch {
    Write-Host "Torch verification failed."
}

Write-Host "Done."
