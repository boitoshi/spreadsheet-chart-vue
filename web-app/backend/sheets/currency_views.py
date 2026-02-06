import datetime
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def get_portfolio_data(request):
    """ポートフォリオデータ（外貨情報含む）を取得"""
    try:
        # 認証情報の設定
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        spreadsheet_id = settings.SPREADSHEET_ID

        if not credentials_path or not Path(credentials_path).exists():
            return JsonResponse(
                {"error": f"Service account file not found at {credentials_path}"},
                status=404,
                json_dumps_params={'ensure_ascii': False}
            )

        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )

        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # ポートフォリオシートからデータ取得
        RANGE_NAME = "ポートフォリオ!A1:J"  # 外貨情報含む
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])

        if not values:
            return JsonResponse(
                {"message": "No portfolio data found."},
                json_dumps_params={'ensure_ascii': False}
            )

        headers = values[0]
        data_rows = values[1:]

        # ヘッダーのインデックス取得
        try:
            symbol_idx = headers.index('銘柄コード')
            name_idx = headers.index('銘柄名')
            purchase_date_idx = headers.index('取得日')
            purchase_price_idx = headers.index('取得単価（円）')
            shares_idx = headers.index('保有株数')
            total_cost_idx = headers.index('取得額合計')
            currency_idx = headers.index('通貨')
            foreign_flag_idx = headers.index('外国株フラグ')
            updated_idx = headers.index('最終更新')
            notes_idx = headers.index('備考')
        except ValueError as e:
            return JsonResponse(
                {"error": f"Required column not found: {str(e)}"},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        portfolio_data = []
        for row in data_rows:
            if len(row) <= max([symbol_idx, name_idx, purchase_price_idx, shares_idx, currency_idx, foreign_flag_idx]):
                continue

            # 外国株フラグの判定
            is_foreign = row[foreign_flag_idx] == '○' if len(row) > foreign_flag_idx else False

            portfolio_data.append({
                "symbol": row[symbol_idx],
                "name": row[name_idx],
                "purchase_date": row[purchase_date_idx] if len(row) > purchase_date_idx else "",
                "purchase_price": float(row[purchase_price_idx]) if row[purchase_price_idx] else 0,
                "shares": int(row[shares_idx]) if row[shares_idx] else 0,
                "total_cost": row[total_cost_idx] if len(row) > total_cost_idx else "",
                "currency": row[currency_idx] if len(row) > currency_idx else "JPY",
                "is_foreign": is_foreign,
                "updated": row[updated_idx] if len(row) > updated_idx else "",
                "notes": row[notes_idx] if len(row) > notes_idx else ""
            })

        return JsonResponse(
            {"data": portfolio_data},
            json_dumps_params={'ensure_ascii': False}
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500,
            json_dumps_params={'ensure_ascii': False}
        )


def get_currency_rates(request):
    """為替レートデータを取得"""
    try:
        # クエリパラメータ
        start_date_str = request.GET.get('start_date', None)
        end_date_str = request.GET.get('end_date', None)
        currency_pair = request.GET.get('currency', None)

        # 認証情報の設定
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        spreadsheet_id = settings.SPREADSHEET_ID

        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )

        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # 為替レートシートからデータ取得
        RANGE_NAME = "為替レート!A1:H"
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])

        if not values:
            return JsonResponse(
                {"message": "No currency data found."},
                json_dumps_params={'ensure_ascii': False}
            )

        headers = values[0]
        data_rows = values[1:]

        # ヘッダーのインデックス取得
        try:
            date_idx = headers.index('取得日')
            pair_idx = headers.index('通貨ペア')
            rate_idx = headers.index('レート')
            prev_rate_idx = headers.index('前回レート')
            change_rate_idx = headers.index('変動率(%)')
            high_idx = headers.index('最高値')
            low_idx = headers.index('最安値')
            updated_idx = headers.index('更新日時')
        except ValueError as e:
            return JsonResponse(
                {"error": f"Required column not found: {str(e)}"},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        currency_data = []
        for row in data_rows:
            if len(row) <= max([date_idx, pair_idx, rate_idx]):
                continue

            # 日付フィルタリング
            try:
                row_date = datetime.datetime.strptime(row[date_idx], '%Y-%m-%d').date()
                if start_date_str:
                    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    if row_date < start_date:
                        continue
                if end_date_str:
                    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    if row_date > end_date:
                        continue
            except ValueError:
                continue

            # 通貨ペアフィルタリング
            if currency_pair and row[pair_idx] != currency_pair:
                continue

            currency_data.append({
                "date": row[date_idx],
                "currency_pair": row[pair_idx],
                "rate": float(row[rate_idx]) if row[rate_idx] else 0,
                "prev_rate": float(row[prev_rate_idx]) if len(row) > prev_rate_idx and row[prev_rate_idx] else 0,
                "change_rate": float(row[change_rate_idx]) if len(row) > change_rate_idx and row[change_rate_idx] else 0,
                "high": float(row[high_idx]) if len(row) > high_idx and row[high_idx] else 0,
                "low": float(row[low_idx]) if len(row) > low_idx and row[low_idx] else 0,
                "updated": row[updated_idx] if len(row) > updated_idx else ""
            })

        return JsonResponse(
            {"data": currency_data},
            json_dumps_params={'ensure_ascii': False}
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500,
            json_dumps_params={'ensure_ascii': False}
        )


def get_currency_portfolio_summary(request):
    """通貨別ポートフォリオサマリーを取得"""
    try:
        # まずポートフォリオデータを取得
        portfolio_response = get_portfolio_data(request)
        if portfolio_response.status_code != 200:
            return portfolio_response

        portfolio_data = portfolio_response.content
        import json
        portfolio_json = json.loads(portfolio_data)

        if 'error' in portfolio_json:
            return portfolio_response

        # 通貨別に集計
        currency_summary = {}
        total_portfolio_value = 0

        for stock in portfolio_json['data']:
            currency = stock['currency']
            total_cost = stock['purchase_price'] * stock['shares']

            if currency not in currency_summary:
                currency_summary[currency] = {
                    'currency': currency,
                    'total_cost': 0,
                    'total_value': 0,  # 現在価値（今後実装）
                    'stocks_count': 0,
                    'is_foreign': currency != 'JPY'
                }

            currency_summary[currency]['total_cost'] += total_cost
            currency_summary[currency]['stocks_count'] += 1
            total_portfolio_value += total_cost

        # パーセンテージ計算
        for currency_data in currency_summary.values():
            currency_data['percentage'] = (currency_data['total_cost'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0

        return JsonResponse(
            {
                "data": list(currency_summary.values()),
                "total_value": total_portfolio_value
            },
            json_dumps_params={'ensure_ascii': False}
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500,
            json_dumps_params={'ensure_ascii': False}
        )
