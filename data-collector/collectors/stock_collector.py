import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from currency_converter import CurrencyConverter


class StockDataCollector:
    """株価データ収集クラス"""
    
    def __init__(self):
        """初期化"""
        self.currency_converter = CurrencyConverter()
    
    def get_stock_data(self, symbol, year, month):
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
    
    def calculate_stock_metrics(self, stock_data, symbol, purchase_price, shares, convert_to_jpy=True):
        """株価メトリクスを計算
        
        Args:
            stock_data (pd.DataFrame): 株価データ
            symbol (str): 銘柄コード
            purchase_price (float): 取得価格（円）
            shares (int): 保有株数
            convert_to_jpy (bool): 外貨を円換算するか
            
        Returns:
            dict: 計算結果
        """
        try:
            # 株価情報の計算
            month_start_price = stock_data['Close'].iloc[0]
            month_end_price = stock_data['Close'].iloc[-1]
            highest_price = stock_data['High'].max()
            lowest_price = stock_data['Low'].min()
            average_price = stock_data['Close'].mean()
            monthly_change = ((month_end_price / month_start_price) - 1) * 100
            average_volume = stock_data['Volume'].mean()
            
            # 通貨判定と換算
            currency = self.currency_converter.get_currency_from_symbol(symbol)
            
            if convert_to_jpy and currency != 'JPY':
                # 外貨を円換算
                exchange_rate = self.currency_converter.get_exchange_rate(currency)
                if exchange_rate is None:
                    print(f"⚠️ {symbol} の為替レート取得に失敗、元通貨で計算します")
                    exchange_rate = 1.0
                    currency = 'JPY'  # エラー時は円として扱う
                
                month_end_price_jpy = month_end_price * exchange_rate
                highest_price_jpy = highest_price * exchange_rate
                lowest_price_jpy = lowest_price * exchange_rate
                average_price_jpy = average_price * exchange_rate
                
                print(f"  💱 {currency}/JPY レート: {exchange_rate:.2f}円")
            else:
                # 円またはそのまま
                month_end_price_jpy = month_end_price
                highest_price_jpy = highest_price
                lowest_price_jpy = lowest_price
                average_price_jpy = average_price
                exchange_rate = 1.0
            
            # 損益計算（円ベース）
            purchase_amount = purchase_price * shares
            current_amount = month_end_price_jpy * shares
            profit_loss = current_amount - purchase_amount
            profit_rate = (profit_loss / purchase_amount) * 100
            
            return {
                'symbol': symbol,
                'currency': currency,
                'exchange_rate': round(exchange_rate, 2) if exchange_rate != 1.0 else None,
                'month_end_price': round(month_end_price_jpy, 2),
                'highest_price': round(highest_price_jpy, 2),
                'lowest_price': round(lowest_price_jpy, 2),
                'average_price': round(average_price_jpy, 2),
                'monthly_change': round(monthly_change, 2),
                'average_volume': int(average_volume),
                'purchase_amount': purchase_amount,
                'current_amount': round(current_amount, 2),
                'profit_loss': round(profit_loss, 2),
                'profit_rate': round(profit_rate, 2)
            }
            
        except Exception as e:
            print(f"メトリクス計算エラー ({symbol}): {e}")
            return None