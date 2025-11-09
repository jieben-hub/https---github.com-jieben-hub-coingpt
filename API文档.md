# CoinGPT API 对接文档

## 基础信息

- **基础URL**: `http://192.168.31.127:5000`
- **认证方式**: Bearer Token (通过 HTTP 头 `Authorization: Bearer <token>` 传递)
- **数据格式**: 所有请求和响应均使用 JSON 格式
- **状态码**:
  - 200: 成功
  - 400: 请求错误
  - 401: 认证失败
  - 403: 权限不足
  - 500: 服务器错误

## 1. 认证相关 API

### 1.1 用户注册

- **URL**: `/api/auth/register`
- **方法**: POST
- **描述**: 注册新用户
- **参数**:

```json
{
  "username": "用户名",
  "password": "密码",
  "inviter_id": "邀请人ID(可选)"
}
```

- **返回值**:

```json
{
  "status": "success",
  "data": {
    "user": {
      "user_id": 123,
      "username": "用户名",
      "membership": "free",
      "dialog_count": 0,
      "inviter_id": null,
      "created_at": "2025-07-13T11:36:47"
    },
    "token": "jwt_token_字符串"
  }
}
```

### 1.2 用户登录

- **URL**: `/api/auth/login`
- **方法**: POST
- **描述**: 用户登录
- **参数**:

```json
{
  "username": "用户名",
  "password": "密码"
}
```

- **返回值**:

```json
{
  "status": "success",
  "data": {
    "user": {
      "user_id": 123,
      "username": "用户名",
      "membership": "free",
      "dialog_count": 5,
      "created_at": "2025-07-13T11:36:47",
      "last_login": "2025-07-13T19:36:47"
    },
    "token": "jwt_token_字符串"
  }
}
```

### 1.3 Apple 账号登录

- **URL**: `/api/auth/apple/login`
- **方法**: POST
- **描述**: 使用 Apple ID 登录
- **参数**:

```json
{
  "id_token": "Apple ID Token",
  "user": {
    "name": {
      "firstName": "名",
      "lastName": "姓"
    },
    "email": "邮箱地址"
  }
}
```

- **返回值**: 同普通登录

### 1.4 用户登出

- **URL**: `/api/auth/logout`
- **方法**: POST
- **描述**: 用户登出
- **参数**: 无
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "message": "已成功登出"
}
```

### 1.5 获取邀请码

- **URL**: `/api/auth/invite`
- **方法**: GET
- **描述**: 获取当前用户的邀请码
- **参数**: 无
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "data": {
    "invite_code": "邀请码字符串",
    "invitee_count": 0
  }
}
```

### 1.6 获取邀请用户列表

- **URL**: `/api/auth/invitees`
- **方法**: GET
- **描述**: 获取当前用户邀请的所有用户列表
- **参数**: 无
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "data": [
    {
      "user_id": 124,
      "created_at": "2025-07-13T11:36:47"
    },
    {
      "user_id": 125,
      "created_at": "2025-07-13T12:36:47"
    }
  ]
}
```

## 2. 用户信息 API

### 2.1 获取当前用户信息

- **URL**: `/api/auth/user`
- **方法**: GET
- **描述**: 获取当前登录用户的详细信息
- **参数**: 无
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "data": {
    "user_id": 123,
    "username": "用户名",
    "membership": "free",
    "dialog_count": 5,
    "created_at": "2025-07-13T11:36:47",
    "last_login": "2025-07-13T19:36:47"
  }
}
```

### 2.2 获取用户使用情况

