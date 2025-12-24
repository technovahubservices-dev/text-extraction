#!/usr/bin/env python3
"""
Technova Hub Dashboard API
Flask backend with SQLite database for storing extraction history
"""

import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'technova.db')

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with schema"""
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create extractions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                extraction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success',
                data_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_extractions_filename ON extractions(filename)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_extractions_date ON extractions(extraction_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_extractions_status ON extractions(status)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

# API Routes
@app.route('/api/extractions', methods=['GET'])
def get_extractions():
    """Get all extractions with optional filtering and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').lower()
        date_filter = request.args.get('date_filter', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        where_clause = "WHERE 1=1"
        params = []
        
        if search:
            where_clause += " AND LOWER(filename) LIKE ?"
            params.append(f'%{search}%')
        
        if date_filter:
            now = datetime.now()
            if date_filter == 'today':
                where_clause += " AND DATE(extraction_date) = DATE(?)"
                params.append(now.strftime('%Y-%m-%d'))
            elif date_filter == 'week':
                week_ago = now - timedelta(days=7)
                where_clause += " AND extraction_date >= ?"
                params.append(week_ago.strftime('%Y-%m-%d %H:%M:%S'))
            elif date_filter == 'month':
                month_ago = now - timedelta(days=30)
                where_clause += " AND extraction_date >= ?"
                params.append(month_ago.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM extractions {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = f"""
            SELECT * FROM extractions 
            {where_clause} 
            ORDER BY extraction_date DESC 
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [per_page, offset])
        extractions = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dicts
        results = []
        for row in extractions:
            result = dict(row)
            # Parse JSON data if exists
            if result['data_json']:
                try:
                    import json
                    result['data'] = json.loads(result['data_json'])
                except:
                    result['data'] = result['data_json']
            del result['data_json']  # Remove raw JSON field
            results.append(result)
        
        return jsonify({
            'extractions': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting extractions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extractions', methods=['POST'])
def create_extraction():
    """Create a new extraction record"""
    try:
        data = request.get_json()
        
        if not data or 'filename' not in data:
            return jsonify({'error': 'Filename is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert new extraction
        cursor.execute('''
            INSERT INTO extractions (filename, file_size, mime_type, status, data_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['filename'],
            data.get('file_size'),
            data.get('mime_type', 'application/pdf'),
            data.get('status', 'success'),
            data.get('data_json')
        ))
        
        extraction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': extraction_id,
            'message': 'Extraction created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating extraction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extractions/<int:extraction_id>', methods=['GET'])
def get_extraction(extraction_id):
    """Get a specific extraction by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM extractions WHERE id = ?', (extraction_id,))
        extraction = cursor.fetchone()
        conn.close()
        
        if not extraction:
            return jsonify({'error': 'Extraction not found'}), 404
        
        result = dict(extraction)
        if result['data_json']:
            try:
                import json
                result['data'] = json.loads(result['data_json'])
            except:
                result['data'] = result['data_json']
        del result['data_json']
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting extraction {extraction_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extractions/<int:extraction_id>', methods=['DELETE'])
def delete_extraction(extraction_id):
    """Delete a specific extraction"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM extractions WHERE id = ?', (extraction_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Extraction not found'}), 404
        
        conn.close()
        return jsonify({'message': 'Extraction deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting extraction {extraction_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extractions/clear', methods=['DELETE'])
def clear_extractions():
    """Clear all extractions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM extractions')
        conn.commit()
        
        deleted_count = cursor.rowcount
        conn.close()
        
        return jsonify({
            'message': f'Cleared {deleted_count} extractions successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing extractions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get dashboard metrics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total extractions
        cursor.execute('SELECT COUNT(*) as total FROM extractions')
        total = cursor.fetchone()['total']
        
        # This week
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) as week_count FROM extractions WHERE extraction_date >= ?', (week_ago,))
        week_count = cursor.fetchone()['week_count']
        
        # Average file size
        cursor.execute('SELECT AVG(file_size) as avg_size FROM extractions WHERE file_size IS NOT NULL')
        avg_size = cursor.fetchone()['avg_size']
        
        # Success rate (all are success for now)
        success_rate = 100 if total > 0 else 0
        
        conn.close()
        
        return jsonify({
            'total_extractions': total,
            'this_week': week_count,
            'avg_size': f"{avg_size/1024/1024:.1f} MB" if avg_size else '—',
            'success_rate': f"{success_rate}%"
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Export extractions as CSV"""
    try:
        import csv
        import io
        
        search = request.args.get('search', '').lower()
        date_filter = request.args.get('date_filter', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        where_clause = "WHERE 1=1"
        params = []
        
        if search:
            where_clause += " AND LOWER(filename) LIKE ?"
            params.append(f'%{search}%')
        
        if date_filter:
            now = datetime.now()
            if date_filter == 'today':
                where_clause += " AND DATE(extraction_date) = DATE(?)"
                params.append(now.strftime('%Y-%m-%d'))
            elif date_filter == 'week':
                week_ago = now - timedelta(days=7)
                where_clause += " AND extraction_date >= ?"
                params.append(week_ago.strftime('%Y-%m-%d %H:%M:%S'))
            elif date_filter == 'month':
                month_ago = now - timedelta(days=30)
                where_clause += " AND extraction_date >= ?"
                params.append(month_ago.strftime('%Y-%m-%d %H:%M:%S'))
        
        query = f"""
            SELECT filename, extraction_date, status 
            FROM extractions 
            {where_clause} 
            ORDER BY extraction_date DESC
        """
        cursor.execute(query, params)
        extractions = cursor.fetchall()
        conn.close()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Filename', 'Date', 'Status'])
        
        # Data rows
        for row in extractions:
            writer.writerow([row['filename'], row['extraction_date'], row['status']])
        
        output.seek(0)
        
        # Create response
        response = send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='extractions.csv'
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run server
    app.run(debug=True, host='0.0.0.0', port=5000)
