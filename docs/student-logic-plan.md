# 学生侧实施计划（三人分工与 Git 规范）

本轮只实现**学生全部相关逻辑**，不做维修人员/管理员逻辑与 P1 附件。范围、验收以 PRD V1.0 为准，接口以 `docs/openapi.yaml` 为准（契约先行，ADR-0001）。基线分支 `develop`（骨架已提交：`9893de8`、`a9b4d27`）。

## 范围与排除

| 包含 | 需求 ID |
| --- | --- |
| 登录 / 登录态恢复 | AUTH-001、AUTH-002 |
| 创建工单 | TKT-001 |
| 我的工单查询（学生数据范围） | LIST-001 |
| 学生统计 | DASH-001 |
| 工单详情（含留言与时间线） | TKT-002 |
| 取消 PENDING、验收关闭 RESOLVED→CLOSED | FLOW-004（学生动作） |
| 处理留言 | TKT-003 |
| 本人工单操作日志 | AUD-001 |

排除：接单/解决（维修）、指派/异常处理（管理员）、附件后端存储（P1）、`/api/tickets/{ticketId}/assignee`。

## 分工（垂直切片）

| 成员 | 切片 | 分支 | 需求 | 交付 | 依赖 |
| --- | --- | --- | --- | --- | --- |
| A | S1 账号+创建 | `feature/be-student-create` | AUTH-001/002、TKT-001 | login/me 测试补全、创建工单（counter 编号、PENDING、CREATE 日志）、种子基线 | 无（骨架已含 auth） |
| B | S2 查询+统计 | `feature/be-student-query` | LIST-001、DASH-001 | 学生范围分页查询（keyword/status/category/page/pageSize）、学生统计口径 | S1 的 `get_current_user` 与数据范围约定 |
| C | S3 详情+互动 | `feature/be-student-interaction` | TKT-002、FLOW-004、TKT-003、AUD-001 | `TicketDetail`（Ticket+comments+logs）、取消/验收关闭（条件更新+409）、留言（写 COMMENT 日志）、日志时间线 | S1 鉴权 + S2 的可见范围规则 |

集成顺序固定：**S1 → S2 → S3**。后一个分支必须从合并后的最新 `develop` 拉出。

## 契约改动（S3 的 PR 内一并提交）

`GET /api/tickets/{ticketId}` 响应从 `Ticket` 改为 `TicketDetail`：

```yaml
TicketDetail:
  allOf:
    - $ref: "#/components/schemas/Ticket"
    - type: object
      properties:
        comments:
          type: array
          items: { $ref: "#/components/schemas/TicketComment" }
        logs:
          type: array
          items: { $ref: "#/components/schemas/TicketLog" }
```

## 契约测试（ADR-0001，本轮启用）

测试改为**学生路径白名单**比对，忽略 FastAPI 自动生成的默认 422 与描述文本，只比对：方法、参数、requestBody schema、响应状态码、成功响应的 data schema 名。

本轮白名单：

- `/api/health`、`/api/auth/login`、`/api/auth/me`
- `GET/POST /api/tickets`、`GET /api/tickets/statistics`
- `GET /api/tickets/{ticketId}`、`PATCH /api/tickets/{ticketId}/status`
- `POST /api/tickets/{ticketId}/comments`、`GET /api/tickets/{ticketId}/logs`

每个切片的 PR 为自己的路径启用比对；`/api/tickets/{ticketId}/assignee` 保持未比对，待维修/管理员轮次放开。

## Git 规范

**分支**：`feature/be-student-{create,query,interaction}`，只从 `develop` 拉取；禁止直接推 `develop`。

**提交**：Conventional Commits，subject 带需求 ID：

```text
feat(backend): student create ticket with counter ticketNo (TKT-001)
fix(backend): strip comment whitespace before validation (TKT-003)
```

一个提交只做一个逻辑变更；不允许 `wip`、混合提交。

**PR**：一个 PR 一个主题；描述用以下模板：

```text
需求 ID：FLOW-004（学生取消/验收）
改动文件：backend/app/services/ticket_service.py、backend/app/api/endpoints/tickets.py、backend/tests/flow/test_flow_004_cancel_pending.py
契约变更：无 / 有（说明 docs/openapi.yaml 改动）
共享文件声明：无 / 涉及 tests/conftest.py（已通知另两人）
测试证据：pytest 输出 / 覆盖率 / 截图
联调注意：409 并发场景需双人验证
```

至少一名非作者评审，高优先级评论关闭后由 PR 作者合并到 `develop`。

## 共享文件所有权

| 文件 | 基线 Owner | 规则 |
| --- | --- | --- |
| `docs/openapi.yaml` | 共享 | 契约改动与对应代码同一 PR，且先改契约 |
| `backend/app/models/*` | S1（合并后） | 改动须在 PR 声明并知会 |
| `backend/tests/conftest.py` | S1（合并后） | 同上 |
| `backend/scripts/seed.py` | S1（合并后） | 同上 |
| `backend/app/api/dependencies.py` | S1（合并后） | 同上 |
| `backend/app/schemas/common.py` | 共享 | 同上 |

## 验收与测试

- 验收用例：AC-01、AC-02、AC-03、AC-08、AC-09、AC-10、AC-12 + AUTH-001/002。
- 测试命名：`test_<需求ID>_<场景>.py`，按切片认领（S3 例：`test_flow_004_cancel_pending.py`）。
- 守门命令：`python -m pytest backend/tests`；`pytest-cov` 行覆盖率 ≥80%。
- 完成标准：三个 PR 全部合并、白名单契约测试绿、AC 清单通过、README 启动步骤可用。

## 成员映射

| 占位 | 切片 | 姓名/Gitee 账号 |
| --- | --- | --- |
| A | S1 账号+创建 | secremate86（姓名待填） |
| B | S2 查询+统计 | 待填写 |
| C | S3 详情+互动 | 待填写 |
