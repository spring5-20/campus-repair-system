import { useCallback, useEffect, useState } from 'react';
import {
  App,
  Button,
  Card,
  Col,
  Descriptions,
  Empty,
  Input,
  List,
  Modal,
  Row,
  Select,
  Space,
  Spin,
  Tag,
  Timeline,
  Typography,
} from 'antd';
import { ArrowLeftOutlined, SendOutlined, UserAddOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import {
  addTicketComment,
  assignTicket,
  changeTicketStatus,
  getTicketDetail,
  getUserList,
} from '@/api/tickets';
import { ACTION_MAP, PRIORITY_MAP, STATUS_MAP } from '@/constants/ticket';
import { formatDateTime } from '@/utils/format';

/**
 * 管理端 — 工单详情
 * 基础信息 + 管理操作（指派/取消/完成维修/关闭）+ 留言 + 操作日志时间线
 */
export const AdminTicketDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { message, modal } = App.useApp();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [comment, setComment] = useState('');

  // 指派弹窗状态
  const [assignOpen, setAssignOpen] = useState(false);
  const [techUsers, setTechUsers] = useState([]);
  const [assigneeId, setAssigneeId] = useState(null);
  const [usersLoading, setUsersLoading] = useState(false);

  const loadDetail = useCallback(() => {
    setLoading(true);
    getTicketDetail(id)
      .then((data) => setDetail(data))
      .catch((error) => {
        message.error(error?.message || '工单详情加载失败');
        setDetail(null);
      })
      .finally(() => setLoading(false));
  }, [id, message]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const openAssignModal = () => {
    setAssignOpen(true);
    setAssigneeId(null);
    setUsersLoading(true);
    getUserList('tech')
      .then((users) => setTechUsers(users))
      .catch((error) => message.error(error?.message || '维修人员列表加载失败'))
      .finally(() => setUsersLoading(false));
  };

  const handleAssign = async () => {
    if (!assigneeId) {
      message.warning('请选择维修人员');
      return;
    }
    setSubmitting(true);
    try {
      await assignTicket(id, assigneeId);
      message.success('指派成功');
      setAssignOpen(false);
      loadDetail();
    } catch (error) {
      message.error(error?.message || '指派失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusAction = (action, title, content) => {
    modal.confirm({
      title,
      content,
      okText: '确认',
      cancelText: '取消',
      centered: true,
      onOk: async () => {
        setSubmitting(true);
        try {
          await changeTicketStatus(id, action);
          message.success('操作成功');
          loadDetail();
        } catch (error) {
          message.error(error?.message || '操作失败');
        } finally {
          setSubmitting(false);
        }
      },
    });
  };

  const handleComment = async () => {
    const content = comment.trim();
    if (!content) {
      message.warning('留言内容不能为空');
      return;
    }
    setSubmitting(true);
    try {
      await addTicketComment(id, content);
      setComment('');
      message.success('留言成功');
      loadDetail();
    } catch (error) {
      message.error(error?.message || '留言失败');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!detail) {
    return (
      <Card bordered={false} style={{ borderRadius: 12 }}>
        <Empty description="工单不存在或无权查看">
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
            返回
          </Button>
        </Empty>
      </Card>
    );
  }

  const statusItem = STATUS_MAP[detail.status];
  const priorityItem = PRIORITY_MAP[detail.priority];

  const renderActions = () => {
    if (detail.status === 'PENDING') {
      return (
        <>
          <Button
            type="primary"
            block
            icon={<UserAddOutlined />}
            loading={submitting}
            onClick={openAssignModal}
            style={{ background: '#16352c' }}
          >
            指派
          </Button>
          <Button
            block
            danger
            style={{ marginTop: 12 }}
            loading={submitting}
            onClick={() =>
              handleStatusAction('CANCEL', '确认取消工单？', `工单 ${detail.ticketNo} 取消后不可恢复。`)
            }
          >
            取消工单
          </Button>
        </>
      );
    }
    if (detail.status === 'PROCESSING') {
      return (
        <Button
          type="primary"
          block
          loading={submitting}
          onClick={() =>
            handleStatusAction('RESOLVE', '确认完成维修？', `工单 ${detail.ticketNo} 将进入「待确认」状态。`)
          }
          style={{ background: '#16352c' }}
        >
          完成维修
        </Button>
      );
    }
    if (detail.status === 'RESOLVED') {
      return (
        <Button
          type="primary"
          block
          loading={submitting}
          onClick={() =>
            handleStatusAction('CLOSE', '确认关闭工单？', `工单 ${detail.ticketNo} 关闭后进入终态。`)
          }
          style={{ background: '#16352c' }}
        >
          关闭工单
        </Button>
      );
    }
    return <Typography.Text type="secondary">当前状态为终态，无可执行操作</Typography.Text>;
  };

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
          返回
        </Button>
        <Typography.Title level={3} style={{ margin: 0 }}>
          {detail.title}
        </Typography.Title>
        {statusItem && <Tag color={statusItem.color}>{statusItem.text}</Tag>}
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={16}>
          <Card bordered={false} title="工单信息" style={{ borderRadius: 12 }}>
            <Descriptions column={{ xs: 1, sm: 2 }} size="middle">
              <Descriptions.Item label="工单号">{detail.ticketNo}</Descriptions.Item>
              <Descriptions.Item label="优先级">
                {priorityItem ? <Tag color={priorityItem.color}>{priorityItem.text}</Tag> : detail.priority}
              </Descriptions.Item>
              <Descriptions.Item label="分类">{detail.category}</Descriptions.Item>
              <Descriptions.Item label="地点">{detail.location}</Descriptions.Item>
              <Descriptions.Item label="报修人">{detail.reporterName}</Descriptions.Item>
              <Descriptions.Item label="负责人">{detail.assigneeName || '未指派'}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{formatDateTime(detail.createdAt)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{formatDateTime(detail.updatedAt)}</Descriptions.Item>
            </Descriptions>
            <Typography.Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
              <Typography.Text strong>故障描述：</Typography.Text>
              <br />
              {detail.description}
            </Typography.Paragraph>
          </Card>

          <Card bordered={false} title="留言" style={{ borderRadius: 12, marginTop: 16 }}>
            <List
              dataSource={detail.comments || []}
              locale={{ emptyText: '暂无留言' }}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Typography.Text strong>{item.authorName}</Typography.Text>
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                          {formatDateTime(item.createdAt)}
                        </Typography.Text>
                      </Space>
                    }
                    description={item.content}
                  />
                </List.Item>
              )}
            />
            <Space.Compact style={{ width: '100%', marginTop: 12 }}>
              <Input.TextArea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="补充说明（去除首尾空格后 1-500 字）"
                autoSize={{ minRows: 2, maxRows: 4 }}
                maxLength={500}
                disabled={submitting}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                loading={submitting}
                onClick={handleComment}
                style={{ background: '#16352c', height: 'auto' }}
              >
                发送
              </Button>
            </Space.Compact>
          </Card>
        </Col>

        <Col xs={24} xl={8}>
          <Card bordered={false} title="管理操作" style={{ borderRadius: 12 }}>
            {renderActions()}
          </Card>

          <Card bordered={false} title="操作日志" style={{ borderRadius: 12, marginTop: 16 }}>
            <Timeline
              items={(detail.logs || []).map((log) => ({
                children: (
                  <div>
                    <Typography.Text strong>{ACTION_MAP[log.action] || log.action}</Typography.Text>
                    <Typography.Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
                      {log.actorName} · {formatDateTime(log.createdAt)}
                    </Typography.Text>
                    {log.detail && (
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                        {log.detail}
                      </Typography.Text>
                    )}
                  </div>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>

      <Modal
        title="指派工单"
        open={assignOpen}
        onOk={handleAssign}
        onCancel={() => setAssignOpen(false)}
        okText="确认指派"
        cancelText="取消"
        confirmLoading={submitting}
        centered
      >
        <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
          选择要指派的维修人员，指派后工单进入「处理中」。
        </Typography.Paragraph>
        <Select
          style={{ width: '100%' }}
          placeholder="请选择维修人员"
          loading={usersLoading}
          value={assigneeId}
          onChange={setAssigneeId}
          options={techUsers.map((user) => ({
            value: user.id,
            label: `${user.displayName}（${user.username}）`,
          }))}
        />
      </Modal>
    </div>
  );
};
