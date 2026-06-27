require('dotenv').config();
const fastify = require('fastify')({ logger: true });
const { v4: uuidv4 } = require('uuid');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

// --- 基础配置 ---
const PORT = parseInt(process.env.PORT || '8000', 10);
const JWT_SECRET = process.env.JWT_SECRET;
const INTERNAL_SECRET = process.env.INTERNAL_SECRET;
const REDIS_URL = process.env.REDIS_URL;

/**
 * 业务码常量表（与后端 nexuskit_sdk/codes.py 中的 BizCode 保持一致）
 * 编码规则： HHHSS  HHH=HTTP状态码  SS=业务子码
 */
const BizCode = {
    // 2xx 成功
    SUCCESS:               20000,
    CREATED:               20100,

    // 400 请求参数错误
    BAD_REQUEST:           40000,
    PARAM_MISSING:         40001,
    PARAM_INVALID:         40002,
    PARAM_TOO_LONG:        40003,
    IMPORT_ERROR:          40004,

    // 401 认证失败（需重新登录）
    UNAUTHORIZED:          40100,
    TOKEN_EXPIRED:         40101,
    TOKEN_INVALID:         40102,
    TOKEN_REVOKED:         40103,
    TOKEN_VERSION:         40104,
    TOKEN_MISSING:         40105,
    TOKEN_MISUSE:          40106,
    USER_NOT_FOUND:        40107,
    INVALID_CREDS:         40108,
    SIGN_INVALID:          40109,
    MFA_REQUIRED:          40110,
    MFA_INVALID:           40111,

    // 403 权限不足（已认证但无权操作）
    FORBIDDEN:             40300,
    APP_FORBIDDEN:         40301,  // 无该系统访问权限（多系统隔离）
    USER_BANNED:           40302,
    SESSION_EXPIRED:       40303,
    DATA_SCOPE:            40304,
    ACCOUNT_LOCKED:        40305,
    ACCOUNT_EXPIRED:       40306,

    // 404 资源不存在
    NOT_FOUND:             40400,

    // 405 方法不允许
    METHOD_NOT_ALLOWED:    40500,

    // 409 资源冲突
    CONFLICT:              40900,
    USER_EXISTS:           40901,
    ROLE_EXISTS:           40902,
    DEPT_EXISTS:           40903,
    MENU_EXISTS:           40904,

    // 410 资源已删除
    GONE:                  41000,

    // 413 请求体/文件过大
    PAYLOAD_TOO_LARGE:     41300,
    FILE_TOO_LARGE:        41301,

    // 415 媒体类型不支持
    UNSUPPORTED_MEDIA_TYPE: 41500,

    // 422 参数校验失败
    UNPROCESSABLE:         42200,
    BUSI_STATUS:           42201,
    RELATION_EXISTS:       42202,

    // 429 限流
    TOO_MANY:              42900,
    REFRESH_CONFLICT:      42901,
    LOGIN_TOO_MANY:        42902,

    // 500 服务器内部错误
    INTERNAL_ERROR:        50000,
    DB_ERROR:              50001,
    CACHE_ERROR:           50002,
    IO_ERROR:              50003,

    // 501 功能未实现
    NOT_IMPLEMENTED:       50100,

    // 502/503/504 网关类
    BAD_GATEWAY:           50200,
    UNAVAILABLE:           50300,
    GATEWAY_TIMEOUT:       50400,
};

/**
 * 上游服务注册表
 * 新增系统只需在此添加一条记录，无需改动其他代码：
 *
 *   prefix       - 客户端请求路径前缀，网关据此识别 appCode（不信任客户端传入）
 *   upstream     - 上游服务地址，从环境变量读取
 *   rewrite      - 转发到上游时替换的前缀（按各服务实际路由调整）
 *   appCode      - 注入到 X-App-Code 头的业务系统标识，后端据此做系统隔离
 *   publicPaths  - 该系统下免鉴权的相对路径列表（相对于 prefix），支持精确匹配和 ? 参数
 *
 * ── 多系统登录设计说明 ──────────────────────────────────────────────────
 * 每个系统通过独立的 auth 前缀区分登录目标，网关自动识别 appCode 并注入请求头。
 * 后端同一套代码，根据 X-App-Code 查询用户在对应系统的角色，实现系统隔离。
 *
 * 示例：
 *   nexuskit 用户  → POST /api/auth/login          → X-App-Code: nexuskit
 *   ERP 用户       → POST /api/erp/auth/login       → X-App-Code: erp
 *   CRM 用户       → POST /api/crm/auth/login       → X-App-Code: crm
 * ────────────────────────────────────────────────────────────────────────
 */
