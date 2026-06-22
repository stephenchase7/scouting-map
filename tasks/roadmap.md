# NYRB Scouting Hub - Roadmap

## Completed

### Phase 0: Security & Code Cleanup (June 22, 2026)
- [x] Fix XSS vulnerability in `report.notes` (scouts.html)
- [x] Fix XSS in `onclick` handlers - sanitize clubId (index.html)
- [x] Remove duplicate `deleteSession()` function (live.html)
- [x] Fix `reportHistorySection` → `reportHistory` ID bug (scouts.html)
- [x] Fix `showToast()` to handle error parameter with styling (live.html)
- [x] Add null check for `data.players` (team.html)
- [x] Remove 16 console.log statements across all files
- [x] Remove unused `.rating-btn-inline` CSS (live.html)
- [x] Update `.gitignore` with comprehensive patterns
- [x] Remove backup files from git tracking
- [x] Enable Row Level Security (RLS) on all Supabase tables
- [x] Create RLS policies for all 5 tables (clubs, squad_data, scout_players, scout_reports, live_sessions)

### Phase 1: Supabase Schema for Player Linking (June 21, 2026)
- [x] Add `linked_player_key` column to `scout_players` table
- [x] Create index on `linked_player_key`

### Phase 2: scouts.html - Manual Linking
- [x] Add "Link to Roster" button in player panel (hidden, code preserved)
- [x] Add Link Modal HTML structure
- [x] Add CSS styles for linking UI
- [x] Add JavaScript linking functions
- [x] Update `viewPlayer()` for link indicator
- [x] Update `savePlayerToSupabase()` with `linked_player_key` field

### Phase 3: scouts.html - UI Redesign (June 22, 2026)
- [x] Add checkbox column for multi-select
- [x] Make player name clickable (opens panel)
- [x] Compact video/report indicators (📹/📝 icons)
- [x] Add inline status dropdown for quick changes
- [x] Add selection bar with bulk delete/status change
- [x] Remove View/Delete/+ buttons from table rows
- [x] Add row hover effects

### Phase 4: team.html → scouts.html Flow
- [x] Add `scoutedPlayerKeys` cache
- [x] Add `loadScoutedPlayers()` function
- [x] Add "Scout" button to player rows
- [x] Add `scoutPlayer()` function with prefill params
- [x] Handle prefill params in scouts.html (auto-create player, open panel)

---

## In Progress

### Phase 5: team.html Badge Display
- [ ] Show 📋 badge next to players who have scouting reports
- [ ] Badge click opens scouts.html with player selected
- [ ] Deep link handler in scouts.html (`?player=ID`)

---

## Planned

### Phase 6: Next Season Stats (2026-2027)
**Supabase Schema:**
```sql
ALTER TABLE scout_players
ADD COLUMN assists INTEGER DEFAULT 0,
ADD COLUMN key_passes INTEGER DEFAULT 0,
ADD COLUMN defensive_duels INTEGER DEFAULT 0,
ADD COLUMN saves INTEGER DEFAULT 0;
```

**UI Changes:**
- [ ] Add +/- buttons for Assists, Key Passes, Defensive Duels
- [ ] Add Saves counter (GK only)
- [ ] Display in player cards (scouts.html)
- [ ] Display in live scouting (live.html)

### Phase 7: ScoutReport AI Integration
- [ ] Integrate Claude Haiku for report generation
- [ ] Add "Generate Report" button in scouts.html
- [ ] Take rough notes → professional paragraphs

### Phase 8: ECNL Teams to Map
- [ ] Add ECNL clubs to index.html
- [ ] Add ECNL logos to `ECNL Logos/` folder
- [ ] Update division filters

### Phase 9: Multi-Season Support
- [ ] Add `season` column to `squad_data` table
- [ ] Update primary key to include season
- [ ] Add season selector UI in team.html
- [ ] Historical comparison views

---

## Backlog (Low Priority)

### Security Improvements
- [ ] Move to Supabase Auth (replace client-side password hash)
- [ ] Add input validation on all form submissions
- [ ] Rate limiting on Supabase writes

### Code Quality
- [ ] Consolidate duplicate haversine distance functions (index.html)
- [ ] Extract common utility functions (escapeHtml, initials calculation)
- [ ] Add TypeScript types (optional)

### UX Improvements
- [ ] Add loading spinners during async operations
- [ ] Improve error messages
- [ ] Add offline mode with service worker sync
