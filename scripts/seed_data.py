#!/usr/bin/env python3
"""
Seed test data for Project Rift
Generates realistic webhook events for testing and development
"""

import os
import random
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from faker import Faker

load_dotenv()

# Configuration
API_URL = f"http://{os.getenv('API_HOST', 'localhost')}:{os.getenv('API_PORT', 8000)}"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_ENDPOINT = f"{API_URL}/api/v1/webhook/ingest"

# Initialize Faker for realistic data
fake = Faker()

# Event types with probabilities (realistic SDR distribution)
EVENT_TYPES = [
    ("call_dial", 0.50),  # 50% of events are dials
    ("call_connect", 0.20),  # 20% are connects
    ("email_sent", 0.25),  # 25% are emails
    ("meeting_booked", 0.04),  # 4% are meetings booked
    ("meeting_attended", 0.01),  # 1% are meetings attended
]

# Sources
SOURCES = ["nooks", "outreach", "manual", "zapier"]


def generate_event():
    """
    Generate a realistic event payload

    Returns:
        Dictionary with event data
    """
    # Select event type based on weighted probabilities
    event_type = random.choices(
        [e[0] for e in EVENT_TYPES], weights=[e[1] for e in EVENT_TYPES]
    )[0]

    # Generate metadata based on event type
    metadata = {
        "prospect_name": fake.name(),
        "company": fake.company(),
    }

    if event_type in ["call_dial", "call_connect"]:
        metadata["phone_number"] = fake.phone_number()
        if event_type == "call_connect":
            metadata["call_duration"] = random.randint(30, 600)
            metadata["disposition"] = random.choice(
                ["interested", "not_interested", "callback", "left_voicemail"]
            )

    if event_type in ["meeting_booked", "meeting_attended"]:
        future_date = datetime.now() + timedelta(days=random.randint(1, 14))
        metadata["meeting_time"] = future_date.isoformat()
        metadata["meeting_type"] = random.choice(["discovery", "demo", "followup"])

    if event_type == "email_sent":
        metadata["email"] = fake.email()
        metadata["subject"] = fake.sentence(nb_words=6)

    return {
        "source": random.choice(SOURCES),
        "event_type": event_type,
        "metadata": metadata,
    }


def send_event(event):
    """
    Send event to the webhook endpoint

    Args:
        event: Event payload dictionary

    Returns:
        Response object from the API
    """
    headers = {"Content-Type": "application/json", "X-RIFT-SECRET": WEBHOOK_SECRET}

    try:
        response = requests.post(
            WEBHOOK_ENDPOINT, json=event, headers=headers, timeout=5
        )
        return response
    except Exception as e:
        print(f"Error sending event: {e}")
        return None


def seed_historical_data(days=7, events_per_day=30):
    """
    Generate historical data for the past N days

    Args:
        days: Number of days to generate data for
        events_per_day: Average number of events per day
    """
    print(f"Generating historical data for {days} days...")
    total_events = 0
    successful = 0

    for day in range(days):
        # Vary events per day slightly
        num_events = random.randint(
            int(events_per_day * 0.7), int(events_per_day * 1.3)
        )

        print(f"\nDay {day + 1}/{days}: Generating {num_events} events...")

        for i in range(num_events):
            event = generate_event()
            response = send_event(event)

            total_events += 1

            if response and response.status_code == 201:
                successful += 1
                result = response.json()
                print(
                    f"  ✓ Event {i+1}: {event['event_type']} | "
                    f"Gold: {result.get('gold_earned')} | "
                    f"XP: {result.get('xp_earned')}"
                )
            else:
                status = response.status_code if response else "ERROR"
                print(f"  ✗ Event {i+1} failed: {status}")

    print(f"\n{'='*60}")
    print(f"Seeding complete!")
    print(f"Total events sent: {total_events}")
    print(f"Successful: {successful}")
    print(f"Failed: {total_events - successful}")
    print(f"{'='*60}")


def seed_current_session(num_events=10):
    """
    Generate events for the current session (testing real-time updates)

    Args:
        num_events: Number of events to generate
    """
    print(f"\nGenerating {num_events} events for current session...")
    successful = 0

    for i in range(num_events):
        event = generate_event()
        response = send_event(event)

        if response and response.status_code == 201:
            successful += 1
            result = response.json()
            print(
                f"  ✓ Event {i+1}: {event['event_type']} | "
                f"Gold: {result.get('gold_earned')} | "
                f"XP: {result.get('xp_earned')}"
            )
        else:
            status = response.status_code if response else "ERROR"
            print(f"  ✗ Event {i+1} failed: {status}")

    print(f"\n✅ Generated {successful}/{num_events} events successfully")


def main():
    """Main function"""
    print("=" * 60)
    print("Project Rift - Data Seeding Script")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Webhook Endpoint: {WEBHOOK_ENDPOINT}")
    print(f"Webhook Secret: {'✓ Set' if WEBHOOK_SECRET else '✗ Not Set'}")
    print("=" * 60)

    if not WEBHOOK_SECRET:
        print("\n❌ ERROR: WEBHOOK_SECRET not set in environment variables!")
        print("Please set it in your .env file.")
        return

    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Seed historical data (7 days, ~30 events/day)")
    print("2. Seed current session (10 events)")
    print("3. Custom seed (specify parameters)")
    print("4. Exit")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1":
        seed_historical_data(days=7, events_per_day=30)
    elif choice == "2":
        seed_current_session(num_events=10)
    elif choice == "3":
        days = int(input("Number of days: "))
        events_per_day = int(input("Events per day: "))
        seed_historical_data(days=days, events_per_day=events_per_day)
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid choice. Exiting...")


if __name__ == "__main__":
    main()
