/**
 * 本地认证 provider
 * - 使用 localStorage 保存登录状态
 * - 默认账号：
 *   admin / admin123（管理员）
 *   editor / editor123（编辑）
 */

const AUTH_KEY = 'reac-admin-auth';

const accounts = [
  { id: 1, username: 'student', password: 'student123', fullName: '学生用户', role: 'student' },
  { id: 2, username: 'repair', password: 'repair123', fullName: '维修人员', role: 'repair' },
  { id: 3, username: 'admin', password: 'admin123', fullName: '系统管理员', role: 'admin' },
];

// 去除密码字段，避免敏感信息写入 localStorage
function toIdentity(account) {
  const { password: _password, ...identity } = account;
  return identity;
}

export const authProvider = {
  async login({ username, password }) {
    const account = accounts.find(
      (item) => item.username === username && item.password === password,
    );
    if (!account) {
      return Promise.reject(new Error('用户名或密码错误'));
    }
    const identity = toIdentity(account);
    localStorage.setItem(AUTH_KEY, JSON.stringify(identity));
    return identity;
  },

  async logout() {
    localStorage.removeItem(AUTH_KEY);
  },

  async checkAuth() {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) {
      return Promise.reject(new Error('未登录'));
    }
  },

  async checkError(error) {
    const status = error?.status;
    if (status === 401 || status === 403) {
      localStorage.removeItem(AUTH_KEY);
      return Promise.reject(error);
    }
  },

  async getIdentity() {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) {
      return Promise.reject(new Error('未登录'));
    }
    return JSON.parse(raw);
  },

  async getPermissions() {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw).role : null;
  },
};
