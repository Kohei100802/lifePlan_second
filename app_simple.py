from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'dev-key-please-change-in-production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
CORS(app)

# 仮想データストア
users = {}
lifeplans = {}
life_events = {}
simulation_results = {}

@app.route('/')
def index():
    logged_in = 'user_id' in session
    user_lifeplans = []
    
    if logged_in:
        user_id = session['user_id']
        user_lifeplans = [plan for plan in lifeplans.values() if plan['user_id'] == user_id]
    
    html = '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ライフプランシミュレーター</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <style>
            body {
                padding-bottom: 20px;
                background-color: #f8f9fa;
            }
            .footer {
                background-color: #f5f5f5;
                padding: 1.5rem 0;
                color: #6c757d;
                border-top: 1px solid #dee2e6;
                margin-top: 3rem;
            }
            .jumbotron {
                background-color: #f8f9fa;
                border-radius: 0.5rem;
                padding: 2rem 1rem;
                margin-bottom: 2rem;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">ライフプランシミュレーター</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/">ホーム</a>
                        </li>
                        {% if logged_in %}
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard">ダッシュボード</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/lifeplan">ライフプラン一覧</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/lifeplan/create">新規作成</a>
                        </li>
                        {% endif %}
                    </ul>
                    <ul class="navbar-nav">
                        {% if logged_in %}
                        <li class="nav-item">
                            <a class="nav-link" href="/auth/logout">ログアウト</a>
                        </li>
                        {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="/auth/login">ログイン</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/auth/register">アカウント登録</a>
                        </li>
                        {% endif %}
                    </ul>
                </div>
            </div>
        </nav>
        
        <div class="container my-4">
            <div class="jumbotron text-center">
                <h1 class="display-4">ライフプランシミュレーター</h1>
                <p class="lead">あなたの将来の資産と生活をシミュレーションして、人生設計をサポートします。</p>
                <hr class="my-4">
                
                {% if logged_in %}
                    <div class="row mt-5">
                        <div class="col-md-6 offset-md-3">
                            <div class="card">
                                <div class="card-header bg-primary text-white">
                                    <h5 class="card-title mb-0">ライフプラン</h5>
                                </div>
                                <div class="card-body">
                                    {% if user_lifeplans %}
                                        <p>あなたのライフプラン一覧</p>
                                        <ul class="list-group">
                                            {% for plan in user_lifeplans %}
                                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                                    <div>
                                                        <a href="/lifeplan/{{ plan.id }}">{{ plan.name }}</a>
                                                        <small class="text-muted d-block">作成日: {{ plan.created_at }}</small>
                                                    </div>
                                                    <div>
                                                        <a href="/lifeplan/{{ plan.id }}" class="btn btn-sm btn-outline-primary">詳細</a>
                                                        <a href="/lifeplan/{{ plan.id }}/edit" class="btn btn-sm btn-outline-secondary">編集</a>
                                                    </div>
                                                </li>
                                            {% endfor %}
                                        </ul>
                                        <div class="mt-3">
                                            <a href="/lifeplan/create" class="btn btn-primary">新規作成</a>
                                        </div>
                                    {% else %}
                                        <p>まだライフプランが作成されていません。</p>
                                        <a href="/lifeplan/create" class="btn btn-primary">新規作成</a>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                {% else %}
                    <p>ライフプランを作成するには、まずログインしてください。</p>
                    <div>
                        <a class="btn btn-primary btn-lg m-2" href="/auth/login" role="button">ログイン</a>
                        <a class="btn btn-secondary btn-lg m-2" href="/auth/register" role="button">アカウント登録</a>
                    </div>
                {% endif %}
            </div>

            <div class="row mt-5">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">将来の資産を見える化</h5>
                            <p class="card-text">収入と支出のバランスを分析し、将来の資産残高をグラフで表示します。</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">ライフイベントを考慮</h5>
                            <p class="card-text">結婚、出産、住宅購入など、人生の重要なイベントを考慮したシミュレーションが可能です。</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">データのエクスポート</h5>
                            <p class="card-text">シミュレーション結果をCSVやJSONで出力して、他のツールでも活用できます。</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="footer bg-light py-3">
            <div class="container text-center">
                <span class="text-muted">© 2025 ライフプランシミュレーター</span>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return render_template_string(html, logged_in=logged_in, user_lifeplans=user_lifeplans)

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 簡易認証（本来はハッシュ化したパスワードを比較）
        for user_id, user in users.items():
            if user['email'] == email and user['password'] == password:
                session['user_id'] = user_id
                return redirect(url_for('index'))
                
        error = 'メールアドレスまたはパスワードが正しくありません。'
    else:
        error = None
    
    html = '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ログイン | ライフプランシミュレーター</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <style>
            body {
                padding-bottom: 20px;
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">ライフプランシミュレーター</a>
            </div>
        </nav>
        
        <div class="container my-4">
            {% if error %}
            <div class="alert alert-danger">
                {{ error }}
            </div>
            {% endif %}
            
            <div class="row">
                <div class="col-md-6 offset-md-3">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="card-title mb-0">ログイン</h5>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="/auth/login">
                                <div class="mb-3">
                                    <label for="email" class="form-label">メールアドレス</label>
                                    <input type="email" class="form-control" id="email" name="email" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="password" class="form-label">パスワード</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="remember_me" name="remember_me">
                                    <label class="form-check-label" for="remember_me">ログイン状態を保持する</label>
                                </div>
                                
                                <div class="d-grid gap-2">
                                    <button type="submit" class="btn btn-primary">ログイン</button>
                                </div>
                            </form>
                            
                            <div class="mt-3 text-center">
                                <p>アカウントをお持ちでない方は <a href="/auth/register">こちら</a> から登録できます。</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return render_template_string(html, error=error)

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        
        if password != password2:
            error = 'パスワードが一致しません。'
            return render_template_string(register_html, error=error)
        
        # メールアドレスの重複チェック
        for user in users.values():
            if user['email'] == email:
                error = 'このメールアドレスは既に使用されています。'
                return render_template_string(register_html, error=error)
        
        # ユーザー登録
        user_id = str(len(users) + 1)
        users[user_id] = {
            'id': user_id,
            'username': username,
            'email': email,
            'password': password,  # 本来はハッシュ化して保存
            'created_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        }
        
        # 自動ログイン
        session['user_id'] = user_id
        return redirect(url_for('index'))
    
    register_html = '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>アカウント登録 | ライフプランシミュレーター</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <style>
            body {
                padding-bottom: 20px;
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">ライフプランシミュレーター</a>
            </div>
        </nav>
        
        <div class="container my-4">
            {% if error %}
            <div class="alert alert-danger">
                {{ error }}
            </div>
            {% endif %}
            
            <div class="row">
                <div class="col-md-6 offset-md-3">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="card-title mb-0">アカウント登録</h5>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="/auth/register">
                                <div class="mb-3">
                                    <label for="username" class="form-label">ユーザー名</label>
                                    <input type="text" class="form-control" id="username" name="username" required minlength="3">
                                </div>
                                
                                <div class="mb-3">
                                    <label for="email" class="form-label">メールアドレス</label>
                                    <input type="email" class="form-control" id="email" name="email" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="password" class="form-label">パスワード</label>
                                    <input type="password" class="form-control" id="password" name="password" required minlength="8">
                                    <small class="form-text text-muted">8文字以上で設定してください。</small>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="password2" class="form-label">パスワード（確認用）</label>
                                    <input type="password" class="form-control" id="password2" name="password2" required minlength="8">
                                </div>
                                
                                <div class="d-grid gap-2">
                                    <button type="submit" class="btn btn-primary">登録</button>
                                </div>
                            </form>
                            
                            <div class="mt-3 text-center">
                                <p>既にアカウントをお持ちの方は <a href="/auth/login">こちら</a> からログインできます。</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return render_template_string(register_html, error=None)

@app.route('/auth/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = users.get(user_id)
    user_lifeplans = [plan for plan in lifeplans.values() if plan['user_id'] == user_id]
    
    html = '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ダッシュボード | ライフプランシミュレーター</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <style>
            body {
                padding-bottom: 20px;
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">ライフプランシミュレーター</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/">ホーム</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="/dashboard">ダッシュボード</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/lifeplan">ライフプラン一覧</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/lifeplan/create">新規作成</a>
                        </li>
                    </ul>
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/auth/logout">ログアウト</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        <div class="container my-4">
            <div class="row mb-4">
                <div class="col">
                    <h1 class="h2">ダッシュボード</h1>
                    <p class="lead">{{ username }}さん、こんにちは！</p>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-8">
                    <div class="card mb-4">
                        <div class="card-header d-flex justify-content-between">
                            <h5 class="card-title mb-0">あなたのライフプラン</h5>
                            <a href="/lifeplan/create" class="btn btn-sm btn-primary">新規作成</a>
                        </div>
                        <div class="card-body">
                            {% if lifeplans %}
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>プラン名</th>
                                                <th>作成日</th>
                                                <th>アクション</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for plan in lifeplans %}
                                            <tr>
                                                <td>{{ plan.name }}</td>
                                                <td>{{ plan.created_at }}</td>
                                                <td>
                                                    <div class="btn-group btn-group-sm" role="group">
                                                        <a href="/lifeplan/{{ plan.id }}" class="btn btn-outline-primary">表示</a>
                                                        <a href="/lifeplan/{{ plan.id }}/edit" class="btn btn-outline-secondary">編集</a>
                                                    </div>
                                                </td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            {% else %}
                                <div class="alert alert-info">
                                    <p class="mb-0">まだライフプランが作成されていません。「新規作成」ボタンから作成を始めましょう。</p>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="card-title mb-0">クイックリンク</h5>
                        </div>
                        <div class="card-body">
                            <div class="list-group">
                                <a href="/lifeplan/create" class="list-group-item list-group-item-action">
                                    <div class="d-flex w-100 justify-content-between">
                                        <h5 class="mb-1">新規ライフプラン作成</h5>
                                    </div>
                                    <p class="mb-1">新しいライフプランを作成します</p>
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">ヒント</h5>
                        </div>
                        <div class="card-body">
                            <p>ライフプランシミュレーターの使い方：</p>
                            <ul>
                                <li>基本情報を入力して新規ライフプランを作成</li>
                                <li>収入・支出・資産情報を詳細に設定</li>
                                <li>ライフイベント（結婚、出産など）を追加</li>
                                <li>シミュレーション結果をグラフや表で確認</li>
                                <li>必要に応じてデータをCSV/JSONでエクスポート</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="footer bg-light py-3 mt-5">
            <div class="container text-center">
                <span class="text-muted">© 2025 ライフプランシミュレーター</span>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return render_template_string(html, username=user['username'], lifeplans=user_lifeplans)

@app.route('/lifeplan')
def lifeplan_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_lifeplans = [plan for plan in lifeplans.values() if plan['user_id'] == user_id]
    
    html = '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ライフプラン一覧 | ライフプランシミュレーター</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <style>
            body {
                padding-bottom: 20px;
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">ライフプランシミュレーター</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/">ホーム</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard">ダッシュボード</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="/lifeplan">ライフプラン一覧</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/lifeplan/create">新規作成</a>
                        </li>
                    </ul>
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/auth/logout">ログアウト</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        <div class="container my-4">
            <div class="row mb-4">
                <div class="col d-flex justify-content-between align-items-center">
                    <h1 class="h2">ライフプラン一覧</h1>
                    <a href="/lifeplan/create" class="btn btn-primary">新規作成</a>
                </div>
            </div>

            <div class="row">
                <div class="col">
                    <div class="card">
                        <div class="card-body">
                            {% if user_lifeplans %}
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>プラン名</th>
                                                <th>現在年齢</th>
                                                <th>作成日</th>
                                                <th>最終更新日</th>
                                                <th>アクション</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for plan in user_lifeplans %}
                                            <tr>
                                                <td>{{ plan.name }}</td>
                                                <td>{{ plan.current_age }}</td>
                                                <td>{{ plan.created_at }}</td>
                                                <td>{{ plan.updated_at }}</td>
                                                <td>
                                                    <div class="btn-group btn-group-sm" role="group">
                                                        <a href="/lifeplan/{{ plan.id }}" class="btn btn-outline-primary">表示</a>
                                                        <a href="/lifeplan/{{ plan.id }}/edit" class="btn btn-outline-secondary">編集</a>
                                                        <a href="/lifeplan/{{ plan.id }}/simulate" class="btn btn-outline-info">シミュレーション</a>
                                                    </div>
                                                </td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            {% else %}
                                <div class="alert alert-info">
                                    <p class="mb-0">まだライフプランが作成されていません。「新規作成」ボタンから作成を始めましょう。</p>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="footer bg-light py-3 mt-5">
            <div class="container text-center">
                <span class="text-muted">© 2025 ライフプランシミュレーター</span>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return render_template_string(html, user_lifeplans=user_lifeplans)

@app.route('/lifeplan/create', methods=['GET', 'POST'])
def lifeplan_create():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        name = request.form.get('name')
        current_age = request.form.get('current_age')
        retirement_age = request.form.get('retirement_age')
        current_salary = request.form.get('current_salary')
        current_savings = request.form.get('current_savings')
        monthly_expenses = request.form.get('monthly_expenses')
        investment_return_rate = request.form.get('investment_return_rate')
        inflation_rate = request.form.get('inflation_rate')
        
        # ライフプランの作成
        plan_id = str(len(lifeplans) + 1)
        now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        
        lifeplans[plan_id] = {
            'id': plan_id,
            'user_id': user_id,
            'name': name,
            'current_age': int(current_age),
            'retirement_age': int(retirement_age),
            'current_salary': int(current_salary),
            'current_savings': int(current_savings),
            'monthly_expenses': int(monthly_expenses),
            'investment_return_rate': float(investment_return_rate),
            'inflation_rate': float(inflation_rate),
            'created_at': now,
            'updated_at': now
        }
        
        return redirect(url_for('lifeplan_view', plan_id=plan_id))
    
    html = '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>新規ライフプラン作成 | ライフプランシミュレーター</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <style>
            body {
                padding-bottom: 20px;
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">ライフプランシミュレーター</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/">ホーム</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard">ダッシュボード</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/lifeplan">ライフプラン一覧</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="/lifeplan/create">新規作成</a>
                        </li>
                    </ul>
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/auth/logout">ログアウト</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        <div class="container my-4">
            <div class="row mb-4">
                <div class="col">
                    <h1 class="h2">新規ライフプラン作成</h1>
                    <p class="lead">基本情報を入力してライフプランを作成しましょう。</p>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="card-title mb-0">基本情報</h5>
                        </div>
                        <div class="card-body">
                            <form method="POST">
                                <div class="mb-3">
                                    <label for="name" class="form-label">プラン名</label>
                                    <input type="text" class="form-control" id="name" name="name" required placeholder="例：マイライフプラン">
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="current_age" class="form-label">現在の年齢</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" id="current_age" name="current_age" min="18" max="100" required placeholder="例：30">
                                            <span class="input-group-text">歳</span>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="retirement_age" class="form-label">定年退職予定年齢</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" id="retirement_age" name="retirement_age" min="40" max="100" required placeholder="例：65">
                                            <span class="input-group-text">歳</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <h5 class="border-bottom pb-2 mt-4 mb-3">収入・支出・資産情報</h5>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="current_salary" class="form-label">現在の年収</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" id="current_salary" name="current_salary" min="0" required placeholder="例：5000000">
                                            <span class="input-group-text">円</span>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="current_savings" class="form-label">現在の貯蓄額</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" id="current_savings" name="current_savings" min="0" required placeholder="例：2000000">
                                            <span class="input-group-text">円</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="monthly_expenses" class="form-label">月々の支出</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" id="monthly_expenses" name="monthly_expenses" min="0" required placeholder="例：200000">
                                            <span class="input-group-text">円</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <h5 class="border-bottom pb-2 mt-4 mb-3">シミュレーション設定</h5>
                                
                                <div class="row mb-4">
                                    <div class="col-md-6">
                                        <label for="investment_return_rate" class="form-label">投資利回り（年率）</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" id="investment_return_rate" name="investment_return_rate" step="0.1" min="0" max="20" required placeholder="例：3.0">
                                            <span class="input-group-text">%</span>
                                        </div>
                                        <small class="form-text text-muted">長期的な投資の期待リターンを入力してください。</small>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="inflation_rate" class="form-label">インフレ率（年率）</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" id="inflation_rate" name="inflation_rate" step="0.1" min="0" max="10" required placeholder="例：1.0">
                                            <span class="input-group-text">%</span>
                                        </div>
                                        <small class="form-text text-muted">将来の物価上昇率を考慮します。</small>
                                    </div>
                                </div>
                                
                                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                    <a href="/lifeplan" class="btn btn-secondary me-md-2">キャンセル</a>
                                    <button type="submit" class="btn btn-primary">ライフプランを作成</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">ヒント</h5>
                        </div>
                        <div class="card-body">
                            <p>ライフプラン作成のポイント：</p>
                            <ul>
                                <li>現実的な数値を入力しましょう</li>
                                <li>一般的な投資利回りは2〜5%程度です</li>
                                <li>日本の長期的なインフレ率は0.5〜2%程度です</li>
                                <li>ライフプラン作成後、ライフイベントの追加ができます</li>
                                <li>収入や支出の変化も考慮しましょう</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="footer bg-light py-3 mt-5">
            <div class="container text-center">
                <span class="text-muted">© 2025 ライフプランシミュレーター</span>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/lifeplan/<plan_id>')
def lifeplan_view(plan_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    plan = lifeplans.get(plan_id)
    
    if not plan:
        return redirect(url_for('lifeplan_list'))
    
    if plan['user_id'] != user_id:
        return redirect(url_for('lifeplan_list'))
    
    # 関連するライフイベントを取得
    plan_life_events = [event for event in life_events.values() if event['plan_id'] == plan_id]
    
    # 簡易シミュレーション結果を生成
    plan_simulation = generate_simple_simulation(plan, plan_life_events)
    
    html = '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ plan.name }} | ライフプランシミュレーター</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                padding-bottom: 20px;
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">ライフプランシミュレーター</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/">ホーム</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard">ダッシュボード</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/lifeplan">ライフプラン一覧</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/lifeplan/create">新規作成</a>
                        </li>
                    </ul>
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/auth/logout">ログアウト</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        <div class="container my-4">
            <div class="row mb-4">
                <div class="col d-flex justify-content-between align-items-center">
                    <div>
                        <h1 class="h2">{{ plan.name }}</h1>
                        <p class="text-muted">作成日: {{ plan.created_at }}</p>
                    </div>
                    <div>
                        <a href="/lifeplan/{{ plan.id }}/edit" class="btn btn-secondary">編集</a>
                        <a href="/lifeplan/{{ plan.id }}/simulate" class="btn btn-primary">シミュレーション</a>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-lg-6">
                    <div class="card mb-4">
                        <div class="card-header bg-primary text-white">
                            <h5 class="card-title mb-0">基本情報</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <tbody>
                                        <tr>
                                            <th style="width: 40%">現在の年齢</th>
                                            <td>{{ plan.current_age }}歳</td>
                                        </tr>
                                        <tr>
                                            <th>定年退職予定年齢</th>
                                            <td>{{ plan.retirement_age }}歳</td>
                                        </tr>
                                        <tr>
                                            <th>現在の年収</th>
                                            <td>{{ '{:,}'.format(plan.current_salary) }}円</td>
                                        </tr>
                                        <tr>
                                            <th>現在の貯蓄額</th>
                                            <td>{{ '{:,}'.format(plan.current_savings) }}円</td>
                                        </tr>
                                        <tr>
                                            <th>月々の支出</th>
                                            <td>{{ '{:,}'.format(plan.monthly_expenses) }}円</td>
                                        </tr>
                                        <tr>
                                            <th>投資利回り（年率）</th>
                                            <td>{{ plan.investment_return_rate }}%</td>
                                        </tr>
                                        <tr>
                                            <th>インフレ率（年率）</th>
                                            <td>{{ plan.inflation_rate }}%</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-6">
                    <div class="card mb-4">
                        <div class="card-header d-flex justify-content-between align-items-center bg-primary text-white">
                            <h5 class="card-title mb-0">ライフイベント</h5>
                            <a href="/lifeplan/{{ plan.id }}/event/add" class="btn btn-sm btn-light">追加</a>
                        </div>
                        <div class="card-body">
                            {% if plan_life_events %}
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>年齢</th>
                                                <th>イベント</th>
                                                <th>金額</th>
                                                <th>アクション</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for event in plan_life_events %}
                                            <tr>
                                                <td>{{ event.age }}歳</td>
                                                <td>{{ event.name }}</td>
                                                <td>{{ '{:,}'.format(event.amount) }}円</td>
                                                <td>
                                                    <a href="/lifeplan/{{ plan.id }}/event/{{ event.id }}/edit" class="btn btn-sm btn-outline-secondary">編集</a>
                                                </td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            {% else %}
                                <div class="alert alert-info">
                                    <p class="mb-0">まだライフイベントが登録されていません。「追加」ボタンからライフイベントを追加しましょう。</p>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="card-title mb-0">資産推移シミュレーション</h5>
                        </div>
                        <div class="card-body">
                            <div style="height: 400px;">
                                <canvas id="assetsChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="footer bg-light py-3 mt-5">
            <div class="container text-center">
                <span class="text-muted">© 2025 ライフプランシミュレーター</span>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // 資産推移グラフ
            const ctx = document.getElementById('assetsChart').getContext('2d');
            const assetsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: {{ plan_simulation.labels|tojson }},
                    datasets: [
                        {
                            label: '資産残高',
                            data: {{ plan_simulation.assets|tojson }},
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderWidth: 2,
                            fill: true
                        },
                        {
                            label: '累計収入',
                            data: {{ plan_simulation.incomes|tojson }},
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 2,
                            fill: false
                        },
                        {
                            label: '累計支出',
                            data: {{ plan_simulation.expenses|tojson }},
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 2,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return value.toLocaleString() + '円';
                                }
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: '年齢'
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.raw.toLocaleString() + '円';
                                }
                            }
                        }
                    }
                }
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, plan=plan, plan_life_events=plan_life_events, plan_simulation=plan_simulation)

# 簡易シミュレーション関数
def generate_simple_simulation(plan, events=[]):
    current_age = plan['current_age']
    retirement_age = plan['retirement_age']
    max_age = 100  # 最大年齢
    
    # 収入、支出、資産の初期値
    annual_income = plan['current_salary']
    monthly_expense = plan['monthly_expenses']
    current_savings = plan['current_savings']
    
    investment_return_rate = plan['investment_return_rate'] / 100
    inflation_rate = plan['inflation_rate'] / 100
    
    # シミュレーション結果を格納する配列
    ages = []
    assets = []
    incomes = []
    expenses = []
    
    # イベントを年齢でソート
    sorted_events = sorted(events, key=lambda e: e['age'])
    event_index = 0
    
    cumulative_income = 0
    cumulative_expense = 0
    
    # 各年齢ごとにシミュレーション
    for age in range(current_age, max_age + 1):
        # 年齢を追加
        ages.append(age)
        
        # 当年のイベントを処理
        current_year_events = [e for e in sorted_events if e['age'] == age]
        for event in current_year_events:
            # イベントの金額を資産に加算/減算
            if event['type'] == 'income':
                current_savings += event['amount']
                cumulative_income += event['amount']
            elif event['type'] == 'expense':
                current_savings -= event['amount']
                cumulative_expense += event['amount']
        
        # 退職後は給与収入がなくなる
        if age >= retirement_age:
            annual_income = 0
        
        # 年間の収入を資産に加算
        current_savings += annual_income
        cumulative_income += annual_income
        
        # 年間の支出を資産から減算
        annual_expense = monthly_expense * 12
        current_savings -= annual_expense
        cumulative_expense += annual_expense
        
        # 投資リターンを資産に加算
        investment_return = current_savings * investment_return_rate
        current_savings += investment_return
        
        # インフレによる支出の増加
        monthly_expense *= (1 + inflation_rate)
        
        # 結果を配列に追加
        assets.append(round(current_savings))
        incomes.append(round(cumulative_income))
        expenses.append(round(cumulative_expense))
    
    return {
        'labels': ages,
        'assets': assets,
        'incomes': incomes,
        'expenses': expenses
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)