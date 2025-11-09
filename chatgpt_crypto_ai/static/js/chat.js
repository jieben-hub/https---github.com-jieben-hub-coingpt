/**
 * CoinGPT 聊天模块
 * 处理聊天界面、消息发送和接收
 */

// 全局变量
let isWaitingForResponse = false;
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const loadingElement = document.getElementById('loading');
const md = window.markdownit();

// 初始化聊天界面
document.addEventListener('DOMContentLoaded', function() {
    // 设置发送消息事件监听
    setupMessageSending();
    
    // 设置清除聊天按钮事件监听
    setupClearChatButton();
    
    // 设置文本框自动调整高度
    setupTextareaAutoResize();
});

/**
 * 设置发送消息功能
 */
function setupMessageSending() {
    // 发送按钮点击事件
    sendButton.addEventListener('click', sendMessage);
    
    // 输入框Enter键事件
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

/**
 * 设置清除聊天功能
 */
function setupClearChatButton() {
    const clearButton = document.getElementById('clear-button');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            // 清空聊天界面
            chatMessages.innerHTML = '';
            
            // 如果已登录，创建新会话
            if (currentToken) {
                createNewSession();
            }
        });
    }
}

/**
 * 发送消息
 */
async function sendMessage() {
    // 获取用户输入
    const message = userInput.value.trim();
    
    // 检查是否已经在等待响应或消息为空
    if (isWaitingForResponse || !message) {
        return;
    }
    
    // 检查是否已认证
    if (!currentToken) {
        appendErrorMessage("请先登录");
        return;
    }
    
    // 检查是否有活跃会话
    if (!currentSessionId) {
        await createNewSession();
    }
    
    // 显示用户消息
    appendUserMessage(message);
    
    // 清空输入框
    userInput.value = '';
    
    // 设置等待状态
    isWaitingForResponse = true;
    loadingElement.style.display = 'block';
    
    // 创建一个空的机器人消息元素，用于流式更新
    const botMessageElement = document.createElement('div');
    botMessageElement.className = 'message bot-message';
    botMessageElement.innerHTML = `
        <div class="avatar bot-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="streaming-content"></div>
        </div>
    `;
    chatMessages.appendChild(botMessageElement);
    const streamingContent = botMessageElement.querySelector('.streaming-content');
    scrollToBottom();
    
    try {
        // 使用流式输出模式
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId,
                stream: true  // 启用流式输出
            })
        });
        
        // 检查响应状态
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }
        
        // 获取响应的读取流
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let fullResponse = '';
        let buffer = ''; // 用于存储未完成的SSE数据
        
        // 读取流数据
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                // 处理最后可能的缓冲数据
                if (buffer.trim() && buffer.includes('data: ')) {
                    processSSEData(buffer);
                }
                break;
            }
            
            // 解码数据
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            // 处理完整的SSE事件
            const events = buffer.split('\n\n');
            // 保留最后一个可能不完整的事件
            buffer = events.pop() || '';
            
            // 处理完整的事件
            for (const event of events) {
                processSSEData(event);
            }
        }
        
        // 处理SSE数据的函数
        function processSSEData(eventText) {
            if (!eventText.trim()) return;
            
            const lines = eventText.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const eventData = JSON.parse(line.substring(6));
                        
                        if (eventData.content) {
                            fullResponse += eventData.content;
                            // 使用markdown渲染部分内容
                            streamingContent.innerHTML = md.render(fullResponse);
                            scrollToBottom();
                        }
                        
                        // 如果流式输出完成
                        if (eventData.done) {
                            // 完成后，使用完整的markdown渲染并添加评分功能
                            const messageContent = botMessageElement.querySelector('.message-content');
                            
                            // 获取消息ID（如果服务器返回了）
                            const messageId = eventData.message_id;
                            
                            // 渲染内容并添加评分按钮
                            messageContent.innerHTML = `
                                ${md.render(fullResponse)}
                                <div class="message-rating" data-message-id="${messageId || ''}">
                                    <div class="rating-text">评价这个回复:</div>
                                    <div class="rating-buttons">
                                        <button class="rating-btn" data-rating="1" title="差"><i class="far fa-thumbs-down"></i></button>
                                        <button class="rating-btn" data-rating="5" title="好"><i class="far fa-thumbs-up"></i></button>
                                    </div>
                                </div>
                            `;
                            
                            // 添加评分按钮事件监听
                            if (messageId) {
                                const ratingButtons = messageContent.querySelectorAll('.rating-btn');
                                ratingButtons.forEach(button => {
                                    button.addEventListener('click', function() {
                                        const rating = parseInt(this.getAttribute('data-rating'));
                                        rateMessage(messageId, rating);
                                        
                                        // 更新UI状态
                                        ratingButtons.forEach(btn => btn.classList.remove('selected'));
                                        this.classList.add('selected');
                                        
                                        // 显示感谢信息
                                        const ratingContainer = messageContent.querySelector('.message-rating');
                                        ratingContainer.innerHTML = '<div class="rating-thanks">感谢您的反馈!</div>';
                                    });
                                });
                            }
                        }
                    } catch (error) {
                        console.error('解析流式数据失败', error, line);
                    }
                }
            }
        }
        
        // 恢复状态
        isWaitingForResponse = false;
        loadingElement.style.display = 'none';
        
    } catch (error) {
        console.error('发送消息失败', error);
        appendErrorMessage("网络错误，请稍后重试");
        
        // 恢复状态
        isWaitingForResponse = false;
        loadingElement.style.display = 'none';
    }
}

