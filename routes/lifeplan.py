from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import LifePlan, LifeEvent, SimulationResult, EducationSelection, Child
from forms import LifePlanForm, LifeEventForm, ChildForm, EducationSelectionForm
import numpy as np
from datetime import datetime
import json
from utils.simulation import run_simulation

lifeplan_bp = Blueprint('lifeplan', __name__)

@lifeplan_bp.route('/')
@login_required
def index():
    lifeplans = LifePlan.query.filter_by(user_id=current_user.id).all()
    return render_template('lifeplan/index.html', lifeplans=lifeplans)

@lifeplan_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = LifePlanForm()
    if request.method == 'POST':
        print("フォームエラー：", form.errors)
        # バリデーションエラーが発生しても処理を継続
        # 必須フィールドの設定
        lifeplan = LifePlan(user_id=current_user.id)
        lifeplan.name = form.name.data or "マイライフプラン"
        lifeplan.birth_year = form.birth_year.data or 1990
        lifeplan.family_structure = form.family_structure.data or "単身"
        
        # デフォルト値を設定
        lifeplan.income_self = form.income_self.data or 0
        lifeplan.income_spouse = form.income_spouse.data or 0
        lifeplan.income_increase_rate = form.income_increase_rate.data/100 if form.income_increase_rate.data else 0.02
        lifeplan.savings = form.savings.data or 0
        lifeplan.investments = form.investments.data or 0
        lifeplan.investment_return_rate = form.investment_return_rate.data/100 if form.investment_return_rate.data else 0.03
        lifeplan.real_estate = form.real_estate.data or 0
        lifeplan.debt = form.debt.data or 0
        
        # 退職情報
        lifeplan.retirement_year_self = form.retirement_year_self.data
        lifeplan.retirement_year_spouse = form.retirement_year_spouse.data
        lifeplan.income_after_retirement_self = form.income_after_retirement_self.data or 0
        lifeplan.income_after_retirement_spouse = form.income_after_retirement_spouse.data or 0
        
        # 支出単位
        lifeplan.expense_unit = form.expense_unit.data or 'yearly'
        
        # 従来の支出情報
        lifeplan.expense_housing = form.expense_housing.data or 0
        lifeplan.expense_living = form.expense_living.data or 0
        lifeplan.expense_education = form.expense_education.data or 0
        lifeplan.expense_insurance = form.expense_insurance.data or 0
        lifeplan.expense_loan = form.expense_loan.data or 0
        lifeplan.expense_entertainment = form.expense_entertainment.data or 0
        lifeplan.expense_transportation = form.expense_transportation.data or 0
        
        try:
            db.session.add(lifeplan)
            db.session.commit()
            
            # 子供と教育費用選択データを処理
            process_children_data(request.form, lifeplan.id)
            
            # 子供が作成されているか確認し、なければデフォルトの子供を追加
            children = Child.query.filter_by(lifeplan_id=lifeplan.id).all()
            if not children:
                from datetime import datetime
                child = Child(
                    lifeplan_id=lifeplan.id,
                    name='お子様',
                    birth_year=datetime.now().year - 20
                )
                db.session.add(child)
                db.session.commit()
                
                # デフォルトの教育選択を追加
                default_education_types = ['幼稚園', '小学校', '中学校', '高校', '大学']
                for edu_type in default_education_types:
                    academic_field = '文系' if edu_type == '大学' else None
                    selection = EducationSelection(
                        lifeplan_id=lifeplan.id,
                        child_id=child.id,
                        education_type=edu_type,
                        institution_type='国公立',
                        academic_field=academic_field
                    )
                    db.session.add(selection)
                db.session.commit()
            
            # シミュレーション実行
            run_simulation(lifeplan)
            
            flash('ライフプランを作成しました。', 'success')
            return redirect(url_for('lifeplan.view', id=lifeplan.id))
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
            return redirect(url_for('lifeplan.index'))
    
    # 新規作成時のサンプル子供フォーム（空で1つだけ）
    child_form = ChildForm()
    
    return render_template('lifeplan/create.html', form=form, child_form=child_form)

