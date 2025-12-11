-- Story Service Database Initialization
-- Creates basic schema for story_db

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Stories table
CREATE TABLE IF NOT EXISTS stories (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    age_range VARCHAR(20) NOT NULL,
    moral_lesson TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
);

-- Index on age_range for filtering
CREATE INDEX IF NOT EXISTS idx_stories_age_range ON stories(age_range);
CREATE INDEX IF NOT EXISTS idx_stories_created_at ON stories(created_at DESC);

-- Personalized stories table (for tracking personalization requests)
CREATE TABLE IF NOT EXISTS personalized_stories (
    id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES stories(id) ON DELETE CASCADE,
    child_name VARCHAR(100) NOT NULL,
    child_photo_url TEXT,
    personalized_content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index on story_id for joins
CREATE INDEX IF NOT EXISTS idx_personalized_stories_story_id ON personalized_stories(story_id);

-- Insert sample stories
INSERT INTO stories (title, content, age_range, moral_lesson) VALUES
    ('The Brave Little Turtle', 'Once upon a time, there was a brave little turtle who lived by the sea...', '3-5', 'Courage comes in all sizes'),
    ('The Magic Paintbrush', 'In a small village, there lived a young artist who discovered a magic paintbrush...', '6-8', 'Use your talents to help others'),
    ('The Friendly Dragon', 'High in the mountains lived a dragon who just wanted to make friends...', '4-6', 'Don''t judge by appearances')
ON CONFLICT DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to stories table
DROP TRIGGER IF EXISTS update_stories_updated_at ON stories;
CREATE TRIGGER update_stories_updated_at
    BEFORE UPDATE ON stories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kidcomic;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kidcomic;
