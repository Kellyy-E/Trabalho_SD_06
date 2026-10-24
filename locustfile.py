import os
import random
import gevent
from locust import HttpUser, task, between, events

WARMUP_SECONDS = int(os.getenv("LOCUST_WARMUP_SECONDS", "60"))


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    # Reseta as estatisticas apos o tempo de aquecimento (1 min)
    if WARMUP_SECONDS > 0 and environment.runner is not None:
        def reset_after_warmup():
            gevent.sleep(WARMUP_SECONDS)
            if environment.runner and environment.runner.state not in ("stopped", "stopping"):
                environment.runner.stats.reset_all()
                print(f"[Warm-up] {WARMUP_SECONDS}s concluidos. Estatisticas resetadas.")

        gevent.spawn(reset_after_warmup)


class BasePetClinicUser(HttpUser):
    abstract = True
    wait_time = between(0.5, 1.5)
    known_owner_ids = list(range(1, 11))

    def _get_owners(self):
        self.client.get("/api/customer/owners", name="GET /owners")

    def _get_owner_by_id(self):
        owner_id = random.choice(self.known_owner_ids)
        self.client.get(f"/api/customer/owners/{owner_id}", name="GET /owners/{id}")

    def _get_vets(self):
        self.client.get("/api/vet/vets", name="GET /vets")

    def _post_owner(self):
        suffix = random.randint(1000, 999999)
        payload = {
            "firstName": f"User{suffix}",
            "lastName": f"Test{suffix}",
            "address": f"{random.randint(1, 999)} Main St",
            "city": random.choice(["Madison", "Sun Prairie", "McFarland", "Windsor", "Monona"]),
            "telephone": f"608555{random.randint(1000, 9999)}"
        }
        with self.client.post(
            "/api/customer/owners",
            json=payload,
            name="POST /owners",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201):
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:120]}")


class Perfil1Leitura(BasePetClinicUser):
    # Pesos proporcionais a 45%, 35%, 15% e 5%
    @task(9)
    def get_owners(self):
        self._get_owners()

    @task(7)
    def get_owner_by_id(self):
        self._get_owner_by_id()

    @task(3)
    def get_vets(self):
        self._get_vets()

    @task(1)
    def post_owner(self):
        self._post_owner()


class Perfil2Escrita(BasePetClinicUser):
    # Pesos proporcionais a 20%, 20%, 20% e 40%
    @task(1)
    def get_owners(self):
        self._get_owners()

    @task(1)
    def get_owner_by_id(self):
        self._get_owner_by_id()

    @task(1)
    def get_vets(self):
        self._get_vets()

    @task(2)
    def post_owner(self):
        self._post_owner()
