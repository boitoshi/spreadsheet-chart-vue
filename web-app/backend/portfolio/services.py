"""
Google Sheets連携サービス
data-collectorとの設定を共有して既存データを読み取り
"""
import gspread
from google.oauth2.service_account import Credentials
from django.conf import settings
from datetime import datetime, timedelta
import sys
import os
from typing import List, Dict, Optional

# 共通設定をインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
try:
    from sheets_config import SCOPES, SHEET_NAMES, HEADERS
except ImportError:
    # フォールバック設定
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SHEET_NAMES = {
        'PORTFOLIO': 'ポートフォリオ',
        'DATA_RECORD': 'データ記録',
        'PERFORMANCE': '損益レポート'
    }


class GoogleSheetsService:
    """Google Sheets読み取り専用サービス"""
    
    def __init__(self):
        """Google Sheets APIクライアントを初期化"""
        self.gc = None
        self.spreadsheet = None
        self._setup_credentials()
    
    def _setup_credentials(self):
        """Google Sheets認証設定"""
        try:
            if not settings.GOOGLE_APPLICATION_CREDENTIALS:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALSが設定されていません")
            
            if not settings.SPREADSHEET_ID:
                raise ValueError("SPREADSHEET_IDが設定されていません")
            
            creds = Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS, 
                scopes=SCOPES
            )
            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open_by_key(settings.SPREADSHEET_ID)
            
        except Exception as e:
            print(f"Google Sheets認証エラー: {e}")
            raise
    
    def get_portfolio_data(self) -> List[Dict]:
        """ポートフォリオマスタシートから取引履歴を取得"""
        try:
            portfolio_sheet = self.spreadsheet.worksheet(SHEET_NAMES['PORTFOLIO'])
            records = portfolio_sheet.get_all_records()
            return records
        except Exception as e:
            print(f"ポートフォリオデータ取得エラー: {e}")
            return []
    
    def get_latest_performance_data(self) -> List[Dict]:
        """損益レポートシートから最新の損益データを取得"""
        try:
            performance_sheet = self.spreadsheet.worksheet(SHEET_NAMES['PERFORMANCE'])
            records = performance_sheet.get_all_records()
            
            # 最新のデータのみを取得（日付でソートして最新月のデータ）
            if not records:
                return []
            
            # 日付で最新のデータをグループ化
            latest_date = max(record['日付'] for record in records if record['日付'])
            latest_records = [r for r in records if r['日付'] == latest_date]
            
            return latest_records
            
        except Exception as e:
            print(f"損益データ取得エラー: {e}")
            return []
    
    def get_performance_history(self, period: str = 'all') -> List[Dict]:
        """損益推移履歴を期間指定で取得"""
        try:
            performance_sheet = self.spreadsheet.worksheet(SHEET_NAMES['PERFORMANCE'])
            records = performance_sheet.get_all_records()
            
            if not records:
                return []
            
            # 期間フィルタリング
            filtered_records = self._filter_by_period(records, period)
            
            # 日付でグループ化して月次サマリーを作成
            monthly_summary = self._create_monthly_summary(filtered_records)
            
            return monthly_summary
            
        except Exception as e:
            print(f"履歴データ取得エラー: {e}")
            return []
    
    def _filter_by_period(self, records: List[Dict], period: str) -> List[Dict]:
        """期間に基づいてレコードをフィルタリング"""
        if period == 'all':
            return records
        
        now = datetime.now()
        
        if period == '6months':
            cutoff_date = now - timedelta(days=180)
        elif period == '1year':
            cutoff_date = now - timedelta(days=365)
        else:
            return records
        
        # 日付文字列をパースしてフィルタリング
        filtered = []
        for record in records:
            try:
                # 日付形式を想定: "2024-01-末" or "2024-01-31"
                date_str = str(record['日付']).replace('-末', '-01')
                record_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                
                if record_date >= cutoff_date:
                    filtered.append(record)
            except (ValueError, TypeError):
                continue
        
        return filtered
    
    def _create_monthly_summary(self, records: List[Dict]) -> List[Dict]:
        """月次サマリーを作成（Vue.jsのチャート用）"""
        monthly_data = {}
        
        for record in records:
            try:
                date_key = str(record['日付'])
                
                if date_key not in monthly_data:
                    monthly_data[date_key] = {
                        'date': date_key,
                        'total_profit': 0,
                        'total_value': 0,
                        'total_cost': 0
                    }
                
                # 数値型に変換（エラー回避）
                profit = float(record.get('損益', 0)) if record.get('損益') else 0
                value = float(record.get('評価額', 0)) if record.get('評価額') else 0
                cost = float(record.get('取得額', 0)) if record.get('取得額') else 0
                
                monthly_data[date_key]['total_profit'] += profit
                monthly_data[date_key]['total_value'] += value
                monthly_data[date_key]['total_cost'] += cost
                
            except (ValueError, TypeError, KeyError):
                continue
        
        # 日付でソート
        sorted_data = sorted(monthly_data.values(), key=lambda x: x['date'])
        return sorted_data


