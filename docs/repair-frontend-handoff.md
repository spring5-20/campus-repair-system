# 维修端前后端联调交接说明（BE2 轮次）

本文档是维修端后端的联调交接物：契约、启动方式、接口清单、权限/按钮规则与验收用例。
给前端同学时，连同 `docs/openapi.yaml` 一起提供；后端已就绪，无需等待。

## 1. 联调前置（后端如何跑起来）

1. 数据库：MySQL `localhost:3307`，库 `repair_system`（已建好并含种子数据
   REP-0001..REP-0007；如被清空，用 DataGrip 执行 `backend/sql/schema.sql` 后运行
   `python -m scripts.seed`）。
2. 启动后端：双击 `backend/start.bat`，或终端执行：
   ```powershell
   cd backend
   ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 3000
   ```
3. 地址：
   - API 根：`http://127.0.0.1:3000/api`
   - Swagger 调试页：`http://127.0.0.1:3000/docs`
   - 在线接口定义：`http://127.0.0.1:3000/openapi.json`
4. 演示账号（密码均 123456）：`student`（学生）、`tech`（维修）、`admin`（管理员）。
5. 前端开发服务器（Vite 默认 5173）已在后端 CORS 白名单内；前端环境变量
   `VITE_API_BASE_URL=http://localhost:3000/api`。

## 2. 契约与类型

- 契约唯一事实源：`docs/openapi.yaml`（本轮新增 `GET /api/tickets` 的 `scope` 参数）。
- 前端 TypeScript 类型以 `docs/openapi.yaml` 为准，可导入 Apifox 后生成，或用
  `openapi-typescript` 从 `http://127.0.0.1:3000/openapi.json` 生成。
- 响应统一信封：`{ code, message, data }`；成功 `code=0`，错误 `code` 镜像 HTTP 状态码。
- 字段一律 camelCase（如 `ticketNo`、`reporterName`、`assigneeId`、`pageSize`）。

## 3. 维修端接口清单

| 方法 | 路径 | 说明 | 角色 |
| --- | --- | --- | --- |
| GET | `/api/tickets` | 角色范围分页列表；维修用 `scope=pool\|mine`，支持 `status/category/keyword/page/pageSize` | student/tech/admin |
| GET | `/api/tickets/statistics` | 看板统计（total/pending/processing/resolved/closed/cancelled/highOpen/closureRate） | student/tech/admin |
| GET | `/api/tickets/{ticketId}` | 详情（基础信息 + comments + logs） | 数据范围内 |
| PATCH | `/api/tickets/{ticketId}/status` | 状态迁移，body `{"action":"ACCEPT"\|"RESOLVE"\|...}` | 见状态迁移表 |
| POST | `/api/tickets/{ticketId}/comments` | 新增留言，body `{"content":"..."}`（1–500 字，纯空格 422） | 数据范围内 |
| GET | `/api/tickets/{ticketId}/logs` | 操作日志时间线（时间正序） | 数据范围内 |

> `PATCH /api/tickets/{ticketId}/assignee`（管理员指派）在管理端轮次实现，维修端暂不调用。

## 4. 数据范围（谁看到哪些工单）

| 角色 | 可见范围 |
| --- | --- |
| student | 仅本人提交 |
| tech | 工单池（PENDING 未指派）+ 指派给本人的工单；`scope=pool` 只看池、`scope=mine` 只看本人任务 |
| admin | 全部 |

越权读取返回 **404**（不泄露存在性）；越权操作返回 **403**。

## 5. 状态迁移与按钮显示规则

| 当前状态 | 可执行动作 | 谁 | 迁移结果 | 冲突时 |
| --- | --- | --- | --- | --- |
| PENDING（未指派） | ACCEPT 接单 | tech | PROCESSING，负责人=本人 | 409 |
| PROCESSING（本人负责） | RESOLVE 完成维修 | tech | RESOLVED | 409 |
| PENDING | CANCEL 取消 | student | CANCELLED | 409 |
| RESOLVED | CLOSE 验收关闭 | student | CLOSED | 409 |

前端按钮可见性建议（后端是最终校验，隐藏只是 UX）：

- tech：PENDING 且 `assigneeId` 为空 → 显示"接单"；PROCESSING 且 `assigneeId===当前用户` → 显示"标记维修完成"；可见工单均可留言。
- student：PENDING → "取消"；RESOLVED → "验收关闭"。
- 收到 **409** 时：提示"工单状态已变化，请刷新后重试"，重新拉详情。
- 收到 **401** 时：清除登录态并跳转登录页。

## 6. 错误语义

| 状态码 | 含义 | 前端处理 |
| --- | --- | --- |
| 401 | 未登录/凭证失效 | 跳登录 |
| 403 | 越权（角色或数据范围） | 隐藏入口/提示无权限 |
| 404 | 工单不存在或不可见 | 提示后返回列表 |
| 409 | 状态冲突（被他人抢先） | 刷新详情重试 |
| 422 | 参数错误（含纯空格留言、非法 scope/action） | 按 `data` 提示 |

## 7. Apifox 联调步骤

1. 导入 `docs/openapi.yaml`（或 `http://127.0.0.1:3000/openapi.json`）。
2. `POST /api/auth/login` 获取 `data.token`，配置环境变量 `token`，接口认证选
   Bearer Token（`Authorization: Bearer {{token}}`）。
3. 建议用例（tech）：
   - `GET /api/tickets?scope=pool` → 取一条 PENDING；
   - `PATCH .../status` `{"action":"ACCEPT"}` → 200；
   - `POST .../comments` 留言 → 200；
   - `PATCH .../status` `{"action":"RESOLVE"}` → 200；
   - 用 student 账号对同一工单 ACCEPT → 403；重复 ACCEPT → 409。

## 8. 后端测试证据（本轮）

`python -m pytest backend/tests`：**98 passed**（含学生侧 79 个回归、维修端 19 个新增用例：
AC-04 接单、AC-05 越权解决 403、AC-07 解决、并发 409、scope 筛选、统计口径、可见性）。
