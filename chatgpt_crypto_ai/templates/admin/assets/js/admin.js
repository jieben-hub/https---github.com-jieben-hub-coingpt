// CoinGPT 管理后台通用JavaScript工具函数

// 全局配置
const ADMIN_CONFIG = {
    BASE_URL: '/admin',
    API_TIMEOUT: 30000,
    PAGE_SIZE: 10
};

// 消息提示函数
function showToast(message, type = 'info') {
    // 检查是否已存在toast容器，不存在则创建
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3 z-50';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastId = `toast-${Date.now()}`;
    const typeClasses = {
        success: 'bg-success',
        error: 'bg-danger',
        warning: 'bg-warning text-dark',
        info: 'bg-info'
    };
    
    const toastHTML = `
        <div id="${toastId}" class="toast ${typeClasses[type] || 'bg-info'} text-white" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('afterbegin', toastHTML);
    
    // 初始化并显示toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    
    toast.show();
    
    // 移除toast元素（防止DOM过多）
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// 显示成功提示
function showSuccess(message) {
    showToast(message, 'success');
}

// 显示错误提示
function showError(message) {
    showToast(message, 'error');
}

// 显示警告提示
function showWarning(message) {
    showToast(message, 'warning');
}

// 显示信息提示
function showInfo(message) {
    showToast(message, 'info');
}

// 确认对话框
function confirmAction(message, confirmCallback, cancelCallback) {
    const modalId = `confirm-modal-${Date.now()}`;
    
    // 创建确认模态框
    const modalHTML = `
        <div id="${modalId}" class="modal fade" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">确认操作</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary confirm-btn">确认</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modalElement = document.getElementById(modalId);
    const modal = new bootstrap.Modal(modalElement);
    
    // 确认按钮点击事件
    modalElement.querySelector('.confirm-btn').addEventListener('click', function() {
        if (typeof confirmCallback === 'function') {
            confirmCallback();
        }
        modal.hide();
    });
    
    // 取消按钮点击事件
    modalElement.querySelector('.btn-secondary').addEventListener('click', function() {
        if (typeof cancelCallback === 'function') {
            cancelCallback();
        }
    });
    
    // 模态框隐藏后移除元素
    modalElement.addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
    
    // 显示模态框
    modal.show();
}

// 格式化日期时间
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '';
    
    const date = new Date(dateTimeString);
    if (isNaN(date.getTime())) return '无效日期';
    
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 格式化日期（仅日期部分）
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '无效日期';
    
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

// 格式化时间（仅时间部分）
function formatTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '无效时间';
    
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 格式化日期时间为输入框格式
function formatDateTimeForInput(date) {
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '';
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// 获取相对时间描述
function getRelativeTime(dateTimeString) {
    const now = new Date();
    const date = new Date(dateTimeString);
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) {
        return '刚刚';
    } else if (diffMins < 60) {
        return `${diffMins}分钟前`;
    } else if (diffHours < 24) {
        return `${diffHours}小时前`;
    } else if (diffDays < 30) {
        return `${diffDays}天前`;
    } else if (diffDays < 365) {
        return `${Math.floor(diffDays / 30)}个月前`;
    } else {
        return `${Math.floor(diffDays / 365)}年前`;
    }
}

// 表单验证
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
            
            // 添加错误提示
            if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                const errorMsg = document.createElement('div');
                errorMsg.className = 'invalid-feedback';
                errorMsg.textContent = field.dataset.errorMessage || '此字段为必填项';
                field.parentNode.appendChild(errorMsg);
            }
        } else {
            field.classList.remove('is-invalid');
            
            // 移除错误提示
            const errorMsg = field.nextElementSibling;
            if (errorMsg && errorMsg.classList.contains('invalid-feedback')) {
                errorMsg.remove();
            }
        }
    });
    
    return isValid;
}

// 清除表单错误提示
function clearFormErrors(formElement) {
    const invalidFields = formElement.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    const errorMessages = formElement.querySelectorAll('.invalid-feedback');
    errorMessages.forEach(msg => {
        msg.remove();
    });
}

// 设置表单数据
function setFormData(formElement, data) {
    if (!data) return;
    
    Object.keys(data).forEach(key => {
        const field = formElement.querySelector(`[name="${key}"], #${key}`);
        if (field) {
            if (field.type === 'checkbox') {
                field.checked = Boolean(data[key]);
            } else if (field.type === 'radio') {
                const radio = formElement.querySelector(`[name="${key}"][value="${data[key]}"]`);
                if (radio) radio.checked = true;
            } else if (field.tagName === 'SELECT') {
                field.value = data[key] !== null && data[key] !== undefined ? String(data[key]) : '';
            } else if (field.type === 'datetime-local') {
                field.value = formatDateTimeForInput(data[key]);
            } else {
                field.value = data[key] !== null && data[key] !== undefined ? data[key] : '';
            }
        }
    });
}

