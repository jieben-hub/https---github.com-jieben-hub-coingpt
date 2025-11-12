# 管理员模块使用说明

## 功能概述

本管理员模块提供以下功能：

1. **管理员登录/登出**
2. **用户管理** - 增删改查用户信息、会员等级管理
3. **公告管理** - 增删改查系统公告
4. **活动管理** - 增删改查系统活动

## API接口文档

### 1. 管理员登录

**接口**: `/admin/login`
**方法**: `POST`
**参数**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**返回**:
```json
{
  "status": "success",
  "message": "登录成功"
}
```

### 2. 管理员登出

**接口**: `/admin/logout`
**方法**: `POST`

**返回**:
```json
{
  "status": "success",
  "message": "登出成功"
}
```

### 3. 用户管理

#### 获取用户列表
**接口**: `/admin/users`
**方法**: `GET`
**参数**:
- `page`: 页码 (默认1)
- `per_page`: 每页数量 (默认20)

**返回**:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "username": "user1",
      "email": "user1@example.com",
      "apple_sub": "sub123",
      "membership": "free",
      "is_active": 1,
      "dialog_count": 10,
      "created_at": "2024-01-01 10:00:00",
      "last_login": "2024-01-02 10:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "pages": 5
}
```

#### 获取单个用户信息
**接口**: `/admin/users/{user_id}`
**方法**: `GET`

#### 更新用户信息
**接口**: `/admin/users/{user_id}`
**方法**: `PUT`
**参数**:
```json
{
  "username": "newname",
  "email": "newemail@example.com",
  "membership": "premium",
  "is_active": 1
}
```

#### 删除用户
**接口**: `/admin/users/{user_id}`
**方法**: `DELETE`

#### 升级用户会员等级
**接口**: `/admin/users/upgrade`
**方法**: `POST`
**参数**:
```json
{
  "user_id": 1,
  "membership": "premium"
}
```

### 4. 公告管理

#### 获取公告列表
**接口**: `/admin/announcements`
**方法**: `GET`
**参数**:
- `page`: 页码
- `per_page`: 每页数量
- `only_active`: 是否只显示活跃公告

#### 创建公告
**接口**: `/admin/announcements`
**方法**: `POST`
**参数**:
```json
{
  "title": "系统维护通知",
  "content": "系统将于明天进行维护...",
  "priority": 10,
  "is_active": true
}
```

#### 更新公告
**接口**: `/admin/announcements/{announcement_id}`
**方法**: `PUT`

#### 删除公告
**接口**: `/admin/announcements/{announcement_id}`
**方法**: `DELETE`

### 5. 活动管理

#### 获取活动列表
**接口**: `/admin/activities`
**方法**: `GET`
**参数**:
- `page`: 页码
- `per_page`: 每页数量
- `only_active`: 是否只显示活跃活动
- `current_only`: 是否只显示当前进行中的活动

#### 创建活动
**接口**: `/admin/activities`
**方法**: `POST`
**参数**:
```json
{
  "title": "新年活动",
  "description": "活动详情...",
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-31T23:59:59Z",
  "priority": 5,
  "is_active": true
}
```

#### 更新活动
**接口**: `/admin/activities/{activity_id}`
**方法**: `PUT`

#### 删除活动
**接口**: `/admin/activities/{activity_id}`
**方法**: `DELETE`

## 环境配置

管理员账号密码可通过环境变量配置：
- `ADMIN_USERNAME`: 管理员用户名（默认: admin）
- `ADMIN_PASSWORD`: 管理员密码（默认: admin123）

## 使用步骤

1. 启动应用后，通过 `/admin/login` 接口登录
2. 使用返回的会话进行其他管理操作
3. 完成操作后，调用 `/admin/logout` 登出

## 注意事项

- 所有管理接口都需要管理员登录状态
- 请妥善保管管理员账号密码
- 在生产环境中，务必修改默认密码
- 建议定期查看系统日志，监控异常操作