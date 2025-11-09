# CoinGPT App 开发需求文档

## 1. 项目概述

CoinGPT App 是一个基于人工智能的加密货币分析和聊天助手，旨在帮助用户了解币价走势、市场分析和交易建议。应用提供直观的界面和智能的对话体验，支持实时数据分析和个性化推荐。本文档详细描述了应用的开发需求、API接口规范和实现步骤。

## 2. 技术栈

- **开发语言**：Swift（iOS 原生开发）
- **架构模式**：MVVM
- **UI 框架**：UIKit
- **网络请求**：Alamofire
- **本地存储**：UserDefaults / Keychain
- **认证**：JWT 认证 / Apple Sign In
- **实时通信**：Server-Sent Events (SSE)
- **依赖管理**：CocoaPods

## 3. 开发优先级和进度规划

### 3.1 第一阶段：用户认证与基础框架（1-2周）

1. **项目初始化与架构搭建**
   - 创建项目并配置基础架构
   - 设置网络层和API客户端
   - 实现JWT Token管理

2. **用户认证模块**
   - 登录/注册界面
   - Apple 登录集成
   - 生物识别认证（Face ID/Touch ID）

### 3.2 第二阶段：聊天核心功能（3-4周）

1. **聊天界面实现**
   - 消息列表UI
   - 消息气泡设计
   - Markdown渲染支持
   - 输入区域实现

2. **聊天功能实现**
   - 消息发送与接收
   - 流式输出处理（SSE）
   - 错误处理与重试机制

### 3.3 第三阶段：会话管理与个人中心（5-6周）

1. **会话管理**
   - 会话列表
   - 会话创建与切换
   - 会话历史记录

2. **个人中心**
   - 用户信息展示
   - 使用统计
   - 设置选项

### 3.4 第四阶段：反馈系统与优化（7-8周）

1. **反馈系统**
   - 消息评分功能
   - 会话评分功能
   - 反馈提交

2. **邀请系统**
   - 邀请码生成与展示
   - 邀请用户列表
   - 分享功能

## 4. API接口规范

### 4.1 基础信息

- **基础URL**: `http://192.168.31.127:5000`
- **认证方式**: Bearer Token (通过 HTTP 头 `Authorization: Bearer <token>` 传递)
- **数据格式**: 所有请求和响应均使用 JSON 格式
- **状态码**:
  - 200: 成功
  - 400: 请求错误
  - 401: 认证失败
  - 403: 权限不足
  - 500: 服务器错误

### 4.2 认证相关API

#### 4.2.1 用户注册

- **URL**: `/api/auth/register`
- **方法**: POST
- **描述**: 注册新用户
- **请求参数**:

```swift
struct RegisterRequest: Codable {
    let username: String
    let password: String
    let inviter_id: String?  // 可选
}
```

- **响应数据**:

```swift
struct RegisterResponse: Codable {
    let status: String
    let data: RegisterData
    
    struct RegisterData: Codable {
        let user: UserInfo
        let token: String
    }
    
    struct UserInfo: Codable {
        let user_id: Int
        let username: String
        let membership: String
        let dialog_count: Int
        let inviter_id: Int?
        let created_at: String
    }
}
```

- **实现示例**:

```swift
func register(username: String, password: String, inviterId: String? = nil) async throws -> RegisterResponse {
    let parameters: [String: Any] = [
        "username": username,
        "password": password,
        "inviter_id": inviterId
    ].compactMapValues { $0 }
    
    return try await APIClient.shared.request(
        .post,
        path: "/api/auth/register",
        parameters: parameters
    )
}
```

#### 4.2.2 用户登录

- **URL**: `/api/auth/login`
- **方法**: POST
- **描述**: 用户登录
- **请求参数**:

```swift
struct LoginRequest: Codable {
    let username: String
    let password: String
}
```

- **响应数据**:

```swift
struct LoginResponse: Codable {
    let status: String
    let data: LoginData
    
    struct LoginData: Codable {
        let user: UserInfo
        let token: String
    }
    
    struct UserInfo: Codable {
        let user_id: Int
        let username: String
        let membership: String
        let dialog_count: Int
        let created_at: String
        let last_login: String?
    }
}
```

- **实现示例**:

```swift
func login(username: String, password: String) async throws -> LoginResponse {
    let parameters: [String: Any] = [
        "username": username,
        "password": password
    ]
    
    return try await APIClient.shared.request(
        .post,
        path: "/api/auth/login",
        parameters: parameters
    )
}
```

#### 4.2.3 Apple账号登录

- **URL**: `/api/auth/apple/login`
- **方法**: POST
- **描述**: 使用Apple账号登录
- **请求参数**:

