# CoinGPT App 开发需求文档

## 1. 项目概述

CoinGPT App 是一个基于人工智能的加密货币分析和聊天助手，旨在帮助用户了解币价走势、市场分析和交易建议。应用提供直观的界面和智能的对话体验，支持实时数据分析和个性化推荐。本文档详细描述了应用的开发需求、API接口规范和实现步骤。

## 2. 技术栈

- **开发语言**：Swift（iOS 原生开发）
- **架构模式**：MVVM
- **UI 框架**：UIKit
- **网络请求**：Alamofire
- **异步通信**：Combine / async/await
- **本地缓存**：Core Data / NSCache
- **本地存储**：UserDefaults / Keychain
- **认证**：JWT 认证 / Apple Sign In
- **实时通信**：Server-Sent Events (SSE)
- **依赖管理**：CocoaPods

## 3. 数据通信与缓存策略

### 3.1 异步通信

- **异步请求模式**：所有网络请求必须采用异步方式，使用Combine或async/await实现
- **请求状态管理**：每个请求必须包含加载中、成功、失败状态处理
- **超时处理**：所有请求需设置适当超时，默认30秒，超时后提示用户并支持重试
- **并发控制**：防止重复请求，实现请求取消和请求合并机制

### 3.2 数据缓存

- **缓存层级**：实现内存缓存和磁盘缓存两级缓存策略
- **缓存对象**：用户信息、会话列表、消息历史必须进行缓存
- **缓存过期**：用户信息缓存24小时，会话列表缓存30分钟，消息历史缓存60分钟
- **缓存更新**：当进行写操作时（发送消息、创建会话）自动更新相关缓存

### 3.3 手动刷新

- **下拉刷新**：所有列表页面（会话列表、消息历史）必须支持下拉刷新
- **刷新按钮**：在导航栏添加刷新按钮，允许用户手动强制刷新数据
- **自动刷新控制**：允许用户在设置中配置自动刷新的频率（关闭、每分钟、每5分钟、每30分钟）
- **离线模式**：当网络不可用时，显示缓存数据并标记为离线模式

## 4. 开发优先级和进度规划

### 4.1 第一阶段：用户认证与基础框架（1-2周）

1. **项目初始化与架构搭建**
   - 创建项目并配置基础架构
   - 设置网络层和API客户端
   - 实现JWT Token管理

2. **用户认证模块**
   - 登录功能（接口：`POST /api/auth/login`），异步处理，缓存用户凭证
   - 注册功能（接口：`POST /api/auth/register`），异步处理，支持邀请码
   - Apple 登录集成（接口：`POST /api/auth/apple/login`），异步处理
   - 登出功能（接口：`POST /api/auth/logout`），清除本地缓存

### 4.2 第二阶段：聊天核心功能（3-4周）

1. **聊天界面实现**
   - 消息列表UI，支持下拉刷新和手动刷新
   - 消息气泡设计，包含用户和AI消息不同样式
   - Markdown渲染支持，处理代码块和表格
   - 输入区域实现，支持多行输入和发送按钮

2. **聊天功能实现**
   - 消息发送（接口：`POST /api/chat/`），异步处理，缓存已发送消息
   - 流式输出处理（接口：`POST /api/chat/?stream=true`），使用SSE实时显示
   - 消息历史获取（接口：`GET /api/chat/session/{session_id}`），异步加载并缓存
   - 消息评分功能（接口：`POST /api/feedback/rate_message`），异步处理
   - 错误处理与重试机制，支持离线模式下查看缓存消息

### 4.3 第三阶段：会话管理与个人中心（5-6周）

1. **会话管理**
   - 会话列表获取（接口：`GET /api/auth/sessions`），异步加载，支持下拉刷新和手动刷新，缓存30分钟
   - 会话创建（接口：`POST /api/auth/sessions`），异步处理，创建后自动更新缓存
   - 会话切换与导航，支持离线模式下查看缓存会话
   - 会话删除与重命名功能，异步处理

2. **个人中心**
   - 用户信息获取（接口：`GET /api/auth/user`），异步加载，缓存24小时，支持手动刷新
   - 使用统计展示，显示对话数量和会话数量，从用户信息缓存中获取
   - 邀请码获取（接口：`GET /api/auth/invite`），异步加载，支持复制和分享
   - 邀请用户列表（接口：`GET /api/auth/invitees`），异步加载，支持下拉刷新
   - 会话评分功能（接口：`POST /api/feedback/rate`），异步处理
   - 设置选项，包括自动刷新频率、消息通知等配置

### 4.4 第四阶段：反馈系统与优化（7-8周）

