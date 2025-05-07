#!/usr/bin/env python3
import os
import sys
import argparse
from dotenv import load_dotenv
import sqlite3
import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# .envファイルの読み込み
load_dotenv()

# 引数パーサーの設定
parser = argparse.ArgumentParser(description='ライフプランシミュレーター管理者ツール')
parser.add_argument('command', choices=['init-db', 'create-admin', 'list-users', 'delete-user', 'backup', 'restore', 'init-master-data'], help='実行するコマンド')
parser.add_argument('--username', help='ユーザー名（create-admin, delete-userコマンド用）')
parser.add_argument('--email', help='メールアドレス（create-adminコマンド用）')
parser.add_argument('--password', help='パスワード（create-adminコマンド用）')
parser.add_argument('--file', help='ファイルパス（backup, restoreコマンド用）')

args = parser.parse_args()

# データベースパスの設定
DB_PATH = os.environ.get('DATABASE_URL', 'sqlite:///instance/lifeplan.db')
if DB_PATH.startswith('sqlite:///'):
    DB_FILE = DB_PATH.replace('sqlite:///', '')
else:
    print('SQLite以外のデータベースはサポートしていません。')
    sys.exit(1)

def init_db():
    """データベースの初期化"""
    # データベースファイルが存在する場合は削除
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            print(f'既存のデータベースファイル {DB_FILE} を削除しました。')
    except Exception as e:
        print(f'データベースファイルの削除に失敗しました: {e}')
        return False
    
    # データベースディレクトリの作成
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    
    # 新しいデータベースファイルの作成
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # usersテーブル作成
        c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # lifeplansテーブル作成
        c.execute('''
        CREATE TABLE lifeplans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            birth_year INTEGER NOT NULL,
            family_structure VARCHAR(100),
            income_self INTEGER DEFAULT 0,
            income_spouse INTEGER DEFAULT 0,
            income_increase_rate FLOAT DEFAULT 0.02,
            savings INTEGER DEFAULT 0,
            investments INTEGER DEFAULT 0,
            investment_return_rate FLOAT DEFAULT 0.03,
            real_estate INTEGER DEFAULT 0,
            debt INTEGER DEFAULT 0,
            expense_unit VARCHAR(10) DEFAULT 'yearly',
            expense_housing INTEGER DEFAULT 0,
            expense_living INTEGER DEFAULT 0,
            expense_education INTEGER DEFAULT 0,
            expense_insurance INTEGER DEFAULT 0,
            expense_loan INTEGER DEFAULT 0,
            expense_entertainment INTEGER DEFAULT 0,
            expense_transportation INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # life_eventsテーブル作成
        c.execute('''
        CREATE TABLE life_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lifeplan_id INTEGER NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            event_year INTEGER NOT NULL,
            description VARCHAR(200),
            cost INTEGER DEFAULT 0,
            recurring BOOLEAN DEFAULT 0,
            recurring_end_year INTEGER,
            FOREIGN KEY (lifeplan_id) REFERENCES lifeplans (id) ON DELETE CASCADE
        )
        ''')
        
        # simulation_resultsテーブル作成
        c.execute('''
        CREATE TABLE simulation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lifeplan_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            age INTEGER NOT NULL,
            income INTEGER DEFAULT 0,
            expenses INTEGER DEFAULT 0,
            savings INTEGER DEFAULT 0,
            investments INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lifeplan_id) REFERENCES lifeplans (id) ON DELETE CASCADE
        )
        ''')
        
        # 支出カテゴリテーブル作成
        c.execute('''
        CREATE TABLE expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL
        )
        ''')
        
        # 支出項目テーブル作成
        c.execute('''
        CREATE TABLE expense_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name VARCHAR(50) NOT NULL,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id) ON DELETE CASCADE
        )
        ''')
        
        # 支出値テーブル作成
        c.execute('''
        CREATE TABLE expense_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lifeplan_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            amount INTEGER DEFAULT 0,
            FOREIGN KEY (lifeplan_id) REFERENCES lifeplans (id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES expense_items (id) ON DELETE CASCADE
        )
        ''')
        
        # 教育費用テーブル作成
        c.execute('''
        CREATE TABLE education_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            education_type VARCHAR(20) NOT NULL,
            institution_type VARCHAR(20) NOT NULL,
            academic_field VARCHAR(20),
            annual_cost INTEGER NOT NULL
        )
        ''')
        
        # 教育費用選択テーブル作成
        c.execute('''
        CREATE TABLE education_selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lifeplan_id INTEGER NOT NULL,
            education_type VARCHAR(20) NOT NULL,
            institution_type VARCHAR(20) NOT NULL,
            academic_field VARCHAR(20),
            FOREIGN KEY (lifeplan_id) REFERENCES lifeplans (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f'データベースを初期化しました: {DB_FILE}')
        
        # マスターデータを初期化
        print('マスターデータを初期化します...')
        init_master_data()
        
        return True
    except Exception as e:
        print(f'データベース初期化に失敗しました: {e}')
        return False

