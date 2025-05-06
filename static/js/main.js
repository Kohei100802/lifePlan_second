// main.js - メインJavaScriptファイル

document.addEventListener('DOMContentLoaded', function() {
    // ツールチップの初期化
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
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
            totalDisplay.textContent = `${total}万円/年`;
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