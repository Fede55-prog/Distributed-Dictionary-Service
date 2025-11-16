import json
import os
import socket
import threading
import time
import shutil

# --- Config ---
MAX_WORDS = 10  # Maximum number of words allowed in the dictionary
COMM_MODE = os.getenv("COMM_MODE", "socket")  # "socket" or "fifo"
HOST = "0.0.0.0"
PORT = int(os.getenv("SERVER_PORT", "9000"))
SERVER_NAME = os.getenv("SERVER_NAME", "server1")
DATA_FILE = os.getenv("DATA_FILE", "./dictionary.json")
BACKUP_FILE = DATA_FILE + ".bak"

DICT_LOCK = threading.Lock()

# --- Dictionary helpers ---
def load_dict():
    """ Function to load the dictionary from a JSON file. """
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"hello": "sawubona", "world": "umhlaba"}, f, indent=2)
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_dict(d):
    """ Function to save the dictionary back to the JSON file. """
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def backup_state():
    """ Backup the current state of the dictionary. """
    shutil.copyfile(DATA_FILE, BACKUP_FILE)


def rollback_state():
    """ Rollback the dictionary to the previous state. """
    if os.path.exists(BACKUP_FILE):
        shutil.copyfile(BACKUP_FILE, DATA_FILE)


# --- Authentication (email + password) ---
USER_CREDENTIALS = {
    "admin@example.com": "admin123",  # admin email and password
    "user@example.com": "user123"    # standard user email and password
}


def authenticate(email, password):
    """ Authenticate the user with email and password. """
    stored_password = USER_CREDENTIALS.get(email)
    if stored_password == password:
        return True
    return False


# --- Add Word (FIFO) ---
def add_word(name, definition):
    """ Add a new word to the dictionary, using FIFO if full. """
    d = load_dict()
    if len(d) >= MAX_WORDS:
        # Remove the first word (FIFO)
        first_name = list(d.keys())[0]
        d.pop(first_name)
        print(f"Removed word: {first_name} (FIFO)")

    d[name] = definition
    save_dict(d)


# --- Core handler (updated for user types) ---
def process_request(req):
    """ Handle the incoming request and perform dictionary operations. """
    op = req.get("op")
    email = req.get("email")
    password = req.get("password")
    user_type = req.get("user_type", "standard")

    if user_type == "admin":
        if not authenticate(email, password):
            return {"status": "error", "error": "authentication_failed"}

    try:
        if op == "get":
            name = req["name"]
            with DICT_LOCK:
                d = load_dict()
                return {"status": "ok", "definition": d.get(name, "not_found")}

        if op == "insert":
            if user_type != "admin":
                return {"status": "error", "error": "admin_only"}
            with DICT_LOCK:
                d = load_dict()
                if req["name"] in d:
                    return {"status": "error", "error": "exists"}
                add_word(req["name"], req["definition"])
                return {"status": "ok"}

        if op == "update":
            if user_type != "admin":
                return {"status": "error", "error": "admin_only"}
            with DICT_LOCK:
                d = load_dict()
                if req["name"] not in d:
                    return {"status": "error", "error": "missing"}
                d[req["name"]] = req["definition"]
                save_dict(d)
                return {"status": "ok"}

        if op == "delete":
            if user_type != "admin":
                return {"status": "error", "error": "admin_only"}
            with DICT_LOCK:
                d = load_dict()
                if req["name"] not in d:
                    return {"status": "error", "error": "missing"}
                del d[req["name"]]
                save_dict(d)
                return {"status": "ok"}

        return {"status": "error", "error": "unknown_op"}
    except Exception as e:
        return {"status": "error", "error": "exception", "detail": str(e)}


# --- Socket mode ---
def handle_client(conn, addr):
    """ Handle incoming client requests in socket mode. """
    with conn:
        buf = conn.recv(65536).decode("utf-8").strip()
        if not buf:
            return
        try:
            req = json.loads(buf)
        except Exception:
            conn.sendall(b'{"status":"error","error":"invalid_json"}')
            return
        result = process_request(req)
        conn.sendall(json.dumps(result).encode())


def run_socket_server():
    """ Run the server and listen for client connections. """
    if not os.path.exists(DATA_FILE):
        save_dict({})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server running at {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    run_socket_server()

