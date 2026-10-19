/**
 * 内存版 dataProvider
 * - 使用 localStorage 持久化模拟数据，刷新页面后数据不丢失
 * - 实现了 react-admin 约定的 CRUD 方法（getList / getOne / getMany / create / update / delete 等）
 * - 如需对接真实后端，只需按同样的方法签名替换为 HTTP 请求即可（例如 ra-core 的 fetchUtils）
 */

const STORAGE_KEY = 'reac-admin-db-v1';

// 模拟网络延迟
const wait = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms));

// 深拷贝，避免直接修改内部数据
const clone = (value) => JSON.parse(JSON.stringify(value));

const now = () => new Date().toISOString();

// 初始种子数据
const seed = {
  posts: [
    {
      id: 1,
      title: 'React-Admin 快速上手指南',
      content:
        'React-admin 是基于 React 的 BFF（后端即前端）管理框架，本指南介绍如何结合 Ant Design 搭建后台。',
      status: 'published',
      category: 'tech',
      author_id: 1,
      views: 1280,
      published_at: '2026-08-01T10:00:00.000Z',
      created_at: '2026-07-28T08:30:00.000Z',
      updated_at: '2026-08-01T10:00:00.000Z',
    },
    {
      id: 2,
      title: 'Ant Design 5 组件最佳实践',
      content:
        '从布局、表格到表单，总结 Ant Design 5 在后台管理场景中的常见用法与踩坑经验。',
      status: 'published',
      category: 'tech',
      author_id: 2,
      views: 956,
      published_at: '2026-08-10T09:00:00.000Z',
      created_at: '2026-08-05T02:20:00.000Z',
      updated_at: '2026-08-10T09:00:00.000Z',
    },
    {
      id: 3,
      title: '八月运营月报',
      content: '本月平台新增用户 320 人，文章发布量较上月提升 18%，整体留存表现良好。',
      status: 'published',
      category: 'news',
      author_id: 1,
      views: 642,
      published_at: '2026-08-20T06:00:00.000Z',
      created_at: '2026-08-18T12:00:00.000Z',
      updated_at: '2026-08-20T06:00:00.000Z',
    },
    {
      id: 4,
      title: 'Vite 8 新特性一览',
      content: 'Vite 8 带来了更快的依赖预构建与更完善的环境变量支持，值得升级体验。',
      status: 'draft',
      category: 'tech',
      author_id: 2,
      views: 0,
      published_at: null,
      created_at: '2026-08-25T03:00:00.000Z',
      updated_at: '2026-08-25T03:00:00.000Z',
    },
    {
      id: 5,
      title: '团队团建活动安排',
      content: '本周五下午组织团队户外拓展，请大家提前安排好工作并准时参加。',
      status: 'draft',
      category: 'life',
      author_id: 2,
      views: 0,
      published_at: null,
      created_at: '2026-08-28T07:40:00.000Z',
      updated_at: '2026-08-28T07:40:00.000Z',
    },
    {
      id: 6,
      title: '后台管理系统重构计划',
      content: '计划在 Q4 完成核心模块迁移到 ra-core + Ant Design 架构，涉及权限、列表与表单。',
      status: 'archived',
      category: 'news',
      author_id: 1,
      views: 388,
      published_at: '2026-07-15T04:00:00.000Z',
      created_at: '2026-07-10T09:00:00.000Z',
      updated_at: '2026-07-15T04:00:00.000Z',
    },
  ],
  users: [
    {
      id: 1,
      username: 'admin',
      name: '系统管理员',
      email: 'admin@example.com',
      role: 'admin',
      status: 'active',
      created_at: '2026-01-01T00:00:00.000Z',
    },
    {
      id: 2,
      username: 'editor',
      name: '内容编辑',
      email: 'editor@example.com',
      role: 'editor',
      status: 'active',
      created_at: '2026-01-15T00:00:00.000Z',
    },
    {
      id: 3,
      username: 'zhangwei',
      name: '张伟',
      email: 'zhangwei@example.com',
      role: 'editor',
      status: 'active',
      created_at: '2026-03-02T00:00:00.000Z',
    },
    {
      id: 4,
      username: 'lina',
      name: '李娜',
      email: 'lina@example.com',
      role: 'viewer',
      status: 'disabled',
      created_at: '2026-04-18T00:00:00.000Z',
    },
    {
      id: 5,
      username: 'wangfang',
      name: '王芳',
      email: 'wangfang@example.com',
      role: 'viewer',
      status: 'active',
      created_at: '2026-06-20T00:00:00.000Z',
    },
  ],
};

