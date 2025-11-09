/**
 * CoinGPT 前端交互脚本
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化Markdown渲染器
    const md = window.markdownit({
        html: false,
        linkify: true,
        typographer: true
    });

    // 获取DOM元素
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const resetBtn = document.getElementById('resetBtn');
    const sendBtn = document.querySelector('#sendBtn');

    /**
     * 添加消息到聊天界面
     * @param {string} content - 消息内容
     * @param {string} sender - 发送者('user'或'bot')
     * @param {boolean} isMarkdown - 是否解析为Markdown
     */
    function addMessage(content, sender, isMarkdown = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');

        // 根据需要解析Markdown
        if (isMarkdown && sender === 'bot') {
            contentDiv.innerHTML = md.render(content);
        } else {
            contentDiv.innerText = content;
        }

        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * 显示加载中动画
     */
    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.classList.add('message', 'bot', 'typing-indicator-container');
        
        const indicatorContent = document.createElement('div');
        indicatorContent.classList.add('typing-indicator');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            indicatorContent.appendChild(dot);
        }
        
        indicator.appendChild(indicatorContent);
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return indicator;
    }

    /**
     * 发送消息到服务器并处理响应
     * @param {string} prompt - 用户输入的消息
     */
    async function sendMessage(prompt) {
        try {
            // 显示用户消息
            addMessage(prompt, 'user');
            
            // 显示加载中动画
            const loadingIndicator = showTypingIndicator();
            
            // 发送请求到后端
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            // 移除加载动画
            chatMessages.removeChild(loadingIndicator);
            
            // 处理响应
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // 显示AI回复，使用Markdown渲染
                    addMessage(data.response, 'bot', true);
                } else {
                    throw new Error(data.error || '未知错误');
                }
            } else {
                throw new Error(`服务器错误: ${response.status}`);
            }
            
        } catch (error) {
            console.error('Error:', error);
            addMessage(`错误: ${error.message}`, 'bot');
        }
    }

    /**
     * 清除聊天历史
     */
    async function clearChat() {
        try {
            // 发送清除上下文的请求
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ clear_context: true }),
            });

            if (response.ok) {
                // 清空聊天界面
                chatMessages.innerHTML = '';
                
                // 添加欢迎消息
                const welcomeMessage = `
你好！我是 CoinGPT，你的加密货币行情分析助手。

你可以这样向我提问:
* "分析一下比特币最近的走势"
* "ETH和SOL哪个表现更好？"
* "BTC今天4小时图怎么样？"
                `;
                
                addMessage(welcomeMessage, 'bot', true);
            } else {
                throw new Error(`服务器错误: ${response.status}`);
            }
        } catch (error) {
            console.error('Error clearing chat:', error);
            addMessage(`错误: ${error.message}`, 'bot');
        }
    }

    // 监听表单提交事件
    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const prompt = userInput.value.trim();
        if (prompt) {
            // 清空输入框
            userInput.value = '';
            
            // 发送消息
            sendMessage(prompt);
        }
    });

    // 监听重置按钮点击事件
    resetBtn.addEventListener('click', clearChat);
    
    // 输入框获取焦点
    userInput.focus();
});
