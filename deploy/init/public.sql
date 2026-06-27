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

 Date: 24/06/2026 17:43:08
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
-- Sequence structure for auth_user_apps_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."auth_user_apps_id_seq";
CREATE SEQUENCE "public"."auth_user_apps_id_seq" 
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
-- Table structure for alembic_version
-- ----------------------------
DROP TABLE IF EXISTS "public"."alembic_version";
CREATE TABLE "public"."alembic_version" (
  "version_num" varchar(32) COLLATE "pg_catalog"."default" NOT NULL
)
;

-- ----------------------------
-- Records of alembic_version
-- ----------------------------
INSERT INTO "public"."alembic_version" VALUES ('b4d8f2e91a05');

-- ----------------------------
-- Table structure for auth_apps
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_apps";
CREATE TABLE "public"."auth_apps" (
  "app_code" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "app_name" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "app_secret" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "perm_mode" varchar(16) COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'full'::character varying,
  "description" varchar(255) COLLATE "pg_catalog"."default",
  "id" int4 NOT NULL DEFAULT nextval('auth_apps_id_seq'::regclass),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  "deleted_at" timestamptz(6),
  "is_deleted" bool NOT NULL
)
;
COMMENT ON COLUMN "public"."auth_apps"."app_code" IS 'app key';
COMMENT ON COLUMN "public"."auth_apps"."perm_mode" IS '权限模式: full=完整RBAC | role_only=仅角色 | passthru=SSO直通';
COMMENT ON COLUMN "public"."auth_apps"."description" IS '系统描述';
COMMENT ON COLUMN "public"."auth_apps"."id" IS 'PK';
COMMENT ON COLUMN "public"."auth_apps"."created_at" IS 'created';
COMMENT ON COLUMN "public"."auth_apps"."updated_at" IS 'updated';
COMMENT ON COLUMN "public"."auth_apps"."deleted_at" IS 'soft delete';
COMMENT ON COLUMN "public"."auth_apps"."is_deleted" IS 'deleted flag';

-- ----------------------------
-- Records of auth_apps
-- ----------------------------
INSERT INTO "public"."auth_apps" VALUES ('nexuskit', 'NexusKit 核心管理平台', '80c2e5ae94e84f8e976fc1068b55a403', 'full', NULL, 1, '2026-06-23 00:52:21.559555+00', '2026-06-23 00:52:21.559555+00', NULL, 'f');

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
COMMENT ON COLUMN "public"."auth_departments"."dept_name" IS 'dept name';
COMMENT ON COLUMN "public"."auth_departments"."parent_id" IS 'parent dept';
COMMENT ON COLUMN "public"."auth_departments"."sort" IS 'sort order';
COMMENT ON COLUMN "public"."auth_departments"."leader" IS 'dept leader';
COMMENT ON COLUMN "public"."auth_departments"."phone" IS 'phone';
COMMENT ON COLUMN "public"."auth_departments"."email" IS 'email';
COMMENT ON COLUMN "public"."auth_departments"."is_active" IS 'status';
COMMENT ON COLUMN "public"."auth_departments"."id" IS 'PK';
COMMENT ON COLUMN "public"."auth_departments"."created_at" IS 'created';
COMMENT ON COLUMN "public"."auth_departments"."updated_at" IS 'updated';
COMMENT ON COLUMN "public"."auth_departments"."deleted_at" IS 'soft delete';
COMMENT ON COLUMN "public"."auth_departments"."is_deleted" IS 'deleted flag';

-- ----------------------------
-- Records of auth_departments
-- ----------------------------
INSERT INTO "public"."auth_departments" VALUES ('总公司', NULL, 1, 'Admin', NULL, NULL, 't', 1, '2026-06-23 00:52:21.559555+00', '2026-06-23 00:52:21.559555+00', NULL, 'f');
INSERT INTO "public"."auth_departments" VALUES ('研发中心', 1, 1, NULL, NULL, NULL, 't', 2, '2026-06-23 00:52:21.559555+00', '2026-06-23 00:52:21.559555+00', NULL, 'f');

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
COMMENT ON COLUMN "public"."auth_permissions"."app_code" IS 'app key';
COMMENT ON COLUMN "public"."auth_permissions"."parent_id" IS 'parent id';
COMMENT ON COLUMN "public"."auth_permissions"."code" IS 'perm code';
COMMENT ON COLUMN "public"."auth_permissions"."name" IS 'perm name';
COMMENT ON COLUMN "public"."auth_permissions"."type" IS 'M=dir, C=menu, F=btn, L=link';
COMMENT ON COLUMN "public"."auth_permissions"."path" IS 'frontend route';
COMMENT ON COLUMN "public"."auth_permissions"."component" IS 'frontend component';
COMMENT ON COLUMN "public"."auth_permissions"."is_ext" IS 'is external';
COMMENT ON COLUMN "public"."auth_permissions"."ext_url" IS 'ext url';
COMMENT ON COLUMN "public"."auth_permissions"."icon" IS 'icon';
COMMENT ON COLUMN "public"."auth_permissions"."sort" IS 'sort order';
COMMENT ON COLUMN "public"."auth_permissions"."is_visible" IS 'visible';
COMMENT ON COLUMN "public"."auth_permissions"."is_active" IS 'active';
COMMENT ON COLUMN "public"."auth_permissions"."props" IS 'JSON props';
COMMENT ON COLUMN "public"."auth_permissions"."synced_at" IS '最近一次子系统同步时间戳';
COMMENT ON COLUMN "public"."auth_permissions"."id" IS 'PK';
COMMENT ON COLUMN "public"."auth_permissions"."created_at" IS 'created';
COMMENT ON COLUMN "public"."auth_permissions"."updated_at" IS 'updated';
COMMENT ON COLUMN "public"."auth_permissions"."deleted_at" IS 'soft delete';
COMMENT ON COLUMN "public"."auth_permissions"."is_deleted" IS 'deleted flag';

