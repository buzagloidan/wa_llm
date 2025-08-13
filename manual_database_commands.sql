-- Manual SQL commands to clear the database for Jeen.ai transformation
-- Run these commands directly in your PostgreSQL database if the Python script fails

-- First, clear all data from existing tables
TRUNCATE TABLE kbtopic CASCADE;
TRUNCATE TABLE message CASCADE; 
TRUNCATE TABLE sender CASCADE;

-- Verify tables are empty
SELECT COUNT(*) as kbtopic_count FROM kbtopic;
SELECT COUNT(*) as message_count FROM message;
SELECT COUNT(*) as sender_count FROM sender;

-- Optional: If you want to completely drop and recreate tables
-- (Use this only if you want a completely fresh start)

-- DROP TABLE IF EXISTS kbtopic CASCADE;
-- DROP TABLE IF EXISTS message CASCADE;
-- DROP TABLE IF EXISTS sender CASCADE;

-- Note: After clearing data, you can run the bot and it will recreate
-- the tables with the new schema automatically via SQLModel