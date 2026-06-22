## Context

当前 MySQL 8.0 已安装运行，`yuairundeep` 数据库已存在且含 4 张表和 8 条用户数据。但 `aiomysql` 未安装，导致后端启动时 `init_db()` 失败，所有依赖 `get_session()` 的接口返回 500。

用户系统目前仅支持微信自动登录（deviceId 模式），缺少手动登录/注册功能。

## Goals / Non-Goals

**Goals:**
- 修复数据库连接（安装 aiomysql）
- users 表新增 username + password_hash 字段，支持用户名密码登录
- 新增手动登录 API（未注册自动注册）
- 前端新增登录页，支持两种登录方式
- 个人中心新增退出登录按钮

**Non-Goals:**
- 不修改微信登录现有逻辑
- 不新增注册页面（自动注册）

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 密码哈希 | bcrypt (passlib) | 行业标准，不可逆加密 |
| 自动注册 | 登录时 username 不存在则自动创建 | 简化用户体验，省掉注册页 |
| 用户名+密码 | 各6位固定长度 | 用户已确认 |
| 微信登录入口 | 走现有 `Taro.login()` + `POST /api/user/login` | 复用已有逻辑，不改后端 |
| 退出登录 | 清除本地 token，刷新为未登录 | 简单可靠 |
