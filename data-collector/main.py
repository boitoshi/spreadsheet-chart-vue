#!/usr/bin/env python3
"""
データ収集メインスクリプト
月次株価データ取得とGoogle Sheets転記を実行
"""

import sys
import os
from datetime import datetime, timedelta

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'collectors'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from stock_collector import StockDataCollector
from sheets_writer import SheetsDataWriter
from settings import GOOGLE_APPLICATION_CREDENTIALS, SPREADSHEET_ID


class PortfolioDataCollector:
    """ポートフォリオデータ収集メインクラス"""
    
    def __init__(self):
        """初期化"""
        self.stock_collector = StockDataCollector()
        self.sheets_writer = SheetsDataWriter(
            GOOGLE_APPLICATION_CREDENTIALS, 
            SPREADSHEET_ID
        )
    
    def collect_monthly_data(self, year, month):
        """月次データ収集
        
        Args:
            year (int): 年
            month (int): 月
            
        Returns:
            bool: 成功/失敗
        """
        print(f"\n📊 {year}年{month}月のポートフォリオ分析を開始...")
        
        # Google Sheets設定
        if not self.sheets_writer.setup_google_sheets():
            print("❌ Google Sheets接続に失敗しました")
            return False
        
        # シート初期化
        self.sheets_writer.setup_portfolio_sheet()
        self.sheets_writer.setup_data_record_sheet()
        self.sheets_writer.setup_performance_sheet()
        
        # ポートフォリオ情報取得
        portfolio_data = self.sheets_writer.get_portfolio_data()
        if not portfolio_data:
            print("❌ ポートフォリオデータが取得できませんでした")
            return False
        
        results = []
        data_record_results = []
        
        # 月末日付を計算
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 各銘柄のデータ収集
        for holding in portfolio_data:
            symbol = holding['銘柄コード']
            name = holding['銘柄名']
            purchase_price = float(holding['取得単価（円）'])
            shares = int(holding['保有株数'])
            
            print(f"  📈 {name} ({symbol}) を処理中...")
            
            # 株価データ取得
            stock_data = self.stock_collector.get_stock_data(symbol, year, month)
            if stock_data is None:
                continue
            
            # メトリクス計算
            metrics = self.stock_collector.calculate_stock_metrics(
                stock_data, symbol, purchase_price, shares
            )
            if metrics is None:
                continue
            
            # Django backendが期待するデータ記録形式
            data_record_results.append([
                last_day.strftime('%Y-%m-%d'),  # 月末日付
                symbol,                         # 銘柄
                purchase_price,                 # 取得価格（円）
                metrics['month_end_price'],     # 報告月末価格（円）
                shares,                         # 保有株数
                metrics['highest_price'],       # 最高値
                metrics['lowest_price'],        # 最安値
                metrics['average_price'],       # 平均価格
                metrics['monthly_change'],      # 月間変動率(%)
                metrics['average_volume'],      # 平均出来高
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 取得日時
                f"自動取得 ({name})"             # 備考
            ])
            
            # 損益レポート用データ準備
            results.append([
                f"{year}-{month:02d}-末",
                symbol,
                name,
                purchase_price,
                metrics['month_end_price'],
                shares,
                metrics['purchase_amount'],
                metrics['current_amount'],
                metrics['profit_loss'],
                metrics['profit_rate'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            
            # 外貨情報の表示
            currency_info = ""
            if metrics.get('exchange_rate'):
                currency_info = f" [{metrics['currency']}: {metrics['exchange_rate']:.2f}円]"
            
            print(f"    ✅ {name}: {metrics['profit_loss']:+,.0f}円 ({metrics['profit_rate']:+.1f}%){currency_info}")
        
        # データをスプレッドシートに保存
        if data_record_results:
            self.sheets_writer.save_data_record(data_record_results)
        
        if results:
            self.sheets_writer.save_performance_data(results)
        
        if results:
            print(f"\n🎉 {year}年{month}月のデータ取得・分析が完了しました！")
            print("   Django backendからWebアプリで確認できます")
            self.sheets_writer.display_portfolio_summary(year, month)
            return True
        else:
            print("❌ データの取得に失敗しました")
            return False
    
    def run_interactive(self):
        """対話型実行"""
        print("=== 📊 ポートフォリオデータ収集システム ===")
        print("🎯 Django backend連携対応版")
        
        while True:
            try:
                print("\n=== メインメニュー ===")
                print("1. 月次データ取得・分析")
                print("2. ポートフォリオサマリー表示")
                print("3. シート初期化")
                print("4. 現在の為替レート表示")
                print("0. 終了")
                
                choice = input("\n選択してください: ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    # 月次データ取得
                    year = int(input("年を入力してください (例: 2024): "))
                    month = int(input("月を入力してください (1-12): "))
                    
                    if month < 1 or month > 12:
                        print("月は1-12の範囲で入力してください。")
                        continue
                    
                    self.collect_monthly_data(year, month)
                
                elif choice == '2':
                    # サマリー表示
                    if not self.sheets_writer.setup_google_sheets():
                        print("❌ Google Sheets接続に失敗しました")
                        continue
                    
                    year = int(input("表示する年を入力 (例: 2024): "))
                    month = int(input("表示する月を入力 (1-12): "))
                    self.sheets_writer.display_portfolio_summary(year, month)
                
                elif choice == '4':
                    # 為替レート表示
                    currency_converter = self.stock_collector.currency_converter
                    currency_converter.display_current_rates()
                
                elif choice == '3':
                    # シート初期化
                    if not self.sheets_writer.setup_google_sheets():
                        print("❌ Google Sheets接続に失敗しました")
                        continue
                    
                    confirm = input("⚠️ 全シートを初期化しますか？ (yes/no): ")
                    if confirm.lower() == 'yes':
                        self.sheets_writer.setup_portfolio_sheet()
                        self.sheets_writer.setup_data_record_sheet()
                        self.sheets_writer.setup_performance_sheet()
                        print("✅ シートの初期化が完了しました")
                
                else:
                    print("❌ 無効な選択です")
                    
            except ValueError:
                print("❌ 正しい数値を入力してください")
            except KeyboardInterrupt:
                print("\nアプリを終了します")
                break
            except Exception as e:
                print(f"❌ エラーが発生しました: {e}")


def main():
    """メイン関数"""
    if not SPREADSHEET_ID:
        print("❌ SPREADSHEET_IDが設定されていません。.envファイルを確認してください。")
        print("   例: SPREADSHEET_ID=your_spreadsheet_id_here")
        return
    
    print(f"📋 スプレッドシートID: {SPREADSHEET_ID}")
    print(f"🔑 認証ファイル: {GOOGLE_APPLICATION_CREDENTIALS}")
    
    collector = PortfolioDataCollector()
    
    # コマンドライン引数でバッチ実行も可能
    if len(sys.argv) == 3:
        try:
            year = int(sys.argv[1])
            month = int(sys.argv[2])
            print(f"バッチモード: {year}年{month}月のデータを収集します")
            collector.collect_monthly_data(year, month)
        except ValueError:
            print("❌ 年と月は数値で指定してください")
            print("使用例: python main.py 2024 12")
    else:
        # 対話型実行
        collector.run_interactive()


if __name__ == "__main__":
    main()