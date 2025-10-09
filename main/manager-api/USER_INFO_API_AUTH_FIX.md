# 用户信息API认证修复说明

## 问题描述

用户信息管理接口出现"token失效，请重新登录"错误，原因是这些接口只支持用户登录token认证，不支持API密钥认证。

## 问题分析

### 原始配置
```java
// 用户信息API使用oauth2过滤器，需要用户登录token
filterMap.put("/user/**", "oauth2");
```

### 场景API配置（正确）
```java
// 场景API使用双重认证，支持服务器密钥和用户token
filterMap.put("/scenario/**", "dual");
```

## 解决方案

为用户信息相关的API添加双重认证支持，使其能够使用API密钥进行认证。

### 修改内容

在 `ShiroConfig.java` 中添加以下配置：

```java
// 用户信息相关API使用双重认证（支持服务器密钥和用户token）
filterMap.put("/user/device-info", "dual");
filterMap.put("/user/has-name", "dual");
filterMap.put("/user/update-name", "dual");
filterMap.put("/user/update-knowledge", "dual");
filterMap.put("/user/knowledge", "dual");
filterMap.put("/user/interaction", "dual");
```

### 支持的API端点

1. **GET /user/device-info** - 根据设备ID获取用户信息
2. **GET /user/has-name** - 检查用户是否已设置姓名
3. **POST /user/update-name** - 更新用户姓名
4. **POST /user/update-knowledge** - 更新用户知识库
5. **GET /user/knowledge** - 获取用户知识库
6. **POST /user/interaction** - 记录用户交互

## 认证机制

### 双重认证过滤器 (DualAuthFilter)

1. **服务器密钥认证**：优先使用API密钥进行认证
   - Header: `Authorization: Bearer {server_secret}`
   - 从系统参数中获取 `SERVER_SECRET` 配置

2. **用户Token认证**：如果服务器密钥认证失败，尝试用户登录token
   - Header: `Authorization: Bearer {user_token}`
   - 需要用户先登录获取token

### 配置要求

确保在系统参数中配置了 `SERVER_SECRET`：

```yaml
# config.yaml
manager-api:
  secret: "your_server_secret_key"
```

## 测试验证

### 使用API密钥测试
```bash
curl -X GET "http://localhost:8002/user/device-info?deviceId=test_device" \
  -H "Authorization: Bearer your_server_secret_key" \
  -H "Content-Type: application/json"
```

### 使用用户Token测试
```bash
# 先登录获取token
curl -X POST "http://localhost:8002/user/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# 使用获取的token访问API
curl -X GET "http://localhost:8002/user/device-info?deviceId=test_device" \
  -H "Authorization: Bearer user_token_from_login" \
  -H "Content-Type: application/json"
```

## 影响范围

- ✅ 用户信息管理功能现在支持API密钥认证
- ✅ 与场景API保持一致的认证机制
- ✅ 向后兼容，仍支持用户token认证
- ✅ 不影响其他用户相关接口（登录、注册等）

## 部署说明

1. 重新编译后端项目
2. 重启manager-api服务
3. 验证用户信息API可以正常使用API密钥访问

## 注意事项

- 确保 `SERVER_SECRET` 配置正确且安全
- 用户信息API现在与场景API使用相同的认证机制
- 如果需要添加新的用户信息相关API，记得配置为 `dual` 过滤器
