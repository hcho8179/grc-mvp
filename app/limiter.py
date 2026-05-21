"""Shared rate limiter instance — imported by main.py and route modules."""

from slowapi import Limiter
from app.utils import real_ip

limiter = Limiter(key_func=real_ip)
