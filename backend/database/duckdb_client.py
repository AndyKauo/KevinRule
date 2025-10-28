"""
DuckDB 資料庫客戶端
DuckDB Database Client

實現每日快照 + 冪等ETL模式
Daily snapshot + idempotent ETL pattern
"""

import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from config.settings import settings


class DuckDBClient:
    """DuckDB 資料庫客戶端"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化DuckDB客戶端

        Args:
            db_path: 資料庫檔案路徑，默認使用settings中的配置
        """
        self.db_path = db_path or settings.duckdb_path

        # 確保資料目錄存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # 連接資料庫
        self.conn = duckdb.connect(self.db_path)

        # 初始化資料表
        self._init_schema()

    def _init_schema(self):
        """初始化資料庫結構"""
        print("🔨 初始化資料庫結構...")

        # 1. 價格數據快照表 (每日快照)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS price_snapshots (
                snapshot_date DATE NOT NULL,
                stock_id VARCHAR NOT NULL,
                close DOUBLE,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                volume BIGINT,
                amount BIGINT,
                PRIMARY KEY (snapshot_date, stock_id)
            )
        """)

        # 2. 市值快照表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS market_cap_snapshots (
                snapshot_date DATE NOT NULL,
                stock_id VARCHAR NOT NULL,
                market_cap DOUBLE,
                PRIMARY KEY (snapshot_date, stock_id)
            )
        """)

        # 3. 月營收表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS monthly_revenue (
                revenue_date DATE NOT NULL,
                stock_id VARCHAR NOT NULL,
                revenue DOUBLE,
                revenue_yoy DOUBLE,
                revenue_mom DOUBLE,
                PRIMARY KEY (revenue_date, stock_id)
            )
        """)

        # 4. 財務報表表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS financial_statements (
                report_date DATE NOT NULL,
                stock_id VARCHAR NOT NULL,
                total_assets DOUBLE,
                total_liabilities DOUBLE,
                equity DOUBLE,
                revenue DOUBLE,
                gross_profit DOUBLE,
                operating_income DOUBLE,
                net_income DOUBLE,
                operating_cash_flow DOUBLE,
                PRIMARY KEY (report_date, stock_id)
            )
        """)

        # 5. 策略選股結果表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS strategy_selections (
                selection_date DATE NOT NULL,
                strategy_name VARCHAR NOT NULL,
                stock_id VARCHAR NOT NULL,
                score DOUBLE,
                rank INTEGER,
                metadata JSON,
                PRIMARY KEY (selection_date, strategy_name, stock_id)
            )
        """)

        # 6. 用戶持股表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_watchlist (
                stock_id VARCHAR PRIMARY KEY,
                stock_name VARCHAR,
                buy_price DOUBLE,
                shares INTEGER,
                added_date DATE,
                notes TEXT
            )
        """)

        # 7. 提醒歷史表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                alert_id VARCHAR PRIMARY KEY,
                alert_type VARCHAR NOT NULL,
                stock_id VARCHAR,
                triggered_at TIMESTAMP NOT NULL,
                fingerprint VARCHAR,
                message TEXT,
                sent_via VARCHAR
            )
        """)

        # 8. ETL執行日誌表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_logs (
                log_id INTEGER PRIMARY KEY,
                etl_date DATE NOT NULL,
                etl_type VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                records_processed INTEGER,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        print("✅ 資料庫結構初始化完成")

    # ========== 價格數據操作 ==========

    def upsert_price_snapshot(self, df: pd.DataFrame, snapshot_date: date):
        """
        插入或更新價格快照（冪等操作）

        Args:
            df: 價格數據 DataFrame (columns: stock_id, close, open, high, low, volume, amount)
            snapshot_date: 快照日期
        """
        if df.empty:
            print(f"⚠️  價格數據為空，跳過 {snapshot_date}")
            return

        # 準備數據
        df = df.copy()
        df['snapshot_date'] = snapshot_date

        # 先刪除該日期的舊數據（冪等）
        self.conn.execute("""
            DELETE FROM price_snapshots
            WHERE snapshot_date = ?
        """, [snapshot_date])

        # 插入新數據
        self.conn.execute("""
            INSERT INTO price_snapshots
            SELECT * FROM df
        """)

        print(f"✅ 已插入 {len(df)} 筆價格數據 ({snapshot_date})")

    def get_price_snapshot(self, snapshot_date: Optional[date] = None) -> pd.DataFrame:
        """
        獲取價格快照

        Args:
            snapshot_date: 快照日期，None則獲取最新

        Returns:
            價格數據 DataFrame
        """
        if snapshot_date:
            query = """
                SELECT * FROM price_snapshots
                WHERE snapshot_date = ?
                ORDER BY stock_id
            """
            return self.conn.execute(query, [snapshot_date]).df()
        else:
            query = """
                SELECT * FROM price_snapshots
                WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM price_snapshots)
                ORDER BY stock_id
            """
            return self.conn.execute(query).df()

    # ========== 策略選股操作 ==========

    def upsert_strategy_selection(
        self,
        strategy_name: str,
        selection_date: date,
        selections: pd.DataFrame
    ):
        """
        插入或更新策略選股結果

        Args:
            strategy_name: 策略名稱
            selection_date: 選股日期
            selections: 選股結果 DataFrame (columns: stock_id, score, rank, metadata)
        """
        if selections.empty:
            print(f"⚠️  {strategy_name} 選股結果為空")
            return

        # 準備數據 - 只選擇表需要的欄位
        df = selections.copy()
        df['strategy_name'] = strategy_name
        df['selection_date'] = selection_date

        # 只保留資料表需要的6個欄位
        required_columns = ['selection_date', 'strategy_name', 'stock_id', 'score', 'rank', 'metadata']
        df = df[required_columns]

        # 先刪除該策略該日期的舊數據
        self.conn.execute("""
            DELETE FROM strategy_selections
            WHERE strategy_name = ? AND selection_date = ?
        """, [strategy_name, selection_date])

        # 插入新數據
        self.conn.execute("""
            INSERT INTO strategy_selections
            SELECT * FROM df
        """)

        print(f"✅ 已插入 {len(df)} 筆選股結果 ({strategy_name}, {selection_date})")

    def get_strategy_selections(
        self,
        strategy_name: Optional[str] = None,
        selection_date: Optional[date] = None,
        top_n: Optional[int] = None
    ) -> pd.DataFrame:
        """
        獲取策略選股結果

        Args:
            strategy_name: 策略名稱，None則獲取所有策略
            selection_date: 選股日期，None則獲取最新
            top_n: 只返回前N名

        Returns:
            選股結果 DataFrame
        """
        conditions = []
        params = []

        if strategy_name:
            conditions.append("strategy_name = ?")
            params.append(strategy_name)

        if selection_date:
            conditions.append("selection_date = ?")
            params.append(selection_date)
        else:
            conditions.append("selection_date = (SELECT MAX(selection_date) FROM strategy_selections)")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT * FROM strategy_selections
            WHERE {where_clause}
            ORDER BY strategy_name, rank
        """

        if top_n:
            query += f" LIMIT {top_n}"

        if params:
            return self.conn.execute(query, params).df()
        else:
            return self.conn.execute(query).df()

    # ========== 用戶持股操作 ==========

    def add_to_watchlist(
        self,
        stock_id: str,
        stock_name: str,
        buy_price: Optional[float] = None,
        shares: Optional[int] = None,
        notes: Optional[str] = None
    ):
        """
        添加股票到自選列表

        Args:
            stock_id: 股票代碼
            stock_name: 股票名稱
            buy_price: 買入價格
            shares: 持股數量
            notes: 備註
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO user_watchlist
            (stock_id, stock_name, buy_price, shares, added_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [stock_id, stock_name, buy_price, shares, date.today(), notes])

        print(f"✅ 已添加 {stock_id} ({stock_name}) 到自選列表")

    def remove_from_watchlist(self, stock_id: str):
        """從自選列表移除股票"""
        self.conn.execute("""
            DELETE FROM user_watchlist
            WHERE stock_id = ?
        """, [stock_id])

        print(f"✅ 已從自選列表移除 {stock_id}")

    def get_watchlist(self) -> pd.DataFrame:
        """獲取自選列表"""
        return self.conn.execute("""
            SELECT * FROM user_watchlist
            ORDER BY added_date DESC
        """).df()

    # ========== 提醒歷史操作 ==========

    def log_alert(
        self,
        alert_id: str,
        alert_type: str,
        message: str,
        stock_id: Optional[str] = None,
        fingerprint: Optional[str] = None,
        sent_via: Optional[str] = None
    ):
        """
        記錄提醒歷史

        Args:
            alert_id: 提醒ID
            alert_type: 提醒類型
            message: 提醒訊息
            stock_id: 股票代碼
            fingerprint: 指紋（用於去重）
            sent_via: 發送渠道
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO alert_history
            (alert_id, alert_type, stock_id, triggered_at, fingerprint, message, sent_via)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [alert_id, alert_type, stock_id, datetime.now(), fingerprint, message, sent_via])

    def get_recent_alerts(
        self,
        hours: int = 24,
        fingerprint: Optional[str] = None
    ) -> pd.DataFrame:
        """
        獲取最近的提醒（用於去重判斷）

        Args:
            hours: 查詢最近N小時
            fingerprint: 指紋過濾

        Returns:
            提醒歷史 DataFrame
        """
        query = """
            SELECT * FROM alert_history
            WHERE triggered_at >= datetime('now', '-{} hours')
        """.format(hours)

        if fingerprint:
            query += " AND fingerprint = ?"
            return self.conn.execute(query, [fingerprint]).df()
        else:
            return self.conn.execute(query).df()

    # ========== ETL日誌操作 ==========

    def log_etl_start(self, etl_date: date, etl_type: str) -> int:
        """記錄ETL開始"""
        result = self.conn.execute("""
            INSERT INTO etl_logs (etl_date, etl_type, status, started_at)
            VALUES (?, ?, 'running', ?)
            RETURNING log_id
        """, [etl_date, etl_type, datetime.now()]).fetchone()

        return result[0]

    def log_etl_complete(
        self,
        log_id: int,
        status: str,
        records_processed: int,
        error_message: Optional[str] = None
    ):
        """記錄ETL完成"""
        self.conn.execute("""
            UPDATE etl_logs
            SET status = ?,
                records_processed = ?,
                error_message = ?,
                completed_at = ?
            WHERE log_id = ?
        """, [status, records_processed, error_message, datetime.now(), log_id])

    # ========== 通用查詢 ==========

    def execute_query(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """
        執行自定義查詢

        Args:
            query: SQL查詢語句
            params: 查詢參數

        Returns:
            查詢結果 DataFrame
        """
        if params:
            return self.conn.execute(query, params).df()
        else:
            return self.conn.execute(query).df()

    def close(self):
        """關閉資料庫連接"""
        self.conn.close()
        print("✅ 資料庫連接已關閉")

    def __enter__(self):
        """Context manager進入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager退出"""
        self.close()


# ========== 測試代碼 ==========

def test_duckdb_client():
    """測試DuckDB客戶端"""
    print("=== DuckDB客戶端測試 ===")
    print()

    try:
        with DuckDBClient() as db:
            print("✅ DuckDB客戶端初始化成功")
            print()

            # 測試添加自選股
            print("測試添加自選股...")
            db.add_to_watchlist('2330', '台積電', 500.0, 10, '長期持有')
            db.add_to_watchlist('2317', '鴻海', 100.0, 20, '短線交易')

            # 獲取自選列表
            watchlist = db.get_watchlist()
            print(f"自選列表數量: {len(watchlist)}")
            print(watchlist)
            print()

            print("✅ 所有測試通過")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")


if __name__ == "__main__":
    test_duckdb_client()
