import os
import hashlib
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv()
db_uri = os.getenv("DB_URI")
if not db_uri:
    print("Error: DB_URI not found in .env")
    exit(1)

# Extract host from DB_URI
# format: postgresql://user:pass@host/dbname?...
host = db_uri.split("@")[1].split("/")[0]
sql_endpoint = f"https://{host}/sql"
print(f"Connecting to Neon HTTP SQL API: {sql_endpoint}")

def run_sql(query: str):
    response = httpx.post(
        sql_endpoint,
        json={"query": query},
        headers={"Neon-Connection-String": db_uri},
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise Exception(f"HTTP {response.status_code} Error: {response.text}")
    return response.json()

# 1. Run migrations in order
migrations_dir = Path(__file__).parent / "migrations"
migration_files = sorted(migrations_dir.glob("*.sql"))

print(f"Found {len(migration_files)} migration files.")

# Ensure schema_migrations table exists
run_sql("""
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""")

for mf in migration_files:
    version = mf.name.split("_")[0]
    sql_text = mf.read_text(encoding="utf-8")
    checksum = hashlib.sha256(sql_text.strip().encode("utf-8")).hexdigest()
    
    # Check if applied
    check_res = run_sql(f"SELECT version FROM schema_migrations WHERE version = '{version}';")
    if check_res.get("rows"):
        print(f"Migration {mf.name} already applied. Skipping.")
        continue
    
    print(f"Applying migration: {mf.name}...")
    run_sql(sql_text)
    run_sql(f"""
    INSERT INTO schema_migrations (version, name, checksum, applied_at)
    VALUES ('{version}', '{mf.name}', '{checksum}', CURRENT_TIMESTAMP)
    ON CONFLICT (version) DO NOTHING;
    """)
    print(f"Successfully applied {mf.name}!")

print("\nAll database migrations are verified and applied!")

# 2. Seed initial sample data if not already present
print("\nSeeding initial demo data...")
from argon2 import PasswordHasher
hasher = PasswordHasher()
pwd_hash = hasher.hash("password123")

seed_statements = [
    # Demo Users
    f"""INSERT INTO users (id, email, password_hash, full_name, phone, role, account_status)
    VALUES 
        ('11111111-1111-1111-1111-111111111111', 'authority@vachan.gov.in', '{pwd_hash}', 'Dr. Aris Thorne', '+91 99000 11223', 'APPROVAL_AUTHORITY', 'ACTIVE'),
        ('22222222-2222-2222-2222-222222222222', 'agent@vachan.in', '{pwd_hash}', 'Rajesh M.', '+91 98401 22334', 'INSURANCE_AGENT', 'ACTIVE'),
        ('33333333-3333-3333-3333-333333333333', 'customer@vachan.in', '{pwd_hash}', 'Ananya Kapoor', '+91 98402 11920', 'CUSTOMER', 'ACTIVE'),
        ('44444444-4444-4444-4444-444444444444', 'vikram.sengupta@example.com', '{pwd_hash}', 'Vikram Sengupta', '+91 98402 11920', 'CUSTOMER', 'ACTIVE')
    ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, account_status = 'ACTIVE';""",

    # Master Policies
    """INSERT INTO policies (id, insurer_name, policy_name, policy_code, category, description, coverage_limit, waiting_period_days, claim_filing_window_days, is_active)
    VALUES
        ('a1111111-1111-1111-1111-111111111111', 'Care Premier Health', 'Care Premier Health Shield', 'VG-HLT-01', 'HOSPITALIZATION', 'Comprehensive inpatient hospitalization with cashless network.', 1500000.00, 730, 30, true),
        ('a2222222-2222-2222-2222-222222222222', 'DriveProtect General', 'Comprehensive Auto DriveProtect', 'VG-MOT-02', 'VEHICLE', 'Motor protection including zero depreciation and roadside telemetry.', 850000.00, 0, 15, true),
        ('a3333333-3333-3333-3333-333333333333', 'Life Horizon Assurance', 'Life Horizon Secure Term', 'VG-TRM-03', 'GENERIC', 'Pure term life protection with critical illness telemetry rider.', 5000000.00, 30, 60, true),
        ('a4444444-4444-4444-4444-444444444444', 'Home Shield Fire & Allied', 'Home Shield Fire & Allied', 'VG-PRP-04', 'GENERIC', 'Structural and contents insurance with catastrophic weather coverage.', 2500000.00, 0, 15, true)
    ON CONFLICT (policy_code) DO NOTHING;""",

    # Policy Versions
    """INSERT INTO policy_versions (id, policy_id, version_number, document_storage_ref, document_checksum, effective_date, is_published)
    VALUES
        ('b1111111-1111-1111-1111-111111111111', 'a1111111-1111-1111-1111-111111111111', 1, 'vault/pol_001_v1.pdf', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '2026-01-01', true),
        ('b2222222-2222-2222-2222-222222222222', 'a2222222-2222-2222-2222-222222222222', 1, 'vault/pol_002_v1.pdf', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '2026-01-01', true)
    ON CONFLICT (policy_id, version_number) DO NOTHING;""",

    # Policy Registrations
    """INSERT INTO policy_registrations (id, customer_id, agent_id, policy_id, policy_version_id, status, customer_consent, consent_notes)
    VALUES
        ('c1111111-1111-1111-1111-111111111111', '44444444-4444-4444-4444-444444444444', '22222222-2222-2222-2222-222222222222', 'a1111111-1111-1111-1111-111111111111', 'b1111111-1111-1111-1111-111111111111', 'AWAITING_CUSTOMER_CONFIRMATION', true, 'Oral affirmative consent captured during biometric telemetry consultation.'),
        ('c2222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222', 'a2222222-2222-2222-2222-222222222222', 'b2222222-2222-2222-2222-222222222222', 'CONFIRMED', true, 'Full consent confirmed with customer signature token.')
    ON CONFLICT (id) DO NOTHING;"""
]

for stmt in seed_statements:
    run_sql(stmt)

print("Demo users, master policies, versions, and registrations seeded into Neon Cloud PostgreSQL successfully!")

# Verify row counts
res_users = run_sql("SELECT count(*) as count FROM users;")
res_policies = run_sql("SELECT count(*) as count FROM policies;")
res_regs = run_sql("SELECT count(*) as count FROM policy_registrations;")
print(f"Verification: {res_users['rows'][0]['count']} Users, {res_policies['rows'][0]['count']} Policies, {res_regs['rows'][0]['count']} Registrations in active DB.")
