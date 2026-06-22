## 1. 依赖安装

- [x] 1.1 安装 `aiomysql` 和 `passlib[bcrypt]`（实际改用 `bcrypt` 直接调用）
- [x] 1.2 在 `requirements.txt` 中添加 `bcrypt>=4.0.0`

## 2. 数据库变更

- [x] 2.1 执行 ALTER TABLE 新增 `username` 和 `password_hash` 字段
- [x] 2.2 更新 `app/db/models/user.py` ORM 模型新增两个字段

## 3. 后端密码工具

- [x] 3.1 在 `app/utils/auth.py` 中新增 `hash_password()` 和 `verify_password()` 函数

## 4. 后端手动登录 API

- [x] 4.1 在 `app/models/user.py` 中新增 `ManualLoginRequest` 请求模型
- [x] 4.2 在 `app/services/user_service.py` 中新增 `manual_login_or_register()` 函数
- [x] 4.3 在 `app/api/v1/endpoints/user.py` 中新增 `POST /api/user/login/manual` 端点

## 5. 前端登录页

- [x] 5.1 新建 `pages/login/index.config.ts`
- [x] 5.2 新建 `pages/login/index.tsx` — 登录页 UI（用户名+密码输入、微信登录按钮）
- [x] 5.3 新建 `pages/login/index.scss` — 暖色调样式
- [x] 5.4 在 `app.config.ts` 中注册登录页路由

## 6. 前端服务层

- [x] 6.1 在 `services/user.ts` 中新增 `manualLogin()` API
- [x] 6.2 在 `store/userStore.ts` 中新增 `manualLogin` action

## 7. 个人中心修改

- [x] 7.1 修改 `pages/profile/index.tsx` — 未登录显示"去登录"按钮，已登录底部加"退出登录"
- [x] 7.2 修改 `pages/profile/index.scss` — 退出登录按钮样式

## 8. 重启验证

- [x] 8.1 重启后端，确认数据库连接成功（✅ 数据库连接成功）
- [x] 8.2 验证手动登录/注册接口正常（✅ 新用户注册 + 再次登录 + 错误密码）
- [x] 8.3 验证微信自动登录正常（✅ 原有 /api/user/login 正常）
- [x] 8.4 验证退出登录功能（✅ 清除 token，重新静默登录）
