/*
 Navicat Premium Dump SQL

 Source Server         : nexus
 Source Server Type    : PostgreSQL
 Source Server Version : 160011 (160011)
 Source Host           : 127.0.0.1:5432
 Source Catalog        : nexuskit_auth
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 160011 (160011)
 File Encoding         : 65001

 Date: 10/06/2026 17:31:18
*/


-- ----------------------------
-- Sequence structure for auth_apps_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."auth_apps_id_seq";
CREATE SEQUENCE "public"."auth_apps_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for auth_departments_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."auth_departments_id_seq";
CREATE SEQUENCE "public"."auth_departments_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for auth_permissions_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."auth_permissions_id_seq";
CREATE SEQUENCE "public"."auth_permissions_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for auth_roles_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."auth_roles_id_seq";
CREATE SEQUENCE "public"."auth_roles_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for auth_users_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."auth_users_id_seq";
CREATE SEQUENCE "public"."auth_users_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Table structure for auth_apps
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_apps";
CREATE TABLE "public"."auth_apps" (
  "app_code" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "app_name" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "app_secret" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "id" int4 NOT NULL DEFAULT nextval('auth_apps_id_seq'::regclass),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  "deleted_at" timestamptz(6),
  "is_deleted" bool NOT NULL
)
;
COMMENT ON COLUMN "public"."auth_apps"."app_code" IS '应用唯一标识';
COMMENT ON COLUMN "public"."auth_apps"."id" IS '主键ID';
COMMENT ON COLUMN "public"."auth_apps"."created_at" IS '创建时间';
COMMENT ON COLUMN "public"."auth_apps"."updated_at" IS '最后更新时间';
COMMENT ON COLUMN "public"."auth_apps"."deleted_at" IS '删除时间(逻辑删除)';
COMMENT ON COLUMN "public"."auth_apps"."is_deleted" IS '是否已删除';

-- ----------------------------
-- Records of auth_apps
-- ----------------------------
INSERT INTO "public"."auth_apps" VALUES ('platform', 'NexusKit 核心管理平台', 'c5c5cb4dc5cb4ff49e37aeb81d1a8d02', 1, '2026-03-03 05:57:02.597511+00', '2026-03-03 05:57:02.597511+00', NULL, 'f');

-- ----------------------------
-- Table structure for auth_departments
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_departments";
CREATE TABLE "public"."auth_departments" (
  "dept_name" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "parent_id" int4,
  "sort" int4 NOT NULL,
  "leader" varchar(64) COLLATE "pg_catalog"."default",
  "phone" varchar(11) COLLATE "pg_catalog"."default",
  "email" varchar(128) COLLATE "pg_catalog"."default",
  "is_active" bool NOT NULL,
  "id" int4 NOT NULL DEFAULT nextval('auth_departments_id_seq'::regclass),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  "deleted_at" timestamptz(6),
  "is_deleted" bool NOT NULL
)
;
COMMENT ON COLUMN "public"."auth_departments"."dept_name" IS '部门名称';
COMMENT ON COLUMN "public"."auth_departments"."parent_id" IS '父部门ID';
COMMENT ON COLUMN "public"."auth_departments"."sort" IS '排序序号';
COMMENT ON COLUMN "public"."auth_departments"."leader" IS '部门负责人';
COMMENT ON COLUMN "public"."auth_departments"."phone" IS '联系电话';
COMMENT ON COLUMN "public"."auth_departments"."email" IS '部门邮箱';
COMMENT ON COLUMN "public"."auth_departments"."is_active" IS '部门状态';
COMMENT ON COLUMN "public"."auth_departments"."id" IS '主键ID';
COMMENT ON COLUMN "public"."auth_departments"."created_at" IS '创建时间';
COMMENT ON COLUMN "public"."auth_departments"."updated_at" IS '最后更新时间';
COMMENT ON COLUMN "public"."auth_departments"."deleted_at" IS '删除时间(逻辑删除)';
COMMENT ON COLUMN "public"."auth_departments"."is_deleted" IS '是否已删除';

-- ----------------------------
-- Records of auth_departments
-- ----------------------------
INSERT INTO "public"."auth_departments" VALUES ('总公司', NULL, 1, 'Admin', NULL, NULL, 't', 1, '2026-03-03 05:57:02.597511+00', '2026-03-03 05:57:02.597511+00', NULL, 'f');
INSERT INTO "public"."auth_departments" VALUES ('研发中心', 1, 1, NULL, NULL, NULL, 't', 2, '2026-03-03 05:57:02.597511+00', '2026-03-03 05:57:02.597511+00', NULL, 'f');

