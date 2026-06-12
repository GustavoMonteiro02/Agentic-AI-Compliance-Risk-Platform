from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RouteMetrics:
    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    status_counts: dict[str, int] = field(default_factory=dict)

    def record(self, status_code: int, duration_ms: float) -> None:
        self.request_count += 1
        if status_code >= 500:
            self.error_count += 1
        self.total_duration_ms += duration_ms
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        status_key = str(status_code)
        self.status_counts[status_key] = self.status_counts.get(status_key, 0) + 1

    def snapshot(self) -> dict:
        average_duration_ms = self.total_duration_ms / self.request_count if self.request_count else 0.0
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "average_duration_ms": round(average_duration_ms, 3),
            "max_duration_ms": round(self.max_duration_ms, 3),
            "status_counts": dict(sorted(self.status_counts.items())),
        }


class HTTPMetricsCollector:
    def __init__(self) -> None:
        self._lock = Lock()
        self._routes: dict[tuple[str, str], RouteMetrics] = defaultdict(RouteMetrics)

    def record(self, *, method: str, path: str, status_code: int, duration_ms: float) -> None:
        route_key = (method.upper(), self._normalize_path(path))
        with self._lock:
            self._routes[route_key].record(status_code, duration_ms)

    def snapshot(self) -> dict:
        with self._lock:
            routes = {
                f"{method} {path}": metrics.snapshot()
                for (method, path), metrics in sorted(self._routes.items())
            }
        total_requests = sum(route["request_count"] for route in routes.values())
        total_errors = sum(route["error_count"] for route in routes.values())
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "routes": routes,
        }

    def prometheus(self) -> str:
        snapshot = self.snapshot()
        lines = [
            "# HELP ai_governance_http_requests_total Total HTTP requests by method, route, and status.",
            "# TYPE ai_governance_http_requests_total counter",
        ]
        for route_name, route_metrics in snapshot["routes"].items():
            method, route = route_name.split(" ", 1)
            for status, count in route_metrics["status_counts"].items():
                lines.append(
                    "ai_governance_http_requests_total"
                    f'{{method="{method}",route="{route}",status="{status}"}} {count}'
                )

        lines.extend(
            [
                "# HELP ai_governance_http_request_duration_ms_average Average HTTP request duration in milliseconds.",
                "# TYPE ai_governance_http_request_duration_ms_average gauge",
            ]
        )
        for route_name, route_metrics in snapshot["routes"].items():
            method, route = route_name.split(" ", 1)
            lines.append(
                "ai_governance_http_request_duration_ms_average"
                f'{{method="{method}",route="{route}"}} {route_metrics["average_duration_ms"]}'
            )
        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self._routes.clear()

    def _normalize_path(self, path: str) -> str:
        if path.startswith("/runtime/metrics"):
            return "/runtime/metrics"
        return path


http_metrics = HTTPMetricsCollector()
