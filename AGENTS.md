# For AI agents in this repo

**This repo is a reference, not an application to build on.** It exists to teach
one thing: how to add Celery to a Django project.

## If you're here to learn the Celery pattern (most likely)

Read **[CELERY_PATTERN.md](./CELERY_PATTERN.md)**. It's the complete,
file-by-file recipe, written to be transplanted into another project. Ignore the
rest of this file — it's about maintaining *this* repo, not about your target
project, and its conventions (Poetry, etc.) may not apply where you're working.

## If you're maintaining this reference repo

Keep the pattern trustworthy — an agent copies whatever is here, so a broken or
stale example propagates into other people's projects.

- **Keep the Celery wiring correct and runnable.** Before changing the pattern,
  verify tasks still register and a worker consumes a task (see the "Verify"
  section of `CELERY_PATTERN.md`).
- **Single source of truth:** `CELERY_PATTERN.md` explains the pattern; the
  README and code comments link to it rather than re-explaining. Keep them in
  sync when the pattern changes.
- **Don't scope-creep.** Extra Django/DRF features dilute the reference. Only add
  what makes the Celery pattern clearer.
