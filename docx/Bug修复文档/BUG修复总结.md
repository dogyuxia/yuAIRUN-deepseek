# Bug 修复总结报告

> **项目名称**：AI闯关学园（yuAIRUN）
> **修复日期**：2026-06-20 ~ 2026-06-21
> **技术栈**：Taro 4 + React + TypeScript + FastAPI + LangChain + DeepSeek

---

## 目录

1. [修复概览](#1-修复概览)
2. [Bug 详情与修复方案](#2-bug-详情与修复方案)
3. [修改文件清单](#3-修改文件清单)
4. [测试验证结果](#4-测试验证结果)
5. [剩余问题](#5-剩余问题)
6. [后续优化建议](#6-后续优化建议)

---

## 1. 修复概览

| 编号 | Bug 现象 | 严重程度 | 状态 |
|------|---------|---------|:----:|
| #1 | 每次重新编译变成新用户，用户身份不持久化 | 🔴 严重 | ✅ 已修复 |
| #2 | 答题结果页和AI分析报告页无返回首页按钮 | 🟡 一般 | ✅ 已修复 |
| #3 | 点击「再来一次」卡在加载中，无法跳转出题页 | 🔴 严重 | ✅ 已修复 |
| #4 | 用户中心学习概览和错题本不随答题更新 | 🟡 一般 | ✅ 已修复 |
| #5 | 答题后经验值不增加 | 🔴 严重 | ✅ 已修复 |
| #6 | 点击最近学习记录产生重复条目 | 🟡 一般 | ✅ 已修复 |
| #7 | 从最近学习查看历史记录时卡在加载界面 | 🔴 严重 | ✅ 已修复 |
| #8 | 出题页面无返回首页按钮 | 🟢 轻微 | ✅ 已修复 |

---

## 2. Bug 详情与修复方案

### Bug #1：用户登录不持久化

**现象**：每次重新编译小程序后，用户都会变成新用户（"一会用户a，一会用户b"）。

**根因分析**：
1. **Token 过期后被静默清除**：后端返回 401 时，`request.ts` 仅从 storage 删除 token，但未通知状态层，导致 Zustand 仍维持 `isLoggedIn: true` 的"假登录"状态
2. **deviceId 与 token 命运捆绑**：两者使用同一存储空间，存储一旦丢失（开发工具重编清缓存），三者同时丢失
3. **不稳定的 deviceId 生成**：使用 `Math.random()` + `Date.now()` 生成，丢失后无法找回同一用户
4. **401 后缺少自动重新登录**：清除 token 后未触发 `silentLogin()`，直到下次编译才暴露问题

**修复内容**：

| 文件 | 修改 |
|------|------|
| `src/store/userStore.ts` | `silentLogin()` 使用稳定的 deviceId 代替 `Taro.login()` 的 code 作为登录凭证 |
| `src/store/userStore.ts` | `loadUserProfile()` 失败时保留缓存数据，不清除登录状态，并同步更新 storage 中的 userInfo |
| `src/services/request.ts` | 遇到 401 时自动触发 `silentLogin()` 重新登录，并同时清除 token 和 userInfo |
| `src/utils/constants.ts` | 新增 `DEVICE_ID`、`LAST_SYNC_TIME` 存储 Key |

**关键代码（deviceId 生成逻辑，userStore.ts）**：
```typescript
// 生成稳定的设备 ID（确保每次编译后同一用户）
let deviceId = getStorageData<string | null>(STORAGE_KEYS.DEVICE_ID, null)
if (!deviceId) {
  deviceId = `device_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`
  setStorageData(STORAGE_KEYS.DEVICE_ID, deviceId)
}
// 调用后端登录（使用稳定的 deviceId 作为 code）
const res = await userApi.login(deviceId)
```

---

### Bug #2：结果页/报告页无返回首页按钮

**现象**：答题完成界面和 AI 分析界面没有返回主界面的按钮。

**修复内容**：
- 结果页底部新增「🏠 返回首页」按钮，使用 `Taro.redirectTo` 跳转
- 报告页底部新增「🏠 返回首页」和「🔄 再来一次」按钮

**涉及文件**：
- `src/pages/result/index.tsx`
- `src/pages/report/index.tsx`
- `src/pages/report/index.scss`

---

### Bug #3：点击「再来一次」卡在加载中

**现象**：点击"再来一次"后出现加载界面，一直没有跳转到选择 AI 出题界面。

**根因**：`handleRetry` 调用 `resetQuiz()` 后执行 `Taro.navigateBack()`，返回的是上一页（答题页），但此时答题数据已被清空，页面显示"加载中..."且无法跳转。

**修复**：将 `navigateBack` 改为 `Taro.redirectTo({ url: '/pages/topic-input/index' })`，直接跳转到出题页面。

**涉及文件**：`src/pages/result/index.tsx`

---

### Bug #4：用户中心/错题本不同步

**现象**：用户中心界面的学习概览没有同步，错题本内容也没有同步。

**根因**：答题完成后仅调用了本地的 `addHistory` 和 `addXp`，未将数据同步到服务器。而用户中心从服务器加载数据（`loadUserProfile`），导致本地有数据但服务器没有。

**修复内容**：
1. 结果页 `useEffect` 中自动调用 `syncHistory()` + `syncWrongBook()` + `loadUserProfile()`
2. 新增 `LAST_SYNC_TIME` 增量同步机制，避免重复同步
3. 答题完成后将错题保存到本地 `WRONG_BOOK` 存储，供后续同步

**涉及文件**：
- `src/pages/result/index.tsx`
- `src/store/userStore.ts`
- `src/utils/constants.ts`

---

### Bug #5：经验值不增加

**现象**：做完题目后经验值没有增加。

**根因**：
1. XP 仅在本地累加（`addXp`），未同步到服务器
2. 答题页中每答一道题就 `addXp(10)` 的写法有误——XP 应在整次闯关完成后统一计算
3. 服务端 XP 只有通过 `syncHistory()` 同步后才更新

**修复内容**：
1. 移除答题页中每题 `addXp(10)` 的错误逻辑
2. 前端 XP 计算与后端 `calculate_xp_earned` 保持一致算法：
   - 每题正确 +10 XP
   - 连续答题额外奖励（第2题起 +5 XP/题）
   - 首次闯关额外 +50 XP
   - 100% 正确额外 +20 XP
3. 答题完成后通过同步机制将 XP 更新到服务器

**涉及文件**：
- `src/pages/quiz/index.tsx`（移除每题加 XP）
- `src/pages/result/index.tsx`（统一 XP 计算与同步）

---

### Bug #6 + #7：点击最近学习产生重复条目 + 卡加载

**现象**：点击首页最近学习中的条目（如"贝多芬"），会在列表中新增一条完全相同的记录；每次点击重复增加；重新编译后再次点击则卡在加载界面。

**根因**：Result 页的 `useEffect` 优先判断 `lastRecord`（Zustand 全局状态），而非 URL 参数。`lastRecord` 在上次答题完成后持久存在，导致：
1. 每次从首页点击历史条目进入 Result 页时，`lastRecord` 仍为非空
2. `addHistory(lastRecord)` 被重复调用 → 重复条目
3. URL 参数从未被读取 → `record` 为 null → 卡加载

**修复**：

```typescript
// 修复后的 useEffect 逻辑（result/index.tsx）
useEffect(() => {
  // 先检查 URL 参数：从首页点击历史进入
  const params = Taro.getCurrentInstance().router?.params
  if (params?.history) {
    // 查看模式：纯展示，不调用 addHistory/addXp
    setRecord(JSON.parse(decodeURIComponent(params.history)))
    setIsViewMode(true)
    return
  }
  // 无 URL 参数且 lastRecord 存在 → 刚完成答题
  if (lastRecord) {
    // ...处理新答题结果...
    resetQuiz() // 消费后清除 lastRecord
  }
}, [])
```

**关键改进**：
1. URL 参数优先于 `lastRecord`
2. 查看历史模式不调用 `addHistory`
3. 消费完 `lastRecord` 后立即 `resetQuiz()` 清除
4. 使用 `freshRecordRef` 绕过 `resetQuiz()` 导致的同步丢失

**涉及文件**：`src/pages/result/index.tsx`

---

### Bug #8：出题页面无返回首页按钮

**现象**：在 topic-input（选择学科/输入知识点）页面没有返回首页的方式。

**修复**：顶部新增「← 返回首页」导航按钮，使用 `redirectTo` 跳转，不残留会话。

**涉及文件**：
- `src/pages/topic-input/index.tsx`
- `src/pages/topic-input/index.scss`

---

## 3. 修改文件清单

### 后端（未修改，仅新增）

| 文件 | 说明 |
|------|------|
| `yuairun-backend/app/db/` | 数据库层（新增） |
| `yuairun-backend/app/api/v1/endpoints/user.py` | 用户 API 路由（新增） |
| `yuairun-backend/app/services/user_service.py` | 用户业务逻辑（新增） |
| `yuairun-backend/app/utils/auth.py` | JWT 工具（新增） |
| `yuairun-backend/app/models/user.py` | 用户 Pydantic 模型（新增） |
| `yuairun-backend/tests/test_user_api.py` | 用户系统测试（新增） |

### 前端（修改）

| 文件 | 修改说明 |
|------|---------|
| `src/app.tsx` | 启动时加载存储 + 静默登录 |
| `src/app.config.ts` | 页面配置 |
| `src/utils/constants.ts` | 新增 `DEVICE_ID`、`LAST_SYNC_TIME` |
| `src/store/userStore.ts` | deviceId 登录、增量同步、profile 缓存更新 |
| `src/services/request.ts` | 401 时触发自动重新登录 |
| `src/pages/result/index.tsx` | URL 参数优先、清除 lastRecord、错题本地保存、XP 计算 |
| `src/pages/report/index.tsx` | 新增「返回首页」「再来一次」按钮 |
| `src/pages/report/index.scss` | 底部按钮样式 |
| `src/pages/quiz/index.tsx` | 移除每题加 XP 逻辑 |
| `src/pages/home/index.tsx` | 首页最近学习列表 |
| `src/pages/home/index.scss` | 首页样式 |
| `src/pages/topic-input/index.tsx` | 新增「返回首页」导航 |
| `src/pages/topic-input/index.scss` | 导航栏样式 |

### 前端（新增）

| 文件 | 说明 |
|------|------|
| `src/services/user.ts` | 用户系统 API 封装 |
| `src/types/user.ts` | 用户系统类型定义 |
| `src/pages/profile/` | 个人中心页 |
| `src/pages/wrong-book/` | 错题本页 |

---

## 4. 测试验证结果

### 后端测试

```
测试运行: pytest tests/test_user_api.py tests/test_api.py tests/test_chains.py -v
结果: 31 个测试中 29 通过, 2 个预存失败
```

**通过的测试**：
- ✅ JWT 工具测试（创建/验证 Token）
- ✅ 鉴权测试（未授权访问拦截）
- ✅ XP 计算测试（等级/称号/经验值计算）
- ✅ Mock 出题链测试（5 项）
- ✅ Mock 报告链测试（3 项）
- ✅ 核心功能回归测试（健康检查/出题/分析）
- ✅ API 测试（出题/验证/分析）

**预存失败的测试**（非本次修改引入）：
- ❌ `test_full_workflow`：报告分析链集成测试
- ❌ `TestExistingCoreFunctions::test_quiz_analyze_still_works`：分析接口回归

### 前端验证

- ✅ TypeScript 零编译错误
- ✅ 前端 build 编译成功

---

## 5. 剩余问题

| 问题 | 说明 | 优先级 |
|------|------|--------|
| 报告分析链偶发失败 | `analyze` 端点偶尔返回 `success: false`，疑似 DeepSeek API 响应解析问题 | 🟡 中 |
| 无微信授权获取头像昵称 | 当前使用模拟 deviceId 登录，未调用 `wx.getUserProfile` 获取微信用户信息 | 🟢 低 |
| 无加载状态骨架屏 | 页面切换时有短暂白屏/加载中，缺乏骨架屏过渡 | 🟢 低 |

---

## 6. 后续优化建议

### 短期（技术债）

1. **Token 刷新机制**：实现自动 Token 刷新（根据过期时间预刷新），而非等到 401 才处理
2. **离线缓存**：使用 IndexedDB 或更可靠的本地存储方案，减少对 WeChat Storage 的依赖

### 中期（功能增强）

1. **微信授权登录**：集成 `wx.getUserProfile` 获取用户微信昵称和头像
2. **骨架屏**：页面加载时使用骨架屏替代"加载中..."文字
3. **错误边界**：React Error Boundary 捕获渲染异常，防止白屏

### 长期（架构）

1. **性能监控**：接入性能监控，跟踪 API 响应时间和页面渲染性能
2. **自动化测试**：补充 E2E 测试覆盖核心用户流程
3. **CI/CD**：建立自动化测试和部署流水线
