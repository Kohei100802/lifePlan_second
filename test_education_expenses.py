#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a test Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import models after initializing db
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))

class LifePlan(db.Model):
    __tablename__ = 'lifeplans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    birth_year = db.Column(db.Integer, nullable=False)
    expense_unit = db.Column(db.String(10), default='yearly')
    expense_values = db.relationship('ExpenseValue', backref='lifeplan', lazy='dynamic')
    children = db.relationship('Child', backref='lifeplan', lazy='dynamic')

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    expense_items = db.relationship('ExpenseItem', backref='category', lazy='dynamic')

class ExpenseItem(db.Model):
    __tablename__ = 'expense_items'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    expense_values = db.relationship('ExpenseValue', backref='item', lazy='dynamic')

class ExpenseValue(db.Model):
    __tablename__ = 'expense_values'
    id = db.Column(db.Integer, primary_key=True)
    lifeplan_id = db.Column(db.Integer, db.ForeignKey('lifeplans.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('expense_items.id'), nullable=False)
    amount = db.Column(db.Integer, default=0)

class Child(db.Model):
    __tablename__ = 'children'
    id = db.Column(db.Integer, primary_key=True)
    lifeplan_id = db.Column(db.Integer, db.ForeignKey('lifeplans.id'), nullable=False)
    name = db.Column(db.String(50), nullable=True)
    birth_year = db.Column(db.Integer, nullable=False)
    education_selections = db.relationship('EducationSelection', backref='child', lazy='dynamic')
    
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

class EducationSelection(db.Model):
    __tablename__ = 'education_selections'
    id = db.Column(db.Integer, primary_key=True)
    lifeplan_id = db.Column(db.Integer, db.ForeignKey('lifeplans.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    education_type = db.Column(db.String(20), nullable=False)
    institution_type = db.Column(db.String(20), nullable=False)
    academic_field = db.Column(db.String(20), nullable=True)

class EducationCost(db.Model):
    __tablename__ = 'education_costs'
    id = db.Column(db.Integer, primary_key=True)
    education_type = db.Column(db.String(20), nullable=False)
    institution_type = db.Column(db.String(20), nullable=False)
    academic_field = db.Column(db.String(20), nullable=True)
    annual_cost = db.Column(db.Integer, nullable=False)

def calculate_education_expenses(lifeplan, year):
    """子供の教育費用計算"""
    education_expenses = 0
    
    # 子供ごとの教育費用を計算
    children = Child.query.filter_by(lifeplan_id=lifeplan.id).all()
    
    print(f"Calculating education expenses for year {year}, found {len(children)} children")
    
    for child in children:
        # 子供の現在の年齢
        child_age = year - child.birth_year
        
        # 教育段階を取得
        education_level = child.get_current_education_level(year)
        
        print(f"Child (id={child.id}, birth_year={child.birth_year}): age={child_age}, education_level={education_level}")
        
        if education_level:
            # 選択された教育設定を取得
            education_selection = EducationSelection.query.filter_by(
                child_id=child.id,
                education_type=education_level
            ).first()
            
            if education_selection:
                print(f"Found education selection: {education_selection.education_type}, {education_selection.institution_type}")
                # 教育費用を取得
                if education_level == '大学':
                    cost = EducationCost.query.filter_by(
                        education_type=education_level,
                        institution_type=education_selection.institution_type,
                        academic_field=education_selection.academic_field
                    ).first()
                else:
                    cost = EducationCost.query.filter_by(
                        education_type=education_level,
                        institution_type=education_selection.institution_type
                    ).first()
                
                if cost:
                    print(f"Found education cost: {cost.annual_cost} 万円/年")
                    education_expenses += cost.annual_cost
                else:
                    print(f"Education cost not found for {education_level}, {education_selection.institution_type}")
            else:
                # 教育選択がない場合は国公立をデフォルトとして使用
                print(f"No education selection found, using default (国公立)")
                if education_level == '大学':
                    cost = EducationCost.query.filter_by(
                        education_type=education_level,
                        institution_type='国公立',
                        academic_field='文系'
                    ).first()
                else:
                    cost = EducationCost.query.filter_by(
                        education_type=education_level,
                        institution_type='国公立'
                    ).first()
                
                if cost:
                    print(f"Using default education cost: {cost.annual_cost} 万円/年")
                    education_expenses += cost.annual_cost
    
    print(f"Total education expenses for year {year}: {education_expenses} 万円")
    return education_expenses

def main():
    # Create the database tables
    with app.app_context():
        db.create_all()
        
        # Sample data setup
        print("Setting up test data...")
        
        # Create a test user
        test_user = User(username="testuser", email="test@example.com", password_hash="dummy_hash")
        db.session.add(test_user)
        db.session.flush()
        
        # Create a test lifeplan
        current_year = datetime.now().year
        test_lifeplan = LifePlan(
            name="Test LifePlan",
            user_id=test_user.id,
            birth_year=current_year - 35,  # 35歳の設定
        )
        db.session.add(test_lifeplan)
        db.session.flush()
        
        # Add children to the lifeplan
        child1 = Child(
            lifeplan_id=test_lifeplan.id,
            name="Child 1",
            birth_year=current_year - 10  # 10歳（小学生）
        )
        child2 = Child(
            lifeplan_id=test_lifeplan.id,
            name="Child 2",
            birth_year=current_year - 18  # 18歳（大学生）
        )
        db.session.add(child1)
        db.session.add(child2)
        db.session.flush()
        
        # Add education selections
        # 小学校（国公立）の選択
        elementary_selection = EducationSelection(
            lifeplan_id=test_lifeplan.id,
            child_id=child1.id,
            education_type='小学校',
            institution_type='国公立'
        )
        
        # 大学（私立、文系）の選択
        university_selection = EducationSelection(
            lifeplan_id=test_lifeplan.id,
            child_id=child2.id,
            education_type='大学',
            institution_type='私立',
            academic_field='文系'
        )
        
        db.session.add(elementary_selection)
        db.session.add(university_selection)
        
        # Add education costs
        elementary_cost = EducationCost(
            education_type='小学校',
            institution_type='国公立',
            annual_cost=10
        )
        
        university_cost_public = EducationCost(
            education_type='大学',
            institution_type='国公立',
            academic_field='文系',
            annual_cost=53
        )
        
        university_cost_private = EducationCost(
            education_type='大学',
            institution_type='私立',
            academic_field='文系',
            annual_cost=100
        )
        
        db.session.add(elementary_cost)
        db.session.add(university_cost_public)
        db.session.add(university_cost_private)
        
        db.session.commit()
        
        print("\nTest data setup complete.\n")
        print("=" * 50)
        
        # Test the function
        print("Testing calculate_education_expenses function...\n")
        
        # 現在年での教育費用
        expenses_current = calculate_education_expenses(test_lifeplan, current_year)
        print(f"\nEducation expenses for current year ({current_year}): {expenses_current} 万円")
        
        # 5年後の教育費用
        expenses_future = calculate_education_expenses(test_lifeplan, current_year + 5)
        print(f"\nEducation expenses for future year ({current_year + 5}): {expenses_future} 万円")
        
        # 10年後の教育費用
        expenses_far_future = calculate_education_expenses(test_lifeplan, current_year + 10)
        print(f"\nEducation expenses for far future year ({current_year + 10}): {expenses_far_future} 万円")

if __name__ == "__main__":
    main()