def create_admin(username, email, password):
    """管理者ユーザーの作成"""
    if not username or not email or not password:
        print('ユーザー名、メールアドレス、パスワードを指定してください。')
        return False
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # ユーザー名が既に存在するか確認
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone():
            print(f'ユーザー名 {username} は既に使用されています。')
            conn.close()
            return False
        
        # メールアドレスが既に存在するか確認
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        if c.fetchone():
            print(f'メールアドレス {email} は既に使用されています。')
            conn.close()
            return False
        
        # パスワードハッシュの生成
        password_hash = generate_password_hash(password)
        
        # ユーザーの作成
        c.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        
        conn.commit()
        conn.close()
        
        print(f'管理者ユーザー {username} を作成しました。')
        return True
    except Exception as e:
        print(f'管理者ユーザーの作成に失敗しました: {e}')
        return False

def list_users():
    """ユーザー一覧の表示"""
    try:
        conn = sqlite3.connect(DB_FILE)
        
        # Pandasを使用してデータフレームとして取得
        users_df = pd.read_sql_query('''
        SELECT id, username, email, created_at,
               (SELECT COUNT(*) FROM lifeplans WHERE user_id = users.id) AS lifeplan_count
        FROM users
        ORDER BY id
        ''', conn)
        
        conn.close()
        
        if len(users_df) == 0:
            print('ユーザーが登録されていません。')
        else:
            print(f'登録ユーザー数: {len(users_df)}')
            print(users_df)
        
        return True
    except Exception as e:
        print(f'ユーザー一覧の取得に失敗しました: {e}')
        return False

def delete_user(username):
    """ユーザーの削除"""
    if not username:
        print('ユーザー名を指定してください。')
        return False
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # ユーザーが存在するか確認
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        
        if not user:
            print(f'ユーザー {username} は存在しません。')
            conn.close()
            return False
        
        user_id = user[0]
        
        # 関連するライフプラン、イベント、シミュレーション結果を削除
        c.execute('DELETE FROM simulation_results WHERE lifeplan_id IN (SELECT id FROM lifeplans WHERE user_id = ?)', (user_id,))
        c.execute('DELETE FROM life_events WHERE lifeplan_id IN (SELECT id FROM lifeplans WHERE user_id = ?)', (user_id,))
        c.execute('DELETE FROM lifeplans WHERE user_id = ?', (user_id,))
        
        # ユーザーを削除
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        print(f'ユーザー {username} を削除しました。')
        return True
    except Exception as e:
        print(f'ユーザーの削除に失敗しました: {e}')
        return False

def backup(file_path):
    """データベースのバックアップ"""
    if not file_path:
        # デフォルトのバックアップファイル名を生成
        current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        file_path = f'backup_{current_time}.sqlite'
    
    try:
        import shutil
        shutil.copy2(DB_FILE, file_path)
        print(f'データベースをバックアップしました: {file_path}')
        return True
    except Exception as e:
        print(f'バックアップに失敗しました: {e}')
        return False

def restore(file_path):
    """データベースの復元"""
    if not file_path:
        print('復元するファイルパスを指定してください。')
        return False
    
    if not os.path.exists(file_path):
        print(f'ファイル {file_path} が存在しません。')
        return False
    
    try:
        # まず既存のDBのバックアップを取る
        current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_before_restore_{current_time}.sqlite'
        
        import shutil
        if os.path.exists(DB_FILE):
            shutil.copy2(DB_FILE, backup_file)
            print(f'既存のデータベースをバックアップしました: {backup_file}')
        
        # ファイルをコピー
        shutil.copy2(file_path, DB_FILE)
        print(f'データベースを復元しました: {file_path} -> {DB_FILE}')
        return True
    except Exception as e:
        print(f'復元に失敗しました: {e}')
        return False

