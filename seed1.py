import random
import string
from datetime import date, timedelta

from faker import Faker
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURATION
# ============================================================

DB_USER = "root"
DB_PASS = "ajk123"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "nbfc_pii_test"

TOTAL_RECORDS = 10_000
BATCH_SIZE = 1_000

fake = Faker("en_IN")


# ============================================================
# CONSTANTS
# ============================================================

INDIAN_STATES = [
    "Maharashtra",
    "Karnataka",
    "Tamil Nadu",
    "Telangana",
    "Gujarat",
    "Delhi",
    "Rajasthan",
    "Uttar Pradesh",
    "Madhya Pradesh",
    "West Bengal",
    "Bihar",
    "Kerala",
    "Punjab",
    "Haryana",
    "Andhra Pradesh",
    "Odisha",
]

CITIES = [
    "Mumbai",
    "Pune",
    "Nagpur",
    "Nashik",
    "Bengaluru",
    "Mysuru",
    "Chennai",
    "Hyderabad",
    "Ahmedabad",
    "Surat",
    "Delhi",
    "Jaipur",
    "Lucknow",
    "Indore",
    "Kolkata",
    "Kochi",
    "Chandigarh",
    "Patna",
    "Bhopal",
]

LOAN_TYPES = [
    "PERSONAL_LOAN",
    "HOME_LOAN",
    "AUTO_LOAN",
    "GOLD_LOAN",
    "BUSINESS_LOAN",
    "CONSUMER_DURABLE_LOAN",
    "EDUCATION_LOAN",
    "MSME_LOAN",
]

EMPLOYMENT_TYPES = [
    "SALARIED",
    "SELF_EMPLOYED",
    "BUSINESS_OWNER",
    "PROFESSIONAL",
    "RETIRED",
    "STUDENT",
]

ACCOUNT_TYPES = [
    "SAVINGS",
    "CURRENT",
    "SALARY",
]

BANKS = [
    "HDFC Bank",
    "ICICI Bank",
    "Axis Bank",
    "State Bank of India",
    "Kotak Mahindra Bank",
    "IndusInd Bank",
    "Bank of Baroda",
    "Punjab National Bank",
    "Yes Bank",
]

PAYMENT_MODES = [
    "UPI",
    "NEFT",
    "RTGS",
    "IMPS",
    "NACH",
    "CHEQUE",
    "CASH",
    "AUTO_DEBIT",
]

COLLATERAL_TYPES = [
    "PROPERTY",
    "VEHICLE",
    "GOLD",
    "EQUIPMENT",
]


# ============================================================
# IDENTIFIER GENERATORS
# ============================================================

def generate_pan():
    """
    PAN format:
    ABCDE1234F
    """

    letters = ''.join(
        random.choices(string.ascii_uppercase, k=3)
    )

    entity = random.choice([
        "P", "C", "H", "F", "A",
        "T", "B", "L", "J", "G"
    ])

    last_name_initial = random.choice(
        string.ascii_uppercase
    )

    digits = ''.join(
        random.choices(string.digits, k=4)
    )

    check = random.choice(
        string.ascii_uppercase
    )

    return (
        f"{letters}"
        f"{entity}"
        f"{last_name_initial}"
        f"{digits}"
        f"{check}"
    )


def generate_aadhaar():
    """
    12 digit Aadhaar-like test number.
    """

    first = str(random.randint(2, 9))

    rest = ''.join(
        random.choices(string.digits, k=11)
    )

    return first + rest


def generate_mobile():
    return (
        "+91"
        + str(random.randint(6000000000, 9999999999))
    )


def generate_ifsc():
    bank_code = ''.join(
        random.choices(string.ascii_uppercase, k=4)
    )

    branch_code = ''.join(
        random.choices(string.digits, k=6)
    )

    return bank_code + "0" + branch_code


def generate_account_number():
    return ''.join(
        random.choices(string.digits, k=12)
    )


def generate_cif():
    return "CIF" + ''.join(
        random.choices(string.digits, k=10)
    )


def generate_ckyc():
    return ''.join(
        random.choices(string.digits, k=14)
    )


def generate_loan_number():
    return (
        "LN"
        + str(random.randint(10000000, 99999999))
    )


def generate_application_number():
    return (
        "APP"
        + str(random.randint(10000000, 99999999))
    )


def generate_upi(name):
    handle = (
        name.lower()
        .replace(" ", "")
        .replace(".", "")
        .replace("'", "")
    )[:10]

    provider = random.choice([
        "okaxis",
        "okhdfcbank",
        "ybl",
        "paytm",
        "icici",
        "oksbi"
    ])

    return (
        f"{handle}"
        f"{random.randint(10, 99)}"
        f"@{provider}"
    )


def generate_card_number():
    return ''.join(
        random.choices(string.digits, k=16)
    )


def generate_credit_score():
    return random.randint(300, 850)


def generate_gst():
    return (
        ''.join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=15
            )
        )
    )


def generate_vehicle_number():
    state = random.choice([
        "MH", "KA", "DL",
        "TN", "GJ", "RJ"
    ])

    district = str(
        random.randint(1, 99)
    ).zfill(2)

    letters = ''.join(
        random.choices(string.ascii_uppercase, k=2)
    )

    number = str(
        random.randint(1, 9999)
    ).zfill(4)

    return f"{state}{district}{letters}{number}"


# ============================================================
# RANDOM HELPERS
# ============================================================

def random_date(start_year=2010, end_year=2026):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)

    return fake.date_between(
        start_date=start,
        end_date=end
    )


def random_bool():
    return random.choice([0, 1])


def generate_interaction_note(name):
    """
    Deliberately introduces PII into unstructured text.
    Useful for testing your LLM/NLP fallback engine.
    """

    if random.random() < 0.25:

        leak_type = random.choice([
            "PAN",
            "AADHAAR",
            "PHONE",
            "BANK",
            "CARD",
            "EMAIL"
        ])

        if leak_type == "PAN":

            return (
                f"Customer {name} confirmed PAN "
                f"{generate_pan()} during verification."
            )

        elif leak_type == "AADHAAR":

            return (
                f"KYC verification completed. "
                f"Aadhaar number provided was "
                f"{generate_aadhaar()}."
            )

        elif leak_type == "PHONE":

            return (
                f"Customer requested callback on "
                f"{generate_mobile()}."
            )

        elif leak_type == "BANK":

            return (
                f"Customer provided bank account "
                f"{generate_account_number()} "
                f"for loan disbursement."
            )

        elif leak_type == "CARD":

            return (
                f"Customer disputed transaction "
                f"on card ending "
                f"{random.randint(1000, 9999)}."
            )

        else:

            return (
                f"Email confirmation sent to "
                f"{fake.email()}."
            )

    return random.choice([
        "Customer requested loan statement.",
        "Customer asked about EMI due date.",
        "Loan foreclosure procedure explained.",
        "Customer requested address update.",
        "KYC documents are under review.",
        "Customer requested repayment schedule.",
        "Payment failure issue resolved.",
        "Customer contacted support regarding interest rate.",
        "Routine customer verification completed.",
        "Loan account statement dispatched."
    ])


