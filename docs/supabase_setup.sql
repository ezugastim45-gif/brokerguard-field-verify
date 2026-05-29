-- ============================================================================
-- BROKERGUARD FIELD VERIFY - SUPABASE SCHEMA
-- Version: 1.0
-- Description: Database schema and storage setup for field verifications
-- ============================================================================

-- ============================================================================
-- TABLE: field_verifications
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_verifications (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- References
  broker_id UUID NOT NULL,
  property_id TEXT NOT NULL,

  -- Location data
  lat DECIMAL(10,8) NOT NULL CHECK (lat >= -90 AND lat <= 90),
  lon DECIMAL(11,8) NOT NULL CHECK (lon >= -180 AND lon <= 180),
  altitude DECIMAL(8,2),  -- Meters above sea level
  address TEXT,

  -- Verification data
  image_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hex
  stamped_image_url TEXT NOT NULL,
  pdf_url TEXT,

  -- Metadata (JSONB for flexible data)
  metadata JSONB DEFAULT '{}'::jsonb,
  -- Example metadata structure:
  -- {
  --   "weather": "22°C, Clear",
  --   "compass": "NE (45°)",
  --   "notes": "Inspección inicial fachada norte",
  --   "device": "iPhone 14 Pro",
  --   "app_version": "0.1.0",
  --   "original_filename": "IMG_1234.jpg"
  -- }

  -- Timestamps
  verified_at TIMESTAMPTZ NOT NULL,  -- Timestamp from photo metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),  -- Row creation time in DB
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index on image_hash for fast verification lookups
CREATE INDEX IF NOT EXISTS idx_field_verifications_hash
  ON field_verifications(image_hash);

-- Composite index for broker + property queries
CREATE INDEX IF NOT EXISTS idx_field_verifications_broker_property
  ON field_verifications(broker_id, property_id);

-- Index on verified_at for chronological queries
CREATE INDEX IF NOT EXISTS idx_field_verifications_verified_at
  ON field_verifications(verified_at DESC);

-- Index on created_at for audit trails
CREATE INDEX IF NOT EXISTS idx_field_verifications_created_at
  ON field_verifications(created_at DESC);

-- GIN index on metadata JSONB for flexible queries
CREATE INDEX IF NOT EXISTS idx_field_verifications_metadata
  ON field_verifications USING GIN(metadata);

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_field_verifications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_field_verifications_updated_at
  BEFORE UPDATE ON field_verifications
  FOR EACH ROW
  EXECUTE FUNCTION update_field_verifications_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on the table
ALTER TABLE field_verifications ENABLE ROW LEVEL SECURITY;

-- Policy: Brokers can only read their own verifications
CREATE POLICY "Brokers can read own verifications"
  ON field_verifications
  FOR SELECT
  USING (broker_id = auth.uid());

-- Policy: Brokers can insert their own verifications
CREATE POLICY "Brokers can insert own verifications"
  ON field_verifications
  FOR INSERT
  WITH CHECK (broker_id = auth.uid());

-- Policy: Brokers can update their own verifications
CREATE POLICY "Brokers can update own verifications"
  ON field_verifications
  FOR UPDATE
  USING (broker_id = auth.uid())
  WITH CHECK (broker_id = auth.uid());

-- Policy: Service role can do everything (for backend API)
CREATE POLICY "Service role full access"
  ON field_verifications
  FOR ALL
  USING (auth.role() = 'service_role');

-- Policy: Public can verify by hash (read-only, no auth required)
CREATE POLICY "Public verification by hash"
  ON field_verifications
  FOR SELECT
  USING (true);  -- Anyone can verify a hash

-- ============================================================================
-- STORAGE BUCKET: field-verifications
-- ============================================================================

-- Create storage bucket (run in Supabase Dashboard > Storage)
-- Bucket name: field-verifications
-- Public: No (authenticated access only)

-- Storage policies (run after bucket creation):

-- Policy: Service role can insert objects
INSERT INTO storage.policies (name, bucket_id, definition)
VALUES (
  'Service role can insert',
  'field-verifications',
  '{"role": "service_role"}'::jsonb
);

-- Policy: Authenticated users can read objects
INSERT INTO storage.policies (name, bucket_id, definition)
VALUES (
  'Authenticated users can read',
  'field-verifications',
  '{"role": "authenticated"}'::jsonb
);

-- Policy: Public can read objects (for verification URLs)
INSERT INTO storage.policies (name, bucket_id, definition)
VALUES (
  'Public can read',
  'field-verifications',
  '{"role": "anon"}'::jsonb
);

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Get all verifications for a broker
-- SELECT * FROM field_verifications
-- WHERE broker_id = 'uuid-here'
-- ORDER BY verified_at DESC;

-- Get verification by hash
-- SELECT * FROM field_verifications
-- WHERE image_hash = 'hash-here';

-- Get verifications for a property
-- SELECT * FROM field_verifications
-- WHERE property_id = 'PROP-123'
-- ORDER BY verified_at DESC;

-- Search metadata (e.g., find all with weather data)
-- SELECT * FROM field_verifications
-- WHERE metadata->>'weather' IS NOT NULL;

-- Get verification stats by broker
-- SELECT
--   broker_id,
--   COUNT(*) as total_verifications,
--   MIN(verified_at) as first_verification,
--   MAX(verified_at) as last_verification
-- FROM field_verifications
-- GROUP BY broker_id;

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

-- Clean up old verifications (optional, run periodically)
-- DELETE FROM field_verifications
-- WHERE created_at < NOW() - INTERVAL '2 years';

-- Vacuum table for performance
-- VACUUM ANALYZE field_verifications;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
