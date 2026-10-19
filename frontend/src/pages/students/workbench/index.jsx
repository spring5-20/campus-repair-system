import { Button, Card, Col, Row, Space, Tag, Typography } from 'antd';
import { CheckOutlined, PlusOutlined } from '@ant-design/icons';

/**
 * 学生端 — 报修首页
 * 布局与视觉按原型还原：欢迎区 + 四步流程 + 统计卡片 + 最近工单 + 快捷操作
 * 数据均为示例占位，后期可替换为接口数据
 */

// 示例数据（后期替换为接口返回）
const STATS = [
  { title: '全部工单', value: 7, caption: '仅显示本人提交' },
  { title: '待接单', value: 2, caption: '等待维修人员处理' },
  { title: '处理中', value: 2, caption: '维修人员正在处理' },
  { title: '待确认', value: 1, caption: '请验收维修结果' },
];

const FLOW_STEPS = [
  { title: '学生报修', description: '提交工单' },
  { title: '维修接单', description: '认领或指派' },
  { title: '完成维修', description: '提交处理结果' },
  { title: '学生确认', description: '关闭工单' },
];

const RECENT_ORDERS = [
  { id: 1, no: 'REP-0001', title: '实训室投影仪无法显示', category: '教学设备', location: '实训楼 A-302', priority: '紧急', priorityColor: '#c2402f', status: '待接单', owner: '未指派' },
  { id: 2, no: 'REP-0002', title: '宿舍楼三层无线网络不稳定', category: '网络故障', location: '3 号宿舍楼 3F', priority: '普通', priorityColor: '#b8860b', status: '处理中', owner: '维修人员' },
  { id: 3, no: 'REP-0003', title: '图书馆二楼饮水机漏水', category: '水电设施', location: '图书馆 2F 东侧', priority: '紧急', priorityColor: '#c2402f', status: '待确认', owner: '维修人员' },
  { id: 4, no: 'REP-0004', title: '教学楼一楼照明灯闪烁', category: '水电设施', location: '教学楼 B-1F', priority: '较低', priorityColor: '#6b716b', status: '已关闭', owner: '维修人员' },
];

// 状态标签配色（与主色墨绿/工牌金体系一致）
const STATUS_TAG = {
  待接单: { color: '#f4ede0', text: '#8a6116' },
  处理中: { color: '#e3ecf7', text: '#2f5a8f' },
  待确认: { color: '#e2efe7', text: '#2f6b4f' },
  已关闭: { color: '#e9eae6', text: '#6b716b' },
};

const StatusPill = ({ status }) => {
  const meta = STATUS_TAG[status] || STATUS_TAG['已关闭'];
  return (
    <Tag style={{ borderRadius: 999, border: 'none', padding: '2px 12px', background: meta.color, color: meta.text, fontWeight: 600 }}>
      {status}
    </Tag>
  );
};

export const RepairWorkbenchPage = () => {
  return (
    <div style={{ margin: -24, padding: 24, background: '#eef1ee' }}>
      {/* 欢迎区 */}
      <Row justify="space-between" align="top" gutter={[16, 16]}>
        <Col>
          <Tag style={{ borderRadius: 6, background: '#f4ede0', color: '#8a6116', border: 'none', fontWeight: 600 }}>
            学生端
          </Tag>
          <Typography.Title level={2} style={{ margin: '10px 0 4px', color: '#16352c', fontWeight: 700 }}>
            上午好，学生用户
          </Typography.Title>
          <Typography.Text type="secondary">提交故障并随时跟踪维修进度。</Typography.Text>
        </Col>
        <Col>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            style={{ background: '#16352c', height: 44, paddingInline: 24, fontWeight: 600, borderRadius: 10 }}
          >
            提交报修
          </Button>
        </Col>
      </Row>

      {/* 四步流程引导 */}
      <Card bordered={false} style={{ marginTop: 20, borderRadius: 12 }}>
        <Row align="center">
          {FLOW_STEPS.map((step, index) => (
            <Col flex="auto" key={step.title} style={{ display: 'flex', alignItems: 'center' }}>
              <Space align="start" size={12}>
                <span
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    background: index === 0 ? '#16352c' : '#e9eae6',
                    color: index === 0 ? '#f0d88d' : '#6b716b',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: 13,
                    flexShrink: 0,
                  }}
                >
                  {index + 1}
                </span>
                <span>
                  <Typography.Text strong style={{ display: 'block', color: '#16352c', fontSize: 14 }}>
                    {step.title}
                  </Typography.Text>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {step.description}
                  </Typography.Text>
                </span>
              </Space>
              {index < FLOW_STEPS.length - 1 && (
                <span style={{ flex: 1, height: 1, background: '#dde1dc', margin: '0 16px', minWidth: 32 }} />
              )}
            </Col>
          ))}
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {STATS.map((item) => (
          <Col xs={12} xl={6} key={item.title}>
            <Card bordered={false} style={{ borderRadius: 12, height: '100%' }}>
              <Typography.Text type="secondary">{item.title}</Typography.Text>
              <div style={{ fontSize: 40, fontWeight: 700, color: '#16352c', lineHeight: 1.3 }}>{item.value}</div>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>{item.caption}</Typography.Text>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 最近工单 + 快捷操作 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} xl={16}>
          <Card
            bordered={false}
            title={<span style={{ color: '#16352c' }}>最近工单</span>}
            extra={<a style={{ color: '#16352c', fontWeight: 600 }}>查看全部</a>}
            styles={{ body: { paddingTop: 8 } }}
            style={{ borderRadius: 12, height: '100%' }}
          >
            {RECENT_ORDERS.map((order, index) => (
              <div
                key={order.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  padding: '14px 4px',
                  borderBottom: index < RECENT_ORDERS.length - 1 ? '1px solid #f0f1ee' : 'none',
                }}
              >
                <div style={{ flex: '0 0 34%', minWidth: 0 }}>
                  <Typography.Text strong style={{ display: 'block', color: '#16352c', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {order.title}
                  </Typography.Text>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {order.no} · {order.category}
                  </Typography.Text>
                </div>
                <div style={{ flex: '0 0 22%', color: '#4f5652' }}>{order.location}</div>
                <div style={{ flex: '0 0 12%', color: order.priorityColor, fontWeight: 600 }}>{order.priority}</div>
                <div style={{ flex: '0 0 16%' }}>
                  <StatusPill status={order.status} />
                </div>
                <div style={{ flex: 1, color: '#4f5652' }}>{order.owner}</div>
              </div>
            ))}
          </Card>
        </Col>

        <Col xs={24} xl={8}>
          <Card bordered={false} title={<span style={{ color: '#16352c' }}>快捷操作</span>} style={{ borderRadius: 12, height: '100%' }}>
            <div
              style={{
                background: '#eaf1ec',
                borderRadius: 10,
                padding: 16,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                cursor: 'pointer',
              }}
            >
              <span
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  background: '#16352c',
                  color: '#fff',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <PlusOutlined />
              </span>
              <span>
                <Typography.Text strong style={{ display: 'block', color: '#16352c' }}>提交新报修</Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>填写位置、分类和现场照片</Typography.Text>
              </span>
            </div>

            <div
              style={{
                background: '#eaf1ec',
                borderRadius: 10,
                padding: 16,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                marginTop: 12,
                cursor: 'pointer',
              }}
            >
              <span
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  background: '#16352c',
                  color: '#f0d88d',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <CheckOutlined />
              </span>
              <span>
                <Typography.Text strong style={{ display: 'block', color: '#16352c' }}>验收维修结果</Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>1 个工单等待确认</Typography.Text>
              </span>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};