-- ----------------------------
-- Table structure for auth_permissions
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_permissions";
CREATE TABLE "public"."auth_permissions" (
  "app_code" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "parent_id" int4,
  "code" varchar(100) COLLATE "pg_catalog"."default" NOT NULL,
  "name" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "type" varchar(10) COLLATE "pg_catalog"."default" NOT NULL,
  "path" varchar(255) COLLATE "pg_catalog"."default",
  "component" varchar(255) COLLATE "pg_catalog"."default",
  "is_ext" bool NOT NULL DEFAULT false,
  "ext_url" varchar(512) COLLATE "pg_catalog"."default",
  "icon" varchar(100) COLLATE "pg_catalog"."default",
  "sort" int4 NOT NULL DEFAULT 0,
  "is_visible" bool NOT NULL DEFAULT true,
  "is_active" bool NOT NULL DEFAULT true,
  "props" text COLLATE "pg_catalog"."default",
  "synced_at" timestamptz(6),
  "id" int4 NOT NULL DEFAULT nextval('auth_permissions_id_seq'::regclass),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  "deleted_at" timestamptz(6),
  "is_deleted" bool NOT NULL
)
;
COMMENT ON COLUMN "public"."auth_permissions"."app_code" IS '所属子系统Key';
COMMENT ON COLUMN "public"."auth_permissions"."parent_id" IS '父级ID';
COMMENT ON COLUMN "public"."auth_permissions"."code" IS '权限唯一标识(如 user:list)';
COMMENT ON COLUMN "public"."auth_permissions"."name" IS '权限/菜单名称';
COMMENT ON COLUMN "public"."auth_permissions"."type" IS '类型: M目录, C菜单, F功能, L外链';
COMMENT ON COLUMN "public"."auth_permissions"."path" IS '前端路由地址';
COMMENT ON COLUMN "public"."auth_permissions"."component" IS '前端组件路径';
COMMENT ON COLUMN "public"."auth_permissions"."is_ext" IS '是否为外链';
COMMENT ON COLUMN "public"."auth_permissions"."ext_url" IS '外链跳转地址';
COMMENT ON COLUMN "public"."auth_permissions"."icon" IS '菜单图标';
COMMENT ON COLUMN "public"."auth_permissions"."sort" IS '排序序号';
COMMENT ON COLUMN "public"."auth_permissions"."is_visible" IS '菜单是否可见';
COMMENT ON COLUMN "public"."auth_permissions"."is_active" IS '是否启用状态';
COMMENT ON COLUMN "public"."auth_permissions"."props" IS '多端适配扩展配置(JSON格式)';
COMMENT ON COLUMN "public"."auth_permissions"."synced_at" IS '最近一次子系统同步时间戳';
COMMENT ON COLUMN "public"."auth_permissions"."id" IS '主键ID';
COMMENT ON COLUMN "public"."auth_permissions"."created_at" IS '创建时间';
COMMENT ON COLUMN "public"."auth_permissions"."updated_at" IS '最后更新时间';
COMMENT ON COLUMN "public"."auth_permissions"."deleted_at" IS '删除时间(逻辑删除)';
COMMENT ON COLUMN "public"."auth_permissions"."is_deleted" IS '是否已删除';

-- ----------------------------
-- Records of auth_permissions
-- ----------------------------
INSERT INTO "public"."auth_permissions" VALUES ('platform', NULL, 'sys:mng', '系统管理', 'M', NULL, NULL, 'f', NULL, 'setting', 100, 't', 't', NULL, NULL, 1, '2026-03-03 05:57:02.597511+00', '2026-03-03 05:57:02.597511+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('platform', 1, 'sys:user:view', '用户管理', 'C', '/system/user', 'system/user/index', 'f', NULL, 'user', 1, 't', 't', NULL, NULL, 2, '2026-03-03 05:57:02.597511+00', '2026-03-03 05:57:02.597511+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('platform', 2, 'sys:user:add', '新增用户', 'F', NULL, NULL, 'f', NULL, NULL, 1, 't', 't', NULL, NULL, 3, '2026-03-03 05:57:02.597511+00', '2026-03-03 05:57:02.597511+00', NULL, 'f');

-- ----------------------------
-- Table structure for auth_role_permissions_link
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_role_permissions_link";
CREATE TABLE "public"."auth_role_permissions_link" (
  "role_id" int4 NOT NULL,
  "permission_id" int4 NOT NULL
)
;

-- ----------------------------
-- Records of auth_role_permissions_link
-- ----------------------------
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 1);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 2);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 3);

