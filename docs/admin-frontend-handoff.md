# 管理端前后端联调交接说明（管理端轮次）

本文档是管理端后端的联调交接物，连同 `docs/openapi.yaml` 一起给前端同学。
管理端复用了学生/维修端的列表、详情、统计、留言、日志接口，只读范围=全部工单；
本轮新增的是**指派**与**异常状态处理**两个能力。

## 1. 联调前置

- 后端启动：双击 `backend/start.bat` 或
  `cd backend && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 3000`。
- 地址：API 根 `http://127.0.0.1:3000/api`；Swagger `http://127.0.0.1:3000/docs`。
- 演示账号：`admin / 123456`（管理员）、`tech / 123456`（维修）、`student / 123456`（学生）。
- 前端环境变量 `VITE_API_BASE_URL=http://localhost:3000/api`（5173 已在 CORS 白名单）。

## 2. 管理端新增接口

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/api/users` | 用户列表（指派下拉数据源），可选 `role=tech` 只取维修人员 | 仅 admin |
| PATCH | `/api/tickets/{ticketId}/assignee` | 指派 PENDING 工单给维修人员，body `{"assigneeId": 用户ID}` | 仅 admin |
| PATCH | `/api/tickets/{ticketId}/status` | 管理员异常处理：`RESOLVE`/`CLOSE`/`CANCEL`，body `{"action":"..."}` | 仅 admin |

指派成功返回 `Ticket`：`status=PROCESSING`，写入 `assigneeId`、`assigneeName`、
`assignedBy`（指派人）、`assignedAt`，并产生 `ASSIGN` 日志。

## 3. 权限与按钮显示规则

管理端看板/全部工单页面（按钮可见性仅 UX，后端才是最终校验）：

| 工单状态 | 管理员可执行动作 |
| --- | --- |
| PENDING（未指派） | 指派（选择维修人员）/ 取消 |
| PROCESSING | 标记解决（异常代为解决，无需本人负责） |
| RESOLVED | 代为关闭 |

注意：`ASSIGN` 动作只能走 `/assignee` 接口；在状态接口传 `{"action":"ASSIGN"}` 返回 403。

## 4. 校验与错误语义

| 场景 | 状态码 |
| --- | --- |
| 非管理员调用指派/异常处理 | 403 |
| 指派对象不存在 | 404 |
| 指派对象不是维修人员（role != tech） | 422 |
| 工单不存在 | 404 |
| 工单不是 PENDING（指派时）或状态不符合迁移前提 | 409 |
| 并发冲突（被接单/他人先指派/状态已变） | 409 |
| 参数错误（非法 action/assigneeId） | 422 |

前端收到 409 提示"工单状态已变化，请刷新后重试"并重新拉取详情；401 清除登录态。

## 5. Apifox 联调用例（admin）

1. 导入 `docs/openapi.yaml`，`POST /api/auth/login`（admin/123456）拿 token 配 Bearer。
2. `GET /api/tickets?status=PENDING` 找一条未指派工单，记录 id。
3. `GET /api/users?role=tech` 拉取维修人员列表，取其中一个 `id`。
4. `PATCH /api/tickets/{id}/assignee` body `{"assigneeId": tech的用户ID}` → 200，状态变 PROCESSING。
5. `PATCH /api/tickets/{id}/status` `{"action":"RESOLVE"}` → 200（异常代为解决）。
6. 对 RESOLVED 工单 `{"action":"CLOSE"}` → 200（代为关闭）。
7. 负向：用 tech 账号调用 `/assignee` → 403；把 `assigneeId` 指向学生 → 422；
   对已指派工单再指派 → 409。

## 6. 后端测试证据（本轮）

`python -m pytest backend/tests`：**110 passed**（学生 79 + 维修 19 + 管理端 12：
AC-06 指派、非管理员 403、目标非维修 422、非 PENDING/并发 409、
管理员 RESOLVE/CLOSE/CANCEL 与错误状态 409）。
