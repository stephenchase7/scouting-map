# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Static web application for MLS NEXT youth soccer scouting. Displays club locations on an interactive map, team rosters with stats, scout watchlists, and AI-powered MLS rules search. No build process - all vanilla HTML/CSS/JS.

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Leaflet.js map with club markers, catchment areas, Add/Delete Club |
| `team.html` | Team rosters by age group (U13-U19), player stats tables |
| `scouts.html` | Scout database, player watchlists, scouting reports, player comparison |
| `rules.html` | MLS NEXT rules viewer with AI Q&A (requires rules_server.py) |

## Running Locally

```bash
# Static pages - use Python HTTP server
cd scouting-map
python3 -m http.server 8001
# Open http://localhost:8001/index.html

# Rules page with AI search - requires separate server
python3 rules_server.py
# Then open http://localhost:8080/rules.html
```

## Data Storage

**Supabase (primary, no fallback):**
- `clubs` table - Club metadata, coordinates, logos (Add/Delete Club uses this)
- `squad_data` table - Player rosters and statistics
- API key in `SUPABASE_ANON_KEY` constant (index.html, team.html, scouts.html)
- All player data loads from Supabase; if unavailable, pages show error state

**Embedded in HTML/JS (static reference data only):**
- `index.html`: `clubs` array for map display, `csvTeamData` for division validation
- `team.html`: `clubsData` (club metadata like logos, directors)

**localStorage (browser-only):**
- `scouts` - Scout profiles
- `scoutPlayers` - Players in watchlists
- `scoutReports` - Scouting reports with ratings
- `compareCart` - Global player comparison cart (shared between scouts.html and team.html)

## Authentication

Password (SHA-256 hashed, not stored in plaintext) unlocks:
- Editing player data in team.html
- Admin mode in scouts.html (delete any report)

## Architecture Notes

**index.html features:**
- Leaflet.js map centered on NYRB HQ (40.8167, -74.4028)
- Club markers with custom icons (logos or initials)
- **Catchment Areas** - 3 scouting zones:
  - Primary: 75-mile radius circle from NYRB
  - Regional: East Coast states (DC, MD, VA, PA, CT, MA, NH, RI, NJ, NY)
  - National: Full US view
  - Open Territory: Highlights MI, NV (no MLS affiliate)
- Division filter dropdown
- Add Club: Saves directly to Supabase (permanent)
- Delete Club: Removes from Supabase via popup button
- Drive distance calculation from NYRB HQ

**team.html features:**
- Age group tabs (U13-U19)
- Filterable/sortable player tables
- Date range filtering for goals
- "Add to Watchlist" button links to scouts.html
- Global compare cart button

**scouts.html features:**
- Scout CRUD with localStorage persistence
- Player watchlist per scout
- Scouting reports with custom fields (Match, Build, Next Action, Priority)
- Video links per player
- Share players between scouts
- Global compare cart (syncs with team.html via localStorage)

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

Git repo deployed to Vercel (auto-deploys on push):
```bash
gh auth switch --user stephenchase7  # if needed
git add . && git commit -m "message" && git push
```

Live URLs:
- https://scouting-map.vercel.app/index.html
- https://scouting-map.vercel.app/team.html?club=CLUB_ID

## Supabase Integration

Data loads from Supabase first, falls back to embedded data:
- Project: `pjorqdzlzgwqpivoibyx.supabase.co`
- Tables: `clubs`, `squad_data`
- Add Club and Delete Club write directly to Supabase
- Upload player data via `import_to_scouting.py --upload-db` (parent directory)

### Multi-Season Support (Planned)

**Schema Changes Required for `squad_data` table:**
```sql
-- Add season column (primary key change)
ALTER TABLE squad_data ADD COLUMN season TEXT DEFAULT '2025-2026';
ALTER TABLE squad_data DROP CONSTRAINT squad_data_pkey;
ALTER TABLE squad_data ADD PRIMARY KEY (club_id, squad, season);

-- Add division column (divisions change per season)
ALTER TABLE squad_data ADD COLUMN division TEXT;
```

**New Table Structure:**
| Column | Type | Description |
|--------|------|-------------|
| club_id | text | Club identifier |
| squad | text | Age group (u13, u14, etc.) |
| season | text | Season identifier (2025-2026, 2026-2027) |
| division | text | Division for this season |
| players | jsonb | Player data including goalsByMatch |
| last_updated | timestamp | When data was last scraped |

**Query Changes:**
```javascript
// Load specific season
const { data } = await supabase
  .from('squad_data')
  .select('*')
  .eq('club_id', clubId)
  .eq('season', '2025-2026');

// Load all seasons for comparison
const { data } = await supabase
  .from('squad_data')
  .select('*')
  .eq('club_id', clubId)
  .order('season', { ascending: false });
```
