import { Button, Card } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

export const QuickActions = ({ onNavigate }) => (
  <Card title="快捷操作">
    <Button
      type="primary"
      block
      icon={<PlusOutlined />}
      style={{ marginBottom: 12 }}
      onClick={() => onNavigate('/workbench')}
    >
      统计概览
    </Button>
    <Button block icon={<PlusOutlined />} onClick={() => onNavigate('/workbench')}>
      返回首页
    </Button>
  </Card>
);
