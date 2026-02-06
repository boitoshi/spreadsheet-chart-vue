"""
Google Sheets API共通設定
data-collector と web-app の両方で使用
"""

# Google Sheets API スコープ
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# シート名定数
SHEET_NAMES = {
    'PORTFOLIO': 'ポートフォリオ',
    'DATA_RECORD': 'データ記録',  
    'PERFORMANCE': '損益レポート'
}

# ヘッダー定義
HEADERS = {
    'PORTFOLIO': [
        "銘柄コード", "銘柄名", "取得日", "取得単価",
        "取得通貨", "取得時レート", "取得単価（円）",
        "保有株数", "外国株フラグ", "最終更新", "備考"
    ],
    'DATA_RECORD': [
        "月末日付", "銘柄コード", "現地通貨価格", "通貨", "為替レート",
        "月末価格（円）", "最高値", "最安値",
        "平均価格", "月間変動率(%)", "平均出来高", "取得日時"
    ],
    'PERFORMANCE': [
        "日付", "銘柄コード", "銘柄名", "取得単価", "月末価格",
        "保有株数", "取得額", "評価額", "損益", "損益率(%)",
        "通貨", "現地通貨損益", "為替影響額", "更新日時"
    ]
}