# services/dictionary_manager_pipe.py  (Lab 6 ready)
import multiprocessing as mp
import json
import uuid

# In-memory transactional dictionary with simple concurrency control.

def run_dictionary_manager(conn, dict_path: str):
    """Dictionary Manager running with Pipe + Transactions"""
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            base = json.load(f)
    except Exception:
        base = {}

    base = {str(k).lower(): v for k, v in base.items()}

    # Transaction state
    tx_writes = {}     # txid -> dict of pending writes {key: value or None for delete}
    key_owner = {}     # key -> txid (write lock)
    tx_active = set()

    def lookup_tx(txid, key):
        key = str(key).lower()
        if txid and txid in tx_writes and key in tx_writes[txid]:
            v = tx_writes[txid][key]
            return None if v is None else v
        return base.get(key)

    def set_tx(txid, key, value):
        key = str(key).lower()
        # lock (write) on key
        owner = key_owner.get(key)
        if owner and owner != txid:
            return False, f"locked by {owner}"
        key_owner[key] = txid
        tx_writes.setdefault(txid, {})[key] = value
        return True, "ok"

    def begin_tx():
        txid = str(uuid.uuid4())[:8]
        tx_active.add(txid)
        tx_writes[txid] = {}
        return txid

    def rollback_tx(txid):
        # release locks
        for k in list(tx_writes.get(txid, {}).keys()):
            if key_owner.get(k) == txid:
                del key_owner[k]
        tx_writes.pop(txid, None)
        tx_active.discard(txid)
        return True

    def commit_tx(txid):
        # 2PC (simplified): PREPARE -> COMMIT
        # PREPARE success if all locks held by us (already ensured).
        # COMMIT: apply and release locks
        writes = tx_writes.get(txid, {})
        for k, v in writes.items():
            if v is None:
                base.pop(k, None)
            else:
                base[k] = v
            if key_owner.get(k) == txid:
                del key_owner[k]
        tx_writes.pop(txid, None)
        tx_active.discard(txid)
        return True

    while True:
        req = conn.recv()
        rid = req.get("id")
        op  = req.get("op","").upper()
        txid = req.get("txid")

        try:
            if op == "LOOKUP":
                key = req["key"]
                val = lookup_tx(txid, key)
                if val is None:
                    conn.send({"id": rid, "status": "not_found"})
                else:
                    conn.send({"id": rid, "status": "ok", "value": val})

            elif op in ("INSERT","UPDATE"):
                key, value = req["key"], req["value"]
                ok, msg = set_tx(txid, key, value)
                status = "ok" if ok else "retry"
                conn.send({"id": rid, "status": status, "value": msg})

            elif op == "DELETE":
                key = req["key"]
                ok, msg = set_tx(txid, key, None)
                status = "ok" if ok else "retry"
                conn.send({"id": rid, "status": status, "value": msg})

            elif op == "BEGIN":
                new_tx = begin_tx()
                conn.send({"id": rid, "status": "ok", "txid": new_tx})

            elif op == "ROLLBACK":
                rollback_tx(txid)
                conn.send({"id": rid, "status": "ok"})

            elif op == "PREPARE":
                status = "ok" if txid in tx_active else "error"
                conn.send({"id": rid, "status": status})

            elif op == "COMMIT":
                commit_tx(txid)
                conn.send({"id": rid, "status": "ok"})

            elif op == "SHUTDOWN":
                conn.send({"id": rid, "status": "ok", "value": "Shutting down"})
                break

            else:
                conn.send({"id": rid, "status": "error", "value": f"Unsupported op: {op}"})
        except Exception as e:
            conn.send({"id": rid, "status": "error", "value": str(e)})

def start_dictionary_manager_pipe(dict_path: str):
    parent_conn, child_conn = mp.Pipe(duplex=True)
    proc = mp.Process(target=run_dictionary_manager, args=(child_conn, dict_path))
    proc.daemon = True
    proc.start()
    return parent_conn, proc

