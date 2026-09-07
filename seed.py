import random
import string
from faker import Faker
from sqlalchemy import create_engine, text

# Initialize Faker with Indian locale
fake = Faker('en_IN')

# --- CONFIGURATION ---
DB_USER = "root"
DB_PASS = "ajk123"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "enterprise_audit_db"

BATCH_SIZE = 1000
TOTAL_RECORDS = 5000

# Helper generators for Indian identifiers
def generate_pan():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    entity = random.choice(['P', 'C', 'H', 'F', 'A', 'T', 'B', 'L', 'J', 'G'])
    last_name_init = random.choice(string.ascii_uppercase)
    digits = ''.join(random.choices(string.digits, k=4))
    check = random.choice(string.ascii_uppercase)
    return f"{letters}{entity}{last_name_init}{digits}{check}"

def generate_aadhaar():
    # 12-digit number, cannot start with 0 or 1
    first = str(random.randint(2, 9))
    rest = ''.join(random.choices(string.digits, k=11))
    return f"{first}{rest}"

def generate_upi(name):
    handle = name.lower().replace(' ', '').replace('.', '')[:10]
    provider = random.choice(['okaxis', 'okhdfcbank', 'ybl', 'paytm', 'icici'])
    return f"{handle}{random.randint(10, 99)}@{provider}"

def generate_free_text_note():
    # 20% chance of an accidental leak inside unstructured notes
    if random.random() < 0.20:
        leak_type = random.choice(['pan', 'aadhaar', 'card'])
        if leak_type == 'pan':
            return f"Customer mentioned their PAN is {generate_pan()} during verification call."
        elif leak_type == 'aadhaar':
            return f"KYC pending document submission. Aadhaar cited: {generate_aadhaar()}."
        else:
            return f"Refund disputed for card ending in {random.randint(1000, 9999)}. Trace ID: TXN-{random.randint(100000, 999999)}."
    return random.choice([
        "Customer requested an address update via net banking.",
        "Query resolved regarding transaction failure charges.",
        "Account statement dispatched to registered email.",
        "KYC renewal notification sent via SMS.",
        "Routine profile maintenance check completed."
    ])

def seed_database():
    # Connect to MySQL server and ensure database exists
    server_engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}")
    with server_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};"))
        conn.commit()

    # Connect to the created database
    db_engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    with db_engine.connect() as conn:
        print("Creating tables...")
        conn.execute(text("DROP TABLE IF EXISTS audit_logs;"))
        conn.execute(text("DROP TABLE IF EXISTS financial_profiles;"))
        conn.execute(text("DROP TABLE IF EXISTS customers;"))

        # Table 1: Demographics (DPDP PII)
        conn.execute(text("""
            CREATE TABLE customers (
                customer_id INT PRIMARY KEY AUTO_INCREMENT,
                full_name VARCHAR(150),
                email VARCHAR(150),
                phone_number VARCHAR(20),
                aadhaar_number VARCHAR(12),
                date_of_birth DATE,
                residential_city VARCHAR(100)
            );
        """))

        # Table 2: Financials (RBI Sensitive)
        conn.execute(text("""
            CREATE TABLE financial_profiles (
                profile_id INT PRIMARY KEY AUTO_INCREMENT,
                customer_id INT,
                pan_number VARCHAR(10),
                upi_identifier VARCHAR(100),
                credit_card_mask VARCHAR(19),
                annual_income DECIMAL(12, 2),
                credit_score INT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
            );
        """))

        # Table 3: Unstructured Notes (Testing LLM Fallback)
        conn.execute(text("""
            CREATE TABLE audit_logs (
                log_id INT PRIMARY KEY AUTO_INCREMENT,
                customer_id INT,
                agent_id VARCHAR(20),
                interaction_notes TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
            );
        """))
        conn.commit()

        print(f"Generating and inserting {TOTAL_RECORDS} records in batches...")

        customer_insert = text("""
            INSERT INTO customers (full_name, email, phone_number, aadhaar_number, date_of_birth, residential_city)
            VALUES (:full_name, :email, :phone_number, :aadhaar_number, :date_of_birth, :residential_city)
        """)

        financial_insert = text("""
            INSERT INTO financial_profiles (customer_id, pan_number, upi_identifier, credit_card_mask, annual_income, credit_score)
            VALUES (:customer_id, :pan_number, :upi_identifier, :credit_card_mask, :annual_income, :credit_score)
        """)

        audit_insert = text("""
            INSERT INTO audit_logs (customer_id, agent_id, interaction_notes)
            VALUES (:customer_id, :agent_id, :interaction_notes)
        """)

        # Insert records in batches
        for start_idx in range(1, TOTAL_RECORDS + 1, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, TOTAL_RECORDS + 1)
            
            customer_batch = []
            financial_batch = []
            audit_batch = []

            for cid in range(start_idx, end_idx):
                name = fake.name()
                customer_batch.append({
                    "full_name": name,
                    "email": fake.email(),
                    "phone_number": f"+91{random.randint(6000000000, 9999999999)}",
                    "aadhaar_number": generate_aadhaar(),
                    "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=75),
                    "residential_city": fake.city()
                })

                financial_batch.append({
                    "customer_id": cid,
                    "pan_number": generate_pan(),
                    "upi_identifier": generate_upi(name),
                    "credit_card_mask": fake.credit_card_number(card_type=None),
                    "annual_income": round(random.uniform(300000, 4500000), 2),
                    "credit_score": random.randint(300, 850)
                })

                audit_batch.append({
                    "customer_id": cid,
                    "agent_id": f"AGT-{random.randint(100, 999)}",
                    "interaction_notes": generate_free_text_note()
                })

            conn.execute(customer_insert, customer_batch)
            conn.execute(financial_insert, financial_batch)
            conn.execute(audit_insert, audit_batch)
            conn.commit()
            print(f"  Inserted up to record {end_idx - 1}...")

    print("\nDatabase seeded successfully!")

if __name__ == "__main__":
    seed_database()