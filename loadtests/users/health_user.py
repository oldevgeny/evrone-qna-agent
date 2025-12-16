"""Health check user scenarios."""

from locust import task

from loadtests.users.base import BaseAPIUser


class HealthUser(BaseAPIUser):
    """User that simulates health check probes.

    Represents monitoring systems and Kubernetes probes that
    periodically check application health.
    """

    weight = 1  # Low weight - background monitoring

    @task(5)
    def basic_health(self) -> None:
        """Basic health check."""
        self.client.get("/health", name="/health [GET]")

    @task(3)
    def liveness_probe(self) -> None:
        """Kubernetes liveness probe."""
        self.client.get("/health/live", name="/health/live [GET]")

    @task(2)
    def readiness_probe(self) -> None:
        """Kubernetes readiness probe (includes DB check)."""
        with self.client.get(
            "/health/ready",
            name="/health/ready [GET]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ready":
                    response.success()
                else:
                    response.failure(f"Not ready: {data.get('status')}")
            else:
                response.failure(f"Status: {response.status_code}")
