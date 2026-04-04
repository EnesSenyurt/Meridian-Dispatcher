import random
import string
import time
from locust import HttpUser, task, between, events


def random_suffix(length=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


class DispatcherUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Her sanal kullanıcı başlangıçta bir kez register + login yapar."""
        suffix = random_suffix()
        self.email = f"user_{suffix}@loadtest.com"
        self.password = "TestPass123!"
        self.token = None
        self.delivery_id = None

        # Register
        register_payload = {
            "email": self.email,
            "password": self.password,
            "role": random.choice(["sender", "courier"]),
        }
        with self.client.post(
            "/auth/register",
            json=register_payload,
            catch_response=True,
            name="POST /auth/register",
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"Register failed: {resp.status_code} {resp.text[:200]}")
                return

        # Login
        login_payload = {
            "email": self.email,
            "password": self.password,
        }
        with self.client.post(
            "/auth/login",
            json=login_payload,
            catch_response=True,
            name="POST /auth/login",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token") or data.get("token")
                if not self.token:
                    resp.failure(f"No token in login response: {data}")
            else:
                resp.failure(f"Login failed: {resp.status_code} {resp.text[:200]}")

    def _auth_headers(self):
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    # ------------------------------------------------------------------ #
    # Delivery CRUD
    # ------------------------------------------------------------------ #

    @task(3)
    def create_delivery(self):
        if not self.token:
            return

        suffix = random_suffix(6)
        payload = {
            "sender_id": self.email,
            "recipient_name": f"Recipient {suffix}",
            "recipient_address": f"{random.randint(1, 999)} Test Street, City",
            "recipient_phone": f"+90{random.randint(5000000000, 5999999999)}",
            "package_description": f"Package {suffix} - fragile",
            "status": "pending",
        }
        with self.client.post(
            "/delivery",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
            name="POST /delivery",
        ) as resp:
            if resp.status_code in (200, 201):
                data = resp.json()
                self.delivery_id = data.get("id")
            else:
                resp.failure(f"Create delivery failed: {resp.status_code} {resp.text[:200]}")

    @task(4)
    def list_deliveries(self):
        if not self.token:
            return

        with self.client.get(
            "/delivery",
            params={"limit": 20, "skip": 0},
            headers=self._auth_headers(),
            catch_response=True,
            name="GET /delivery",
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"List deliveries failed: {resp.status_code} {resp.text[:200]}")

    @task(3)
    def get_delivery(self):
        if not self.token or not self.delivery_id:
            return

        with self.client.get(
            f"/delivery/{self.delivery_id}",
            headers=self._auth_headers(),
            catch_response=True,
            name="GET /delivery/{id}",
        ) as resp:
            if resp.status_code == 404:
                # Delivery silinmiş olabilir, sıfırla
                self.delivery_id = None
            elif resp.status_code != 200:
                resp.failure(f"Get delivery failed: {resp.status_code} {resp.text[:200]}")

    @task(2)
    def update_delivery(self):
        if not self.token or not self.delivery_id:
            return

        statuses = ["pending", "in_transit", "delivered", "cancelled"]
        payload = {
            "status": random.choice(statuses),
            "package_description": f"Updated package {random_suffix(4)}",
        }
        with self.client.put(
            f"/delivery/{self.delivery_id}",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
            name="PUT /delivery/{id}",
        ) as resp:
            if resp.status_code == 404:
                self.delivery_id = None
            elif resp.status_code not in (200, 201):
                resp.failure(f"Update delivery failed: {resp.status_code} {resp.text[:200]}")

    @task(1)
    def delete_delivery(self):
        if not self.token or not self.delivery_id:
            return

        del_id = self.delivery_id
        self.delivery_id = None  # Önce sıfırla, sonra sil

        with self.client.delete(
            f"/delivery/{del_id}",
            headers=self._auth_headers(),
            catch_response=True,
            name="DELETE /delivery/{id}",
        ) as resp:
            if resp.status_code not in (200, 204, 404):
                resp.failure(f"Delete delivery failed: {resp.status_code} {resp.text[:200]}")

    # ------------------------------------------------------------------ #
    # Tracking
    # ------------------------------------------------------------------ #

    @task(2)
    def update_tracking_location(self):
        if not self.token or not self.delivery_id:
            return

        payload = {
            "lat": round(random.uniform(36.0, 42.0), 6),
            "lng": round(random.uniform(26.0, 45.0), 6),
            "status": random.choice(["in_transit", "delivered", "pending"]),
        }
        with self.client.post(
            f"/tracking/{self.delivery_id}/location",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
            name="POST /tracking/{id}/location",
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"Update tracking failed: {resp.status_code} {resp.text[:200]}")

    @task(2)
    def get_tracking_location(self):
        if not self.token or not self.delivery_id:
            return

        with self.client.get(
            f"/tracking/{self.delivery_id}/location",
            headers=self._auth_headers(),
            catch_response=True,
            name="GET /tracking/{id}/location",
        ) as resp:
            if resp.status_code == 404:
                resp.success()  # Henüz konum girilmemiş olabilir, beklenen durum
            elif resp.status_code != 200:
                resp.failure(f"Get tracking failed: {resp.status_code} {resp.text[:200]}")