function loadDb() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (error) {
    // localStorage 不可用时忽略，直接使用种子数据
  }
  return clone(seed);
}

function saveDb(db) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
  } catch (error) {
    // 存储失败不影响本次会话内操作
  }
}

// 通用过滤：q 为全文搜索，其余字段做精确匹配
function applyFilters(resource, rows, filter = {}) {
  const { q, ...rest } = filter;
  let result = rows;

  if (q) {
    const keyword = String(q).toLowerCase();
    result = result.filter((row) =>
      Object.values(row).some((value) => {
        if (value === null || value === undefined) return false;
        return String(value).toLowerCase().includes(keyword);
      }),
    );
  }

  for (const [key, value] of Object.entries(rest)) {
    if (value === undefined || value === null || value === '') continue;
    result = result.filter((row) => row[key] === value);
  }

  return result;
}

function compareValues(a, b) {
  if (a === b) return 0;
  if (a === null || a === undefined) return -1;
  if (b === null || b === undefined) return 1;
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b), 'zh-CN');
}

export const dataProvider = {
  async getList(resource, params = {}) {
    await wait();
    const db = loadDb();
    const rows = db[resource] || [];

    const { pagination = { page: 1, perPage: 10 }, sort = { field: 'id', order: 'DESC' }, filter = {} } = params;

    let result = applyFilters(resource, rows, filter);

    const { field, order } = sort;
    result = [...result].sort((a, b) => {
      const cmp = compareValues(a[field], b[field]);
      return order === 'ASC' ? cmp : -cmp;
    });

    const total = result.length;
    const start = (pagination.page - 1) * pagination.perPage;
    const pageRows = result.slice(start, start + pagination.perPage);

    return { data: clone(pageRows), total };
  },

  async getOne(resource, { id }) {
    await wait();
    const db = loadDb();
    const row = (db[resource] || []).find((item) => item.id === id);
    if (!row) {
      return Promise.reject(new Error(`资源 ${resource} 中不存在 id=${id} 的记录`));
    }
    return { data: clone(row) };
  },

  async getMany(resource, { ids }) {
    await wait();
    const db = loadDb();
    const rows = (db[resource] || []).filter((item) => ids.includes(item.id));
    return { data: clone(rows) };
  },

  async create(resource, { data }) {
    await wait();
    const db = loadDb();
    const rows = db[resource] || [];
    const id = rows.reduce((max, item) => Math.max(max, item.id), 0) + 1;
    const record = {
      id,
      ...data,
      created_at: data.created_at || now(),
      updated_at: now(),
    };
    db[resource] = [...rows, record];
    saveDb(db);
    return { data: clone(record) };
  },

  async update(resource, { id, data }) {
    await wait();
    const db = loadDb();
    const rows = db[resource] || [];
    const index = rows.findIndex((item) => item.id === id);
    if (index === -1) {
      return Promise.reject(new Error(`资源 ${resource} 中不存在 id=${id} 的记录`));
    }
    const record = {
      ...rows[index],
      ...data,
      id,
      updated_at: now(),
    };
    db[resource] = [...rows.slice(0, index), record, ...rows.slice(index + 1)];
    saveDb(db);
    return { data: clone(record) };
  },

  async updateMany(resource, { ids, data }) {
    await wait();
    const db = loadDb();
    const rows = db[resource] || [];
    const updatedIds = [];
    db[resource] = rows.map((item) => {
      if (!ids.includes(item.id)) return item;
      updatedIds.push(item.id);
      return { ...item, ...data, id: item.id, updated_at: now() };
    });
    saveDb(db);
    return { data: updatedIds };
  },

  async delete(resource, { id }) {
    await wait();
    const db = loadDb();
    const rows = db[resource] || [];
    const index = rows.findIndex((item) => item.id === id);
    if (index === -1) {
      return Promise.reject(new Error(`资源 ${resource} 中不存在 id=${id} 的记录`));
    }
    const [removed] = rows.splice(index, 1);
    db[resource] = rows;
    saveDb(db);
    return { data: clone(removed) };
  },

  async deleteMany(resource, { ids }) {
    await wait();
    const db = loadDb();
    const rows = db[resource] || [];
    const remaining = rows.filter((item) => !ids.includes(item.id));
    db[resource] = remaining;
    saveDb(db);
    return { data: ids };
  },
};
