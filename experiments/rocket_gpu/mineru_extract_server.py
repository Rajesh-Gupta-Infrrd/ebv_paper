#!/usr/bin/env python3
"""Out-of-process MinerU extract server (run inside mineru-venv or mineru-vllm-venv).

Loads MinerU weights in this process (transformers / vllm / mlx-engine / …) and
exposes a tiny HTTP API the pipeline adapter can call:

  GET  /health
  POST /extract  {"image_path": "/abs/path.png", "image_analysis": false}
                 → {"content_list": [...]}

Pipeline process should use MINERU_BACKEND=http-extract and point at this server.
This process sets the *real* engine via MINERU_BACKEND (transformers, vllm-*, mlx-engine).

Serving mode (same entrypoint, same port, same /extract contract):

  - transformers / mlx / vllm-engine  → ThreadingHTTPServer
  - vllm-async-engine                 → ASGI (uvicorn) + micro-batch coalesce

Examples::

    # Mac / local (mineru-venv)
    source mineru-venv/bin/activate
    export MINERU_BACKEND=transformers
    python scripts/parse/servers/mineru_extract_server.py --port 30000 --preload

    # NVIDIA GPU (mineru-vllm-venv)
    source mineru-vllm-venv/bin/activate
    export MINERU_BACKEND=vllm-async-engine
    python scripts/parse/servers/mineru_extract_server.py --port 30000 --preload
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

DEFAULT_MODEL_ID = "opendatalab/MinerU2.5-Pro-2605-1.2B"
VLLM_BACKENDS = frozenset({"vllm-engine", "vllm-async-engine"})
ASGI_BACKENDS = frozenset({"vllm-async-engine"})

_CLIENT: Any = None
_ACTIVE_BACKEND: str = ""
_ACTIVE_BATCH_SIZE: int | None = None
_SERVER_MODE: str = "threading"



def _resolve_batch_size() -> int:
    """Batch size for the transformers backend.

    Explicit ``MINERU_BATCH_SIZE`` always wins. Otherwise use 8 on CUDA
    (A10/Lambda) and 1 on Mac/CPU.
    """
    raw = os.environ.get("MINERU_BATCH_SIZE", "").strip()
    if raw:
        return max(1, int(raw))

    try:
        import torch

        if torch.cuda.is_available():
            return 8
    except Exception:
        pass
    return 1


def _micro_batch_window_s() -> float:
    raw = os.environ.get("MINERU_MICRO_BATCH_MS", "20").strip()
    try:
        return max(0.0, float(raw) / 1000.0)
    except ValueError:
        return 0.02


def _micro_batch_max() -> int:
    raw = os.environ.get("MINERU_MICRO_BATCH_MAX", "8").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 8


def _require_vllm_installed(backend: str) -> None:
    """Fail fast if a vLLM backend was requested but vLLM is not importable."""
    try:
        import vllm  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            f"MINERU_BACKEND={backend} requires the `vllm` package, but it is "
            f"not installed in this environment ({exc}).\n\n"
            "Fix one of:\n"
            "  1) Use a dedicated venv on NVIDIA GPU machines:\n"
            "       python3.12 -m venv mineru-vllm-venv\n"
            "       source mineru-vllm-venv/bin/activate\n"
            "       pip install vllm 'mineru-vl-utils[transformers]==1.0.5' "
            "fastapi uvicorn\n"
            "  2) Or stay on transformers (Mac / no vLLM):\n"
            "       export MINERU_BACKEND=transformers\n"
            "       source mineru-venv/bin/activate\n"
        ) from exc


def _require_asgi_deps() -> None:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "MINERU_BACKEND=vllm-async-engine requires FastAPI + uvicorn "
            f"(ASGI server): {exc}\n"
            "  pip install fastapi uvicorn\n"
        ) from exc


def _build_transformers_client(
    *,
    model_id: str,
    image_analysis: bool,
) -> Any:
    from mineru_vl_utils import MinerUClient
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    batch_size = _resolve_batch_size()
    global _ACTIVE_BATCH_SIZE
    _ACTIVE_BATCH_SIZE = batch_size

    print(
        f"[mineru-server] transformers batch_size={batch_size} "
        f"(override with MINERU_BATCH_SIZE)",
        flush=True,
    )

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id,
        dtype="auto",
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(model_id, use_fast=True)
    return MinerUClient(
        backend="transformers",
        model=model,
        processor=processor,
        image_analysis=image_analysis,
        use_tqdm=False,
        batch_size=batch_size,
    )


def _build_vllm_client(
    *,
    backend: str,
    model_id: str,
    image_analysis: bool,
) -> Any:
    from mineru_vl_utils import MinerUClient

    _require_vllm_installed(backend)

    global _ACTIVE_BATCH_SIZE
    _ACTIVE_BATCH_SIZE = None

    print(f"[mineru-server] {backend} ready (library defaults for batch/concurrency)", flush=True)

    if backend == "vllm-engine":
        from vllm import LLM

        try:
            from mineru_vl_utils import MinerULogitsProcessor

            logits_processors = [MinerULogitsProcessor]
        except ImportError:
            logits_processors = None

        llm_kwargs: dict[str, Any] = {"model": model_id}
        if logits_processors is not None:
            llm_kwargs["logits_processors"] = logits_processors
        llm = LLM(**llm_kwargs)
        return MinerUClient(
            backend="vllm-engine",
            vllm_llm=llm,
            image_analysis=image_analysis,
            use_tqdm=False,
        )

    return MinerUClient(
        backend=backend,
        model_path=model_id,
        image_analysis=image_analysis,
        use_tqdm=False,
    )


def _build_client() -> Any:
    from mineru_vl_utils import MinerUClient

    model_id = os.environ.get("MINERU_MODEL_ID", DEFAULT_MODEL_ID)
    backend = os.environ.get("MINERU_BACKEND", "mlx-engine").strip().lower()
    image_analysis = os.environ.get("MINERU_IMAGE_ANALYSIS", "0").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    global _ACTIVE_BACKEND
    _ACTIVE_BACKEND = backend

    if backend == "http-client":
        raise SystemExit(
            "MINERU_BACKEND=http-client is for the pipeline client, not this server. "
            "Use transformers, vllm-engine, vllm-async-engine, or mlx-engine here."
        )

    if backend == "http-extract":
        raise SystemExit(
            "MINERU_BACKEND=http-extract is for the pipeline process, not this server. "
            "On this process set transformers (Mac/local) or vllm-async-engine (NVIDIA GPU)."
        )

    if backend == "transformers":
        return _build_transformers_client(
            model_id=model_id,
            image_analysis=image_analysis,
        )

    if backend in VLLM_BACKENDS:
        return _build_vllm_client(
            backend=backend,
            model_id=model_id,
            image_analysis=image_analysis,
        )

    return MinerUClient(
        backend=backend,
        model_path=model_id,
        image_analysis=image_analysis,
        use_tqdm=False,
    )


def _health_payload() -> dict[str, Any]:
    """Health body shared by both server modes.

    Both the threading handler and the ASGI route return this. It used to be
    inlined in the threading handler only, which left the ASGI ``/health``
    route calling an undefined name and returning 500 in vllm-async-engine
    mode — the mode the setup script actually runs.
    """
    return {
        "status": "ok",
        "backend": _ACTIVE_BACKEND,
        "server_mode": _SERVER_MODE,
        "model_id": os.environ.get("MINERU_MODEL_ID", DEFAULT_MODEL_ID),
        "batch_size": _ACTIVE_BATCH_SIZE,
        "model_loaded": _CLIENT is not None,
    }


def get_client() -> Any:
    global _CLIENT
    if _CLIENT is None:
        print(
            f"Loading MinerU client backend={os.environ.get('MINERU_BACKEND', 'mlx-engine')} "
            f"model={os.environ.get('MINERU_MODEL_ID', DEFAULT_MODEL_ID)} …",
            flush=True,
        )
        _CLIENT = _build_client()
        print("MinerU client ready.", flush=True)
    return _CLIENT



def _content_list_payload(content_list: Any) -> dict[str, Any]:
    return {"content_list": [dict(block) for block in content_list]}


def _sync_extract(image_path: Path, image_analysis: bool) -> list[dict[str, Any]]:
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    client = get_client()
    content_list = client.two_step_extract(image, image_analysis=image_analysis)
    return [dict(block) for block in content_list]


async def _async_extract_many(
    images: list[Any],
    *,
    image_analysis: bool,
) -> list[list[dict[str, Any]]]:
    """Run multi-image extract via MinerU async APIs; fall back to sync per image."""
    client = get_client()

    if hasattr(client, "aio_concurrent_two_step_extract"):
        raw = await client.aio_concurrent_two_step_extract(
            images, image_analysis=image_analysis
        )
        return [[dict(block) for block in item] for item in raw]

    if hasattr(client, "aio_batch_two_step_extract"):
        raw = await client.aio_batch_two_step_extract(
            images, image_analysis=image_analysis
        )
        return [[dict(block) for block in item] for item in raw]

    results: list[list[dict[str, Any]]] = []
    for image in images:
        if hasattr(client, "aio_two_step_extract"):
            raw = await client.aio_two_step_extract(
                image, image_analysis=image_analysis
            )
        else:
            raw = await asyncio.to_thread(
                client.two_step_extract, image, image_analysis=image_analysis
            )
        results.append([dict(block) for block in raw])
    return results


class _ExtractMicroBatcher:
    """Coalesce near-simultaneous /extract calls into one async multi-image run."""

    def __init__(self, *, window_s: float, max_batch: int) -> None:
        self._window_s = window_s
        self._max_batch = max_batch
        self._lock = asyncio.Lock()
        self._pending: list[tuple[Path, bool, asyncio.Future]] = []
        self._flush_handle: asyncio.TimerHandle | None = None

    async def submit(
        self, image_path: Path, image_analysis: bool
    ) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        async with self._lock:
            self._pending.append((image_path, image_analysis, fut))
            if len(self._pending) >= self._max_batch:
                batch = self._pending
                self._pending = []
                self._cancel_flush()
                loop.create_task(self._run_batch(batch))
            elif self._flush_handle is None:
                if self._window_s <= 0:
                    batch = self._pending
                    self._pending = []
                    loop.create_task(self._run_batch(batch))
                else:
                    self._flush_handle = loop.call_later(
                        self._window_s, self._on_timer
                    )
        return await fut

    def _cancel_flush(self) -> None:
        if self._flush_handle is not None:
            self._flush_handle.cancel()
            self._flush_handle = None

    def _on_timer(self) -> None:
        self._flush_handle = None
        asyncio.create_task(self._flush_now())

    async def _flush_now(self) -> None:
        async with self._lock:
            if not self._pending:
                return
            batch = self._pending
            self._pending = []
            self._cancel_flush()
        await self._run_batch(batch)

    async def _run_batch(
        self, batch: list[tuple[Path, bool, asyncio.Future]]
    ) -> None:
        from PIL import Image

        # Preserve request order; group only by image_analysis for the API call.
        by_flag: dict[bool, list[tuple[int, Path, asyncio.Future]]] = {}
        for idx, (path, analysis, fut) in enumerate(batch):
            by_flag.setdefault(analysis, []).append((idx, path, fut))

        results: list[list[dict[str, Any]] | BaseException | None] = [None] * len(
            batch
        )

        for analysis, items in by_flag.items():
            images = []
            futs = []
            indices = []
            try:
                for idx, path, fut in items:
                    images.append(Image.open(path).convert("RGB"))
                    futs.append(fut)
                    indices.append(idx)
                lists = await _async_extract_many(images, image_analysis=analysis)
                if len(lists) != len(items):
                    raise RuntimeError(
                        f"async extract returned {len(lists)} results for "
                        f"{len(items)} images"
                    )
                for idx, content in zip(indices, lists):
                    results[idx] = content
            except Exception:  # noqa: BLE001 - fall back per image
                for idx, path, _fut in items:
                    try:
                        one = await _async_extract_many(
                            [Image.open(path).convert("RGB")],
                            image_analysis=analysis,
                        )
                        results[idx] = one[0]
                    except Exception as one_exc:  # noqa: BLE001
                        results[idx] = one_exc

        for (_path, _analysis, fut), result in zip(batch, results):
            if fut.done():
                continue
            if isinstance(result, BaseException):
                fut.set_exception(result)
            elif result is None:
                fut.set_exception(RuntimeError("extract produced no result"))
            else:
                fut.set_result(result)


# ---------------------------------------------------------------------------
# ThreadingHTTPServer path (transformers / mlx / vllm-engine)
# ---------------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[mineru-server] {self.address_string()} {fmt % args}", flush=True)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._send_json(200, _health_payload())
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/extract":
            self._send_json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8"))
            image_path = Path(str(payload.get("image_path") or "")).expanduser()
            if not image_path.is_file():
                self._send_json(400, {"error": f"image_path not found: {image_path}"})
                return
            image_analysis = bool(payload.get("image_analysis", False))
            content_list = _sync_extract(image_path, image_analysis)
            self._send_json(200, _content_list_payload(content_list))
        except Exception as exc:  # noqa: BLE001 - surface errors to client
            self._send_json(
                500,
                {
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )


def _run_threading(host: str, port: int) -> None:
    global _SERVER_MODE
    _SERVER_MODE = "threading"
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"MinerU extract server listening on http://{host}:{port}", flush=True)
    print("Mode: threading  Endpoints: GET /health  POST /extract", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
        server.shutdown()


# ---------------------------------------------------------------------------
# ASGI path (vllm-async-engine) + micro-batch
# ---------------------------------------------------------------------------


def _build_asgi_app():
    """Build FastAPI app for vllm-async-engine.

    Important: this file uses ``from __future__ import annotations``. FastAPI then
    stringifies annotations and can mis-classify parameters as *query* fields
    (HTTP 422 ``loc=["query","payload"]``). Force a JSON **body** with
    ``Body(...)`` and a plain ``dict`` annotation (always resolvable).
    """
    from fastapi import Body, FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="MinerU extract server", docs_url=None, redoc_url=None)
    batcher = _ExtractMicroBatcher(
        window_s=_micro_batch_window_s(),
        max_batch=_micro_batch_max(),
    )

    @app.on_event("startup")
    async def _startup() -> None:
        get_client()
        print(
            f"[mineru-server] ASGI micro-batch window="
            f"{_micro_batch_window_s() * 1000:.0f}ms "
            f"max={_micro_batch_max()}",
            flush=True,
        )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return _health_payload()

    @app.post("/extract")
    async def extract(payload: dict = Body(...)) -> JSONResponse:
        # ``dict = Body(...)`` — Body() default forces JSON body even when
        # ``from __future__ import annotations`` stringifies type hints.
        if not isinstance(payload, dict):
            return JSONResponse({"error": "invalid_json"}, status_code=400)
        image_path = Path(str(payload.get("image_path") or "")).expanduser()
        if not image_path.is_file():
            return JSONResponse(
                {"error": f"image_path not found: {image_path}"},
                status_code=400,
            )
        image_analysis = bool(payload.get("image_analysis", False))
        try:
            content_list = await batcher.submit(image_path, image_analysis)
            return JSONResponse(_content_list_payload(content_list))
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                {
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
                status_code=500,
            )

    return app


def _run_asgi(host: str, port: int) -> None:
    global _SERVER_MODE
    _SERVER_MODE = "asgi"
    _require_asgi_deps()
    import uvicorn

    app = _build_asgi_app()
    print(f"MinerU extract server listening on http://{host}:{port}", flush=True)
    print(
        "Mode: asgi (vllm-async-engine + micro-batch)  "
        "Endpoints: GET /health  POST /extract",
        flush=True,
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


def main() -> None:
    parser = argparse.ArgumentParser(description="MinerU out-of-process extract server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=30000)
    parser.add_argument(
        "--preload",
        action="store_true",
        help="Load MinerU model at startup instead of on first request",
    )
    args = parser.parse_args()

    backend = os.environ.get("MINERU_BACKEND", "mlx-engine")
    use_asgi = backend in ASGI_BACKENDS

    # ASGI app preloads on startup; threading honors --preload here.
    if args.preload and not use_asgi:
        get_client()

    if use_asgi:
        _run_asgi(args.host, args.port)
    else:
        _run_threading(args.host, args.port)


if __name__ == "__main__":
    main()