-- ----------------------------
-- Records of auth_permissions
-- ----------------------------
INSERT INTO "public"."auth_permissions" VALUES ('nexuskit', 2, 'sys:user:add', '新增用户', 'F', NULL, NULL, 'f', NULL, NULL, 1, 't', 't', NULL, NULL, 3, '2026-06-23 00:52:21.559555+00', '2026-06-23 00:52:21.559555+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('nexuskit', NULL, 'sys:system:manage', '系统管理', 'M', '/system', NULL, 'f', NULL, 'icon-park-outline:setting', 1, 't', 't', NULL, NULL, 1, '2026-06-23 00:52:21.559555+00', '2026-06-24 01:06:55.908884+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('nexuskit', 1, 'sys:role:manage', '角色管理', 'C', '/system/role', '/setting/roles/index.vue', 'f', NULL, 'carbon:user-role', 1, 't', 't', NULL, NULL, 4, '2026-06-23 09:17:53+00', '2026-06-24 01:07:24.081636+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('nexuskit', 1, 'sys:user:manage', '用户管理', 'C', '/system/user', '/setting/account/index.vue', 'f', NULL, 'icon-park-outline:every-user', 1, 't', 't', NULL, NULL, 2, '2026-06-23 00:52:21.559555+00', '2026-06-24 01:07:44.333004+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('nexuskit', 1, 'sys:dept:manage', '部门管理', 'C', '/system/dept', '/setting/dept/index.vue', 'f', NULL, 'carbon:column-dependency', 1, 't', 't', NULL, NULL, 5, '2026-06-23 09:29:44+00', '2026-06-24 01:07:58.842863+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('nexuskit', NULL, 'sys:dev:manage', '开发管理', 'M', '/dev', NULL, 'f', NULL, 'carbon:development', 1, 't', 't', NULL, NULL, 6, '2026-06-23 09:31:03+00', '2026-06-24 01:08:30.703775+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('nexuskit', 6, 'sys:menu:manage', '菜单管理', 'C', '/dev/menu', '/system/menu/index.vue', 'f', NULL, 'icon-park-outline:application-menu', 1, 't', 't', NULL, NULL, 7, '2026-06-23 09:32:08+00', '2026-06-24 01:08:46.049337+00', NULL, 'f');
INSERT INTO "public"."auth_permissions" VALUES ('nexuskit', 6, 'sys:app:manage', '应用管理', 'C', '/system/app', '/system/app/index.vue', 'f', NULL, 'icon-park-outline:app-store', 1, 't', 't', NULL, NULL, 8, '2026-06-23 09:42:45+00', '2026-06-24 01:09:06.915256+00', NULL, 'f');

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
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 3);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 1);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 6);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 2);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 4);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 5);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 7);
INSERT INTO "public"."auth_role_permissions_link" VALUES (1, 8);

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
COMMENT ON COLUMN "public"."auth_roles"."app_code" IS 'app code';
COMMENT ON COLUMN "public"."auth_roles"."role_name" IS 'role name';
COMMENT ON COLUMN "public"."auth_roles"."role_code" IS 'role code';
COMMENT ON COLUMN "public"."auth_roles"."synced_at" IS '最近一次子系统同步时间戳';
COMMENT ON COLUMN "public"."auth_roles"."id" IS 'PK';
COMMENT ON COLUMN "public"."auth_roles"."created_at" IS 'created';
COMMENT ON COLUMN "public"."auth_roles"."updated_at" IS 'updated';
COMMENT ON COLUMN "public"."auth_roles"."deleted_at" IS 'soft delete';
COMMENT ON COLUMN "public"."auth_roles"."is_deleted" IS 'deleted flag';

-- ----------------------------
-- Records of auth_roles
-- ----------------------------
INSERT INTO "public"."auth_roles" VALUES ('nexuskit', '超级管理员', 'super_admin', NULL, 1, '2026-06-23 00:52:21.559555+00', '2026-06-23 00:52:21.559555+00', NULL, 'f');