1. **反馈系统**
   - 消息评分功能（接口：`POST /api/feedback/rate_message`），异步处理，支持点赞/点踩
   - 会话评分功能（接口：`POST /api/feedback/rate`），异步处理，支持1-5星评分和文字反馈
   - 反馈分析统计（接口：`GET /api/feedback/analytics`），异步加载，缓存24小时提交

2. **邀请系统**
   - 邀请码获取（接口：`GET /api/auth/invite`），异步加载，缓存24小时，支持手动刷新
   - 邀请用户列表（接口：`GET /api/auth/invitees`），异步加载，支持下拉刷新和手动刷新
   - 邀请码分享功能，支持复制和系统分享

3. **性能优化**
   - 图片缓存与加载优化，使用NSCache和磁盘缓存
   - 内存使用优化，实现消息分页加载和内存释放
   - 网络请求队列与合并，实现请求限流和失败重试
   - 健康检查功能（接口：`GET /api/chat/api/health`），定期检测服务器状态

## 5. API接口规范

### 5.1 基础信息

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

#### 4.4.3 删除会话

- **URL**: `/api/auth/sessions/{session_id}`
- **方法**: DELETE
- **描述**: 删除指定的会话（仅会员用户可用）
- **请求参数**: 无（session_id在URL中指定）
- **响应数据**:

```swift
struct DeleteSessionResponse: Codable {
    let status: String
    let message: String
    let code: String?
}
```

- **实现示例**:

```swift
func deleteSession(sessionId: Int) async throws -> DeleteSessionResponse {
    return try await APIClient.shared.request(
        .delete,
        path: "/api/auth/sessions/\(sessionId)"
    )
}

// 使用示例
func handleDeleteSession(sessionId: Int) async {
    do {
        let response = try await deleteSession(sessionId: sessionId)
        if response.status == "success" {
            // 删除成功处理
            showToast(message: response.message)
            refreshSessionList()
        } else {
            // 错误处理
            if response.code == "PREMIUM_REQUIRED" {
                showUpgradeDialog(message: response.message)
            } else {
                showErrorAlert(message: response.message)
            }
        }
    } catch {
        showErrorAlert(message: "删除会话失败: \(error.localizedDescription)")
    }
}
```

#### 4.4.4 获取会话消息

- **URL**: `/api/chat/session/{session_id}`
- **方法**: GET
- **描述**: 获取指定会话的历史消息
- **请求参数**:
  - `session_id`: 会话ID (URL路径参数)
- **响应数据**:

```swift
struct SessionMessagesResponse: Codable {
    let status: String
    let data: SessionData
    
    struct SessionData: Codable {
        let session_id: Int
        let messages: [MessageInfo]
    }
    
    struct MessageInfo: Codable {
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
    let message: String
    let session_id: Int
}
```

- **响应数据** (流式, SSE格式):

