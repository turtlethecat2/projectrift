#!/usr/bin/env python3
"""
Sample asset downloader for Project Rift
Downloads free placeholder assets that match the LoL aesthetic
"""

import os
import requests
from pathlib import Path

# Base directories
ASSETS_DIR = Path(__file__).parent.parent / "app" / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"

# Create directories if they don't exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

# Sample assets (using free resources)
SAMPLE_ASSETS = {
    "images": [
        {
            "name": "gold_icon.png",
            "url": "https://raw.githubusercontent.com/game-icons/icons/master/delapouite/originals/svg/gold-bar.svg",
            "description": "Gold coin icon (SVG - convert to PNG)"
        },
    ],
    "sounds": [
        # Note: These are placeholder URLs - you'll need to download from Freesound.org
        {
            "name": "level_up.mp3",
            "url": None,
            "description": "Download from: https://freesound.org/search/?q=level+up&f=tag:game"
        },
        {
            "name": "gold_earned.mp3",
            "url": None,
            "description": "Download from: https://freesound.org/search/?q=coin&f=tag:game"
        },
        {
            "name": "meeting_booked.mp3",
            "url": None,
            "description": "Download from: https://freesound.org/search/?q=achievement&f=tag:game"
        }
    ]
}

def download_file(url, destination):
    """Download a file from URL to destination"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading: {e}")
        return False

def main():
    print("="*60)
    print("Project Rift - Asset Setup Guide")
    print("="*60)
    print("\nThis script helps you set up visual and audio assets.\n")

    print("📁 Asset Directories:")
    print(f"   Images: {IMAGES_DIR}")
    print(f"   Sounds: {SOUNDS_DIR}")
    print()

    print("🎨 RECOMMENDED ASSET SOURCES:\n")

    print("1. IMAGES (Gold Icon, Badges, etc.)")
    print("   " + "-"*55)
    print("   • Game-Icons.net - Free gaming icons")
    print("     https://game-icons.net/")
    print("     Search: 'gold', 'level', 'rank'")
    print()
    print("   • Flaticon.com - Icon packs")
    print("     https://flaticon.com/")
    print("     Search: 'game badge', 'gold coin'")
    print()
    print("   • Community Dragon (Official LoL assets)")
    print("     https://raw.communitydragon.org/latest/")
    print("     Browse: plugins/rcp-fe-lol-static-assets/")
    print()

    print("2. SOUNDS (Level Up, Coins, Achievements)")
    print("   " + "-"*55)
    print("   • Freesound.org - Free sound effects (CC0)")
    print("     https://freesound.org/")
    print("     Searches:")
    print("       - 'coin game' for gold_earned.mp3")
    print("       - 'level up game' for level_up.mp3")
    print("       - 'achievement fanfare' for meeting_booked.mp3")
    print()
    print("   • Zapsplat.com - Game sounds (free tier)")
    print("     https://zapsplat.com/")
    print()
    print("   • Pixabay - Royalty-free sounds")
    print("     https://pixabay.com/sound-effects/search/game/")
    print()

    print("3. LEAGUE OF LEGENDS STYLE GUIDE")
    print("   " + "-"*55)
    print("   Colors (already in styles.css):")
    print("     • Dark Blue: #010a13")
    print("     • Gold: #785a28")
    print("     • Gold Bright: #c8aa6e")
    print("     • Cream: #f0e6d2")
    print()
    print("   Fonts:")
    print("     • Primary: Beaufort (LoL official font)")
    print("     • Download: https://na.leagueoflegends.com/en-us/news/dev/")
    print()

    print("="*60)
    print("QUICK START:")
    print("="*60)
    print()
    print("Step 1: Download Assets")
    print("   Visit the sites above and download:")
    print("   - 1 gold coin icon (save as gold_icon.png)")
    print("   - 1 avatar/profile image (save as avatar.png)")
    print("   - 3 sound effects (save as .mp3 files)")
    print()
    print("Step 2: Place Files")
    print(f"   Images → {IMAGES_DIR}")
    print(f"   Sounds → {SOUNDS_DIR}")
    print()
    print("Step 3: Test")
    print("   Run: streamlit run app/main_hud.py")
    print("   The HUD should show your assets!")
    print()
    print("="*60)

    # Check current assets
    print("\n📊 CURRENT ASSETS STATUS:\n")

    print("Images:")
    image_files = ["gold_icon.png", "avatar.png", "level_badge.png"]
    for img in image_files:
        exists = (IMAGES_DIR / img).exists()
        status = "✅ Found" if exists else "❌ Missing"
        print(f"   {status}: {img}")

    print("\nSounds:")
    sound_files = ["level_up.mp3", "gold_earned.mp3", "meeting_booked.mp3"]
    for sound in sound_files:
        exists = (SOUNDS_DIR / sound).exists()
        status = "✅ Found" if exists else "❌ Missing"
        print(f"   {status}: {sound}")

    print("\n" + "="*60)
    print("TIP: For a quick test, you can use emoji placeholders")
    print("     The HUD will work without assets, just less fancy!")
    print("="*60)

if __name__ == "__main__":
    main()