-- ----------------------------
-- Table structure for auth_roles
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_roles";
CREATE TABLE "public"."auth_roles" (
  "app_code" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "role_name" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "role_code" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "synced_at" timestamptz(6),
  "id" int4 NOT NULL DEFAULT nextval('auth_roles_id_seq'::regclass),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  "deleted_at" timestamptz(6),
  "is_deleted" bool NOT NULL
)
;
COMMENT ON COLUMN "public"."auth_roles"."app_code" IS '所属应用编码';
COMMENT ON COLUMN "public"."auth_roles"."role_name" IS '角色名称';
COMMENT ON COLUMN "public"."auth_roles"."role_code" IS '角色唯一编码';
COMMENT ON COLUMN "public"."auth_roles"."synced_at" IS '最近一次子系统同步时间戳';
COMMENT ON COLUMN "public"."auth_roles"."id" IS '主键ID';
COMMENT ON COLUMN "public"."auth_roles"."created_at" IS '创建时间';
COMMENT ON COLUMN "public"."auth_roles"."updated_at" IS '最后更新时间';
COMMENT ON COLUMN "public"."auth_roles"."deleted_at" IS '删除时间(逻辑删除)';
COMMENT ON COLUMN "public"."auth_roles"."is_deleted" IS '是否已删除';

-- ----------------------------
-- Records of auth_roles
-- ----------------------------
INSERT INTO "public"."auth_roles" VALUES ('platform', '超级管理员', 'super_admin', NULL, 1, '2026-03-03 05:57:02.597511+00', '2026-03-03 05:57:02.597511+00', NULL, 'f');

-- ----------------------------
-- Table structure for auth_user_roles_link
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_user_roles_link";
CREATE TABLE "public"."auth_user_roles_link" (
  "user_id" int4 NOT NULL,
  "role_id" int4 NOT NULL
)
;

-- ----------------------------
-- Records of auth_user_roles_link
-- ----------------------------
INSERT INTO "public"."auth_user_roles_link" VALUES (1, 1);

-- ----------------------------
-- Table structure for auth_users
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_users";
CREATE TABLE "public"."auth_users" (
  "username" varchar(50) COLLATE "pg_catalog"."default" NOT NULL,
  "email" varchar(100) COLLATE "pg_catalog"."default",
  "phone" varchar(20) COLLATE "pg_catalog"."default",
  "phone_code" varchar(10) COLLATE "pg_catalog"."default" NOT NULL DEFAULT '86'::character varying,
  "hashed_password" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "mfa_secret" varchar(100) COLLATE "pg_catalog"."default",
  "is_mfa_enabled" bool NOT NULL DEFAULT false,
  "version" int4 NOT NULL DEFAULT 1,
  "is_active" bool NOT NULL DEFAULT true,
  "dept_id" int4,
  "id" int4 NOT NULL DEFAULT nextval('auth_users_id_seq'::regclass),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  "deleted_at" timestamptz(6),
  "is_deleted" bool NOT NULL
)
;
COMMENT ON COLUMN "public"."auth_users"."id" IS '主键ID';
COMMENT ON COLUMN "public"."auth_users"."created_at" IS '创建时间';
COMMENT ON COLUMN "public"."auth_users"."updated_at" IS '最后更新时间';
COMMENT ON COLUMN "public"."auth_users"."deleted_at" IS '删除时间(逻辑删除)';
COMMENT ON COLUMN "public"."auth_users"."is_deleted" IS '是否已删除';

