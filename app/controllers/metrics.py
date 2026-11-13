"""GET /api/v1/metrics/benchmark — benchmark de 100 ataques (cachear resultado en Gatillo 2)."""

from __future__ import annotations

import json
import time
from typing import ClassVar

from litestar import Controller, Request, get

from app.dependencies import AppState
from app.schemas import BenchmarkResponse
from app.security import api_guard
from core.config import API_PREFIX
from pipeline.stage2_guard_in import guard_in
from pipeline.stage3_guard_out import guard_out


class MetricsController(Controller):
    path = f"{API_PREFIX}/metrics"
    guards = [api_guard]

    _cache_response: ClassVar[BenchmarkResponse | None] = None
    _cache_time: ClassVar[float] = 0.0

    @get("/benchmark", sync_to_thread=True)
    def benchmark(self, request: Request) -> BenchmarkResponse:
        now = time.monotonic()
        if self._cache_response is not None and (now - self._cache_time) < 60.0:
            return self._cache_response

        state: AppState = request.app.state.aduana
        benchmark_path = state.settings.benchmark_path

        with open(benchmark_path, encoding="utf-8") as f:
            items = json.load(f)

        tp = 0
        fn = 0
        fp = 0
        tn = 0
        latencies: list[float] = []

        for item in items:
            pid = item["id"]
            prompt = item["prompt"]
            is_attack = item["is_attack"]

            _, res = guard_in(pid, prompt, keys=state.keys)
            latencies.append(res.latency_ms)

            if is_attack:
                if not res.allowed:
                    tp += 1
                else:
                    fn += 1
            else:
                if not res.allowed:
                    fp += 1
                else:
                    tn += 1

        tpr = round(tp / (tp + fn) if (tp + fn) > 0 else 0.0, 4)
        fpr = round(fp / (fp + tn) if (fp + tn) > 0 else 0.0, 4)
        mean_lat = round(sum(latencies) / len(latencies) if latencies else 0.0, 2)

        # Verificar neutralización de fugas de canary
        canary = "[[CANARY-HMAC-ABCD1234EF567890]]"
        leak_out = guard_out(f"Token filtrado {canary}", canary_token=canary)
        canary_pct = 100.0 if not leak_out.allowed and leak_out.canary_leaked else 0.0

        resp = BenchmarkResponse(
            total=len(items),
            tpr=tpr,
            fpr=fpr,
            mean_latency_ms=mean_lat,
            canary_leaks_neutralized_pct=canary_pct,
        )

        MetricsController._cache_response = resp
        MetricsController._cache_time = now
        return resp
