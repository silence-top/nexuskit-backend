require('dotenv').config();
const fastify = require('fastify')({ logger: true });
const { v4: uuidv4 } = require('uuid');
const jwt = require('jsonwebtoken');

// --- 基础配置 ---
const PORT = parseInt(process.env.PORT || '8000', 10);
const JWT_SECRET = process.env.JWT_SECRET;
const INTERNAL_SECRET = process.env.INTERNAL_SECRET;
const REDIS_URL = process.env.REDIS_URL;

/**
 * 上游服务注册表
 * 新增系统只需在此添加一条记录：
 *   prefix      - 客户端请求路径前缀（同时作为 app_code 来源）
 *   upstream    - 上游服务地址，从环境变量读取
 *   rewrite     - 转发到上游时替换的前缀（按各服务实际路由调整）
 *   appCode     - 注入到 X-App-Code 头的业务系统标识
 *   public      - true 表示该 prefix 下所有路由免鉴权（如独立公开服务）
 */
const UPSTREAM_SERVICES = [
    {
        prefix: '/api/auth',
        upstream: process.env.UPSTREAM_URL || 'http://127.0.0.1:5000',
        rewrite: '/api/v1/auth',
        appCode: 'nexuskit',
    },
    {
        prefix: '/api/identity',
        upstream: process.env.UPSTREAM_URL || 'http://127.0.0.1:5000',
        rewrite: '/api/v1/identity',
        appCode: 'nexuskit',
    },
    // 示例：接入新系统
    {
        prefix: '/api/new-system',
        upstream: process.env.NEW_SYSTEM_URL || 'http://127.0.0.1:5001',
        rewrite: '/api/v1/new-system',
        appCode: 'new_system',
    },
];

/** 免鉴权白名单（精确路径或 ? 前缀匹配） */
const AUTH_WHITELIST = [
    '/api/auth/login',
    '/api/auth/register',
    '/api/auth/refresh',
];

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
    if (AUTH_WHITELIST.some(p => request.url === p || request.url.startsWith(p + '?'))) return;

    const authHeader = request.headers['authorization'];
    if (!authHeader?.startsWith('Bearer ')) {
        return reply.code(401).send({ code: 40100, message: 'Missing Token', traceId: request.traceId });
    }

    const token = authHeader.split(' ')[1];
    let decoded;
    try {
        decoded = jwt.verify(token, JWT_SECRET);
    } catch (err) {
        console.error('[NexusKit Gateway] JWT Verify Error:', err);
        return reply.code(401).send({ code: 40100, message: 'Invalid Token', traceId: request.traceId });
    }

    // AT 黑名单检查：拦截已刷新/已吸销的不过期 token
    if (decoded.jti) {
        const blacklisted = await fastify.redis.get(`auth:at:blacklist:${decoded.jti}`);
        if (blacklisted) {
            return reply.code(401).send({ code: 40100, message: 'Token Revoked', traceId: request.traceId });
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
 * 4. 构建代理的请求头重写逻辑
 */
function buildProxyHeaders(request, headers) {
    const newHeaders = {
        ...headers,
        'X-NexusKit-Trace-Id': request.traceId,
        'X-App-Code': request.appCode,
    };
    if (request.user) {
        newHeaders['X-Internal-Secret'] = INTERNAL_SECRET;
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