def process_children_data(form_data, lifeplan_id):
    """フォームデータから子供情報と教育費用選択を処理"""
    # デバッグ: フォームデータを出力
    print("Processing children data for lifeplan_id:", lifeplan_id)
    print("Form data keys related to children:", [k for k in form_data.keys() if 'child-' in k or 'education-' in k])
    
    # 既存の子供データを一旦すべて取得（教育選択も含めてカスケード削除されるため）
    existing_children = Child.query.filter_by(lifeplan_id=lifeplan_id).all()
    existing_children_dict = {str(child.id): child for child in existing_children}
    
    # リクエストデータから子供情報を抽出
    children_data = {}
    child_prefix = 'child-'
    
    # デフォルトの子供データを作成（フォームに子供データがない場合のフォールバック）
    children_data['0'] = {
        'birth_year': '2005',  # 現在の年から20年前を仮定
        'name': 'お子様'
    }
    
    # 新しい形式の子供データを処理
    for key, value in form_data.items():
        if key.startswith(child_prefix) and '-' in key:
            parts = key.split('-')
            if len(parts) == 3:
                index = parts[1]
                field_name = parts[2]
                
                if index not in children_data:
                    children_data[index] = {'id': None}
                
                # childのIDが設定されている場合は保存
                if field_name == 'id' and value:
                    children_data[index]['id'] = value
                else:
                    children_data[index][field_name] = value
    
    # 教育費用選択データを抽出
    education_data = {}
    edu_prefix = 'education-'
    
    # デバッグ出力
    print("Form data education-related keys:")
    for key in form_data.keys():
        if 'education' in key:
            print(f"  {key}: {form_data[key]}")
    
    # 優先的に education- プレフィックスを処理
    for key, value in form_data.items():
        if key.startswith(edu_prefix) and '-' in key:
            parts = key.split('-')
            if len(parts) >= 4:  # education-{child_index}-{edu_index}-{field_name}
                child_index = parts[1]
                edu_index = parts[2]
                field_name = parts[3]
                
                if child_index not in education_data:
                    education_data[child_index] = {}
                
                if edu_index not in education_data[child_index]:
                    education_data[child_index][edu_index] = {}
                
                education_data[child_index][edu_index][field_name] = value
    
    # education_selections- プレフィックスのフォームデータを処理（フォールバック）
    education_selections_prefix = 'education_selections-'
    for key, value in form_data.items():
        if key.startswith(education_selections_prefix) and '-' in key:
            parts = key.split('-')
            if len(parts) == 3:  # education_selections-{index}-{field_name}
                edu_index = parts[1]
                field_name = parts[2]
                
                # デフォルトで最初の子供に割り当て
                child_index = '0'
                
                # すでに education- で処理されていれば無視
                if child_index in education_data and edu_index in education_data[child_index]:
                    continue
                
                if child_index not in education_data:
                    education_data[child_index] = {}
                
                if edu_index not in education_data[child_index]:
                    education_data[child_index][edu_index] = {}
                
                education_data[child_index][edu_index][field_name] = value
                
    print(f"Found {len(children_data)} children and {sum(len(eds) for eds in education_data.values() if eds)} education settings")
    
    # 子供情報を保存または更新
    processed_children = {}
    for index, data in children_data.items():
        child = None
        
        # 既存の子供情報があれば更新、なければ新規作成
        if 'id' in data and data['id'] and data['id'] in existing_children_dict:
            child = existing_children_dict[data['id']]
            # 基本情報を更新
            if 'name' in data:
                child.name = data['name']
            if 'birth_year' in data and data['birth_year']:
                child.birth_year = int(data['birth_year'])
            
            # 削除済みとマークされた子供は対象外
            existing_children_dict.pop(data['id'], None)
        else:
            # 新規作成
            if 'birth_year' in data and data['birth_year']:
                child = Child(
                    lifeplan_id=lifeplan_id,
                    name=data.get('name', ''),
                    birth_year=int(data['birth_year'])
                )
                db.session.add(child)
                # 一時的にフラッシュしてIDを取得
                db.session.flush()
        
        if child:
            processed_children[index] = child
    
    # 不要な子供データを削除
    for child_id, child in existing_children_dict.items():
        db.session.delete(child)
    
    # 教育費用選択を保存
    for child_index, edu_selections in education_data.items():
        if child_index in processed_children:
            child = processed_children[child_index]
            
            # 既存の教育選択をすべて削除
            EducationSelection.query.filter_by(child_id=child.id).delete()
            
            # 新しい教育選択を追加
            if edu_selections:
                for _, edu_data in edu_selections.items():
                    if 'education_type' in edu_data and 'institution_type' in edu_data:
                        academic_field = edu_data.get('academic_field')
                        # 大学以外はacademic_fieldを無視
                        if edu_data['education_type'] != '大学':
                            academic_field = None
                        
                        education_selection = EducationSelection(
                            lifeplan_id=lifeplan_id,
                            child_id=child.id,
                            education_type=edu_data['education_type'],
                            institution_type=edu_data['institution_type'],
                            academic_field=academic_field
                        )
                        db.session.add(education_selection)
            else:
                # デフォルトの教育選択を追加
                default_education_types = ['幼稚園', '小学校', '中学校', '高校', '大学']
                for edu_type in default_education_types:
                    academic_field = '文系' if edu_type == '大学' else None
                    education_selection = EducationSelection(
                        lifeplan_id=lifeplan_id,
                        child_id=child.id,
                        education_type=edu_type,
                        institution_type='国公立',
                        academic_field=academic_field
                    )
                    db.session.add(education_selection)
    
    db.session.commit()
    return processed_children

