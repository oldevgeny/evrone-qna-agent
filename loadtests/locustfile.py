"""Main Locust entry point with all user classes.

This file is the default entry point for Locust. It imports and exports
all user classes so they are discovered by Locust's test runner.

Usage:
    uv run locust -f loadtests/locustfile.py --host=http://localhost:8000

For specific scenarios:
    uv run locust -f loadtests/scenarios/smoke.py --host=http://localhost:8000
"""

from loadtests.users.chat_user import ChatUser
from loadtests.users.health_user import HealthUser
from loadtests.users.message_user import MessageUser

# Re-export for Locust discovery
__all__ = ["ChatUser", "HealthUser", "MessageUser"]
