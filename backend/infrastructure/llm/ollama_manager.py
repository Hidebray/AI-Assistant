import asyncio
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from typing import AsyncGenerator, Callable, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Default Ollama download URL for Windows
OLLAMA_DOWNLOAD_URL = "https://ollama.com/download/OllamaSetup.exe"
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"
RECOMMENDED_MODEL = "qwen2.5:3b"


class OllamaManager:
    """Manages the lifecycle of a local Ollama installation:
    detect, download, install, start server, and pull models."""

    def __init__(self, base_url: str = OLLAMA_DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # 1. Status / Detection
    # ------------------------------------------------------------------

    def _find_ollama_exe(self) -> Optional[str]:
        """Try to locate ollama.exe on the system."""
        # 1) Check PATH
        ollama_in_path = shutil.which("ollama")
        if ollama_in_path:
            return ollama_in_path

        # 2) Check common Windows install locations
        candidates = []
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidates.append(os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe"))
            candidates.append(os.path.join(local_app_data, "Ollama", "ollama.exe"))

        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            candidates.append(os.path.join(user_profile, "AppData", "Local", "Programs", "Ollama", "ollama.exe"))

        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        candidates.append(os.path.join(program_files, "Ollama", "ollama.exe"))

        for path in candidates:
            if os.path.isfile(path):
                return path

        return None

    async def _is_server_running(self) -> bool:
        """Check if Ollama server is responding."""
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[Dict]:
        """Return the list of locally installed models."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("models", [])
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
        return []

    async def check_status(self) -> Dict:
        """Return a full status dict for the frontend."""
        ollama_exe = self._find_ollama_exe()
        installed = ollama_exe is not None
        server_running = await self._is_server_running()
        models: List[Dict] = []

        if server_running:
            models = await self.list_models()

        model_names = [m.get("name", "") for m in models]

        return {
            "installed": installed,
            "server_running": server_running,
            "models": model_names,
            "recommended_model": RECOMMENDED_MODEL,
            "ollama_path": ollama_exe,
        }

    # ------------------------------------------------------------------
    # 2. Download Installer
    # ------------------------------------------------------------------

    async def download_installer(self) -> AsyncGenerator[Dict, None]:
        """Download OllamaSetup.exe, yielding progress dicts."""
        tmp_dir = tempfile.mkdtemp(prefix="aaa_ollama_")
        dest_path = os.path.join(tmp_dir, "OllamaSetup.exe")

        try:
            async with httpx.AsyncClient(timeout=600.0, follow_redirects=True) as client:
                async with client.stream("GET", OLLAMA_DOWNLOAD_URL) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("content-length", 0))
                    downloaded = 0

                    with open(dest_path, "wb") as f:
                        async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                            f.write(chunk)
                            downloaded += len(chunk)
                            pct = int((downloaded / total) * 100) if total else 0
                            yield {
                                "stage": "downloading",
                                "progress": pct,
                                "downloaded_mb": round(downloaded / (1024 * 1024), 1),
                                "total_mb": round(total / (1024 * 1024), 1),
                            }

            yield {"stage": "download_complete", "progress": 100, "installer_path": dest_path}
        except Exception as e:
            logger.error(f"Failed to download Ollama installer: {e}", exc_info=True)
            yield {"stage": "error", "message": f"Download failed: {str(e)}"}

    # ------------------------------------------------------------------
    # 3. Silent Install
    # ------------------------------------------------------------------

    async def install_ollama(self, installer_path: str) -> AsyncGenerator[Dict, None]:
        """Run the Ollama installer silently."""
        if not os.path.isfile(installer_path):
            yield {"stage": "error", "message": "Installer file not found"}
            return

        yield {"stage": "installing", "message": "Đang cài đặt Ollama (có thể mất 1-2 phút)..."}

        try:
            process = await asyncio.create_subprocess_exec(
                installer_path, "/VERYSILENT",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

            if process.returncode == 0:
                yield {"stage": "install_complete", "message": "Ollama đã cài đặt thành công!"}
            else:
                error_msg = stderr.decode(errors="replace") if stderr else "Unknown error"
                yield {"stage": "error", "message": f"Install failed (code {process.returncode}): {error_msg}"}
        except asyncio.TimeoutError:
            yield {"stage": "error", "message": "Installation timed out after 5 minutes"}
        except Exception as e:
            logger.error(f"Ollama install error: {e}", exc_info=True)
            yield {"stage": "error", "message": f"Install error: {str(e)}"}

    # ------------------------------------------------------------------
    # 4. Start Server
    # ------------------------------------------------------------------

    async def start_server(self) -> Dict:
        """Start `ollama serve` if not already running. Returns status."""
        if await self._is_server_running():
            return {"success": True, "message": "Ollama server is already running"}

        ollama_exe = self._find_ollama_exe()
        if not ollama_exe:
            return {"success": False, "message": "Ollama is not installed"}

        try:
            # Launch ollama serve as a detached background process
            if sys.platform == "win32":
                CREATE_NO_WINDOW = 0x08000000
                subprocess.Popen(
                    [ollama_exe, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW,
                )
            else:
                subprocess.Popen(
                    [ollama_exe, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # Poll until server is ready (max 30s)
            for _ in range(30):
                await asyncio.sleep(1)
                if await self._is_server_running():
                    logger.info("Ollama server started successfully")
                    return {"success": True, "message": "Ollama server started"}

            return {"success": False, "message": "Ollama server did not start within 30 seconds"}
        except Exception as e:
            logger.error(f"Failed to start Ollama server: {e}", exc_info=True)
            return {"success": False, "message": f"Failed to start: {str(e)}"}

    # ------------------------------------------------------------------
    # 5. Pull Model
    # ------------------------------------------------------------------

    async def pull_model(self, model_name: str) -> AsyncGenerator[Dict, None]:
        """Pull a model from Ollama registry, yielding progress."""
        # Ensure server is running first
        if not await self._is_server_running():
            start_result = await self.start_server()
            if not start_result["success"]:
                yield {"stage": "error", "message": start_result["message"]}
                return

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json={"name": model_name, "stream": True},
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            import json
                            data = json.loads(line)
                            status = data.get("status", "")
                            total = data.get("total", 0)
                            completed = data.get("completed", 0)
                            pct = int((completed / total) * 100) if total else 0

                            yield {
                                "stage": "pulling",
                                "status": status,
                                "progress": pct,
                                "completed_mb": round(completed / (1024 * 1024), 1) if completed else 0,
                                "total_mb": round(total / (1024 * 1024), 1) if total else 0,
                            }
                        except Exception:
                            pass  # Skip malformed lines

            yield {"stage": "pull_complete", "model": model_name, "progress": 100}
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}", exc_info=True)
            yield {"stage": "error", "message": f"Failed to pull model: {str(e)}"}


# Module-level singleton for convenience
ollama_manager = OllamaManager()
