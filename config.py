import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

class Config:
    # Flask設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # データベース設定
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # セッション設定
    SESSION_TYPE = 'filesystem'
    
    # アプリケーション設定
    APP_NAME = 'ライフプランシミュレーター'
    
    # 年齢設定
    MIN_AGE = 20
    MAX_AGE = 100
    
    # シミュレーション初期値
    DEFAULT_ANNUAL_INCOME_INCREASE_RATE = 0.02  # 年収上昇率 2%
    DEFAULT_INVESTMENT_RETURN_RATE = 0.03  # 投資収益率 3%
    DEFAULT_INFLATION_RATE = 0.01  # インフレ率 1%
    
    # 自動計算設定
    INCOME_TAX_RATE = 0.1  # 所得税率（簡易版）
    SOCIAL_INSURANCE_RATE = 0.15  # 社会保険料率（簡易版）
    
    # 教育費デフォルト値（単位：万円）
    EDUCATION_COST = {
        "幼稚園": 50,  # 3年間の合計
        "小学校": 180,  # 6年間の合計
        "中学校": 150,  # 3年間の合計
        "高校": 180,  # 3年間の合計
        "大学": 400,  # 4年間の合計
    }
    
    # ライフイベントのデフォルトコスト（単位：万円）
    LIFE_EVENT_COST = {
        "結婚": 250,
        "出産": 50,
        "住宅購入": 3000,
        "車購入": 250,
        "転職": 0,
        "老後": 2000,  # 年間ベース
        "介護": 150,  # 年間ベース
        "相続": -1000,  # マイナスは収入
    }
