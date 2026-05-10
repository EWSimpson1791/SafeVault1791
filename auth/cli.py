# auth/cli.py
import argparse
from auth.auth_manager import create_user_with_generated_password, create_user, generate_password

def main():
    parser = argparse.ArgumentParser(description="Auth CLI for Risk_Battle_Game_A")
    sub = parser.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("create-generated", help="Create user with generated password")
    add.add_argument("username")
    add.add_argument("--length", type=int, default=20)

    add2 = sub.add_parser("create", help="Create user with provided password")
    add2.add_argument("username")
    add2.add_argument("password")

    args = parser.parse_args()
    if args.cmd == "create-generated":
        out = create_user_with_generated_password(args.username, length=args.length)
        if out.get("created"):
            print("User created:", out["username"])
            print("Generated password (show once):", out["password"])
        else:
            print("Failed to create user:", out.get("reason", "unknown"))
    elif args.cmd == "create":
        out = create_user(args.username, args.password)
        if out.get("created"):
            print("User created:", out["username"])
        else:
            print("Failed to create user:", out.get("reason", "unknown"))

if __name__ == "__main__":
    main()
