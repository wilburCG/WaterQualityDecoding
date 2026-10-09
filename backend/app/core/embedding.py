"""本地中文嵌入模型（bge-small-zh ONNX），进程内单例。"""
import os

from functools import lru_cache

from app.config import get_settings


@lru_cache
def _model():
    # 首次加载从镜像站拉取权重；禁用 xet（镜像站不代理 xet 存储）
    settings = get_settings()
    os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [vec.tolist() for vec in _model().embed(texts)]


def embed_one(text: str) -> list[float]:
    return embed_texts([text])[0]