```
data: {"content":"AI回复", "done":false}
data: {"content":"的部分", "done":false}
data: {"content":"内容", "done":true, "message_id":42}
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
func sendStreamMessage(sessionId: Int, message: String, onReceive: @escaping (String, Bool, Int?) -> Void) {
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
        
        let messageId = json["message_id"] as? Int
        onReceive(content, done, messageId)
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

#### 5.1.1 UI布局与组件

- **整体布局**：全屏垂直设计，上方为应用Logo和标题，中间为表单区域，底部为辅助操作按钮

- **登录表单**：
  - 用户名输入框：圆角矩形，高度50pt，宽度屏幕宽度的80%，居中对齐，内部左侧填充为15pt
  - 密码输入框：与用户名输入框相同样式，隐藏密码显示，右侧添加显示/隐藏切换按钮
  - 登录按钮：圆角矩形，高度50pt，宽度与输入框一致，背景色为主题色(#10a37f)，白色文字
  - Apple登录按钮：黑色背景，白色Apple图标和文字，高度50pt，使用系统ASAuthorizationAppleIDButton

- **注册表单**：
  - 用户名输入框：与登录表单相同
  - 密码输入框：与登录表单相同
  - 确认密码输入框：与密码输入框相同
  - 邀请码输入框（可选）：样式与其他输入框一致，添加“可选”标记
  - 注册按钮：与登录按钮相同样式

- **辅助元素**：
  - 错误提示标签：红色文字，位于表单下方，默认隐藏
  - 登录/注册切换按钮：文本按钮，位于底部，带下划线
  - 隐私政策和服务条款链接：小号文本，位于最底部

#### 5.1.2 交互设计

1. **切换效果**：登录和注册表单之间使用水平滑动过渡效果
2. **表单验证**：实时验证输入内容，不符合规则时输入框边框变红并显示错误提示
3. **加载状态**：登录/注册按钮点击后显示旋转加载指示器，按钮文字变为“正在登录...”

#### 5.1.3 实现步骤

1. 创建`LoginViewController`和`RegisterViewController`类
2. 使用Auto Layout构建响应式界面
3. 实现表单验证逻辑和错误提示
4. 集成Apple登录按钮和授权流程
5. 实现Keychain存储进行安全凭证管理
6. 处理登录/注册API调用和响应

### 5.2 聊天模块

#### 5.2.1 UI布局与组件

- **整体布局**：
  - 导航栏：顶部，高度44pt，包含会话标题、返回按钮和菜单按钮
  - 消息区域：占据主要屏幕空间，使用`UICollectionView`实现
  - 输入区域：底部，固定高度且可根据输入内容自动扩展

- **消息气泡设计**：
  - 用户消息：
    - 位置：右侧对齐，距离右边16pt
    - 外观：圆角矩形，半径为18pt，主题色背景(#10a37f)，白色文字
    - 内边距：上下12pt，左右16pt
    - 最大宽度：屏幕宽度的75%
  
  - AI回复消息：
    - 位置：左侧对齐，距离左边16pt，左侧显示AI头像，尺寸30x30pt
    - 外观：圆角矩形，半径为18pt，浅色背景(#f7f7f8)，深色文字
    - 内边距：上下12pt，左右16pt
    - 最大宽度：屏幕宽度的85%
    - 特殊效果：支持Markdown渲染，包括代码块、表格、列表等

- **输入区域**：
  - 布局：底部栏，宽度占据屏幕宽度，带有模糊背景效果
  - 输入框：圆角矩形，半径为18pt，最小高度44pt，最大高度120pt，自动扩展
  - 发送按钮：圆形，直径36pt，位于输入框右侧，主题色背景，白色发送图标

- **交互元素**：
  - 加载指示器：在AI回复气泡中，流式输出时显示打字动画
  - 消息评分按钮：每条AI回复下方显示评分选项（👍/👎），默认半透明，选中后高亮
  - 消息时间戳：在每条消息上方或下方显示发送时间，小号浅色文字
  - 滚动到底部按钮：当有新消息且用户不在底部时显示

#### 5.2.2 交互设计

1. **消息输入**：
   - 输入框获取焦点时自动将消息列表滚动到底部
   - 支持多行输入，按回车键换行，按Shift+回车发送消息
   - 输入内容为空时发送按钮禁用

2. **消息加载**：
   - 发送消息后立即在列表中显示用户消息
   - AI回复区域显示打字动画，流式输出文本
   - 流式输出完成后显示评分按钮

3. **滚动行为**：
   - 新消息到达时自动滚动到底部
   - 支持上拉加载历史消息
   - 浏览历史消息时显示“滚动到底部”按钮

4. **Markdown渲染**：
   - 支持代码块语法高亮，带复制按钮
   - 支持表格、列表、引用等格式化内容
   - 支持数学公式和图表展示

#### 5.2.3 实现步骤

1. 创建`ChatViewController`和自定义消息Cell（`UserMessageCell`和`AIMessageCell`）
2. 使用`UICollectionViewCompositionalLayout`实现消息列表布局
3. 集成`MarkdownKit`或`Down`库实现Markdown渲染
4. 实现自动扩展的输入区域和键盘处理
5. 实现消息发送和接收逻辑
6. 使用`EventSource`实现SSE流式输出处理
7. 添加消息评分功能和动画效果
8. 实现消息列表的性能优化，如延迟加载和回收利用

### 5.3 会话管理模块

#### 5.3.1 UI布局与组件

- **整体布局**：
  - 导航栏：顶部，高度44pt，包含应用标题、用户头像按钮和新建会话按钮
  - 搜索栏：导航栏下方，高度44pt，圆角矩形，带搜索图标
  - 会话列表：使用`UITableView`，占据剩余屏幕空间

- **会话卡片设计**：
  - 高度：70pt
  - 布局：水平方向分为两部分
  - 左侧：会话标题（粗体，16pt）和最后一条消息预览（浅色，14pt，单行截断）
  - 右侧：时间戳（小号，12pt）和币种图标（如有）
  - 分隔线：浅色，宽度为屏幕宽度的90%，居中对齐

- **新建会话按钮**：
  - 类型：浮动操作按钮（FAB）
  - 位置：右下角，距离底部和右侧各20pt
  - 外观：圆形，直径56pt，主题色背景，白色“+”图标
  - 阴影：轻微阴影效果，增强浮动感

- **搜索交互**：
  - 搜索栏：圆角矩形，半径18pt，浅灰色背景，左侧有搜索图标
  - 取消按钮：搜索模式下显示在搜索栏右侧
  - 筛选按钮：位于搜索栏右侧，显示筛选图标

- **空状态设计**：
  - 位置：屏幕中央
  - 内容：提示图标（聊天气泡）、文字提示和创建新会话的引导按钮
  - 样式：浅色图标和文字，主题色按钮

#### 5.3.2 交互设计

1. **会话列表交互**：
   - 左滑操作：
     - 会员用户：显示删除和编辑选项
     - 非会员用户：显示编辑选项，删除选项显示为灰色并标记会员图标
   - 长按操作：
     - 会员用户：显示上下文菜单，包含删除、重命名、导出等选项
     - 非会员用户：删除选项显示为灰色并标记会员图标，点击时显示升级提示
   - 点击操作：进入相应会话的聊天界面

2. **搜索交互**：
   - 实时搜索：输入时即时过滤会话列表
   - 搜索范围：会话标题、消息内容和币种标签
   - 搜索结果高亮：匹配文本使用主题色高亮显示

3. **筛选交互**：
   - 点击筛选按钮显示筛选面板
   - 支持按币种、时间范围和会话评分进行筛选
   - 应用筛选后列表实时更新

4. **新建会话**：
   - 点击新建按钮时显示微小的缩放动画
   - 创建新会话后自动跳转到聊天界面
   - 新会话创建后显示在列表顶部

#### 5.3.3 实现步骤

1. 创建`SessionsViewController`和自定义`SessionTableViewCell`
2. 使用`UISearchController`实现搜索功能
3. 实现会话列表数据源和始终保持最新状态
4. 实现会话操作功能（创建、删除、重命名）
5. 实现筛选功能和自定义筛选面板
6. 添加列表动画和过渡效果
7. 实现空状态处理和引导界面

### 5.4 个人中心模块

#### 5.4.1 UI布局与组件

- **整体布局**：
  - 导航栏：顶部，高度44pt，显示“个人中心”标题和返回按钮
  - 内容区域：使用`UITableView`实现，包含多个功能区块
  - 底部区域：包含登出按钮和版本信息

- **用户信息卡片**：
  - 布局：表格的首个区域，高度120pt，带有浅色背景
  - 头像：圆形，直径80pt，左侧对齐，距离左边20pt
  - 用户名：粗体，18pt，头像右侧，垂直居中对齐
  - 会员等级：用户名下方，小号，14pt，带有特殊标识（如金色标签或图标）
  - 编辑按钮：右侧，文本按钮，主题色

- **使用统计区域**：
  - 布局：卡片式设计，圆角矩形，带有浅色背景和细微阴影
  - 数据展示：使用网格布局，显示关键指标（对话数量、消息数量、使用天数）
  - 数值显示：大号粗体，24pt，下方是小号标签文字，12pt
  - 内边距：四周填充为16pt

- **邀请系统区域**：
  - 布局：卡片式设计，与使用统计区域相同样式
  - 邀请码展示：大号字体，带复制按钮
  - 邀请人数统计：显示已邀请人数和限额
  - 分享按钮：主题色按钮，带分享图标

- **设置选项列表**：
  - 布局：分组表格视图，每个选项高度50pt
  - 选项样式：左侧图标，中间标题，右侧箭头或开关
  - 分组：按功能分组，如“账户设置”、“应用设置”、“关于”等
  - 分组标题：小号浅色文字，左侧对齐，内边距16pt

- **登出按钮**：
  - 布局：底部区域，宽度占据屏幕宽度的90%，高度50pt
  - 样式：圆角矩形，红色文字，浅色背景，无边框
  - 位置：居中对齐，距离底部20pt

#### 5.4.2 交互设计

1. **用户信息编辑**：
   - 点击编辑按钮弹出编辑弹窗
   - 支持修改用户名和头像
   - 头像支持从相册选择或拍照

2. **邀请系统交互**：
   - 点击复制按钮复制邀请码并显示成功提示
   - 点击分享按钮调用系统分享面板
   - 支持查看已邀请用户列表

3. **设置选项交互**：
   - 点击设置项进入相应设置页面
   - 开关类选项支持直接在列表中切换
   - 带有视觉反馈和过渡动画

4. **登出交互**：
   - 点击登出按钮显示确认弹窗
   - 确认登出后返回登录界面
   - 清除本地用户数据和会话缓存

#### 5.4.3 实现步骤

1. 创建`ProfileViewController`和各种自定义Cell
2. 使用`UITableView`实现分组列表布局
3. 实现用户信息获取和展示
4. 实现邀请码功能和分享机制
5. 实现各种设置项和子页面
6. 实现登出功能和数据清理
7. 添加页面过渡动画和交互反馈

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
