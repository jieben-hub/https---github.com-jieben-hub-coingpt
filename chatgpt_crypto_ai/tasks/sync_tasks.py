# -*- coding: utf-8 -*-
"""Celery tasks for synchronizing trading history."""
import logging
from celery import shared_task

from services.auto_sync_service import AutoSyncService

logger = logging.getLogger(__name__)


@shared_task(name="tasks.sync_tasks.sync_all_users_history_task")
def sync_all_users_history_task(days: int = 7):
    """Task to synchronize trading history for all eligible users."""
    logger.info("[Celery] 开始执行全量交易历史同步任务")
    AutoSyncService.sync_all_users_history(days=days)
    logger.info("[Celery] 全量交易历史同步任务完成")


@shared_task(name="tasks.sync_tasks.sync_user_history_task")
def sync_user_history_task(user_id: int, days: int = 7):
    """Task to synchronize trading history for a specific user."""
    logger.info("[Celery] 开始执行用户 %s 交易历史同步任务", user_id)
    AutoSyncService.sync_user_history(user_id=user_id, days=days)
    logger.info("[Celery] 用户 %s 交易历史同步任务完成", user_id)
