# dbt_project/CLAUDE.md

dbt analytics layer - transforms raw events into aggregated metrics.

## Structure

```
dbt_project.yml   → Project config, model materialization settings
profiles.yml      → Database connection (uses DATABASE_URL)
models/
  staging/
    stg_sales_events.sql  → Cleaned raw events (VIEW)
    schema.yml            → Column docs and tests
  marts/
    dim_user_stats.sql         → Lifetime user statistics (TABLE)
    fct_daily_performance.sql  → Daily aggregates (TABLE)
    schema.yml
```

## Model Materialization

- **staging/** models: `VIEW` (lightweight, always current)
- **marts/** models: `TABLE` (materialized for query performance)

## Key Variables (in dbt_project.yml)

```yaml
vars:
  raw_events_retention_days: 90
  xp_per_level: 1000
  rank_thresholds:
    iron: 0
    bronze: 200
    # ...
```

## Commands

```bash
cd dbt_project

dbt run                           # Run all models
dbt run --select stg_sales_events # Run specific model
dbt run --select marts.*          # Run all marts
dbt test                          # Run data quality tests
dbt docs generate && dbt docs serve  # Generate docs at localhost:8080
```

## Adding a Model

1. Create `.sql` file in appropriate folder (`staging/` or `marts/`)
2. Add column documentation in `schema.yml`
3. Add tests in `schema.yml` (unique, not_null, accepted_values)
4. Run `dbt run --select model_name` to test

## Staging vs Marts

**Staging:** Light transformations, renaming, type casting. Source of truth for downstream models.

**Marts:** Business logic, aggregations, calculated fields. Consumed by the HUD and reporting.

## Docs

- dbt: https://docs.getdbt.com/
- dbt-postgres: https://docs.getdbt.com/docs/core/connect-data-platform/postgres-setup
