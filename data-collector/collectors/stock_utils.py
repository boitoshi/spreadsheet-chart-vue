"""株式データ処理ユーティリティ"""


def is_foreign_stock(symbol: str, currency: str | None = None) -> bool:
    """銘柄コードと通貨情報から外国株かどうかを判定

    Args:
        symbol: 銘柄コード（例: NVDA, 7974.T, 2432.T）
        currency: 通貨コード（例: USD, JPY）- オプション

    Returns:
        True: 外国株, False: 日本株

    判定ロジック:
    1. 通貨情報があればそれを優先（JPY以外なら外国株）
    2. 銘柄コードが数字で始まり .T/.JP で終わる → 日本株
    3. 銘柄コードが数字のみ（4桁） → 日本株
    4. それ以外（アルファベットのみ、等） → 外国株
    """
    # 通貨情報がある場合は優先
    if currency and currency != "JPY":
        return True
    if currency == "JPY":
        # 通貨がJPYでも、コードで再判定（円換算されている外国株の可能性）
        pass

    # 銘柄コードが空の場合
    if not symbol:
        return False

    symbol = symbol.strip()

    # 外国株の明確なパターン
    # 1. 香港株（.HK）、ロンドン株（.L）など
    foreign_suffixes = (".HK", ".L", ".DE", ".TO", ".AX", ".PA", ".SW")
    if symbol.endswith(foreign_suffixes):
        return True

    # 日本株の典型的なパターン
    # 2. 数字で始まり .T または .JP で終わる
    if symbol.endswith((".T", ".JP")) and symbol[0].isdigit():
        return False

    # 3. 数字のみ（4桁の証券コード）
    if symbol.isdigit() and len(symbol) == 4:
        return False

    # 4. アルファベットのみ、またはアルファベットで始まる → 外国株（米国株など）
    if symbol[0].isalpha():
        return True

    # デフォルトは日本株
    return False


def get_currency_from_symbol(symbol: str) -> str:
    """銘柄コードから想定通貨を推定

    Args:
        symbol: 銘柄コード

    Returns:
        通貨コード（USD, JPY, HKD等）
    """
    if not symbol:
        return "JPY"

    symbol = symbol.strip()

    # 日本株
    if not is_foreign_stock(symbol):
        return "JPY"

    # 外国株の場合、デフォルトはUSD
    # 香港株(.HK)
    if symbol.endswith(".HK"):
        return "HKD"

    # ロンドン株(.L)
    if symbol.endswith(".L"):
        return "GBP"

    # ドイツ株(.DE)
    if symbol.endswith(".DE"):
        return "EUR"

    # カナダ株(.TO)
    if symbol.endswith(".TO"):
        return "CAD"

    # オーストラリア株(.AX)
    if symbol.endswith(".AX"):
        return "AUD"

    # デフォルトはUSD（米国株）
    return "USD"
