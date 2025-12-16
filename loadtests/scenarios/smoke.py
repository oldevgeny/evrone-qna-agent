"""Smoke test scenario - verify endpoints work under minimal load.

This scenario runs through all endpoints sequentially to verify
they are functioning correctly before running more intensive tests.

Usage:
    uv run locust -f loadtests/scenarios/smoke.py \\
        --host=http://localhost:8000 \\
        --users=1 \\
        --spawn-rate=1 \\
        --run-time=30s \\
        --headless
"""

from locust import HttpUser, between, task


class SmokeTestUser(HttpUser):
    """Single user verifying all endpoints work.

    Runs through all API endpoints in a logical sequence to verify
    basic functionality before running more intensive load tests.
    """

    wait_time = between(0.5, 1)

    @task
    def smoke_test_sequence(self) -> None:
        """Run through all endpoints in sequence."""
        # Health checks first
        self.client.get("/health", name="[smoke] /health")
        self.client.get("/health/live", name="[smoke] /health/live")
        self.client.get("/health/ready", name="[smoke] /health/ready")

        # Create chat
        create_response = self.client.post(
            "/api/v1/chats",
            json={"title": "Smoke Test Chat"},
            name="[smoke] POST /api/v1/chats",
        )
        if create_response.status_code != 201:
            return

        chat_id = create_response.json()["id"]

        # List chats
        self.client.get("/api/v1/chats", name="[smoke] GET /api/v1/chats")

        # Get specific chat
        self.client.get(
            f"/api/v1/chats/{chat_id}",
            name="[smoke] GET /api/v1/chats/{id}",
        )

        # Send message (critical path)
        self.client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Smoke test message - please respond briefly."},
            name="[smoke] POST /api/v1/chats/{id}/messages",
        )

        # Get messages
        self.client.get(
            f"/api/v1/chats/{chat_id}/messages",
            name="[smoke] GET /api/v1/chats/{id}/messages",
        )

        # Update chat
        self.client.patch(
            f"/api/v1/chats/{chat_id}",
            json={"title": "Smoke Test - Updated"},
            name="[smoke] PATCH /api/v1/chats/{id}",
        )

        # Delete chat (cleanup)
        self.client.delete(
            f"/api/v1/chats/{chat_id}",
            name="[smoke] DELETE /api/v1/chats/{id}",
        )
