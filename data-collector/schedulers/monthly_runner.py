#!/usr/bin/env python3
"""
月次データ収集スケジューラー
cron等のスケジューラーから実行するためのスクリプト
"""

import sys
import os
from datetime import datetime, timedelta
import logging

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import PortfolioDataCollector
from config.settings import LOG_FILE, LOG_LEVEL


def setup_logging():
    """ログ設定"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def run_monthly_collection():
    """月次データ収集実行"""
    logger = logging.getLogger(__name__)
    
    try:
        # 前月のデータを収集
        today = datetime.now()
        if today.month == 1:
            prev_year = today.year - 1
            prev_month = 12
        else:
            prev_year = today.year
            prev_month = today.month - 1
        
        logger.info(f"月次データ収集開始: {prev_year}年{prev_month}月")
        
        collector = PortfolioDataCollector()
        success = collector.collect_monthly_data(prev_year, prev_month)
        
        if success:
            logger.info("月次データ収集完了")
            return True
        else:
            logger.error("月次データ収集失敗")
            return False
            
    except Exception as e:
        logger.error(f"月次データ収集エラー: {e}")
        return False


def main():
    """メイン関数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("月次データ収集スケジューラー開始")
    
    success = run_monthly_collection()
    
    if success:
        logger.info("月次データ収集スケジューラー正常終了")
        sys.exit(0)
    else:
        logger.error("月次データ収集スケジューラー異常終了")
        sys.exit(1)


if __name__ == "__main__":
    main()