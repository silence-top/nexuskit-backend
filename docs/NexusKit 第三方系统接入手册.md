# NexusKit 第三方系统接入手册

> 版本 v1.0 · 适用范围：接入 NexusKit 统一认证与权限平台的子系统

---

## 一、接入流程概览

```
1. 联系平台管理员注册应用  →  获得 app_code + app_secret
2. 网关添加路由配置         →  子系统拥有独立 URL 前缀
3. 子系统信任网关注入的请求头  →  无需自己做 Token 验证
4. 按需调用 /internal/* 接口  →  主动拉取用户信息/角色
```

---

## 二、注册应用

联系 NexusKit 平台管理员，通过管理后台创建应用：

| 字段 | 说明 | 示例 |
|------|------|------|
| `app_code` | 全局唯一标识，小写下划线 | `erp` / `diagnosis` |
| `app_name` | 系统显示名称 | `ERP 系统` |
| `perm_mode` | 权限模式：`full`（菜单+按钮）/ `role_only`（仅角色） | `full` |

**创建成功后，平台返回 `app_secret`（仅展示一次，请妥善保存）：**

```json
{
  "app_code": "erp",
  "app_secret": "Kx9mN2pQrT...",
  "message": "请将密钥安全保存，不会再次展示"
}
```

> ⚠️ 密钥泄露后可通过管理后台一键重置：`POST /api/identity/apps/{app_code}/secret`

---

## 三、网关路由配置

平台管理员在 `gateway/server.js` 的 `UPSTREAM_SERVICES` 中添加路由条目：

```js
// 子系统的独立登录入口（复用 NexusKit 认证服务）
{
    prefix: '/api/erp/auth',
    upstream: process.env.UPSTREAM_URL || 'http://nexuskit:5000',
    rewrite: '/api/v1/auth',
    appCode: 'erp',
    publicPaths: ['/login', '/refresh'],
},
// 子系统自身的业务接口
{
    prefix: '/api/erp',
    upstream: process.env.ERP_URL || 'http://erp-service:8001',
    rewrite: '/api/v1',
    appCode: 'erp',
    publicPaths: [],
},
```

配置完成后重启网关即可生效。

---

## 四、用户登录

子系统用户通过**子系统专属登录路径**登录，网关自动识别系统归属并注入 `X-App-Code`：

**请求：**

```http
POST /api/erp/auth/login
Content-Type: application/json

{
  "username": "zhangsan",
  "password": "123456"
}
```

**响应：**

```json
{
  "code": 20000,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 1800,
    "token_type": "bearer",
    "user": {
      "id": 42,
      "username": "zhangsan",
      "email": "zhangsan@example.com",
      "is_active": true
    }
  }
}
```

> ⚠️ **登录前置条件**：用户必须已被管理员授权访问该系统，否则返回 `40301 APP_FORBIDDEN`。  
> 授权接口：`POST /api/identity/users/{user_id}/apps`

**刷新 Token：**

```http
POST /api/erp/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGci..."
}
```

---

## 五、请求鉴权

登录后每次请求在 Header 中携带 `Authorization`，**网关自动完成 Token 验证**，子系统无需关心 JWT 细节：

```http
GET /api/erp/products
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

网关验证通过后，向子系统转发请求时注入以下请求头：

| 请求头 | 说明 | 示例值 |
|--------|------|--------|
| `X-App-Code` | 当前系统标识（网关按路由自动设置，不信任客户端传入） | `erp` |
| `X-User-Id` | 当前登录用户的 ID | `42` |
| `X-User-Version` | Token 版本号（密码变更时递增，用于强制下线） | `1` |
| `X-NexusKit-Trace-Id` | 全链路追踪 ID，用于日志关联 | `nk-a1b2c3d4` |

**子系统只需从 Header 中读取 `X-User-Id` 即可识别当前用户，无需自行验证 Token。**

---

## 六、获取用户权限

### 6.1 role_only 模式 — 仅需角色编码

适用于：页面固定、只需粗粒度角色分流的系统。

```http
GET /api/identity/roles
Authorization: Bearer eyJhbGci...
```

响应：

```json
{
  "code": 20000,
  "data": ["erp:admin", "erp:viewer"]
}
```

### 6.2 full 模式 — 完整菜单树 + 按钮权限

适用于：需要动态渲染菜单、按钮级权限控制的完整后台系统。

```http
GET /api/identity/permissions
Authorization: Bearer eyJhbGci...
```

响应：

```json
{
  "code": 20000,
  "data": {
    "roles": ["erp:admin"],
    "menu_tree": [
      {
        "id": 1,
        "name": "采购管理",
        "path": "/purchase",
        "component": "views/purchase/index",
        "meta": {
          "title": "采购管理",
          "icon": "shopping-cart",
          "order": 1,
          "type": "C"
        },
        "children": [
          {
            "id": 2,
            "name": "采购订单",
            "path": "/purchase/orders",
            "component": "views/purchase/orders",
            "children": []
          }
        ]
      }
    ],
    "buttons": [
      "erp:purchase:create",
      "erp:purchase:export",
      "erp:purchase:delete"
    ]
  }
}
```

> 💡 `superAdmin` 角色用户将直接返回该系统全量菜单，跳过权限过滤。

---

## 七、服务间调用（后端对后端）

子系统后端主动调用 NexusKit 内部接口时，使用 **HMAC-SHA256 签名鉴权**（不走用户 Token）。

### 7.1 签名算法

```python
import hmac
import hashlib
import time
import secrets

