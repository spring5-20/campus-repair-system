import { useEffect, useState } from 'react';
import { Button, Card, Col, Empty, Row, Spin, Statistic, Typography } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  FormOutlined,
  StopOutlined,
  ToolOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getTicketStatistics } from '@/api/tickets';

/**
 * 管理端 — 数据看板
 * 全局统计来自 /tickets/statistics（管理员可见全部工单），快捷入口跳转全部工单
 */
export const AdminDashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;
    getTicketStatistics()
      .then((data) => {
        if (active) {
          setStats(data);
          setLoadError('');
        }
      })
      .catch((error) => {
        if (active) setLoadError(error?.message || '统计加载失败');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const mainCards = stats
    ? [
        { title: '总工单', value: stats.total, icon: <FormOutlined />, color: '#16352c' },
        { title: '待接单', value: stats.pending, icon: <ClockCircleOutlined />, color: '#faad14' },
        { title: '处理中', value: stats.processing, icon: <ToolOutlined />, color: '#1677ff' },
        { title: '待确认', value: stats.resolved, icon: <CheckCircleOutlined />, color: '#722ed1' },
      ]
    : [];

  const extraCards = stats
    ? [
        { title: '已关闭', value: stats.closed, icon: <CheckCircleOutlined />, color: '#52c41a' },
        { title: '已取消', value: stats.cancelled, icon: <CloseCircleOutlined />, color: '#8c8c8c' },
        { title: '紧急工单', value: stats.highOpen, icon: <WarningOutlined />, color: '#ff4d4f' },
        { title: '关闭率', value: stats.closureRate, suffix: '%', icon: <StopOutlined />, color: '#16352c' },
      ]
    : [];

  return (
    <div>
      <Typography.Title level={3} style={{ marginBottom: 4 }}>
        数据看板
      </Typography.Title>
      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 20 }}>
        全局工单统计，口径来自后端统计接口，涵盖全部工单数据。
      </Typography.Text>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
        </div>
      ) : loadError ? (
        <Card bordered={false} style={{ borderRadius: 12 }}>
          <Empty description={loadError} />
        </Card>
      ) : (
        <>
          <Row gutter={[16, 16]}>
            {mainCards.map((item) => (
              <Col xs={12} xl={6} key={item.title}>
                <Card bordered={false} style={{ borderRadius: 12 }}>
                  <Statistic
                    title={item.title}
                    value={item.value}
                    valueStyle={{ fontWeight: 700, color: item.color }}
                    prefix={<span style={{ color: item.color, fontSize: 18 }}>{item.icon}</span>}
                  />
                </Card>
              </Col>
            ))}
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            {extraCards.map((item) => (
              <Col xs={12} xl={6} key={item.title}>
                <Card bordered={false} style={{ borderRadius: 12 }}>
                  <Statistic
                    title={item.title}
                    value={item.value}
                    suffix={item.suffix}
                    valueStyle={{ fontWeight: 700, color: item.color }}
                    prefix={<span style={{ color: item.color, fontSize: 18 }}>{item.icon}</span>}
                  />
                </Card>
              </Col>
            ))}
          </Row>

          <Card bordered={false} style={{ borderRadius: 12, marginTop: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <Typography.Text strong style={{ fontSize: 16, color: '#16352c' }}>
                  全部工单
                </Typography.Text>
                <Typography.Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                  全量查询、筛选、指派与异常处理
                </Typography.Text>
              </div>
              <Button
                type="primary"
                icon={<FormOutlined />}
                style={{ background: '#16352c' }}
                onClick={() => navigate('/admin/all-orders')}
              >
                查看全部工单
              </Button>
            </div>
          </Card>
        </>
      )}
    </div>
  );
};
