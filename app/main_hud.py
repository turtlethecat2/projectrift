"""
Project Rift - Main HUD Application
League of Legends inspired overlay for SDR gamification
"""

import os
import time
import streamlit as st
import pygame
from pathlib import Path
from dotenv import load_dotenv

from database.queries import DatabaseQueries
from app.components.gold_counter import render_gold_counter
from app.components.xp_bar import render_xp_bar, render_level_badge, render_rank_badge
from app.components.kda_display import render_kda_display, render_event_counts

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Project Rift - HUD",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# Configuration
REFRESH_INTERVAL = int(os.getenv('HUD_REFRESH_INTERVAL', 5))
SOUND_VOLUME = float(os.getenv('SOUND_VOLUME', 0.7))
SOUND_ENABLED = True  # Can be toggled in UI


# Sound helper functions
def play_sound(sound_file: str):
    """
    Play a sound effect

    Args:
        sound_file: Name of the sound file in assets/sounds/
    """
    if not SOUND_ENABLED:
        return

    try:
        sound_path = Path(__file__).parent / "assets" / "sounds" / sound_file
        if sound_path.exists():
            sound = pygame.mixer.Sound(str(sound_path))
            sound.set_volume(SOUND_VOLUME)
            sound.play()
    except Exception as e:
        st.error(f"Failed to play sound: {e}")


def check_for_level_up(current_level: int, previous_level: int):
    """Check if player leveled up and play sound"""
    if current_level > previous_level:
        play_sound("level_up.mp3")
        return True
    return False


def check_for_gold_earned(current_gold: int, previous_gold: int):
    """Check if gold was earned and play sound"""
    if current_gold > previous_gold:
        play_sound("gold_earned.mp3")
        return True
    return False


def check_for_meeting_booked(current_meetings: int, previous_meetings: int):
    """Check if a meeting was booked and play sound"""
    if current_meetings > previous_meetings:
        play_sound("meeting_booked.mp3")
        return True
    return False


def check_for_rank_up(current_rank: str, previous_rank: str):
    """Check if player ranked up and play sound"""
    rank_order = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum',
                  'Emerald', 'Diamond', 'Master', 'Grandmaster', 'Challenger']

    if current_rank != previous_rank:
        curr_idx = rank_order.index(current_rank) if current_rank in rank_order else -1
        prev_idx = rank_order.index(previous_rank) if previous_rank in rank_order else -1

        if curr_idx > prev_idx:
            play_sound("level_up.mp3")  # Reuse level_up sound for rank up
            return True
    return False


# Initialize session state
if 'previous_stats' not in st.session_state:
    st.session_state.previous_stats = {
        'total_gold': 0,
        'total_xp': 0,
        'current_level': 1,
        'meetings_booked': 0,
        'rank': 'Iron'
    }

if 'level_up_animation' not in st.session_state:
    st.session_state.level_up_animation = False


# Main application
def main():
    """Main HUD application"""

    # Title (can be hidden in production)
    st.title("⚔️ Project Rift - SDR HUD")

    # Database connection
    try:
        db = DatabaseQueries()
        stats = db.get_current_stats()
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.info("Please ensure the database is running and DATABASE_URL is set correctly.")
        return

    # Extract stats
    total_gold = stats.get('total_gold', 0)
    total_xp = stats.get('total_xp', 0)
    current_level = stats.get('current_level', 1)
    xp_in_current_level = stats.get('xp_in_current_level', 0)
    xp_to_next_level = stats.get('xp_to_next_level', 1000)
    rank = stats.get('rank', 'Iron')
    calls_made = stats.get('calls_made', 0)
    calls_connected = stats.get('calls_connected', 0)
    meetings_booked = stats.get('meetings_booked', 0)
    events_today = stats.get('events_today', 0)

    # Check for events and play sounds
    prev_stats = st.session_state.previous_stats

    # Check for level up
    if check_for_level_up(current_level, prev_stats['current_level']):
        st.session_state.level_up_animation = True
        st.balloons()  # Streamlit celebration

    # Check for rank up
    if check_for_rank_up(rank, prev_stats['rank']):
        st.balloons()  # Streamlit celebration for rank up

    # Check for gold earned
    check_for_gold_earned(total_gold, prev_stats['total_gold'])

    # Check for meeting booked
    check_for_meeting_booked(meetings_booked, prev_stats['meetings_booked'])

    # Update previous stats
    st.session_state.previous_stats = {
        'total_gold': total_gold,
        'total_xp': total_xp,
        'current_level': current_level,
        'meetings_booked': meetings_booked,
        'rank': rank
    }

    # Layout using columns
    col1, col2, col3 = st.columns([1, 3, 2])

    # Left column - Avatar and Level
    with col1:
        # Avatar placeholder (can be replaced with actual image)
        st.markdown(
            """
            <div class="avatar-container">
                <div style="width: 80px; height: 80px; border-radius: 50%;
                     background: linear-gradient(135deg, #785a28 0%, #c8aa6e 100%);
                     border: 3px solid #c8aa6e; display: flex; align-items: center;
                     justify-content: center; font-size: 36px;">
                    ⚔️
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        render_level_badge(current_level)
        st.markdown("<br>", unsafe_allow_html=True)
        render_rank_badge(rank)

    # Center column - Gold and XP
    with col2:
        render_gold_counter(total_gold)
        st.markdown("<br>", unsafe_allow_html=True)
        render_xp_bar(xp_in_current_level, xp_to_next_level, current_level)

    # Right column - KDA Stats
    with col3:
        render_kda_display(calls_made, calls_connected, meetings_booked)

    # Full width - Event counts
    st.markdown("<br>", unsafe_allow_html=True)
    render_event_counts(stats)

    # Debug/Info section (collapsible)
    with st.expander("📊 Detailed Stats"):
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric("Total Events", stats.get('total_events', 0))
            st.metric("Events Today", events_today)

        with col_b:
            st.metric("Total Gold", f"{total_gold:,}")
            st.metric("Total XP", f"{total_xp:,}")

        with col_c:
            st.metric("Current Level", current_level)
            st.metric("Current Rank", rank)

    # Settings section (collapsible)
    with st.expander("⚙️ Settings"):
        sound_enabled = st.checkbox("Enable Sound Effects", value=SOUND_ENABLED)
        if sound_enabled != SOUND_ENABLED:
            globals()['SOUND_ENABLED'] = sound_enabled

        refresh_rate = st.slider(
            "Refresh Rate (seconds)",
            min_value=1,
            max_value=30,
            value=REFRESH_INTERVAL
        )

        if st.button("Test Sound - Gold Earned"):
            play_sound("gold_earned.mp3")

        if st.button("Test Sound - Level Up"):
            play_sound("level_up.mp3")

        if st.button("Test Sound - Meeting Booked"):
            play_sound("meeting_booked.mp3")

    # Footer
    st.markdown("---")
    st.caption(
        f"Project Rift v1.0 | Refreshing every {REFRESH_INTERVAL}s | "
        f"Database: Connected ✅"
    )

    # Auto-refresh
    time.sleep(REFRESH_INTERVAL)
    st.rerun()


if __name__ == "__main__":
    main()
