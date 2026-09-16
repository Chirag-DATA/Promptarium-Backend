from slowapi import Limiter # pyright: ignore[reportMissingImports]
from slowapi.util import get_remote_address # pyright: ignore[reportMissingImports]

limiter = Limiter(key_func=get_remote_address)