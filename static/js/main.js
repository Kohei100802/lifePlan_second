// main.js - メインJavaScriptファイル

document.addEventListener('DOMContentLoaded', function() {
    // ツールチップの初期化
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // 支出単位の切り替えに応じてラベルを更新
    const expenseUnitSelect = document.getElementById('expense_unit');
    if (expenseUnitSelect) {
        const updateExpenseLabels = () => {
            const isMonthly = expenseUnitSelect.value === 'monthly';
            const periodTexts = document.querySelectorAll('.expense-period');
            
            periodTexts.forEach(text => {
                text.textContent = isMonthly ? '月間' : '年間';
            });
            
            // 合計表示がある場合はその単位も更新
            const totalDisplay = document.getElementById('total_expense');
            if (totalDisplay) {
                const totalText = totalDisplay.textContent.split('万円')[0];
                totalDisplay.textContent = `${totalText}万円/${isMonthly ? '月' : '年'}`;
            }
            
            // カテゴリごとの合計表示を更新
            document.querySelectorAll('.category-total').forEach(element => {
                const totalText = element.textContent.split('万円')[0];
                element.textContent = `${totalText}万円/${isMonthly ? '月' : '年'}`;
            });
        };
        
        // 初期表示時
        updateExpenseLabels();
        
        // 選択変更時
        expenseUnitSelect.addEventListener('change', updateExpenseLabels);
        
        // カテゴリ内の項目値変更時に合計を再計算
        document.querySelectorAll('.expense-item').forEach(input => {
            input.addEventListener('input', calculateCategoryTotal);
        });
    }
    
    // 支出カテゴリごとの合計金額を計算して表示
    function calculateCategoryTotal(event) {
        // カテゴリの特定
        const categoryContainer = event.target.closest('.accordion-item');
        if (!categoryContainer) return;
        
        // そのカテゴリー内の全ての入力フィールドを取得
        const inputs = categoryContainer.querySelectorAll('.expense-item');
        const categoryTotalElement = categoryContainer.querySelector('.category-total');
        
        if (!categoryTotalElement) return;
        
        // 合計を計算
        let total = 0;
        inputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            total += value;
        });
        
        // 単位に応じたテキスト
        const isMonthly = document.getElementById('expense_unit').value === 'monthly';
        categoryTotalElement.textContent = `${total}万円/${isMonthly ? '月' : '年'}`;
    }
    
    // 初期表示時にカテゴリごとの合計を計算
    function initCategoryTotals() {
        const accordionItems = document.querySelectorAll('.accordion-item');
        accordionItems.forEach(item => {
            // カテゴリ名部分（ヘッダー）を取得
            const header = item.querySelector('.accordion-header');
            const headerButton = header.querySelector('.accordion-button');
            
            // カテゴリ内の全入力フィールド
            const inputs = item.querySelectorAll('.expense-item');
            
            // 合計計算
            let total = 0;
            inputs.forEach(input => {
                total += parseFloat(input.value) || 0;
            });
            
            // 合計表示用の要素がなければ作成
            if (!item.querySelector('.category-total')) {
                const totalElement = document.createElement('span');
                totalElement.className = 'category-total badge bg-success ms-2';
                const isMonthly = document.getElementById('expense_unit').value === 'monthly';
                totalElement.textContent = `${total}万円/${isMonthly ? '月' : '年'}`;
                headerButton.appendChild(totalElement);
            }
        });
    }
    
    // ページ読み込み時にカテゴリ合計を初期化
    document.addEventListener('DOMContentLoaded', function() {
        // 他の初期化コードの後
        if (document.getElementById('expense_unit')) {
            initCategoryTotals();
        }
    });
    
    // 教育費用の選択機能
    const educationSettings = document.getElementById('education-settings');
    if (educationSettings) {
        // 教育費用データ（年間の学費・教育費用、単位: 万円）
        const educationCosts = {
            '幼稚園': {
                '国公立': 20,
                '私立': 40
            },
            '小学校': {
                '国公立': 15,
                '私立': 100
            },
            '中学校': {
                '国公立': 25,
                '私立': 120
            },
            '高校': {
                '国公立': 30,
                '私立': 100
            },
            '大学': {
                '国公立': {
                    '文系': 54,
                    '理系': 65
                },
                '私立': {
                    '文系': 86,
                    '理系': 120
                }
            }
        };
        
        // 教育費用の表示更新
        function updateEducationCost(row) {
            const educationType = row.querySelector('.education-type').value;
            const institutionType = row.querySelector('.institution-type').value;
            const academicFieldContainer = row.querySelector('.academic-field-container');
            const academicField = row.querySelector('.academic-field');
            const costDisplay = row.querySelector('.education-cost');
            
            // 大学の場合は学問分野を表示
            if (educationType === '大学') {
                academicFieldContainer.style.display = '';
                const field = academicField.value;
                const cost = educationCosts[educationType][institutionType][field];
                costDisplay.textContent = `${cost} 万円/年`;
            } else {
                academicFieldContainer.style.display = 'none';
                const cost = educationCosts[educationType][institutionType];
                costDisplay.textContent = `${cost} 万円/年`;
            }
        }
        
        // 既存の教育費用行の更新
        document.querySelectorAll('.education-row').forEach(row => {
            updateEducationCost(row);
            
            // イベントリスナーの設定
            row.querySelector('.education-type').addEventListener('change', () => updateEducationCost(row));
            row.querySelector('.institution-type').addEventListener('change', () => updateEducationCost(row));
            if (row.querySelector('.academic-field')) {
                row.querySelector('.academic-field').addEventListener('change', () => updateEducationCost(row));
            }
            row.querySelector('.remove-education').addEventListener('click', () => row.remove());
        });
        
        // 子供の管理機能 -----------------------------------------------------
        
        // 子供カウンター
        let childCounter = document.querySelectorAll('.child-row:not(#child-template)').length;
        
        // 子供追加ボタンの処理
        const addChildButton = document.getElementById('add-child');
        if (addChildButton) {
            addChildButton.addEventListener('click', () => {
                // 子供のテンプレートをクローン
                const template = document.getElementById('child-template');
                const newChild = template.cloneNode(true);
                newChild.classList.remove('d-none');
                newChild.id = '';
                
                // インデックスを更新
                newChild.querySelector('.child-index').textContent = childCounter + 1;
                
                // フィールド名を更新
                const nameInput = newChild.querySelector('.child-name');
                const birthYearInput = newChild.querySelector('.child-birth-year');
                
                nameInput.name = `child-${childCounter}-name`;
                birthYearInput.name = `child-${childCounter}-birth_year`;
                
                // 現在年から10年引いた年をデフォルト値として設定
                const currentYear = new Date().getFullYear();
                birthYearInput.value = currentYear - 10;
                
                // 削除ボタンにイベントリスナーを追加
                const removeButton = newChild.querySelector('.remove-child');
                removeButton.addEventListener('click', () => newChild.remove());
                
                // コンテナに追加
                document.getElementById('children-container').appendChild(newChild);
                
                // カウンターをインクリメント
                childCounter++;
            });
        }
        
        // 既存の子供の削除ボタンにイベントリスナーを追加
        document.querySelectorAll('.remove-child').forEach(button => {
            button.addEventListener('click', function() {
                const childRow = this.closest('.child-row');
                if (childRow) {
                    childRow.remove();
                }
            });
        });
        
        // 子供データが存在しない場合のフォールバック処理
        const birthYearInput = document.querySelector('input[name="child-0-birth_year"]');
        if (!birthYearInput) {
            // 子供情報がまだないので作成
            const childForm = document.createElement('div');
            childForm.classList.add('hidden');
            childForm.style.display = 'none';
            
            // 現在の年から20年前をデフォルトの誕生年とする
            const currentYear = new Date().getFullYear();
            const defaultBirthYear = currentYear - 20;
            
            childForm.innerHTML = `
                <input type="hidden" name="child-0-birth_year" value="${defaultBirthYear}">
                <input type="hidden" name="child-0-name" value="お子様">
            `;
            
            document.querySelector('form').appendChild(childForm);
        }
        
        // 教育費用の追加ボタン
        const addEducationButton = document.getElementById('add-education');
        if (addEducationButton) {
            let counter = document.querySelectorAll('.education-row').length;
            
            addEducationButton.addEventListener('click', () => {
                // テンプレートのクローンを作成
                const template = document.getElementById('education-template');
                const newRow = template.cloneNode(true);
                newRow.classList.remove('d-none');
                newRow.classList.add('education-row');
                newRow.id = '';
                
                // フォーム名の更新
                const educationType = newRow.querySelector('.education-type');
                const institutionType = newRow.querySelector('.institution-type');
                const academicField = newRow.querySelector('.academic-field');
                
                // 全ての子供情報を取得
                const childInputs = document.querySelectorAll('input[name^="child-"][name$="-id"]');
                let childId = '0';
                
                // 選択メニューを作成して設定
                const childSelectContainer = document.createElement('div');
                childSelectContainer.className = 'col-md-3 mb-2';
                
                const childSelectLabel = document.createElement('label');
                childSelectLabel.className = 'form-label';
                childSelectLabel.textContent = 'お子様を選択';
                
                const childSelect = document.createElement('select');
                childSelect.className = 'form-select education-child-select';
                
                // 子供選択肢を追加
                childInputs.forEach((input, index) => {
                    const childIndex = input.name.split('-')[1];
                    const nameInput = document.querySelector(`input[name="child-${childIndex}-name"]`);
                    const birthYearInput = document.querySelector(`input[name="child-${childIndex}-birth_year"]`);
                    
                    if (nameInput && birthYearInput) {
                        const option = document.createElement('option');
                        option.value = input.value || index;
                        option.textContent = `${nameInput.value} (${birthYearInput.value}年生)`;
                        childSelect.appendChild(option);
                        
                        // 最初の子供IDを初期値として保存
                        if (index === 0) {
                            childId = input.value || index;
                        }
                    }
                });
                
                childSelectContainer.appendChild(childSelectLabel);
                childSelectContainer.appendChild(childSelect);
                
                // 既存の行の最初に挿入
                newRow.insertBefore(childSelectContainer, newRow.firstChild);
                
                // 子供IDを持つ非表示フィールドを追加
                const hiddenChildId = document.createElement('input');
                hiddenChildId.type = 'hidden';
                hiddenChildId.name = 'education-0-' + counter + '-child_id';
                hiddenChildId.value = childId;
                newRow.appendChild(hiddenChildId);
                
                // 選択が変更されたときに子供IDを更新
                childSelect.addEventListener('change', () => {
                    hiddenChildId.value = childSelect.value;
                });
                
                // フィールド名の設定
                educationType.name = 'education-0-' + counter + '-education_type';
                institutionType.name = 'education-0-' + counter + '-institution_type';
                academicField.name = 'education-0-' + counter + '-academic_field';
                
                // イベントリスナーの設定
                educationType.addEventListener('change', () => updateEducationCost(newRow));
                institutionType.addEventListener('change', () => updateEducationCost(newRow));
                academicField.addEventListener('change', () => updateEducationCost(newRow));
                newRow.querySelector('.remove-education').addEventListener('click', () => newRow.remove());
                
                // 行の追加
                educationSettings.appendChild(newRow);
                
                // 初期表示の更新
                updateEducationCost(newRow);
                
                counter++;
            });
            
            // 初期状態で教育費用が設定されていない場合は、デフォルト値を設定
            if (counter === 0) {
                // すべての学校種類についてデフォルト設定を追加
                const defaultTypes = ['幼稚園', '小学校', '中学校', '高校', '大学'];
                defaultTypes.forEach((type, index) => {
                    setTimeout(() => {
                        addEducationButton.click();
                        const lastRow = document.querySelector('.education-row:last-child');
                        const typeSelect = lastRow.querySelector('.education-type');
                        typeSelect.value = type;
                        
                        // 大学の場合は文系をデフォルトに
                        if (type === '大学') {
                            const academicField = lastRow.querySelector('.academic-field');
                            academicField.value = '文系';
                            const academicFieldContainer = lastRow.querySelector('.academic-field-container');
                            academicFieldContainer.style.display = '';
                        }
                        
                        // 費用表示を更新
                        updateEducationCost(lastRow);
                    }, index * 10); // わずかな遅延をつけて順番に追加
                });
            }
        }
    }
    
    // 削除確認モーダルの処理
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    if (deleteConfirmModal) {
        deleteConfirmModal.addEventListener('show.bs.modal', function (event) {
            // ボタンを取得
            const button = event.relatedTarget;
            
            // data-bs-* 属性からデータを取得
            const targetId = button.getAttribute('data-bs-id');
            const targetName = button.getAttribute('data-bs-name');
            const targetUrl = button.getAttribute('data-bs-url');
            
            // モーダル内の要素を更新
            const modalTitle = deleteConfirmModal.querySelector('.modal-title');
            const modalBody = deleteConfirmModal.querySelector('.modal-body p');
            const confirmButton = deleteConfirmModal.querySelector('#confirmDeleteButton');
            
            modalTitle.textContent = `${targetName}の削除`;
            modalBody.textContent = `「${targetName}」を削除してもよろしいですか？この操作は元に戻せません。`;
            
            // 削除フォームのアクションURLを設定
            const form = deleteConfirmModal.querySelector('form');
            form.action = targetUrl;
        });
    }
    
    // フォームのバリデーション
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // 年齢自動計算（生年フィールドと年齢表示フィールドがある場合）
    const birthYearInput = document.getElementById('birth_year');
    const ageDisplay = document.getElementById('age_display');
    if (birthYearInput && ageDisplay) {
        birthYearInput.addEventListener('input', function() {
            const birthYear = parseInt(this.value, 10);
            const currentYear = new Date().getFullYear();
            
            if (!isNaN(birthYear) && birthYear > 1900 && birthYear <= currentYear) {
                const age = currentYear - birthYear;
                ageDisplay.textContent = `${age}歳`;
            } else {
                ageDisplay.textContent = '-';
            }
        });
        
        // 初期表示
        if (birthYearInput.value) {
            const birthYear = parseInt(birthYearInput.value, 10);
            const currentYear = new Date().getFullYear();
            
            if (!isNaN(birthYear)) {
                const age = currentYear - birthYear;
                ageDisplay.textContent = `${age}歳`;
            }
        }
    }
    
    // 支出合計の自動計算
    function calculateTotalExpense() {
        // 詳細支出アイテムから計算する場合
        if (document.querySelector('.expense-item')) {
            let total = 0;
            
            // 全ての支出項目を取得
            const expenseItems = document.querySelectorAll('.expense-item');
            expenseItems.forEach(input => {
                if (!isNaN(input.value) && input.value.trim() !== '') {
                    total += parseInt(input.value, 10);
                }
            });
            
            // 合計表示の更新
            const totalDisplay = document.getElementById('total_expense');
            if (totalDisplay) {
                // 支出単位に応じた表示に変更
                const expenseUnitSelect = document.getElementById('expense_unit');
                const isMonthly = expenseUnitSelect && expenseUnitSelect.value === 'monthly';
                totalDisplay.textContent = `${total}万円/${isMonthly ? '月' : '年'}`;
            }
            
            return;
        }
        
        // 以下は従来の支出項目からの計算（後方互換性のため）
        const expenseFields = [
            'expense_housing',
            'expense_living',
            'expense_education',
            'expense_insurance',
            'expense_loan',
            'expense_entertainment',
            'expense_transportation'
        ];
        
        let total = 0;
        
        expenseFields.forEach(field => {
            const input = document.getElementById(field);
            if (input && !isNaN(input.value) && input.value.trim() !== '') {
                total += parseInt(input.value, 10);
            }
        });
        
        const totalDisplay = document.getElementById('total_expense');
        if (totalDisplay) {
            // 支出単位に応じた表示に変更
            const expenseUnitSelect = document.getElementById('expense_unit');
            const isMonthly = expenseUnitSelect && expenseUnitSelect.value === 'monthly';
            totalDisplay.textContent = `${total}万円/${isMonthly ? '月' : '年'}`;
        }
    }
    
    // 支出フィールドにイベントリスナーを追加
    const expenseInputs = document.querySelectorAll('[id^="expense_"]');
    expenseInputs.forEach(input => {
        input.addEventListener('input', calculateTotalExpense);
    });
    
    // 初期表示時に合計を計算
    calculateTotalExpense();
    
    // 継続的なイベントのチェックボックス制御
    const recurringCheckbox = document.getElementById('recurring');
    const recurringEndYearField = document.getElementById('recurring_end_year_field');
    if (recurringCheckbox && recurringEndYearField) {
        function toggleRecurringEndYear() {
            recurringEndYearField.style.display = recurringCheckbox.checked ? 'block' : 'none';
        }
        
        recurringCheckbox.addEventListener('change', toggleRecurringEndYear);
        
        // 初期表示
        toggleRecurringEndYear();
    }
});