def init_master_data():
    """マスターデータの初期化"""
    try:
        # Flaskアプリのインポートと初期化
        from app import create_app, db
        from models import ExpenseCategory, ExpenseItem, EducationCost
        
        app = create_app()
        with app.app_context():
            # 既存のマスターデータを確認
            expense_categories = ExpenseCategory.query.all()
            education_costs = EducationCost.query.all()
            
            # 支出カテゴリと項目のデータがなければ作成
            if not expense_categories:
                print("支出カテゴリと項目のマスターデータを作成します...")
                
                # カテゴリと項目のデータ
                categories_data = {
                    "住居費": ["家賃・住宅ローン", "管理費・修繕積立金", "火災保険料", "修繕費", "住民税・固定資産税"],
                    "食費": ["食材費", "外食費", "飲料費", "お菓子・スイーツ"],
                    "光熱・水道費": ["電気代", "水道代", "ガス代", "灯油代"],
                    "通信費": ["携帯電話料金", "インターネット料金", "固定電話料金", "郵便・宅配便", "サブスクリプション"],
                    "医療・健康": ["医療費", "薬・サプリメント", "保険料", "フィットネス費用"],
                    "衣服・美容": ["衣服費", "美容院・理容院", "化粧品", "アクセサリー", "クリーニング代"],
                    "日用品": ["日用雑貨", "家具・家電", "キッチン用品", "掃除用品", "ペット関連"],
                    "教養・娯楽": ["書籍・雑誌", "映画・音楽", "旅行費", "趣味費用", "スポーツ観戦"],
                    "交通・車両": ["公共交通費", "ガソリン代", "車検・整備費", "駐車場代", "高速道路料金", "自動車税"],
                    "教育費": ["学費", "習い事", "塾・予備校", "教材費"],
                    "交際費": ["交際費", "冠婚葬祭", "プレゼント代", "寄付・募金"],
                    "その他": ["その他", "予備費", "お小遣い"]
                }
                
                # カテゴリと項目を作成
                for category_name, item_names in categories_data.items():
                    category = ExpenseCategory(name=category_name)
                    db.session.add(category)
                    db.session.flush()  # IDを生成するためにフラッシュする
                    
                    for item_name in item_names:
                        item = ExpenseItem(
                            category_id=category.id,
                            name=item_name
                        )
                        db.session.add(item)
                
                db.session.commit()
                print("支出カテゴリと項目を作成しました。")
            else:
                print("支出カテゴリと項目は既に存在します。スキップします。")
            
            # 教育費用のマスターデータがなければ作成
            if not education_costs:
                print("教育費用のマスターデータを作成します...")
                
                # 教育費用のデータ（年間の学費・教育費用、単位: 万円）
                education_costs_data = [
                    # 幼稚園
                    {"education_type": "幼稚園", "institution_type": "国公立", "annual_cost": 20},
                    {"education_type": "幼稚園", "institution_type": "私立", "annual_cost": 40},
                    
                    # 小学校
                    {"education_type": "小学校", "institution_type": "国公立", "annual_cost": 15},
                    {"education_type": "小学校", "institution_type": "私立", "annual_cost": 100},
                    
                    # 中学校
                    {"education_type": "中学校", "institution_type": "国公立", "annual_cost": 25},
                    {"education_type": "中学校", "institution_type": "私立", "annual_cost": 120},
                    
                    # 高校
                    {"education_type": "高校", "institution_type": "国公立", "annual_cost": 30},
                    {"education_type": "高校", "institution_type": "私立", "annual_cost": 100},
                    
                    # 大学（文系）
                    {"education_type": "大学", "institution_type": "国公立", "academic_field": "文系", "annual_cost": 54},
                    {"education_type": "大学", "institution_type": "私立", "academic_field": "文系", "annual_cost": 86},
                    
                    # 大学（理系）
                    {"education_type": "大学", "institution_type": "国公立", "academic_field": "理系", "annual_cost": 65},
                    {"education_type": "大学", "institution_type": "私立", "academic_field": "理系", "annual_cost": 120}
                ]
                
                # 教育費用データを作成
                for cost_data in education_costs_data:
                    cost = EducationCost(**cost_data)
                    db.session.add(cost)
                
                db.session.commit()
                print("教育費用データを作成しました。")
            else:
                print("教育費用データは既に存在します。スキップします。")
            
            print("マスターデータの初期化が完了しました。")
            return True
    except Exception as e:
        print(f"マスターデータの初期化に失敗しました: {e}")
        return False

if __name__ == '__main__':
    # コマンドに応じた処理を実行
    if args.command == 'init-db':
        init_db()
    elif args.command == 'create-admin':
        create_admin(args.username, args.email, args.password)
    elif args.command == 'list-users':
        list_users()
    elif args.command == 'delete-user':
        delete_user(args.username)
    elif args.command == 'backup':
        backup(args.file)
    elif args.command == 'restore':
        restore(args.file)
    elif args.command == 'init-master-data':
        init_master_data()