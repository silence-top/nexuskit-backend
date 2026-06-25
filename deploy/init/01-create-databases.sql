-- deploy/init/01-create-databases.sql
-- PostgreSQL 容器启动时自动执行（仅首次初始化有效）
-- 创建 datahub-service 所需的独立数据库

SELECT 'CREATE DATABASE nexuskit_datahub OWNER nexus_admin'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'nexuskit_datahub')\gexec