# ============================================================
# DATABASE CREATION
# ============================================================

def create_database():

    server_engine = create_engine(
        f"mysql+mysqlconnector://"
        f"{DB_USER}:{DB_PASS}@"
        f"{DB_HOST}:{DB_PORT}"
    )

    with server_engine.connect() as conn:

        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS "
                f"{DB_NAME}"
            )
        )

        conn.commit()

    server_engine.dispose()


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables(engine):

    with engine.connect() as conn:

        print("Dropping existing tables...")

        tables = [
            "customer_interactions",
            "collateral_assets",
            "credit_bureau_profiles",
            "loan_repayments",
            "loans",
            "loan_applications",
            "bank_accounts",
            "employment_profiles",
            "customer_addresses",
            "customers",
        ]

        for table in tables:

            conn.execute(
                text(
                    f"DROP TABLE IF EXISTS {table}"
                )
            )

        conn.commit()

        print("Creating tables...")


        # ====================================================
        # 1. CUSTOMERS
        # ====================================================

        conn.execute(text("""
            CREATE TABLE customers (

                customer_id INT PRIMARY KEY AUTO_INCREMENT,

                cif_number VARCHAR(20),

                full_name VARCHAR(150),

                first_name VARCHAR(75),

                middle_name VARCHAR(75),

                last_name VARCHAR(75),

                gender VARCHAR(20),

                date_of_birth DATE,

                age INT,

                email VARCHAR(150),

                alternate_email VARCHAR(150),

                phone_number VARCHAR(20),

                alternate_phone VARCHAR(20),

                aadhaar_number VARCHAR(12),

                pan_number VARCHAR(10),

                ckyc_number VARCHAR(14),

                nationality VARCHAR(50),

                marital_status VARCHAR(30),

                residential_city VARCHAR(100),

                residential_state VARCHAR(100),

                pincode VARCHAR(10),

                customer_type VARCHAR(50),

                customer_status VARCHAR(30),

                risk_category VARCHAR(30),

                kyc_status VARCHAR(30),

                kyc_last_verified DATE,

                preferred_language VARCHAR(50),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )
        """))


        # ====================================================
        # 2. CUSTOMER ADDRESSES
        # ====================================================

        conn.execute(text("""
            CREATE TABLE customer_addresses (

                address_id INT PRIMARY KEY AUTO_INCREMENT,

                customer_id INT,

                address_type VARCHAR(30),

                address_line_1 VARCHAR(200),

                address_line_2 VARCHAR(200),

                landmark VARCHAR(150),

                city VARCHAR(100),

                district VARCHAR(100),

                state VARCHAR(100),

                pincode VARCHAR(10),

                country VARCHAR(50),

                latitude DECIMAL(10,7),

                longitude DECIMAL(10,7),

                residence_type VARCHAR(50),

                years_at_address DECIMAL(5,2),

                address_proof_type VARCHAR(50),

                address_proof_number VARCHAR(100),

                verified_flag BOOLEAN,

                verification_date DATE,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))


        # ====================================================
        # 3. EMPLOYMENT PROFILES
        # ====================================================

        conn.execute(text("""
            CREATE TABLE employment_profiles (

                employment_id INT PRIMARY KEY AUTO_INCREMENT,

                customer_id INT,

                employment_type VARCHAR(50),

                employer_name VARCHAR(200),

                employer_address VARCHAR(300),

                designation VARCHAR(100),

                department VARCHAR(100),

                employee_id VARCHAR(100),

                work_email VARCHAR(150),

                work_phone VARCHAR(20),

                joining_date DATE,

                years_of_experience DECIMAL(5,2),

                monthly_income DECIMAL(14,2),

                annual_income DECIMAL(16,2),

                other_income DECIMAL(14,2),

                total_monthly_obligation DECIMAL(14,2),

                income_source VARCHAR(100),

                income_verification_method VARCHAR(100),

                itr_number VARCHAR(100),

                gst_number VARCHAR(20),

                salary_account_number VARCHAR(30),

                salary_credit_bank VARCHAR(100),

                employment_status VARCHAR(30),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))


        # ====================================================
        # 4. BANK ACCOUNTS
        # ====================================================

        conn.execute(text("""
            CREATE TABLE bank_accounts (

                bank_account_id INT PRIMARY KEY AUTO_INCREMENT,

                customer_id INT,

                bank_name VARCHAR(150),

                branch_name VARCHAR(150),

                account_number VARCHAR(30),

                account_type VARCHAR(30),

                ifsc_code VARCHAR(20),

                micr_code VARCHAR(20),

                upi_identifier VARCHAR(150),

                account_holder_name VARCHAR(150),

                account_status VARCHAR(30),

                account_opening_date DATE,

                last_transaction_date DATE,

                average_monthly_balance DECIMAL(16,2),

                monthly_credit DECIMAL(16,2),

                monthly_debit DECIMAL(16,2),

                penny_drop_status VARCHAR(30),

                bank_statement_file VARCHAR(300),

                verification_status VARCHAR(30),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))


        # ====================================================
        # 5. LOAN APPLICATIONS
        # ====================================================

        conn.execute(text("""
            CREATE TABLE loan_applications (

                application_id INT PRIMARY KEY AUTO_INCREMENT,

                application_number VARCHAR(30),

                customer_id INT,

                loan_type VARCHAR(50),

                requested_amount DECIMAL(16,2),

                approved_amount DECIMAL(16,2),

                tenure_months INT,

                interest_rate DECIMAL(6,3),

                application_date DATE,

                approval_date DATE,

                rejection_date DATE,

                application_status VARCHAR(30),

                sourcing_channel VARCHAR(50),

                branch_code VARCHAR(30),

                relationship_manager VARCHAR(100),

                sales_agent_id VARCHAR(30),

                pan_number VARCHAR(10),

                aadhaar_number VARCHAR(12),

                employment_type VARCHAR(50),

                declared_monthly_income DECIMAL(14,2),

                requested_purpose VARCHAR(200),

                bureau_score INT,

                fraud_check_status VARCHAR(30),

                kyc_check_status VARCHAR(30),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))


        # ====================================================
        # 6. LOANS
        # ====================================================

        conn.execute(text("""
            CREATE TABLE loans (

                loan_id INT PRIMARY KEY AUTO_INCREMENT,

                loan_number VARCHAR(30),

                customer_id INT,

                application_id INT,

                loan_type VARCHAR(50),

                sanctioned_amount DECIMAL(16,2),

                disbursed_amount DECIMAL(16,2),

                outstanding_principal DECIMAL(16,2),

                outstanding_interest DECIMAL(16,2),

                interest_rate DECIMAL(6,3),

                tenure_months INT,

                emi_amount DECIMAL(14,2),

                emi_frequency VARCHAR(30),

                disbursement_date DATE,

                first_emi_date DATE,

                maturity_date DATE,

                next_due_date DATE,

                loan_status VARCHAR(30),

                dpd_days INT,

                overdue_amount DECIMAL(14,2),

                principal_overdue DECIMAL(14,2),

                interest_overdue DECIMAL(14,2),

                penalty_amount DECIMAL(14,2),

                risk_grade VARCHAR(20),

                npa_flag BOOLEAN,

                foreclosure_flag BOOLEAN,

                branch_code VARCHAR(30),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))


        # ====================================================
        # 7. LOAN REPAYMENTS
        # ====================================================

        conn.execute(text("""
            CREATE TABLE loan_repayments (

                repayment_id INT PRIMARY KEY AUTO_INCREMENT,

                loan_id INT,

                customer_id INT,

                transaction_reference VARCHAR(50),

                payment_date DATE,

                value_date DATE,

                due_date DATE,

                emi_number INT,

                payment_amount DECIMAL(14,2),

                principal_component DECIMAL(14,2),

                interest_component DECIMAL(14,2),

                penalty_component DECIMAL(14,2),

                payment_mode VARCHAR(50),

                bank_account_number VARCHAR(30),

                upi_identifier VARCHAR(150),

                cheque_number VARCHAR(30),

                transaction_status VARCHAR(30),

                settlement_status VARCHAR(30),

                reversal_flag BOOLEAN,

                narration VARCHAR(300),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(loan_id)

                REFERENCES loans(loan_id)

                ON DELETE CASCADE,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))


        # ====================================================
        # 8. CREDIT BUREAU
        # ====================================================

        conn.execute(text("""
            CREATE TABLE credit_bureau_profiles (

                bureau_id INT PRIMARY KEY AUTO_INCREMENT,

                customer_id INT,

                bureau_name VARCHAR(50),

                bureau_reference_number VARCHAR(100),

                pan_number VARCHAR(10),

                full_name VARCHAR(150),

                date_of_birth DATE,

                mobile_number VARCHAR(20),

                credit_score INT,

                score_date DATE,

                total_accounts INT,

                active_accounts INT,

                closed_accounts INT,

                total_credit_limit DECIMAL(16,2),

                total_outstanding DECIMAL(16,2),

                total_overdue DECIMAL(16,2),

                secured_loans INT,

                unsecured_loans INT,

                credit_card_accounts INT,

                days_past_due INT,

                write_off_amount DECIMAL(16,2),

                settlement_amount DECIMAL(16,2),

                enquiry_count INT,

                last_enquiry_date DATE,

                report_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))


        # ====================================================
        # 9. COLLATERAL
        # ====================================================

        conn.execute(text("""
            CREATE TABLE collateral_assets (

                collateral_id INT PRIMARY KEY AUTO_INCREMENT,

                loan_id INT,

                customer_id INT,

                collateral_type VARCHAR(50),

                asset_description VARCHAR(300),

                owner_name VARCHAR(150),

                registration_number VARCHAR(100),

                property_address VARCHAR(300),

                vehicle_registration_number VARCHAR(30),

                valuation_amount DECIMAL(16,2),

                forced_sale_value DECIMAL(16,2),

                market_value DECIMAL(16,2),

                valuation_date DATE,

                valuer_name VARCHAR(150),

                valuer_registration_number VARCHAR(100),

                insurance_policy_number VARCHAR(100),

                insurance_expiry_date DATE,

                lien_marked BOOLEAN,

                hypothecation_number VARCHAR(100),

                document_number VARCHAR(100),

                document_type VARCHAR(100),

                collateral_status VARCHAR(30),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(loan_id)

                REFERENCES loans(loan_id)

                ON DELETE CASCADE,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))


        # ====================================================
        # 10. CUSTOMER INTERACTIONS
        # ====================================================

        conn.execute(text("""
            CREATE TABLE customer_interactions (

                interaction_id INT PRIMARY KEY AUTO_INCREMENT,

                customer_id INT,

                loan_id INT,

                interaction_type VARCHAR(50),

                channel VARCHAR(50),

                agent_id VARCHAR(30),

                agent_name VARCHAR(150),

                customer_name VARCHAR(150),

                customer_phone VARCHAR(20),

                customer_email VARCHAR(150),

                interaction_subject VARCHAR(300),

                interaction_notes TEXT,

                call_duration_seconds INT,

                sentiment VARCHAR(30),

                resolution_status VARCHAR(50),

                complaint_category VARCHAR(100),

                complaint_reference_number VARCHAR(100),

                recording_reference VARCHAR(300),

                ip_address VARCHAR(50),

                device_id VARCHAR(150),

                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(customer_id)

                REFERENCES customers(customer_id)

                ON DELETE CASCADE

            )
        """))

        conn.commit()

    print("All 10 tables created successfully.")


# ============================================================
# SEED CUSTOMERS
# ============================================================

def seed_customers(engine):

    print("\nSeeding customers...")

    sql = text("""
        INSERT INTO customers (

            cif_number,
            full_name,
            first_name,
            middle_name,
            last_name,
            gender,
            date_of_birth,
            age,
            email,
            alternate_email,
            phone_number,
            alternate_phone,
            aadhaar_number,
            pan_number,
            ckyc_number,
            nationality,
            marital_status,
            residential_city,
            residential_state,
            pincode,
            customer_type,
            customer_status,
            risk_category,
            kyc_status,
            kyc_last_verified,
            preferred_language

        )

        VALUES (

            :cif_number,
            :full_name,
            :first_name,
            :middle_name,
            :last_name,
            :gender,
            :date_of_birth,
            :age,
            :email,
            :alternate_email,
            :phone_number,
            :alternate_phone,
            :aadhaar_number,
            :pan_number,
            :ckyc_number,
            :nationality,
            :marital_status,
            :residential_city,
            :residential_state,
            :pincode,
            :customer_type,
            :customer_status,
            :risk_category,
            :kyc_status,
            :kyc_last_verified,
            :preferred_language

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for _ in range(start, end):

                name = fake.name()

                parts = name.split()

                first_name = parts[0]

                last_name = (
                    parts[-1]
                    if len(parts) > 1
                    else ""
                )

                middle_name = (
                    " ".join(parts[1:-1])
                    if len(parts) > 2
                    else ""
                )

                dob = fake.date_of_birth(
                    minimum_age=18,
                    maximum_age=75
                )

                today = date.today()

                age = (
                    today.year
                    - dob.year
                    - (
                        (today.month, today.day)
                        <
                        (dob.month, dob.day)
                    )
                )

                batch.append({

                    "cif_number":
                        generate_cif(),

                    "full_name":
                        name,

                    "first_name":
                        first_name,

                    "middle_name":
                        middle_name,

                    "last_name":
                        last_name,

                    "gender":
                        random.choice([
                            "MALE",
                            "FEMALE",
                            "OTHER"
                        ]),

                    "date_of_birth":
                        dob,

                    "age":
                        age,

                    "email":
                        fake.email(),

                    "alternate_email":
                        fake.email(),

                    "phone_number":
                        generate_mobile(),

                    "alternate_phone":
                        generate_mobile(),

                    "aadhaar_number":
                        generate_aadhaar(),

                    "pan_number":
                        generate_pan(),

                    "ckyc_number":
                        generate_ckyc(),

                    "nationality":
                        "Indian",

                    "marital_status":
                        random.choice([
                            "SINGLE",
                            "MARRIED",
                            "DIVORCED",
                            "WIDOWED"
                        ]),

                    "residential_city":
                        random.choice(CITIES),

                    "residential_state":
                        random.choice(INDIAN_STATES),

                    "pincode":
                        str(
                            random.randint(
                                110001,
                                799999
                            )
                        ),

                    "customer_type":
                        random.choice([
                            "INDIVIDUAL",
                            "SOLE_PROPRIETOR",
                            "MSME"
                        ]),

                    "customer_status":
                        random.choice([
                            "ACTIVE",
                            "ACTIVE",
                            "ACTIVE",
                            "INACTIVE"
                        ]),

                    "risk_category":
                        random.choice([
                            "LOW",
                            "MEDIUM",
                            "HIGH"
                        ]),

                    "kyc_status":
                        random.choice([
                            "VERIFIED",
                            "VERIFIED",
                            "PENDING"
                        ]),

                    "kyc_last_verified":
                        random_date(
                            2023,
                            2026
                        ),

                    "preferred_language":
                        random.choice([
                            "English",
                            "Hindi",
                            "Marathi",
                            "Kannada",
                            "Tamil",
                            "Telugu",
                            "Gujarati"
                        ])
                })

            conn.execute(sql, batch)

            print(
                f"  Customers: {end - 1:,}"
            )


# ============================================================
# GENERIC CUSTOMER-BASED TABLE SEEDER
# ============================================================

def seed_customer_addresses(engine):

    print("\nSeeding customer_addresses...")

    sql = text("""
        INSERT INTO customer_addresses (

            customer_id,
            address_type,
            address_line_1,
            address_line_2,
            landmark,
            city,
            district,
            state,
            pincode,
            country,
            latitude,
            longitude,
            residence_type,
            years_at_address,
            address_proof_type,
            address_proof_number,
            verified_flag,
            verification_date

        )

        VALUES (

            :customer_id,
            :address_type,
            :address_line_1,
            :address_line_2,
            :landmark,
            :city,
            :district,
            :state,
            :pincode,
            :country,
            :latitude,
            :longitude,
            :residence_type,
            :years_at_address,
            :address_proof_type,
            :address_proof_number,
            :verified_flag,
            :verification_date

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for cid in range(start, end):

                batch.append({

                    "customer_id": cid,

                    "address_type":
                        random.choice([
                            "RESIDENTIAL",
                            "PERMANENT",
                            "OFFICE"
                        ]),

                    "address_line_1":
                        fake.street_address(),

                    "address_line_2":
                        f"Flat {random.randint(1, 999)}, "
                        f"{fake.street_name()}",

                    "landmark":
                        random.choice([
                            "Near Bus Stand",
                            "Near Railway Station",
                            "Opposite Mall",
                            "Near Main Road",
                            "Near Hospital"
                        ]),

                    "city":
                        random.choice(CITIES),

                    "district":
                        random.choice(CITIES),

                    "state":
                        random.choice(INDIAN_STATES),

                    "pincode":
                        str(
                            random.randint(
                                110001,
                                799999
                            )
                        ),

                    "country":
                        "India",

                    "latitude":
                        round(
                            random.uniform(
                                8.0,
                                28.0
                            ),
                            7
                        ),

                    "longitude":
                        round(
                            random.uniform(
                                72.0,
                                88.0
                            ),
                            7
                        ),

                    "residence_type":
                        random.choice([
                            "OWNED",
                            "RENTED",
                            "FAMILY"
                        ]),

                    "years_at_address":
                        round(
                            random.uniform(
                                0.5,
                                25
                            ),
                            2
                        ),

                    "address_proof_type":
                        random.choice([
                            "AADHAAR",
                            "PASSPORT",
                            "VOTER_ID",
                            "UTILITY_BILL",
                            "DRIVING_LICENSE"
                        ]),

                    "address_proof_number":
                        ''.join(
                            random.choices(
                                string.ascii_uppercase
                                + string.digits,
                                k=12
                            )
                        ),

                    "verified_flag":
                        random_bool(),

                    "verification_date":
                        random_date(2023, 2026)
                })

            conn.execute(sql, batch)

            print(
                f"  Addresses: {end - 1:,}"
            )


# ============================================================
# EMPLOYMENT
# ============================================================

def seed_employment(engine):

    print("\nSeeding employment_profiles...")

    sql = text("""
        INSERT INTO employment_profiles (

            customer_id,
            employment_type,
            employer_name,
            employer_address,
            designation,
            department,
            employee_id,
            work_email,
            work_phone,
            joining_date,
            years_of_experience,
            monthly_income,
            annual_income,
            other_income,
            total_monthly_obligation,
            income_source,
            income_verification_method,
            itr_number,
            gst_number,
            salary_account_number,
            salary_credit_bank,
            employment_status

        )

        VALUES (

            :customer_id,
            :employment_type,
            :employer_name,
            :employer_address,
            :designation,
            :department,
            :employee_id,
            :work_email,
            :work_phone,
            :joining_date,
            :years_of_experience,
            :monthly_income,
            :annual_income,
            :other_income,
            :total_monthly_obligation,
            :income_source,
            :income_verification_method,
            :itr_number,
            :gst_number,
            :salary_account_number,
            :salary_credit_bank,
            :employment_status

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for cid in range(start, end):

                monthly_income = round(
                    random.uniform(
                        18000,
                        500000
                    ),
                    2
                )

                batch.append({

                    "customer_id":
                        cid,

                    "employment_type":
                        random.choice(
                            EMPLOYMENT_TYPES
                        ),

                    "employer_name":
                        fake.company(),

                    "employer_address":
                        fake.address(),

                    "designation":
                        random.choice([
                            "Manager",
                            "Senior Manager",
                            "Executive",
                            "Engineer",
                            "Analyst",
                            "Director",
                            "Consultant"
                        ]),

                    "department":
                        random.choice([
                            "Finance",
                            "Technology",
                            "Operations",
                            "Sales",
                            "HR",
                            "Marketing"
                        ]),

                    "employee_id":
                        "EMP-" + str(
                            random.randint(
                                100000,
                                999999
                            )
                        ),

                    "work_email":
                        fake.company_email(),

                    "work_phone":
                        generate_mobile(),

                    "joining_date":
                        random_date(
                            2010,
                            2025
                        ),

                    "years_of_experience":
                        round(
                            random.uniform(
                                1,
                                30
                            ),
                            2
                        ),

                    "monthly_income":
                        monthly_income,

                    "annual_income":
                        monthly_income * 12,

                    "other_income":
                        round(
                            random.uniform(
                                0,
                                100000
                            ),
                            2
                        ),

                    "total_monthly_obligation":
                        round(
                            random.uniform(
                                0,
                                monthly_income * 0.7
                            ),
                            2
                        ),

                    "income_source":
                        random.choice([
                            "SALARY",
                            "BUSINESS",
                            "RENTAL",
                            "INVESTMENTS"
                        ]),

                    "income_verification_method":
                        random.choice([
                            "BANK_STATEMENT",
                            "SALARY_SLIP",
                            "ITR",
                            "GST_RETURN"
                        ]),

                    "itr_number":
                        "ITR"
                        + ''.join(
                            random.choices(
                                string.digits,
                                k=10
                            )
                        ),

                    "gst_number":
                        generate_gst(),

                    "salary_account_number":
                        generate_account_number(),

                    "salary_credit_bank":
                        random.choice(BANKS),

                    "employment_status":
                        random.choice([
                            "ACTIVE",
                            "ACTIVE",
                            "NOTICE_PERIOD",
                            "LEFT"
                        ])
                })

            conn.execute(sql, batch)

            print(
                f"  Employment: {end - 1:,}"
            )


# ============================================================
# BANK ACCOUNTS
# ============================================================

def seed_bank_accounts(engine):

    print("\nSeeding bank_accounts...")

    sql = text("""
        INSERT INTO bank_accounts (

            customer_id,
            bank_name,
            branch_name,
            account_number,
            account_type,
            ifsc_code,
            micr_code,
            upi_identifier,
            account_holder_name,
            account_status,
            account_opening_date,
            last_transaction_date,
            average_monthly_balance,
            monthly_credit,
            monthly_debit,
            penny_drop_status,
            bank_statement_file,
            verification_status

        )

        VALUES (

            :customer_id,
            :bank_name,
            :branch_name,
            :account_number,
            :account_type,
            :ifsc_code,
            :micr_code,
            :upi_identifier,
            :account_holder_name,
            :account_status,
            :account_opening_date,
            :last_transaction_date,
            :average_monthly_balance,
            :monthly_credit,
            :monthly_debit,
            :penny_drop_status,
            :bank_statement_file,
            :verification_status

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for cid in range(start, end):

                name = fake.name()

                batch.append({

                    "customer_id":
                        cid,

                    "bank_name":
                        random.choice(BANKS),

                    "branch_name":
                        fake.city() + " Branch",

                    "account_number":
                        generate_account_number(),

                    "account_type":
                        random.choice(
                            ACCOUNT_TYPES
                        ),

                    "ifsc_code":
                        generate_ifsc(),

                    "micr_code":
                        ''.join(
                            random.choices(
                                string.digits,
                                k=9
                            )
                        ),

                    "upi_identifier":
                        generate_upi(name),

                    "account_holder_name":
                        name,

                    "account_status":
                        "ACTIVE",

                    "account_opening_date":
                        random_date(
                            2010,
                            2025
                        ),

                    "last_transaction_date":
                        random_date(
                            2025,
                            2026
                        ),

                    "average_monthly_balance":
                        round(
                            random.uniform(
                                5000,
                                500000
                            ),
                            2
                        ),

                    "monthly_credit":
                        round(
                            random.uniform(
                                20000,
                                500000
                            ),
                            2
                        ),

                    "monthly_debit":
                        round(
                            random.uniform(
                                10000,
                                400000
                            ),
                            2
                        ),

                    "penny_drop_status":
                        random.choice([
                            "SUCCESS",
                            "SUCCESS",
                            "FAILED"
                        ]),

                    "bank_statement_file":
                        f"/statements/"
                        f"{cid}/statement.pdf",

                    "verification_status":
                        random.choice([
                            "VERIFIED",
                            "VERIFIED",
                            "PENDING"
                        ])
                })

            conn.execute(sql, batch)

            print(
                f"  Bank accounts: {end - 1:,}"
            )


# ============================================================
# LOAN APPLICATIONS
# ============================================================

def seed_loan_applications(engine):

    print("\nSeeding loan_applications...")

    sql = text("""
        INSERT INTO loan_applications (

            application_number,
            customer_id,
            loan_type,
            requested_amount,
            approved_amount,
            tenure_months,
            interest_rate,
            application_date,
            approval_date,
            rejection_date,
            application_status,
            sourcing_channel,
            branch_code,
            relationship_manager,
            sales_agent_id,
            pan_number,
            aadhaar_number,
            employment_type,
            declared_monthly_income,
            requested_purpose,
            bureau_score,
            fraud_check_status,
            kyc_check_status

        )

        VALUES (

            :application_number,
            :customer_id,
            :loan_type,
            :requested_amount,
            :approved_amount,
            :tenure_months,
            :interest_rate,
            :application_date,
            :approval_date,
            :rejection_date,
            :application_status,
            :sourcing_channel,
            :branch_code,
            :relationship_manager,
            :sales_agent_id,
            :pan_number,
            :aadhaar_number,
            :employment_type,
            :declared_monthly_income,
            :requested_purpose,
            :bureau_score,
            :fraud_check_status,
            :kyc_check_status

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for cid in range(start, end):

                requested = round(
                    random.uniform(
                        50000,
                        5000000
                    ),
                    2
                )

                approved = round(
                    requested
                    * random.uniform(
                        0.7,
                        1.0
                    ),
                    2
                )

                batch.append({

                    "application_number":
                        generate_application_number(),

                    "customer_id":
                        cid,

                    "loan_type":
                        random.choice(
                            LOAN_TYPES
                        ),

                    "requested_amount":
                        requested,

                    "approved_amount":
                        approved,

                    "tenure_months":
                        random.choice([
                            12, 24, 36,
                            48, 60, 84
                        ]),

                    "interest_rate":
                        round(
                            random.uniform(
                                8,
                                24
                            ),
                            3
                        ),

                    "application_date":
                        random_date(
                            2023,
                            2026
                        ),

                    "approval_date":
                        random_date(
                            2023,
                            2026
                        ),

                    "rejection_date":
                        None,

                    "application_status":
                        random.choice([
                            "APPROVED",
                            "APPROVED",
                            "REJECTED",
                            "UNDER_REVIEW"
                        ]),

                    "sourcing_channel":
                        random.choice([
                            "BRANCH",
                            "WEBSITE",
                            "MOBILE_APP",
                            "DSA",
                            "PARTNER"
                        ]),

                    "branch_code":
                        "BR"
                        + str(
                            random.randint(
                                100,
                                999
                            )
                        ),

                    "relationship_manager":
                        fake.name(),

                    "sales_agent_id":
                        "AGT-"
                        + str(
                            random.randint(
                                1000,
                                9999
                            )
                        ),

                    "pan_number":
                        generate_pan(),

                    "aadhaar_number":
                        generate_aadhaar(),

                    "employment_type":
                        random.choice(
                            EMPLOYMENT_TYPES
                        ),

                    "declared_monthly_income":
                        round(
                            random.uniform(
                                20000,
                                400000
                            ),
                            2
                        ),

                    "requested_purpose":
                        random.choice([
                            "Medical expenses",
                            "Education",
                            "Home renovation",
                            "Vehicle purchase",
                            "Business expansion",
                            "Debt consolidation",
                            "Personal expenses"
                        ]),

                    "bureau_score":
                        generate_credit_score(),

                    "fraud_check_status":
                        random.choice([
                            "PASSED",
                            "PASSED",
                            "REVIEW"
                        ]),

                    "kyc_check_status":
                        random.choice([
                            "VERIFIED",
                            "VERIFIED",
                            "PENDING"
                        ])
                })

            conn.execute(sql, batch)

            print(
                f"  Applications: {end - 1:,}"
            )


# ============================================================
# LOANS
# ============================================================

def seed_loans(engine):

    print("\nSeeding loans...")

    sql = text("""
        INSERT INTO loans (

            loan_number,
            customer_id,
            application_id,
            loan_type,
            sanctioned_amount,
            disbursed_amount,
            outstanding_principal,
            outstanding_interest,
            interest_rate,
            tenure_months,
            emi_amount,
            emi_frequency,
            disbursement_date,
            first_emi_date,
            maturity_date,
            next_due_date,
            loan_status,
            dpd_days,
            overdue_amount,
            principal_overdue,
            interest_overdue,
            penalty_amount,
            risk_grade,
            npa_flag,
            foreclosure_flag,
            branch_code

        )

        VALUES (

            :loan_number,
            :customer_id,
            :application_id,
            :loan_type,
            :sanctioned_amount,
            :disbursed_amount,
            :outstanding_principal,
            :outstanding_interest,
            :interest_rate,
            :tenure_months,
            :emi_amount,
            :emi_frequency,
            :disbursement_date,
            :first_emi_date,
            :maturity_date,
            :next_due_date,
            :loan_status,
            :dpd_days,
            :overdue_amount,
            :principal_overdue,
            :interest_overdue,
            :penalty_amount,
            :risk_grade,
            :npa_flag,
            :foreclosure_flag,
            :branch_code

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for cid in range(start, end):

                sanctioned = round(
                    random.uniform(
                        100000,
                        5000000
                    ),
                    2
                )

                disbursed = sanctioned

                outstanding = round(
                    disbursed
                    * random.uniform(
                        0.1,
                        0.95
                    ),
                    2
                )

                tenure = random.choice([
                    12, 24, 36,
                    48, 60, 84
                ])

                interest_rate = round(
                    random.uniform(
                        8,
                        24
                    ),
                    3
                )

                emi = round(
                    (
                        sanctioned
                        * (
                            1
                            + interest_rate / 100
                        )
                    )
                    / tenure,
                    2
                )

                dpd = random.choice([
                    0, 0, 0,
                    5, 10, 30,
                    60, 90
                ])

                batch.append({

                    "loan_number":
                        generate_loan_number(),

                    "customer_id":
                        cid,

                    "application_id":
                        cid,

                    "loan_type":
                        random.choice(
                            LOAN_TYPES
                        ),

                    "sanctioned_amount":
                        sanctioned,

                    "disbursed_amount":
                        disbursed,

                    "outstanding_principal":
                        outstanding,

                    "outstanding_interest":
                        round(
                            random.uniform(
                                1000,
                                50000
                            ),
                            2
                        ),

                    "interest_rate":
                        interest_rate,

                    "tenure_months":
                        tenure,

                    "emi_amount":
                        emi,

                    "emi_frequency":
                        "MONTHLY",

                    "disbursement_date":
                        random_date(
                            2022,
                            2026
                        ),

                    "first_emi_date":
                        random_date(
                            2022,
                            2026
                        ),

                    "maturity_date":
                        random_date(
                            2026,
                            2032
                        ),

                    "next_due_date":
                        random_date(
                            2026,
                            2026
                        ),

                    "loan_status":
                        random.choice([
                            "ACTIVE",
                            "ACTIVE",
                            "CLOSED",
                            "OVERDUE"
                        ]),

                    "dpd_days":
                        dpd,

                    "overdue_amount":
                        round(
                            random.uniform(
                                0,
                                100000
                            ),
                            2
                        ),

                    "principal_overdue":
                        round(
                            random.uniform(
                                0,
                                70000
                            ),
                            2
                        ),

                    "interest_overdue":
                        round(
                            random.uniform(
                                0,
                                30000
                            ),
                            2
                        ),

                    "penalty_amount":
                        round(
                            random.uniform(
                                0,
                                10000
                            ),
                            2
                        ),

                    "risk_grade":
                        random.choice([
                            "A",
                            "B",
                            "C",
                            "D"
                        ]),

                    "npa_flag":
                        dpd >= 90,

                    "foreclosure_flag":
                        random_bool(),

                    "branch_code":
                        "BR"
                        + str(
                            random.randint(
                                100,
                                999
                            )
                        )
                })

            conn.execute(sql, batch)

            print(
                f"  Loans: {end - 1:,}"
            )


# ============================================================
# LOAN REPAYMENTS
# ============================================================

def seed_repayments(engine):

    print("\nSeeding loan_repayments...")

    sql = text("""
        INSERT INTO loan_repayments (

            loan_id,
            customer_id,
            transaction_reference,
            payment_date,
            value_date,
            due_date,
            emi_number,
            payment_amount,
            principal_component,
            interest_component,
            penalty_component,
            payment_mode,
            bank_account_number,
            upi_identifier,
            cheque_number,
            transaction_status,
            settlement_status,
            reversal_flag,
            narration

        )

        VALUES (

            :loan_id,
            :customer_id,
            :transaction_reference,
            :payment_date,
            :value_date,
            :due_date,
            :emi_number,
            :payment_amount,
            :principal_component,
            :interest_component,
            :penalty_component,
            :payment_mode,
            :bank_account_number,
            :upi_identifier,
            :cheque_number,
            :transaction_status,
            :settlement_status,
            :reversal_flag,
            :narration

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for loan_id in range(start, end):

                payment = round(
                    random.uniform(
                        5000,
                        100000
                    ),
                    2
                )

                interest = round(
                    payment
                    * random.uniform(
                        0.05,
                        0.25
                    ),
                    2
                )

                principal = (
                    payment - interest
                )

                batch.append({

                    "loan_id":
                        loan_id,

                    "customer_id":
                        loan_id,

                    "transaction_reference":
                        "TXN-"
                        + ''.join(
                            random.choices(
                                string.ascii_uppercase
                                + string.digits,
                                k=12
                            )
                        ),

                    "payment_date":
                        random_date(
                            2025,
                            2026
                        ),

                    "value_date":
                        random_date(
                            2025,
                            2026
                        ),

                    "due_date":
                        random_date(
                            2025,
                            2026
                        ),

                    "emi_number":
                        random.randint(
                            1,
                            60
                        ),

                    "payment_amount":
                        payment,

                    "principal_component":
                        principal,

                    "interest_component":
                        interest,

                    "penalty_component":
                        round(
                            random.uniform(
                                0,
                                5000
                            ),
                            2
                        ),

                    "payment_mode":
                        random.choice(
                            PAYMENT_MODES
                        ),

                    "bank_account_number":
                        generate_account_number(),

                    "upi_identifier":
                        generate_upi(
                            fake.name()
                        ),

                    "cheque_number":
                        ''.join(
                            random.choices(
                                string.digits,
                                k=6
                            )
                        ),

                    "transaction_status":
                        random.choice([
                            "SUCCESS",
                            "SUCCESS",
                            "FAILED"
                        ]),

                    "settlement_status":
                        random.choice([
                            "SETTLED",
                            "SETTLED",
                            "PENDING"
                        ]),

                    "reversal_flag":
                        random.choice([
                            False,
                            False,
                            False,
                            True
                        ]),

                    "narration":
                        "Loan EMI repayment"
                })

            conn.execute(sql, batch)

            print(
                f"  Repayments: {end - 1:,}"
            )


# ============================================================
# CREDIT BUREAU
# ============================================================

def seed_credit_bureau(engine):

    print("\nSeeding credit_bureau_profiles...")

    sql = text("""
        INSERT INTO credit_bureau_profiles (

            customer_id,
            bureau_name,
            bureau_reference_number,
            pan_number,
            full_name,
            date_of_birth,
            mobile_number,
            credit_score,
            score_date,
            total_accounts,
            active_accounts,
            closed_accounts,
            total_credit_limit,
            total_outstanding,
            total_overdue,
            secured_loans,
            unsecured_loans,
            credit_card_accounts,
            days_past_due,
            write_off_amount,
            settlement_amount,
            enquiry_count,
            last_enquiry_date

        )

        VALUES (

            :customer_id,
            :bureau_name,
            :bureau_reference_number,
            :pan_number,
            :full_name,
            :date_of_birth,
            :mobile_number,
            :credit_score,
            :score_date,
            :total_accounts,
            :active_accounts,
            :closed_accounts,
            :total_credit_limit,
            :total_outstanding,
            :total_overdue,
            :secured_loans,
            :unsecured_loans,
            :credit_card_accounts,
            :days_past_due,
            :write_off_amount,
            :settlement_amount,
            :enquiry_count,
            :last_enquiry_date

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for cid in range(start, end):

                score = generate_credit_score()

                batch.append({

                    "customer_id":
                        cid,

                    "bureau_name":
                        random.choice([
                            "CIBIL",
                            "Experian",
                            "Equifax",
                            "CRIF"
                        ]),

                    "bureau_reference_number":
                        "BUR"
                        + ''.join(
                            random.choices(
                                string.digits,
                                k=12
                            )
                        ),

                    "pan_number":
                        generate_pan(),

                    "full_name":
                        fake.name(),

                    "date_of_birth":
                        fake.date_of_birth(
                            minimum_age=18,
                            maximum_age=75
                        ),

                    "mobile_number":
                        generate_mobile(),

                    "credit_score":
                        score,

                    "score_date":
                        random_date(
                            2025,
                            2026
                        ),

                    "total_accounts":
                        random.randint(
                            1,
                            15
                        ),

                    "active_accounts":
                        random.randint(
                            1,
                            8
                        ),

                    "closed_accounts":
                        random.randint(
                            0,
                            8
                        ),

                    "total_credit_limit":
                        round(
                            random.uniform(
                                100000,
                                10000000
                            ),
                            2
                        ),

                    "total_outstanding":
                        round(
                            random.uniform(
                                0,
                                5000000
                            ),
                            2
                        ),

                    "total_overdue":
                        round(
                            random.uniform(
                                0,
                                500000
                            ),
                            2
                        ),

                    "secured_loans":
                        random.randint(
                            0,
                            5
                        ),

                    "unsecured_loans":
                        random.randint(
                            0,
                            8
                        ),

                    "credit_card_accounts":
                        random.randint(
                            0,
                            5
                        ),

                    "days_past_due":
                        random.choice([
                            0,
                            0,
                            0,
                            30,
                            60,
                            90
                        ]),

                    "write_off_amount":
                        round(
                            random.uniform(
                                0,
                                100000
                            ),
                            2
                        ),

                    "settlement_amount":
                        round(
                            random.uniform(
                                0,
                                100000
                            ),
                            2
                        ),

                    "enquiry_count":
                        random.randint(
                            0,
                            15
                        ),

                    "last_enquiry_date":
                        random_date(
                            2025,
                            2026
                        )
                })

            conn.execute(sql, batch)

            print(
                f"  Bureau: {end - 1:,}"
            )


# ============================================================
# COLLATERAL
# ============================================================

def seed_collateral(engine):

    print("\nSeeding collateral_assets...")

    sql = text("""
        INSERT INTO collateral_assets (

            loan_id,
            customer_id,
            collateral_type,
            asset_description,
            owner_name,
            registration_number,
            property_address,
            vehicle_registration_number,
            valuation_amount,
            forced_sale_value,
            market_value,
            valuation_date,
            valuer_name,
            valuer_registration_number,
            insurance_policy_number,
            insurance_expiry_date,
            lien_marked,
            hypothecation_number,
            document_number,
            document_type,
            collateral_status

        )

        VALUES (

            :loan_id,
            :customer_id,
            :collateral_type,
            :asset_description,
            :owner_name,
            :registration_number,
            :property_address,
            :vehicle_registration_number,
            :valuation_amount,
            :forced_sale_value,
            :market_value,
            :valuation_date,
            :valuer_name,
            :valuer_registration_number,
            :insurance_policy_number,
            :insurance_expiry_date,
            :lien_marked,
            :hypothecation_number,
            :document_number,
            :document_type,
            :collateral_status

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for loan_id in range(start, end):

                market_value = round(
                    random.uniform(
                        300000,
                        20000000
                    ),
                    2
                )

                batch.append({

                    "loan_id":
                        loan_id,

                    "customer_id":
                        loan_id,

                    "collateral_type":
                        random.choice(
                            COLLATERAL_TYPES
                        ),

                    "asset_description":
                        fake.text(
                            max_nb_chars=200
                        ),

                    "owner_name":
                        fake.name(),

                    "registration_number":
                        "REG-"
                        + ''.join(
                            random.choices(
                                string.ascii_uppercase
                                + string.digits,
                                k=10
                            )
                        ),

                    "property_address":
                        fake.address(),

                    "vehicle_registration_number":
                        generate_vehicle_number(),

                    "valuation_amount":
                        market_value,

                    "forced_sale_value":
                        round(
                            market_value * 0.7,
                            2
                        ),

                    "market_value":
                        market_value,

                    "valuation_date":
                        random_date(
                            2025,
                            2026
                        ),

                    "valuer_name":
                        fake.name(),

                    "valuer_registration_number":
                        "VAL-"
                        + str(
                            random.randint(
                                10000,
                                99999
                            )
                        ),

                    "insurance_policy_number":
                        "POL-"
                        + ''.join(
                            random.choices(
                                string.digits,
                                k=12
                            )
                        ),

                    "insurance_expiry_date":
                        random_date(
                            2026,
                            2030
                        ),

                    "lien_marked":
                        True,

                    "hypothecation_number":
                        "HYPO-"
                        + ''.join(
                            random.choices(
                                string.digits,
                                k=10
                            )
                        ),

                    "document_number":
                        "DOC-"
                        + ''.join(
                            random.choices(
                                string.ascii_uppercase
                                + string.digits,
                                k=12
                            )
                        ),

                    "document_type":
                        random.choice([
                            "SALE_DEED",
                            "RC_BOOK",
                            "GOLD_RECEIPT",
                            "PROPERTY_DOCUMENT"
                        ]),

                    "collateral_status":
                        random.choice([
                            "ACTIVE",
                            "RELEASED",
                            "UNDER_VERIFICATION"
                        ])
                })

            conn.execute(sql, batch)

            print(
                f"  Collateral: {end - 1:,}"
            )


# ============================================================
# CUSTOMER INTERACTIONS
# ============================================================

def seed_interactions(engine):

    print("\nSeeding customer_interactions...")

    sql = text("""
        INSERT INTO customer_interactions (

            customer_id,
            loan_id,
            interaction_type,
            channel,
            agent_id,
            agent_name,
            customer_name,
            customer_phone,
            customer_email,
            interaction_subject,
            interaction_notes,
            call_duration_seconds,
            sentiment,
            resolution_status,
            complaint_category,
            complaint_reference_number,
            recording_reference,
            ip_address,
            device_id

        )

        VALUES (

            :customer_id,
            :loan_id,
            :interaction_type,
            :channel,
            :agent_id,
            :agent_name,
            :customer_name,
            :customer_phone,
            :customer_email,
            :interaction_subject,
            :interaction_notes,
            :call_duration_seconds,
            :sentiment,
            :resolution_status,
            :complaint_category,
            :complaint_reference_number,
            :recording_reference,
            :ip_address,
            :device_id

        )
    """)

    with engine.begin() as conn:

        for start in range(
            1,
            TOTAL_RECORDS + 1,
            BATCH_SIZE
        ):

            batch = []

            end = min(
                start + BATCH_SIZE,
                TOTAL_RECORDS + 1
            )

            for cid in range(start, end):

                name = fake.name()

                batch.append({

                    "customer_id":
                        cid,

                    "loan_id":
                        cid,

                    "interaction_type":
                        random.choice([
                            "CALL",
                            "EMAIL",
                            "CHAT",
                            "BRANCH_VISIT",
                            "SMS"
                        ]),

                    "channel":
                        random.choice([
                            "PHONE",
                            "EMAIL",
                            "MOBILE_APP",
                            "BRANCH",
                            "WEB"
                        ]),

                    "agent_id":
                        "AGT-"
                        + str(
                            random.randint(
                                100,
                                999
                            )
                        ),

                    "agent_name":
                        fake.name(),

                    "customer_name":
                        name,

                    "customer_phone":
                        generate_mobile(),

                    "customer_email":
                        fake.email(),

                    "interaction_subject":
                        random.choice([
                            "EMI query",
                            "Loan statement request",
                            "Address update",
                            "KYC verification",
                            "Foreclosure request",
                            "Payment issue",
                            "Interest rate query"
                        ]),

                    "interaction_notes":
                        generate_interaction_note(
                            name
                        ),

                    "call_duration_seconds":
                        random.randint(
                            30,
                            1800
                        ),

                    "sentiment":
                        random.choice([
                            "POSITIVE",
                            "NEUTRAL",
                            "NEGATIVE"
                        ]),

                    "resolution_status":
                        random.choice([
                            "RESOLVED",
                            "PENDING",
                            "ESCALATED"
                        ]),

                    "complaint_category":
                        random.choice([
                            "PAYMENT",
                            "KYC",
                            "LOAN",
                            "EMI",
                            "SERVICE",
                            "NONE"
                        ]),

                    "complaint_reference_number":
                        "CMP-"
                        + str(
                            random.randint(
                                100000,
                                999999
                            )
                        ),

                    "recording_reference":
                        "/recordings/"
                        + str(cid)
                        + ".wav",

                    "ip_address":
                        fake.ipv4(),

                    "device_id":
                        "DEV-"
                        + ''.join(
                            random.choices(
                                string.ascii_uppercase
                                + string.digits,
                                k=16
                            )
                        )
                })

            conn.execute(sql, batch)

            print(
                f"  Interactions: {end - 1:,}"
            )


# ============================================================
# MAIN
# ============================================================

def seed_database():

    print("=" * 70)

    print("NBFC PII TEST DATABASE SEEDER")

    print("=" * 70)

    print(
        f"Records per table: {TOTAL_RECORDS:,}"
    )

    print(
        f"Batch size: {BATCH_SIZE:,}"
    )

    # Create DB
    create_database()

    # Connect
    engine = create_engine(
        f"mysql+mysqlconnector://"
        f"{DB_USER}:{DB_PASS}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}",
        pool_pre_ping=True
    )

    # Create schema
    create_tables(engine)

    # Seed
    seed_customers(engine)

    seed_customer_addresses(engine)

    seed_employment(engine)

    seed_bank_accounts(engine)

    seed_loan_applications(engine)

    seed_loans(engine)

    seed_repayments(engine)

    seed_credit_bureau(engine)

    seed_collateral(engine)

    seed_interactions(engine)

    print("\n" + "=" * 70)

    print("DATABASE SEEDING COMPLETE")

    print("=" * 70)

    print(
        f"Database: {DB_NAME}"
    )

    print(
        f"Tables: 10"
    )

    print(
        f"Records/table: {TOTAL_RECORDS:,}"
    )

    print(
        f"Approx total records: "
        f"{TOTAL_RECORDS * 10:,}"
    )

    print("=" * 70)

    engine.dispose()


if __name__ == "__main__":
    seed_database()