@lifeplan_bp.route('/<int:id>')
@login_required
def view(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        flash('アクセス権限がありません。', 'danger')
        return redirect(url_for('lifeplan.index'))
    
    # シミュレーション結果を取得
    results = SimulationResult.query.filter_by(lifeplan_id=lifeplan.id).order_by(SimulationResult.year.asc()).all()
    
    # ライフイベントを取得
    events = LifeEvent.query.filter_by(lifeplan_id=lifeplan.id).order_by(LifeEvent.event_year.asc()).all()
    
    # 現在の年を取得
    current_year = datetime.now().year
    
    # グラフ用データの準備
    chart_data = {
        'years': [r.year for r in results],
        'savings': [r.savings for r in results],
        'income': [r.income for r in results],
        'expenses': [r.expenses for r in results],
        'balance': [r.balance for r in results]
    }
    
    # EducationCostモデルをテンプレートに渡す
    from models import EducationCost
    
    return render_template('lifeplan/view.html', 
                         lifeplan=lifeplan, 
                         results=results, 
                         events=events, 
                         chart_data=json.dumps(chart_data),
                         current_year=current_year,
                         EducationCost=EducationCost)

@lifeplan_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        flash('アクセス権限がありません。', 'danger')
        return redirect(url_for('lifeplan.index'))
    
    form = LifePlanForm(obj=lifeplan)
    if request.method == 'POST':
        print("フォームエラー（編集）：", form.errors)
        
        # 必須フィールドの更新
        lifeplan.name = form.name.data or lifeplan.name or "マイライフプラン"
        lifeplan.birth_year = form.birth_year.data or lifeplan.birth_year or 1990
        lifeplan.family_structure = form.family_structure.data or lifeplan.family_structure or "単身"
        
        # デフォルト値を設定
        lifeplan.income_self = form.income_self.data if form.income_self.data is not None else lifeplan.income_self or 0
        lifeplan.income_spouse = form.income_spouse.data if form.income_spouse.data is not None else lifeplan.income_spouse or 0
        lifeplan.income_increase_rate = form.income_increase_rate.data/100 if form.income_increase_rate.data is not None else lifeplan.income_increase_rate or 0.02
        lifeplan.savings = form.savings.data if form.savings.data is not None else lifeplan.savings or 0
        lifeplan.investments = form.investments.data if form.investments.data is not None else lifeplan.investments or 0
        lifeplan.investment_return_rate = form.investment_return_rate.data/100 if form.investment_return_rate.data is not None else lifeplan.investment_return_rate or 0.03
        lifeplan.real_estate = form.real_estate.data if form.real_estate.data is not None else lifeplan.real_estate or 0
        lifeplan.debt = form.debt.data if form.debt.data is not None else lifeplan.debt or 0
        
        # 退職情報
        lifeplan.retirement_year_self = form.retirement_year_self.data
        lifeplan.retirement_year_spouse = form.retirement_year_spouse.data
        lifeplan.income_after_retirement_self = form.income_after_retirement_self.data if form.income_after_retirement_self.data is not None else lifeplan.income_after_retirement_self or 0
        lifeplan.income_after_retirement_spouse = form.income_after_retirement_spouse.data if form.income_after_retirement_spouse.data is not None else lifeplan.income_after_retirement_spouse or 0
        
        # 支出単位
        lifeplan.expense_unit = form.expense_unit.data or lifeplan.expense_unit or 'yearly'
        
        # 従来の支出情報
        lifeplan.expense_housing = form.expense_housing.data if form.expense_housing.data is not None else lifeplan.expense_housing or 0
        lifeplan.expense_living = form.expense_living.data if form.expense_living.data is not None else lifeplan.expense_living or 0
        lifeplan.expense_education = form.expense_education.data if form.expense_education.data is not None else lifeplan.expense_education or 0
        lifeplan.expense_insurance = form.expense_insurance.data if form.expense_insurance.data is not None else lifeplan.expense_insurance or 0
        lifeplan.expense_loan = form.expense_loan.data if form.expense_loan.data is not None else lifeplan.expense_loan or 0
        lifeplan.expense_entertainment = form.expense_entertainment.data if form.expense_entertainment.data is not None else lifeplan.expense_entertainment or 0
        lifeplan.expense_transportation = form.expense_transportation.data if form.expense_transportation.data is not None else lifeplan.expense_transportation or 0
        
        try:
            # 支出項目の保存
            if hasattr(form, '_create_expense_items') and callable(form._create_expense_items):
                # 既存の支出値を削除
                from models import ExpenseValue
                ExpenseValue.query.filter_by(lifeplan_id=lifeplan.id).delete()
                
                # 新しい支出値を保存
                for key, value in request.form.items():
                    if key.startswith('expense_item_') and value and int(value) > 0:
                        item_id = key.replace('expense_item_', '')
                        expense_value = ExpenseValue(
                            lifeplan_id=lifeplan.id,
                            item_id=int(item_id),
                            amount=int(value)
                        )
                        db.session.add(expense_value)
            
            db.session.commit()
            
            # 子供と教育費用選択データを処理
            process_children_data(request.form, lifeplan.id)
            
            # シミュレーション結果を削除して再計算
            SimulationResult.query.filter_by(lifeplan_id=lifeplan.id).delete()
            db.session.commit()
            
            # シミュレーション実行
            run_simulation(lifeplan)
            
            flash('ライフプランを更新しました。', 'success')
            return redirect(url_for('lifeplan.view', id=lifeplan.id))
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
            return redirect(url_for('lifeplan.index'))
    
    # 既存の子供情報を取得
    children = Child.query.filter_by(lifeplan_id=id).all()
    
    # 子供がいなければデフォルトの子供を作成
    if not children:
        from datetime import datetime
        child = Child(
            lifeplan_id=id,
            name='お子様',
            birth_year=datetime.now().year - 20
        )
        db.session.add(child)
        db.session.commit()
        children = [child]
    
    # 子供の教育選択情報を取得
    children_with_education = []
    education_selections = []
    for child in children:
        selections = EducationSelection.query.filter_by(child_id=child.id).all()
        
        # 教育選択がなければ各段階のデフォルト選択を作成
        if not selections:
            default_education_types = ['幼稚園', '小学校', '中学校', '高校', '大学']
            for edu_type in default_education_types:
                academic_field = '文系' if edu_type == '大学' else None
                selection = EducationSelection(
                    lifeplan_id=id,
                    child_id=child.id,
                    education_type=edu_type,
                    institution_type='国公立',
                    academic_field=academic_field
                )
                db.session.add(selection)
            
            db.session.commit()
            selections = EducationSelection.query.filter_by(child_id=child.id).all()
        
        education_selections.extend(selections)
        children_with_education.append({
            'child': child,
            'education_selections': selections
        })
    
    # 子供がいない場合は空のフォームを用意
    child_form = ChildForm()
    
    return render_template('lifeplan/edit.html', form=form, lifeplan=lifeplan, 
                         children_with_education=children_with_education,
                         child_form=child_form,
                         education_selections=education_selections)

@lifeplan_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        flash('アクセス権限がありません。', 'danger')
        return redirect(url_for('lifeplan.index'))
    
    db.session.delete(lifeplan)
    db.session.commit()
    
    flash('ライフプランを削除しました。', 'info')
    return redirect(url_for('lifeplan.index'))

@lifeplan_bp.route('/<int:id>/events')
@login_required
def events(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        flash('アクセス権限がありません。', 'danger')
        return redirect(url_for('lifeplan.index'))
    
    events = LifeEvent.query.filter_by(lifeplan_id=id).order_by(LifeEvent.event_year.asc()).all()
    return render_template('lifeplan/events.html', lifeplan=lifeplan, events=events)

@lifeplan_bp.route('/<int:id>/events/add', methods=['GET', 'POST'])
@login_required
def add_event(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        flash('アクセス権限がありません。', 'danger')
        return redirect(url_for('lifeplan.index'))
    
    form = LifeEventForm()
    if form.validate_on_submit():
        event = LifeEvent(lifeplan_id=id)
        form.populate_obj(event)
        
        db.session.add(event)
        db.session.commit()
        
        # シミュレーション結果を削除して再計算
        SimulationResult.query.filter_by(lifeplan_id=id).delete()
        db.session.commit()
        
        # シミュレーション実行
        run_simulation(lifeplan)
        
        flash('ライフイベントを追加しました。', 'success')
        return redirect(url_for('lifeplan.events', id=id))
    
    return render_template('lifeplan/add_event.html', form=form, lifeplan=lifeplan)

@lifeplan_bp.route('/<int:id>/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(id, event_id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        flash('アクセス権限がありません。', 'danger')
        return redirect(url_for('lifeplan.index'))
    
    event = LifeEvent.query.get_or_404(event_id)
    if event.lifeplan_id != id:
        flash('無効なイベントIDです。', 'danger')
        return redirect(url_for('lifeplan.events', id=id))
    
    form = LifeEventForm(obj=event)
    if form.validate_on_submit():
        form.populate_obj(event)
        db.session.commit()
        
        # シミュレーション結果を削除して再計算
        SimulationResult.query.filter_by(lifeplan_id=id).delete()
        db.session.commit()
        
        # シミュレーション実行
        run_simulation(lifeplan)
        
        flash('ライフイベントを更新しました。', 'success')
        return redirect(url_for('lifeplan.events', id=id))
    
    return render_template('lifeplan/edit_event.html', form=form, lifeplan=lifeplan, event=event)

@lifeplan_bp.route('/<int:id>/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(id, event_id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        flash('アクセス権限がありません。', 'danger')
        return redirect(url_for('lifeplan.index'))
    
    event = LifeEvent.query.get_or_404(event_id)
    if event.lifeplan_id != id:
        flash('無効なイベントIDです。', 'danger')
        return redirect(url_for('lifeplan.events', id=id))
    
    db.session.delete(event)
    db.session.commit()
    
    # シミュレーション結果を削除して再計算
    SimulationResult.query.filter_by(lifeplan_id=id).delete()
    db.session.commit()
    
    # シミュレーション実行
    run_simulation(lifeplan)
    
    flash('ライフイベントを削除しました。', 'info')
    return redirect(url_for('lifeplan.events', id=id))