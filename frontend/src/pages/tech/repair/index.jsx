
import { useEffect, useState } from 'react';
import { Button, Card, Col, Empty, Row, Spin, Statistic, Typography } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  FormOutlined,
  ToolOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getTicketStatistics } from '@/api/tickets';

/**
 * 维修端 — 维修工作台
 * 统计卡片来自 /tickets/statistics（按维修角色可见范围），快捷入口跳转工单池与我的处理中
 */
export const RepairPage = () => {
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

  const cards = stats
    ? [
        { title: '待接单', value: stats.pending, icon: <ClockCircleOutlined />, color: '#faad14' },
        { title: '处理中', value: stats.processing, icon: <ToolOutlined />, color: '#1677ff' },
        { title: '待确认', value: stats.resolved, icon: <CheckCircleOutlined />, color: '#722ed1' },
        { title: '已关闭', value: stats.closed, icon: <CheckCircleOutlined />, color: '#52c41a' },
      ]
    : [];

  const extraStats = stats
    ? [
        { title: '紧急工单', value: stats.highOpen, icon: <WarningOutlined />, color: '#ff4d4f' },
        { title: '关闭率', value: stats.closureRate, suffix: '%', icon: <CheckCircleOutlined />, color: '#16352c' },
      ]
    : [];

  return (
    <div>
      <Typography.Title level={3} style={{ marginBottom: 4 }}>
        维修工作台
      </Typography.Title>
      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 20 }}>
        查看工单池与本人任务的实时统计，及时接单和处理。
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
            {cards.map((item) => (
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
            {extraStats.map((item) => (
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

          <Row gutter={[16, 16]} style={{ marginTop: 20 }}>
            <Col xs={24} lg={12}>
              <Card bordered={false} style={{ borderRadius: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <Typography.Text strong style={{ fontSize: 16, color: '#16352c' }}>
                      工单池
                    </Typography.Text>
                    <Typography.Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                      浏览待接单的报修工单并认领
                    </Typography.Text>
                  </div>
                  <Button
                    type="primary"
                    icon={<FormOutlined />}
                    style={{ background: '#16352c' }}
                    onClick={() => navigate('/tech/workPool')}
                  >
                    去工单池
                  </Button>
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card bordered={false} style={{ borderRadius: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <Typography.Text strong style={{ fontSize: 16, color: '#16352c' }}>
                      我的处理中
                    </Typography.Text>
                    <Typography.Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                      处理指派或认领给本人的工单
                    </Typography.Text>
                  </div>
                  <Button
                    type="primary"
                    icon={<ToolOutlined />}
                    style={{ background: '#16352c' }}
                    onClick={() => navigate('/tech/myProcessing')}
                  >
                    去处理中
                  </Button>
                </div>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};
