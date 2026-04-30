#!/usr/bin/env python3
"""Seed data: `--direct` inserts into Postgres; default posts webhooks to the API."""

import argparse
import os
import random
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv()

fake = Faker()

EVENT_TYPES = [
    ("call_dial", 0.50),
    ("call_connect", 0.20),
    ("email_sent", 0.25),
    ("meeting_booked", 0.04),
    ("meeting_attended", 0.01),
]

SOURCES = ["nooks", "outreach", "manual", "zapier"]


def _api_base() -> str:
    host = os.getenv("API_HOST", "localhost")
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    port = os.getenv("API_PORT", "8000")
    return f"http://{host}:{port}"


def generate_event():
    event_type = random.choices(
        [e[0] for e in EVENT_TYPES], weights=[e[1] for e in EVENT_TYPES]
    )[0]
    metadata = {"prospect_name": fake.name(), "company": fake.company()}
    if event_type in ["call_dial", "call_connect"]:
        metadata["phone_number"] = fake.phone_number()
    if event_type == "email_sent":
        metadata["email"] = fake.email()
    return {
        "source": random.choice(SOURCES),
        "event_type": event_type,
        "metadata": metadata,
    }


def seed_direct() -> None:
    from database.queries import DatabaseQueries

    db = DatabaseQueries()
    samples = [
        ("manual", "call_dial", {}),
        ("manual", "call_connect", {"prospect_name": "Ada"}),
        ("manual", "email_sent", {"subject": "Hello"}),
    ]
    for source, etype, meta in samples:
        rule = db.get_gamification_rule(etype)
        if not rule:
            print(f"Skipping {etype}: no rule")
            continue
        eid = db.insert_event(
            source,
            etype,
            int(rule["gold_value"]),
            int(rule["xp_value"]),
            meta,
        )
        print(f"Inserted {etype} -> {eid}")
    print("Done.")


def seed_via_api(count: int) -> None:
    secret = os.getenv("WEBHOOK_SECRET")
    if not secret:
        print("WEBHOOK_SECRET missing in environment.")
        sys.exit(1)

    base = _api_base()
    url = f"{base}/api/v1/webhook/ingest"

    print(f"Posting {count} events to {url}")
    ok = 0
    for i in range(count):
        payload = generate_event()
        r = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json", "X-RIFT-SECRET": secret},
            timeout=10,
        )
        if r.status_code == 201:
            ok += 1
            print(f"  [{i+1}/{count}] {payload['event_type']} OK")
        else:
            print(f"  [{i+1}/{count}] FAILED {r.status_code} {r.text}")

    print(f"Completed: {ok}/{count} accepted")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--direct",
        action="store_true",
        help="Insert sample rows via DATABASE_URL (API not required)",
    )
    p.add_argument(
        "-n",
        "--count",
        type=int,
        default=int(os.getenv("SEED_COUNT", "15")),
        help="Webhook mode only: number of events (default SEED_COUNT or 15)",
    )
    args = p.parse_args()

    if args.direct:
        seed_direct()
    else:
        seed_via_api(args.count)


if __name__ == "__main__":
    main()