-- ----------------------------
-- Table structure for auth_user_apps
-- ----------------------------
DROP TABLE IF EXISTS "public"."auth_user_apps";
CREATE TABLE "public"."auth_user_apps" (
  "user_id" int4 NOT NULL,
  "app_code" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "is_active" bool NOT NULL DEFAULT true,
  "expired_at" timestamptz(6),
  "created_at" timestamptz(6) NOT NULL DEFAULT '2026-06-23 05:13:31.17155+00'::timestamp with time zone,
  "id" int4 NOT NULL DEFAULT nextval('auth_user_apps_id_seq'::regclass),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  "deleted_at" timestamptz(6),
  "is_deleted" bool NOT NULL
)
;
COMMENT ON COLUMN "public"."auth_user_apps"."user_id" IS 'user id';
COMMENT ON COLUMN "public"."auth_user_apps"."app_code" IS 'app code';
COMMENT ON COLUMN "public"."auth_user_apps"."is_active" IS '是否启用';
COMMENT ON COLUMN "public"."auth_user_apps"."expired_at" IS '过期时间，NULL=永久';
COMMENT ON COLUMN "public"."auth_user_apps"."created_at" IS '授权时间';
COMMENT ON COLUMN "public"."auth_user_apps"."id" IS 'PK';
COMMENT ON COLUMN "public"."auth_user_apps"."updated_at" IS 'updated';
COMMENT ON COLUMN "public"."auth_user_apps"."deleted_at" IS 'soft delete';
COMMENT ON COLUMN "public"."auth_user_apps"."is_deleted" IS 'deleted flag';

-- ----------------------------
-- Records of auth_user_apps
-- ----------------------------
INSERT INTO "public"."auth_user_apps" VALUES (1, 'nexuskit', 't', NULL, '2026-06-23 05:13:31.17155+00', 2, '2026-06-23 05:46:26.544079+00', NULL, 'f');

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
COMMENT ON COLUMN "public"."auth_users"."id" IS 'PK';
COMMENT ON COLUMN "public"."auth_users"."created_at" IS 'created';
COMMENT ON COLUMN "public"."auth_users"."updated_at" IS 'updated';
COMMENT ON COLUMN "public"."auth_users"."deleted_at" IS 'soft delete';
COMMENT ON COLUMN "public"."auth_users"."is_deleted" IS 'deleted flag';

-- ----------------------------
-- Records of auth_users
-- ----------------------------
INSERT INTO "public"."auth_users" VALUES ('admin', 'admin@nexuskit.com', NULL, '86', '$argon2id$v=19$m=65536,t=3,p=4$LqW0ds75X8uZc6611pqzdg$2h1kBMugAMTwgaOjmhcIjUZGZW3TQ4EqM/YZ/pYjy/k', NULL, 'f', 1, 't', NULL, 1, '2026-06-23 00:52:21.559555+00', '2026-06-23 00:52:21.559555+00', NULL, 'f');

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_apps_id_seq"
OWNED BY "public"."auth_apps"."id";
SELECT setval('"public"."auth_apps_id_seq"', 2, true);

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
SELECT setval('"public"."auth_permissions_id_seq"', 9, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_roles_id_seq"
OWNED BY "public"."auth_roles"."id";
SELECT setval('"public"."auth_roles_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_user_apps_id_seq"
OWNED BY "public"."auth_user_apps"."id";
SELECT setval('"public"."auth_user_apps_id_seq"', 3, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."auth_users_id_seq"
OWNED BY "public"."auth_users"."id";
SELECT setval('"public"."auth_users_id_seq"', 1, true);

-- ----------------------------
-- Primary Key structure for table alembic_version
-- ----------------------------
ALTER TABLE "public"."alembic_version" ADD CONSTRAINT "alembic_version_pkc" PRIMARY KEY ("version_num");

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
-- Primary Key structure for table auth_user_apps
-- ----------------------------
ALTER TABLE "public"."auth_user_apps" ADD CONSTRAINT "auth_user_apps_pkey" PRIMARY KEY ("id", "user_id", "app_code");

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
-- Foreign Keys structure for table auth_user_apps
-- ----------------------------
ALTER TABLE "public"."auth_user_apps" ADD CONSTRAINT "auth_user_apps_app_code_fkey" FOREIGN KEY ("app_code") REFERENCES "public"."auth_apps" ("app_code") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."auth_user_apps" ADD CONSTRAINT "auth_user_apps_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."auth_users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table auth_user_roles_link
-- ----------------------------
ALTER TABLE "public"."auth_user_roles_link" ADD CONSTRAINT "auth_user_roles_link_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."auth_roles" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."auth_user_roles_link" ADD CONSTRAINT "auth_user_roles_link_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."auth_users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table auth_users
-- ----------------------------
ALTER TABLE "public"."auth_users" ADD CONSTRAINT "auth_users_dept_id_fkey" FOREIGN KEY ("dept_id") REFERENCES "public"."auth_departments" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
