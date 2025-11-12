# -*- coding: utf-8 -*-
"""Celery app initialization for CoinGPT."""
from celery import Celery
from datetime import timedelta

import config
from app import create_app


def make_celery(flask_app) -> Celery:
    celery = Celery(
        flask_app.import_name,
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND,
    )

    # 安全的默认值（防止 config 未设置时报错）
    REDIS_SOCKET_TIMEOUT = getattr(config, "REDIS_SOCKET_TIMEOUT", 30)               # 读写超时(s)
    REDIS_SOCKET_CONNECT_TIMEOUT = getattr(config, "REDIS_SOCKET_CONNECT_TIMEOUT", 10)  # 连接超时(s)
    REDIS_MAX_RETRIES = getattr(config, "REDIS_MAX_RETRIES", 0)                      # 0=无限重试
    CELERY_TIMEZONE = getattr(config, "CELERY_TIMEZONE", "Asia/Taipei")
    CELERY_ENABLE_UTC = getattr(config, "CELERY_ENABLE_UTC", False)

    celery.conf.update(
        timezone=CELERY_TIMEZONE,
        enable_utc=CELERY_ENABLE_UTC,
        accept_content=getattr(config, "CELERY_ACCEPT_CONTENT", ["json"]),
        task_serializer=getattr(config, "CELERY_TASK_SERIALIZER", "json"),
        result_serializer=getattr(config, "CELERY_RESULT_SERIALIZER", "json"),
        beat_schedule={},

        # 连接池与心跳
        broker_pool_limit=getattr(config, "BROKER_POOL_LIMIT", 10),
        broker_heartbeat=getattr(config, "BROKER_HEARTBEAT", 30),
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=REDIS_MAX_RETRIES,
        broker_connection_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,

        # —— 关键：Redis 传输层稳连参数（避免空闲被断） ——
        broker_transport_options={
            "visibility_timeout": 3600,
            "max_retries": 0,

            # 定期 PING（redis/kombu 支持），防空闲断连
            "health_check_interval": getattr(config, "REDIS_HEALTH_CHECK_INTERVAL", 30),

            # 超时与重试
            "socket_timeout":   REDIS_SOCKET_TIMEOUT,
            "socket_connect_timeout": REDIS_SOCKET_CONNECT_TIMEOUT,
            "retry_on_timeout": True,

            # TCP keepalive（穿越中间设备 idle 回收）
            "socket_keepalive": True,
            # Linux 上可用的细粒度 keepalive 选项（键为内核常量：1/2/3 分别对应 TCP_KEEPIDLE/INTVL/CNT）
            "socket_keepalive_options": getattr(config, "REDIS_SOCKET_KEEPALIVE_OPTIONS", {
                1: 60,   # 空闲 60s 后开始保活
                2: 10,   # 每 10s 发一次
                3: 5,    # 连续 5 次失败判死
            }),
        },

        # 结果后端也同样加稳连参数
        result_backend_transport_options={
            "health_check_interval": getattr(config, "REDIS_HEALTH_CHECK_INTERVAL", 30),
            "socket_timeout":   REDIS_SOCKET_TIMEOUT,
            "socket_connect_timeout": REDIS_SOCKET_CONNECT_TIMEOUT,
            "retry_on_timeout": True,
            "socket_keepalive": True,
            "socket_keepalive_options": getattr(config, "REDIS_SOCKET_KEEPALIVE_OPTIONS", {
                1: 60, 2: 10, 3: 5
            }),
            "retry_policy": {
                "interval_start": 0,
                "interval_step": 0.5,
                "interval_max": min(5, REDIS_SOCKET_TIMEOUT),
                "max_retries": REDIS_MAX_RETRIES,
            },
        },
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # 确保任务模块被正确加载
    celery.autodiscover_tasks(["tasks"])
    try:
        __import__("tasks.sync_tasks")
    except ImportError:
        pass

    celery.conf.beat_schedule = {
        "sync-all-users-history": {
            "task": "tasks.sync_tasks.sync_all_users_history_task",
            "schedule": timedelta(seconds=getattr(config, "CELERY_SYNC_INTERVAL_SECONDS", 300)),
        }
    }

    return celery


flask_app = create_app(enable_socketio=False)
celery_app = make_celery(flask_app)
