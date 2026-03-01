"""
ベンチマーク比較エンドポイントのロジックテスト。

fetch_performance を monkeypatch でモックして、
ネットワーク・Sheets アクセスなしで集計ロジックを検証する。
"""

from collections import defaultdict
from unittest.mock import patch

import pandas as pd
import pytest


# ベンチマーク集計ロジックを直接テストするためのヘルパー
def _aggregate(records: list[dict]) -> dict[str, dict]:
    """月ごとに value/cost を集計する（router と同じロジック）"""
    monthly: dict[str, dict] = defaultdict(lambda: {"value": 0.0, "cost": 0.0})
    for r in records:
        monthly[r["date"]]["value"] += r["value"]
        monthly[r["date"]]["cost"] += r["cost"]
    return dict(monthly)


def _calc_portfolio_rate(value: float, cost: float) -> float:
    """ポートフォリオ累積リターン率を計算"""
    if cost == 0:
        return 0.0
    return (value - cost) / cost * 100


class TestBenchmarkAggregation:
    """月次集計ロジックのユニットテスト"""

    def test_単一銘柄単一月の集計(self):
        records = [
            {"date": "2024-01-末", "value": 110000.0, "cost": 100000.0},
        ]
        monthly = _aggregate(records)
        assert "2024-01-末" in monthly
        assert monthly["2024-01-末"]["value"] == pytest.approx(110000.0)
        assert monthly["2024-01-末"]["cost"] == pytest.approx(100000.0)

    def test_複数銘柄同一月の合算(self):
        records = [
            {"date": "2024-01-末", "value": 110000.0, "cost": 100000.0},
            {"date": "2024-01-末", "value": 220000.0, "cost": 200000.0},
        ]
        monthly = _aggregate(records)
        assert monthly["2024-01-末"]["value"] == pytest.approx(330000.0)
        assert monthly["2024-01-末"]["cost"] == pytest.approx(300000.0)

    def test_複数月の分離(self):
        records = [
            {"date": "2024-01-末", "value": 110000.0, "cost": 100000.0},
            {"date": "2024-02-末", "value": 120000.0, "cost": 100000.0},
        ]
        monthly = _aggregate(records)
        assert len(monthly) == 2
        assert monthly["2024-01-末"]["value"] == pytest.approx(110000.0)
        assert monthly["2024-02-末"]["value"] == pytest.approx(120000.0)


class TestPortfolioRateCalc:
    """ポートフォリオ累積リターン率計算のテスト"""

    def test_10パーセント利益(self):
        rate = _calc_portfolio_rate(110000.0, 100000.0)
        assert rate == pytest.approx(10.0)

    def test_損失ケース(self):
        rate = _calc_portfolio_rate(90000.0, 100000.0)
        assert rate == pytest.approx(-10.0)

    def test_ゼロ除算ガード_cost_が_0(self):
        rate = _calc_portfolio_rate(110000.0, 0.0)
        assert rate == 0.0

    def test_損益ゼロのケース(self):
        rate = _calc_portfolio_rate(100000.0, 100000.0)
        assert rate == pytest.approx(0.0)


class TestBenchmarkEndpoint:
    """FastAPI エンドポイントの統合テスト（Sheets・yfinance をモック）"""

    def test_パフォーマンスデータが空の場合は空リストを返す(self):
        """fetch_performance が空リストを返すとき data: [] になること"""
        from fastapi.testclient import TestClient

        from main import app

        with patch("app.routers.benchmark.fetch_performance", return_value=[]):
            client = TestClient(app)
            response = client.get("/api/benchmark")
        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []

    def test_正常データで集計が正しい(self):
        """2ヶ月分データ: 1月目は0%、2月目は10%になること"""
        from fastapi.testclient import TestClient

        from main import app

        records = [
            {"date": "2024-01-末", "value": 100000.0, "cost": 100000.0},
            {"date": "2024-02-末", "value": 110000.0, "cost": 100000.0},
        ]

        with (
            patch(
                "app.routers.benchmark.fetch_performance",
                return_value=records,
            ),
            patch("app.routers.benchmark.yf.download") as mock_dl,
        ):
            # 空 DataFrame を返すと except ブロックに落ちてベンチマーク値は None になる
            mock_dl.return_value = pd.DataFrame()

            client = TestClient(app)
            response = client.get("/api/benchmark")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        # 最初の月: cost=value なのでポートフォリオ率は 0%
        assert data[0]["date"] == "2024-01-末"
        assert data[0]["portfolio"] == pytest.approx(0.0)
        # 2ヶ月目: (110000-100000)/100000*100 = 10%
        assert data[1]["date"] == "2024-02-末"
        assert data[1]["portfolio"] == pytest.approx(10.0)