```swift
struct AppleLoginRequest: Codable {
    let id_token: String
    let user_info: AppleUserInfo?
    let inviter_id: String?
    
    struct AppleUserInfo: Codable {
        let name: AppleName?
        let email: String?
        
        struct AppleName: Codable {
            let firstName: String?
            let lastName: String?
        }
    }
}
```

- **响应数据**: 与普通登录相同

- **实现示例**:

```swift
func appleLogin(idToken: String, userInfo: AppleUserInfo?, inviterId: String? = nil) async throws -> LoginResponse {
    let parameters: [String: Any] = [
        "id_token": idToken,
        "user_info": userInfo,
        "inviter_id": inviterId
    ].compactMapValues { $0 }
    
    return try await APIClient.shared.request(
        .post,
        path: "/api/auth/apple/login",
        parameters: parameters
    )
}
```

#### 4.2.4 用户登出

- **URL**: `/api/auth/logout`
- **方法**: POST
- **描述**: 用户登出
- **请求参数**: 无
- **响应数据**:

```swift
struct LogoutResponse: Codable {
    let status: String
    let message: String
}
```

- **实现示例**:

```swift
func logout() async throws -> LogoutResponse {
    return try await APIClient.shared.request(
        .post,
        path: "/api/auth/logout"
    )
}
```

#### 4.2.5 获取邀请码

- **URL**: `/api/auth/invite`
- **方法**: GET
- **描述**: 获取当前用户的邀请码
- **请求参数**: 无
- **响应数据**:

```swift
struct InviteCodeResponse: Codable {
    let status: String
    let data: InviteData
    
    struct InviteData: Codable {
        let invite_code: String
        let invitee_count: Int
    }
}
```

- **实现示例**:

```swift
func getInviteCode() async throws -> InviteCodeResponse {
    return try await APIClient.shared.request(
        .get,
        path: "/api/auth/invite"
    )
}
```

#### 4.2.6 获取邀请用户列表

- **URL**: `/api/auth/invitees`
- **方法**: GET
- **描述**: 获取当前用户邀请的所有用户列表
- **请求参数**: 无
- **响应数据**:

```swift
struct InviteesResponse: Codable {
    let status: String
    let data: [InviteeInfo]
    
    struct InviteeInfo: Codable {
        let user_id: Int
        let created_at: String
    }
}
```

- **实现示例**:

```swift
func getInvitees() async throws -> InviteesResponse {
    return try await APIClient.shared.request(
        .get,
        path: "/api/auth/invitees"
    )
}
```

### 4.3 用户信息API

#### 4.3.1 获取当前用户信息

- **URL**: `/api/auth/user`
- **方法**: GET
- **描述**: 获取当前登录用户的详细信息
- **请求参数**: 无
- **响应数据**:

```swift
struct UserInfoResponse: Codable {
    let status: String
    let data: UserData
    
    struct UserData: Codable {
        let user_id: Int
        let membership: String
        let dialog_count: Int
        let created_at: String
        let last_login: String?
    }
}
```

- **实现示例**:

```swift
func getUserInfo() async throws -> UserInfoResponse {
    return try await APIClient.shared.request(
        .get,
        path: "/api/auth/user"
    )
}
```

#### 4.3.2 获取用户使用情况

- **URL**: `/api/auth/usage-stats`
- **方法**: GET
- **描述**: 获取用户使用统计信息
- **请求参数**: 无
- **响应数据**:

```swift
struct UsageStatsResponse: Codable {
    let status: String
    let data: UsageData
    
    struct UsageData: Codable {
        let total_sessions: Int
        let total_messages: Int
        let remaining_sessions: Int
        let remaining_messages: Int
        let membership: String
        let session_limit: Int
        let message_limit: Int
    }
}
```

- **实现示例**:

```swift
func getUsageStats() async throws -> UsageStatsResponse {
    return try await APIClient.shared.request(
        .get,
        path: "/api/auth/usage-stats"
    )
}
```

### 4.4 会话管理API

#### 4.4.1 获取会话列表

- **URL**: `/api/auth/sessions`
- **方法**: GET
- **描述**: 获取用户的会话列表
- **请求参数**:
  - `limit`: 可选，限制返回的会话数量
- **响应数据**:

```swift
struct SessionsResponse: Codable {
    let status: String
    let data: [SessionInfo]
    
    struct SessionInfo: Codable {
        let session_id: Int
        let created_at: String
        let updated_at: String
        let last_symbol: String?
        let preview: String
    }
}
```

- **实现示例**:

```swift
func getSessions(limit: Int = 5) async throws -> SessionsResponse {
    return try await APIClient.shared.request(
        .get,
        path: "/api/auth/sessions",
        parameters: ["limit": limit]
    )
}
```

#### 4.4.2 创建新会话

