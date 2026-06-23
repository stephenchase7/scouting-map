# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Static web application for MLS NEXT and ECNL youth soccer scouting. Displays club locations on an interactive map, team rosters with stats, scout watchlists, and AI-powered MLS rules search. No build process - all vanilla HTML/CSS/JS.

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Leaflet.js map with club markers, catchment areas, Add/Delete Club |
| `team.html` | Team rosters by age group (U13-U19), player stats tables |
| `scouts.html` | Scout database, player watchlists, scouting reports, player comparison |
| `live.html` | Live scouting with pitch tracking, player cards, action counters |
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

## Security

**Row Level Security (RLS):** Enabled on all Supabase tables (June 2026)
- `clubs`, `squad_data` - Public read/write
- `scout_players`, `scout_reports`, `live_sessions` - Public read/write
- Future: Restrict writes to authenticated users when Supabase Auth is added

**XSS Prevention:**
- Use `escapeHtml()` for all user content in innerHTML
- Use `sanitizeString()` for onclick attribute values
- Never concatenate raw user input into HTML

**Sensitive Files:**
- `.env` files must stay in parent directory (not in scouting-map/)
- Never commit API keys, passwords, or service_role keys
- `.gitignore` excludes: `.env`, `*.bak`, `*.backup`

## Architecture Notes

**index.html features:**
- Google Maps centered on NYRB HQ (40.8167, -74.4028)
- Club markers with custom icons (logos or initials)
- **League Toggle Filter** - [All] [MLS NEXT] [ECNL] buttons
  - MLS NEXT = HD (Homegrown Division) + AD (Academy Division)
  - ECNL = Elite Clubs National League
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
- Season selector dropdown (2024-2025, 2025-2026, 2026-2027)
- **Per-Match Stats System:**
  - New columns: A (Assists), KP (Key Passes), A1v1, D1v1, SV (Saves)
  - Player detail modal with "+ Add Match" button
  - Edit/delete buttons on each match stat entry
  - Stats aggregate from `player_match_stats` Supabase table
- **Add Player button** - Manual roster entry for ECNL teams (no Kitman scraping)
- Date range filtering for goals
- "Add to Watchlist" button links to scouts.html
- Global compare cart button

**scouts.html features:**
- Scout CRUD with Supabase persistence
- Player watchlist per scout with inline status dropdown
- Checkbox multi-select with bulk delete/status change
- Clickable player names (opens detail panel)
- Compact video/report indicators (📹/📝 icons)
- Scouting reports with custom fields (Match, Build, Next Action, Priority)
- Video links per player
- Share players between scouts
- Global compare cart (syncs with team.html via localStorage)
- Link to Roster modal (hidden, code preserved for future use)
- Prefill from team.html Scout button (auto-creates player with linked_player_key)

**live.html features:**
- Drag-and-drop player markers onto soccer pitch
- Player cards with:
  - Player info (name, birth year, jersey, club, position, foot)
  - 4 Pillars rating (Technical, Tactical, Physical, Mental - 5 stars each)
  - With Ball actions: Goal, Assist, Personality, Problem Solving, 1v1 Dribble, Ball Carrying, Passing, Shot
  - Against Ball actions: Tackle, Intercept, Block, Press, Recovery, Aerial
  - Corner badge +/- buttons (green positive, red negative) for rating actions
  - Quick tags (Top Prospect, Watch Closely, Academy Ready, etc.)
  - Voice notes recording
  - Notes textarea
- Session management (save to Supabase `live_sessions` table)
- Export to Scout DB button (copies players to scouts.html watchlist)
- Undo functionality for actions

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
- Tables: `clubs`, `squad_data`, `scout_players`, `scout_reports`, `live_sessions`, `player_match_stats`
- RLS enabled on all tables with public read/write policies
- Add Club and Delete Club write directly to Supabase
- Upload player data via `import_to_scouting.py --upload-db` (parent directory)
- Import ECNL clubs via `import_ecnl_clubs.py` (parent directory)

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

## Data Flow Architecture

```
Supabase `clubs` table (SOURCE OF TRUTH for club IDs)
    ↓
┌───────────────────────────────────────────────────┐
│  APIscraper4.py / scraper3.py                     │
│  - Queries Supabase clubs for ID mapping          │
│  - Falls back to local csv_to_map_id dict         │
│  - Outputs JSON with clubId field                 │
└───────────────────────────────────────────────────┘
    ↓
import_to_scouting.py --upload-db
    ↓
Supabase `squad_data` table
    ↓
team.html (loads by ?club=CLUB_ID)
```

## Related Projects

- **ScoutReport** (github.com/stephenchase7/scoutreport): AI-powered report generator using Claude Haiku. Takes rough scouting notes and generates professional paragraphs. Planned integration with scouts.html.

- **FC360** (fc360.co): Video tagging system for match analysis. Used alongside Taka.io video platform.

## Roadmap

See `tasks/roadmap.md` for full implementation plan.

**Completed (June 2026):**
- Phase 0: Security & code cleanup (XSS fixes, RLS policies, dead code removal)
- Phase 1-4: Supabase schema, scouts.html UI redesign, team→scouts flow
- Phase 5: ScoutReport AI integration (voice input, trait buttons, Claude Haiku)
- Phase 6: Multi-season support (season dropdown, filtered queries)
- Phase 7: Per-match stats system (player_match_stats table, edit/delete)
- Phase 9: ECNL teams to map (league toggle, import script, Add Player)

**Next Up:**
- Phase 8: Multi-season history (compare seasons side-by-side)
- Phase 10: Authentication & Multi-Tenant SaaS

## ECNL Club Import

Import ECNL clubs from CSV:
```bash
python3 import_ecnl_clubs.py ecnl_clubs.csv
```

**CSV format:**
```csv
division,team_name,club_name,address,logo_filename
ECNL Northeast,PDA U13,Players Development Academy,"123 Main St, NJ",pda.png
```

**Logo files:** Place in `scouting-map/ECNL Logos/`
