import os, json

REQ_FIFO = "/tmp/dict_req"
RESP_FIFO = "/tmp/dict_resp"

menu = """
FIFO Dictionary Client
1) GET
2) INSERT
3) UPDATE
4) DELETE
q) Quit
Choice: """

while True:
    choice = input(menu).strip().lower()
    if choice == "q":
        break

    if choice == "1":
        key = input("key: ")
        msg = {"op": "get", "key": key}
    elif choice == "2":
        key = input("key: "); val = input("value: ")
        msg = {"op": "insert", "key": key, "value": val}
    elif choice == "3":
        key = input("key: "); val = input("value: ")
        msg = {"op": "update", "key": key, "value": val}
    elif choice == "4":
        key = input("key: ")
        msg = {"op": "delete", "key": key}
    else:
        print("invalid choice")
        continue

    # Write request
    with open(REQ_FIFO, "w") as req:
        req.write(json.dumps(msg) + "\n")

    # Read response
    with open(RESP_FIFO, "r") as resp:
        print("Response:", resp.readline().strip())
