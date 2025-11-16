import json
import socket

# --- Config ---
NAMING_HOST = "127.0.0.1"
NAMING_PORT = 9000  # Same port as server

# Function to interact with the server
def ask_server(payload):
    try:
        with socket.create_connection((NAMING_HOST, NAMING_PORT), timeout=5) as s:
            s.sendall(json.dumps(payload).encode())
            return json.loads(s.recv(65536).decode())
    except Exception as e:
        return {"status": "error", "error": f"server_unavailable: {str(e)}"}

# Function to handle the interactive client menu
def interactive():
    menu = """
Dictionary Client
1) GET
2) INSERT
3) UPDATE
4) DELETE
q) Quit
Choice: """
    while True:
        ch = input(menu).strip().lower()
        try:
            if ch == "1":
                name = input("name: ")
                print(ask_server({"op": "get", "name": name}))
            elif ch == "2":
                name = input("name: ")
                definition = input("definition: ")
                email = input("Email (Admin only): ")
                password = input("Password (Admin only): ")
                print(ask_server({"op": "insert", "name": name, "definition": definition, "email": email, "password": password, "user_type": "admin"}))
            elif ch == "3":
                name = input("name: ")
                definition = input("definition: ")
                email = input("Email (Admin only): ")
                password = input("Password (Admin only): ")
                print(ask_server({"op": "update", "name": name, "definition": definition, "email": email, "password": password, "user_type": "admin"}))
            elif ch == "4":
                name = input("name: ")
                email = input("Email (Admin only): ")
                password = input("Password (Admin only): ")
                print(ask_server({"op": "delete", "name": name, "email": email, "password": password, "user_type": "admin"}))
            elif ch == "q":
                break
            else:
                print("invalid choice")
        except Exception as e:
            print("error:", e)

if __name__ == "__main__":
    interactive()
