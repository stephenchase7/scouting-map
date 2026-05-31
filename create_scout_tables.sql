-- Create scouts table
CREATE TABLE IF NOT EXISTS scouts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create scout_players table
CREATE TABLE IF NOT EXISTS scout_players (
  id TEXT PRIMARY KEY,
  scout_id TEXT NOT NULL,
  name TEXT NOT NULL,
  club TEXT,
  squad TEXT,
  jersey TEXT,
  yob TEXT,
  foot TEXT,
  position TEXT,
  status TEXT DEFAULT 'watching',
  notes TEXT,
  video_links JSONB DEFAULT '[]',
  shared_with JSONB DEFAULT '[]',
  date_added TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create scout_reports table
CREATE TABLE IF NOT EXISTS scout_reports (
  id TEXT PRIMARY KEY,
  player_id TEXT NOT NULL,
  author_id TEXT NOT NULL,
  author_name TEXT,
  report_date TIMESTAMPTZ DEFAULT NOW(),
  match TEXT,
  source TEXT,
  build TEXT,
  weaker_foot TEXT,
  with_ball TEXT,
  against_ball TEXT,
  next_action TEXT,
  priority TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS but allow public access (same as other tables)
ALTER TABLE scouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout_reports ENABLE ROW LEVEL SECURITY;

-- Create policies for public read/write access
CREATE POLICY "Allow public read on scouts" ON scouts FOR SELECT USING (true);
CREATE POLICY "Allow public insert on scouts" ON scouts FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on scouts" ON scouts FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on scouts" ON scouts FOR DELETE USING (true);

CREATE POLICY "Allow public read on scout_players" ON scout_players FOR SELECT USING (true);
CREATE POLICY "Allow public insert on scout_players" ON scout_players FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on scout_players" ON scout_players FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on scout_players" ON scout_players FOR DELETE USING (true);

CREATE POLICY "Allow public read on scout_reports" ON scout_reports FOR SELECT USING (true);
CREATE POLICY "Allow public insert on scout_reports" ON scout_reports FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on scout_reports" ON scout_reports FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on scout_reports" ON scout_reports FOR DELETE USING (true);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_scout_players_scout_id ON scout_players(scout_id);
CREATE INDEX IF NOT EXISTS idx_scout_reports_player_id ON scout_reports(player_id);
CREATE INDEX IF NOT EXISTS idx_scout_reports_author_id ON scout_reports(author_id);
