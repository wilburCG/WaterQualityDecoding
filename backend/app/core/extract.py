# -*- coding: utf-8 -*-
"""M4 文件抽取：Excel/CSV（确定性）、PDF（文本+表格）、照片（视觉模型）。

设计原则：只"识别"，不"判定"。抽取结果回填表单，由用户人工核对后再生成报告。
"""
import io
import json
import re
from typing import Optional

# 指标别名 → code（匹配时统一小写、去空格和常见符号）
INDICATOR_ALIASES = {
    "ph": ["ph", "ph值", "酸碱度"],
    "wt": ["水温", "温度", "水温℃"],
    "do": ["溶解氧", "do", "溶氧", "溶解氧do"],
    "codmn": ["高锰酸盐指数", "codmn", "高锰酸盐", "cod", "高锰酸盐指数codmn"],
    "nh3n": ["氨氮", "nh3-n", "nh3n", "nh", "氨态氮", "nh₃-n", "氨氮nh3n"],
    "tp": ["总磷", "tp", "总磷tp"],
    "tn": ["总氮", "tn", "总氮tn"],
}

# 数字（支持 1.23 / .47 / 0,47 / 全角）
_NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def _norm_label(s: str) -> str:
    s = str(s).strip().lower()
    # 去掉空格、冒号、括号及常见下标符号，统一全角→半角
    s = s.replace("：", ":")
    s = re.sub(r"[\s()（）\[\]【】*#:：,，。.\-—_/\\]", "", s)
    return s


def _to_float(raw: str) -> Optional[float]:
    raw = raw.strip().replace(",", ".")
    # 中文逗号当小数点的罕见情况已处理；千分位逗号去掉
    if not _NUMBER_RE.fullmatch(raw.replace(" ", "")):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _match_indicator(label: str) -> Optional[str]:
    norm = _norm_label(label)
    if not norm:
        return None
    # 精确别名优先
    for code, aliases in INDICATOR_ALIASES.items():
        if norm in [_norm_label(a) for a in aliases]:
            return code
    # 包含匹配（处理 "溶解氧(mg/L)" 等带单位写法）
    for code, aliases in INDICATOR_ALIASES.items():
        for a in aliases:
            na = _norm_label(a)
            if na and (norm.startswith(na) or na in norm):
                return code
    return None


def extract_from_label_value_pairs(pairs) -> dict:
    """通用：从 (标签, 数值文本) 序列中抽取指标。返回 {code: value}。"""
    values: dict[str, float] = {}
    for label, value in pairs:
        code = _match_indicator(str(label))
        if not code:
            continue
        nums = _NUMBER_RE.findall(str(value))
        if not nums:
            # 数值可能和标签在同一格，尝试从标签后取数
            nums = _NUMBER_RE.findall(str(label))
            nums = nums[1:] if len(nums) > 1 else nums
        if nums:
            f = _to_float(nums[0])
            if f is not None and code not in values:
                values[code] = f
    return values


# ---------------------------------------------------------------------------
# Excel / CSV
# ---------------------------------------------------------------------------
def extract_excel(data: bytes) -> dict:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    pairs = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cells = [c for c in row if c is not None]
            if len(cells) >= 2:
                # 第一个非数字单元格当标签，其后第一个数字当值
                for i, c in enumerate(cells):
                    label = str(c)
                    if _match_indicator(label):
                        for nxt in cells[i + 1:]:
                            nums = _NUMBER_RE.findall(str(nxt))
                            if nums:
                                pairs.append((label, nums[0]))
                                break
            elif len(cells) == 1:
                # "pH: 7.42" 这种同格写法
                pairs.append((str(cells[0]), str(cells[0])))
    return {"values": extract_from_label_value_pairs(pairs)}


def extract_csv(data: bytes) -> dict:
    import csv

    text = None
    for enc in ("utf-8-sig", "gbk", "latin-1"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    pairs = []
    for row in csv.reader(io.StringIO(text)):
        cells = [c.strip() for c in row if c.strip()]
        if len(cells) >= 2:
            pairs.append((cells[0], " ".join(cells[1:])))
        elif len(cells) == 1:
            pairs.append((cells[0], cells[0]))
    return {"values": extract_from_label_value_pairs(pairs)}


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def extract_pdf(data: bytes) -> dict:
    import pdfplumber

    pairs = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    cells = [c for c in row if c]
                    if len(cells) >= 2:
                        pairs.append((cells[0], " ".join(cells[1:])))
            text = page.extract_text() or ""
            for line in text.splitlines():
                # 每行内：标签 + 数字
                if _has_indicator(line):
                    pairs.append((line, line))
    return {"values": extract_from_label_value_pairs(pairs)}


def _has_indicator(line: str) -> bool:
    return any(_match_indicator(part) for part in re.split(r"[\s,，;；]+", line))


# ---------------------------------------------------------------------------
# 照片（视觉模型）
# ---------------------------------------------------------------------------
async def extract_image(data: bytes, mime: str) -> dict:
    import base64

    from app.config import get_settings
    from app.core.llm import vision_extract

    s = get_settings()
    b64 = base64.b64encode(data).decode()
    instruction = (
        '识别图片中的水质检测数据。严格只输出JSON，格式：'
        '{"values":{"ph":null,"wt":null,"do":null,"codmn":null,'
        '"nh3n":null,"tp":null,"tn":null},"site":"","river":"","date":""}。'
        "无法识别的项目填null，不要臆造。"
    )
    raw = await vision_extract(
        f"data:{mime};base64,{b64}", instruction)
    return _parse_vision_json(raw)


def _parse_vision_json(raw: str) -> dict:
    # 容错：剥离 ```json 包裹和前后说明
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {"values": {}, "raw": raw}
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"values": {}, "raw": raw}
    values = {}
    for code, v in (obj.get("values") or {}).items():
        if isinstance(v, (int, float)):
            values[code] = float(v)
        elif isinstance(v, str):
            nums = _NUMBER_RE.findall(v)
            if nums:
                values[code] = _to_float(nums[0])
    meta = {k: obj.get(k, "") for k in ("site", "river", "date")}
    return {"values": values, **{k: v for k, v in meta.items() if v}}


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------
IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "bmp", "gif"}
EXCEL_EXTS = {"xlsx", "xlsm"}
CSV_EXTS = {"csv"}
PDF_EXTS = {"pdf"}


async def extract_file(filename: str, data: bytes, mime: str) -> dict:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in EXCEL_EXTS:
        kind, result = "excel", extract_excel(data)
    elif ext in CSV_EXTS:
        kind, result = "csv", extract_csv(data)
    elif ext in PDF_EXTS:
        kind, result = "pdf", extract_pdf(data)
    elif ext in IMAGE_EXTS:
        kind, result = "image", await extract_image(data, mime)
    else:
        raise ValueError(f"暂不支持的文件类型：.{ext or '未知'}")
    return {"file_type": kind, **result}
