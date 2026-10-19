import { App, Tag, Typography } from 'antd';
import { ProTable } from '@ant-design/pro-components';
import { getTicketList } from '@/api/tickets';
import { formatDateTime } from '@/utils/format';

// 工单状态：后端枚举 -> 中文文案与标签颜色
const STATUS_MAP = {
  PENDING: { text: '待分派', color: 'gold' },
  PROCESSING: { text: '处理中', color: 'blue' },
  RESOLVED: { text: '待验收', color: 'purple' },
  CLOSED: { text: '已完成', color: 'green' },
  CANCELLED: { text: '已取消', color: 'default' },
};

// 优先级：后端枚举 -> 中文文案与标签颜色
const PRIORITY_MAP = {
  LOW: { text: '低', color: 'default' },
  MEDIUM: { text: '中', color: 'gold' },
  HIGH: { text: '高', color: 'red' },
};

const statusOptions = Object.entries(STATUS_MAP).map(([value, item]) => ({
  value,
  label: item.text,
}));

/**
 * 工单池列表页：通过 getTicketList 接口拉取后端工单数据
 */
export const RepairOrdersPage = () => {
  const { message } = App.useApp();

  const columns = [
    // 隐藏列：仅作为查询表单中的「关键词」搜索框，提交时转换为 keyword 参数
    {
      title: '关键词',
      dataIndex: 'keyword',
      hideInTable: true,
      search: {
        transform: (value) => ({ keyword: value }),
      },
    },
    { title: '工单号', dataIndex: 'ticketNo', width: 150, copyable: true, search: false },
    { title: '标题', dataIndex: 'title', ellipsis: true, search: false },
    { title: '地点', dataIndex: 'location', width: 170, ellipsis: true, search: false },
    {
      title: '分类',
      dataIndex: 'category',
      width: 110,
      search: {
        valueType: 'text',
      },
    },
    { title: '报修人', dataIndex: 'reporterName', width: 110, search: false },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 90,
      search: false,
      render: (value) => {
        const item = PRIORITY_MAP[value];
        return item ? <Tag color={item.color}>{item.text}</Tag> : value || '—';
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (value) => {
        const item = STATUS_MAP[value];
        return item ? <Tag color={item.color}>{item.text}</Tag> : value || '—';
      },
      search: {
        valueType: 'select',
        fieldProps: {
          options: statusOptions,
          placeholder: '请选择状态',
        },
      },
    },
    { title: '创建时间', dataIndex: 'createdAt', width: 170, search: false, render: formatDateTime },
  ];

  const handleRequest = async (params) => {
    const { current = 1, pageSize = 10, keyword, status, category } = params;
    try {
      const data = await getTicketList({
        page: current,
        pageSize,
        keyword: keyword || undefined,
        status: status || undefined,
        category: category || undefined,
      });
      return {
        data: data?.items || [],
        total: data?.total || 0,
        success: true,
      };
    } catch (error) {
      message.error(error?.message || '工单列表加载失败');
      return { data: [], total: 0, success: false };
    }
  };

  return (
    <div>
      <Typography.Title level={3} style={{ marginBottom: 20 }}>
        工单池
      </Typography.Title>

      <ProTable
        rowKey="id"
        columns={columns}
        request={handleRequest}
        search={{
          labelWidth: 'auto',
        }}
        pagination={{
          pageSize: 10,
          pageSizeOptions: [10, 20, 50],
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
        style={{ borderRadius: 12 }}
      />
    </div>
  );
};
