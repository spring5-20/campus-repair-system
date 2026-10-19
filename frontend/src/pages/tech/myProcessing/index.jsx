import { useRef } from 'react';
import { App, Button, Tag, Typography } from 'antd';
import { ProTable } from '@ant-design/pro-components';
import { useNavigate } from 'react-router-dom';
import { useGetIdentity } from 'ra-core';
import { changeTicketStatus, getTicketList } from '@/api/tickets';
import { PRIORITY_MAP, STATUS_MAP, statusOptions } from '@/constants/ticket';
import { formatDateTime } from '@/utils/format';

/**
 * 维修端 — 我的处理中（scope=mine）
 * 展示指派/认领给本人的工单；PROCESSING 且负责人为本人时可完成维修（RESOLVE）
 */
export const MyProcessingPage = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const actionRef = useRef();
  const { data: identity } = useGetIdentity();
  const currentUserId = identity?.id;

  const handleResolve = (record) => {
    modal.confirm({
      title: '确认完成维修？',
      content: `工单 ${record.ticketNo} 完成后将进入「待确认」状态，等待学生验收。`,
      okText: '确认完成',
      cancelText: '取消',
      centered: true,
      onOk: async () => {
        try {
          await changeTicketStatus(record.id, 'RESOLVE');
          message.success(`工单 ${record.ticketNo} 已完成维修`);
          actionRef.current?.reload();
        } catch (error) {
          message.error(error?.message || '操作失败');
        }
      },
    });
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
    { title: '分类', dataIndex: 'category', width: 110, search: false },
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
      width: 160,
      render: (_, record) => (
        <>
          <Button type="link" size="small" onClick={() => navigate(`/tech/tickets/${record.id}`)}>
            详情
          </Button>
          {record.status === 'PROCESSING' && record.assigneeId === currentUserId && (
            <Button type="link" size="small" onClick={() => handleResolve(record)}>
              完成维修
            </Button>
          )}
        </>
      ),
    },
  ];

  const handleRequest = async (params) => {
    const { current = 1, pageSize = 10, keyword, status } = params;
    try {
      const data = await getTicketList({
        page: current,
        pageSize,
        scope: 'mine',
        keyword: keyword || undefined,
        status: status || undefined,
      });
      return {
        data: data?.items || [],
        total: data?.total || 0,
        success: true,
      };
    } catch (error) {
      message.error(error?.message || '列表加载失败');
      return { data: [], total: 0, success: false };
    }
  };

  return (
    <div>
      <Typography.Title level={3} style={{ marginBottom: 20 }}>
        我的处理中
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
