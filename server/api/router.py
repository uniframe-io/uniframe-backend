from fastapi import APIRouter

from server.apps.config.endpoints import router as config_router
from server.apps.dataset.endpoints import router as dataset_router
from server.apps.group.endpoints import router as group_router
from server.apps.media.endpoints import router as media_router
from server.apps.nm_task.endpoints import router as task_router
from server.apps.oauth.endpoints import router as oauth_router
from server.apps.permission.endpoints import router as permission_router
from server.apps.stat.endpoints import router as stat_router
from server.apps.user.endpoints import router as user_router

api_router = APIRouter()

api_router.include_router(user_router, tags=["user"])
api_router.include_router(oauth_router, tags=["oauth"])
api_router.include_router(task_router, tags=["task"])
api_router.include_router(group_router, tags=["group"])
api_router.include_router(dataset_router, tags=["dataset"])
api_router.include_router(media_router, tags=["media"])
api_router.include_router(config_router, tags=["config"])
api_router.include_router(stat_router, tags=["stat"])
api_router.include_router(permission_router, tags=["permission"])
