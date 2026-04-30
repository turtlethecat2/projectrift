# app/CLAUDE.md

Streamlit HUD frontend - League of Legends-themed overlay displaying real-time stats.

## Structure

```
main_hud.py       → Main app, polling loop, sound effects, session state
styles.css        → LoL-themed CSS (dark blue, gold accents)
components/
  gold_counter.py → Gold display with animation
  xp_bar.py       → XP progress bar, level badge, rank badge
  kda_display.py  → Stats display (calls, meetings, events)
assets/
  sounds/         → Sound effects (gold_earned.mp3, level_up.mp3, etc.)
```

## Key Patterns

**Polling:** `main_hud.py` polls the database every 5 seconds via `DatabaseQueries.get_current_stats()`, then calls `st.rerun()`.

**Session State:** Tracks previous stats to detect changes (level ups, rank ups, gold earned) and trigger sounds/animations.

**Sound Effects:** Uses pygame mixer. Sounds play on:
- Gold earned (`gold_gen.mp3`)
- Level up (`level_up.mp3`)
- Rank up (`level_up.mp3`)
- Meeting booked (`level_up.mp3`)

**CSS Variables** (in `styles.css`):
```css
--lol-dark-blue: #010a13
--lol-gold: #785a28
--lol-gold-bright: #c8aa6e
--lol-cream: #f0e6d2
```

## Adding a Component

1. Create file in `components/`
2. Export a `render_*` function that uses `st.markdown()` with `unsafe_allow_html=True`
3. Import and call in `main_hud.py`

## Running

```bash
PYTHONPATH=. streamlit run app/main_hud.py
```

## Configuration (via .env)

- `HUD_REFRESH_INTERVAL` - Polling interval in seconds (default: 5)
- `SOUND_VOLUME` - Volume 0.0-1.0 (default: 0.7)

## Docs

- Streamlit: https://docs.streamlit.io/
- Pygame: https://www.pygame.org/docs/
