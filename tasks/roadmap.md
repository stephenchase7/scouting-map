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

### Phase 5: ScoutReport AI Integration (June 22, 2026)
- [x] Collapsible sections: Special Weapons, With the Ball, Against the Ball
- [x] Multi-select trait buttons (12 special weapons, 13 with ball, 12 against ball)
- [x] Voice input via Web Speech API (click mic to record)
- [x] "Generate Report" button calls rules_server.py /api/generate-report
- [x] Preview area with editable content
- [x] Save/Cancel after generation
- [x] Edit existing reports with Update Report button
- [x] Reports show Special Weapons in history
- [x] special_weapons column added to Supabase scout_reports table

### Phase 6: Multi-Season Support (June 22, 2026)
- [x] Verified squad_data table has season column
- [x] Standardized season format to YYYY-YYYY (e.g., 2025-2026)
- [x] Implemented `changeSeason()` function in team.html
- [x] Added season filter to Supabase query
- [x] Season dropdown UI with dynamic selection

### Phase 7: Per-Match Stats System (June 22, 2026)
- [x] Created player_match_stats table in Supabase
- [x] New columns in team.html: A, KP, A1v1, D1v1, SV (removed Link/Scout)
- [x] Player detail modal: + Add Match button
- [x] Match stats entry modal with all fields
- [x] Edit/delete buttons on each match stat row
- [x] Stats aggregate from per-match entries to roster table

---

## Planned

### Phase 8: Multi-Season History

**What this is:** Currently all data is for one season (2025-2026). This feature lets you:
- View historical seasons (2024-2025, 2023-2024, etc.)
- Compare player progression across seasons
- Keep old data when new season starts (no overwriting)

**Example use case:** "How many goals did Player X score last season vs this season?"

**Supabase Schema:**
```sql
-- Add season to squad_data (composite primary key)
ALTER TABLE squad_data ADD COLUMN season TEXT DEFAULT '2025-2026';
ALTER TABLE squad_data DROP CONSTRAINT squad_data_pkey;
ALTER TABLE squad_data ADD PRIMARY KEY (club_id, squad, season);

-- Add season to player_match_stats when created
-- Already designed with season support in mind
```

**UI Changes - team.html:**
- [ ] Season dropdown selector (top of page)
- [ ] Default to current season
- [ ] Load data filtered by selected season
- [ ] "Compare Seasons" button (side-by-side view)

**Data Flow:**
```
Scraper runs for 2026-2027 season
    ↓
Upload with --season 2026-2027 flag
    ↓
New rows created (old 2025-2026 data preserved)
    ↓
UI shows both seasons in dropdown
```

**Implementation:**
1. [ ] Add season column to squad_data
2. [ ] Update scraper to include season in output
3. [ ] Update import script with --season flag
4. [ ] Add season selector UI
5. [ ] Update queries to filter by season
6. [ ] Build comparison view

---

### Phase 9: ECNL Teams to Map

**Overview:** Add ECNL (Elite Clubs National League) clubs to the scouting map alongside MLS NEXT clubs.

**Tasks:**
- [ ] Add ECNL clubs to index.html clubs array
- [ ] Collect ECNL club logos → `ECNL Logos/` folder
- [ ] Add "ECNL" option to division/pathway filter
- [ ] Different marker color or icon for ECNL vs MLS NEXT
- [ ] Update CSV validation for ECNL club names

---

### Phase 10: Authentication & Multi-Tenant SaaS

**Overview:** Supabase Auth with organization-based access. White-label ready for selling to other MLS clubs.

**Access Model:**
- **Logged out:** Map view only (index.html map + buttons). All other features locked.
- **Logged in:** Full access to organization's data only
- **Org admin:** Manages their users, full control of their account
- **Super admin (you):** Emergency break-glass access with audit trail

**Multi-Tenant Architecture:**
```sql
-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,                    -- "New England Revolution"
    slug TEXT UNIQUE NOT NULL,             -- "ne-revolution"

    -- Customization
    primary_color TEXT DEFAULT '#ED1B24', -- Theme color
    logo_url TEXT,
    hq_lat DECIMAL(10, 6),                 -- Distance calculations from their HQ
    hq_lng DECIMAL(10, 6),
    hq_name TEXT,                          -- "Gillette Stadium"

    -- Settings
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User profiles with org membership
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    organization_id UUID REFERENCES organizations(id),
    role TEXT DEFAULT 'member',            -- 'member', 'admin', 'super_admin'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add org_id to all data tables
ALTER TABLE clubs ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE squad_data ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE scout_players ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE scout_reports ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE live_sessions ADD COLUMN organization_id UUID REFERENCES organizations(id);
```

**Row Level Security (Tenant Isolation):**
```sql
-- Users can only see their organization's data
CREATE POLICY "Tenant isolation" ON clubs
    USING (organization_id = (
        SELECT organization_id FROM user_profiles
        WHERE id = auth.uid()
    ));

-- Super admin bypass (your account)
CREATE POLICY "Super admin access" ON clubs
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND role = 'super_admin'
        )
    );
```

**Security Measures:**
- [ ] RLS on ALL tables with tenant isolation
- [ ] Super admin access logged to audit table
- [ ] Password requirements: 12+ chars, complexity rules
- [ ] Email verification required
- [ ] Session timeout (configurable per org)
- [ ] Rate limiting on auth endpoints
- [ ] No plaintext secrets in code (use Supabase Vault)

**Features:**
- [ ] Email/password login via Supabase Auth
- [ ] Email notification on new signups (Edge Function → your email)
- [ ] Org admin: invite users, remove users, change roles
- [ ] Account settings: change password, profile
- [ ] Super admin dashboard (emergency access, view audit logs)
- [ ] Help section (How-to guides, FAQs)

**White-Label Customization:**
- [ ] Dynamic theme colors from org settings
- [ ] Custom logo per org
- [ ] Distance calculations from org HQ (not hardcoded NYRB)
- [ ] Org name in header/title

**Implementation:**
1. [ ] Create organizations and user_profiles tables
2. [ ] Add organization_id to all existing tables
3. [ ] Set up Supabase Auth
4. [ ] Implement RLS policies with tenant isolation
5. [ ] Build login/signup UI
6. [ ] Build org admin user management
7. [ ] Add super admin dashboard
8. [ ] Implement white-label theming
9. [ ] Add audit logging
10. [ ] Security hardening (rate limits, session config)

---

## Backlog (Low Priority)

### Code Quality
- [ ] Consolidate duplicate haversine distance functions (index.html)
- [ ] Extract common utility functions (escapeHtml, initials calculation)
- [ ] Add TypeScript types (optional)

### UX Improvements
- [ ] Add loading spinners during async operations
- [ ] Improve error messages
- [ ] Add offline mode with service worker sync
