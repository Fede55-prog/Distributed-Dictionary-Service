import json, socket, threading, time, os

HOST = "0.0.0.0"
PORT = int(os.getenv("NAMING_PORT", "8000"))
TTL_SECONDS = int(os.getenv("TTL_SECONDS", "20"))
HEARTBEAT_GRACE = int(os.getenv("HEARTBEAT_GRACE", "10"))

# registry: name -> {"host": str, "port": int, "last_seen": float}
REGISTRY = {}
REG_LOCK = threading.Lock()

def prune_loop():
    while True:
        time.sleep(3)
        now = time.time()
        with REG_LOCK:
            dead = [name for name, meta in REGISTRY.items()
                    if now - meta["last_seen"] > TTL_SECONDS + HEARTBEAT_GRACE]
            for name in dead:
                REGISTRY.pop(name, None)

def handle_conn(conn, addr):
    with conn:
        buf = conn.recv(65536).decode("utf-8").strip()
        if not buf:
            return
        try:
            msg = json.loads(buf)
        except Exception:
            conn.sendall(b'{"status":"error","error":"invalid_json"}')
            return

        typ = msg.get("type")
        if typ == "register":
            name = msg["name"]; host = msg["host"]; port = int(msg["port"])
            with REG_LOCK:
                REGISTRY[name] = {"host": host, "port": port, "last_seen": time.time()}
            conn.sendall(json.dumps({"status": "ok"}).encode())
        elif typ == "heartbeat":
            name = msg["name"]
            with REG_LOCK:
                if name in REGISTRY:
                    REGISTRY[name]["last_seen"] = time.time()
            conn.sendall(json.dumps({"status": "ok"}).encode())
        elif typ == "lookup":
            # choose a live server (round-robin simple: pick the first)
            with REG_LOCK:
                live = sorted(REGISTRY.items(), key=lambda kv: kv[0])
                if not live:
                    conn.sendall(json.dumps({"status":"error","error":"no_servers"}).encode())
                    return
                # pick the one with most recent heartbeat
                live.sort(key=lambda kv: kv[1]["last_seen"], reverse=True)
                name, meta = live[0]
            conn.sendall(json.dumps({"status":"ok","name":name,"host":meta["host"],"port":meta["port"]}).encode())
        elif typ == "deregister":
            name = msg["name"]
            with REG_LOCK:
                REGISTRY.pop(name, None)
            conn.sendall(json.dumps({"status":"ok"}).encode())
        else:
            conn.sendall(json.dumps({"status":"error","error":"unknown_type"}).encode())

def main():
    threading.Thread(target=prune_loop, daemon=True).start()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[naming] listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_conn, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
