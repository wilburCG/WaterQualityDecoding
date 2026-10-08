"""水质评价引擎 —— 确定性规则，零 LLM 参与判定。

依据《地表水环境质量标准》GB 3838-2002（河流）。

设计要点：
- 限值以参数注入（standard 参数），便于扩展湖库、饮用水、地下水等多套标准；
- 指标方向：溶解氧为 "ge"（≥），其余化学指标为 "le"（≤）；
- pH 为全类别通用边界指标：6~9 达标且不单独定类，超出则整体判 "不达标"；
- 断面综合类别 = 各指标类别最差值（一票否决），并列最差者均列为定类因子；
- 超过 Ⅴ 类限值 => 劣 Ⅴ 类（类别码 6）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# 类别码：1-5 对应 Ⅰ-Ⅴ，6 = 劣 Ⅴ
GRADE_LABELS: Dict[int, str] = {1: "Ⅰ", 2: "Ⅱ", 3: "Ⅲ", 4: "Ⅳ", 5: "Ⅴ", 6: "劣Ⅴ"}

# ---------------------------------------------------------------------------
# GB 3838-2002 河流标准限值（mg/L；pH 无量纲）
# limits: 类别码 -> 限值
# ---------------------------------------------------------------------------
GB3838_RIVER: Dict[str, dict] = {
    "ph": {"direction": "range", "limits": (6.0, 9.0), "name": "pH", "unit": ""},
    "do": {"direction": "ge", "limits": {1: 7.5, 2: 6.0, 3: 5.0, 4: 3.0, 5: 2.0},
           "name": "溶解氧", "unit": "mg/L"},
    "codmn": {"direction": "le", "limits": {1: 2.0, 2: 4.0, 3: 6.0, 4: 10.0, 5: 15.0},
              "name": "高锰酸盐指数", "unit": "mg/L"},
    "nh3n": {"direction": "le", "limits": {1: 0.15, 2: 0.5, 3: 1.0, 4: 1.5, 5: 2.0},
             "name": "氨氮", "unit": "mg/L"},
    "tp": {"direction": "le", "limits": {1: 0.02, 2: 0.1, 3: 0.2, 4: 0.3, 5: 0.4},
           "name": "总磷", "unit": "mg/L"},
    "tn": {"direction": "le", "limits": {1: 0.2, 2: 0.5, 3: 1.0, 4: 1.5, 5: 2.0},
           "name": "总氮", "unit": "mg/L"},
}


@dataclass
class ItemResult:
    code: str
    name: str
    value: float
    unit: str
    grade: Optional[int] = None          # pH 达标时为 None（不定类）
    compliant: bool = True
    limit_value: Optional[float] = None  # 所命中档位的限值
    exceed_ratio: Optional[float] = None # 超出 Ⅴ 类/该档限值的倍数


@dataclass
class GradeResult:
    overall_grade: Optional[int] = None
    overall_label: Optional[str] = None
    deciding_factors: List[str] = field(default_factory=list)
    worst_factors: List[str] = field(default_factory=list)  # 技术口径：全部最差档指标
    items: Dict[str, ItemResult] = field(default_factory=dict)
    unknown_indicators: List[str] = field(default_factory=list)
    non_compliant_boundary: List[str] = field(default_factory=list)  # 如 pH 超标
    error: Optional[str] = None

    @property
    def compliant(self) -> bool:
        return not self.non_compliant_boundary


def _classify_le(value: float, limits: Dict[int, float]):
    """≤ 方向：返回 (类别码, 命中档限值, 相对Ⅴ类的超标倍数或None)。"""
    for grade in (1, 2, 3, 4, 5):
        if value <= limits[grade]:
            return grade, limits[grade], None
    return 6, limits[5], value / limits[5]


def _classify_ge(value: float, limits: Dict[int, float]):
    """≥ 方向：返回 (类别码, 命中档限值, 劣Ⅴ倍数或None)。低于Ⅴ类下限即劣Ⅴ。"""
    for grade in (1, 2, 3, 4, 5):
        if value >= limits[grade]:
            return grade, limits[grade], None
    return 6, limits[5], limits[5] / value if value > 0 else None


def grade_section(values: Dict[str, float],
                  standard: Optional[Dict[str, dict]] = None) -> GradeResult:
    """对一个断面的指标集合进行评价。

    :param values: {indicator_code: value}，可为任意指标子集
    :param standard: 标准定义，默认 GB3838 河流
    """
    standard = standard or GB3838_RIVER
    result = GradeResult()

    known = {k: v for k, v in values.items() if k in standard}
    result.unknown_indicators = sorted(k for k in values if k not in standard)

    if not known:
        result.error = "no_data"
        return result

    for code, value in known.items():
        spec = standard[code]
        item = ItemResult(code=code, name=spec["name"], value=value, unit=spec["unit"])

        if spec["direction"] == "range":
            low, high = spec["limits"]
            item.compliant = low <= value <= high
            item.limit_value = high
            if not item.compliant:
                result.non_compliant_boundary.append(code)
        elif spec["direction"] == "le":
            item.grade, item.limit_value, item.exceed_ratio = _classify_le(value, spec["limits"])
        elif spec["direction"] == "ge":
            item.grade, item.limit_value, item.exceed_ratio = _classify_ge(value, spec["limits"])
        else:  # pragma: no cover - 防御
            raise ValueError(f"unknown direction: {spec['direction']}")

        result.items[code] = item

    # pH 等边界指标超标 => 整体不达标（比劣Ⅴ更严重的口径提示）
    if result.non_compliant_boundary:
        result.overall_grade = 6
        result.overall_label = GRADE_LABELS[6]
        result.deciding_factors = list(result.non_compliant_boundary)
        return result

    graded = [it for it in result.items.values() if it.grade is not None]
    if not graded:
        # 只有 pH 且达标：无法定类
        result.error = "ungraded"
        return result

    worst = max(it.grade for it in graded)
    result.overall_grade = worst
    result.overall_label = GRADE_LABELS[worst]
    worst_factors = sorted(it.code for it in graded if it.grade == worst)
    result.worst_factors = worst_factors
    # 报告/评价惯例：断面达到 Ⅲ 类（管理目标）时不记定类因子；
    # 仅 Ⅳ/Ⅴ/劣Ⅴ 在报告中列出定类因子。
    result.deciding_factors = worst_factors if worst > 3 else []
    return result
