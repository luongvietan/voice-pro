"""Chạy callable đồng bộ với timeout (worker Celery / không asyncio)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Callable, TypeVar

T = TypeVar("T")


def run_sync_with_timeout(
    fn: Callable[[], T],
    *,
    timeout_seconds: float,
    operation_label: str,
) -> T:
    """Chạy ``fn`` trong thread pool và raise ``TimeoutError`` nếu vượt ``timeout_seconds``."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    with ThreadPoolExecutor(max_workers=1) as executor:
        fut = executor.submit(fn)
        try:
            return fut.result(timeout=timeout_seconds)
        except FuturesTimeout:
            raise TimeoutError(f"{operation_label} timed out after {timeout_seconds}s") from None