class PortfolioDataTransformer:
    """Google SheetsデータをVue.js形式に変換"""
    
    @staticmethod
    def transform_to_vue_format(portfolio_data: List[Dict], performance_data: List[Dict]) -> Dict:
        """
        Google Sheetsの複数シートデータをVue.jsダッシュボード期待形式に変換
        
        Args:
            portfolio_data: ポートフォリオマスタシートのデータ
            performance_data: 損益レポートシートの最新データ
            
        Returns:
            Vue.js App.vue が期待するデータ形式
        """
        stocks = []
        
        # 銘柄別にグループ化
        stock_groups = PortfolioDataTransformer._group_by_stock(portfolio_data)
        
        # 損益データをマッピング用辞書に変換
        performance_map = {p['銘柄名']: p for p in performance_data}
        
        for stock_name, transactions in stock_groups.items():
            # パフォーマンスデータから現在価格と損益情報取得
            perf_data = performance_map.get(stock_name, {})
            current_price = float(perf_data.get('月末価格', 0)) if perf_data.get('月末価格') else 0
            
            # Vue.js形式の取引履歴に変換
            vue_transactions = []
            total_quantity = 0
            total_cost = 0
            
            for tx in transactions:
                quantity = int(tx.get('保有株数', 0)) if tx.get('保有株数') else 0
                price = float(tx.get('取得単価（円）', 0)) if tx.get('取得単価（円）') else 0
                date = PortfolioDataTransformer._format_date(tx.get('取得日', ''))
                
                vue_transactions.append({
                    'date': date,
                    'quantity': quantity,
                    'price': price
                })
                
                total_quantity += quantity
                total_cost += quantity * price
            
            # 平均取得価格計算
            avg_price = total_cost / total_quantity if total_quantity > 0 else 0
            
            # 現在の評価額と損益計算
            current_value = current_price * total_quantity
            profit = current_value - total_cost
            
            stocks.append({
                'name': stock_name,
                'currentPrice': current_price,
                'transactions': vue_transactions,
                'quantity': total_quantity,
                'avgPrice': round(avg_price, 0),
                'currentValue': round(current_value, 0),
                'profit': round(profit, 0),
                'totalCost': round(total_cost, 0)
            })
        
        # サマリー計算
        total_value = sum(stock['currentValue'] for stock in stocks)
        total_cost = sum(stock['totalCost'] for stock in stocks)
        total_profit = total_value - total_cost
        
        return {
            'summary': {
                'totalValue': round(total_value, 0),
                'totalProfit': round(total_profit, 0),
                'totalCost': round(total_cost, 0)
            },
            'stocks': stocks
        }
    
    @staticmethod
    def _group_by_stock(portfolio_data: List[Dict]) -> Dict[str, List[Dict]]:
        """銘柄名でポートフォリオデータをグループ化"""
        groups = {}
        
        for record in portfolio_data:
            stock_name = record.get('銘柄名', '')
            if not stock_name:
                continue
            
            if stock_name not in groups:
                groups[stock_name] = []
            
            groups[stock_name].append(record)
        
        return groups
    
    @staticmethod
    def _format_date(date_str: str) -> str:
        """日付形式をVue.js期待形式に変換 (YYYY-MM-DD → YYYY/MM/DD)"""
        try:
            if not date_str:
                return ''
            
            # 様々な日付形式に対応
            date_str = str(date_str).strip()
            
            if '-' in date_str:
                # 2024-01-15 → 2024/01/15
                return date_str.replace('-', '/')
            
            return date_str
            
        except Exception:
            return date_str