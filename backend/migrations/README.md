Alembic migration scripts for the Zytlog backend.

## Usage

From repository root:

```bash
alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini downgrade -1
```

## Notes

- `env.py` reads SQLAlchemy metadata from `backend.db.base.Base` and model imports from `backend.models`.
- Database URL is taken from backend settings (`DATABASE_URL` environment variable).
- Initial revision: `20260330_0001_initial_foundation.py`.
