#!/bin/bash
set -e

VENV="/media/sampk/512GB/uv_envs/whisper"
INPUT="$1"

if [ -z "$INPUT" ]; then
    echo "usage: ./run_transcribe.sh <video_or_audio_file>"
    exit 1
fi

source "$VENV/bin/activate"
trap 'deactivate' EXIT

python3 - "$INPUT" << 'PYEOF'
import sys, time, subprocess, shutil
from faster_whisper import WhisperModel

video = sys.argv[1]
device = "cuda"
compute_type = "int8"
model_size = "small"

def gpu_stats():
    if shutil.which("nvidia-smi") is None:
        return "nvidia-smi not found"
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True
    ).stdout.strip()
    name, mem_used, mem_total, util = [x.strip() for x in out.split(",")]
    return f"{name} | VRAM {mem_used}/{mem_total} MiB | util {util}%"

print(f"model     : {model_size}")
print(f"device    : {device} ({compute_type})")
print(f"gpu       : {gpu_stats()}")
print(f"file      : {video}")
print("-" * 60)

t0 = time.time()
model = WhisperModel(model_size, device=device, compute_type=compute_type)
segments, info = model.transcribe(video, vad_filter=True)

total = info.duration

def fmt(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    ms = int((s - int(s)) * 1000)
    return f"{int(h):02}:{int(m):02}:{int(s):02},{ms:03}"

def bar(pct, width=30):
    filled = int(width * pct / 100)
    return "#" * filled + "-" * (width - filled)

out_path = video.rsplit(".", 1)[0] + ".srt"
with open(out_path, "w") as f:
    for i, seg in enumerate(segments, 1):
        f.write(f"{i}\n{fmt(seg.start)} --> {fmt(seg.end)}\n{seg.text.strip()}\n\n")
        pct = min(100.0, seg.end / total * 100)
        elapsed = time.time() - t0
        speed = seg.end / elapsed if elapsed > 0 else 0
        sys.stdout.write(
            f"\r[{bar(pct)}] {pct:5.1f}% | {fmt(seg.end)}/{fmt(total)} "
            f"| {speed:4.1f}x realtime | {gpu_stats()}"
        )
        sys.stdout.flush()

print()
print(f"done -> {out_path} ({time.time()-t0:.1f}s total)")
PYEOF
