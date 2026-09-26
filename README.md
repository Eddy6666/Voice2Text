# Voice2Text

本地语音转文本工具，基于 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)，无需联网、无需鉴权，一键把视频/音频中的语音转成带时间戳的文字稿。

## 功能

- 🎙️ 支持视频（mp4/mov/mkv/avi/flv/wmv/webm）和音频（mp3/m4a/wav/flac/ogg/aac）
- 💻 完全本地运行，不上传任何数据到云端
- 🚀 一键启动，图形界面操作
- 📝 自动输出两个文件：
  - `原名_字幕_带时间戳.txt`：每段话的起止时间 + 文字
  - `原名_字幕_纯文本.txt`：整段连贯文字稿
- 🌏 自动检测语言，支持中英混合识别

## 安装

### 前置要求

- Windows 系统
- Python 3.10 ~ 3.13（[下载地址](https://www.python.org/downloads/)）

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/Eddy6666/Voice2Text.git
cd Voice2Text

# 2. 创建虚拟环境
python -m venv venv

# 3. 安装依赖
venv\Scripts\pip install faster-whisper
```

### 下载模型（首次）

推荐用 base 模型（约 140MB），手动下载到 `models/base/` 目录：

从 [hf-mirror.com](https://hf-mirror.com/Systran/faster-whisper-base) 或 [HuggingFace](https://huggingface.co/Systran/faster-whisper-base) 下载以下文件：

- `config.json`
- `model.bin`
- `tokenizer.json`
- `vocabulary.txt`

目录结构：
```
models/base/
├── config.json
├── model.bin
├── tokenizer.json
└── vocabulary.txt
```

> 如果网络可以直接访问 HuggingFace，程序首次运行会自动下载模型。

### 模型大小选择

| 模型 | 大小 | 速度 | 准确率 |
|------|------|------|--------|
| base | ~140MB | 最快 | 一般 |
| small | ~460MB | 中等 | 较好 |
| medium | ~1.5GB | 较慢 | 好 |
| large-v3 | ~3GB | 慢 | 最好 |

默认使用 base 模型，平衡速度与准确率。

## 使用

双击 `一键启动.bat`，或命令行运行：

```bash
venv\Scripts\pythonw asr_tool.py
```

操作步骤：
1. 点「选择文件」选视频/音频
2. 选择模型大小（默认 base）
3. 点「开始转写」
4. 完成后字幕文件自动生成在原文件同目录

## 目录结构

```
Voice2Text/
├── asr_tool.py          # 主程序（GUI）
├── 一键启动.bat         # Windows 启动器
├── 使用说明.txt
├── README.md
├── .gitignore
├── venv/               # 虚拟环境（不进 git）
└── models/
    └── base/           # 模型文件（不进 git）
```

## 性能参考

CPU（无 GPU）上 base 模型约为实时速度的 3-5 倍，49 分钟视频约 3-5 分钟转完。

## License

MIT