APP_CODE   = "erp"                    # 在 NexusKit 注册的应用编码
APP_SECRET = "从管理员处获取的密钥"   # 保存在子系统 .env 中，切勿硬编码

# 每次请求动态生成
timestamp = str(int(time.time()))       # Unix 秒级时间戳
nonce     = secrets.token_hex(16)       # 随机字符串，防重放，每次请求必须不同

# 拼接待签名串（字段间用换行符分隔）
string_to_sign = f"{APP_CODE}\n{timestamp}\n{nonce}"

# HMAC-SHA256 签名
signature = hmac.new(
    APP_SECRET.encode("utf-8"),
    string_to_sign.encode("utf-8"),
    hashlib.sha256,
).hexdigest()
```

### 7.2 请求示例（Python）

```python
import httpx

headers = {
    "X-App-Code":  APP_CODE,
    "X-Timestamp": timestamp,
    "X-Nonce":     nonce,
    "X-Signature": signature,
}

async with httpx.AsyncClient() as client:
    # 查询用户信息
    resp = await client.get(
        "http://nexuskit:5000/api/v1/identity/internal/users/42",
        headers=headers,
    )
    user = resp.json()["data"]

    # 查询用户在本系统的角色
    resp = await client.get(
        "http://nexuskit:5000/api/v1/identity/internal/users/42/roles",
        params={"app_code": "erp"},
        headers=headers,
    )
    roles = resp.json()["data"]
```

### 7.3 可用内部接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/identity/internal/users/{user_id}` | 查询用户基本信息 |
| `GET` | `/api/v1/identity/internal/users/{user_id}/roles?app_code=erp` | 查询用户在指定系统的角色列表 |

### 7.4 安全约束

| 校验项 | 规则 |
|--------|------|
| 时间窗口 | 时间戳与服务器时钟偏差须 ≤ 300s，超时请求直接拒绝 |
| Nonce 防重放 | 同一 nonce 在 300s 窗口内只能使用一次（Redis 记录） |
| 签名校验 | HMAC-SHA256，大小写不敏感 |
| App 有效性 | app_code 必须已在 NexusKit 注册且 app_secret 有效 |

---

## 八、统一响应格式

所有接口均返回统一结构：

```json
{
  "code": 20000,
  "message": "ok",
  "data": { },
  "trace_id": "nk-a1b2c3d4"
}
```

### 8.1 常用业务码

| code | HTTP | 含义 | 前端处理建议 |
|------|------|------|------------|
| `20000` | 200 | 成功 | 正常处理 |
| `20100` | 201 | 创建成功 | 跳转详情或刷新列表 |
| `40100` | 401 | 未携带 Token | 跳转登录页 |
| `40101` | 401 | Token 已过期 | 用 refresh_token 自动换新 |
| `40103` | 401 | Token 已吊销（已登出/已刷新） | 跳转登录页 |
| `40104` | 401 | Token 版本失效（密码已修改） | 提示重新登录 |
| `40301` | 403 | 无该系统访问权限 | 提示"您没有访问该系统的权限" |
| `40302` | 403 | 账号已封禁 | 提示"账号已被禁用，请联系管理员" |
| `40303` | 403 | 会话已失效 | 跳转登录页 |
| `40305` | 403 | 账号已锁定（多次密码错误） | 提示锁定状态及解锁方式 |
| `40400` | 404 | 资源不存在 | 提示"内容不存在" |
| `40900` | 409 | 资源已存在（冲突） | 提示重复，用户修改后重试 |
| `42200` | 422 | 请求参数格式错误 | 展示字段级校验提示 |
| `42202` | 422 | 存在关联数据，不可删除 | 提示"请先移除关联数据" |
| `50000` | 500 | 服务器内部错误 | 展示友好提示，提供 trace_id 反馈 |

> 完整业务码定义参见 `sdk/nexuskit_sdk/codes.py`

---

## 九、常见问题

**Q：登录时报 40301，是什么原因？**  
A：该用户未被授权访问当前系统。请联系管理员执行：`POST /api/identity/users/{user_id}/apps`，将用户授权到对应的 `app_code`。

**Q：内部接口调用报 401 "请求已过期"？**  
A：服务器时钟与 NexusKit 服务器偏差超过 300s，请同步时钟（NTP）。

**Q：内部接口调用报 401 "Nonce 已使用"？**  
A：同一 nonce 不能重复使用。确保每次请求都调用 `secrets.token_hex(16)` 生成新的随机 nonce。

**Q：app_secret 泄露了怎么办？**  
A：立即联系管理员执行密钥重置：`POST /api/identity/apps/{app_code}/secret`。重置后旧密钥立即失效，子系统更新 `.env` 中的 `APP_SECRET` 后重启即可。

**Q：Token 过期后前端如何自动续期？**  
A：前端拦截 `code == 40101` 响应，自动调用 `POST /api/erp/auth/refresh` 换取新 Token，然后重试原请求。若 refresh_token 也失效（`40103`），则跳转登录页。
