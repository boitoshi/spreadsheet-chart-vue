from datetime import datetime, timedelta

import yfinance as yf

from .currency_converter import CurrencyConverter


class StockDataCollector:
    """株価データ収集クラス"""

    def __init__(self) -> None:
        """初期化"""
        self.currency_converter = CurrencyConverter()

    def get_stock_data(
        self, symbol: str, year: int, month: int
    ) -> dict[str, object] | None:
        """株価データを取得

        Args:
            symbol (str): 銘柄コード
            year (int): 年
            month (int): 月

        Returns:
            pd.DataFrame: 株価データ
        """
        try:
            # 月の開始日と終了日を計算
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)

            # yfinanceでデータ取得
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date + timedelta(days=1))

            if data.empty:
                print(f"⚠️ {symbol} のデータが取得できませんでした")
                return None

            return data

        except Exception as e:
            print(f"株価データ取得エラー ({symbol}): {e}")
            return None

    def calculate_stock_metrics(
        self, stock_data: dict[str, object], symbol: str,
        purchase_price_foreign: float, purchase_exchange_rate: float,
        shares: int, convert_to_jpy: bool = True
    ) -> dict[str, object] | None:
        """株価メトリクスを計算（為替損益分離対応）

        Args:
            stock_data (pd.DataFrame): 株価データ
            symbol (str): 銘柄コード
            purchase_price_foreign (float): 取得価格（外貨建て、日本株は円）
            purchase_exchange_rate (float): 取得時為替レート（日本株は1.0）
            shares (int): 保有株数
            convert_to_jpy (bool): 外貨を円換算するか

        Returns:
            dict: 計算結果
        """
        try:
            # 株価情報の計算（外貨建て）
            month_start_price = stock_data['Close'].iloc[0]
            month_end_price = stock_data['Close'].iloc[-1]
            highest_price = stock_data['High'].max()
            lowest_price = stock_data['Low'].min()
            average_price = stock_data['Close'].mean()
            monthly_change = ((month_end_price / month_start_price) - 1) * 100
            average_volume = stock_data['Volume'].mean()

            # 通貨判定と換算
            currency = self.currency_converter.get_currency_from_symbol(symbol)

            # 外貨建ての月末価格を保持
            month_end_price_foreign = float(month_end_price)

            if convert_to_jpy and currency != 'JPY':
                # 現在の為替レート取得
                current_exchange_rate = (
                    self.currency_converter.get_exchange_rate(currency)
                )
                if current_exchange_rate is None:
                    print(f"⚠️ {symbol} の為替レート取得に失敗、元通貨で計算します")
                    current_exchange_rate = 1.0
                    currency = 'JPY'

                # 円換算
                month_end_price_jpy = month_end_price * current_exchange_rate
                highest_price_jpy = highest_price * current_exchange_rate
                lowest_price_jpy = lowest_price * current_exchange_rate
                average_price_jpy = average_price * current_exchange_rate

                print(f"  💱 {currency}/JPY レート: {current_exchange_rate:.2f}円")
            else:
                # 円またはそのまま
                current_exchange_rate = 1.0
                month_end_price_jpy = month_end_price
                highest_price_jpy = highest_price
                lowest_price_jpy = lowest_price
                average_price_jpy = average_price

            # 円建ての取得単価
            purchase_price_jpy = purchase_price_foreign * purchase_exchange_rate

            # 総損益計算（円ベース）
            purchase_amount = purchase_price_jpy * shares
            current_amount = month_end_price_jpy * shares
            total_profit_loss = current_amount - purchase_amount
            profit_rate = (
                (total_profit_loss / purchase_amount) * 100
                if purchase_amount > 0
                else 0
            )

            # 為替損益分離計算
            stock_profit_loss = (
                (month_end_price_foreign - purchase_price_foreign)
                * purchase_exchange_rate * shares
            )
            fx_profit_loss = (
                (current_exchange_rate - purchase_exchange_rate)
                * month_end_price_foreign * shares
            )

            return {
                'symbol': symbol,
                'currency': currency,
                'exchange_rate': (
                    round(current_exchange_rate, 2)
                    if current_exchange_rate != 1.0
                    else None
                ),
                'month_end_price': round(float(month_end_price_jpy), 2),
                'highest_price': round(float(highest_price_jpy), 2),
                'lowest_price': round(float(lowest_price_jpy), 2),
                'average_price': round(float(average_price_jpy), 2),
                'monthly_change': round(float(monthly_change), 2),
                'average_volume': int(average_volume),
                'purchase_amount': round(purchase_amount, 2),
                'current_amount': round(float(current_amount), 2),
                'profit_loss': round(float(total_profit_loss), 2),
                'profit_rate': round(float(profit_rate), 2),
                # 外貨・為替情報
                'purchase_price_foreign': round(purchase_price_foreign, 2),
                'purchase_exchange_rate': round(purchase_exchange_rate, 2),
                'month_end_price_foreign': round(month_end_price_foreign, 2),
                'current_exchange_rate': round(current_exchange_rate, 2),
                'stock_profit_loss': round(float(stock_profit_loss), 2),
                'fx_profit_loss': round(float(fx_profit_loss), 2),
            }

        except Exception as e:
            print(f"メトリクス計算エラー ({symbol}): {e}")
            return None
