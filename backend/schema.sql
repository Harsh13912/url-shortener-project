-- URL Shortener Database Schema
-- PostgreSQL (Neon) Setup Script

-- Drop existing table if you're resetting
-- DROP TABLE IF EXISTS urls CASCADE;

-- Create URLs table
CREATE TABLE IF NOT EXISTS urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    short_code VARCHAR(10) UNIQUE NOT NULL,
    long_url TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    click_count INTEGER DEFAULT 0,
    
    -- Add index for fast lookups
    CONSTRAINT short_code_length CHECK (char_length(short_code) >= 5)
);

-- Create indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code);
CREATE INDEX IF NOT EXISTS idx_expires_at ON urls(expires_at);
CREATE INDEX IF NOT EXISTS idx_created_at ON urls(created_at DESC);

-- Create function to automatically delete expired URLs (optional)
CREATE OR REPLACE FUNCTION delete_expired_urls() 
RETURNS void AS $$
BEGIN
    DELETE FROM urls WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a scheduled job to clean up expired URLs
-- (This requires pg_cron extension - available on some managed PostgreSQL services)
-- SELECT cron.schedule('delete-expired-urls', '0 2 * * *', 'SELECT delete_expired_urls()');

-- Verify table creation
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'urls'
ORDER BY ordinal_position;
