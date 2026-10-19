/**
 * 轻量中文 i18n provider
 * - 主要服务 ra-core 内部使用的少量文案
 * - 页面自身文案直接在组件中书写中文
 */

const messages = {
  'ra.page.workbench': '仪表盘',
  'ra.action.create': '新建',
  'ra.action.edit': '编辑',
  'ra.action.show': '查看',
  'ra.action.delete': '删除',
  'ra.action.save': '保存',
  'ra.action.cancel': '取消',
  'ra.action.back': '返回',
  'ra.action.search': '搜索',
  'ra.action.logout': '退出登录',
  'ra.message.not_authorized': '您没有权限执行此操作',
  'ra.notification.created': '创建成功',
  'ra.notification.updated': '更新成功',
  'ra.notification.deleted': '删除成功',
  'ra.notification.http_error': '网络请求出错',
  'ra.validation.required': '必填字段',
};

function interpolate(message, params = {}) {
  return message.replace(/%{(\w+)}/g, (_, key) => params[key] ?? `%{${key}}`);
}

export const i18nProvider = {
  translate: (key, params) => interpolate(messages[key] || key, params),
  changeLocale: () => Promise.resolve(),
  getLocale: () => 'zh',
};