- **URL**: `/api/auth/sessions`
- **方法**: POST
- **描述**: 创建一个新的会话
- **请求参数**: 无
- **响应数据**:

```swift
struct CreateSessionResponse: Codable {
    let status: String
    let data: SessionData
    
    struct SessionData: Codable {
        let session_id: Int
        let created_at: String
    }
}
```

- **实现示例**:

```swift
func createSession() async throws -> CreateSessionResponse {
    return try await APIClient.shared.request(
        .post,
        path: "/api/auth/sessions"
    )
}
```

#### 4.4.3 获取会话消息

- **URL**: `/api/chat/session/{session_id}`
- **方法**: GET
- **描述**: 获取指定会话的历史消息
- **请求参数**:
  - `session_id`: 会话ID (URL路径参数)
- **响应数据**:

```swift
struct SessionMessagesResponse: Codable {
    let status: String
    let data: [MessageInfo]
    
    struct MessageInfo: Codable {
        let message_id: Int
        let session_id: Int
        let role: String  // "user" 或 "assistant"
        let content: String
        let created_at: String
    }
}
```

- **实现示例**:

```swift
func getSessionMessages(sessionId: Int) async throws -> SessionMessagesResponse {
    return try await APIClient.shared.request(
        .get,
        path: "/api/chat/session/\(sessionId)"
    )
}
```

### 4.5 聊天API

#### 4.5.1 发送消息

- **URL**: `/api/chat/`
- **方法**: POST
- **描述**: 发送消息并获取AI回复
- **请求参数**:

```swift
struct SendMessageRequest: Codable {
    let session_id: Int
    let message: String
    let stream: Bool?  // 是否使用流式输出，默认false
}
```

- **响应数据** (非流式):

```swift
struct ChatResponse: Codable {
    let status: String
    let data: ChatData
    
    struct ChatData: Codable {
        let message_id: Int
        let content: String
        let created_at: String
    }
}
```

- **响应数据** (流式, SSE格式):

```
data: {"content":"AI回复", "done":false}
data: {"content":"的部分", "done":false}
data: {"content":"内容", "done":true}
```

- **实现示例** (非流式):

```swift
func sendMessage(sessionId: Int, message: String) async throws -> ChatResponse {
    let parameters: [String: Any] = [
        "session_id": sessionId,
        "message": message
    ]
    
    return try await APIClient.shared.request(
        .post,
        path: "/api/chat/",
        parameters: parameters
    )
}
```

- **实现示例** (流式):

```swift
func sendStreamMessage(sessionId: Int, message: String, onReceive: @escaping (String, Bool) -> Void) {
    let parameters: [String: Any] = [
        "session_id": sessionId,
        "message": message,
        "stream": true
    ]
    
    APIClient.shared.requestSSE(
        path: "/api/chat/",
        parameters: parameters
    ) { data in
        guard let data = data,
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let content = json["content"] as? String,
              let done = json["done"] as? Bool else {
            return
        }
        
        onReceive(content, done)
    }
}
```

### 4.6 反馈系统API

#### 4.6.1 提交会话评分

- **URL**: `/api/feedback/rate`
- **方法**: POST
- **描述**: 提交对整个会话的评分和反馈
- **请求参数**:

```swift
struct RateSessionRequest: Codable {
    let session_id: Int
    let rating: Int  // 1-5
    let feedback: String?
}
```

- **响应数据**:

```swift
struct RateResponse: Codable {
    let status: String
    let message: String
}
```

- **实现示例**:

```swift
func rateSession(sessionId: Int, rating: Int, feedback: String? = nil) async throws -> RateResponse {
    let parameters: [String: Any] = [
        "session_id": sessionId,
        "rating": rating,
        "feedback": feedback
    ].compactMapValues { $0 }
    
    return try await APIClient.shared.request(
        .post,
        path: "/api/feedback/rate",
        parameters: parameters
    )
}
```

#### 4.6.2 提交消息评分

- **URL**: `/api/feedback/rate_message`
- **方法**: POST
- **描述**: 提交对单条消息的评分和反馈
- **请求参数**:

```swift
struct RateMessageRequest: Codable {
    let message_id: Int
    let rating: Int  // 1-5
    let feedback: String?
}
```

- **响应数据**:

```swift
struct RateMessageResponse: Codable {
    let status: String
    let message: String
}
```

- **实现示例**:

```swift
func rateMessage(messageId: Int, rating: Int, feedback: String? = nil) async throws -> RateMessageResponse {
    let parameters: [String: Any] = [
        "message_id": messageId,
        "rating": rating,
        "feedback": feedback
    ].compactMapValues { $0 }
    
    return try await APIClient.shared.request(
        .post,
        path: "/api/feedback/rate_message",
        parameters: parameters
    )
}
```

