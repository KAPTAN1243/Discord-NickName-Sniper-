import sys
import requests
import threading
import time
import queue
import string
import random
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
        return "Bot is alive 24/7!"

def keep_alive():
        t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
        t.daemon = True
        t.start()

WEBHOOK_URL = "https://discord.com/api/webhooks/1497368595968163850/278eP8w1R5BMDJmZBpOqcWJJoBOiRCMKOOUqT_eKUY8Q1Sl-8kXXJTJbuRMChzbO0OTA"
THREADS_COUNT = 50
PROXY_REFRESH_INTERVAL = 60
MAX_PROXY_FAILS = 1
TIMEOUT = 2.0
USE_PROXIES = True
WEBHOOK_INTERVAL = 1.0

hits = misses = errors = ratelimits = total_checked = checks_per_second = current_cps = 0
start_time = None
proxy_lock = threading.Lock()
proxies_list = []
proxy_fail_count = {}
proxy_ping = {}
webhook_queue = queue.Queue()

class AIOptimizer:
        @staticmethod
        def rank_proxies():
                    global proxies_list
                    with proxy_lock:
                                    good = [p for p in proxies_list if proxy_fail_count.get(p,0) < MAX_PROXY_FAILS and proxy_ping.get(p,0.5) < 2.0]
                                    good.sort(key=lambda p: proxy_ping.get(p,1000))
                                    proxies_list = good

                @staticmethod
        def record_ping(p, t):
                    if p is None: return
        with proxy_lock:
                        proxy_ping[p] = (proxy_ping.get(p,t) + t) / 2

PROXY_SOURCES = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://proxyspace.pro/socks5.txt",
        "https://proxyspace.pro/http.txt",
]

def fetch_proxies_from_url(url):
        result = set()
    protocol = "socks5" if "socks5" in url.lower() else "http"
    try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                                for line in r.text.splitlines():
                                                    p = line.strip()
                                                    if p and ":" in p and len(p) < 30:
                                                                            parts = p.split(":")
                                                                            if len(parts) >= 2 and parts[-1].isdigit():
                                                                                                        result.add(f"{protocol}://{p}")
                                                                                    except: pass
                                                                                            return result

                                    def fetch_all_proxies():
                                            all_p = set()
                                            with ThreadPoolExecutor(max_workers=8) as ex:
                                                        for f in [ex.submit(fetch_proxies_from_url, u) for u in PROXY_SOURCES]:
                                                                        try: all_p.update(f.result(timeout=10))
                                                                                        except: pass
                                                                                                return list(all_p)

                                                def load_proxies():
                                                        global proxies_list, proxy_fail_count, proxy_ping
                                                        online = fetch_all_proxies()
                                                        with proxy_lock:
                                                                    proxies_list = list(set(online))
                                                                    proxy_fail_count = {}; proxy_ping = {}
                                                                AIOptimizer.rank_proxies()
                                                        print(f"[AI] {len(proxies_list)} proxy aktif.")

                                        def get_proxy():
                                                with proxy_lock:
                                                            if not proxies_list: return None
                                                                        top = max(1, len(proxies_list) // 5)
                                                            return random.choice(proxies_list[:top])

                                            def format_proxy(p):
                                                    return {"http": p, "https": p} if p else None

                    def mark_fail(p):
                            if not p: return
                                    with proxy_lock:
                                                proxy_fail_count[p] = proxy_fail_count.get(p,0) + 1
                                                proxy_ping[p] = proxy_ping.get(p,1000) + 2.0

def mark_ok(p):
        if not p: return
                with proxy_lock: proxy_fail_count[p] = 0

def proxy_refresher():
        while True:
                    time.sleep(PROXY_REFRESH_INTERVAL)
        new = fetch_all_proxies()
        with proxy_lock:
                        ex = set(proxies_list)
            for p in new:
                                if p not in ex: proxies_list.append(p)
                                            AIOptimizer.rank_proxies()
        print(f"[PROXY] Guncellendi: {len(proxies_list)} proxy")

USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
]

