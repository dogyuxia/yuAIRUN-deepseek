/** 用户系统 API 封装 */
import { request } from './request'
import type {
  LoginResponse,
  ProfileResponse,
  HistoryListResponse,
  WrongBookResponse,
  SyncResponse,
  MessageResponse,
} from '../types/user'

/** 手动登录（用户名+密码，未注册自动创建） */
export async function manualLogin(
  username: string,
  password: string,
): Promise<LoginResponse> {
  return request<LoginResponse>({
    url: '/api/user/login/manual',
    method: 'POST',
    data: { username, password },
  })
}

/** 微信静默登录 */
export async function login(
  code: string,
  nickname?: string,
  avatarUrl?: string,
): Promise<LoginResponse> {
  return request<LoginResponse>({
    url: '/api/user/login',
    method: 'POST',
    data: { code, nickname, avatarUrl },
  })
}

/** 获取用户个人信息 + 统计 */
export async function getProfile(): Promise<ProfileResponse> {
  return request<ProfileResponse>({
    url: '/api/user/profile',
    method: 'GET',
  })
}

/** 更新用户信息 */
export async function updateProfile(nickname: string): Promise<ProfileResponse> {
  return request<ProfileResponse>({
    url: '/api/user/profile',
    method: 'PUT',
    data: { nickname },
  })
}

/** 分页获取闯关历史 */
export async function getHistory(
  page = 1,
  pageSize = 20,
): Promise<HistoryListResponse> {
  return request<HistoryListResponse>({
    url: `/api/user/history?page=${page}&pageSize=${pageSize}`,
    method: 'GET',
  })
}

/** 批量同步本地闯关记录 */
export async function syncHistory(
  records: unknown[],
): Promise<SyncResponse> {
  return request<SyncResponse>({
    url: '/api/user/history/sync',
    method: 'POST',
    data: { records },
    timeout: 30000,
  })
}

/** 分页获取错题本 */
export async function getWrongBook(
  page = 1,
  pageSize = 20,
  subject?: string,
): Promise<WrongBookResponse> {
  let url = `/api/user/wrong-book?page=${page}&pageSize=${pageSize}`
  if (subject) {
    url += `&subject=${encodeURIComponent(subject)}`
  }
  return request<WrongBookResponse>({ url, method: 'GET' })
}

/** 批量同步本地错题 */
export async function syncWrongBook(
  items: unknown[],
): Promise<SyncResponse> {
  return request<SyncResponse>({
    url: '/api/user/wrong-book/sync',
    method: 'POST',
    data: { items },
  })
}

/** 标记错题为已掌握 */
export async function markWrongMastered(
  wrongId: string,
): Promise<MessageResponse> {
  return request<MessageResponse>({
    url: `/api/user/wrong-book/${wrongId}/master`,
    method: 'PUT',
  })
}

/** 从错题本删除 */
export async function deleteWrongBook(
  wrongId: string,
): Promise<MessageResponse> {
  return request<MessageResponse>({
    url: `/api/user/wrong-book/${wrongId}`,
    method: 'DELETE',
  })
}
