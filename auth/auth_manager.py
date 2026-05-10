# auth/auth_manager.py

from pathlib import Path
import sqlite3
import bcrypt
import subprocess
from typing import Optional

DB_PATH = Path(__file__).resolve().parents[1] / "auth.db"


# ---------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------

def _get_conn():
    """Return SQLite connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create users table if it does not exist."""
    conn = _get_conn()
    cur = conn.cursor()

    # noinspection SqlNoDataSourceInspection
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------

def _hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------
# User Management
# ---------------------------------------------------------

def create_user(username: str, password: str) -> dict:
    """Create a user with a plaintext password."""
    init_db()
    conn = _get_conn()
    cur = conn.cursor()
    pw_hash = _hash_password(password)

    try:
        # noinspection SqlNoDataSourceInspection
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw_hash)
        )
        conn.commit()
        return {"username": username, "created": True}

    except sqlite3.IntegrityError:
        return {"username": username, "created": False, "reason": "username_exists"}

    finally:
        conn.close()


def authenticate(username: str, password: str) -> bool:
    """Verify username/password."""
    init_db()
    conn = _get_conn()
    cur = conn.cursor()

    # noinspection SqlNoDataSourceInspection
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    return _verify_password(password, row["password_hash"])


# ---------------------------------------------------------
# Secure Password Generator Integration
# ---------------------------------------------------------

def _generate_password_via_module(length: int = 20, **kwargs) -> Optional[str]:
    """Try to import secure_password_generator module."""
    try:
        import secure_password_generator as spg  # type: ignore
        return spg.generate(length=length, **kwargs)
    except ImportError:
        return None
    except (ValueError, TypeError):
        return None


def _generate_password_via_cli(
    length: int = 20,
    exe_path: str = "SecurePasswordGenerator.exe"
) -> Optional[str]:
    """Fallback: call external executable."""
    try:
        proc = subprocess.run(
            [exe_path, "--length", str(length)],
            capture_output=True,
            text=True,
            check=True
        )
        return proc.stdout.strip()

    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError:
        return None
    except OSError:
        return None


def generate_password(length: int = 20, **options) -> str:
    """Try module import first, then CLI."""
    pw = _generate_password_via_module(length=length, **options)
    if pw:
        return pw

    pw = _generate_password_via_cli(length=length)
    if pw:
        return pw

    raise RuntimeError("Secure password generator not available (module or CLI).")


def create_user_with_generated_password(
    username: str,
    length: int = 20,
    **gen_options
) -> dict:
    """Create a user using a generated password."""
    password = generate_password(length=length, **gen_options)
    res = create_user(username, password)

    if not res.get("created"):
        return res

    return {"username": username, "created": True, "password": password}


# ---------------------------------------------------------
# Authentication Menu + Flows
# ---------------------------------------------------------

def create_account_flow() -> None:
    """Interactive flow to create a new user."""
    print("\n=== CREATE ACCOUNT ===")
    username = input("New username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    password = input("New password: ").strip()
    if not password:
        print("Password cannot be empty.")
        return

    result = create_user(username, password)
    if result.get("created"):
        print(f"Account created for user '{username}'.")
    else:
        reason = result.get("reason", "unknown_error")
        if reason == "username_exists":
            print(f"Username '{username}' already exists.")
        else:
            print("Failed to create account:", reason)


def login_flow() -> bool:
    """Interactive login flow."""
    print("\n=== LOGIN ===")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if authenticate(username, password):
        print(f"Welcome, {username}.")
        return True
    else:
        print("Invalid username or password.")
        return False


def auth_menu() -> bool:
    """Top-level authentication menu."""
    while True:
        print("\n=== AUTHENTICATION ===")
        print("1. Login")
        print("2. Create Account")
        print("3. Exit")

        choice = input("Select option: ").strip()

        if choice == "1":
            if login_flow():
                return True
        elif choice == "2":
            create_account_flow()
        elif choice == "3":
            print("Exiting authentication.")
            return False
        else:
            print("Invalid choice. Please try again.")
