# 校园报修协同系统前端

这是一个基于 Vite + React 18 + ra-core + Ant Design 5 的校园报修后台前端项目，适用于学生报修、维修处理、工单派发等协同流程的管理后台开发。

## 项目特点

- 使用 React 18 + Vite 构建前端应用
- 采用 `ra-core` 作为状态与鉴权基础
- 使用 `react-router-dom` 实现路由与登录守卫
- 使用 Ant Design 5 作为 UI 组件库
- 通过 `localStorage` 提供 mock 登录状态和基础页面数据
- 提供统一 Axios 请求封装和 `/api/auth/login` 接口入口
- 配置了 ESLint 和 commitlint，统一编码与提交规范

## 技术栈

- Vite 8
- React 18
- react-router-dom 7
- Ant Design 5
- ra-core 5
- Axios 1.x
- ESLint 9
- commitlint

## 当前项目结构

```text
teacher-campus-front-system/
├── AGENTS.md
├── README.md
├── eslint.config.js
├── index.html
├── package.json
├── vite.config.js
├── vite.smoke.config.js
├── src/
│   ├── App.jsx
│   ├── index.css
│   ├── main.jsx
│   ├── api/
│   │   ├── auth/
│   │   │   └── login.js
│   │   ├── client.js
│   │   └── index.js
│   ├── components/
│   │   ├── PageHeader.jsx
│   │   └── RequireAuth.jsx
│   ├── layout/
│   │   └── AdminLayout.jsx
│   ├── pages/
│   │   ├── login/
│   │   │   └── index.jsx
│   │   ├── notFound/
│   │   │   └── index.jsx
│   │   └── students/
│   │       ├── myProcessing/
│   │       │   └── index.jsx
│   │       ├── orders/
│   │       │   └── index.jsx
│   │       └── workbench/
│   │           └── index.jsx
│   ├── providers/
│   │   ├── authProvider.js
│   │   ├── dataProvider.js
│   │   └── i18nProvider.js
│   ├── routes/
│   │   └── index.jsx
│   └── utils/
│       └── format.js
├── scripts/
│   └── smoke.jsx
├── work/
│   └── smoke-out/
│       ├── smoke.js
│       └── assets/
├── dist/
└── outputs/
```

## 运行方式

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发环境

```bash
npm run dev
```

默认访问地址：

```text
http://localhost:5173
```

### 3. 构建生产环境包

```bash
npm run build
```

### 4. 预览构建产物

```bash
npm run preview
```

### 5. 运行冒烟测试

```bash
npm run smoke
```

### 6. 代码检查与提交校验

```bash
npm run lint
npm run commitlint:check
```

## 路由说明

当前实际路由：

- `/login`：登录页
- `/workbench`：维修工作台
- `/orders`：工单池
- `/my-processing`：我的处理中
- `*`：404 页面

未登录用户会被 `RequireAuth` 拦截并重定向到 `/login`。

## 默认账号

项目内置 mock 登录账号，便于本地演示：

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| student | student123 | 学生用户 |
| repair | repair123 | 维修人员 |
| admin | admin123 | 管理员 |

## 接口说明

### 登录接口

接口文件：

- `src/api/auth/login.js`

调用方式：

```js
import { login } from '@/api/auth/login';

const result = await login({ username: 'admin', password: 'admin123' });
```

默认请求地址：

```text
POST /api/auth/login
```

后端常见返回结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "xxx",
    "user": {
      "id": 1,
      "username": "admin",
      "fullName": "系统管理员",
      "role": "admin"
    }
  }
}
```

如果后端暂未准备好，前端会自动回退到本地 mock 登录逻辑。

## 认证与数据说明

- 认证逻辑位于：`src/providers/authProvider.js`
- 请求实例位于：`src/api/client.js`
- 通用请求封装位于：`src/api/index.js`
- 当前 mock 数据仍通过 `localStorage` 持久化，便于本地演示和开发

## 代码规范

- 2 空格缩进
- 使用单引号
- 语句以分号结尾
- 组件文件命名使用 PascalCase
- 普通逻辑文件命名使用 camelCase
- 路径优先使用 `@/` 绝对导入

## 提交规范

项目要求遵循 Conventional Commits，例如：

- `feat: 新增登录页`
- `fix: 修复路由跳转`
- `chore: 更新依赖`

提交前推荐执行：

```bash
npm run lint
npm run commitlint:check
```


这样在开发环境中，前端请求：

```js
api.get('/users')
```

会被转发到：

```text
http://192.168.60.6:8000/users
```

这使得前端可以直接按 `/api` 方式访问后端，同时避免跨域问题。

## 路径别名

项目中已配置 `@` 别名，映射到 `src` 目录：

```js
resolve: {
  alias: {
    '@': fileURLToPath(new URL('./src', import.meta.url)),
  },
}
```

因此可以这样写：

```js
import { dataProvider } from '@/providers/dataProvider';
import { PageHeader } from '@/components/PageHeader';
```

## 真实后端接入建议

当前项目默认使用本地 mock 数据，适合前端开发和演示场景。

接入真实后端时，建议：

1. 在 `.env` 中设置 `VITE_API_BASE_URL`
2. 保持 `src/api/` 的统一请求封装不变
3. 逐步替换 `src/providers/dataProvider.js` 的实现为真实接口版本
4. 保持 UI 层不变，继续使用 `ra-core` 的 Controller Hooks

## 说明

- 演示数据保存在浏览器 `localStorage` 中，key 为 `reac-admin-db-v1`
- 登录状态保存在 `localStorage` 中，key 为 `reac-admin-auth`
- 项目默认为前后端分离/管理后台模板，适合快速扩展文章、用户、权限、报表等模块

## 许可证

本项目仅用于学习和演示，适用于前端后台管理系统模版开发场景。
