import { Button, Result } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useGetIdentity } from 'ra-core';
import { getRoleHomePath } from '@/routes/config.js';

/**
 * 404 页面
 */
export const NotFound = () => {
  const navigate = useNavigate();
  const { data: identity } = useGetIdentity();
  const homePath = identity?.role ? getRoleHomePath(identity.role) : '/login';

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Result
        status="404"
        title="404"
        subTitle="抱歉，您访问的页面不存在"
        extra={
          <Button type="primary" onClick={() => navigate(homePath)}>
            返回首页
          </Button>
        }
      />
    </div>
  );
};
