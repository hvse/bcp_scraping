import os
import json
import time
import threading
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn

# =========================================================
# CONFIG
# =========================================================

URL = "https://www.bcp.gov.py/webapps/web/cotizacion/monedas"

CACHE_FILE = "bcp_cache.json"

UPDATE_INTERVAL_MINUTES = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="BCP Cotizaciones API",
    version="1.0.0"
)

# =========================================================
# CACHE
# =========================================================

def save_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# =========================================================
# SCRAPER
# =========================================================

def scrape_bcp():
    print(f"[{datetime.now()}] Consultando BCP...")

    session = requests.Session()

    response = session.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    html = response.text

    soup = BeautifulSoup(html, "html.parser")

    cotizaciones = []

    # =====================================================
    # IMPORTANTE:
    # Este selector puede cambiar si BCP cambia el HTML.
    # =====================================================

    rows = soup.select("table tbody tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        moneda = cols[0].get_text(strip=True)
        abreviatura = cols[1].get_text(strip=True)
        valorME_USD = cols[2].get_text(strip=True)
        vvalorGs_ME = cols[3].get_text(strip=True)

        if not moneda:
            continue

        cotizaciones.append({
            "moneda": moneda,
            "abreviatura": abreviatura,
            "valorME_USD": valorME_USD,
            "vvalorGs_ME": vvalorGs_ME
        })

    data = {
        "success": True,
        "source": "BCP",
        "updated_at": datetime.now().isoformat(),
        "total": len(cotizaciones),
        "Observaciones": "ME/USD → Moneda Extranjera por Dólar Estadounidense →→ Gs/ME o Gs ME → Guaraníes por Moneda Extranjera",
        "data": cotizaciones

    }

    save_cache(data)

    print(f"[{datetime.now()}] Cache actualizado")

    return data

# =========================================================
# BACKGROUND JOB
# =========================================================

def update_job():
    try:
        scrape_bcp()
    except Exception as e:
        print(f"[ERROR] {e}")

scheduler = BackgroundScheduler()

scheduler.add_job(
    update_job,
    "interval",
    minutes=UPDATE_INTERVAL_MINUTES
)

# =========================================================
# API ROUTES
# =========================================================

@app.get("/")
def home():
    return {
        "service": "BCP Cotizaciones API",
        "status": "online"
    }


@app.get("/cotizaciones")
def get_cotizaciones():
    cache = load_cache()

    if not cache:
        return {
            "success": False,
            "message": "No hay datos en cache"
        }

    return cache


@app.get("/refresh")
def refresh():
    try:
        data = scrape_bcp()
        return data
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# =========================================================
# STARTUP
# =========================================================

def start_scheduler():
    scheduler.start()

    # Primera carga inmediata
    try:
        scrape_bcp()
    except Exception as e:
        print(f"[INIT ERROR] {e}")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    print("===================================")
    print(" BCP COTIZACIONES SCRAPER")
    print("===================================")

    # Scheduler en background
    threading.Thread(
        target=start_scheduler,
        daemon=True
    ).start()

    # API FastAPI
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )