import { request } from '@/api/client';

/**
 * 工单列表接口：GET /api/tickets（需要 Bearer Token）
 * 请求参数：
 * - page: 页码，从 1 开始
 * - pageSize: 每页条数，仅支持 10 / 20 / 50
 * - status: 工单状态（PENDING / PROCESSING / RESOLVED / CLOSED / CANCELLED）
 * - category: 故障分类
 * - keyword: 关键词（匹配工单号 / 标题等）
 * 返回：{ items, total, page, pageSize, pages }
 */
export const getTicketList = async (params = {}) => {
  const response = await request({
    method: 'get',
    url: '/tickets',
    params,
  });

  const payload = response?.data ?? response;
  const code = response?.code ?? payload?.code;

  if (code !== undefined && code !== 0 && code !== 200) {
    throw new Error(response?.message || payload?.message || '获取工单列表失败');
  }

  return payload;
};

/**
 * 工单统计：GET /api/tickets/statistics（按当前角色可见范围统计）
 * 返回：{ total, pending, processing, resolved, closed, cancelled, highOpen, closureRate }
 */
export const getTicketStatistics = async () => {
  const response = await request({
    method: 'get',
    url: '/tickets/statistics',
  });

  const payload = response?.data ?? response;
  const code = response?.code ?? payload?.code;

  if (code !== undefined && code !== 0 && code !== 200) {
    throw new Error(response?.message || payload?.message || '获取工单统计失败');
  }

  return payload;
};

/**
 * 工单详情：GET /api/tickets/{id}
 * 返回：TicketDetail（基础信息 + comments + logs）
 */
export const getTicketDetail = async (id) => {
  const response = await request({
    method: 'get',
    url: `/tickets/${id}`,
  });

  const payload = response?.data ?? response;
  const code = response?.code ?? payload?.code;

  if (code !== undefined && code !== 0 && code !== 200) {
    throw new Error(response?.message || payload?.message || '获取工单详情失败');
  }

  return payload;
};

/**
 * 工单状态变更：PATCH /api/tickets/{id}/status
 * action: ACCEPT（接单）/ RESOLVE（完成维修）/ CLOSE / CANCEL / ASSIGN
 */
export const changeTicketStatus = async (id, action) => {
  const response = await request({
    method: 'patch',
    url: `/tickets/${id}/status`,
    data: { action },
  });

  const payload = response?.data ?? response;
  const code = response?.code ?? payload?.code;

  if (code !== undefined && code !== 0 && code !== 200) {
    throw new Error(response?.message || payload?.message || '工单状态操作失败');
  }

  return payload;
};

/**
 * 新增工单留言：POST /api/tickets/{id}/comments
 * content 去除首尾空格后 1-500 字
 */
export const addTicketComment = async (id, content) => {
  const response = await request({
    method: 'post',
    url: `/tickets/${id}/comments`,
    data: { content },
  });

  const payload = response?.data ?? response;
  const code = response?.code ?? payload?.code;

  if (code !== undefined && code !== 0 && code !== 200) {
    throw new Error(response?.message || payload?.message || '留言失败');
  }

  return payload;
};

/**
 * 管理员指派工单：PATCH /api/tickets/{id}/assignee
 * assigneeId 为目标维修人员 ID；PENDING -> PROCESSING，写 ASSIGN 日志
 */
export const assignTicket = async (id, assigneeId) => {
  const response = await request({
    method: 'patch',
    url: `/tickets/${id}/assignee`,
    data: { assigneeId },
  });

  const payload = response?.data ?? response;
  const code = response?.code ?? payload?.code;

  if (code !== undefined && code !== 0 && code !== 200) {
    throw new Error(response?.message || payload?.message || '指派失败');
  }

  return payload;
};

/**
 * 用户列表：GET /api/users（管理端指派下拉等场景）
 * role: student / tech / admin，可选
 * 返回：User[]（{ id, username, displayName, role }）
 */
export const getUserList = async (role) => {
  const response = await request({
    method: 'get',
    url: '/users',
    params: role ? { role } : undefined,
  });

  const payload = response?.data ?? response;
  const code = response?.code ?? payload?.code;

  if (code !== undefined && code !== 0 && code !== 200) {
    throw new Error(response?.message || payload?.message || '获取用户列表失败');
  }

  return Array.isArray(payload) ? payload : [];
};

export default { getTicketList };
