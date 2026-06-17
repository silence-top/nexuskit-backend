# core/lifespan.py — Application lifespan (startup/shutdown)
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.db import init_db, wait_for_db
from scripts.seed_data import seed_if_empty

logger = logging.getLogger("nexuskit")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("正在等待数据库连接...")
    await wait_for_db()

    logger.info("正在检查数据库表结构...")
    await init_db()
    logger.info("表结构就绪")

    logger.info("正在检查基础数据...")
    await seed_if_empty()
    logger.info("数据库初始化完成")

    yield

    # --- Shutdown ---
    logger.info("服务正在关闭")
