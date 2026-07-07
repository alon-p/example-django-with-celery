# Django + Celery — a reference pattern for AI coding agents

This repo is **not** a starter you clone and run. It's a reference
implementation of *how to add Celery to a Django project*, written to be **read
by an AI coding agent** and transplanted into **your** project.

## How to use it

In your own project, point your agent at the recipe and let it apply the pattern:

```text
Read CELERY_PATTERN.md at
https://github.com/alon-p/example-django-with-celery/blob/main/CELERY_PATTERN.md
and apply the same Celery integration to this project, adapting the project and app names to mine.
```

Prefer having the agent read the **raw file by URL** over cloning this repo into
your workspace — that keeps this repo's own agent-instruction files
(`AGENTS.md`, `CLAUDE.md`) out of your project's context.

## What it demonstrates

A minimal, opinionated Celery setup you can lift piece by piece:

- **Celery app bootstrap** — `example_django_with_celery/celery.py` and the
  package `__init__.py` re-export that makes tasks register.
- **Config in Django settings, per environment** — broker URL, an env-var eager
  toggle for local dev, and always-eager in tests so the suite needs no broker
  (`example_django_with_celery/settings.py`).
- **A thin task delegating to a service** — `app_example/tasks.py` +
  `app_example/services/notification_service.py`.
- **Dispatching from a view** with `.delay()` — `app_example/views.py`.
- **A test that exercises the task with no worker/broker** —
  `app_example/tests/test_send_notification.py`.
- **Broker + worker as docker-compose services** — the `redis` and
  `celery_worker` services in `docker-compose.yml`.

## The recipe

The full, file-by-file guide — every change, the reasoning behind it, plain-Django
adaptations, and the identifiers to rename — lives in
**[CELERY_PATTERN.md](./CELERY_PATTERN.md)**.