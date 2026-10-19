import { CoreAdminContext } from 'ra-core';
import { HashRouter, useRoutes } from 'react-router-dom';
import { dataProvider } from '@/providers/dataProvider';
import { authProvider } from '@/providers/authProvider';
import { i18nProvider } from '@/providers/i18nProvider';
import { appRoutes } from '@/routes/index';

/**
 * 应用入口：
 * - HashRouter 承担路由，RequireAuth 统一做登录校验
 * - CoreAdminContext 提供 ra-core 的 dataProvider / authProvider / i18nProvider 等上下文
 *   （Router 必须位于 CoreAdminContext 外层，避免其内部 AdminRouter 再次创建路由器）
 * - 所有页面 UI 均使用 Ant Design，数据逻辑由 ra-core Controller Hooks 驱动
 */
function AppRoutes() {
  return useRoutes(appRoutes);
}

export default function App() {
  return (
    <HashRouter>
      <CoreAdminContext
        dataProvider={dataProvider}
        authProvider={authProvider}
        i18nProvider={i18nProvider}
      >
        <AppRoutes />
      </CoreAdminContext>
    </HashRouter>
  );
}
