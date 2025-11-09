/**
 * CoinGPT 用户认证模块
 * 处理用户登录、认证和会话管理
 */

// 存储用户信息
let currentUser = null;
let currentToken = null;
let currentSessionId = null;

// 初始化认证系统
document.addEventListener('DOMContentLoaded', function() {
    // 检查本地存储的token
    initAuth();
    
    // 设置登录与注册表单
    setupLoginRegisterForms();
    
    // 添加Apple登录按钮事件监听
    setupAppleLogin();
    
    // 添加会话管理事件监听
    setupSessionManagement();
    
    // 添加退出按钮事件监听
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

/**
 * 初始化认证
 */
function initAuth() {
    // 从localStorage获取token
    const token = localStorage.getItem('coingpt_token');
    if (token) {
        currentToken = token;
        // 获取用户信息
        fetchUserInfo(token)
            .then(userData => {
                if (userData) {
                    showAuthenticatedUI(userData);
                } else {
                    showLoginUI();
                }
            })
            .catch(err => {
                console.error('获取用户信息失败', err);
                // 清除无效token
                localStorage.removeItem('coingpt_token');
                showLoginUI();
            });
    } else {
        showLoginUI();
    }
}

/**
 * 设置Apple登录
 */
function setupAppleLogin() {
    // 加载Apple Sign In JS SDK
    const script = document.createElement('script');
    script.src = "https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js";
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
    
    script.onload = () => {
        // 配置Apple Sign In
        window.AppleID.auth.init({
            clientId: document.querySelector('meta[name="appleid-signin-client-id"]').content,
            scope: document.querySelector('meta[name="appleid-signin-scope"]').content,
            redirectURI: document.querySelector('meta[name="appleid-signin-redirect-uri"]').content,
            state: document.querySelector('meta[name="appleid-signin-state"]').content
        });
        
        // 添加登录按钮点击事件
        const signInBtn = document.getElementById('apple-sign-in');
        if (signInBtn) {
            signInBtn.addEventListener('click', () => {
                window.AppleID.auth.signIn();
            });
        }
    };
    
    // 处理Apple登录回调
    window.handleAppleSignInCallback = function(response) {
        if (response.authorization && response.authorization.id_token) {
            // 发送ID token到后端进行验证
            fetch('/api/auth/apple/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    id_token: response.authorization.id_token,
                    user_info: response.user || {}
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    // 保存token到localStorage
                    localStorage.setItem('coingpt_token', data.data.token);
                    currentToken = data.data.token;
                    // 显示已认证UI
                    showAuthenticatedUI(data.data.user);
                } else {
                    alert('登录失败: ' + data.message);
                    showLoginUI();
                }
            })
            .catch(err => {
                console.error('登录请求失败', err);
                showLoginUI();
            });
        }
    };
}

/**
 * 设置登录与注册表单
 */
function setupLoginRegisterForms() {
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    // 切换登录/注册表单
    if (loginTab && registerTab) {
        loginTab.addEventListener('click', () => {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.style.display = 'block';
            registerForm.style.display = 'none';
        });
        
        registerTab.addEventListener('click', () => {
            registerTab.classList.add('active');
            loginTab.classList.remove('active');
            registerForm.style.display = 'block';
            loginForm.style.display = 'none';
        });
    }
    
    // 处理登录表单提交
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            const errorMsg = document.getElementById('login-error');
            
            if (!username || !password) {
                errorMsg.textContent = '用户名和密码不能为空';
                return;
            }
            
            // 发送登录请求
            fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    // 保存token到localStorage
                    localStorage.setItem('coingpt_token', data.data.token);
                    currentToken = data.data.token;
                    // 显示已认证UI
                    showAuthenticatedUI(data.data.user);
                } else {
                    errorMsg.textContent = data.message || '登录失败';
                }
            })
            .catch(err => {
                console.error('登录请求失败', err);
                errorMsg.textContent = '登录请求失败，请重试';
            });
        });
    }
    
    // 处理注册表单提交
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('register-username').value;
            const password = document.getElementById('register-password').value;
            const confirmPassword = document.getElementById('register-confirm-password').value;
            const errorMsg = document.getElementById('register-error');
            
            if (!username || !password) {
                errorMsg.textContent = '用户名和密码不能为空';
                return;
            }
            
            if (password !== confirmPassword) {
                errorMsg.textContent = '两次输入的密码不一致';
                return;
            }
            
            // 发送注册请求
            fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    // 保存token到localStorage
                    localStorage.setItem('coingpt_token', data.data.token);
                    currentToken = data.data.token;
                    // 显示已认证UI
                    showAuthenticatedUI(data.data.user);
                } else {
                    errorMsg.textContent = data.message || '注册失败';
                }
            })
            .catch(err => {
                console.error('注册请求失败', err);
                errorMsg.textContent = '注册请求失败，请重试';
            });
        });
    }
}

/**
 * 设置会话管理
 */
