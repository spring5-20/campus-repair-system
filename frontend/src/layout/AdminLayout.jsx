import { useMemo, useState } from 'react';
import { Avatar, Button, Dropdown, Layout, Menu, Modal, Space, Typography, theme } from 'antd';
import {
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useGetIdentity, useLogout } from 'ra-core';
import { setAuthToken } from '@/api/client';
import { getMenuItemsByRole } from '@/routes/config.js';

const { Header, Sider, Content } = Layout;

/**
 * 整体布局：左侧菜单 + 顶部用户区 + 内容区
 */
export const AdminLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { data: identity } = useGetIdentity();
  const logout = useLogout();
  const { token } = theme.useToken();
  const currentUserName = identity?.username || identity?.fullName || '未知用户';

  // 根据当前用户角色过滤左侧菜单
  const menuItems = useMemo(
    () =>
      getMenuItemsByRole(identity?.role).map((item) => ({
        ...item,
        icon: <item.icon />,
      })),
    [identity?.role],
  );

  // 根据当前路径高亮菜单
  const selectedKey = useMemo(() => {
    const path = location.pathname;
    const match = menuItems.find(
      (item) => path === item.key || path.startsWith(`${item.key}/`),
    );
    return match ? match.key : '/login';
  }, [location.pathname, menuItems]);

  const handleLogout = () => {
    Modal.confirm({
      title: '确认退出登录？',
      content: '退出后将返回登录页，需要重新登录。',
      okText: '确认退出',
      cancelText: '取消',
      centered: true,
      onOk: () => {
        setAuthToken('');
        localStorage.removeItem('reac-admin-auth');
        logout(undefined, '/login');
      },
    });
  };

  const userMenu = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
      },
    ],
    onClick: handleLogout,
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={220}
        style={{
          background: '#fff',
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: collapsed ? 0 : 10,
            padding: collapsed ? '0 10px' : '0 14px',
            background: '#1a3f3b',
            color: '#fff',
            overflow: 'hidden',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            transition: 'all 0.2s ease',
          }}
        >
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 10,
              background: 'linear-gradient(180deg, #f0d88d 0%, #d9b75a 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#1a3f3b',
              fontSize: collapsed ? 20 : 24,
              fontWeight: 700,
              flexShrink: 0,
              boxShadow: '0 8px 16px rgba(0, 0, 0, 0.12)',
            }}
          >
            修
          </div>

          {!collapsed && (
            <div
              style={{
                minWidth: 0,
                maxWidth: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  fontSize: 18,
                  lineHeight: 1.2,
                  fontWeight: 700,
                  color: '#f5f6f2',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                校园报修
              </div>
              <div
                style={{
                  marginTop: 1,
                  fontSize: 9,
                  letterSpacing: 1,
                  color: 'rgba(255,255,255,0.8)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                MINI REPAIR SYSTEM
              </div>
            </div>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={({ key }) => navigate(key)}
          style={{
            background: '#fff',
            borderRight: 0,
            color: '#1f2d2c',
            padding: '12px 4px'
          }}
          items={menuItems.map((item) => ({
            ...item,
            style: {
              color: selectedKey === item.key ? '#fff' : '#1a3f3b',
              fontWeight: 600,
              background: selectedKey === item.key ? '#1a3f3b' : 'transparent',
              borderRadius: 6,
            },
            icon: selectedKey === item.key
              ? <span style={{ color: '#fff' }}>{item.icon}</span>
              : item.icon,
          }))}
        />
      </Sider>

      <Layout>
        <Header
          style={{
            background: '#1a3f3b',
            height: 64,
            lineHeight: '64px',
            padding: '0 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0, 21, 41, 0.08)',
            zIndex: 1,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined style={{ color: '#fff' }} /> : <MenuFoldOutlined style={{ color: '#fff' }} />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ color: '#fff' }}
          />

          <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer', padding: '0 8px', color: '#fff' }}>
              <Avatar
                size="small"
                icon={<UserOutlined style={{ color: '#fff' }} />}
                style={{ backgroundColor: 'rgba(255,255,255,0.15)', color: '#fff' }}
              >
                {currentUserName.slice(0, 1).toUpperCase()}
              </Avatar>
              <Typography.Text strong style={{ color: '#fff' }}>
                {currentUserName}
              </Typography.Text>
            </Space>
          </Dropdown>
        </Header>

        <Content style={{ margin: 16 }}>
          <div
            style={{
              background: token.colorBgContainer,
              borderRadius: token.borderRadiusLG,
              padding: 24,
              minHeight: 'calc(100vh - 116px)',
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};
