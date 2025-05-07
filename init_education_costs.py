import os
import sys
import sqlite3
from datetime import datetime

# 現在のディレクトリをプロジェクトのルートディレクトリに設定
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'instance', 'lifeplan.db')

def check_education_costs_table():
    """教育費用テーブルの存在確認"""
    print(f"データベースに接続: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # テーブルの存在を確認
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='education_costs'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # テーブル内のレコード数を取得
        cursor.execute("SELECT COUNT(*) FROM education_costs")
        count = cursor.fetchone()[0]
        print(f"education_costs テーブルには {count} 件のレコードが存在します。")
        
        # レコードの内容を表示
        if count > 0:
            cursor.execute("SELECT * FROM education_costs")
            records = cursor.fetchall()
            print("教育費用レコード:")
            for record in records:
                print(record)
        
        return count
    else:
        print("education_costs テーブルが存在しません。")
        return 0

def create_education_costs_table():
    """教育費用テーブルの作成"""
    print("education_costs テーブルを作成します...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # テーブルの作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS education_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        education_type TEXT NOT NULL,
        institution_type TEXT NOT NULL,
        academic_field TEXT,
        annual_cost INTEGER NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    
    print("education_costs テーブルを作成しました。")

def populate_education_costs():
    """教育費用テーブルにデフォルト値を投入"""
    print("教育費用テーブルにデフォルト値を設定します...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 既存のデータをクリア
    try:
        cursor.execute("DELETE FROM education_costs")
    except sqlite3.OperationalError:
        # テーブルが存在しない場合は作成
        create_education_costs_table()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    
    # デフォルトの教育費用データ
    education_costs = [
        # 幼稚園
        ('幼稚園', '国公立', None, 20),  # 年間20万円
        ('幼稚園', '私立', None, 40),    # 年間40万円
        
        # 小学校
        ('小学校', '国公立', None, 15),  # 年間15万円
        ('小学校', '私立', None, 100),   # 年間100万円
        
        # 中学校
        ('中学校', '国公立', None, 25),  # 年間25万円
        ('中学校', '私立', None, 120),   # 年間120万円
        
        # 高校
        ('高校', '国公立', None, 30),    # 年間30万円
        ('高校', '私立', None, 100),     # 年間100万円
        
        # 大学（文系）
        ('大学', '国公立', '文系', 54),  # 年間54万円
        ('大学', '私立', '文系', 86),    # 年間86万円
        
        # 大学（理系）
        ('大学', '国公立', '理系', 65),  # 年間65万円
        ('大学', '私立', '理系', 120)    # 年間120万円
    ]
    
    # データを挿入
    cursor.executemany(
        "INSERT INTO education_costs (education_type, institution_type, academic_field, annual_cost) VALUES (?, ?, ?, ?)",
        education_costs
    )
    
    conn.commit()
    conn.close()
    
    print(f"{len(education_costs)} 件の教育費用データを登録しました。")

def main():
    print(f"教育費用テーブル初期化スクリプト (実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("-" * 50)
    
    # 教育費用テーブルの状態を確認
    record_count = check_education_costs_table()
    
    # レコードが存在しない場合は初期データを投入
    if record_count == 0:
        print("\n教育費用テーブルにデフォルト値を設定します...")
        populate_education_costs()
        
        # 再度確認
        record_count = check_education_costs_table()
    
    print("-" * 50)
    print("処理が完了しました。")

if __name__ == "__main__":
    main()