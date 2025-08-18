#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
from typing import Dict, Type, Optional

from pilot.connections.base import BaseConnect
from pilot.connections.rdbms.mysql_connection import MySQLConnect
from pilot.connections.sqlite_connection import SQLiteConnect

class ConnectionRegistry:
    """Registry for database connections"""
    
    _registry: Dict[str, Type[BaseConnect]] = {}
    
    @classmethod
    def register(cls, db_type: str, connection_class: Type[BaseConnect]):
        """Register a connection class for a database type"""
        cls._registry[db_type.lower()] = connection_class
    
    @classmethod
    def get_connection(cls, db_type: str, **kwargs) -> Optional[BaseConnect]:
        """Get a connection instance for a database type"""
        db_type = db_type.lower()
        if db_type not in cls._registry:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        return cls._registry[db_type](**kwargs)
    
    @classmethod
    def get_connection_from_env(cls) -> Optional[BaseConnect]:
        """Get a connection instance from environment variables"""
        db_type = os.getenv("DB_TYPE", "sqlite").lower()
        
        if db_type == "mysql":
            return cls.get_connection(
                db_type,
                host=os.getenv("LOCAL_DB_HOST", "localhost"),
                port=int(os.getenv("LOCAL_DB_PORT", "3306")),
                user=os.getenv("LOCAL_DB_USER", "root"),
                password=os.getenv("LOCAL_DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "db_faturamento")
            )
        elif db_type == "sqlite":
            return cls.get_connection(
                db_type,
                db_path=os.getenv("DB_PATH", "data/faturamento.db"),
                db_name=os.getenv("DB_NAME", "db_faturamento")
            )
        else:
            raise ValueError(f"Unsupported database type in environment: {db_type}")


# Register connection classes
ConnectionRegistry.register("mysql", MySQLConnect)
ConnectionRegistry.register("sqlite", SQLiteConnect)
