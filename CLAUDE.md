# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Static web application for MLS NEXT youth soccer scouting. Displays club locations on an interactive map, team rosters with stats, scout watchlists, and AI-powered MLS rules search. No build process - all vanilla HTML/CSS/JS.

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Leaflet.js map with club markers, filtering, "Add Club" feature |
| `team.html` | Team rosters by age group (U13-U19), player stats tables |
| `scouts.html` | Scout database, player watchlists, scouting reports, player comparison |
| `rules.html` | MLS NEXT rules viewer with AI Q&A (requires rules_server.py) |
| `playersData.js` | Embedded player statistics loaded by team.html |

## Running Locally

```bash
# Static pages (map, team rosters) - just open in browser
open index.html

# Rules page with AI search - requires Python server
python3 rules_server.py
# Then open http://localhost:8080/rules.html

# Add Club server (for geocoding/file updates)
python3 server.py
# or
python3 add_club_server.py
```

## Data Storage

**Embedded in HTML/JS (permanent):**
- `index.html`: `clubs` array with coordinates, logos, divisions
- `team.html`: `clubsData` (metadata) and `playersData` (player stats)
- `playersData.js`: Alternative player data source

**localStorage (browser-only, not permanent):**
- `scouts` - Scout profiles
- `scoutPlayers` - Players in watchlists
- `scoutReports` - Scouting reports with ratings
- `customClubs` - Clubs added via "Add Club" button
- `compareCart` - Global player comparison cart (shared between scouts.html and team.html)
- `clubData_{id}` - Director edits for clubs

## Authentication

Password `NYRBScout@26` unlocks:
- Editing player data in team.html
- Admin mode in scouts.html (delete any report)

## Architecture Notes

**scouts.html features:**
- Scout CRUD with localStorage persistence
- Player watchlist per scout
- Scouting reports with custom fields (Match, Build, Next Action, Priority)
- Video links per player
- Share players between scouts
- Global compare cart (syncs with team.html via localStorage)

**team.html features:**
- Age group tabs (U13-U19)
- Filterable/sortable player tables
- Date range filtering for goals
- "Add to Watchlist" button links to scouts.html
- Global compare cart button

**index.html features:**
- Leaflet.js map centered on NYRB (40.82, -74.4)
- Club markers with custom icons (logos or initials)
- Sidebar with search, division/distance filters
- "Add Club" with geocoding, CSV validation, logo upload
- Drive distance calculation from NYRB HQ

**rules.html + rules_server.py:**
- Loads 4 MLS NEXT documents as semantic HTML
- AI search via Claude API (ANTHROPIC_API_KEY from ../.env)
- Returns answers with page references

## Club ID System

Two naming conventions must stay in sync:
1. **Map IDs** (URLs): `team.html?club=dusc`
2. **Folder names** (scraping): `downtown_united_soccer_club/`

Mappings in parent directory: `scraper3.py` and `import_to_scouting.py`

## Deployment

This is a separate git repo deployed to Vercel:
```bash
git add . && git commit -m "message" && git push
vercel --prod  # if needed
```

Live URLs:
- https://scouting-map.vercel.app/index.html
- https://scouting-map.vercel.app/team.html?club=CLUB_ID

## Supabase Integration

Player data loads from Supabase first, falls back to embedded data:
- API key in `SUPABASE_ANON_KEY` constant (index.html, team.html)
- Tables: `clubs`, `squad_data`, `club_directors`
- Upload via `import_to_scouting.py --upload-db` (parent directory)
