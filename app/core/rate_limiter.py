import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.attempts: dict[str, list[float]] = defaultdict(list)

    def __call__(self, request: Request):
        client_ip = request.client.host
        now = time.time()

        recent_attempts = [
            ts for ts in self.attempts[client_ip] if now - ts < self.window_seconds
        ]

        if len(recent_attempts) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Please try again in {self.window_seconds} seconds.",
            )

        recent_attempts.append(now)
        self.attempts[client_ip] = recent_attempts