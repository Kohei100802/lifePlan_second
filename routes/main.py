from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import LifePlan

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        # ログイン済みユーザーには自分のライフプラン一覧を表示
        lifeplans = LifePlan.query.filter_by(user_id=current_user.id).all()
        return render_template('index.html', lifeplans=lifeplans)
    else:
        # 未ログインユーザーにはウェルカムページを表示
        return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # ユーザーのライフプラン一覧を取得
    lifeplans = LifePlan.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/index.html', lifeplans=lifeplans)