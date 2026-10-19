import { useMemo } from 'react';
import { Row, Col } from 'antd';
import { RocketOutlined, TeamOutlined } from '@ant-design/icons';
import { useGetList } from 'ra-core';
import { useNavigate } from 'react-router-dom';
import { formatDateTime } from '@/utils/format';
import { StatCards } from '@/pages/workbench/components/statCards';
import { RecentPosts } from '@/pages/workbench/components/recentPosts';
import { QuickActions } from '@/pages/workbench/components/quickActions';

/**
 * 首页：展示概览统计、最近文章和快捷操作
 */
export const Home = () => {
  const navigate = useNavigate();

  const { total: publishedTotal } = useGetList('posts', {
    pagination: { page: 1, perPage: 1 },
    sort: { field: 'id', order: 'DESC' },
    filter: { status: 'published' },
  });
  const { total: userTotal } = useGetList('users', {
    pagination: { page: 1, perPage: 1 },
    sort: { field: 'id', order: 'DESC' },
  });

  const { data: recentPosts = [], isPending } = useGetList('posts', {
    pagination: { page: 1, perPage: 5 },
    sort: { field: 'published_at', order: 'DESC' },
  });

  const { data: users = [] } = useGetList('users', {
    pagination: { page: 1, perPage: 100 },
    sort: { field: 'id', order: 'ASC' },
  });
  const userMap = useMemo(() => new Map(users.map((item) => [item.id, item])), [users]);

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      ellipsis: true,
    },
    {
      title: '作者',
      dataIndex: 'author_id',
      width: 120,
      render: (value) => userMap.get(value)?.name || `用户 ${value}`,
    },
    {
      title: '发布时间',
      dataIndex: 'published_at',
      width: 160,
      render: formatDateTime,
    },
  ];

  const stats = [
    { title: '已发布', value: publishedTotal, icon: <RocketOutlined />, color: '#52c41a' },
    { title: '用户总数', value: userTotal, icon: <TeamOutlined />, color: '#722ed1' },
  ];

  return (
    <div>
      <StatCards stats={stats} />

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <RecentPosts data={recentPosts} loading={isPending} columns={columns} />
        </Col>

        <Col xs={24} lg={8}>
          <QuickActions onNavigate={navigate} />
        </Col>
      </Row>
    </div>
  );
};
