-- Migration: Backup Settings Configuration
-- Description: Add backup_settings table for configurable backup directory
-- Created: 2025-10-05

CREATE TABLE IF NOT EXISTS backup_settings (
  id SERIAL PRIMARY KEY,
  backup_directory VARCHAR(500) NOT NULL DEFAULT '/app/backups',
  auto_backup_enabled BOOLEAN DEFAULT false,
  auto_backup_schedule VARCHAR(50) DEFAULT '0 2 * * *', -- Cron format: 2 AM daily
  retention_days INTEGER DEFAULT 30,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO backup_settings (backup_directory, auto_backup_enabled, retention_days)
VALUES ('/app/backups', false, 30)
ON CONFLICT DO NOTHING;

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_backup_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER backup_settings_updated_at
BEFORE UPDATE ON backup_settings
FOR EACH ROW
EXECUTE FUNCTION update_backup_settings_updated_at();
