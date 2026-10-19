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
  Row,
  Space,
  Spin,
  Tag,
  Timeline,
  Typography,
} from 'antd';
import { ArrowLeftOutlined, SendOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useGetIdentity } from 'ra-core';
import { addTicketComment, changeTicketStatus, getTicketDetail } from '@/api/tickets';
import { ACTION_MAP, PRIORITY_MAP, STATUS_MAP } from '@/constants/ticket';
import { formatDateTime } from '@/utils/format';

/**
 * 维修端 — 工单详情
 * 基础信息 + 按状态/角色显示操作（接单/完成维修）+ 留言 + 操作日志时间线
 */
export const TechTicketDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { data: identity } = useGetIdentity();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [comment, setComment] = useState('');

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

  const handleAction = async (action) => {
    setSubmitting(true);
    try {
      await changeTicketStatus(id, action);
      message.success(action === 'ACCEPT' ? '接单成功' : '已完成维修');
      loadDetail();
    } catch (error) {
      message.error(error?.message || '操作失败');
    } finally {
      setSubmitting(false);
    }
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
  const canAccept = detail.status === 'PENDING';
  const canResolve = detail.status === 'PROCESSING' && detail.assigneeId === identity?.id;

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

          <Card
            bordered={false}
            title="留言"
            style={{ borderRadius: 12, marginTop: 16 }}
          >
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
          <Card bordered={false} title="操作" style={{ borderRadius: 12 }}>
            {canAccept && (
              <Button
                type="primary"
                block
                loading={submitting}
                onClick={() => handleAction('ACCEPT')}
                style={{ background: '#16352c' }}
              >
                接单
              </Button>
            )}
            {canResolve && (
              <Button
                type="primary"
                block
                loading={submitting}
                onClick={() => handleAction('RESOLVE')}
                style={{ background: '#16352c' }}
              >
                完成维修
              </Button>
            )}
            {!canAccept && !canResolve && (
              <Typography.Text type="secondary">当前状态没有可执行的操作</Typography.Text>
            )}
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
    </div>
  );
};
