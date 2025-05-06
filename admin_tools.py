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
parser.add_argument('command', choices=['init-db', 'create-admin', 'list-users', 'delete-user', 'backup', 'restore'], help='実行するコマンド')
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
        
        conn.commit()
        conn.close()
        
        print(f'データベースを初期化しました: {DB_FILE}')
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