const UPSTREAM_SERVICES = [
    // ── nexuskit 平台 ──────────────────────────────────────────────────────
    {
        prefix: '/api/auth',
        upstream: process.env.UPSTREAM_URL || 'http://127.0.0.1:5000',
        rewrite: '/api/v1/auth',
        appCode: 'nexuskit',
        publicPaths: ['/login', '/register', '/refresh'],
    },
    {
        prefix: '/api/identity',
        upstream: process.env.UPSTREAM_URL || 'http://127.0.0.1:5000',
        rewrite: '/api/v1/identity',
        appCode: 'nexuskit',
        publicPaths: [],
    },
    // ── datahub-service（数据中心：设备管理 + 切片上传）──────────────────
    {
        prefix: '/api/datahub/auth',
        upstream: process.env.UPSTREAM_URL || 'http://127.0.0.1:5000',
        rewrite: '/api/v1/auth',
        appCode: 'datahub',
        publicPaths: ['/login', '/register', '/refresh'],
    },
    {
        prefix: '/api/datahub',
        upstream: process.env.DATAHUB_URL || 'http://127.0.0.1:6000',
        rewrite: '/api/v1',
        appCode: 'datahub',
        publicPaths: ['/devices/scanner/device'],  // 扫描仪查询设备信息，免 JWT
    },
    // ── 示例：接入 ERP 系统（独立登录入口，复用同一套后端认证服务）────────
    // {
    //     prefix: '/api/erp/auth',
    //     upstream: process.env.UPSTREAM_URL || 'http://127.0.0.1:5000',
    //     rewrite: '/api/v1/auth',          // 复用同一后端认证接口
    //     appCode: 'erp',                   // 网关注入 X-App-Code: erp
    //     publicPaths: ['/login', '/refresh'],
    // },
    // {
    //     prefix: '/api/erp',
    //     upstream: process.env.ERP_URL || 'http://127.0.0.1:5002',
    //     rewrite: '/api/v1',
    //     appCode: 'erp',
    //     publicPaths: [],
    // },
];

/**
 * 动态白名单：从 UPSTREAM_SERVICES 的 publicPaths 自动生成，无需手动维护。
 * 匹配规则：精确匹配 或 以 "?" 开头的查询参数（如 /login?redirect=xxx）
 */
function isPublicPath(url) {
    return UPSTREAM_SERVICES.some(svc =>
        (svc.publicPaths || []).some(p => {
            const full = svc.prefix + p;
            return url === full
                || url.startsWith(full + '?')
                || url.startsWith(full + '/');  // 支持路径参数前缀匹配
        })
    );
}

const ORIGIN_RAW = process.env.ORIGIN || '*';
// '*' 时回退为 true（回显请求 Origin 头），因为 CORS 规范禁止 origin:'*' + credentials:true
const ORIGIN = ORIGIN_RAW === '*' ? true : ORIGIN_RAW.split(',').map(s => s.trim()).filter(Boolean);

if (!JWT_SECRET || !INTERNAL_SECRET) {
    console.error('[NexusKit Gateway] FATAL: JWT_SECRET 和 INTERNAL_SECRET 环境变量未设置');
    process.exit(1);
}
if (!REDIS_URL) {
    console.error('[NexusKit Gateway] FATAL: REDIS_URL 环境变量未设置');
    process.exit(1);
}

// 注册 Redis——仅用于 AT 黑名单查询
fastify.register(require('@fastify/redis'), { url: REDIS_URL, closeClient: true });

// 注册 CORS——允许前端跨域访问
fastify.register(require('@fastify/cors'), {
    origin: ORIGIN,            // '*' → true（回显Origin头）；生产环境设为逗号分隔的域名列表
    credentials: true,     // 允许携带 Cookie / Authorization 头
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-NexusKit-Trace-Id'],
    exposedHeaders: ['X-NexusKit-Trace-Id'],
});


/**
 * 1. 全局 Trace ID 注入
 */
