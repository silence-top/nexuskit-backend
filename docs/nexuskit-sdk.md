# nexuskit-sdk 使用手册

> 版本：0.1.0 · 运行环境：Python ≥ 3.12 · 依赖：FastAPI、Pydantic ≥ 2.0

nexuskit-sdk 是 NexusKit 平台提供的 Python 工具包，为所有后端微服务提供：

- **统一响应结构**（`response` 模块）
- **统一业务码规范**（`BizCode`）
- **结构化异常体系**（`NexusKitException` 及子类）
- **链路追踪中间件**（`NexusTraceMiddleware`）
- **一键初始化**（`init_app`）

---

## 目录

1. [安装](#1-安装)
2. [快速开始](#2-快速开始)
3. [统一响应结构](#3-统一响应结构)
4. [业务码（BizCode）](#4-业务码bizcodes)
5. [异常体系](#5-异常体系)
6. [链路追踪中间件](#6-链路追踪中间件)
7. [API 速查表](#7-api-速查表)

---

## 1. 安装

### 本地可编辑安装（推荐开发环境）

```bash
# 在任意服务目录下，通过相对路径安装 sdk
pip install -e ../sdk
```

### pyproject.toml 声明依赖

```toml
[project]
dependencies = [
    "nexuskit-sdk",
]

[tool.uv.sources]
nexuskit-sdk = { path = "../sdk", editable = true }
```

---

## 2. 快速开始

在 FastAPI 应用的入口文件调用 `init_app`，即可完成所有中间件与异常处理器的注册：

```python
# main.py
from fastapi import FastAPI
from nexuskit_sdk import init_app

app = FastAPI()
init_app(app)
```

`init_app` 会自动完成以下三件事：

| 注册内容 | 作用 |
|---|---|
| `NexusTraceMiddleware` | 注入 / 透传 `X-NexusKit-Trace-Id` 请求链路 ID |
| `nexuskit_exception_handler` | 处理所有业务异常，返回标准 JSON 结构 |
| `validation_exception_handler` | 处理 Pydantic 参数校验失败（422），格式化错误信息 |
| `unhandled_exception_handler` | 兜底捕获所有未处理异常，返回 500 |

---

## 3. 统一响应结构

所有接口响应均使用 `UnionResponse` 格式：

```json
{
  "code": 20000,
  "message": "success",
  "data": { ... },
  "trace_id": "nk-a1b2c3d4"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | `int` | 业务码，见 [BizCode](#4-业务码bizcodes) |
| `message` | `str` | 可读提示信息 |
| `data` | `Any \| null` | 业务数据，失败时为 `null` |
| `trace_id` | `str \| null` | 链路追踪 ID |

### 3.1 `response.success`

```python
from nexuskit_sdk import response

# 基本用法
return response.success(data={"id": 1, "name": "Alice"})

# 自定义 message
return response.success(data=result, message="创建成功")

# 手动传入 trace_id（通常由中间件自动处理）
return response.success(data=result, trace_id=trace_ctx.get())
```

**返回示例：**

```json
{
  "code": 20000,
  "message": "success",
  "data": {"id": 1, "name": "Alice"},
  "trace_id": "nk-a1b2c3d4"
}
```

### 3.2 `response.fail`

通常不需要手动调用，异常处理器会自动构造失败响应。特殊场景下可直接使用：

```python
from nexuskit_sdk import response, BizCode
from fastapi.responses import JSONResponse

return JSONResponse(
    status_code=409,
    content=response.fail(code=BizCode.USER_EXISTS, message="用户名已存在")
)
```

### 3.3 在路由中使用 `UnionResponse` 泛型声明响应类型

```python
from nexuskit_sdk.response import UnionResponse
from app.schemas import UserOut

@router.get("/users/{user_id}", response_model=UnionResponse[UserOut])
async def get_user(user_id: int):
    user = await user_service.get(user_id)
    return response.success(data=UserOut.model_validate(user))
```

---

## 4. 业务码（BizCode）

业务码采用 **5 位十进制** 设计：前 3 位对应 HTTP 状态码，后 2 位为业务子码。

```
H H H S S
│ │ │ └─ 业务子码（00 = 通用，01+ = 具体场景）
└─────── 对应 HTTP 状态码
```

**推算规则：** `http_status = biz_code // 100`

### 4.1 完整业务码列表

#### 2xx 成功

| 常量 | 值 | 含义 |
|---|---|---|
| `BizCode.SUCCESS` | 20000 | 通用成功 |
| `BizCode.CREATED` | 20100 | 资源创建成功 |

#### 400 请求参数错误

| 常量 | 值 | 含义 |
|---|---|---|
| `BizCode.BAD_REQUEST` | 40000 | 通用参数错误 |
| `BizCode.PARAM_MISSING` | 40001 | 必填参数缺失 |
| `BizCode.PARAM_INVALID` | 40002 | 参数格式或值非法 |
| `BizCode.PARAM_TOO_LONG` | 40003 | 参数值超出长度限制 |
| `BizCode.IMPORT_ERROR` | 40004 | 导入数据格式错误 |

#### 401 认证失败

| 常量 | 值 | 含义 |
|---|---|---|
| `BizCode.UNAUTHORIZED` | 40100 | 通用未认证 |
| `BizCode.TOKEN_EXPIRED` | 40101 | Token 已过期 |
| `BizCode.TOKEN_INVALID` | 40102 | Token 无效（签名错误/被篡改） |
| `BizCode.TOKEN_REVOKED` | 40103 | Token 已吊销 |
| `BizCode.TOKEN_VERSION` | 40104 | Token 版本失效（密码已修改） |
| `BizCode.TOKEN_MISSING` | 40105 | 请求未携带 Token |
| `BizCode.TOKEN_MISUSE` | 40106 | Token 用途非法 |
| `BizCode.USER_NOT_FOUND` | 40107 | 用户不存在 |
| `BizCode.INVALID_CREDS` | 40108 | 账号或密码错误 |
| `BizCode.SIGN_INVALID` | 40109 | 接口签名验证失败 |
| `BizCode.MFA_REQUIRED` | 40110 | 需要 MFA 二次验证 |
| `BizCode.MFA_INVALID` | 40111 | MFA 验证码错误或已过期 |

#### 403 权限不足

| 常量 | 值 | 含义 |
|---|---|---|
| `BizCode.FORBIDDEN` | 40300 | 通用权限拒绝 |
| `BizCode.APP_FORBIDDEN` | 40301 | 无该系统访问权限 |
| `BizCode.USER_BANNED` | 40302 | 账号已被封禁 |
| `BizCode.SESSION_EXPIRED` | 40303 | 会话已失效，需重新登录 |
| `BizCode.DATA_SCOPE` | 40304 | 数据权限不足 |
| `BizCode.ACCOUNT_LOCKED` | 40305 | 账号已锁定 |
| `BizCode.ACCOUNT_EXPIRED` | 40306 | 账号已过期 |

#### 404 / 405 / 409 / 410

| 常量 | 值 | 含义 |
|---|---|---|
| `BizCode.NOT_FOUND` | 40400 | 资源未找到 |
| `BizCode.METHOD_NOT_ALLOWED` | 40500 | HTTP 方法不支持 |
| `BizCode.CONFLICT` | 40900 | 通用冲突 |
| `BizCode.USER_EXISTS` | 40901 | 用户已存在 |
| `BizCode.ROLE_EXISTS` | 40902 | 角色编码已存在 |
| `BizCode.DEPT_EXISTS` | 40903 | 部门已存在 |
| `BizCode.MENU_EXISTS` | 40904 | 菜单路径或编码已存在 |
| `BizCode.GONE` | 41000 | 资源已被永久删除 |

#### 413 / 415 / 422

| 常量 | 值 | 含义 |
|---|---|---|
| `BizCode.PAYLOAD_TOO_LARGE` | 41300 | 请求体超出大小限制 |
| `BizCode.FILE_TOO_LARGE` | 41301 | 上传文件超出单文件限制 |
| `BizCode.UNSUPPORTED_MEDIA_TYPE` | 41500 | 不支持的文件/内容类型 |
| `BizCode.UNPROCESSABLE` | 42200 | 请求体结构或字段类型不匹配 |
| `BizCode.BUSI_STATUS` | 42201 | 当前业务状态不允许此操作 |
| `BizCode.RELATION_EXISTS` | 42202 | 存在关联数据，无法删除/修改 |

#### 429 限流

| 常量 | 值 | 含义 |
|---|---|---|
| `BizCode.TOO_MANY` | 42900 | 通用请求频次超限 |
| `BizCode.REFRESH_CONFLICT` | 42901 | 并发刷新 Token 冲突 |
| `BizCode.LOGIN_TOO_MANY` | 42902 | 登录尝试次数超限 |

#### 5xx 服务端错误

| 常量 | 值 | 含义 |
|---|---|---|
| `BizCode.INTERNAL_ERROR` | 50000 | 通用服务器内部错误 |
| `BizCode.DB_ERROR` | 50001 | 数据库操作失败 |
| `BizCode.CACHE_ERROR` | 50002 | 缓存服务（Redis）异常 |
| `BizCode.IO_ERROR` | 50003 | 文件/IO 操作失败 |
| `BizCode.NOT_IMPLEMENTED` | 50100 | 功能暂未实现 |
| `BizCode.BAD_GATEWAY` | 50200 | 上游服务返回非预期响应 |
| `BizCode.UNAVAILABLE` | 50300 | 上游/依赖服务不可用 |
| `BizCode.GATEWAY_TIMEOUT` | 50400 | 上游服务响应超时 |

### 4.2 工具方法

```python
# 根据业务码推算 HTTP 状态码
BizCode.http_status(40103)  # → 401
BizCode.http_status(40301)  # → 403
BizCode.http_status(42901)  # → 429
```

### 4.3 前端判断逻辑建议

```javascript
if (code === 20000)                  // 操作成功
if (code === 20100)                  // 创建成功，可跳转详情
if (code >= 40000 && code < 40100)  // 参数错误，展示字段提示
if (code >= 40100 && code < 40200)  // 认证失败，清除 Token 跳转登录
if (code === 40303)                  // 会话失效，跳转登录
if (code === 40305)                  // 账号锁定，展示锁定提示
if (code >= 40300 && code < 40400)  // 权限不足，展示无权限页
if (code >= 40900 && code < 41000)  // 资源冲突，提示已存在
if (code >= 50000)                   // 服务端错误，展示友好提示
```

---

## 5. 异常体系

所有异常均继承自 `NexusKitException`，通过 `raise` 抛出后由异常处理器自动转换为标准 JSON 响应。

### 5.1 异常继承关系

```
NexusKitException
├── AuthException               → 401  token/认证相关
│   └── TokenExpiredException  → 401  (40101) Token 已过期
├── PermissionException         → 403  权限相关
│   └── AppAccessException     → 403  (40301) 无系统访问权限
├── ValidationException         → 400  参数/业务校验
├── NotFoundException           → 404  资源未找到
├── TooManyRequestsException    → 429  限流
└── ServiceUnavailableException → 503  上游服务不可用
```

### 5.2 使用示例

```python
from nexuskit_sdk import (
    AuthException,
    PermissionException,
    AppAccessException,
    ValidationException,
    NotFoundException,
    TokenExpiredException,
    BizCode,
)

# 认证失败（Token 无效）
raise AuthException(message="Token 无效", code=BizCode.TOKEN_INVALID)

# Token 过期（使用专用子类）
raise TokenExpiredException()

# 权限不足（通用）
raise PermissionException(message="无权操作该资源")

# 无系统访问权限
raise AppAccessException(message="您无权访问诊断系统")

# 参数校验失败
raise ValidationException(message="手机号格式不正确", code=BizCode.PARAM_INVALID)

# 资源不存在
raise NotFoundException(message=f"切片 #{slice_id} 不存在")

# 自定义业务码
raise PermissionException(message="账号已被封禁", code=BizCode.USER_BANNED)
```

**对应的 HTTP 响应：**

```json
{
  "code": 40101,
  "message": "Token 已过期",
  "data": null,
  "trace_id": "nk-a1b2c3d4"
}
```

### 5.3 `NexusKitException` 基类

需要完全自定义时可直接使用基类：

```python
from nexuskit_sdk import NexusKitException, BizCode

raise NexusKitException(
    code=BizCode.BUSI_STATUS,
    message="已发布的菜单无法删除",
    status_code=422,
)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `code` | `int` | `50000` | 业务码 |
| `message` | `str` | `"Internal Server Error"` | 可读错误信息 |
| `status_code` | `int` | `500` | HTTP 状态码 |

---

## 6. 链路追踪中间件

`NexusTraceMiddleware` 为每个请求维护一个唯一的链路追踪 ID。

### 6.1 工作机制

1. **请求入站**：读取 `X-NexusKit-Trace-Id` 请求头
   - 若存在则复用（网关下游透传场景）
   - 若不存在则生成新 ID，格式：`nk-{8位随机hex}`
2. **响应出站**：将 Trace ID 回写至响应头 `X-NexusKit-Trace-Id`
3. **上下文清理**：请求结束后自动清理 ContextVar，防止内存泄漏

### 6.2 在代码中获取当前 Trace ID

```python
from nexuskit_sdk import trace_ctx

# 在路由、Service、异常处理器中均可访问
current_trace_id = trace_ctx.get()
```

### 6.3 在响应中携带 Trace ID

```python
from nexuskit_sdk import response, trace_ctx

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await service.get(user_id)
    return response.success(
        data=UserOut.model_validate(user),
        trace_id=trace_ctx.get()   # 可选，附加到响应体
    )
```

> `init_app` 已自动注册中间件，无需手动 `add_middleware`。

---

## 7. API 速查表

### 顶层导出（`from nexuskit_sdk import ...`）

| 名称 | 类型 | 说明 |
|---|---|---|
| `init_app(app)` | 函数 | 一键注册中间件 + 异常处理器 |
| `BizCode` | 类 | 业务码命名空间 |
| `NexusKitException` | 异常基类 | 全局异常基类 |
| `AuthException` | 异常类 | 认证失败（401） |
| `TokenExpiredException` | 异常类 | Token 过期（40101） |
| `PermissionException` | 异常类 | 权限不足（403） |
| `AppAccessException` | 异常类 | 系统访问拒绝（40301） |
| `ValidationException` | 异常类 | 参数校验失败（400） |
| `NotFoundException` | 异常类 | 资源未找到（404） |
| `TooManyRequestsException` | 异常类 | 限流（429） |
| `ServiceUnavailableException` | 异常类 | 上游不可用（503） |
| `trace_ctx` | ContextVar | 当前请求 Trace ID |
| `response` | 模块 | `success` / `fail` / `UnionResponse` |

### `response` 模块

| 函数/类 | 签名 | 返回 |
|---|---|---|
| `success` | `(data=None, message="success", trace_id=None)` | `dict` |
| `fail` | `(code, message, trace_id=None)` | `dict` |
| `UnionResponse[T]` | Pydantic Generic Model | 响应体 Schema |
