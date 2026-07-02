-- Create database_players table for unified scout database
CREATE TABLE IF NOT EXISTS database_players (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  club TEXT,
  pos TEXT,
  age TEXT,
  foot TEXT DEFAULT 'R',
  status TEXT DEFAULT 'database',
  now_rating INTEGER DEFAULT 0,
  ceiling INTEGER DEFAULT 0,
  press INTEGER DEFAULT 0,
  weapons JSONB DEFAULT '[]',
  kpi_ratings JSONB DEFAULT '{}',
  reports JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS with public access
ALTER TABLE database_players ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read on database_players" ON database_players FOR SELECT USING (true);
CREATE POLICY "Allow public insert on database_players" ON database_players FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on database_players" ON database_players FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on database_players" ON database_players FOR DELETE USING (true);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_database_players_status ON database_players(status);
CREATE INDEX IF NOT EXISTS idx_database_players_age ON database_players(age);
CREATE INDEX IF NOT EXISTS idx_database_players_pos ON database_players(pos);