### 4.7 健康检查API

- **URL**: `/api/chat/api/health`
- **方法**: GET
- **描述**: API健康检查
- **请求参数**: 无
- **响应数据**:

```swift
struct HealthCheckResponse: Codable {
    let status: String
    let message: String
}
```

- **实现示例**:

```swift
func checkHealth() async throws -> HealthCheckResponse {
    return try await APIClient.shared.request(
        .get,
        path: "/api/chat/api/health"
    )
}
```

## 5. UI模块详细设计

### 5.1 登录/注册模块

#### 5.1.1 UI组件

- 登录表单（用户名/密码输入框）
- Apple登录按钮
- 注册表单（用户名/密码/确认密码输入框）
- 邀请码输入框（可选）
- 错误提示标签
- 登录/注册切换按钮

#### 5.1.2 实现步骤

1. 创建`LoginViewController`和`RegisterViewController`
2. 实现表单验证逻辑
3. 集成Apple登录按钮和授权流程
4. 实现生物识别认证
5. 处理登录/注册API调用
6. 实现错误处理和用户反馈

### 5.2 聊天模块

#### 5.2.1 UI组件

- 消息列表（`UICollectionView`）
- 用户消息气泡（右侧对齐）
- AI回复气泡（左侧对齐）
- 输入区域（`UITextView`）
- 发送按钮
- 加载指示器
- 消息评分按钮（👍/👎）

#### 5.2.2 实现步骤

1. 创建`ChatViewController`和自定义消息Cell
2. 实现消息列表布局和自适应高度
3. 集成Markdown渲染库
4. 实现输入区域和键盘处理
5. 实现消息发送和接收逻辑
6. 实现流式输出处理（SSE）
7. 添加消息评分功能

### 5.3 会话管理模块

#### 5.3.1 UI组件

- 会话列表（`UITableView`）
- 会话卡片（包含预览、时间、币种信息）
- 新建会话按钮
- 搜索栏
- 筛选选项
- 空状态提示

#### 5.3.2 实现步骤

1. 创建`SessionsViewController`和自定义Cell
2. 实现会话列表获取和展示
3. 实现新建会话功能
4. 添加会话搜索和筛选功能
5. 实现会话选择和导航逻辑

### 5.4 个人中心模块

#### 5.4.1 UI组件

- 用户信息卡片（头像、用户名、会员等级）
- 使用统计区域
- 邀请系统区域
- 设置选项列表
- 登出按钮

#### 5.4.2 实现步骤

1. 创建`ProfileViewController`
2. 实现用户信息获取和展示
3. 实现使用统计展示
4. 添加邀请码生成和分享功能
5. 实现设置选项和登出功能

## 6. 开发流程与测试

### 6.1 开发流程

1. **基础框架搭建**
   - 创建项目和目录结构
   - 配置网络层和API客户端
   - 实现基础UI组件和导航

2. **模块开发顺序**
   - 登录/注册模块
   - 聊天核心功能
   - 会话管理
   - 个人中心
   - 反馈系统
   - 邀请系统

3. **代码规范**
   - 使用Swift风格指南
   - 实现适当的错误处理
   - 添加必要的注释和文档

### 6.2 测试计划

1. **单元测试**
   - 网络请求和响应解析
   - 业务逻辑和数据处理
   - UI组件和交互

2. **集成测试**
   - API集成测试
   - 模块间交互测试
   - 用户流程测试

3. **UI测试**
   - 界面布局和响应式适配
   - 用户交互流程
   - 边缘情况处理

### 6.3 发布准备

1. **性能优化**
   - 内存使用优化
   - 网络请求优化
   - UI渲染优化

2. **安全审核**
   - 敏感数据处理
   - 认证和授权机制
   - 网络安全

3. **应用商店准备**
   - 应用图标和截图
   - 应用描述和关键词
   - 隐私政策和使用条款

## 7. 附录

### 7.1 API基础URL

- 开发环境: `http://192.168.31.127:5000`
- 测试环境: `https://test-api.coingpt.com`
- 生产环境: `https://api.coingpt.com`

### 7.2 错误码说明

- 400: 请求参数错误
- 401: 未认证或认证失败
- 403: 权限不足
- 404: 资源不存在
- 429: 请求频率超限
- 500: 服务器内部错误

### 7.3 免费用户限制

- 最多创建5个会话
- 每个会话最多10条消息
- 不支持高级分析功能

### 7.4 参考文档

- [API文档.md](API文档.md) - 详细API接口说明
- [Swift风格指南](https://swift.org/documentation/api-design-guidelines/) - Swift编码规范
- [Apple人机界面指南](https://developer.apple.com/design/human-interface-guidelines/) - iOS界面设计规范
