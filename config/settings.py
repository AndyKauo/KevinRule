"""
配置管理系統
Configuration Management System

參考來源: reference/config.py
Patterns copied from reference, adapted for KevinRule project
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

class Settings:
    """應用程式設定"""

    def __init__(self):
        # 項目根目錄
        self.project_root = Path(__file__).parent.parent

        # API Keys
        self.finlab_api_key = os.getenv('FINLAB_API_KEY', '')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.line_notify_token = os.getenv('LINE_NOTIFY_TOKEN', '')
        self.trading_economics_api_key = os.getenv('TRADING_ECONOMICS_API_KEY', '')

        # Email配置
        self.email_smtp_host = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.email_smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.email_recipient = os.getenv('EMAIL_RECIPIENT', '')

        # 資料庫路徑
        self.duckdb_path = os.getenv('DUCKDB_PATH', 'data/kevinrule.duckdb')

        # 確保資料目錄存在
        data_dir = self.project_root / 'data'
        data_dir.mkdir(exist_ok=True)

        # 日誌目錄
        log_dir = self.project_root / 'logs'
        log_dir.mkdir(exist_ok=True)

        # 應用程式配置
        self.app_env = os.getenv('APP_ENV', 'development')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # 回測設定
        self.backtest_start_date = os.getenv('BACKTEST_START_DATE', '2020-01-01')
        self.backtest_commission = float(os.getenv('BACKTEST_COMMISSION', '0.001425'))
        self.backtest_tax = float(os.getenv('BACKTEST_TAX', '0.003'))
        self.backtest_slippage = float(os.getenv('BACKTEST_SLIPPAGE', '0.001'))

        # 策略設定
        self.max_positions = int(os.getenv('MAX_POSITIONS', '30'))
        self.rebalance_frequency = os.getenv('REBALANCE_FREQUENCY', 'M')
        self.min_market_cap = float(os.getenv('MIN_MARKET_CAP', '500000000'))  # 降低到5億
        self.min_liquidity_percentile = float(os.getenv('MIN_LIQUIDITY_PERCENTILE', '0.3'))

        # 提醒設定
        self.alert_cooldown_hours = int(os.getenv('ALERT_COOLDOWN_HOURS', '24'))
        self.enable_line_notify = os.getenv('ENABLE_LINE_NOTIFY', 'true').lower() == 'true'
        self.enable_email_notify = os.getenv('ENABLE_EMAIL_NOTIFY', 'false').lower() == 'true'

    def validate(self) -> tuple[bool, list[str]]:
        """驗證必要的配置是否已設定"""
        errors = []

        if not self.finlab_api_key:
            errors.append("❌ 缺少 FINLAB_API_KEY")

        if not self.anthropic_api_key:
            errors.append("⚠️  缺少 ANTHROPIC_API_KEY (AI功能將無法使用)")

        if self.enable_line_notify and not self.line_notify_token:
            errors.append("⚠️  啟用LINE通知但缺少 LINE_NOTIFY_TOKEN")

        if self.enable_email_notify and (not self.email_username or not self.email_password):
            errors.append("⚠️  啟用Email通知但缺少郵箱配置")

        is_valid = len([e for e in errors if e.startswith("❌")]) == 0
        return is_valid, errors

# 全局設定實例
settings = Settings()

# FinLab登入狀態（全局單例模式，參考 reference/config.py）
_finlab_logged_in = False

def ensure_finlab_login(force: bool = False, verbose: bool = True) -> bool:
    """
    確保FinLab已登入（全局單例）

    參考來源: reference/config.py

    Args:
        force: 強制重新登入
        verbose: 顯示登入訊息

    Returns:
        bool: 登入是否成功
    """
    global _finlab_logged_in

    # 如果已登入且不強制重新登入，直接返回
    if _finlab_logged_in and not force:
        if verbose:
            print("ℹ️  FinLab API 已登入（使用現有連線）")
        return True

    try:
        import finlab

        api_key = settings.finlab_api_key
        if not api_key:
            raise ValueError("未找到FINLAB_API_KEY，請檢查.env檔案")

        finlab.login(api_key)
        _finlab_logged_in = True

        if verbose:
            print("✅ FinLab API 登入成功")

        return True

    except ImportError:
        if verbose:
            print("❌ 無法導入finlab套件，請執行: pip install finlab")
        return False

    except Exception as e:
        if verbose:
            print(f"❌ FinLab API 登入失敗: {e}")
            print("請檢查:")
            print("  1. FINLAB_API_KEY是否正確")
            print("  2. 網路連線是否正常")
            print("  3. FinLab服務是否可用")
        return False

def reset_finlab_login():
    """重置FinLab登入狀態（用於測試或強制重新登入）"""
    global _finlab_logged_in
    _finlab_logged_in = False

if __name__ == "__main__":
    # 測試配置
    print("=== KevinRule 配置檢查 ===")
    print()

    # 驗證配置
    is_valid, errors = settings.validate()

    if errors:
        print("配置檢查結果:")
        for error in errors:
            print(f"  {error}")
        print()

    if is_valid:
        print("✅ 必要配置完整")
        print()
        print("嘗試登入FinLab...")
        ensure_finlab_login()
    else:
        print("❌ 配置不完整，請檢查.env檔案")
