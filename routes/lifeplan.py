from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import LifePlan, LifeEvent, SimulationResult
from forms import LifePlanForm, LifeEventForm
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
    if form.validate_on_submit():
        lifeplan = LifePlan(user_id=current_user.id)
        form.populate_obj(lifeplan)
        
        db.session.add(lifeplan)
        db.session.commit()
        
        # シミュレーション実行
        run_simulation(lifeplan)
        
        flash('ライフプランを作成しました。', 'success')
        return redirect(url_for('lifeplan.view', id=lifeplan.id))
    
    return render_template('lifeplan/create.html', form=form)

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
    
    # グラフ用データの準備
    chart_data = {
        'years': [r.year for r in results],
        'savings': [r.savings for r in results],
        'income': [r.income for r in results],
        'expenses': [r.expenses for r in results],
        'balance': [r.balance for r in results]
    }
    
    return render_template('lifeplan/view.html', lifeplan=lifeplan, results=results, events=events, chart_data=json.dumps(chart_data))

@lifeplan_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        flash('アクセス権限がありません。', 'danger')
        return redirect(url_for('lifeplan.index'))
    
    form = LifePlanForm(obj=lifeplan)
    if form.validate_on_submit():
        form.populate_obj(lifeplan)
        db.session.commit()
        
        # シミュレーション結果を削除して再計算
        SimulationResult.query.filter_by(lifeplan_id=lifeplan.id).delete()
        db.session.commit()
        
        # シミュレーション実行
        run_simulation(lifeplan)
        
        flash('ライフプランを更新しました。', 'success')
        return redirect(url_for('lifeplan.view', id=lifeplan.id))
    
    return render_template('lifeplan/edit.html', form=form, lifeplan=lifeplan)

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