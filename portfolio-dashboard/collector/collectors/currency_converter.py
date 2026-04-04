from datetime import datetime

import yfinance as yf


class CurrencyConverter:
    """為替レート取得・通貨換算クラス"""

    def __init__(self) -> None:
        """初期化"""
        # 対応通貨ペア
        self.supported_pairs = {
            "USD": "USDJPY=X",
            "EUR": "EURJPY=X",
            "GBP": "GBPJPY=X",
            "AUD": "AUDJPY=X",
            "CAD": "CADJPY=X",
            "HKD": "HKDJPY=X",
            "SGD": "SGDJPY=X",
        }

    def get_exchange_rate(
        self, currency: str, date: datetime | None = None
    ) -> float | None:
        """指定通貨の対円レートを取得

        Args:
            currency (str): 通貨コード（USD, EUR等）
            date (datetime, optional): 取得日付（デフォルトは最新）

        Returns:
            float: 為替レート（None if エラー）
        """
        try:
            if currency == "JPY":
                return 1.0

            if currency not in self.supported_pairs:
                print(f"⚠️ {currency} は対応していない通貨です")
                return None

            pair = self.supported_pairs[currency]
            ticker = yf.Ticker(pair)

            if date:
                # 特定日のレート取得
                start_date = date
                end_date = date
                data = ticker.history(start=start_date, end=end_date)
            else:
                # 最新レート取得
                data = ticker.history(period="1d")

            if data.empty:
                print(f"⚠️ {currency}/JPY のレートが取得できませんでした")
                return None

            rate = data["Close"].iloc[-1]
            return float(rate)

        except Exception as e:
            print(f"為替レート取得エラー ({currency}): {e}")
            return None

    def convert_to_jpy(
        self, amount: float, currency: str, date: datetime | None = None
    ) -> float | None:
        """外貨を円に換算

        Args:
            amount (float): 外貨金額
            currency (str): 通貨コード
            date (datetime, optional): 換算日付

        Returns:
            float: 円換算金額（None if エラー）
        """
        if currency == "JPY":
            return amount

        rate = self.get_exchange_rate(currency, date)
        if rate is None:
            return None

        return amount * rate

    def get_currency_from_symbol(self, symbol: str) -> str:
        """銘柄コードから通貨を推定

        Args:
            symbol (str): 銘柄コード

        Returns:
            str: 通貨コード
        """
        # 日本株
        if ".T" in symbol or ".OS" in symbol:
            return "JPY"

        # 香港株
        if ".HK" in symbol:
            return "HKD"

        # ロンドン株
        if ".L" in symbol:
            return "GBP"

        # ユーロ圏
        if any(suffix in symbol for suffix in [".PA", ".DE", ".MI", ".AS"]):
            return "EUR"

        # オーストラリア
        if ".AX" in symbol:
            return "AUD"

        # カナダ
        if ".TO" in symbol:
            return "CAD"

        # デフォルトは米ドル（NASDAQ, NYSE等）
        return "USD"

    def get_all_current_rates(self) -> dict[str, float]:
        """全ての対応通貨の現在レートを取得

        Returns:
            dict: 通貨コード -> レートの辞書
        """
        rates = {"JPY": 1.0}

        for currency, _pair in self.supported_pairs.items():
            rate = self.get_exchange_rate(currency)
            if rate is not None:
                rates[currency] = rate

        return rates

    def display_current_rates(self) -> dict[str, float]:
        """現在の為替レートを表示"""
        print("\n💱 現在の為替レート（対円）:")
        rates = self.get_all_current_rates()

        for currency, rate in rates.items():
            if currency == "JPY":
                continue
            print(f"  {currency}/JPY: {rate:.2f}円")

        print(f"  更新日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return rates
