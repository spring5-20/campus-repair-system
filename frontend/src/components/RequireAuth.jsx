import { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthProvider } from 'ra-core';
import { getRoleHomePath, isPathAllowedForRole } from '@/routes/config.js';

/**
 * 登录守卫：校验 authProvider.checkAuth()
 * - 未登录时重定向到 /login，并记录来源地址
 * - 已登录但访问其他角色分组时，重定向到当前角色默认首页
 */
export const RequireAuth = () => {
  const authProvider = useAuthProvider();
  const location = useLocation();
  const [state, setState] = useState({ loading: true, authenticated: false, role: null });

  useEffect(() => {
    let active = true;
    authProvider
      .checkAuth()
      .then(() => authProvider.getIdentity())
      .then((identity) => {
        if (active) {
          setState({ loading: false, authenticated: true, role: identity?.role });
        }
      })
      .catch(() => {
        if (active) setState({ loading: false, authenticated: false, role: null });
      });
    return () => {
      active = false;
    };
  }, [authProvider]);

  if (state.loading) {
    return (
      <div
        style={{
          display: 'flex',
          height: '100vh',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Spin size="large" />
      </div>
    );
  }

  if (!state.authenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }

  if (!isPathAllowedForRole(location.pathname, state.role)) {
    return <Navigate to={getRoleHomePath(state.role)} replace />;
  }

  return <Outlet />;
};
