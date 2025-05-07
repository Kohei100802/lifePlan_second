import numpy as np
from datetime import datetime
from app import db
from models import LifeEvent, SimulationResult, Child, EducationSelection, EducationCost
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
                    pass
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

def calculate_expenses(
    lifeplan, 
    year, 
    age, 
    events_by_year,
    recurring_events
):
    """年間支出の計算"""
    # 詳細な支出項目がある場合はそちらを使用
    if lifeplan.expense_values.count() > 0:
        # 支出値の合計を取得
        expenses_data = lifeplan.get_total_expenses()
        expenses = expenses_data['total']
        
        # 月間データの場合は年間に変換
        if lifeplan.expense_unit == 'monthly':
            expenses *= 12
            print(f"Converting monthly expenses to yearly: {expenses_data['total']} × 12 = {expenses}")
    else:
        # 従来の支出項目を使用（ただし教育費は除く - 別途calculate_education_expensesで計算するため）
        if lifeplan.expense_unit == 'monthly':
            # 月間データを年間に変換（月額 × 12）
            expenses = (
                (lifeplan.expense_housing or 0) * 12 +
                (lifeplan.expense_living or 0) * 12 +
                # (lifeplan.expense_education or 0) * 12 + # 教育費は別途計算するため除外
                (lifeplan.expense_insurance or 0) * 12 +
                (lifeplan.expense_loan or 0) * 12 +
                (lifeplan.expense_entertainment or 0) * 12 +
                (lifeplan.expense_transportation or 0) * 12
            )
            print(f"Using monthly expenses × 12 (excluding education): {expenses}")
        else:
            # 年間データはそのまま使用（ただし教育費は除く）
            expenses = (
                (lifeplan.expense_housing or 0) +
                (lifeplan.expense_living or 0) +
                # (lifeplan.expense_education or 0) + # 教育費は別途計算するため除外
                (lifeplan.expense_insurance or 0) +
                (lifeplan.expense_loan or 0) +
                (lifeplan.expense_entertainment or 0) +
                (lifeplan.expense_transportation or 0)
            )
            print(f"Using yearly expenses (excluding education): {expenses}")
    
    # 教育費用（新しいモデルから計算）
    education_expenses = calculate_education_expenses(lifeplan, year)
    if education_expenses > 0:
        print(f"Year {year}: Adding education expenses: {education_expenses} 万円")
    expenses += education_expenses
    
    # 従来のモデルの教育費（calculate_education_expensesと合わせて二重計上にならないように0にする）
    # lifeplan.expense_education はフォームから入力された固定値であり、calculate_education_expensesが子供の年齢に基づく動的計算のため
    
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
    
    # 初期値（負の値は0に調整）
    savings = max(0, lifeplan.savings or 0)
    investments = max(0, lifeplan.investments or 0)
    
    # print(f"Starting simulation with: savings={savings} 万円, investments={investments} 万円")
    
    # 各年のシミュレーション結果を計算
    for year in range(start_year, end_year + 1):
        age = calculate_age(lifeplan.birth_year, year)
        
        # 年齢が設定範囲外の場合はスキップ
        if age < Config.MIN_AGE or age > Config.MAX_AGE:
            continue
        
        # 収入計算
        # 本人の収入計算
        if lifeplan.retirement_year_self and year >= lifeplan.retirement_year_self:
            # 退職後は退職後年収を使用
            income_self = lifeplan.income_after_retirement_self
        else:
            # 現役時代は通常の年収計算
            income_self = calculate_income(lifeplan.income_self, year, start_year, lifeplan.income_increase_rate)
        
        # 配偶者の収入計算
        if lifeplan.retirement_year_spouse and year >= lifeplan.retirement_year_spouse:
            # 退職後は退職後年収を使用
            income_spouse = lifeplan.income_after_retirement_spouse
        else:
            # 現役時代は通常の年収計算
            income_spouse = calculate_income(lifeplan.income_spouse, year, start_year, lifeplan.income_increase_rate)
        
        # 総収入
        income = income_self + income_spouse
        
        # 支出計算
        expenses = calculate_expenses(lifeplan, year, age, events_by_year, recurring_events)
        
        # 投資収益計算
        investment_return = calculate_investment_return(investments, lifeplan.investment_return_rate)
        
        # 年間収支
        balance = income - expenses + investment_return
        
        # 貯蓄残高の更新
        # print(f"Year {year}: Balance = {balance} 万円, Savings before = {savings} 万円, Investments before = {investments} 万円")
        
        if balance > 0:
            # 余剰金の半分を投資に回すと仮定
            investment_portion = balance * 0.5
            savings_portion = balance * 0.5
            
            investments += investment_portion
            savings += savings_portion
            
            # print(f"  Positive balance: +{investment_portion} 万円 to investments, +{savings_portion} 万円 to savings")
        else:
            # 赤字の場合は貯蓄から取り崩し
            savings += balance
            # print(f"  Negative balance: {balance} 万円 from savings")
            
            # 貯蓄がマイナスになった場合は投資から取り崩し
            if savings < 0:
                amount_to_take = abs(savings)
                investments -= amount_to_take
                # print(f"  Not enough savings, taking {amount_to_take} 万円 from investments")
                savings = 0
                
                # 投資もマイナスになった場合は0に調整（借金は考慮しない）
                if investments < 0:
                    # print(f"  Warning: Investments would be negative ({investments} 万円), setting to 0")
                    investments = 0
        
        # print(f"  Savings after = {savings} 万円, Investments after = {investments} 万円")
        
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