// 获取表单数据
function getFormData(formElement) {
    const formData = new FormData(formElement);
    const data = {};
    
    formData.forEach((value, key) => {
        // 处理复选框
        if (formElement.querySelector(`[name="${key}"][type="checkbox"]`)) {
            if (!data[key]) data[key] = [];
            data[key].push(value);
        } else {
            data[key] = value;
        }
    });
    
    // 特殊处理单选按钮
    const radioGroups = formElement.querySelectorAll('[type="radio"]');
    const uniqueNames = new Set();
    
    radioGroups.forEach(radio => {
        if (!uniqueNames.has(radio.name)) {
            uniqueNames.add(radio.name);
            const checked = formElement.querySelector(`[name="${radio.name}"]:checked`);
            data[radio.name] = checked ? checked.value : '';
        }
    });
    
    return data;
}

// 重置表单
function resetForm(formElement) {
    formElement.reset();
    clearFormErrors(formElement);
}

// 初始化导航高亮
function initNavigationHighlight() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar a');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (currentPath === linkPath || 
            (currentPath.startsWith(linkPath) && linkPath !== '/admin' && 
             !currentPath.startsWith('/admin/login'))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// 初始化退出登录按钮
function initLogoutButton() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            confirmAction('确定要退出登录吗？', function() {
                fetch('/admin/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        window.location.href = '/admin/login';
                    } else {
                        showError('退出登录失败，请稍后重试');
                    }
                })
                .catch(error => {
                    console.error('Logout error:', error);
                    showError('退出登录失败，请稍后重试');
                });
            });
        });
    }
}

// 检查用户登录状态
function checkLoginStatus() {
    return fetch('/admin/check-login', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            window.location.href = '/admin/login';
            throw new Error('未登录');
        }
        return response.json();
    })
    .catch(error => {
        console.error('Check login status error:', error);
        window.location.href = '/admin/login';
        throw error;
    });
}

// 生成唯一ID
function generateId() {
    return 'id_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 节流函数
function throttle(func, delay) {
    let lastCall = 0;
    return function(...args) {
        const now = Date.now();
        if (now - lastCall >= delay) {
            lastCall = now;
            return func.apply(this, args);
        }
    };
}

// 防抖函数
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// 深拷贝对象
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
}

// 比较两个对象是否相等
function objectsEqual(obj1, obj2) {
    if (obj1 === obj2) return true;
    if (obj1 == null || obj2 == null) return false;
    if (typeof obj1 !== 'object' || typeof obj2 !== 'object') return false;
    
    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);
    
    if (keys1.length !== keys2.length) return false;
    
    for (const key of keys1) {
        if (!keys2.includes(key) || !objectsEqual(obj1[key], obj2[key])) {
            return false;
        }
    }
    
    return true;
}

// 安全地解析JSON
function safeJsonParse(jsonString, defaultValue = null) {
    try {
        return JSON.parse(jsonString);
    } catch (error) {
        console.error('JSON parse error:', error);
        return defaultValue;
    }
}

// 存储数据到本地存储
function setLocalStorage(key, value) {
    try {
        const serializedValue = JSON.stringify(value);
        localStorage.setItem(key, serializedValue);
        return true;
    } catch (error) {
        console.error('Set localStorage error:', error);
        return false;
    }
}

// 从本地存储获取数据
function getLocalStorage(key, defaultValue = null) {
    try {
        const serializedValue = localStorage.getItem(key);
        return serializedValue === null ? defaultValue : JSON.parse(serializedValue);
    } catch (error) {
        console.error('Get localStorage error:', error);
        return defaultValue;
    }
}

// 从本地存储删除数据
function removeLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Remove localStorage error:', error);
        return false;
    }
}

// 清空本地存储
function clearLocalStorage() {
    try {
        localStorage.clear();
        return true;
    } catch (error) {
        console.error('Clear localStorage error:', error);
        return false;
    }
}

// 初始化通用功能
function initCommonFunctions() {
    // 初始化导航高亮
    if (document.querySelector('.sidebar')) {
        initNavigationHighlight();
        initLogoutButton();
    }
    
    // 为所有带tooltip的元素初始化tooltip
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 为所有带popover的元素初始化popover
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 监听表单提交事件，添加基本验证
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                e.stopPropagation();
                showError('请填写所有必填项');
            }
        });
    });
    
    // 为所有必填字段添加输入事件监听器，实时验证
    document.querySelectorAll('[required]').forEach(field => {
        field.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('is-invalid');
                const errorMsg = this.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('invalid-feedback')) {
                    errorMsg.remove();
                }
            }
        });
    });
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCommonFunctions);
} else {
    initCommonFunctions();
}

// 导出工具函数（如果支持模块）
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = {
        showToast,
        showSuccess,
        showError,
        showWarning,
        showInfo,
        confirmAction,
        formatDateTime,
        formatDate,
        formatTime,
        formatDateTimeForInput,
        getRelativeTime,
        validateForm,
        clearFormErrors,
        setFormData,
        getFormData,
        resetForm,
        initNavigationHighlight,
        initLogoutButton,
        checkLoginStatus,
        generateId,
        throttle,
        debounce,
        deepClone,
        objectsEqual,
        safeJsonParse,
        setLocalStorage,
        getLocalStorage,
        removeLocalStorage,
        clearLocalStorage,
        initCommonFunctions,
        ADMIN_CONFIG
    };
}

// 全局错误处理
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    // 可以在这里添加错误日志上报等功能
});

// 未捕获的Promise错误处理
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    // 可以在这里添加错误日志上报等功能
});