def get_headers():
        return {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json", "Accept": "*/*", "Origin": "https://discord.com", "Referer": "https://discord.com/register"}

sessions = {}
sessions_lock = threading.Lock()

def get_session(p):
        with sessions_lock:
                    if p not in sessions:
                                    s = requests.Session()
                                    s.proxies = format_proxy(p)
                                    sessions[p] = s
                                return sessions[p]

def check_username(username, proxy_str):
        url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    t0 = time.time()
    try:
                if USE_PROXIES and proxy_str:
                                r = get_session(proxy_str).post(url, json={"username": username}, headers=get_headers(), timeout=TIMEOUT)
else:
            r = requests.post(url, json={"username": username}, headers=get_headers(), timeout=TIMEOUT)
        AIOptimizer.record_ping(proxy_str, time.time() - t0)
        if r.status_code == 200:
                        return "available" if not r.json().get("taken", True) else "taken"
elif r.status_code == 429: return "ratelimit"
else: return "error"
    except:
        AIOptimizer.record_ping(proxy_str, 5.0)
        return "error"

def send_webhook(username):
        nick_type = "Sayisal" if username.isdigit() else ("Harf" if username.isalpha() else "Karma")
    embed = {
                "title": "BOSTA USERNAME BULUNDU!",
                "description": f"**Username:** `{username}`\n**Durum:** Bosta\n**Tip:** {nick_type} ({len(username)} karakter)\n**Tarih:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                "color": 0x2ecc71,
                "footer": {"text": "Discord Sniper v6.0 | 7/24 Aktif"}
    }
    payload = {"content": "@everyone Bosta Nick!", "embeds": [embed]}
    for _ in range(3):
                try:
                                r = requests.post(WEBHOOK_URL, json=payload, timeout=8)
                                if r.status_code in (200, 204): return
                                                if r.status_code == 429:
                                                                    time.sleep(float(r.json().get("retry_after", 2)))
                                                            except: time.sleep(2)
def webhook_dispatcher():
        while True:
                    try:
                                    username = webhook_queue.get(timeout=5)
                                    if username:
                                                        send_webhook(username)
                                                        print(f"[WEBHOOK] Gonderildi: {username}")
                                                    time.sleep(WEBHOOK_INTERVAL)
except queue.Empty: continue
except Exception as e:
            print(f"[WEBHOOK HATA] {e}")
            time.sleep(3)

def generate_all_usernames():
        out = set()
    L = string.ascii_lowercase
    D = string.digits
    for length in range(2, 5):
                for _ in range(2000):
                                out.add("".join(random.choice(D) for _ in range(length)))
    for length in range(5, 9):
                for _ in range(5000):
                                out.add("".join(random.choice(D) for _ in range(length)))
    for length in range(2, 6):
                for _ in range(3000):
                                out.add("".join(random.choice(L) for _ in range(length)))
    for _ in range(5000):
                n = "".join(random.choice(D) for _ in range(random.randint(2,4)))
        a = "".join(random.choice(L) for _ in range(random.randint(2,4)))
        out.add(n+a); out.add(a+n)
    for _ in range(3000):
                a, b = random.choice(D), random.choice(D)
        out.add(a*3+b*3); out.add(a+b+a+b+a+b)
    return list(out)

def worker(q):
        global hits, misses, errors, ratelimits, total_checked, checks_per_second
    while True:
                try: username = q.get(timeout=5)
except queue.Empty: continue
        if username is None: break
                    proxy = get_proxy() if USE_PROXIES else None
        result = check_username(username, proxy)
        if result == "available":
                        hits += 1; total_checked += 1
            print(f"[HIT] {username} BOSTA!")
            webhook_queue.put(username)
            mark_ok(proxy)
elif result == "taken":
            misses += 1; total_checked += 1
            mark_ok(proxy)
elif result == "ratelimit":
            ratelimits += 1; mark_fail(proxy); q.put(username); time.sleep(1)
else:
            errors += 1; mark_fail(proxy); q.put(username)
        if total_checked % 25 == 0:
                        AIOptimizer.rank_proxies()
        q.task_done()

def main():
        global start_time
    print("=== DISCORD NICK SNIPER v6.0 - 7/24 AKTIF ===")
    keep_alive()
    print("[PROXY] Yukleniyor...")
    load_proxies()
    start_time = time.time()
    threading.Thread(target=proxy_refresher, daemon=True).start()
    threading.Thread(target=webhook_dispatcher, daemon=True).start()
    q = queue.Queue(maxsize=100000)
    for _ in range(THREADS_COUNT):
                threading.Thread(target=worker, args=(q,), daemon=True).start()
    loop = 0
    usernames = []
    print("[OK] TARAMA BASLADI!")
    while True:
                try:
                                new = generate_all_usernames()
                                usernames = list(set(usernames + new))
                                random.shuffle(usernames)
                                loop += 1
                                print(f"[DONGU #{loop}] {len(usernames)} hedef")
                                for u in usernames:
                q.put(u)
            q.join()
            if loop % 5 == 0:
                usernames = []
except KeyboardInterrupt:
            break
except Exception as e:
            print(f"[HATA] {e}")
            time.sleep(10)

if __name__ == "__main__":
        main()
    
