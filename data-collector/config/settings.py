import os
from dotenv import load_dotenv

# .envファイルを読み込み（data-collectorディレクトリの.envファイル）
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Google Sheets API設定
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'my-service-account.json')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# デフォルト銘柄設定（外貨情報付き）
DEFAULT_STOCKS = {
    "7974.T": {
        "name": "任天堂", 
        "purchase_price": 5500, 
        "shares": 10, 
        "purchase_date": "2024-01-15",
        "currency": "JPY",
        "is_foreign": False
    },
    "2432.T": {
        "name": "DeNA", 
        "purchase_price": 2100, 
        "shares": 5, 
        "purchase_date": "2024-02-10",
        "currency": "JPY",
        "is_foreign": False
    },
    "NVDA": {
        "name": "エヌビディア", 
        "purchase_price": 850, 
        "shares": 2, 
        "purchase_date": "2024-03-05",
        "currency": "USD",
        "is_foreign": True
    },
    "AAPL": {
        "name": "Apple", 
        "purchase_price": 180, 
        "shares": 3, 
        "purchase_date": "2024-04-01",
        "currency": "USD",
        "is_foreign": True
    },
    "0700.HK": {
        "name": "テンセント", 
        "purchase_price": 350, 
        "shares": 5, 
        "purchase_date": "2024-05-01",
        "currency": "HKD",
        "is_foreign": True
    }
}

# 外貨設定
CURRENCY_SETTINGS = {
    # 為替レート取得対象通貨
    "supported_currencies": ["USD", "EUR", "GBP", "HKD", "AUD", "CAD", "SGD"],
    
    # 為替レート更新頻度（月次データ取得時に同時取得）
    "update_rates_with_stocks": True,
    
    # 円換算設定
    "auto_convert_to_jpy": True,
    
    # 外国株の識別パターン
    "foreign_stock_patterns": {
        "US": ["NASDAQ", "NYSE"],  # 米国株（シンボルのみ）
        "HK": [".HK"],             # 香港株
        "EU": [".PA", ".DE", ".AS", ".MI"],  # 欧州株
        "UK": [".L"],              # ロンドン株
        "AU": [".AX"],             # オーストラリア株
        "CA": [".TO"]              # カナダ株
    }
}

# ログ設定
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/data_collector.log')

# データ収集設定
DEFAULT_YEAR = 2024
DEFAULT_MONTH = 12