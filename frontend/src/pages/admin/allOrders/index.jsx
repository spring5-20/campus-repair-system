import { App, Button, Tag, Typography } from 'antd';
import { ProTable } from '@ant-design/pro-components';
import { useNavigate } from 'react-router-dom';
import { getTicketList } from '@/api/tickets';
import { CATEGORY_OPTIONS, PRIORITY_MAP, STATUS_MAP, statusOptions } from '@/constants/ticket';
import { formatDateTime } from '@/utils/format';

/**
 * 管理端 — 全部工单
 * 全量查询（管理员可见全部），支持关键词/状态/分类筛选与分页
 */
export const AdminAllOrdersPage = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();

  const columns = [
    {
      title: '关键词',
      dataIndex: 'keyword',
      hideInTable: true,
      search: {
        transform: (value) => ({ keyword: value }),
      },
    },
    { title: '工单号', dataIndex: 'ticketNo', width: 140, copyable: true, search: false },
    { title: '标题', dataIndex: 'title', ellipsis: true, search: false },
    { title: '地点', dataIndex: 'location', width: 170, ellipsis: true, search: false },
    {
      title: '分类',
      dataIndex: 'category',
      width: 110,
      search: {
        valueType: 'select',
        fieldProps: {
          options: CATEGORY_OPTIONS.map((item) => ({ value: item, label: item })),
          placeholder: '请选择分类',
        },
      },
    },
    { title: '报修人', dataIndex: 'reporterName', width: 100, search: false },
    { title: '负责人', dataIndex: 'assigneeName', width: 100, search: false, render: (value) => value || '未指派' },
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
    {
      title: '操作',
      valueType: 'option',
      width: 100,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => navigate(`/admin/tickets/${record.id}`)}>
          详情
        </Button>
      ),
    },
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
        全部工单
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
