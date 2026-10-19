# Campus Repair System — Backend

FastAPI + SQLAlchemy Async 后端，对应 PRD V1.0（P0 接口）与 `docs/openapi.yaml` 契约。

## 环境准备

```bash
uv venv                 # 创建 .venv（Python 3.12）
uv pip install -r requirements.txt
```

兼容 pip：`pip install -r requirements.txt` 可直接使用。

## 启动（开发）

```bash
# 1) 建库建表（二选一）
# 方式 A：DataGrip 中执行 backend/sql/schema.sql（自动创建 repair_system 库、
#         5 张表、演示账号与工单编号计数器；连接 localhost:3307，root 执行）
# 方式 B：docker compose up -d 启动 MySQL 8（宿主机 3307），再执行 schema.sql
# 2) 配置连接：复制 .env.example 为 .env（默认
#    DATABASE_URL=mysql+aiomysql://repair:repair@localhost:3307/repair_system）
# 3) 幂等种子：演示账号 + 样例工单 REP-0001..REP-0007
uv run python -m scripts.seed
# 4) 启动服务
uv run uvicorn app.main:app --reload --port 3000
```

服务地址：`http://localhost:3000/api`；Swagger：`http://localhost:3000/docs`。

## 演示账号（密码均为 123456）

| 账号 | 角色 | 数据范围 |
| --- | --- | --- |
| student | 学生 | 本人提交的工单 |
| tech | 维修人员 | 工单池（PENDING 未指派）+ 指派给本人的工单 |
| admin | 系统管理员 | 全部工单（只读范围；指派等动作在管理端轮次提供） |

## 维修端接口（本轮）

- `GET /api/tickets`：角色范围分页查询；维修人员可用 `scope=pool|mine` 筛选
  （pool=工单池，mine=本人任务，缺省=工单池+本人任务），并支持
  `status/category/keyword/page/pageSize` 筛选（LIST-001）。
- `GET /api/tickets/statistics`：角色范围统计（DASH-001）。
- `GET /api/tickets/{ticketId}`：详情（含留言与时间线，TKT-002）。
- `PATCH /api/tickets/{ticketId}/status`：状态迁移，body `{"action": "..."}`：
  - 维修 `ACCEPT`：仅 PENDING→PROCESSING，负责人=本人，并发冲突 409（FLOW-001）
  - 维修 `RESOLVE`：仅 PROCESSING→RESOLVED，且必须本人负责，越权 403（FLOW-003）
  - 学生 `CANCEL/CLOSE`：取消 PENDING / 验收关闭 RESOLVED（FLOW-004）
- `POST /api/tickets/{ticketId}/comments`、`GET /api/tickets/{ticketId}/logs`：
  留言与操作时间线（TKT-003 / AUD-001）。

统一错误语义：未登录 401、越权 403、工单不存在/不可见 404、状态冲突 409、
参数错误 422；错误响应信封为 `{code, message, data: null}`。

## 管理端接口（本轮）

- `PATCH /api/tickets/{ticketId}/assignee`：管理员指派，body `{"assigneeId": 用户ID}`；
  仅 admin；目标必须是维修人员（否则 422）；仅 PENDING 未指派可指派（否则 409）；
  写入负责人/指派人/指派时间并产生 `ASSIGN` 日志（FLOW-002）。
- `PATCH /api/tickets/{ticketId}/status`：管理员异常处理（FLOW-003/004）：
  - `RESOLVE`：任意 PROCESSING → RESOLVED（无需本人负责）
  - `CLOSE`：RESOLVED → CLOSED（代为关闭）
  - `CANCEL`：PENDING → CANCELLED（异常取消）
  - `ASSIGN` 只能走 `/assignee` 接口，状态接口传 ASSIGN 返回 403
- 管理端列表/详情/统计/留言/日志复用既有接口，数据范围为全部工单。

管理端联调交接说明见 `docs/admin-frontend-handoff.md`。

## Apifox 联调

1. 在 Apifox 中导入接口：`docs/openapi.yaml`（或运行后访问
   `http://localhost:3000/openapi.json` 导入）。
2. 先调用 `POST /api/auth/login` 获取 `data.token`。
3. 在 Apifox 环境变量中配置 `token`，接口认证选择 Bearer Token
   （`Authorization: Bearer {{token}}`）。
4. 建议用例：tech 登录 → `GET /api/tickets?scope=pool` 找一条 PENDING →
   `PATCH .../status` 传 `{"action":"ACCEPT"}` → 留言 → `{"action":"RESOLVE"}`；
   学生登录对同一工单执行 `ACCEPT` 应得到 403。

## 测试

```bash
uv run python -m pytest tests
uv run python -m pytest tests --cov=app --cov-report=term-missing
```

测试使用 aiosqlite 内存库，不依赖本机 MySQL；MySQL 联调（3307）作为独立验收步骤。

## 配置

复制 `.env.example` 为 `.env` 并按需修改。`JWT_SECRET` 仅用于开发，禁止提交真实密钥。
