#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from pilot.connections.base import BaseConnect
from pilot.configs.config import Config

class SQLiteConnect(BaseConnect):
    """SQLite connection implementation"""

    def __init__(self, db_path: str = None, db_name: str = None):
        """Initialize SQLite connection
        
        Args:
            db_path: Path to SQLite database file
            db_name: Database name (not used for SQLite, but kept for compatibility)
        """
        self.db_path = db_path or os.getenv("DB_PATH", "data/faturamento.db")
        self.db_name = db_name or os.getenv("DB_NAME", "db_faturamento")
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """Connect to SQLite database"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to database
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            print(f"Connected to SQLite database: {self.db_path}")
        except Exception as e:
            print(f"Error connecting to SQLite database: {e}")
            raise

    def get_connection(self):
        """Get SQLite connection"""
        if not self.conn:
            self._connect()
        return self.conn

    def get_cursor(self):
        """Get SQLite cursor"""
        if not self.cursor:
            self._connect()
        return self.cursor

    def execute(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results
        
        Args:
            sql: SQL query to execute
            params: Parameters for the SQL query
            
        Returns:
            List of dictionaries with query results
        """
        try:
            cursor = self.get_cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # For SELECT queries, return results
            if sql.strip().upper().startswith("SELECT"):
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                self.conn.commit()
                return []
        except Exception as e:
            print(f"Error executing SQL: {e}")
            print(f"SQL: {sql}")
            if params:
                print(f"Params: {params}")
            raise

    def get_tables(self) -> List[str]:
        """Get list of tables in database
        
        Returns:
            List of table names
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        result = self.execute(sql)
        return [row["name"] for row in result]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of dictionaries with column information
        """
        sql = f"PRAGMA table_info({table_name})"
        return self.execute(sql)

    def get_table_comment(self, table_name: str) -> str:
        """Get comment for a table (not supported in SQLite)
        
        Args:
            table_name: Name of the table
            
        Returns:
            Empty string (SQLite doesn't support table comments)
        """
        return ""

    def get_column_comments(self, table_name: str) -> Dict[str, str]:
        """Get comments for columns in a table (not supported in SQLite)
        
        Args:
            table_name: Name of the table
            
        Returns:
            Empty dictionary (SQLite doesn't support column comments)
        """
        return {}

    def get_primary_keys(self, table_name: str) -> List[str]:
        """Get primary keys for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of primary key column names
        """
        schema = self.get_table_schema(table_name)
        return [col["name"] for col in schema if col["pk"] == 1]

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign keys for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of dictionaries with foreign key information
        """
        sql = f"PRAGMA foreign_key_list({table_name})"
        return self.execute(sql)

    def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of dictionaries with index information
        """
        sql = f"PRAGMA index_list({table_name})"
        return self.execute(sql)

    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from a table
        
        Args:
            table_name: Name of the table
            limit: Maximum number of rows to return
            
        Returns:
            List of dictionaries with sample data
        """
        sql = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute(sql)

    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
