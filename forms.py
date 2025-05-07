from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, FloatField, SelectField, TextAreaField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from models import User, ExpenseCategory, ExpenseItem, EducationCost

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

# 支出項目のフォーム
class ExpenseItemForm(FlaskForm):
    item_id = HiddenField('項目ID')
    item_name = HiddenField('項目名')
    amount = IntegerField('金額', validators=[NumberRange(min=0)])
    
    class Meta:
        # CSRFトークンを無効化（親フォームでチェック）
        csrf = False

# 子供のフォーム
class ChildForm(FlaskForm):
    name = StringField('名前', validators=[Optional(), Length(max=50)])
    birth_year = IntegerField('誕生年（西暦）', validators=[DataRequired(), NumberRange(min=1900, max=2100)])
    
    class Meta:
        # CSRFトークンを無効化（親フォームでチェック）
        csrf = False

# 教育費用選択のフォーム
class EducationSelectionForm(FlaskForm):
    child_id = HiddenField('子供ID')
    education_type = SelectField('学校種類', choices=[
        ('幼稚園', '幼稚園'),
        ('小学校', '小学校'),
        ('中学校', '中学校'),
        ('高校', '高校'),
        ('大学', '大学')
    ])
    institution_type = SelectField('学校タイプ', choices=[
        ('国公立', '国公立'),
        ('私立', '私立')
    ])
    academic_field = SelectField('専攻分野（大学のみ）', choices=[
        ('文系', '文系'),
        ('理系', '理系')
    ])
    
    class Meta:
        # CSRFトークンを無効化（親フォームでチェック）
        csrf = False

class LifePlanForm(FlaskForm):
    name = StringField('プラン名', validators=[DataRequired(), Length(max=100)])
    birth_year = IntegerField('生年（西暦）', validators=[DataRequired(), NumberRange(min=1900, max=2023)])
    family_structure = StringField('家族構成', validators=[Length(max=100)])
    
    # 収入情報
    income_self = IntegerField('本人年収（万円）', validators=[NumberRange(min=0)])
    income_spouse = IntegerField('配偶者年収（万円）', validators=[NumberRange(min=0)])
    income_increase_rate = FloatField('昇給率（％）', validators=[NumberRange(min=0, max=100)])
    
    # 退職情報
    retirement_year_self = IntegerField('本人退職予定年（西暦）', validators=[Optional(), NumberRange(min=1900, max=2100)])
    retirement_year_spouse = IntegerField('配偶者退職予定年（西暦）', validators=[Optional(), NumberRange(min=1900, max=2100)])
    income_after_retirement_self = IntegerField('本人退職後年収（万円）', validators=[NumberRange(min=0)])
    income_after_retirement_spouse = IntegerField('配偶者退職後年収（万円）', validators=[NumberRange(min=0)])
    
    # 資産情報
    savings = IntegerField('預貯金（万円）', validators=[NumberRange(min=0)])
    investments = IntegerField('投資資産（万円）', validators=[NumberRange(min=0)])
    investment_return_rate = FloatField('投資収益率（％）', validators=[NumberRange(min=0, max=100)])
    real_estate = IntegerField('不動産資産（万円）', validators=[NumberRange(min=0)])
    debt = IntegerField('負債（万円）', validators=[NumberRange(min=0)])
    
    # 支出情報の単位選択
    expense_unit = SelectField('支出単位', choices=[
        ('yearly', '年間'),
        ('monthly', '月間')
    ], default='yearly')
    
    # 支出情報（単位は「万円/年」または「万円/月」）- 従来の項目（後方互換性のため）
    expense_housing = IntegerField('住居費', validators=[NumberRange(min=0)])
    expense_living = IntegerField('生活費', validators=[NumberRange(min=0)])
    expense_education = IntegerField('教育費', validators=[NumberRange(min=0)])
    expense_insurance = IntegerField('保険料', validators=[NumberRange(min=0)])
    expense_loan = IntegerField('ローン返済', validators=[NumberRange(min=0)])
    expense_entertainment = IntegerField('娯楽費', validators=[NumberRange(min=0)])
    expense_transportation = IntegerField('交通費', validators=[NumberRange(min=0)])
    
    # 詳細支出項目（動的に生成）
    expense_items = {}
    
    # 教育費用選択（FormFieldではなく個別フィールドとして実装）
    # education_selections = FieldList(FormField(EducationSelectionForm), min_entries=0)
    
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(LifePlanForm, self).__init__(*args, **kwargs)
        # フォーム表示時に%表示のために100倍する
        if 'obj' in kwargs and kwargs['obj'] is not None:
            if kwargs['obj'].income_increase_rate is not None:
                self.income_increase_rate.data = kwargs['obj'].income_increase_rate * 100
            if kwargs['obj'].investment_return_rate is not None:
                self.investment_return_rate.data = kwargs['obj'].investment_return_rate * 100
        
        # 支出項目の動的生成
        self._create_expense_items()
    
    def _create_expense_items(self):
        """支出項目の動的なフィールド生成"""
        # カテゴリと項目の取得
        categories = ExpenseCategory.query.all()
        
        for category in categories:
            category_fields = []
            
            for item in category.expense_items:
                field_name = f"expense_item_{item.id}"
                setattr(self, field_name, IntegerField(item.name, validators=[NumberRange(min=0)], default=0))
                field = getattr(self, field_name)
                category_fields.append((item.id, item.name, field))
            
            self.expense_items[category.name] = category_fields
    
    def populate_obj(self, obj):
        """オブジェクトの値設定"""
        super(LifePlanForm, self).populate_obj(obj)
        
        # 保存時に%表示のために100で割る
        if self.income_increase_rate.data is not None:
            obj.income_increase_rate = self.income_increase_rate.data / 100
        if self.investment_return_rate.data is not None:
            obj.investment_return_rate = self.investment_return_rate.data / 100
        
        # 支出項目の値を保存
        from app import db
        from models import ExpenseValue
        
        # 既存の支出値を削除
        ExpenseValue.query.filter_by(lifeplan_id=obj.id).delete()
        
        # 新しい支出値を保存
        for category_name, items in self.expense_items.items():
            for item_id, item_name, field in items:
                if field.data and field.data > 0:
                    expense_value = ExpenseValue(
                        lifeplan_id=obj.id,
                        item_id=item_id,
                        amount=field.data
                    )
                    db.session.add(expense_value)
                    
        # 教育費用選択は直接HTMLからフォームデータを受け取って処理

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