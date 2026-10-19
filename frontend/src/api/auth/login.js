import { request } from '@/api/client';

/**
 * 登录接口：POST /api/auth/login
 * 约定请求参数：{ username, password }
 * 约定返回：{
 *   code: 200,
 *   message: 'success',
 *   data: {
 *     token: 'xxx',
 *     user: {
 *       id: 1,
 *       username: 'admin',
 *       fullName: '系统管理员',
 *       role: 'admin'
 *     }
 *   }
 * }
 */
export const login = async (params) => {
  const response = await request({
    method: 'post',
    url: '/auth/login',
    data: params,
  });

  const payload = response?.data ?? response;
  const code = response?.code ?? payload?.code;

  if (code !== undefined && code !== 200 && code !== 0) {
    throw new Error(response?.message || payload?.message || '登录失败');
  }

  return response;
};

export default login;
