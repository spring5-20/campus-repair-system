import { Card, Col, Row, Statistic } from 'antd';

export const StatCards = ({ stats = [] }) => (
  <Row gutter={[16, 16]}>
    {stats.map((item) => (
      <Col xs={24} sm={12} lg={6} key={item.title}>
        <Card>
          <Statistic
            title={item.title}
            value={item.value ?? 0}
            prefix={<span style={{ color: item.color, marginRight: 8 }}>{item.icon}</span>}
          />
        </Card>
      </Col>
    ))}
  </Row>
);
