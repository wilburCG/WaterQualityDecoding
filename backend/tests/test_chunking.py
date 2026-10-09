"""M3 中文分块逻辑测试（无外部依赖）。"""
from app.core.rag import chunk_text


def test_empty():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_short_text_single_chunk():
    text = "这是一个短段落。"
    chunks = chunk_text(text)
    assert chunks == [text]


def test_paragraphs_grouped():
    paras = [f"这是第{i}段，内容不算太长。" for i in range(10)]
    chunks = chunk_text("\n\n".join(paras), size=60, overlap=0)
    assert len(chunks) >= 2
    # 不丢内容：所有段落都应完整出现在分块中（按段落边界切分）
    for p in paras:
        assert any(p in c for c in chunks)


def test_long_paragraph_hard_split():
    text = "字" * 1000
    chunks = chunk_text(text, size=300, overlap=0)
    assert all(len(c) <= 300 for c in chunks)
    assert sum(len(c) for c in chunks) == 1000


def test_overlap_present():
    text = "\n\n".join(["段落内容一二三四五六七八。" * 20] * 4)
    chunks = chunk_text(text, size=100, overlap=20)
    assert len(chunks) >= 2
    # 相邻块应有重叠内容
    assert chunks[0][-10:] in chunks[1]
