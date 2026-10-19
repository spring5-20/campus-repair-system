import dayjs from 'dayjs';

/** 格式化日期时间，空值显示占位符 */
export const formatDateTime = (value) =>
  value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '—';
