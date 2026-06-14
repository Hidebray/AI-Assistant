import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from backend.infrastructure.llm.ollama_manager import ollama_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ollama", tags=["ollama"])


@router.get("/status")
async def get_ollama_status():
    """Check Ollama installation status, server status, and available models."""
    status = await ollama_manager.check_status()
    return status


@router.post("/start")
async def start_ollama_server():
    """Start Ollama server if not already running."""
    result = await ollama_manager.start_server()
    return result


@router.get("/models")
async def list_ollama_models():
    """List locally installed Ollama models."""
    models = await ollama_manager.list_models()
    return {"models": models}


class PullModelRequest(BaseModel):
    model: str = "qwen2.5:3b"


async def _sse_generator(async_gen):
    """Wrap an async generator into Server-Sent Events format."""
    try:
        async for data in async_gen:
            yield f"data: {json.dumps(data)}\n\n"
        yield f"data: {json.dumps({'stage': 'stream_end'})}\n\n"
    except Exception as e:
        logger.error(f"SSE stream error: {e}", exc_info=True)
        yield f"data: {json.dumps({'stage': 'error', 'message': str(e)})}\n\n"


@router.post("/install")
async def install_ollama():
    """Download and install Ollama silently. Returns SSE stream with progress."""

    async def combined_stream():
        installer_path = None

        # Phase 1: Download
        async for progress in ollama_manager.download_installer():
            yield progress
            if progress.get("stage") == "download_complete":
                installer_path = progress.get("installer_path")
            if progress.get("stage") == "error":
                return

        if not installer_path:
            yield {"stage": "error", "message": "Download did not produce an installer file"}
            return

        # Phase 2: Install
        async for progress in ollama_manager.install_ollama(installer_path):
            yield progress
            if progress.get("stage") == "error":
                return

        # Phase 3: Start server
        yield {"stage": "starting_server", "message": "Đang khởi động Ollama server..."}
        result = await ollama_manager.start_server()
        if result["success"]:
            yield {"stage": "server_started", "message": result["message"]}
        else:
            yield {"stage": "error", "message": result["message"]}

    return StreamingResponse(
        _sse_generator(combined_stream()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/pull")
async def pull_ollama_model(req: PullModelRequest):
    """Pull a model from Ollama registry. Returns SSE stream with progress."""
    return StreamingResponse(
        _sse_generator(ollama_manager.pull_model(req.model)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