fastify.addHook('onRequest', async (request) => {
    const incomingTrace = request.headers['x-nexuskit-trace-id'];
    request.traceId = incomingTrace || `nk-${uuidv4().split('-')[0]}`;
    // app_code 从路由表自动识别，不信任客户端传入
    const matched = UPSTREAM_SERVICES.find(s => request.url.startsWith(s.prefix));
    request.appCode = matched ? matched.appCode : 'unknown-app';
});

/**
 * 2. 鉴权：JWT 签名验证 + AT 黑名单检查
 */
fastify.addHook('preHandler', async (request, reply) => {
    if (isPublicPath(request.url)) return;

    const authHeader = request.headers['authorization'];
    if (!authHeader?.startsWith('Bearer ')) {
        return reply.code(401).send({ code: BizCode.UNAUTHORIZED, message: 'Missing Token', traceId: request.traceId });
    }

    const token = authHeader.split(' ')[1];
    let decoded;
    try {
        decoded = jwt.verify(token, JWT_SECRET);
    } catch (err) {
        console.error('[NexusKit Gateway] JWT Verify Error:', err);
        const code = err.name === 'TokenExpiredError' ? BizCode.TOKEN_EXPIRED : BizCode.TOKEN_INVALID;
        return reply.code(401).send({ code, message: err.name === 'TokenExpiredError' ? 'Token Expired' : 'Invalid Token', traceId: request.traceId });
    }

    // AT 黑名单检查：拦截已刷新/已吸销的不过期 token
    if (decoded.jti) {
        const blacklisted = await fastify.redis.get(`auth:at:blacklist:${decoded.jti}`);
        if (blacklisted) {
            return reply.code(403).send({ code: BizCode.SESSION_EXPIRED, message: 'Token Revoked', traceId: request.traceId });
        }
    }

    request.user = decoded;
});

/**
 * 3. 响应拦截：注入 Trace ID
 */
fastify.addHook('onSend', async (request, reply, payload) => {
    reply.header('x-nexuskit-trace-id', request.traceId);
    return payload;
});

/**
 * 生成网关 → 后端的内部信任令牌（HMAC-SHA256）
 * 格式：{timestamp}.{hmac}   timestamp = Unix 秒
 * 后端验证：签名匹配 + 时间戳在 ±30s 窗口内（防重放）
 */
function buildGatewayToken() {
    const ts = Math.floor(Date.now() / 1000).toString();
    const sig = crypto.createHmac('sha256', INTERNAL_SECRET).update(ts).digest('hex');
    return `${ts}.${sig}`;
}

/**
 * 4. 构建代理的请求头重写逻辑
 */
function buildProxyHeaders(request, headers) {
    const newHeaders = {
        ...headers,
        'X-NexusKit-Trace-Id': request.traceId,
        'X-App-Code': request.appCode,
        'X-Gateway-Token': buildGatewayToken(),  // 每次请求动态签名，防重放
    };
    if (request.user) {
        newHeaders['X-User-Id'] = request.user.sub.toString();
        if (request.user.ver !== undefined) {
            newHeaders['X-User-Version'] = request.user.ver.toString();
        }
        if (request.user.jti !== undefined) {
            newHeaders['X-User-Jti'] = request.user.jti;
        }
    }
    return newHeaders;
}

/**
 * 5. 从注册表动态注册代理路由
 */
for (const svc of UPSTREAM_SERVICES) {
    fastify.register(require('@fastify/http-proxy'), {
        upstream: svc.upstream,
        prefix: svc.prefix,
        rewritePrefix: svc.rewrite,
        replyOptions: {
            rewriteRequestHeaders: (request, headers) => buildProxyHeaders(request, headers),
        },
    });
    fastify.log.info(`[Gateway] 已注册代理: ${svc.prefix} → ${svc.upstream}${svc.rewrite} (appCode=${svc.appCode})`);
}

const start = async () => {
    try {
        await fastify.listen({ port: PORT, host: '0.0.0.0' });
        fastify.log.info('NexusKit Gateway Ready');
    } catch (err) {
        fastify.log.error(err);
        process.exit(1);
    }
};

// Graceful shutdown
const shutdown = async (signal) => {
    fastify.log.info(`Received ${signal}, shutting down gracefully...`);
    await fastify.close();
    fastify.log.info('Gateway stopped');
    process.exit(0);
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

start();
