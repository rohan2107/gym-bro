# Database Migrations with Alembic

This directory contains database migration scripts managed by Alembic.

## Commands

### Create a new migration
```bash
cd gymbro-api
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply to a specific revision
alembic upgrade <revision_id>
```

### Rollback migrations
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### View migration history
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --indicate-current
```

## Workflow

1. **Make changes to models** in `app/models.py`

2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Add new field to User model"
   ```

3. **Review the generated migration** in `alembic/versions/`
   - Verify the upgrade() and downgrade() functions
   - Make any manual adjustments if needed

4. **Test the migration**:
   ```bash
   # Apply
   alembic upgrade head
   
   # Rollback if needed
   alembic downgrade -1
   ```

5. **Commit the migration** to version control

## Tips

- Always review auto-generated migrations before applying
- Test migrations on a development database first
- Keep migrations small and focused
- Write descriptive commit messages for migrations
- Never edit applied migrations; create a new one instead

## Configuration

Migration settings are in `alembic.ini`. The database URL is automatically loaded from `app/config.py` settings.

## Initial Setup

The initial database schema is created using SQLModel's `create_all()` in development. For production, use Alembic migrations:

```bash
# Generate initial migration from current models
alembic revision --autogenerate -m "Initial schema"

# Apply to production database
alembic upgrade head
```
