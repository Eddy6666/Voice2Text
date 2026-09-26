# -*- coding: utf-8 -*-
"""
语音转文本工具（本地版）
基于 faster-whisper，完全本地运行，无需联网鉴权。
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 让模型缓存也放在本工具目录下，完全自包含
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("HF_HOME", os.path.join(BASE_DIR, "models"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", os.path.join(BASE_DIR, "models"))
# 国内镜像，首次下载模型用；下完后可离线运行
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

SUPPORTED_EXTS = (
    ".mp4", ".flv", ".ts", ".avi", ".mov", ".wmv", ".mkv", ".webm",
    ".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg",
)
MODEL_CHOICES = ["base", "small", "medium", "large-v3"]
DEFAULT_MODEL = "base"

# 本地已下载的模型目录映射（避免再走网络）
LOCAL_MODELS = {
    "base": os.path.join(BASE_DIR, "models", "base"),
}


def fmt_ts(t):
    m = int(t // 60)
    s = t - m * 60
    return "%02d:%05.2f" % (m, s)


def do_transcribe(media_path, model_name, log, progress_cb):
    from faster_whisper import WhisperModel

    log(f"加载模型 {model_name} ...")
    progress_cb(5, "加载模型中")
    local_path = LOCAL_MODELS.get(model_name)
    if local_path and os.path.isdir(local_path):
        log(f"使用本地模型: {local_path}")
        model = WhisperModel(local_path, device="cpu", compute_type="int8")
    else:
        log("本地未找到，尝试从网络下载（需要联网）...")
        model = WhisperModel(model_name, device="cpu", compute_type="int8")

    log("开始识别（本地 CPU 运行，请耐心等待）...")
    progress_cb(10, "识别中")

    segments, info = model.transcribe(
        media_path,
        beam_size=5,
        vad_filter=True,
    )
    log(f"检测到语言: {info.language} (置信度 {info.language_probability:.2f})")
    log(f"音频时长约: {info.duration:.1f} 秒")

    ts_path = os.path.splitext(media_path)[0] + "_字幕_带时间戳.txt"
    plain_path = os.path.splitext(media_path)[0] + "_字幕_纯文本.txt"

    total = info.duration or 1
    count = 0
    with open(ts_path, "w", encoding="utf-8") as f_ts, \
         open(plain_path, "w", encoding="utf-8") as f_plain:
        f_ts.write("源文件: %s\n" % os.path.basename(media_path))
        f_ts.write("模型: %s\n" % model_name)
        f_ts.write("检测语言: %s\n" % info.language)
        f_ts.write("时长: %.1f 秒 (%.1f 分钟)\n" % (info.duration, info.duration / 60))
        f_ts.write("=" * 60 + "\n\n")

        for seg in segments:
            text = seg.text.strip()
            count += 1
            f_ts.write("[%s -> %s] %s\n" % (fmt_ts(seg.start), fmt_ts(seg.end), text))
            f_ts.flush()
            f_plain.write(text)
            f_plain.flush()
            pct = min(10 + int(seg.end / total * 85), 95)
            progress_cb(pct, "识别中 %.0f%%" % (seg.end / total * 100))
            log("[%s] %s" % (fmt_ts(seg.start), text))

    progress_cb(100, "完成")
    log("完成！共 %d 段。" % count)
    log("输出：\n  %s\n  %s" % (ts_path, plain_path))
    return ts_path, plain_path


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("语音转文本（本地版）")
        self.geometry("760x560")
        self.resizable(True, True)
        self.file_path = tk.StringVar()
        self.model_name = tk.StringVar(value=DEFAULT_MODEL)
        self.worker = None
        self._out_dir = None
        self._build()

    def _build(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)
        ttk.Label(top, text="媒体文件：").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.file_path).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(top, text="选择文件", command=self.choose).pack(side=tk.LEFT)

        row2 = ttk.Frame(self, padding=(10, 0))
        row2.pack(fill=tk.X)
        ttk.Label(row2, text="模型大小：").pack(side=tk.LEFT)
        ttk.Combobox(row2, textvariable=self.model_name, values=MODEL_CHOICES,
                     state="readonly", width=10).pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, text="(small 平衡速度与准确率；medium 更准但更慢)",
                  foreground="#666").pack(side=tk.LEFT, padx=6)

        btns = ttk.Frame(self, padding=(10, 10))
        btns.pack(fill=tk.X)
        self.start_btn = ttk.Button(btns, text="开始转写", command=self.start)
        self.start_btn.pack(side=tk.LEFT)
        self.open_btn = ttk.Button(btns, text="打开输出目录",
                                    command=self.open_out, state=tk.DISABLED)
        self.open_btn.pack(side=tk.LEFT, padx=8)

        self.progress = ttk.Progressbar(self, maximum=100)
        self.progress.pack(fill=tk.X, padx=10)
        self.status = ttk.Label(self, text="就绪", anchor=tk.W)
        self.status.pack(fill=tk.X, padx=10, pady=(4, 0))

        self.log = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Consolas", 10))
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def choose(self):
        p = filedialog.askopenfilename(
            title="选择视频或音频文件",
            filetypes=[("媒体文件", "*.mp4 *.flv *.ts *.avi *.mov *.wmv *.mkv *.webm *.mp3 *.m4a *.wav *.aac *.flac *.ogg"),
                       ("所有文件", "*.*")],
        )
        if p:
            self.file_path.set(p)

    def append_log(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def set_progress(self, val, text):
        self.progress["value"] = val
        self.status.config(text=text)

    def start(self):
        p = self.file_path.get().strip()
        if not p or not os.path.exists(p):
            messagebox.showwarning("提示", "请先选择一个存在的视频/音频文件。")
            return
        self.start_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)
        self._out_dir = None
        self.log.delete("1.0", tk.END)
        model = self.model_name.get()
        self.worker = threading.Thread(target=self._run, args=(p, model), daemon=True)
        self.worker.start()

    def _run(self, p, model):
        try:
            ts_path, plain_path = do_transcribe(
                p, model,
                log=lambda m: self.after(0, self.append_log, m),
                progress_cb=lambda v, t: self.after(0, self.set_progress, v, t),
            )
            self._out_dir = os.path.dirname(ts_path)
            self.after(0, lambda: messagebox.showinfo(
                "完成", f"转写完成！\n\n带时间戳：{ts_path}\n纯文本：{plain_path}"))
        except Exception:
            import traceback
            err = traceback.format_exc()
            self.after(0, lambda: messagebox.showerror("出错了", err[-500:]))
            self.after(0, lambda: self.append_log("[错误] " + err))
        finally:
            self.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.after(0, lambda: self.open_btn.config(
                state=tk.NORMAL if self._out_dir else tk.DISABLED))

    def open_out(self):
        if self._out_dir and os.path.isdir(self._out_dir):
            os.startfile(self._out_dir)


if __name__ == "__main__":
    app = App()
    app.mainloop()
