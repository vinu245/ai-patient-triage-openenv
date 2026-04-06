from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Request

from app.models import EnvironmentState, MetricsSnapshot, StepRequest, StepResponse

router = APIRouter()


async def _broadcast(request: Request, payload: Dict[str, Any]) -> None:
    manager = request.app.state.ws_manager
    await manager.broadcast_json(payload)


@router.post("/step", response_model=StepResponse)
async def step(request: Request, body: StepRequest) -> StepResponse:
    env = request.app.state.env
    result = env.step(body.action)

    state = env.state()
    metrics = env.metrics()
    asyncio.create_task(_broadcast(request, {"event": "step", "result": result.model_dump(), "state": state.model_dump(), "metrics": metrics.model_dump()}))

    return StepResponse(result=result, state=state, metrics=metrics)


@router.post("/reset", response_model=EnvironmentState)
async def reset(request: Request) -> EnvironmentState:
    env = request.app.state.env
    state = env.reset()

    asyncio.create_task(_broadcast(request, {"event": "reset", "state": state.model_dump(), "metrics": env.metrics().model_dump()}))
    return state


@router.get("/state", response_model=EnvironmentState)
async def get_state(request: Request) -> EnvironmentState:
    return request.app.state.env.state()


@router.get("/metrics", response_model=MetricsSnapshot)
async def get_metrics(request: Request) -> MetricsSnapshot:
    return request.app.state.env.metrics()
