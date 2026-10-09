# -*- coding: utf-8 -*-
"""M5 测试：距离 / 官方对照 / 订阅匹配（纯逻辑，不连库不调模型）。"""
from datetime import datetime, timezone

from app.core.geo import haversine_km
from app.core.notify import match_subscriptions
from app.core.official import (
    CandidateReading,
    CandidateSection,
    compare,
)


class _Sub:
    def __init__(self, user_id, target_type, target_key, alert_grade_from=4):
        self.user_id = user_id
        self.target_type = target_type
        self.target_key = target_key
        self.alert_grade_from = alert_grade_from


# ---------------------------------------------------------------------------
# 距离
# ---------------------------------------------------------------------------
def test_haversine_zero():
    assert haversine_km(121.5, 31.1, 121.5, 31.1) == 0.0


def test_haversine_known():
    # 同汾泾下游 (121.5230,31.1610) 到演示断面 (121.5260,31.1680)，约 0.8km
    d = haversine_km(121.5230, 31.1610, 121.5260, 31.1680)
    assert 0.6 < d < 1.0


def test_haversine_symmetric():
    d1 = haversine_km(121.5, 31.1, 121.6, 31.2)
    d2 = haversine_km(121.6, 31.2, 121.5, 31.1)
    assert abs(d1 - d2) < 1e-9


# ---------------------------------------------------------------------------
# 订阅匹配
# ---------------------------------------------------------------------------
def test_match_river_and_site():
    subs = [
        _Sub(1, "river", "同汾泾"),
        _Sub(2, "river", "三林塘港"),
        _Sub(3, "site", "10"),
    ]
    matched = match_subscriptions(subs, "同汾泾", 10)
    assert {s.user_id for s in matched} == {1, 3}


def test_match_none():
    subs = [_Sub(2, "river", "三林塘港")]
    assert match_subscriptions(subs, "同汾泾", 99) == []


# ---------------------------------------------------------------------------
# 官方对照
# ---------------------------------------------------------------------------
UTC = timezone.utc


def _section(readings):
    return CandidateSection(
        code="DEMO-TFJ-01", name="同汾泾入河口（演示断面）", river="同汾泾",
        lng=121.5260, lat=31.1680, level="市控", source_org="（演示）",
        readings=readings)


def test_compare_basic():
    when = datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
    sec = _section([
        CandidateReading(
            observed_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
            values={"tp": 0.09, "nh3n": 0.30},
            overall_grade=3, source="演示", source_url="", note=""),
    ])
    result = compare(
        lng=121.5230, lat=31.1610, sampled_at=when,
        values={"tp": 0.25, "nh3n": 0.47, "do": 4.61},
        sections=[sec],
        indicator_meta={"tp": {"name": "总磷", "unit": "mg/L"}})

    assert len(result["matches"]) == 1
    m = result["matches"][0]
    assert m["distance_km"] < 1.0
    assert m["days_gap"] <= 1.0
    # do 在官方读数中缺失，不进对照项
    assert {i["code"] for i in m["items"]} == {"tp", "nh3n"}
    tp_item = next(i for i in m["items"] if i["code"] == "tp")
    assert tp_item["diff"] == round(0.25 - 0.09, 3)
    assert tp_item["rel_diff_pct"] > 100
    assert tp_item["label"] == "总磷"
    assert "caveat" in result and result["caveat"]


def test_compare_outside_radius():
    sec = _section([
        CandidateReading(
            observed_at=datetime(2026, 8, 2, tzinfo=UTC),
            values={"tp": 0.1}, overall_grade=3,
            source="", source_url="", note="")])
    result = compare(
        lng=121.0, lat=31.0, sampled_at=datetime(2026, 8, 2, tzinfo=UTC),
        values={"tp": 0.25}, sections=[sec], indicator_meta={}, radius_km=5)
    assert result["matches"] == []


def test_compare_reading_outside_window():
    sec = _section([
        CandidateReading(
            observed_at=datetime(2026, 1, 1, tzinfo=UTC),
            values={"tp": 0.1}, overall_grade=3,
            source="", source_url="", note="")])
    result = compare(
        lng=121.5230, lat=31.1610, sampled_at=datetime(2026, 8, 2, tzinfo=UTC),
        values={"tp": 0.25}, sections=[sec], indicator_meta={}, max_days=14)
    assert result["matches"] == []


def test_compare_picks_nearest_reading():
    sec = _section([
        CandidateReading(
            observed_at=datetime(2026, 8, 8, tzinfo=UTC),
            values={"tp": 0.30}, overall_grade=4,
            source="far", source_url="", note=""),
        CandidateReading(
            observed_at=datetime(2026, 8, 3, tzinfo=UTC),
            values={"tp": 0.10}, overall_grade=3,
            source="near", source_url="", note=""),
    ])
    result = compare(
        lng=121.5230, lat=31.1610,
        sampled_at=datetime(2026, 8, 2, tzinfo=UTC),
        values={"tp": 0.25}, sections=[sec], indicator_meta={}, max_days=10)
    m = result["matches"][0]
    assert m["reading"]["source"] == "near"


def test_compare_zero_base_no_rel():
    sec = _section([
        CandidateReading(
            observed_at=datetime(2026, 8, 2, tzinfo=UTC),
            values={"do": 0.0}, overall_grade=6,
            source="", source_url="", note="")])
    result = compare(
        lng=121.5230, lat=31.1610,
        sampled_at=datetime(2026, 8, 2, tzinfo=UTC),
        values={"do": 4.6}, sections=[sec], indicator_meta={})
    item = result["matches"][0]["items"][0]
    assert item["rel_diff_pct"] is None
