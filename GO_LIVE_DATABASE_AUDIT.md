# Go-Live Database Audit

## Review date
16 April 2026

## Current evidence
Live database counts at review time:
- RACE: 28 rows
- RACE_ENTRY: 472 rows
- LAP: 475 rows
- SAILORCONTROL: 128 rows
- BOATCONTROL: 149 rows
- RACE_RESULT_AUDIT: 10 rows
- RACE_RESULT_REVISION: 10 rows

Current table sizes are very small, with the largest reviewed table still only in the low hundreds of kilobytes.

## Verdict
The database is fit for purpose for go-live at the current scale.

There is no immediate performance concern with the present data volume. The main risk was not current size, but future growth without the right indexes and query patterns.

## Hardening completed
The following improvements have already been applied:
- added a database hardening migration in [migrate_p1_database_hardening.py](migrate_p1_database_hardening.py)
- updated startup schema indexes in [init.d/init.sql](init.d/init.sql)
- replaced index-blocking date filters in [app/services/club_dashboard_repository.py](app/services/club_dashboard_repository.py) and [app/services/duty_repository.py](app/services/duty_repository.py)

## Performance horizon
You are unlikely to feel meaningful database slowdown in the immediate term.

A reasonable planning guide is:
- safe and comfortable: current size through many months or several seasons of use
- watch closely: when RACE grows into the thousands and LAP grows beyond about 100,000 rows
- likely need stronger mitigation: when LAP and audit tables approach 250,000 to 1,000,000+ rows, or if multiple clubs are active concurrently

## What will become slow first
The first pressure points will usually be:
- dashboard race listings by club and date
- race result aggregation across RACE_ENTRY and LAP
- audit and revision history growth
- login and member lookups if the user base becomes much larger

## Recommended mitigation plan
### Now
- keep the new indexes in place
- continue running regression tests before release
- keep one canonical production database path and backup plan

### Before medium growth
- enable query monitoring such as pg_stat_statements
- review slow queries quarterly with EXPLAIN ANALYZE
- make sure autovacuum and ANALYZE are healthy in production
- keep backups and restore drills current

### Before large growth
- archive or prune old audit and revision rows
- partition LAP and possibly audit tables by season or year
- add a connection pooler if concurrent users increase materially
- consider materialized summaries for expensive dashboard aggregations

## Operational recommendation
For launch, the database is ready.

For scale, the best mitigation is to monitor growth early and treat LAP and audit history as the first candidates for partitioning or archival.