/**
 * 添加用户消息到聊天界面
 */
function appendUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    messageElement.innerHTML = `
        <div class="avatar user-avatar">
            <i class="fas fa-user"></i>
        </div>
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

/**
 * 添加机器人消息到聊天界面
 */
function appendBotMessage(message, messageId) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message';
    messageElement.innerHTML = `
        <div class="avatar bot-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            ${md.render(message)}
            <div class="message-rating" data-message-id="${messageId || ''}">
                <div class="rating-text">评价这个回复:</div>
                <div class="rating-buttons">
                    <button class="rating-btn" data-rating="1" title="差"><i class="far fa-thumbs-down"></i></button>
                    <button class="rating-btn" data-rating="5" title="好"><i class="far fa-thumbs-up"></i></button>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(messageElement);
    
    // 添加评分按钮事件监听
    if (messageId) {
        const ratingButtons = messageElement.querySelectorAll('.rating-btn');
        ratingButtons.forEach(button => {
            button.addEventListener('click', function() {
                const rating = parseInt(this.getAttribute('data-rating'));
                rateMessage(messageId, rating);
                
                // 更新UI状态
                ratingButtons.forEach(btn => btn.classList.remove('selected'));
                this.classList.add('selected');
                
                // 显示感谢信息
                const ratingContainer = messageElement.querySelector('.message-rating');
                ratingContainer.innerHTML = '<div class="rating-thanks">感谢您的反馈!</div>';
            });
        });
    }
    
    scrollToBottom();
}

/**
 * 添加错误消息到聊天界面
 */
function appendErrorMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message system-message error-message';
    messageElement.innerHTML = `
        <div class="avatar system-avatar">
            <i class="fas fa-exclamation-circle"></i>
        </div>
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    chatMessages.appendChild(messageElement);
    scrollToBottom();
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
 * 设置文本框自动调整高度
 */
function setupTextareaAutoResize() {
    userInput.addEventListener('input', function() {
        // 先将高度重置为自动，这样可以得到本次内容的实际高度
        this.style.height = 'auto';
        
        // 计算新高度，但限制最大高度
        const newHeight = Math.min(this.scrollHeight, 120);
        
        // 设置新高度
        this.style.height = newHeight + 'px';
    });
    
    // 初始化时也触发一次，设置初始高度
    userInput.dispatchEvent(new Event('input'));
}

/**
 * 提交消息评分
 */
async function rateMessage(messageId, rating, feedback = '') {
    if (!currentToken || !messageId) return;
    
    try {
        const response = await fetch('/api/feedback/rate_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                message_id: messageId,
                rating: rating,
                feedback: feedback
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('提交评分失败', errorData);
            return false;
        }
        
        const result = await response.json();
        console.log('评分提交成功', result);
        return true;
        
    } catch (error) {
        console.error('提交评分时出错', error);
        return false;
    }
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
    // 使用setTimeout确保在DOM更新后滚动
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 50);
}
