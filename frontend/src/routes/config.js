import {
  FormOutlined,
  ToolOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { RepairWorkbenchPage } from '@/pages/students/workbench/index.jsx';
import { RepairOrdersPage } from '@/pages/students/orders/index.jsx';
import { MyProcessingPage } from '@/pages/students/myProcessing/index.jsx';
import { RepairPage as TechRepairPage } from '@/pages/tech/repair/index.jsx';
import { WorkPoolPage as TechWorkPoolPage } from '@/pages/tech/workPool/index.jsx';
import { MyProcessingPage as TechMyProcessingPage } from '@/pages/tech/myProcessing/index.jsx';
import { TechTicketDetailPage } from '@/pages/tech/ticketDetail/index.jsx';
import { AdminDashboardPage } from '@/pages/admin/dashboard/index.jsx';
import { AdminAllOrdersPage } from '@/pages/admin/allOrders/index.jsx';
import { AdminTicketDetailPage } from '@/pages/admin/ticketDetail/index.jsx';

export const appRoutesConfig = [
  {
    path: '/student',
    label: '学生端',
    roles: ['student'],
    children: [
      { path: 'workbench', label: '维修工作台', icon: ToolOutlined, component: RepairWorkbenchPage },
      { path: 'orders', label: '工单池', icon: FormOutlined, component: RepairOrdersPage },
      { path: 'my-processing', label: '我的处理中', icon: UserOutlined, component: MyProcessingPage },
    ],
  },
  {
    path: '/tech',
    label: '运维端',
    roles: ['repair', 'tech'],
    children: [
      { path: 'repair', label: '维修工作台', icon: ToolOutlined, component: TechRepairPage },
      { path: 'workPool', label: '工作池', icon: FormOutlined, component: TechWorkPoolPage },
      { path: 'myProcessing', label: '我的处理中', icon: UserOutlined, component: TechMyProcessingPage },
      { path: 'tickets/:id', label: '工单详情', component: TechTicketDetailPage, hideInMenu: true },
    ],
  },
  {
    path: '/admin',
    label: '管理端',
    roles: ['admin'],
    children: [
      { path: 'dashboard', label: '数据看板', icon: ToolOutlined, component: AdminDashboardPage },
      { path: 'all-orders', label: '全部工单', icon: FormOutlined, component: AdminAllOrdersPage },
      { path: 'tickets/:id', label: '工单详情', component: AdminTicketDetailPage, hideInMenu: true },
    ],
  },
];

/** 角色 -> 默认首页，后端返回的 role 需与这里保持一致 */
const roleHomeMap = {
  student: '/student/workbench',
  repair: '/tech/repair',
  tech: '/tech/repair',
  admin: '/admin/dashboard',
};

/** 根据角色返回默认首页，未知角色回退到学生工作台 */
export const getRoleHomePath = (role) => roleHomeMap[role] || roleHomeMap.student;

/** 根据角色过滤出可访问的菜单项 */
export const getMenuItemsByRole = (role) =>
  appRoutesConfig
    .filter((group) => group.roles.includes(role))
    .flatMap((group) =>
      group.children
        .filter((item) => !item.hideInMenu)
        .map((item) => ({
          key: `${group.path}/${item.path}`,
          label: item.label,
          icon: item.icon ? item.icon : ToolOutlined,
        })),
    );

/** 判断某个路径是否属于当前角色可访问的分组 */
export const isPathAllowedForRole = (pathname, role) => {
  const group = appRoutesConfig.find(
    (item) => pathname === item.path || pathname.startsWith(`${item.path}/`),
  );
  return group ? group.roles.includes(role) : true;
};