- **URL**: `/api/auth/usage-stats`
- **方法**: GET
- **描述**: 获取当前用户的使用统计信息
- **参数**: 无
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "data": {
    "session_count": 3,
    "max_sessions": 5,
    "sessions": [
      {
        "session_id": 1,
        "message_count": 8,
        "max_messages": 10,
        "created_at": "2025-07-13T11:36:47",
        "last_updated": "2025-07-13T19:36:47"
      },
      {
        "session_id": 2,
        "message_count": 10,
        "max_messages": 10,
        "created_at": "2025-07-13T12:36:47",
        "last_updated": "2025-07-13T18:36:47"
      }
    ],
    "is_limited": true
  }
}
```

## 3. 会话管理 API

### 3.1 创建新会话

- **URL**: `/api/chat/sessions`
- **方法**: POST
- **描述**: 创建新的聊天会话
- **参数**: 无
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "data": {
    "session_id": 3,
    "created_at": "2025-07-13T19:36:47"
  }
}
```

- **错误返回** (当达到会话限制):

```json
{
  "status": "error",
  "message": "免费用户最多只能创建5个会话",
  "code": "SESSION_LIMIT_REACHED"
}
```

### 3.2 获取会话列表

- **URL**: `/api/auth/sessions`
- **方法**: GET
- **描述**: 获取当前用户的所有会话列表
- **参数**: 无
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "data": [
    {
      "session_id": 1,
      "title": "关于比特币的分析",
      "last_message": "BTC目前处于上升趋势...",
      "created_at": "2025-07-13T11:36:47",
      "updated_at": "2025-07-13T19:36:47",
      "symbol": "BTC"
    },
    {
      "session_id": 2,
      "title": "以太坊价格预测",
      "last_message": "ETH短期内可能会...",
      "created_at": "2025-07-13T12:36:47",
      "updated_at": "2025-07-13T18:36:47",
      "symbol": "ETH"
    }
  ]
}
```

### 3.3 删除会话

- **URL**: `/api/auth/sessions/{session_id}`
- **方法**: DELETE
- **描述**: 删除指定的会话（仅会员用户可用）
- **参数**: 无 (session_id 在 URL 中)
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "message": "会话已成功删除"
}
```

- **错误返回** (非会员用户):

```json
{
  "status": "error",
  "message": "只有会员用户才能删除会话",
  "code": "PREMIUM_REQUIRED"
}
```

### 3.4 获取会话消息

- **URL**: `/api/chat/session/<session_id>`
- **方法**: GET
- **描述**: 获取指定会话的所有历史消息
- **参数**: 无 (session_id 在 URL 中)
- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "data": {
    "session_id": 1,
    "messages": [
      {
        "role": "user",
        "content": "分析一下BTC的日线",
        "created_at": "2025-07-13T11:36:47"
      },
      {
        "role": "assistant",
        "content": "根据BTC日线图分析，当前价格...",
        "created_at": "2025-07-13T11:36:52"
      }
    ]
  }
}
```

## 4. 聊天 API

### 4.1 发送消息

- **URL**: `/api/chat/`
- **方法**: POST
- **描述**: 发送消息并获取AI回复
- **参数**:

```json
{
  "message": "用户消息内容",
  "session_id": 1,  // 可选，如不提供则创建新会话
  "stream": false    // 可选，设置为true启用流式输出
}
```

- **认证**: 需要
- **返回值** (非流式):

```json
{
  "status": "success",
  "message": "AI回复内容",
  "session_id": 1
}
```

- **返回值** (流式输出):
  - 使用 Server-Sent Events (SSE) 格式
  - 每个事件包含部分回复内容和完成状态
  - 最后一个事件包含消息ID

```
data: {"content":"AI回复", "done":false}

data: {"content":"的部分", "done":false}

data: {"content":"", "done":true, "message_id":42}
```

- **错误返回** (当达到消息限制):

```json
{
  "status": "error",
  "message": "免费用户每个会话最多只能发送10条消息",
  "code": "MESSAGE_LIMIT_REACHED"
}
```

### 4.2 显示意图提取结果 (调试用)

- **URL**: `/api/chat/show_prompt`
- **方法**: POST
- **描述**: 仅显示意图提取的prompt，不进行后续处理
- **参数**:

```json
{
  "message": "用户消息内容",
  "session_id": 1  // 可选
}
```

- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "data": {
    "intent_prompt": "提示内容",
    "intent_result": {
      "intent": "analyze",
      "coin": "BTC",
      "timeframe": "daily"
    },
    "traditional_extraction": {
      "symbols": ["BTC"],
      "time_window": "1d"
    },
    "user_message": "分析一下BTC的日线"
  }
}
```

