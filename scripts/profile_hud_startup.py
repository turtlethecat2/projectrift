#!/usr/bin/env python3
"""
Profile HUD Startup Performance

Reusable profiling utility to identify performance bottlenecks in the Streamlit HUD.
Run this script whenever investigating slow startup times.

Usage:
    python scripts/profile_hud_startup.py

Output:
    - Timing breakdown for each component (pygame, CSS, DB, images, sounds)
    - Ranked list of slowest operations
    - Recommendations based on measured times
"""

import time
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def time_operation(name: str, func):
    """Time an operation and return result with elapsed time in ms"""
    start = time.perf_counter()
    try:
        result = func()
        elapsed = (time.perf_counter() - start) * 1000
        return result, elapsed, None
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return None, elapsed, str(e)


def profile_pygame_mixer():
    """Profile pygame mixer initialization"""
    import pygame
    pygame.mixer.init()


def profile_css_load():
    """Profile CSS file loading"""
    css_path = PROJECT_ROOT / "app" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            return f.read()
    return ""


def profile_font_check():
    """Profile font file access"""
    fonts_dir = PROJECT_ROOT / "app" / "assets" / "fonts"
    if fonts_dir.exists():
        fonts = list(fonts_dir.glob("*.ttf"))
        return [f.stat().st_size for f in fonts]
    return []


def profile_db_query():
    """Profile database connection and get_current_stats query"""
    from database.queries import DatabaseQueries
    db = DatabaseQueries()
    return db.get_current_stats()


def profile_rank_images():
    """Profile rank image loading"""
    images_dir = PROJECT_ROOT / "app" / "assets" / "images" / "ranks"
    loaded = []
    if images_dir.exists():
        for img in images_dir.glob("*.png"):
            with open(img, 'rb') as f:
                loaded.append(len(f.read()))
    return loaded


def profile_sound_files():
    """Profile sound file loading via pygame"""
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    sounds_dir = PROJECT_ROOT / "app" / "assets" / "sounds"
    loaded = []
    if sounds_dir.exists():
        for sound_file in sounds_dir.glob("*.mp3"):
            sound = pygame.mixer.Sound(str(sound_file))
            loaded.append(sound)
    return loaded


def profile_dotenv():
    """Profile dotenv loading"""
    from dotenv import load_dotenv
    load_dotenv()


def main():
    print("=" * 60)
    print("HUD STARTUP PROFILER")
    print("=" * 60)
    print()

    timings = {}
    errors = {}

    # Run all profilers
    operations = [
        ("pygame.mixer.init()", profile_pygame_mixer),
        ("CSS file load", profile_css_load),
        ("Font files check", profile_font_check),
        ("DatabaseQueries.get_current_stats()", profile_db_query),
        ("Rank images load (all 10)", profile_rank_images),
        ("Sound files load (all)", profile_sound_files),
        ("dotenv load", profile_dotenv),
    ]

    for name, func in operations:
        _, elapsed, error = time_operation(name, func)
        timings[name] = elapsed
        if error:
            errors[name] = error
            print(f"  {name}: {elapsed:.2f}ms [FAILED: {error}]")
        else:
            print(f"  {name}: {elapsed:.2f}ms")

    # Summary
    print()
    print("=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)

    total = sum(timings.values())
    print(f"\nTotal measured time: {total:.2f}ms")
    print()

    # Sort by time descending
    sorted_timings = sorted(timings.items(), key=lambda x: x[1], reverse=True)
    print("Ranked by time (slowest first):")
    for i, (name, ms) in enumerate(sorted_timings, 1):
        pct = (ms / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 5)
        status = " [ERROR]" if name in errors else ""
        print(f"  {i}. {name}: {ms:.2f}ms ({pct:.1f}%) {bar}{status}")

    # Recommendations
    print()
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print()

    recommendations = []

    if timings.get("pygame.mixer.init()", 0) > 100:
        recommendations.append(
            "- pygame.mixer.init() is slow ({:.0f}ms) - use @st.cache_resource".format(
                timings["pygame.mixer.init()"]
            )
        )

    if timings.get("DatabaseQueries.get_current_stats()", 0) > 50:
        recommendations.append(
            "- DB query is slow ({:.0f}ms) - consider @st.cache_data with TTL".format(
                timings["DatabaseQueries.get_current_stats()"]
            )
        )

    if timings.get("Rank images load (all 10)", 0) > 20:
        recommendations.append(
            "- Rank images loading is slow ({:.0f}ms) - cache in session_state".format(
                timings["Rank images load (all 10)"]
            )
        )

    if timings.get("Sound files load (all)", 0) > 50:
        recommendations.append(
            "- Sound files are loaded eagerly ({:.0f}ms) - lazy load on first use".format(
                timings["Sound files load (all)"]
            )
        )

    if recommendations:
        for rec in recommendations:
            print(rec)
    else:
        print("No significant bottlenecks detected in measured operations.")

    print()
    print("Note: This measures Python-level startup. Streamlit framework")
    print("overhead and browser rendering are not included. For full analysis,")
    print("use browser DevTools Network/Performance tabs.")
    print()

    return timings


if __name__ == "__main__":
    main()
