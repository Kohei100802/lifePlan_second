from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーションシップ
    lifeplans = db.relationship('LifePlan', backref='user', lazy='dynamic')
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class LifePlan(db.Model):
    __tablename__ = 'lifeplans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 基本情報
    birth_year = db.Column(db.Integer, nullable=False)
    family_structure = db.Column(db.String(100))  # 例: "夫婦+子供2人"
    
    # 収入情報
    income_self = db.Column(db.Integer, default=0)  # 本人年収（万円）
    income_spouse = db.Column(db.Integer, default=0)  # 配偶者年収（万円）
    income_increase_rate = db.Column(db.Float, default=0.02)  # 昇給率
    
    # 資産情報
    savings = db.Column(db.Integer, default=0)  # 預貯金（万円）
    investments = db.Column(db.Integer, default=0)  # 投資資産（万円）
    investment_return_rate = db.Column(db.Float, default=0.03)  # 投資収益率
    real_estate = db.Column(db.Integer, default=0)  # 不動産資産（万円）
    debt = db.Column(db.Integer, default=0)  # 負債（万円）
    
    # 支出情報
    expense_housing = db.Column(db.Integer, default=0)  # 住居費（万円/年）
    expense_living = db.Column(db.Integer, default=0)  # 生活費（万円/年）
    expense_education = db.Column(db.Integer, default=0)  # 教育費（万円/年）
    expense_insurance = db.Column(db.Integer, default=0)  # 保険料（万円/年）
    expense_loan = db.Column(db.Integer, default=0)  # ローン返済（万円/年）
    expense_entertainment = db.Column(db.Integer, default=0)  # 娯楽費（万円/年）
    expense_transportation = db.Column(db.Integer, default=0)  # 交通費（万円/年）
    
    # リレーションシップ
    life_events = db.relationship('LifeEvent', backref='lifeplan', lazy='dynamic', cascade="all, delete-orphan")
    simulation_results = db.relationship('SimulationResult', backref='lifeplan', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<LifePlan {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'birth_year': self.birth_year,
            'family_structure': self.family_structure,
            'income_self': self.income_self,
            'income_spouse': self.income_spouse,
            'income_increase_rate': self.income_increase_rate,
            'savings': self.savings,
            'investments': self.investments,
            'investment_return_rate': self.investment_return_rate,
            'real_estate': self.real_estate,
            'debt': self.debt,
            'expense_housing': self.expense_housing,
            'expense_living': self.expense_living,
            'expense_education': self.expense_education,
            'expense_insurance': self.expense_insurance,
            'expense_loan': self.expense_loan,
            'expense_entertainment': self.expense_entertainment,
            'expense_transportation': self.expense_transportation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class LifeEvent(db.Model):
    __tablename__ = 'life_events'
    
    id = db.Column(db.Integer, primary_key=True)
    lifeplan_id = db.Column(db.Integer, db.ForeignKey('lifeplans.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 結婚、出産、住宅購入など
    event_year = db.Column(db.Integer, nullable=False)  # イベント発生年
    description = db.Column(db.String(200))  # イベントの詳細説明
    cost = db.Column(db.Integer, default=0)  # 費用（万円）
    recurring = db.Column(db.Boolean, default=False)  # 継続的なイベントか
    recurring_end_year = db.Column(db.Integer)  # 継続終了年（任意）
    
    def __repr__(self):
        return f'<LifeEvent {self.event_type} at {self.event_year}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'lifeplan_id': self.lifeplan_id,
            'event_type': self.event_type,
            'event_year': self.event_year,
            'description': self.description,
            'cost': self.cost,
            'recurring': self.recurring,
            'recurring_end_year': self.recurring_end_year
        }

class SimulationResult(db.Model):
    __tablename__ = 'simulation_results'
    
    id = db.Column(db.Integer, primary_key=True)
    lifeplan_id = db.Column(db.Integer, db.ForeignKey('lifeplans.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)  # シミュレーション年
    age = db.Column(db.Integer, nullable=False)  # その年の年齢
    income = db.Column(db.Integer, default=0)  # 年収（万円）
    expenses = db.Column(db.Integer, default=0)  # 支出（万円）
    savings = db.Column(db.Integer, default=0)  # 貯蓄残高（万円）
    investments = db.Column(db.Integer, default=0)  # 投資残高（万円）
    balance = db.Column(db.Integer, default=0)  # 年間収支（万円）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SimulationResult Year:{self.year} Age:{self.age}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'lifeplan_id': self.lifeplan_id,
            'year': self.year,
            'age': self.age,
            'income': self.income,
            'expenses': self.expenses,
            'savings': self.savings,
            'investments': self.investments,
            'balance': self.balance,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }