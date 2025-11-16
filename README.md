
# Distributed Dictionary – Labs 1–6

## Run
```bash
docker compose up --build

Start FIFO server:
docker compose run fifo_server

Start FIFO client:

docker compose run fifo_client

Socket mode (Labs 2–3, 5–6):
docker compose --profile socket up


FIFO mode (Lab 4):
docker compose --profile fifo up


Demonstration Script
🔹 Step 1: Build the system

From the root project folder, run:

docker compose build

🔹 Step 2: Run the system

Socket mode (Labs 1–3, 5–6):

docker compose --profile socket up


FIFO mode (Lab 4, IPC demo):

docker compose --profile fifo up

🔹 Step 3: Test cases
(a) Single Client – Basic CRUD

Start the system in socket mode.

Attach to client:

docker exec -it dictionary_client python /app/client.py


Run:

GET hello → expect sawubona.

INSERT uni → University of Zululand.

UPDATE uni → UniZulu.

DELETE uni.

Confirms dictionary CRUD works for one client.

(b) Multi-Client Concurrency

Open two terminals and attach clients:

docker exec -it dictionary_client python /app/client.py
docker run -it --rm --network=dictionary-service-final_default client-image python /app/client.py


Both clients insert/update keys at the same time.

Logs show multithreading, and dictionary data remains consistent (thanks to locks).

(c) Failure Recovery

While clients are running, stop one server:

docker stop dictionary_server1


The naming service deregisters it.

Clients still resolve server2 and continue normally.

 Confirms naming service fault tolerance.

(d) Transactions & Rollback

In client, select option 5 (Simulated TX failure).

Update a key with fail_after_write=True.

Server simulates a crash → rolls back.

GET the same key.

confirms that rollback works and no partial updates occur.

(e) FIFO IPC Demo (Lab 4 only)
Start in FIFO mode:
docker compose --profile fifo up
Attach to FIFO client:
docker exec -it fifo_client python /app/client.py


Run GET/INSERT/UPDATE/DELETE like before.

Requests and responses flow via named pipes, proving IPC functionality.

Step 4: Shutdown
After testing:
docker compose down
