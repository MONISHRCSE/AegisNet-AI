import time
import json
import os
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
ZEEK_LOG_PATH = "/var/log/zeek/current/conn.log"

r = redis.from_url(REDIS_URL, decode_responses=True)

def tail_conn_log():
    print("[AegisNet-Zeek] Tailing conn.log and forwarding to Redis stream...")
    with open(ZEEK_LOG_PATH, "r") as f:
        # Skip existing content, go to end
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            if line.startswith("#"):
                continue
            try:
                fields = line.strip().split("\t")
                if len(fields) < 20:
                    continue
                record = {
                    "ts": fields[0],
                    "uid": fields[1],
                    "id.orig_h": fields[2],
                    "id.orig_p": fields[3],
                    "id.resp_h": fields[4],
                    "id.resp_p": fields[5],
                    "proto": fields[6],
                    "service": fields[7],
                    "duration": fields[8],
                    "orig_bytes": fields[9],
                    "resp_bytes": fields[10],
                    "conn_state": fields[11],
                }
                r.xadd("stream:telemetry:raw_flows", record, maxlen=100000)
            except Exception as e:
                print(f"[AegisNet-Zeek] Parse error: {e}")

if __name__ == "__main__":
    # Wait for Zeek to create the log file
    while not os.path.exists(ZEEK_LOG_PATH):
        print("[AegisNet-Zeek] Waiting for conn.log...")
        time.sleep(2)
    tail_conn_log()
