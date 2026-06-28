import time
import random
import os
from datetime import datetime

ZEEK_LOG_FILE = "/var/log/zeek/current/conn.log"

def generate_zeek_line():
    ts = time.time()
    uid = f"C{random.randint(10000000, 99999999)}"
    src_ip = f"192.168.1.{random.randint(10, 250)}"
    src_port = random.randint(1024, 65535)
    
    # 10% chance of malicious traffic
    if random.random() < 0.10:
        dst_ip = "10.0.0.5" # Honeypot or target
        dst_port = 22 # SSH brute force simulation
        proto = "tcp"
        service = "ssh"
        conn_state = "S0" # Attempted connection
        missed_bytes = 0
        history = "S"
        pkts_sent = random.randint(5, 50)
        bytes_sent = pkts_sent * random.randint(40, 100)
        pkts_recv = 0
        bytes_recv = 0
        duration = random.uniform(0.1, 2.0)
    else:
        # Normal traffic
        dst_ip = f"8.8.8.{random.randint(8, 9)}"
        dst_port = 443
        proto = "tcp"
        service = "ssl"
        conn_state = "SF"
        missed_bytes = 0
        history = "ShADadFf"
        pkts_sent = random.randint(10, 100)
        bytes_sent = pkts_sent * random.randint(100, 1500)
        pkts_recv = random.randint(10, 100)
        bytes_recv = pkts_recv * random.randint(100, 1500)
        duration = random.uniform(1.0, 30.0)

    # Zeek format fields (TS, UID, id.orig_h, id.orig_p, id.resp_h, id.resp_p, proto, service, duration, orig_bytes, resp_bytes, conn_state, local_orig, local_resp, missed_bytes, history, orig_pkts, orig_ip_bytes, resp_pkts, resp_ip_bytes, tunnel_parents)
    # The parser in parser.py splits by tab and expects JSON if it starts with { or plain TSV.
    # The worker says: "parse_conn_log_line". If it's Zeek default, it's TSV.
    
    line = f"{ts}\t{uid}\t{src_ip}\t{src_port}\t{dst_ip}\t{dst_port}\t{proto}\t{service}\t{duration:.6f}\t{bytes_sent}\t{bytes_recv}\t{conn_state}\t-\t-\t{missed_bytes}\t{history}\t{pkts_sent}\t{bytes_sent}\t{pkts_recv}\t{bytes_recv}\t(empty)"
    return line

def run():
    os.makedirs(os.path.dirname(ZEEK_LOG_FILE), exist_ok=True)
    if not os.path.exists(ZEEK_LOG_FILE):
        with open(ZEEK_LOG_FILE, "w") as f:
            f.write("#separator \\x09\n#set_separator\t,\n#empty_field\t(empty)\n#unset_field\t-\n#path\tconn\n#open\t2026-05-17-00-00-00\n")
            f.write("#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\tservice\tduration\torig_bytes\tresp_bytes\tconn_state\tlocal_orig\tlocal_resp\tmissed_bytes\thistory\torig_pkts\torig_ip_bytes\tresp_pkts\tresp_ip_bytes\ttunnel_parents\n")
            f.write("#types\ttime\tstring\taddr\tport\taddr\tport\tenum\tstring\tinterval\tcount\tcount\tstring\tbool\tbool\tcount\tstring\tcount\tcount\tcount\tcount\tset[string]\n")
            
    print(f"Starting synthetic Zeek telemetry generator writing to {ZEEK_LOG_FILE}")
    while True:
        line = generate_zeek_line()
        with open(ZEEK_LOG_FILE, "a") as f:
            f.write(line + "\n")
        time.sleep(random.uniform(0.1, 2.0))

if __name__ == "__main__":
    run()
