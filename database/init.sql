-- SQLite database schema for Technova Hub Dashboard
-- Run this script to initialize the database

CREATE TABLE IF NOT EXISTS extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    extraction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'success',
    data_json TEXT,  -- JSON data extracted from PDF
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_extractions_filename ON extractions(filename);
CREATE INDEX IF NOT EXISTS idx_extractions_date ON extractions(extraction_date);
CREATE INDEX IF NOT EXISTS idx_extractions_status ON extractions(status);

-- Sample data (optional)
-- INSERT INTO extractions (filename, file_size, mime_type, data_json) VALUES 
-- ('sample_report.pdf', 1024000, 'application/pdf', '{"title":"Sample Report","pages":5}');
