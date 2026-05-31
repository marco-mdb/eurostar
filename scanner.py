"""
Eurostar Snap Scanner — GitHub Actions edition
Checks target dates and sends a Gmail alert if available.
Run once per invocation — GitHub Actions handles the scheduling.
"""

import json
import os
import re
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup


# ==============================================================
#  CONFIG
#  Do NOT put real credentials here.
#  Set these as GitHub Secrets (see README) and they are
#  injected automatically as environment variables at runtime.
# ==============================================================

WATCH_DATES =  os.environ["WATCH_DATES"]

# Read from GitHub Secrets — set these in your repo settings
GMAIL_FROM         = os.environ["GMAIL_FROM"]
GMAIL_TO           = os.environ["GMAIL_TO"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

SEARCH_URL = (
    "https://snap.eurostar.com/uk-en/search"
    "?adult=1&origin=7015400&destination=8727100&outbound={date}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ==============================================================
#  FETCH
# ==============================================================

def fetch_availability(date_str: str) -> list[dict]:
    """
    Fetch the Snap page for a date and return available slots.
    Reads the __NEXT_DATA__ JSON blob embedded in the page —
    no browser needed.
    """
    url = SEARCH_URL.format(date=date_str)
    print(f"  Fetching {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    tag  = soup.find("script", {"id": "__NEXT_DATA__"})
    if not tag:
        print("  __NEXT_DATA__ not found in page")
        return []

    try:
        data = json.loads(tag.string)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return []

    try:
        slots_raw = data["props"]["pageProps"]["outboundTimeSlots"] or []
    except KeyError:
        print("  outboundTimeSlots key missing")
        return []

    available = []
    for slot in slots_raw:
        if not slot.get("id", "").startswith(date_str):
            continue

        fare   = slot.get("fare") or {}
        window = slot.get("departureWindow") or {}

        # Skip slots with no fare data — not yet bookable
        prices = fare.get("prices") or {}
        price  = prices.get("displayPrice")
        if price is None:
            print(f"  Skipping slot {slot.get('id')} — no price data yet")
            continue

        earliest   = window.get("earliest", "")[-5:]
        latest     = window.get("latest",   "")[-5:]
        time_label = f"{earliest} - {latest}" if earliest else slot["id"]

        available.append({
            "time":  time_label,
            "price": price,
            "seats": fare.get("seats"),
        })

    return available


# ==============================================================
#  EMAIL
# ==============================================================

def send_email(subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_FROM
        msg["To"]      = GMAIL_TO
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_FROM, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_FROM, GMAIL_TO, msg.as_string())
        return True
    except Exception as e:
        print(f"  Email error: {e}")
        return False


def build_email(date_str: str, slots: list[dict]) -> tuple[str, str]:
    dt       = datetime.strptime(date_str, "%Y-%m-%d")
    friendly = dt.strftime("%A %d %B")
    subject  = f"Eurostar Snap available — {friendly}!"

    slot_lines = "\n".join(
        f"  • {s['time']}   £{s['price']}   ({s['seats']} seats left)"
        for s in slots
    )
    book_url = SEARCH_URL.format(date=date_str)

    body = (
        f"A Snap fare just appeared for {friendly}!\n\n"
        f"Available slots:\n{slot_lines}\n\n"
        f"Book NOW — these sell out in minutes:\n{book_url}\n\n"
        f"Snap fares are non-refundable and non-exchangeable.\n\n"
        f"---\nSent by your Eurostar Snap scanner (GitHub Actions)"
    )
    return subject, body


# ==============================================================
#  MAIN
# ==============================================================

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] Eurostar Snap scanner")
    print(f"Watching: {', '.join(WATCH_DATES)}\n")

    found_any = False

    for date_str in WATCH_DATES:
        print(f"Checking {date_str}...")
        slots = fetch_availability(date_str)

        if not slots:
            print("  → Not available\n")
            continue

        found_any = True
        for s in slots:
            print(f"  → AVAILABLE: {s['time']}  £{s['price']}  ({s['seats']} seats)")

        subject, body = build_email(date_str, slots)
        print("  → Sending email...")
        if send_email(subject, body):
            print("  → Email sent!\n")
        else:
            print("  → Email failed\n")
            sys.exit(1)  # causes GitHub Actions to flag the run as failed

    if not found_any:
        print("No availability found on any watched date.")


if __name__ == "__main__":
    main()
