"""
Database Manager Module
Handles SQLite database operations for storing processed PDFs
"""

import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)
DEFAULT_DB_DIR = Path(r"C:\LLM\tools\pdf_rag_db")
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "processed_pdfs.db"


class DatabaseManager:
    """
    Manage SQLite database for processed PDF storage
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database (default: C:\\LLM\\tools\\pdf_rag_db\\processed_pdfs.db)
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default path in shared tools directory
            self.db_path = DEFAULT_DB_PATH
            
        # Create directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
        logger.info(f"Database initialized at: {self.db_path}")
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for PDF documents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT,
                    file_hash TEXT UNIQUE NOT NULL,
                    file_size INTEGER,
                    num_pages INTEGER,
                    extraction_date TIMESTAMP,
                    extraction_method TEXT,
                    extraction_quality TEXT,
                    processing_status TEXT DEFAULT 'pending',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for extracted text chunks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS text_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_hash TEXT UNIQUE,
                    page_numbers TEXT,
                    char_count INTEGER,
                    word_count INTEGER,
                    quality_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
                    UNIQUE(document_id, chunk_index)
                )
            """)
            
            # Table for training data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    chunk_id INTEGER,
                    format_type TEXT NOT NULL,
                    instruction TEXT,
                    input_text TEXT,
                    output_text TEXT,
                    full_example TEXT NOT NULL,
                    example_hash TEXT UNIQUE,
                    tokens_estimate INTEGER,
                    used_in_training BOOLEAN DEFAULT 0,
                    training_batch TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE SET NULL,
                    FOREIGN KEY (chunk_id) REFERENCES text_chunks (id) ON DELETE SET NULL
                )
            """)
            
            # Table for processing logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    log_level TEXT,
                    message TEXT,
                    error_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document ON text_chunks(document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_training_document ON training_data(document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_training_used ON training_data(used_in_training)")
            
            conn.commit()
    
    def document_exists(self, file_hash: str) -> bool:
        """Check if document already exists in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,))
            return cursor.fetchone() is not None

    def get_document_id(self, file_hash: str) -> Optional[int]:
        """Get document ID for a given file hash."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_training_data_for_document(
        self,
        doc_id: int,
        format_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Retrieve training data examples for a specific document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT full_example FROM training_data WHERE document_id = ?"
            params = [doc_id]

            if format_type:
                query += " AND format_type = ?"
                params.append(format_type)

            query += " ORDER BY id"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)

            examples = []
            for row in cursor.fetchall():
                try:
                    example = json.loads(row[0])
                    examples.append(example)
                except json.JSONDecodeError:
                    logger.warning("Failed to decode training example for document %s", doc_id)

            return examples

    def reset_document_data(self, doc_id: int) -> Tuple[int, int]:
        """Remove existing chunks and training data for a document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM training_data WHERE document_id = ?", (doc_id,))
            training_deleted = cursor.rowcount

            cursor.execute("DELETE FROM text_chunks WHERE document_id = ?", (doc_id,))
            chunks_deleted = cursor.rowcount

            conn.commit()

        logger.info(
            "Reset document data for %s (deleted %s training examples, %s chunks)",
            doc_id,
            training_deleted,
            chunks_deleted,
        )
        return training_deleted, chunks_deleted
    
    def insert_document(self, doc_data: Dict) -> int:
        """
        Insert document metadata into database
        
        Args:
            doc_data: Document data from PDFExtractor
            
        Returns:
            Document ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if document already exists
            if self.document_exists(doc_data['file_hash']):
                logger.warning(f"Document already exists: {doc_data['filename']}")
                cursor.execute("SELECT id FROM documents WHERE file_hash = ?", 
                             (doc_data['file_hash'],))
                return cursor.fetchone()[0]
            
            # Insert document
            cursor.execute("""
                INSERT INTO documents (
                    filename, filepath, file_hash, file_size, num_pages,
                    extraction_date, extraction_method, extraction_quality,
                    processing_status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_data.get('filename'),
                doc_data.get('filepath'),
                doc_data.get('file_hash'),
                doc_data.get('file_size'),
                doc_data.get('num_pages'),
                doc_data.get('extraction_date'),
                doc_data.get('extraction_method'),
                doc_data.get('extraction_quality'),
                'extracted',
                json.dumps(doc_data.get('metadata', {}))
            ))
            
            doc_id = cursor.lastrowid
            
            # Log the insertion
            self._log_processing(doc_id, 'info', f"Document inserted: {doc_data['filename']}", conn)
            
            conn.commit()
            return doc_id
    
    def insert_text_chunks(self, doc_id: int, chunks: List[str]) -> List[int]:
        """
        Insert text chunks for a document
        
        Args:
            doc_id: Document ID
            chunks: List of text chunks
            
        Returns:
            List of chunk IDs
        """
        chunk_ids = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for i, chunk in enumerate(chunks):
                chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
                
                # Check if chunk already exists
                cursor.execute("SELECT id FROM text_chunks WHERE chunk_hash = ?", (chunk_hash,))
                existing = cursor.fetchone()
                
                if existing:
                    chunk_ids.append(existing[0])
                    continue
                
                # Insert new chunk
                cursor.execute("""
                    INSERT INTO text_chunks (
                        document_id, chunk_index, chunk_text, chunk_hash,
                        char_count, word_count
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    i,
                    chunk,
                    chunk_hash,
                    len(chunk),
                    len(chunk.split())
                ))
                
                chunk_ids.append(cursor.lastrowid)
            
            conn.commit()
            
        logger.info(f"Inserted {len(chunk_ids)} chunks for document {doc_id}")
        return chunk_ids
    
    def insert_training_examples(self, training_data: List[Dict], 
                                doc_id: Optional[int] = None,
                                batch_name: Optional[str] = None) -> int:
        """
        Insert training examples into database
        
        Args:
            training_data: List of training examples
            doc_id: Optional document ID
            batch_name: Optional batch identifier
            
        Returns:
            Number of examples inserted
        """
        inserted = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for example in training_data:
                # Calculate example hash to avoid duplicates
                example_str = json.dumps(example, sort_keys=True)
                example_hash = hashlib.md5(example_str.encode()).hexdigest()
                
                # Check if example already exists
                cursor.execute("SELECT id FROM training_data WHERE example_hash = ?", 
                             (example_hash,))
                if cursor.fetchone():
                    continue
                
                # Detect format type
                if 'instruction' in example:
                    format_type = 'alpaca'
                    instruction = example.get('instruction', '')
                    input_text = example.get('input', '')
                    output_text = example.get('output', '')
                elif 'messages' in example:
                    format_type = 'chatml'
                    instruction = ''
                    input_text = ''
                    output_text = ''
                else:
                    format_type = 'raw'
                    instruction = ''
                    input_text = example.get('text', '')
                    output_text = ''
                
                # Estimate tokens (rough: 1 token ≈ 4 characters)
                total_chars = len(instruction) + len(input_text) + len(output_text)
                tokens_estimate = total_chars // 4
                
                # Insert example
                cursor.execute("""
                    INSERT INTO training_data (
                        document_id, format_type, instruction, input_text, 
                        output_text, full_example, example_hash, tokens_estimate,
                        training_batch
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    format_type,
                    instruction[:1000],  # Truncate for display
                    input_text[:1000],
                    output_text[:1000],
                    example_str,
                    example_hash,
                    tokens_estimate,
                    batch_name
                ))
                
                inserted += 1
            
            conn.commit()
            
        logger.info(f"Inserted {inserted} training examples")
        return inserted
    
    def get_unprocessed_documents(self, limit: int = 10) -> List[Dict]:
        """Get documents that haven't been fully processed"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM documents 
                WHERE processing_status != 'completed'
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_training_data(self, 
                         unused_only: bool = True,
                         format_type: Optional[str] = None,
                         limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve training data from database
        
        Args:
            unused_only: Only get examples not yet used in training
            format_type: Filter by format type
            limit: Maximum number of examples to retrieve
            
        Returns:
            List of training examples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT full_example FROM training_data WHERE 1=1"
            params = []
            
            if unused_only:
                query += " AND used_in_training = 0"
            
            if format_type:
                query += " AND format_type = ?"
                params.append(format_type)
            
            query += " ORDER BY RANDOM()"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            
            examples = []
            for row in cursor.fetchall():
                try:
                    example = json.loads(row[0])
                    examples.append(example)
                except json.JSONDecodeError:
                    logger.warning("Failed to decode training example")
                    
            return examples
    
    def mark_training_data_used(self, example_ids: List[int], batch_name: str):
        """Mark training examples as used"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.executemany("""
                UPDATE training_data 
                SET used_in_training = 1, training_batch = ?
                WHERE id = ?
            """, [(batch_name, id_) for id_ in example_ids])
            
            conn.commit()
    
    def update_document_status(self, doc_id: int, status: str):
        """Update document processing status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE documents 
                SET processing_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, doc_id))
            
            conn.commit()
    
    def _log_processing(self, doc_id: int, level: str, message: str, 
                       conn: Optional[sqlite3.Connection] = None):
        """Log processing event"""
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO processing_logs (document_id, log_level, message)
            VALUES (?, ?, ?)
        """, (doc_id, level, message))
        
        if should_close:
            conn.commit()
            conn.close()
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Document statistics
            cursor.execute("SELECT COUNT(*) FROM documents")
            stats['total_documents'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT processing_status, COUNT(*) 
                FROM documents 
                GROUP BY processing_status
            """)
            stats['documents_by_status'] = dict(cursor.fetchall())
            
            # Chunk statistics
            cursor.execute("SELECT COUNT(*) FROM text_chunks")
            stats['total_chunks'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(char_count), AVG(word_count) FROM text_chunks")
            avg_chars, avg_words = cursor.fetchone()
            stats['avg_chunk_chars'] = avg_chars or 0
            stats['avg_chunk_words'] = avg_words or 0
            
            # Training data statistics
            cursor.execute("SELECT COUNT(*) FROM training_data")
            stats['total_training_examples'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT format_type, COUNT(*) 
                FROM training_data 
                GROUP BY format_type
            """)
            stats['training_by_format'] = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) FROM training_data WHERE used_in_training = 1")
            stats['used_training_examples'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(tokens_estimate) FROM training_data")
            stats['total_tokens_estimate'] = cursor.fetchone()[0] or 0
            
            # Database size
            stats['database_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
            
            return stats
    
    def export_training_data_to_jsonl(self, output_path: str, **filters):
        """
        Export training data to JSONL file
        
        Args:
            output_path: Path to output file
            **filters: Filters for get_training_data
        """
        training_data = self.get_training_data(**filters)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in training_data:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
                
        logger.info(f"Exported {len(training_data)} examples to {output_path}")
    
    def cleanup_duplicates(self):
        """Remove duplicate training examples"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Find and remove duplicates, keeping the first occurrence
            cursor.execute("""
                DELETE FROM training_data 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM training_data 
                    GROUP BY example_hash
                )
            """)
            
            deleted = cursor.rowcount
            conn.commit()
            
        logger.info(f"Removed {deleted} duplicate training examples")
        return deleted
    
    def backup_database(self, backup_dir: Optional[str] = None):
        """Create a backup of the database"""
        if backup_dir:
            backup_path = Path(backup_dir)
        else:
            backup_path = self.db_path.parent / 'backups'
            
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_path / f"processed_pdfs_backup_{timestamp}.db"
        
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(backup_file) as backup:
                source.backup(backup)
                
        logger.info(f"Database backed up to: {backup_file}")
        return str(backup_file)