function setupSessionManagement() {
    // 添加创建新会话按钮事件监听
    const newSessionBtn = document.getElementById('new-session');
    if (newSessionBtn) {
        newSessionBtn.addEventListener('click', createNewSession);
    }
    
    // 添加加载会话列表事件监听
    const sessionListBtn = document.getElementById('load-sessions');
    if (sessionListBtn) {
        sessionListBtn.addEventListener('click', loadSessionList);
    }
}

/**
 * 获取用户信息
 */
async function fetchUserInfo(token) {
    try {
        const response = await fetch('/api/auth/user', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            currentUser = data.data;
            return data.data;
        }
        return null;
    } catch (error) {
        console.error('获取用户信息失败', error);
        return null;
    }
}

/**
 * 创建新会话
 */
async function createNewSession() {
    if (!currentToken) return;
    
    try {
        const response = await fetch('/api/auth/sessions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            currentSessionId = data.data.session_id;
            // 清空聊天内容
            document.getElementById('chat-messages').innerHTML = '';
            // 显示会话ID
            document.getElementById('session-info').textContent = `会话ID: ${currentSessionId}`;
            return data.data;
        }
        return null;
    } catch (error) {
        console.error('创建会话失败', error);
        return null;
    }
}

/**
 * 加载会话列表
 */
async function loadSessionList() {
    if (!currentToken) return;
    
    try {
        const response = await fetch('/api/auth/sessions', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            // 显示会话列表
            const sessionList = document.getElementById('session-list');
            if (sessionList) {
                sessionList.innerHTML = '';
                data.data.forEach(session => {
                    const li = document.createElement('li');
                    li.className = 'session-item';
                    li.textContent = `${session.preview} (${formatDate(session.updated_at)})`;
                    li.dataset.sessionId = session.session_id;
                    li.addEventListener('click', () => loadSession(session.session_id));
                    sessionList.appendChild(li);
                });
                
                // 显示会话列表面板
                document.getElementById('sessions-panel').style.display = 'block';
            }
            return data.data;
        }
        return null;
    } catch (error) {
        console.error('加载会话列表失败', error);
        return null;
    }
}

/**
 * 加载指定会话
 */
async function loadSession(sessionId) {
    if (!currentToken) return;
    
    try {
        // 显示加载中状态
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
        
        // 更新当前会话ID
        currentSessionId = sessionId;
        
        // 从后端获取会话消息历史
        const response = await fetch(`/api/chat/session/${sessionId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 清空当前聊天内容
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = '';
            
            // 添加历史消息
            const messages = data.data.messages;
            const md = window.markdownit();
            
            for (const msg of messages) {
                // 根据角色生成不同样式的消息
                if (msg.role === 'user') {
                    // 添加用户消息
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message user-message';
                    messageElement.innerHTML = `
                        <div class="avatar user-avatar">
                            <i class="fas fa-user"></i>
                        </div>
                        <div class="message-content">
                            <p>${escapeHtml(msg.content)}</p>
                        </div>
                    `;
                    chatMessages.appendChild(messageElement);
                } else if (msg.role === 'assistant') {
                    // 添加机器人消息
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message bot-message';
                    messageElement.innerHTML = `
                        <div class="avatar bot-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-content">
                            ${md.render(msg.content)}
                        </div>
                    `;
                    chatMessages.appendChild(messageElement);
                }
            }
            
            // 滚动到底部
            scrollToBottom();
            
            // 关闭会话列表面板
            document.getElementById('sessions-panel').style.display = 'none';
            
            // 显示会话ID
            document.getElementById('session-info').textContent = `会话ID: ${currentSessionId}`;
            
            return true;
        } else {
            console.error('加载会话数据失败:', data.message);
            return false;
        }
    } catch (error) {
        console.error('加载会话失败', error);
        return false;
    } finally {
        // 隐藏加载中状态
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}

/**
 * 显示未登录UI
 */
function showLoginUI() {
    document.getElementById('auth-container').style.display = 'block';
    document.getElementById('chat-container').style.display = 'none';
    document.getElementById('user-info').style.display = 'none';
}

/**
 * 显示已登录UI
 */
function showAuthenticatedUI(user) {
    currentUser = user;
    document.getElementById('auth-container').style.display = 'none';
    document.getElementById('chat-container').style.display = 'block';
    document.getElementById('user-info').style.display = 'block';
    
    // 显示用户信息
    document.getElementById('user-name').textContent = user.user_id;
    document.getElementById('user-membership').textContent = user.membership;
    document.getElementById('dialog-count').textContent = user.dialog_count;
    
    // 创建一个新会话
    createNewSession();
}

/**
 * 注销登录
 */
function logout() {
    // 清除localStorage
    localStorage.removeItem('coingpt_token');
    
    // 发送登出请求
    fetch('/api/auth/logout', { method: 'POST' })
        .catch(err => console.error('登出请求失败', err));
    
    // 重置变量
    currentUser = null;
    currentToken = null;
    currentSessionId = null;
    
    // 显示登录UI
    showLoginUI();
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * 转义HTML特殊字符
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
    // 使用setTimeout确保在DOM更新后滚动
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 50);
    }
}
