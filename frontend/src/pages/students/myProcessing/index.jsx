import { Card, Col, List, Row, Tag, Typography } from 'antd';

const tasks = [
  { title: '2#楼 302 室空调维修', status: '处理中', tag: '待确认' },
  { title: '教学楼 3# 楼灯具更换', status: '已预约', tag: '待施工' },
  { title: '宿舍门锁维修', status: '已完成', tag: '已验收' },
];

export const MyProcessingPage = () => (
  <div>
    <Typography.Title level={3} style={{ marginBottom: 20 }}>我的处理中</Typography.Title>

    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card bordered={false} style={{ borderRadius: 12 }}>
          <List
            itemLayout="horizontal"
            dataSource={tasks}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Tag key={item.title} color={item.status === '已完成' ? 'green' : 'processing'}>
                    {item.status}
                  </Tag>,
                ]}
              >
                <List.Item.Meta
                  title={item.title}
                  description={item.tag}
                />
              </List.Item>
            )}
          />
        </Card>
      </Col>
    </Row>
  </div>
);
