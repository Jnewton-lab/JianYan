# 语音转文字工具（Windows）

## 适合谁
- 需要在 Windows 上用快捷键快速“语音转文字 + 规整输出”的用户

## 功能概览
- AI 自动去口水/去重复，让语音更精炼，不用担心啰唆废话
- `Ctrl+Shift+Space` 开始/停止录音
- 本地 SenseVoice Small 转写
- OpenAI 兼容模型进行整理（推荐 Qwen）
- 自动粘贴到当前光标位置

## 安装（推荐安装包）
### 准备
1) 下载 Python 安装包 `python-3.10.13-amd64.exe` 放到 `installer/`
2) 安装 Inno Setup

### 构建安装包（开发者）
1) 用 Inno Setup 打开并编译：`installer\setup.iss`
2) 生成安装包：`installer\output\AudioToTextSetup.exe`

### 用户安装流程
1) 下载并运行安装包
2) 选择普通可写目录（如 `D:\Apps` 或 `D:\Tools`），不要选系统保护目录（如 `C:\Program Files`）
3) 安装过程中自动检测 NVIDIA 驱动：
   - 有驱动：安装 CUDA 版依赖
   - 无驱动：提示是否继续安装 CPU 版
4) 安装阶段自动下载模型并显示只读进度输出，预计 5–20 分钟（取决于网速）
5) 安装完成即可使用

### 开发者快速安装（RTX 显卡）
**前提**：已安装 Python 3.10 + NVIDIA 驱动

```cmd
# 一键安装（推荐）
install.cmd

# 或手动安装
py -3.10 -m venv .venv
.\.venv\Scripts\activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
python scripts\predownload_models.py
```


## 启动方式
- 开始菜单/桌面图标
- 或运行：`run_app.cmd`

## 设置（托盘右键）
- OpenAI Base URL
- OpenAI API Key
- 模型名（推荐 Qwen 系列）

## 模型说明
- SenseVoice Small 本地模型
- 模型缓存目录：安装目录下 `models/`
- 录音格式：WAV PCM 16kHz 单声道

## 空间与性能
- 安装依赖 + 模型缓存：约 6–10 GB
- GPU 显存占用：约 2–4 GB（含 VAD/标点）

## 常见问题
- 快捷键无效：请以管理员身份运行（`keyboard` 库需要高权限）
- 安装失败：确认 Python 安装包放在 `installer/`，以及网络可用
- AMD 显卡：将使用 CPU 版本运行，转写速度较慢（约 10-30 秒），但功能完整
