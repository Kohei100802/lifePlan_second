import numpy as np
from datetime import datetime
from app import db
from models import LifeEvent, SimulationResult
from config import Config

def calculate_age(birth_year, year):
    """指定年の年齢を計算"""
    return year - birth_year

def calculate_income(base_income, year, start_year, increase_rate):
    """年収の計算（昇給率を考慮）"""
    years = year - start_year
    if years < 0:
        return 0
    return base_income * ((1 + increase_rate) ** years)

def calculate_expenses(
    lifeplan, 
    year, 
    age, 
    events_by_year,
    recurring_events
):
    """年間支出の計算"""
    # 基本支出
    expenses = (
        lifeplan.expense_housing +
        lifeplan.expense_living +
        lifeplan.expense_education +
        lifeplan.expense_insurance +
        lifeplan.expense_loan +
        lifeplan.expense_entertainment +
        lifeplan.expense_transportation
    )
    
    # 税金・社会保険料（簡易計算）
    total_income = lifeplan.income_self + lifeplan.income_spouse
    tax = total_income * Config.INCOME_TAX_RATE
    social_insurance = total_income * Config.SOCIAL_INSURANCE_RATE
    expenses += tax + social_insurance
    
    # その年のイベント支出
    if year in events_by_year:
        for event in events_by_year[year]:
            expenses += event.cost
    
    # 継続的なイベント支出
    for event in recurring_events:
        if event.event_year <= year and (event.recurring_end_year is None or event.recurring_end_year >= year):
            expenses += event.cost
    
    # 年齢による調整（例：老後は生活費が減る、子育て期間は増えるなど）
    if age >= 65:  # 老後
        expenses *= 0.9  # 生活費10%減と仮定
    
    return expenses

def calculate_investment_return(investment_amount, return_rate):
    """投資収益の計算"""
    return investment_amount * return_rate

def run_simulation(lifeplan):
    """ライフプランのシミュレーションを実行し、結果をデータベースに保存"""
    # 現在の年を取得
    current_year = datetime.now().year
    
    # シミュレーション開始年（現在年）
    start_year = current_year
    
    # シミュレーション終了年（100歳時点）
    end_year = lifeplan.birth_year + 100
    
    # ライフイベントを年ごとに整理
    events = LifeEvent.query.filter_by(lifeplan_id=lifeplan.id).all()
    events_by_year = {}
    recurring_events = []
    
    for event in events:
        # 継続的なイベントを別に保存
        if event.recurring:
            recurring_events.append(event)
        else:
            if event.event_year not in events_by_year:
                events_by_year[event.event_year] = []
            events_by_year[event.event_year].append(event)
    
    # 初期値
    savings = lifeplan.savings
    investments = lifeplan.investments
    
    # 各年のシミュレーション結果を計算
    for year in range(start_year, end_year + 1):
        age = calculate_age(lifeplan.birth_year, year)
        
        # 年齢が設定範囲外の場合はスキップ
        if age < Config.MIN_AGE or age > Config.MAX_AGE:
            continue
        
        # 収入計算
        if age < 65:  # 65歳未満は現役世代
            income_self = calculate_income(lifeplan.income_self, year, start_year, lifeplan.income_increase_rate)
            income_spouse = calculate_income(lifeplan.income_spouse, year, start_year, lifeplan.income_increase_rate)
            income = income_self + income_spouse
        else:  # 65歳以上は年金生活（簡易計算）
            income = (lifeplan.income_self + lifeplan.income_spouse) * 0.6  # 現役時代の60%と仮定
        
        # 支出計算
        expenses = calculate_expenses(lifeplan, year, age, events_by_year, recurring_events)
        
        # 投資収益計算
        investment_return = calculate_investment_return(investments, lifeplan.investment_return_rate)
        
        # 年間収支
        balance = income - expenses + investment_return
        
        # 貯蓄残高の更新
        if balance > 0:
            # 余剰金の半分を投資に回すと仮定
            investments += balance * 0.5
            savings += balance * 0.5
        else:
            # 赤字の場合は貯蓄から取り崩し
            savings += balance
            
            # 貯蓄がマイナスになった場合は投資から取り崩し
            if savings < 0:
                investments += savings
                savings = 0
                
                # 投資もマイナスになった場合は0に調整（借金は考慮しない）
                if investments < 0:
                    investments = 0
        
        # シミュレーション結果をデータベースに保存
        result = SimulationResult(
            lifeplan_id=lifeplan.id,
            year=year,
            age=age,
            income=int(income),
            expenses=int(expenses),
            savings=int(savings),
            investments=int(investments),
            balance=int(balance)
        )
        db.session.add(result)
    
    db.session.commit()
    return True