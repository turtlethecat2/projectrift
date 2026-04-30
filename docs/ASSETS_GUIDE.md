# 🎨 Visual Assets Guide for Project Rift

This guide helps you add League of Legends-style visual and audio assets to your HUD.

## 📂 Where Assets Go

```
app/assets/
├── images/
│   ├── gold_icon.png          # Gold coin icon (64x64px recommended)
│   ├── avatar.png             # Your avatar/profile pic (80x80px)
│   └── level_badge.png        # Level badge background (optional)
└── sounds/
    ├── level_up.mp3           # Plays when you level up (~2 seconds)
    ├── gold_earned.mp3        # Plays when gold increases (~0.5 seconds)
    └── meeting_booked.mp3     # Plays when meeting booked (~1.5 seconds)
```

## 🎮 Getting League of Legends Assets

### Option 1: Community Dragon (Official LoL Assets)

**Best for authentic LoL look!**

Base URL: `https://raw.communitydragon.org/latest/`

**Recommended assets:**

1. **Gold Icon:**
   ```
   /plugins/rcp-fe-lol-static-assets/global/default/images/currency_icon.png
   ```
   Save as: `app/assets/images/gold_icon.png`

2. **Level Borders/Frames:**
   ```
   /plugins/rcp-fe-lol-uikit/global/default/level-{number}.png
   ```
   Example: level-1.png, level-2.png, etc.

3. **Rank Emblems:**
   ```
   /plugins/rcp-fe-lol-static-assets/global/default/ranked-emblems/emblem-{rank}.png
   ```
   Example: emblem-gold.png, emblem-platinum.png

**How to download:**
```bash
# Gold icon
curl -o "app/assets/images/gold_icon.png" \
  "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/currency_icon.png"

# Champion icon (for avatar)
curl -o "app/assets/images/avatar.png" \
  "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/1.png"
```

### Option 2: Free Alternative Assets

**For legally safer portfolio use:**

#### Images

1. **Game-Icons.net** (CC BY 3.0 - Free with attribution)
   - Link: https://game-icons.net/
   - Search terms:
     - "gold bar" → gold_icon.png
     - "rank 3" → level_badge.png
     - "player" → avatar.png
   - Download as SVG, convert to PNG
   - Recommended size: 64x64px or 128x128px

2. **Flaticon** (Free tier with attribution)
   - Link: https://www.flaticon.com/
   - Search: "game gold coin"
   - Filter: Free
   - Pick gold/yellow colored icons

3. **Figma Community Templates**
   - Link: https://www.figma.com/community
   - Search: "game UI kit" or "RPG interface"
   - Many free game UI elements
   - Export as PNG

#### Sounds

1. **Freesound.org** (Best for game sounds)
   - Link: https://freesound.org/

   **Specific recommendations:**

   **Level Up Sound:**
   - Search: "level up game"
   - Filter: CC0 (Public Domain)
   - Recommended: Short fanfare (1-2 seconds)
   - Example search: https://freesound.org/search/?q=level+up&f=tag:game

   **Gold Earned Sound:**
   - Search: "coin collect game"
   - Filter: CC0
   - Recommended: Quick "bling" sound (~0.5 seconds)
   - Example search: https://freesound.org/search/?q=coin&f=tag:game

   **Meeting Booked Sound:**
   - Search: "achievement unlock"
   - Filter: CC0
   - Recommended: Triumphant sound (1-2 seconds)
   - Example search: https://freesound.org/search/?q=achievement&f=tag:game

2. **Zapsplat** (Free tier available)
   - Link: https://www.zapsplat.com/
   - Categories: Game Sounds > Achievements
   - Free account required

3. **Pixabay Sound Effects**
   - Link: https://pixabay.com/sound-effects/
   - Search: "game coin", "achievement"
   - All CC0 (no attribution needed)

## 🎨 LoL Color Palette (Already in styles.css)

```css
Dark Blue:    #010a13  /* Background */
Dark Gray:    #1e2328  /* UI elements */
Gold:         #785a28  /* Borders, accents */
Gold Bright:  #c8aa6e  /* Text highlights */
Cream:        #f0e6d2  /* Primary text */
Blue Glow:    #0acbe6  /* Stats, highlights */
```

## 🔧 Using Your Own Images

If you want to use your own images, here are the recommended specs:

| Asset | Size | Format | Notes |
|-------|------|--------|-------|
| gold_icon.png | 64x64px | PNG | Transparent background preferred |
| avatar.png | 80x80px | PNG | Will be displayed in circle |
| level_badge.png | 100x30px | PNG | Optional overlay for level |

**Edit images with:**
- **GIMP** (free, powerful) - https://www.gimp.org/
- **Photopea** (browser-based, free) - https://www.photopea.com/
- **Canva** (easy templates) - https://www.canva.com/

## 🎵 Sound File Specs

| Sound | Duration | Format | Volume |
|-------|----------|--------|--------|
| level_up.mp3 | 1-2 sec | MP3 | Loud/triumphant |
| gold_earned.mp3 | 0.3-0.5 sec | MP3 | Medium/pleasant |
| meeting_booked.mp3 | 1-1.5 sec | MP3 | Loud/exciting |

**Convert audio files:**
```bash
# If you have .wav or .ogg files, convert to MP3:
ffmpeg -i sound.wav -codec:a libmp3lame -b:a 128k sound.mp3
```

Or use online converters:
- https://cloudconvert.com/
- https://convertio.co/

## 🚀 Quick Test

After adding assets, test them:

```bash
# Run the asset setup script
python scripts/download_sample_assets.py

# Start the HUD
streamlit run app/main_hud.py

# Send a test webhook to trigger sounds
make webhook-test
```

## 💡 Pro Tips

1. **High DPI Displays:** Use 2x resolution images (128x128 for 64x64 display)
2. **Transparent Backgrounds:** PNGs with transparency look best
3. **Sound Volume:** Adjust in `.env` file with `SOUND_VOLUME=0.7`
4. **Disable Sounds:** Set `SOUND_VOLUME=0` or toggle in HUD settings

## 📜 Legal & Attribution

**If using Community Dragon assets:**
- ✅ Fine for portfolio/personal use
- ✅ Show to potential employers
- ❌ Don't redistribute or sell
- ⚠️ Add note: "League of Legends assets © Riot Games"

**If using free asset sites:**
- ✅ Check license (CC0, CC BY, etc.)
- ✅ Provide attribution if required
- ✅ Keep attribution file in `app/assets/CREDITS.txt`

## 🎬 Example Credits File

Create `app/assets/CREDITS.txt`:

```
Project Rift Asset Credits
===========================

Images:
- Gold Icon: Game-Icons.net (CC BY 3.0) by Delapouite
- Avatar: Custom created with Canva

Sounds:
- Level Up: Freesound.org (CC0) by user123
- Gold Earned: Freesound.org (CC0) by soundguy
- Meeting Booked: Pixabay (CC0)

League of Legends is a trademark of Riot Games, Inc.
This project is not affiliated with or endorsed by Riot Games.
```

## 🔗 Quick Links

- **Community Dragon:** https://www.communitydragon.org/
- **Game Icons:** https://game-icons.net/
- **Free Sounds:** https://freesound.org/
- **Flaticon:** https://www.flaticon.com/
- **Figma Community:** https://www.figma.com/community

---

Need help? Check the main README.md or open an issue!
