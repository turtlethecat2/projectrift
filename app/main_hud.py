"""Streamlit HUD — polls DATABASE_URL for weekly stats."""

import os
import time
from pathlib import Path

import pygame
import streamlit as st
from dotenv import load_dotenv

from app.components.avatar import render_avatar
from app.components.gold_counter import render_gold_counter
from app.components.kda_display import render_event_counts, render_kda_display
from app.components.xp_bar import (
    render_level_badge,
    render_rank_badge,
    render_xp_bar,
)
from database.queries import DatabaseQueries

load_dotenv()

RANK_ORDER = (
    "Iron",
    "Bronze",
    "Silver",
    "Gold",
    "Platinum",
    "Emerald",
    "Diamond",
    "Master",
    "Grandmaster",
    "Challenger",
)


def _rank_index(name: str) -> int:
    try:
        return RANK_ORDER.index(name)
    except ValueError:
        return -1


st.set_page_config(
    page_title="Project Rift - HUD",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def load_css() -> str:
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


@st.cache_resource
def init_pygame_mixer() -> bool:
    pygame.mixer.init()
    return True


@st.cache_resource
def get_db_connection():
    return DatabaseQueries()


@st.cache_data(ttl=60)
def get_cached_stats(_db: DatabaseQueries):
    return _db.get_current_stats()


css_content = load_css()
if css_content:
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

init_pygame_mixer()

REFRESH_INTERVAL = int(os.getenv("HUD_REFRESH_INTERVAL", "5"))
SOUND_VOLUME = float(os.getenv("SOUND_VOLUME", "0.7"))

if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = True


def get_sound(sound_file: str):
    if "sound_cache" not in st.session_state:
        st.session_state.sound_cache = {}

    if sound_file not in st.session_state.sound_cache:
        sound_path = Path(__file__).parent / "assets" / "sounds" / sound_file
        if sound_path.exists():
            sound = pygame.mixer.Sound(str(sound_path))
            sound.set_volume(SOUND_VOLUME)
            st.session_state.sound_cache[sound_file] = sound
        else:
            st.session_state.sound_cache[sound_file] = None

    return st.session_state.sound_cache.get(sound_file)


def play_sound(sound_file: str) -> None:
    if not st.session_state.sound_enabled:
        return
    try:
        sound = get_sound(sound_file)
        if sound:
            sound.play()
    except Exception as e:
        st.error(f"Failed to play sound: {e}")


def check_for_level_up(current_level: int, previous_level: int) -> bool:
    if current_level > previous_level:
        play_sound("level_up.mp3")
        return True
    return False


def check_for_gold_earned(current_gold: int, previous_gold: int) -> bool:
    if current_gold > previous_gold:
        play_sound("gold_earned.mp3")
        return True
    return False


def check_for_meeting_booked(current_meetings: int, previous_meetings: int) -> bool:
    if current_meetings > previous_meetings:
        play_sound("meeting_booked.mp3")
        return True
    return False


def rank_up_sound(current_rank: str, previous_rank: str) -> bool:
    if _rank_index(current_rank) > _rank_index(previous_rank):
        play_sound("level_up.mp3")
        return True
    return False


if "previous_stats" not in st.session_state:
    st.session_state.previous_stats = {
        "total_gold": 0,
        "total_xp": 0,
        "current_level": 1,
        "meetings_booked": 0,
        "rank": "Iron",
    }


def main() -> None:
    st.title("⚔️ Project Rift — SDR HUD")

    try:
        db = get_db_connection()
        stats = get_cached_stats(db)
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.info("Ensure PostgreSQL is running and DATABASE_URL is set in `.env`.")
        return

    total_gold = stats.get("total_gold", 0)
    total_xp = stats.get("total_xp", 0)
    current_level = stats.get("current_level", 1)
    xp_in_current_level = stats.get("xp_in_current_level", 0)
    xp_to_next_level = stats.get("xp_to_next_level", 1000)
    rank = stats.get("rank", "Iron")
    calls_made = stats.get("calls_made", 0)
    calls_connected = stats.get("calls_connected", 0)
    meetings_booked = stats.get("meetings_booked", 0)
    events_today = stats.get("events_today", 0)

    prev_stats = st.session_state.previous_stats

    celebrate = check_for_level_up(current_level, prev_stats["current_level"]) or rank_up_sound(
        rank, prev_stats["rank"]
    )
    if celebrate:
        st.balloons()

    check_for_gold_earned(total_gold, prev_stats["total_gold"])
    check_for_meeting_booked(meetings_booked, prev_stats["meetings_booked"])

    st.session_state.previous_stats = {
        "total_gold": total_gold,
        "total_xp": total_xp,
        "current_level": current_level,
        "meetings_booked": meetings_booked,
        "rank": rank,
    }

    col1, col2, col3 = st.columns([1, 3, 2])

    with col1:
        render_avatar()
        st.markdown(" ")
        render_level_badge(current_level)
        st.markdown(" ")
        render_rank_badge(rank)

    with col2:
        render_gold_counter(total_gold)
        st.markdown(" ")
        render_xp_bar(xp_in_current_level, xp_to_next_level, current_level)

    with col3:
        render_kda_display(calls_made, calls_connected, meetings_booked)

    st.markdown(" ")
    render_event_counts(stats)

    with st.expander("📊 Detailed Stats"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Events", stats.get("total_events", 0))
            st.metric("Events Today", events_today)
        with col_b:
            st.metric("Total Gold", f"{total_gold:,}")
            st.metric("Total XP", f"{total_xp:,}")
        with col_c:
            st.metric("Current Level", current_level)
            st.metric("Current Rank", rank)

    with st.expander("⚙️ Settings"):
        st.session_state.sound_enabled = st.checkbox(
            "Enable sound effects",
            value=st.session_state.sound_enabled,
        )
        refresh_rate = st.slider(
            "Refresh interval (seconds)",
            min_value=5,
            max_value=300,
            value=REFRESH_INTERVAL,
        )
        if st.button("Test sound — gold"):
            play_sound("gold_earned.mp3")
        if st.button("Test sound — level up"):
            play_sound("level_up.mp3")
        if st.button("Test sound — meeting"):
            play_sound("meeting_booked.mp3")

    st.markdown("---")
    st.caption(
        f"Project Rift | Refreshing every {refresh_rate}s | DATABASE_URL configured ✅"
    )

    time.sleep(refresh_rate)
    st.rerun()


if __name__ == "__main__":
    main()