-- ----------------------------
-- Records of auth_users
-- ----------------------------
INSERT INTO "public"."auth_users" VALUES ('admin', 'admin@nexuskit.com', NULL, '86', '$argon2id$v=19$m=65536,t=3,p=4$BSDknFOKUar13jsnBCAkRA$O4P5IdbnkF8jWRmtxyDtY4VtM/Edp5xeiOJnGk+fU6E', NULL, 'f', 1, 't', NULL, 1, '2026-03-03 05:57:02.597511+00', '2026-03-03 05:57:02.597511+00', NULL, 'f');

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_apps_id_seq"
OWNED BY "public"."auth_apps"."id";
SELECT setval('"public"."auth_apps_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_departments_id_seq"
OWNED BY "public"."auth_departments"."id";
SELECT setval('"public"."auth_departments_id_seq"', 2, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_permissions_id_seq"
OWNED BY "public"."auth_permissions"."id";
SELECT setval('"public"."auth_permissions_id_seq"', 3, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_roles_id_seq"
OWNED BY "public"."auth_roles"."id";
SELECT setval('"public"."auth_roles_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_users_id_seq"
OWNED BY "public"."auth_users"."id";
SELECT setval('"public"."auth_users_id_seq"', 1, true);

-- ----------------------------
-- Indexes structure for table auth_apps
-- ----------------------------
CREATE UNIQUE INDEX "ix_auth_apps_app_code" ON "public"."auth_apps" USING btree (
  "app_code" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table auth_apps
-- ----------------------------
ALTER TABLE "public"."auth_apps" ADD CONSTRAINT "auth_apps_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table auth_departments
-- ----------------------------
ALTER TABLE "public"."auth_departments" ADD CONSTRAINT "auth_departments_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table auth_permissions
-- ----------------------------
CREATE INDEX "ix_auth_permissions_app_code" ON "public"."auth_permissions" USING btree (
  "app_code" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE UNIQUE INDEX "ix_auth_permissions_code" ON "public"."auth_permissions" USING btree (
  "code" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table auth_permissions
-- ----------------------------
ALTER TABLE "public"."auth_permissions" ADD CONSTRAINT "auth_permissions_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table auth_role_permissions_link
-- ----------------------------
ALTER TABLE "public"."auth_role_permissions_link" ADD CONSTRAINT "auth_role_permissions_link_pkey" PRIMARY KEY ("role_id", "permission_id");

-- ----------------------------
-- Indexes structure for table auth_roles
-- ----------------------------
CREATE INDEX "ix_auth_roles_app_code" ON "public"."auth_roles" USING btree (
  "app_code" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE UNIQUE INDEX "ix_auth_roles_role_code" ON "public"."auth_roles" USING btree (
  "role_code" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table auth_roles
-- ----------------------------
ALTER TABLE "public"."auth_roles" ADD CONSTRAINT "auth_roles_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table auth_user_roles_link
-- ----------------------------
ALTER TABLE "public"."auth_user_roles_link" ADD CONSTRAINT "auth_user_roles_link_pkey" PRIMARY KEY ("user_id", "role_id");

-- ----------------------------
-- Indexes structure for table auth_users
-- ----------------------------
CREATE UNIQUE INDEX "ix_auth_users_email" ON "public"."auth_users" USING btree (
  "email" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE UNIQUE INDEX "ix_auth_users_phone" ON "public"."auth_users" USING btree (
  "phone" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE UNIQUE INDEX "ix_auth_users_username" ON "public"."auth_users" USING btree (
  "username" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table auth_users
-- ----------------------------
ALTER TABLE "public"."auth_users" ADD CONSTRAINT "auth_users_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table auth_departments
-- ----------------------------
ALTER TABLE "public"."auth_departments" ADD CONSTRAINT "auth_departments_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "public"."auth_departments" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table auth_permissions
-- ----------------------------
ALTER TABLE "public"."auth_permissions" ADD CONSTRAINT "auth_permissions_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "public"."auth_permissions" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table auth_role_permissions_link
-- ----------------------------
ALTER TABLE "public"."auth_role_permissions_link" ADD CONSTRAINT "auth_role_permissions_link_permission_id_fkey" FOREIGN KEY ("permission_id") REFERENCES "public"."auth_permissions" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."auth_role_permissions_link" ADD CONSTRAINT "auth_role_permissions_link_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."auth_roles" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table auth_roles
-- ----------------------------
ALTER TABLE "public"."auth_roles" ADD CONSTRAINT "auth_roles_app_code_fkey" FOREIGN KEY ("app_code") REFERENCES "public"."auth_apps" ("app_code") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table auth_user_roles_link
-- ----------------------------
ALTER TABLE "public"."auth_user_roles_link" ADD CONSTRAINT "auth_user_roles_link_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."auth_roles" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."auth_user_roles_link" ADD CONSTRAINT "auth_user_roles_link_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."auth_users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table auth_users
-- ----------------------------
ALTER TABLE "public"."auth_users" ADD CONSTRAINT "auth_users_dept_id_fkey" FOREIGN KEY ("dept_id") REFERENCES "public"."auth_departments" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
