# Celery + Django — transplant recipe

**You are an AI agent reading this to add Celery to a *different* Django
project.** This file is the pattern. Below is every file that changes, the exact
code, and *why* each piece exists. Apply the same shape to the target project,
renaming the two identifiers in the table below.

This repo is the worked example the snippets are taken from. Read the referenced
files in this repo if you want fuller context, but everything you need to
transplant is inline here.

## Before you start: read the target project

Two things about the target project change how you apply this recipe:

1. **Settings style.** This example uses
   [`django-configurations`](https://django-configurations.readthedocs.io/)
   (class-based settings). If the target project uses **plain Django settings**
   (a normal `settings.py` with module-level variables), use the "plain Django"
   variants noted at each step instead of the `values.*` / `configurations.setup()`
   versions.
2. **Names.** Substitute these throughout every snippet:

   | Placeholder in this repo   | Replace with                                   |
   | -------------------------- | ---------------------------------------------- |
   | `example_django_with_celery` | the target project's Django project package (the dir containing `settings.py`) |
   | `app_example`              | the target app you're adding the task to        |

Also confirm the target has a **broker available** (this example uses Redis).
If not, add one (see Step 7).

---

## Step 1 — Dependencies

Add `celery` and, for a Redis broker, `redis`.

`pyproject.toml` (Poetry):
```toml
celery = "^5.6.3"
redis = "^8.0.1"
```

Adapt to the target's tool: `pip install celery redis` / add to
`requirements.txt` / `uv add celery redis`. Match the target's existing
dependency workflow — don't introduce Poetry if the project doesn't use it.

---

## Step 2 — Create the Celery app (`example_django_with_celery/celery.py`)

This is the Celery bootstrap. It lives next to `settings.py`.

```python
import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_django_with_celery.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Development")

import configurations

configurations.setup()

app = Celery("example_django_with_celery")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
```

**Why each line:**
- `setdefault("DJANGO_SETTINGS_MODULE", ...)` — the worker is a standalone
  process; it must know which settings to load.
- `DJANGO_CONFIGURATION` + `import configurations` + `configurations.setup()` —
  **this project uses django-configurations, so Django is bootstrapped via
  `configurations.setup()` rather than the usual `django.setup()`.** The import
  is placed *after* the env vars are set because it reads them.
- `config_from_object("django.conf:settings", namespace="CELERY")` — Celery
  reads its config from Django settings, but only settings **prefixed
  `CELERY_`** (e.g. `CELERY_BROKER_URL` → Celery's `broker_url`). This is what
  lets you keep all config in `settings.py`.
- `autodiscover_tasks(...)` — auto-imports a `tasks.py` from every installed app,
  so you never hand-register tasks.

> **Plain Django variant:** drop the `DJANGO_CONFIGURATION` line, the
> `import configurations`, and `configurations.setup()`; replace with the
> standard `app.config_from_object("django.conf:settings", namespace="CELERY")`
> as-is (it already works). Django's app registry loads lazily via
> `autodiscover_tasks`, so no explicit `django.setup()` is needed here.

---

## Step 3 — Wire it into the package (`example_django_with_celery/__init__.py`)

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

**Why:** this import runs at Django startup and guarantees the Celery `app` is
created and `@shared_task`s attach to it. **Skipping this is the most common
reason tasks silently don't register.** Keep whatever else already lives in the
package `__init__.py` and add these lines.

---

## Step 4 — Configuration in `settings.py`

All Celery config is `CELERY_`-prefixed and grouped per environment.

**Base** (shared) — the broker:
```python
# An example of a celery config
CELERY_BROKER_URL = values.Value(
    "redis://localhost:6379/0",
    environ_prefix="",
    environ_name="CELERY_BROKER_URL",
)
CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": "example_django_with_celery"}
```
- `CELERY_BROKER_URL` — where tasks are queued.
- `environ_prefix="", environ_name="CELERY_BROKER_URL"` — without these,
  django-configurations defaults to reading `DJANGO_CELERY_BROKER_URL`. That
  silently ignores the plain `CELERY_BROKER_URL` env var that docker-compose
  and production set (Step 7), leaving every environment pointed at
  `localhost` instead of the real broker.
- `global_keyprefix` — namespaces all keys in Redis, so multiple apps can safely
  share one Redis instance without colliding.

**Development** — let a developer force synchronous execution via env var:
```python
# An example of a celery eager config for the development environment
CELERY_TASK_ALWAYS_EAGER = values.BooleanValue(
    default=False, environ_prefix="CELERY", environ_name="TASK_ALWAYS_EAGER"
)
```
When eager, `.delay()` runs the task **inline in the caller** instead of sending
it to a worker — handy when you don't want to run a worker locally.

**Testing** — always eager, so tests need no broker and no worker:
```python
# An example of a skipping celery in testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```
`EAGER_PROPAGATES` re-raises exceptions from inside the task so tests can assert
on them.

**Staging/Production** — point the broker at the managed Redis:
```python
# An example of a celery config for the staging environment using redis cloud on heroku
CELERY_BROKER_URL = values.Value(environ_prefix="", environ_name="REDISCLOUD_URL")
```

> **Plain Django variant:** these become plain module-level assignments, split
> across your settings files/branches. Minimum viable set:
> ```python
> CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
> # in your test settings:
> CELERY_TASK_ALWAYS_EAGER = True
> CELERY_TASK_EAGER_PROPAGATES = True
> ```

---

## Step 5 — A task, and the service it calls

Keep the task **thin**: it's a queue entry point that delegates to a plain
function. Business logic stays testable and callable without Celery.

`app_example/tasks.py`:
```python
from celery import shared_task

from app_example.services.notification_service import send_notification


# An example task
@shared_task
def send_notification_task(content: str):
    send_notification(content=content)
```

`app_example/services/notification_service.py` (the real work):
```python
import logging

logger = logging.getLogger(__name__)


# An example of a service that celery can call
def send_notification(content: str):
    logger.info(f"Sending notification: {content}")
    return True
```

- `@shared_task` (not `@app.task`) — the task isn't bound to a specific Celery
  app instance, which is what lets `autodiscover_tasks` pick it up from any app.
- The task file **must** be named `tasks.py` for autodiscovery to find it.

---

## Step 6 — Dispatch the task (`app_example/views.py`)

```python
from django.http import JsonResponse
from app_example.tasks import send_notification_task


# An example view calling a celery task
def notify(request):
    send_notification_task.delay("hello celery task")
    return JsonResponse({"status": "OK"})
```

`.delay(...)` enqueues and returns immediately (unless eager). The request
finishes without waiting for the notification. This is the whole point:
work happens **out of the request/response cycle**.

---

## Step 7 — Run the worker & broker

**Locally**, with a broker running:
```bash
celery -A example_django_with_celery worker --loglevel=INFO
```

**With docker-compose**, add a broker service and a worker service. From this
repo's `docker-compose.yml`:

```yaml
  redis:
    container_name: redis_example_django_with_celery
    image: redis:latest
    hostname: redis
    ports:
      - "6379:6379"
    healthcheck:
      test: [ "CMD-SHELL", "redis-cli ping | grep PONG" ]
      interval: 1s
      timeout: 3s
      retries: 5

  celery_worker:
    build:
      context: .
      dockerfile: ./ecs/Dockerfile   # reuse the same image as the web service
    environment:
      - DJANGO_CONFIGURATION=Development
      - DJANGO_SETTINGS_MODULE=example_django_with_celery.settings
      - DATABASE_URL=postgresql://...@db/...   # match the web service
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_TASK_ALWAYS_EAGER=False
    command:
      - bash
      - -c
      - celery -A example_django_with_celery worker --loglevel=DEBUG
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

Key points to carry over:
- The worker **reuses the web service's image and environment** — same code,
  same settings, just a different `command`.
- It depends on the broker being healthy.
- `CELERY_TASK_ALWAYS_EAGER=False` here ensures work actually goes through the
  worker (not inline) in this container.

---

## Step 8 — Test without a broker

Because Testing sets `CELERY_TASK_ALWAYS_EAGER = True` (Step 4), `.delay()` runs
inline, so a normal view test exercises the task end-to-end with no worker.

`app_example/tests/test_send_notification.py`:
```python
def test_log_was_created_after_notification_sent(self):
    with self.assertLogs(
        "app_example.services.notification_service", level="INFO"
    ) as logs:
        response = self.client.get(self.path)

    self.assertIn(
        "INFO:app_example.services.notification_service:Sending notification: hello celery task",
        logs.output[0],
    )
```

The test hits the view, the view calls `.delay()`, eager mode runs the task
synchronously, the service logs — and the test asserts on the log. No Celery
infrastructure involved.

---

## Rename checklist (do this before you finish)

- [ ] Replaced **every** `example_django_with_celery` with the target project package,
      including the `global_keyprefix` value in `CELERY_BROKER_TRANSPORT_OPTIONS` (Step 4).
- [ ] Replaced **every** `app_example` with the target app.
- [ ] `Celery("...")` in `celery.py` uses the target project name.
- [ ] `-A <project>` in the worker command uses the target project name.
- [ ] `celery.py` uses the target's bootstrap (django-configurations *or* plain).
- [ ] Package `__init__.py` imports `celery_app` (Step 3).
- [ ] Test settings set `CELERY_TASK_ALWAYS_EAGER = True`.
- [ ] A broker (Redis or equivalent) is available in every environment that runs a worker.

## Verify it works

1. **Eager path (no infra):** set eager mode and confirm a view that calls
   `.delay()` runs the task inline — the existing test pattern in Step 8 covers this.
2. **Real path:** start the broker + worker, hit the view, and confirm the task
   runs in the **worker's** logs (not the web process).