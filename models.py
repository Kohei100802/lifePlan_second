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

# 支出カテゴリのモデル
class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 大項目名（例: 住居費、食費など）
    
    # リレーションシップ
    expense_items = db.relationship('ExpenseItem', backref='category', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'

# 支出項目のモデル
class ExpenseItem(db.Model):
    __tablename__ = 'expense_items'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # 小項目名（例: 家賃、電気代など）
    
    # リレーションシップ
    expense_values = db.relationship('ExpenseValue', backref='item', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ExpenseItem {self.name}>'

# 支出値のモデル（各ライフプランごとの支出項目の値）
class ExpenseValue(db.Model):
    __tablename__ = 'expense_values'
    
    id = db.Column(db.Integer, primary_key=True)
    lifeplan_id = db.Column(db.Integer, db.ForeignKey('lifeplans.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('expense_items.id'), nullable=False)
    amount = db.Column(db.Integer, default=0)  # 金額（万円）
    
    def __repr__(self):
        return f'<ExpenseValue for item {self.item_id} in plan {self.lifeplan_id}: {self.amount}万円>'

# 教育費用のモデル
class EducationCost(db.Model):
    __tablename__ = 'education_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    education_type = db.Column(db.String(20), nullable=False)  # 学校種類（幼稚園、小学校、中学校、高校、大学）
    institution_type = db.Column(db.String(20), nullable=False)  # 国公立/私立
    academic_field = db.Column(db.String(20), nullable=True)  # 文系/理系（大学のみ）
    annual_cost = db.Column(db.Integer, nullable=False)  # 年間費用（万円）
    
    def __repr__(self):
        if self.academic_field:
            return f'<EducationCost {self.education_type} {self.institution_type} {self.academic_field}: {self.annual_cost}万円/年>'
        else:
            return f'<EducationCost {self.education_type} {self.institution_type}: {self.annual_cost}万円/年>'

# 子供の情報モデル
class Child(db.Model):
    __tablename__ = 'children'
    
    id = db.Column(db.Integer, primary_key=True)
    lifeplan_id = db.Column(db.Integer, db.ForeignKey('lifeplans.id'), nullable=False)
    name = db.Column(db.String(50), nullable=True)  # 子供の名前（任意）
    birth_year = db.Column(db.Integer, nullable=False)  # 誕生年
    
    # リレーションシップ
    education_selections = db.relationship('EducationSelection', backref='child', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Child {self.name or "unnamed"} born in {self.birth_year}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'birth_year': self.birth_year,
            'education_selections': [es.to_dict() for es in self.education_selections]
        }
    
    def get_current_education_level(self, current_year):
        """現在の年齢から教育段階を判定"""
        age = current_year - self.birth_year
        
        if age < 3:
            return None  # まだ教育を受けていない
        elif age < 6:
            return '幼稚園'
        elif age < 12:
            return '小学校'
        elif age < 15:
            return '中学校'
        elif age < 18:
            return '高校'
        elif age < 22:
            return '大学'
        else:
            return None  # 教育終了

# 教育費用選択のモデル（各ライフプランごとの教育費用設定）
class EducationSelection(db.Model):
    __tablename__ = 'education_selections'
    
    id = db.Column(db.Integer, primary_key=True)
    lifeplan_id = db.Column(db.Integer, db.ForeignKey('lifeplans.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    education_type = db.Column(db.String(20), nullable=False)  # 学校種類
    institution_type = db.Column(db.String(20), nullable=False)  # 国公立/私立
    academic_field = db.Column(db.String(20), nullable=True)  # 文系/理系（大学のみ）
    
    def __repr__(self):
        if self.academic_field:
            return f'<EducationSelection for child {self.child_id}: {self.education_type} {self.institution_type} {self.academic_field}>'
        else:
            return f'<EducationSelection for child {self.child_id}: {self.education_type} {self.institution_type}>'
    
    def to_dict(self):
        result = {
            'id': self.id,
            'education_type': self.education_type,
            'institution_type': self.institution_type
        }
        if self.academic_field:
            result['academic_field'] = self.academic_field
        return result

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
    
    # 退職情報
    retirement_year_self = db.Column(db.Integer)  # 本人退職予定年
    retirement_year_spouse = db.Column(db.Integer)  # 配偶者退職予定年
    income_after_retirement_self = db.Column(db.Integer, default=0)  # 本人退職後年収（万円）
    income_after_retirement_spouse = db.Column(db.Integer, default=0)  # 配偶者退職後年収（万円）
    
    # 資産情報
    savings = db.Column(db.Integer, default=0)  # 預貯金（万円）
    investments = db.Column(db.Integer, default=0)  # 投資資産（万円）
    investment_return_rate = db.Column(db.Float, default=0.03)  # 投資収益率
    real_estate = db.Column(db.Integer, default=0)  # 不動産資産（万円）
    debt = db.Column(db.Integer, default=0)  # 負債（万円）
    
    # 支出単位（yearly または monthly）
    expense_unit = db.Column(db.String(10), default='yearly')

    # 支出情報（従来の項目 - 後方互換性のために残す）
    expense_housing = db.Column(db.Integer, default=0)  # 住居費
    expense_living = db.Column(db.Integer, default=0)  # 生活費
    expense_education = db.Column(db.Integer, default=0)  # 教育費
    expense_insurance = db.Column(db.Integer, default=0)  # 保険料
    expense_loan = db.Column(db.Integer, default=0)  # ローン返済
    expense_entertainment = db.Column(db.Integer, default=0)  # 娯楽費
    expense_transportation = db.Column(db.Integer, default=0)  # 交通費
    
    # リレーションシップ
    life_events = db.relationship('LifeEvent', backref='lifeplan', lazy='dynamic', cascade="all, delete-orphan")
    simulation_results = db.relationship('SimulationResult', backref='lifeplan', lazy='dynamic', cascade="all, delete-orphan")
    expense_values = db.relationship('ExpenseValue', backref='lifeplan', lazy='dynamic', cascade="all, delete-orphan")
    education_selections = db.relationship('EducationSelection', backref='lifeplan', lazy='dynamic', cascade="all, delete-orphan")
    children = db.relationship('Child', backref='lifeplan', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<LifePlan {self.name}>'
    
    def to_dict(self):
        base_dict = {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'birth_year': self.birth_year,
            'family_structure': self.family_structure,
            
            # 収入情報
            'income_self': self.income_self,
            'income_spouse': self.income_spouse,
            'income_increase_rate': self.income_increase_rate,
            
            # 退職情報
            'retirement_year_self': self.retirement_year_self,
            'retirement_year_spouse': self.retirement_year_spouse,
            'income_after_retirement_self': self.income_after_retirement_self,
            'income_after_retirement_spouse': self.income_after_retirement_spouse,
            
            # 資産情報
            'savings': self.savings,
            'investments': self.investments,
            'investment_return_rate': self.investment_return_rate,
            'real_estate': self.real_estate,
            'debt': self.debt,
            
            # 支出情報
            'expense_unit': self.expense_unit,
            'expense_housing': self.expense_housing,
            'expense_living': self.expense_living,
            'expense_education': self.expense_education,
            'expense_insurance': self.expense_insurance,
            'expense_loan': self.expense_loan,
            'expense_entertainment': self.expense_entertainment,
            'expense_transportation': self.expense_transportation,
            
            # 日付
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 新しい支出項目の辞書を追加
        expense_values_dict = {}
        for expense_value in self.expense_values:
            item = expense_value.item
            category = item.category
            
            if category.name not in expense_values_dict:
                expense_values_dict[category.name] = {}
            
            expense_values_dict[category.name][item.name] = expense_value.amount
        
        base_dict['detailed_expenses'] = expense_values_dict
        
        # 教育費用の選択情報
        education_selections_dict = {}
        for selection in self.education_selections:
            education_selections_dict[selection.education_type] = {
                'institution_type': selection.institution_type
            }
            if selection.academic_field:
                education_selections_dict[selection.education_type]['academic_field'] = selection.academic_field
        
        base_dict['education_selections'] = education_selections_dict
        
        return base_dict
    
    def get_total_expenses(self):
        """各支出カテゴリの合計を計算して返す"""
        total = 0
        total_by_category = {}
        
        # 詳細支出情報がある場合はそちらを使用
        if self.expense_values.count() > 0:
            for expense_value in self.expense_values:
                item = expense_value.item
                category = item.category
                
                if category.name not in total_by_category:
                    total_by_category[category.name] = 0
                
                total_by_category[category.name] += expense_value.amount
                total += expense_value.amount
        else:
            # 従来の支出情報を使用（ただし教育費用は除く - 別途計算するため）
            total = (self.expense_housing or 0) + \
                    (self.expense_living or 0) + \
                    (self.expense_insurance or 0) + \
                    (self.expense_loan or 0) + \
                    (self.expense_entertainment or 0) + \
                    (self.expense_transportation or 0)
            # 注意: expense_education は含めない（子供の年齢に基づいて別途計算）
        
        return {
            'total': total,
            'by_category': total_by_category
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