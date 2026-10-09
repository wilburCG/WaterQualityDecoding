# -*- coding: utf-8 -*-
"""M4 文件抽取测试（确定性部分，不调视觉模型）。"""
import io

from app.core.extract import (
    _match_indicator,
    _parse_vision_json,
    extract_csv,
    extract_excel,
    extract_from_label_value_pairs,
)


def test_indicator_alias_exact():
    assert _match_indicator("pH") == "ph"
    assert _match_indicator("溶解氧 (mg/L)") == "do"
    assert _match_indicator("氨氮 NH3-N") == "nh3n"
    assert _match_indicator("高锰酸盐指数 CODMn") == "codmn"
    assert _match_indicator("总磷（TP）") == "tp"
    assert _match_indicator("总氮") == "tn"
    assert _match_indicator("水温") == "wt"
    assert _match_indicator("无关字段") is None


def test_label_value_pairs():
    pairs = [
        ("pH", "7.42"),
        ("溶解氧", "4.61"),
        ("氨氮", "0.47"),
        ("总磷", "0.25"),
    ]
    out = extract_from_label_value_pairs(pairs)
    assert out == {"ph": 7.42, "do": 4.61, "nh3n": 0.47, "tp": 0.25}


def test_same_cell_value():
    out = extract_from_label_value_pairs([("pH: 7.42", "pH: 7.42")])
    assert out.get("ph") == 7.42


def test_csv_basic():
    text = "指标,数值\npH,7.4\n溶解氧,5.2\n氨氮,0.8\n"
    out = extract_csv(text.encode("utf-8"))["values"]
    assert out == {"ph": 7.4, "do": 5.2, "nh3n": 0.8}


def test_csv_gbk():
    text = "指标,数值\n总磷,0.1\n总氮,0.9\n"
    out = extract_csv(text.encode("gbk"))["values"]
    assert out == {"tp": 0.1, "tn": 0.9}


def test_excel_extract():
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    rows = [
        ("河流", "同汾泾"),
        ("pH", 7.42),
        ("溶解氧", 4.61),
        ("氨氮", 0.47),
        ("总磷", 0.25),
        ("总氮", 1.73),
    ]
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    out = extract_excel(buf.getvalue())["values"]
    assert out == {"ph": 7.42, "do": 4.61, "nh3n": 0.47, "tp": 0.25, "tn": 1.73}


def test_vision_json_plain():
    raw = '{"values":{"ph":7.4,"do":4.6,"tp":0.2},"site":"同汾泾上游","date":"2026-08-02"}'
    out = _parse_vision_json(raw)
    assert out["values"] == {"ph": 7.4, "do": 4.6, "tp": 0.2}
    assert out["site"] == "同汾泾上游"
    assert out["date"] == "2026-08-02"


def test_vision_json_wrapped():
    raw = "好的，结果如下：\n```json\n{\"values\":{\"nh3n\":0.47,\"tn\":1.73}}\n```"
    out = _parse_vision_json(raw)
    assert out["values"] == {"nh3n": 0.47, "tn": 1.73}


def test_vision_json_string_numbers():
    raw = '{"values":{"ph":"约7.4","codmn":"4.61"}}'
    out = _parse_vision_json(raw)
    assert out["values"] == {"ph": 7.4, "codmn": 4.61}


def test_vision_json_garbage():
    out = _parse_vision_json("识别失败，没有数据")
    assert out["values"] == {}
