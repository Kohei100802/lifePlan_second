from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS

# データベースの初期化
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # CORSの設定 - ローカル開発環境でも外部からアクセス可能に
    CORS(app)
    
    # データベースの初期化
    db.init_app(app)
    migrate.init_app(app, db)
    
    # ログイン管理の初期化
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'このページにアクセスするにはログインが必要です。'
    
    # ルートブループリントの登録
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.lifeplan import lifeplan_bp
    from routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(lifeplan_bp, url_prefix='/lifeplan')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # データベースのテーブル作成
    with app.app_context():
        db.create_all()
    
    return app