// エクスポートボタンのクリックイベント
function exportData(format, url) {
    window.location.href = url;
}

// シミュレーション結果を絞り込む（年代別）
function filterResults(startYear, endYear) {
    const rows = document.querySelectorAll('#resultsTable tbody tr');
    rows.forEach(row => {
        const yearCell = row.cells[0];
        const year = parseInt(yearCell.textContent, 10);
        
        if (year >= startYear && year <= endYear) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// ページ遷移時のロード表示
function showLoading() {
    const loader = document.createElement('div');
    loader.className = 'loading';
    loader.innerHTML = '<div class="spinner-border loading-spinner text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    document.body.appendChild(loader);
    
    return loader;
}

function hideLoading(loader) {
    if (loader && loader.parentNode) {
        loader.parentNode.removeChild(loader);
    }
}

// フォーム送信時のロード表示
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form:not(.no-loading)');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const loader = showLoading();
            
            // 5秒後にローディング表示を消す（タイムアウト対策）
            setTimeout(() => {
                hideLoading(loader);
            }, 5000);
        });
    });
    
    // ページ内リンクでもローディング表示（データ量が多い場合）
    const dataLinks = document.querySelectorAll('a[data-loading="true"]');
    dataLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 同じページ内のアンカーリンクは除外
            if (this.getAttribute('href').startsWith('#')) {
                return;
            }
            
            const loader = showLoading();
            
            // 5秒後にローディング表示を消す（タイムアウト対策）
            setTimeout(() => {
                hideLoading(loader);
            }, 5000);
        });
    });
});