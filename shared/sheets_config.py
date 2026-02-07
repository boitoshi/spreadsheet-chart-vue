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
    'PERFORMANCE': '損益レポート',
    'CURRENCY': '為替レート',
}

# ヘッダー定義
HEADERS = {
    'PORTFOLIO': [
        "銘柄コード", "銘柄名", "取得日", "取得単価（円）",
        "保有株数", "取得額合計", "通貨", "外国株フラグ",
        "最終更新", "備考", "取得単価（外貨）", "取得時為替レート"
    ],
    'DATA_RECORD': [
        "月末日付", "銘柄コード", "月末価格（円）", "最高値", "最安値",
        "平均価格", "月間変動率(%)", "平均出来高", "取得日時"
    ],
    'PERFORMANCE': [
        "日付", "銘柄コード", "銘柄名", "取得単価", "月末価格",
        "保有株数", "取得額", "評価額", "損益", "損益率(%)", "更新日時",
        "通貨", "取得単価（外貨）", "月末価格（外貨）",
        "取得時為替レート", "現在為替レート"
    ],
    'CURRENCY': [
        "取得日", "通貨ペア", "レート", "前回レート", "変動率(%)",
        "最高値", "最安値", "更新日時"
    ],
}

# スプレッドシート範囲定数（ヘッダーのカラム数に対応）
COLUMN_RANGES = {
    'PORTFOLIO': 'A1:L',
    'DATA_RECORD': 'A1:I',
    'PERFORMANCE': 'A1:P',
    'CURRENCY': 'A1:H',
}