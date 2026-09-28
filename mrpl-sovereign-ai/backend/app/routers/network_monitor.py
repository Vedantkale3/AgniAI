import os

import psutil
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.tools.net_sentinel import (
    get_all_local_traffic_summary,
    get_egress_feed,
)


router = APIRouter(
    prefix="/api/network",
    tags=["Network"],
    dependencies=[Depends(get_current_user)],
)


def _own_process_tree() -> set[int]:
    try:
        current_process = psutil.Process(os.getpid())

        process_ids = {
            current_process.pid,
        }

        process_ids.update(
            child.pid
            for child in current_process.children(
                recursive=True,
            )
        )

        return process_ids

    except Exception:
        return set()


@router.get("/status")
async def network_status():
    return get_all_local_traffic_summary(
        _own_process_tree()
    )


@router.get("/egress-alerts")
async def egress_alerts():
    return {
        "alerts": get_egress_feed(),
    }