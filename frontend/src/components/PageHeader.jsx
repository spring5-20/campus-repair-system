import { Space, Typography } from 'antd';

/**
 * 页面标题栏：标题 + 右侧操作区
 */
export const PageHeader = ({ title, extra, style }) => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 16,
      flexWrap: 'wrap',
      gap: 12,
      ...style,
    }}
  >
    <Typography.Title level={4} style={{ margin: 0 }}>
      {title}
    </Typography.Title>
    {extra ? <Space wrap>{extra}</Space> : null}
  </div>
);
