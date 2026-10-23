## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Core Data & Pipeline Invariants (ANTI-REGRESSION RULES)

To prevent hallucinations and breaking existing functionality when making changes:

1. **Pending Follow-up Invariant**:
   - Pending follow-ups must NEVER be 0 when processing the full REDCap dataset. Normal range is ~3,500 to ~4,000 pending babies.
   - A baby is classified as **Pending** if:
     `is_live_born` is True, `is_stillbirth` is False, `is_dead` is False, AND Call 3 status is empty / not in `['Healthy', 'Dead', 'Sick', 'Completed']`.
   - In `generate_dashboard.py`, `babies = []` MUST ALWAYS be initialized per row right before `for b_conf in baby_configs:`.

2. **Vital Statistics Invariants**:
   - `total_neonatal_deaths` must be > 1,000 (currently ~1,153).
   - `total_stillbirths` must be > 800 (currently ~862).
   - `total_discrepancies` must be > 10,000 (currently ~12,246).

3. **Mandatory Verification Workflow After Any Code Edit**:
   - Step 1: Run `python -m py_compile generate_dashboard.py` to check for syntax/variable errors.
   - Step 2: If generating dashboard data, run `python generate_dashboard.py` and ensure exit code 0.
   - Step 3: Run `python test_dashboard_integrity.py` to verify all business rules and invariants pass.
   - Step 4: Run `graphify update .` to keep the knowledge graph synchronized.