## 5. 反馈系统 API

### 5.1 提交对话评分

- **URL**: `/api/feedback/rate`
- **方法**: POST
- **描述**: 对整个对话进行评分和提供反馈
- **参数**:

```json
{
  "session_id": 1,
  "rating": 5,  // 1-5星评分
  "feedback": "反馈内容"  // 可选
}
```

- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "message": "感谢您的反馈"
}
```

### 5.2 提交单条消息评分

- **URL**: `/api/feedback/rate_message`
- **方法**: POST
- **描述**: 对单条AI回复进行评分，可用于在每条回复下方显示评分选项
- **参数**:

```json
{
  "message_id": 42,  // 消息ID
  "rating": 5,      // 1-5星评分
  "feedback": "这个回答很有帮助"  // 可选
}
```

- **认证**: 需要
- **返回值**:

```json
{
  "status": "success",
  "message": "感谢您的评分"
}
```

### 5.3 获取反馈分析

- **URL**: `/api/feedback/analytics`
- **方法**: GET
- **描述**: 获取反馈分析数据 (管理员功能)
- **参数**: 无
- **认证**: 需要 (管理员权限)
- **返回值**:

```json
{
  "status": "success",
  "data": {
    "average_rating": 4.5,
    "total_feedback": 100,
    "rating_distribution": {
      "1": 2,
      "2": 3,
      "3": 10,
      "4": 25,
      "5": 60
    }
  }
}
```

## 6. 健康检查 API

### 6.1 API健康检查

- **URL**: `/api/chat/api/health`
- **方法**: GET
- **描述**: 检查API服务是否正常运行
- **参数**: 无
- **认证**: 不需要
- **返回值**:

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

## 7. 使用限制说明

1. **免费用户限制**:
   - 最多创建 5 个会话
   - 每个会话最多发送 10 条消息
   - 无法删除会话

2. **付费会员**:
   - 无会话数量限制
   - 无消息数量限制
   - 可以删除会话

3. **错误代码**:
   - `SESSION_LIMIT_REACHED`: 达到会话数量限制
   - `MESSAGE_LIMIT_REACHED`: 达到消息数量限制

## 8. 开发注意事项

1. **认证处理**:
   - 所有需要认证的API都需要在请求头中添加 `Authorization: Bearer <token>`
   - Token有效期为7天，过期需要重新登录

2. **错误处理**:
   - 所有API返回的错误都包含 `status: "error"` 和错误信息 `message`
   - 特定错误会包含错误代码 `code`

3. **邀请码机制**:
   - 用户可以获取自己的邀请码并分享给他人
   - 新用户注册时可以填写邀请码 (即邀请人ID)

4. **会话管理**:
   - 创建新会话时，如果达到限制会返回错误
   - 发送消息时，如果未指定会话ID，系统会自动创建新会话

5. **消息格式**:
   - 所有消息内容均为纯文本
   - 消息历史按时间顺序排列，最新的消息在最后

6. **意图识别**:
   - 系统会自动识别用户消息中的币种、时间框架和意图
   - 支持的意图类型：分析(analyze)、交易(trade)、价格监控(monitor)、聊天(chat)

7. **币种支持**:
   - 系统支持所有主流加密货币，如BTC、ETH、SOL等
   - 币种符号格式为大写，如"BTC"、"ETH"

8. **时间框架**:
   - 支持的时间框架：分钟(m)、小时(h)、日(d)、周(w)、月(M)
   - 默认时间框架为日线(1d)
