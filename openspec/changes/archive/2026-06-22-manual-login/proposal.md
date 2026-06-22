## Why

当前用户系统仅支持微信自动登录（通过 deviceId），但后端因缺少 `aiomysql` 导致数据库连接失败，登录接口返回 500。同时缺少手动登录/注册功能，用户无法主动选择账号登录。需要增加用户名+密码的登录方式，保留微信登录，并修复数据库连接。

## What Changes

### 修复
- 安装 `aiomysql` 依赖，修复数据库连接
- 后端 `init_db()` 成功后，用户相关接口恢复正常

### 新增功能
- `users` 表新增 `username`（唯一）和 `password_hash` 字段
- 新增 `POST /api/user/login/manual` 接口：用户名+密码登录/自动注册
- 新增登录页（用户名输入 + 密码输入 + 微信一键登录按钮）
- 个人中心底部新增"退出登录"按钮
- 未登录时个人中心显示"去登录"入口

## Capabilities

### New Capabilities
- `manual-login`: 手动登录/注册 — 用户可通过用户名+密码登录，未注册自动创建账号

### Modified Capabilities
- （无）

## Impact

- **后端新增依赖**：`aiomysql`、`passlib[bcrypt]`
- **后端修改**：`app/db/models/user.py`（新增字段）、`app/models/user.py`（新增请求模型）、`app/services/user_service.py`（新增手动登录函数）、`app/api/v1/endpoints/user.py`（新增端点）、`app/utils/auth.py`（新增密码工具）
- **前端新增**：`pages/login/` 登录页
- **前端修改**：`app.config.ts`（路由）、`store/userStore.ts`（新增 action）、`services/user.ts`（新增 API）、`pages/profile/index.tsx`（退出登录按钮、登录入口）
