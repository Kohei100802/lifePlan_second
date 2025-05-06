from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
from models import LifePlan, SimulationResult, LifeEvent
import pandas as pd
import json
import io
from datetime import datetime
import csv

api_bp = Blueprint('api', __name__)

@api_bp.route('/lifeplans', methods=['GET'])
@login_required
def get_lifeplans():
    lifeplans = LifePlan.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'status': 'success',
        'data': [lifeplan.to_dict() for lifeplan in lifeplans]
    })

@api_bp.route('/lifeplans/<int:id>', methods=['GET'])
@login_required
def get_lifeplan(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'アクセス権限がありません。'
        }), 403
    
    return jsonify({
        'status': 'success',
        'data': lifeplan.to_dict()
    })

@api_bp.route('/lifeplans/<int:id>/events', methods=['GET'])
@login_required
def get_lifeplan_events(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'アクセス権限がありません。'
        }), 403
    
    events = LifeEvent.query.filter_by(lifeplan_id=id).all()
    return jsonify({
        'status': 'success',
        'data': [event.to_dict() for event in events]
    })

@api_bp.route('/lifeplans/<int:id>/results', methods=['GET'])
@login_required
def get_lifeplan_results(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'アクセス権限がありません。'
        }), 403
    
    results = SimulationResult.query.filter_by(lifeplan_id=id).order_by(SimulationResult.year.asc()).all()
    return jsonify({
        'status': 'success',
        'data': [result.to_dict() for result in results]
    })

@api_bp.route('/lifeplans/<int:id>/export/json', methods=['GET'])
@login_required
def export_json(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'アクセス権限がありません。'
        }), 403
    
    # ライフプラン基本情報
    data = lifeplan.to_dict()
    
    # イベント情報を追加
    events = LifeEvent.query.filter_by(lifeplan_id=id).all()
    data['events'] = [event.to_dict() for event in events]
    
    # シミュレーション結果を追加
    results = SimulationResult.query.filter_by(lifeplan_id=id).order_by(SimulationResult.year.asc()).all()
    data['results'] = [result.to_dict() for result in results]
    
    # JSONファイルとして返す
    output = io.BytesIO()
    output.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    output.seek(0)
    
    filename = f"lifeplan_{lifeplan.name}_{datetime.now().strftime('%Y%m%d')}.json"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )

@api_bp.route('/lifeplans/<int:id>/export/csv', methods=['GET'])
@login_required
def export_csv(id):
    lifeplan = LifePlan.query.get_or_404(id)
    if lifeplan.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'アクセス権限がありません。'
        }), 403
    
    # シミュレーション結果をCSVに変換
    results = SimulationResult.query.filter_by(lifeplan_id=id).order_by(SimulationResult.year.asc()).all()
    
    # Pandasを使用してCSVを作成
    data = {
        '年': [r.year for r in results],
        '年齢': [r.age for r in results],
        '収入(万円)': [r.income for r in results],
        '支出(万円)': [r.expenses for r in results],
        '貯蓄残高(万円)': [r.savings for r in results],
        '投資残高(万円)': [r.investments for r in results],
        '年間収支(万円)': [r.balance for r in results]
    }
    
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8')
    
    # CSVファイルとして返す
    output_bytes = io.BytesIO()
    output_bytes.write(output.getvalue().encode('utf-8-sig'))  # BOMを含めてExcelで文字化けしないように
    output_bytes.seek(0)
    
    filename = f"lifeplan_{lifeplan.name}_{datetime.now().strftime('%Y%m%d')}.csv"
    return send_file(
        output_bytes,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )