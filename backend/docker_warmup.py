"""镜像构建预热：从 hf-mirror 下载 bge-small-zh 到 fastembed 缓存目录并验证。"""
import os
import time

import requests

CACHE_DIR = "/tmp/fastembed_cache/fast-bge-small-zh-v1.5"
BASE = "https://hf-mirror.com/Qdrant/bge-small-zh-v1.5/resolve/main"
FILES = [
    "config.json",
    "model_optimized.onnx",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt",
]

os.makedirs(CACHE_DIR, exist_ok=True)

for name in FILES:
    dest = os.path.join(CACHE_DIR, name)
    url = f"{BASE}/{name}"
    last_err = None
    for attempt in range(6):
        try:
            with requests.get(url, stream=True, timeout=(20, 120)) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1 << 16):
                        f.write(chunk)
            print(f"fetched {name} ({os.path.getsize(dest)} bytes)")
            break
        except requests.RequestException as e:
            last_err = e
            time.sleep(3 * (attempt + 1))
    else:
        raise SystemExit(f"failed to download {name}: {last_err}")

# 验证 fastembed 能直接使用本地缓存
from fastembed import TextEmbedding

vec = list(TextEmbedding(model_name="BAAI/bge-small-zh-v1.5").embed(["预热"]))
assert len(vec[0]) == 512
print("warmup ok")
