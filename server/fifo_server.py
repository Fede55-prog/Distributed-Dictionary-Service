import os, json, threading

REQ_FIFO = "/tmp/dict_req"
RESP_FIFO = "/tmp/dict_resp"

# Ensure FIFO files exist
for fifo in [REQ_FIFO, RESP_FIFO]:
    try:
        os.mkfifo(fifo)
    except FileExistsError:
        pass

dictionary = {"hello": "sawubona", "world": "umhlaba"}
lock = threading.Lock()

print("[fifo_server] Ready. Waiting for requests...")

while True:
    with open(REQ_FIFO, "r") as req:
        line = req.readline().strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except Exception:
            continue

        op = msg.get("op")
        key = msg.get("key")
        val = msg.get("value")

        with lock:
            if op == "get":
                result = dictionary.get(key, "not_found")
            elif op == "insert":
                dictionary[key] = val
                result = "inserted"
            elif op == "update":
                if key in dictionary:
                    dictionary[key] = val
                    result = "updated"
                else:
                    result = "missing"
            elif op == "delete":
                dictionary.pop(key, None)
                result = "deleted"
            else:
                result = "unknown_op"

        with open(RESP_FIFO, "w") as resp:
            resp.write(json.dumps({"status": result}) + "\n")
