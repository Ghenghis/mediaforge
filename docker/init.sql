-- Civitai AI Learning Database Schema
-- PostgreSQL / Supabase Compatible

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Images table with full tracking
CREATE TABLE IF NOT EXISTS images (
    image_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) UNIQUE NOT NULL,
    prompt TEXT,
    negative_prompt TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    model VARCHAR(100),
    seed BIGINT,
    rating DECIMAL(4,2) DEFAULT 0 CHECK (rating >= 0 AND rating <= 15),
    rating_history JSONB DEFAULT '[]'::jsonb,
    analysis JSONB DEFAULT '{}'::jsonb,
    generation_source VARCHAR(50) DEFAULT 'manual',
    parent_image_id UUID REFERENCES images(image_id),
    is_gold_standard BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rated_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tag analysis table
CREATE TABLE IF NOT EXISTS tag_analysis (
    tag VARCHAR(255) PRIMARY KEY,
    category VARCHAR(50),
    avg_rating DECIMAL(4,2) DEFAULT 0,
    high_rating_count INTEGER DEFAULT 0,
    low_rating_count INTEGER DEFAULT 0,
    weight DECIMAL(5,4) DEFAULT 0.5000,
    importance DECIMAL(5,4) DEFAULT 0.5000,
    last_high_rating TIMESTAMPTZ,
    associated_tags JSONB DEFAULT '[]'::jsonb,
    enhancement_suggestions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rating events for learning
CREATE TABLE IF NOT EXISTS rating_events (
    id SERIAL PRIMARY KEY,
    image_id UUID REFERENCES images(image_id),
    old_rating DECIMAL(4,2),
    new_rating DECIMAL(4,2),
    rating_change DECIMAL(4,2),
    tags_analyzed JSONB DEFAULT '[]'::jsonb,
    learning_applied JSONB DEFAULT '{}'::jsonb,
    auto_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Gold standard images (rating 15)
CREATE TABLE IF NOT EXISTS gold_standards (
    id SERIAL PRIMARY KEY,
    image_id UUID REFERENCES images(image_id),
    prompt TEXT,
    tags JSONB,
    key_features JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generation queue
CREATE TABLE IF NOT EXISTS generation_queue (
    id SERIAL PRIMARY KEY,
    trigger_image_id UUID REFERENCES images(image_id),
    trigger_rating DECIMAL(4,2),
    images_to_generate INTEGER,
    images_generated INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    prompt_enhancements JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Story collections
CREATE TABLE IF NOT EXISTS story_collections (
    id SERIAL PRIMARY KEY,
    collection_name VARCHAR(255),
    theme VARCHAR(50),
    story_hash VARCHAR(20),
    total_scenes INTEGER DEFAULT 0,
    images_generated INTEGER DEFAULT 0,
    target_images INTEGER DEFAULT 500,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Story scenes
CREATE TABLE IF NOT EXISTS story_scenes (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES story_collections(id),
    scene_number INTEGER,
    scene_text TEXT,
    extracted_elements JSONB DEFAULT '{}'::jsonb,
    prompt TEXT,
    images_generated INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collection images
CREATE TABLE IF NOT EXISTS collection_images (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES story_collections(id),
    scene_id INTEGER REFERENCES story_scenes(id),
    image_id UUID REFERENCES images(image_id),
    rating DECIMAL(4,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User preferences / memories
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    item VARCHAR(255),
    preference INTEGER DEFAULT 0,
    weight DECIMAL(5,4) DEFAULT 0.5000,
    times_selected INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, subcategory, item)
);

-- Chat learning history
CREATE TABLE IF NOT EXISTS chat_memory (
    id SERIAL PRIMARY KEY,
    user_input TEXT,
    extracted_data JSONB DEFAULT '{}'::jsonb,
    actions_taken JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prompt patterns that work
CREATE TABLE IF NOT EXISTS prompt_patterns (
    id SERIAL PRIMARY KEY,
    pattern TEXT,
    category VARCHAR(50),
    avg_rating DECIMAL(4,2) DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning log
CREATE TABLE IF NOT EXISTS learning_log (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(50),
    category VARCHAR(50),
    item VARCHAR(255),
    old_weight DECIMAL(5,4),
    new_weight DECIMAL(5,4),
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_images_rating ON images(rating DESC);
CREATE INDEX IF NOT EXISTS idx_images_created ON images(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_images_gold ON images(is_gold_standard) WHERE is_gold_standard = TRUE;
CREATE INDEX IF NOT EXISTS idx_tag_analysis_weight ON tag_analysis(weight DESC);
CREATE INDEX IF NOT EXISTS idx_rating_events_image ON rating_events(image_id);
CREATE INDEX IF NOT EXISTS idx_collection_images ON collection_images(collection_id, scene_id);

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER images_updated_at BEFORE UPDATE ON images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tag_analysis_updated_at BEFORE UPDATE ON tag_analysis
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER story_collections_updated_at BEFORE UPDATE ON story_collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- View for dashboard stats
CREATE OR REPLACE VIEW dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM images) as total_images,
    (SELECT COUNT(*) FROM images WHERE rating > 0) as rated_images,
    (SELECT COUNT(*) FROM images WHERE is_gold_standard = TRUE) as gold_standards,
    (SELECT COALESCE(AVG(rating), 0) FROM images WHERE rating > 0) as avg_rating,
    (SELECT COUNT(*) FROM tag_analysis WHERE weight > 0.6) as high_performing_tags,
    (SELECT COALESCE(SUM(images_generated), 0) FROM generation_queue) as auto_generated,
    (SELECT COUNT(*) FROM story_collections) as story_collections,
    (SELECT COUNT(*) FROM learning_log) as learning_events;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO civitai;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO civitai;
