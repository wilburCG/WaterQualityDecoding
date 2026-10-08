"""评价引擎回测：同汾泾报告全部 7 行数据 + 边界用例。

运行：cd backend && pytest -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.grading import grade_section, GRADE_LABELS  # noqa: E402


# ---------------------------------------------------------------------------
# 报告原始数据（mg/L）：(标签, 输入, 期望类别码, 期望定类因子)
# ---------------------------------------------------------------------------
REPORT_ROWS = [
    # 8 月 2 日
    ("8/2 上游", {"tp": 0.25, "tn": 1.73, "nh3n": 0.47, "codmn": 4.61}, 5, ["tn"]),
    ("8/2 中游", {"tp": 0.16, "tn": 1.21, "nh3n": 0.18, "codmn": 4.56}, 4, ["tn"]),
    ("8/2 下游", {"tp": 0.08, "tn": 0.90, "nh3n": 0.28, "codmn": 4.14}, 3, []),
    # 8 月 5 日（未测氨氮）
    ("8/5 三林塘港", {"tp": 0.20, "tn": 1.84, "codmn": 5.84}, 5, ["tn"]),
    ("8/5 上游", {"tp": 0.20, "tn": 2.09, "codmn": 6.17}, 6, ["tn"]),
    ("8/5 中游", {"tp": 0.13, "tn": 0.78, "codmn": 5.04}, 3, []),
    ("8/5 下游", {"tp": 0.09, "tn": 0.85, "codmn": 4.63}, 3, []),
]


def test_report_rows_match_exactly():
    """报告 7 行：综合类别与定类因子必须逐行一致。"""
    for label, values, exp_grade, exp_factors in REPORT_ROWS:
        r = grade_section(values)
        assert r.overall_grade == exp_grade, (
            f"{label}: 期望 {GRADE_LABELS[exp_grade]} 实际 {r.overall_label}")
        assert r.deciding_factors == exp_factors, (
            f"{label}: 定类因子 期望 {exp_factors} 实际 {r.deciding_factors}")
        assert r.error is None


def test_grade6_is_inferior_class_v():
    r = grade_section({"tn": 2.09, "codmn": 6.17, "tp": 0.20})
    assert r.overall_label == "劣Ⅴ"
    assert r.items["tn"].exceed_ratio is not None
    assert r.items["tn"].exceed_ratio > 1.0


def test_ph_boundaries():
    # 边界值 6.0 / 9.0 达标
    assert grade_section({"ph": 6.0}).non_compliant_boundary == []
    assert grade_section({"ph": 9.0}).non_compliant_boundary == []
    # 越界 => 不达标，pH 为决定因素
    r = grade_section({"ph": 5.9, "tn": 0.5})
    assert r.non_compliant_boundary == ["ph"]
    assert r.overall_grade == 6


def test_do_direction_is_greater_equal():
    # DO 越低越差：2.0 恰为 Ⅴ 类
    r = grade_section({"do": 2.0})
    assert r.overall_grade == 5
    r2 = grade_section({"do": 9.14})
    assert r2.overall_grade == 1
    r3 = grade_section({"do": 0.25})
    assert r3.overall_grade == 6


def test_ph_alone_cannot_set_class():
    # pH 达标且无其他指标：无法定类
    r = grade_section({"ph": 7.5})
    assert r.error == "ungraded"
    assert r.overall_grade is None


def test_empty_and_unknown():
    assert grade_section({}).error == "no_data"
    r = grade_section({"xx": 1.0})
    assert r.error == "no_data"
    assert r.unknown_indicators == ["xx"]
    r2 = grade_section({"tn": 0.9, "xx": 1.0})
    assert r2.overall_grade == 3
    assert r2.unknown_indicators == ["xx"]


def test_multiple_deciding_factors():
    # TN 与 TP 同为最差档（Ⅴ）时都应列出
    r = grade_section({"tn": 1.8, "tp": 0.35, "codmn": 5.0})
    assert r.overall_grade == 5
    assert r.deciding_factors == ["tn", "tp"]


def test_full_report_range_with_ph_normal():
    """加上报告实测 pH（6.96~8.42）后判定不变。"""
    for label, values, exp_grade, exp_factors in REPORT_ROWS:
        values = dict(values, ph=7.8)
        r = grade_section(values)
        assert r.overall_grade == exp_grade
        assert r.deciding_factors == exp_factors
