import { Card } from 'antd';
import { ProTable } from '@ant-design/pro-components';

export const RecentPosts = ({ data = [], loading = false, columns = [] }) => (
  <Card title="最近文章">
    <ProTable
      rowKey="id"
      columns={columns}
      dataSource={data}
      loading={loading}
      pagination={false}
      size="middle"
      search={false}
      options={false}
      toolbar={false}
    />
  </Card>
);
