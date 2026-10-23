"""
Automated Integrity & Regression Test Suite for REDCap Follow-up Dashboard
Ensures critical metrics, pending follow-ups, discrepancy validation, and data integrity
are preserved and prevents accidental regressions or hallucinations during edits.
"""
import sys
import json
import os
import py_compile

def run_tests():
    print("=" * 60)
    print("   RUNNING REDCAP DASHBOARD INTEGRITY & REGRESSION TESTS    ")
    print("=" * 60)

    # 1. Python Syntax & Compilation Check
    print("\n[TEST 1] Checking Python syntax of generate_dashboard.py...")
    try:
        py_compile.compile('generate_dashboard.py', doraise=True)
        print("  --> PASS: generate_dashboard.py syntax is valid.")
    except py_compile.PyCompileError as e:
        print(f"  --> FAIL: Syntax error in generate_dashboard.py:\n{e}")
        return False

    # 2. Check existence of generated artifacts
    print("\n[TEST 2] Verifying generated artifacts...")
    json_path = os.path.join('templates', 'dashboard_data.json')
    js_data_path = 'dashboard_data.js'
    html_path = 'index.html'

    if not os.path.exists(json_path):
        print(f"  --> FAIL: Missing {json_path}")
        return False
    if not os.path.exists(js_data_path):
        print(f"  --> FAIL: Missing {js_data_path}")
        return False
    if not os.path.exists(html_path):
        print(f"  --> FAIL: Missing {html_path}")
        return False

    html_size_kb = os.path.getsize(html_path) / 1024
    js_data_mb = os.path.getsize(js_data_path) / (1024 * 1024)
    if html_size_kb < 10.0:
        print(f"  --> FAIL: index.html is suspiciously small ({html_size_kb:.2f} KB)")
        return False
    if js_data_mb < 5.0:
        print(f"  --> FAIL: dashboard_data.js is suspiciously small ({js_data_mb:.2f} MB)")
        return False
    print(f"  --> PASS: Artifacts exist (Lightweight HTML: {html_size_kb:.1f} KB, Data JS: {js_data_mb:.2f} MB).")

    # 3. Parse JSON and check structure
    print("\n[TEST 3] Inspecting dashboard_data.json schema and invariants...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  --> FAIL: Failed to parse {json_path}: {e}")
        return False

    # Check required top-level keys
    required_keys = [
        'metadata', 'activity_report', 'overall_list', 'pending_list', 'lost_to_followup_list',
        'neonatal_deaths_list', 'stillbirths_list', 'out_of_range_deaths_list',
        'home_deliveries_list', 'out_district_deliveries_list', 'sncu_deaths_list'
    ]
    for k in required_keys:
        if k not in data:
            print(f"  --> FAIL: Missing key '{k}' in dashboard_data.json")
            return False

    overall_list = data.get('overall_list', [])
    pending_list = data.get('pending_list', [])
    lost_list = data.get('lost_to_followup_list', [])
    nd_list = data.get('neonatal_deaths_list', [])
    sb_list = data.get('stillbirths_list', [])
    disc_count = sum(1 for r in overall_list if r.get('has_disc'))

    print(f"  * Total Overall Records: {len(overall_list):,}")
    print(f"  * Total Pending Follow-ups: {len(pending_list):,}")
    print(f"  * Total Lost to Follow-up: {len(lost_list):,}")
    print(f"  * Total Neonatal Deaths: {len(nd_list):,}")
    print(f"  * Total Stillbirths: {len(sb_list):,}")
    print(f"  * Total Records with Discrepancies: {disc_count:,}")

    # Critical Invariant Checks
    if len(overall_list) < 10000:
        print(f"  --> FAIL: Total records unexpectedly low ({len(overall_list)})")
        return False

    # PENDING FOLLOW-UP INVARIANT: MUST NEVER BE 0!
    if len(pending_list) <= 0:
        print(f"  --> REGRESSION FAILURE: Pending follow-ups is {len(pending_list)}! Must be > 0!")
        return False

    # Neonatal Deaths Invariant: MUST NEVER BE 0!
    if len(nd_list) <= 0:
        print(f"  --> REGRESSION FAILURE: Neonatal deaths is {len(nd_list)}! Must be > 0!")
        return False

    # Stillbirths Invariant: MUST NEVER BE 0!
    if len(sb_list) <= 0:
        print(f"  --> REGRESSION FAILURE: Stillbirths is {len(sb_list)}! Must be > 0!")
        return False

    # Discrepancies Invariant: MUST NEVER BE 0!
    if disc_count <= 0:
        print(f"  --> REGRESSION FAILURE: Discrepancy count is {disc_count}! Must be > 0!")
        return False

    print("  --> PASS: All top-level metric invariants satisfied.")

    # 4. Deep Inspection of Pending Records & Baby Logic
    print("\n[TEST 4] Validating pending baby logic and record properties...")
    sample_pending = pending_list[:50]
    required_pending_baby_keys = ['baby_id', 'birth_status', 'sex', 'status', 'followup_coord', 'call_statuses']
    for idx, p in enumerate(sample_pending):
        babies = p.get('babies', [])
        if not babies:
            print(f"  --> FAIL: Pending item #{idx} (ID: {p.get('id')}) has no babies listed!")
            return False
        has_pending_baby = any(b.get('status') == 'Pending' for b in babies)
        if not has_pending_baby:
            print(f"  --> FAIL: Pending item #{idx} (ID: {p.get('id')}) has no baby with status 'Pending'!")
            return False
        for b in babies:
            for bk in required_pending_baby_keys:
                if bk not in b:
                    print(f"  --> FAIL: Pending baby #{idx} missing key '{bk}'!")
                    return False

    print(f"  --> PASS: Verified {len(sample_pending)} sample pending records contain valid Pending babies.")

    # 5. Deep Inspection of Baby Structure in overall_list
    print("\n[TEST 5] Validating baby structure across records...")
    sample_overall = overall_list[:50]
    required_baby_keys = ['baby_id', 'status', 'sex', 'is_stillbirth', 'is_neonatal_death', 'call_statuses', 'call_dates']
    for idx, r in enumerate(sample_overall):
        for b in r.get('babies', []):
            for bk in required_baby_keys:
                if bk not in b:
                    print(f"  --> FAIL: Baby record in row #{idx} missing key '{bk}'!")
                    return False
    print(f"  --> PASS: Verified baby structure across {len(sample_overall)} overall sample records.")

    # 6. Deep Inspection of Discrepancy structure
    print("\n[TEST 6] Validating discrepancy categorization...")
    records_with_disc = [r for r in overall_list if r.get('disc_notif_reg') or r.get('disc_day29')]
    if len(records_with_disc) == 0:
        print("  --> FAIL: No records found with categorized discrepancies (disc_notif_reg or disc_day29)!")
        return False
    print(f"  --> PASS: Found {len(records_with_disc):,} records with classified discrepancies.")

    # 7. Deep Inspection of Neonatal Deaths Structure
    print("\n[TEST 7] Validating neonatal deaths structure (mother, husband, MP/RCH ID)...")
    sample_nd = nd_list[:50]
    required_nd_keys = ['id', 'mother_name', 'husband_name', 'mp_id_rch', 'baby_num', 'sex', 'weight', 'delivery_date', 'death_date']
    for idx, nd in enumerate(sample_nd):
        for k in required_nd_keys:
            if k not in nd:
                print(f"  --> FAIL: Neonatal death #{idx} missing key '{k}'!")
                return False
    print(f"  --> PASS: Verified {len(sample_nd)} neonatal death sample records contain required fields.")

    print("\n" + "=" * 60)
    print("     ALL INTEGRITY & REGRESSION TESTS PASSED SUCCESSFULLY!    ")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
