# Technova Hub Dashboard Server

Python Flask backend with SQLite database for storing PDF extraction history.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

- `GET /api/extractions` - Get all extractions (with pagination, search, filters)
- `POST /api/extractions` - Create new extraction record
- `GET /api/extractions/<id>` - Get specific extraction
- `DELETE /api/extractions/<id>` - Delete specific extraction
- `DELETE /api/extractions/clear` - Clear all extractions
- `GET /api/metrics` - Get dashboard metrics
- `GET /api/export/csv` - Export extractions as CSV

## Query Parameters

For `/api/extractions`:
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 10)
- `search` - Search filename (case-insensitive)
- `date_filter` - Filter by date: `today`, `week`, `month`

## Database

SQLite database created automatically at `technova.db` with schema:
- `extractions` table stores all extraction records
- Indexes on filename, date, and status for performance
