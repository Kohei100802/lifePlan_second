from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, FloatField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from models import User

class LoginForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保持する')
    submit = SubmitField('ログイン')

class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('メールアドレス', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('パスワード', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('パスワード（確認用）', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('登録')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('このユーザー名は既に使用されています。')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('このメールアドレスは既に使用されています。')

class LifePlanForm(FlaskForm):
    name = StringField('プラン名', validators=[DataRequired(), Length(max=100)])
    birth_year = IntegerField('生年（西暦）', validators=[DataRequired(), NumberRange(min=1900, max=2023)])
    family_structure = StringField('家族構成', validators=[Length(max=100)])
    
    # 収入情報
    income_self = IntegerField('本人年収（万円）', validators=[NumberRange(min=0)])
    income_spouse = IntegerField('配偶者年収（万円）', validators=[NumberRange(min=0)])
    income_increase_rate = FloatField('昇給率（％）', validators=[NumberRange(min=0, max=100)])
    
    # 資産情報
    savings = IntegerField('預貯金（万円）', validators=[NumberRange(min=0)])
    investments = IntegerField('投資資産（万円）', validators=[NumberRange(min=0)])
    investment_return_rate = FloatField('投資収益率（％）', validators=[NumberRange(min=0, max=100)])
    real_estate = IntegerField('不動産資産（万円）', validators=[NumberRange(min=0)])
    debt = IntegerField('負債（万円）', validators=[NumberRange(min=0)])
    
    # 支出情報
    expense_housing = IntegerField('住居費（万円/年）', validators=[NumberRange(min=0)])
    expense_living = IntegerField('生活費（万円/年）', validators=[NumberRange(min=0)])
    expense_education = IntegerField('教育費（万円/年）', validators=[NumberRange(min=0)])
    expense_insurance = IntegerField('保険料（万円/年）', validators=[NumberRange(min=0)])
    expense_loan = IntegerField('ローン返済（万円/年）', validators=[NumberRange(min=0)])
    expense_entertainment = IntegerField('娯楽費（万円/年）', validators=[NumberRange(min=0)])
    expense_transportation = IntegerField('交通費（万円/年）', validators=[NumberRange(min=0)])
    
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(LifePlanForm, self).__init__(*args, **kwargs)
        # フォーム表示時に%表示のために100倍する
        if 'obj' in kwargs and kwargs['obj'] is not None:
            if kwargs['obj'].income_increase_rate is not None:
                self.income_increase_rate.data = kwargs['obj'].income_increase_rate * 100
            if kwargs['obj'].investment_return_rate is not None:
                self.investment_return_rate.data = kwargs['obj'].investment_return_rate * 100
    
    def populate_obj(self, obj):
        super(LifePlanForm, self).populate_obj(obj)
        # 保存時に%表示のために100で割る
        if self.income_increase_rate.data is not None:
            obj.income_increase_rate = self.income_increase_rate.data / 100
        if self.investment_return_rate.data is not None:
            obj.investment_return_rate = self.investment_return_rate.data / 100

class LifeEventForm(FlaskForm):
    event_type = SelectField('イベント種類', choices=[
        ('結婚', '結婚'),
        ('出産', '出産'),
        ('住宅購入', '住宅購入'),
        ('車購入', '車購入'),
        ('転職', '転職'),
        ('子供の進学', '子供の進学'),
        ('老後', '老後'),
        ('介護', '介護'),
        ('相続', '相続'),
        ('その他', 'その他')
    ])
    event_year = IntegerField('イベント発生年（西暦）', validators=[DataRequired(), NumberRange(min=1900, max=2100)])
    description = StringField('詳細説明', validators=[Length(max=200)])
    cost = IntegerField('費用（万円）', validators=[NumberRange(min=-10000, max=10000)])
    recurring = BooleanField('継続的なイベント')
    recurring_end_year = IntegerField('継続終了年（西暦）', validators=[Optional(), NumberRange(min=1900, max=2100)])
    
    submit = SubmitField('保存')