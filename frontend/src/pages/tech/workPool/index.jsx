import { useRef } from 'react';
import { App, Button, Tag, Typography } from 'antd';
import { ProTable } from '@ant-design/pro-components';
import { useNavigate } from 'react-router-dom';
import { changeTicketStatus, getTicketList } from '@/api/tickets';
import { CATEGORY_OPTIONS, PRIORITY_MAP, STATUS_MAP, statusOptions } from '@/constants/ticket';
import { formatDateTime } from '@/utils/format';

/**
 * 维修端 — 工单池（scope=pool）
 * PENDING 工单可接单（ACCEPT），接单成功后刷新列表
 */
export const WorkPoolPage = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const actionRef = useRef();

  const handleAccept = async (record) => {
    try {
      await changeTicketStatus(record.id, 'ACCEPT');
      message.success(`工单 ${record.ticketNo} 接单成功`);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error?.message || '接单失败');
    }
  };

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
      width: 140,
      render: (_, record) => (
        <>
          <Button type="link" size="small" onClick={() => navigate(`/tech/tickets/${record.id}`)}>
            详情
          </Button>
          {record.status === 'PENDING' && (
            <Button type="link" size="small" onClick={() => handleAccept(record)}>
              接单
            </Button>
          )}
        </>
      ),
    },
  ];

  const handleRequest = async (params) => {
    const { current = 1, pageSize = 10, keyword, status, category } = params;
    try {
      const data = await getTicketList({
        page: current,
        pageSize,
        scope: 'pool',
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
      message.error(error?.message || '工单池加载失败');
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
        actionRef={actionRef}
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
