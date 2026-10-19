/**
 * 工单公共常量：状态、优先级、操作动作的中文映射与标签颜色
 * 状态文案与 PRD 4.2 状态字典一致
 */

/** 工单状态：后端枚举 -> 中文文案与标签颜色 */
export const STATUS_MAP = {
  PENDING: { text: '待接单', color: 'gold' },
  PROCESSING: { text: '处理中', color: 'blue' },
  RESOLVED: { text: '待确认', color: 'purple' },
  CLOSED: { text: '已关闭', color: 'green' },
  CANCELLED: { text: '已取消', color: 'default' },
};

/** 优先级：后端枚举 -> 中文文案与标签颜色 */
export const PRIORITY_MAP = {
  LOW: { text: '低', color: 'default' },
  MEDIUM: { text: '中', color: 'gold' },
  HIGH: { text: '高', color: 'red' },
};

/** 操作日志动作 -> 中文文案 */
export const ACTION_MAP = {
  CREATE: '创建工单',
  ACCEPT: '接单',
  ASSIGN: '指派',
  RESOLVE: '完成维修',
  CLOSE: '验收关闭',
  CANCEL: '取消工单',
  COMMENT: '留言',
};

/** 故障分类选项（PRD 5.3） */
export const CATEGORY_OPTIONS = ['教学设备', '电脑设备', '网络故障', '水电设施'];

/** 状态下拉选项 */
export const statusOptions = Object.entries(STATUS_MAP).map(([value, item]) => ({
  value,
  label: item.text,
}));

/** 优先级下拉选项 */
export const priorityOptions = Object.entries(PRIORITY_MAP).map(([value, item]) => ({
  value,
  label: item.text,
}));
