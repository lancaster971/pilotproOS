"""
PostgreSQL Connection Pool
===========================
ThreadedConnectionPool per gestione connessioni efficienti
"""

import psycopg2
from psycopg2 import pool
from typing import Optional
import os


class DatabasePool:
    """PostgreSQL connection pool wrapper"""

    def __init__(self,
                 minconn: int = 1,
                 maxconn: int = 5,
                 host: str = "localhost",
                 port: int = 5432,
                 dbname: str = "pilotpros_db",
                 user: str = "pilotpros_user",
                 password: str = None):
        """
        Initialize connection pool

        Args:
            minconn: Minimum connections
            maxconn: Maximum connections
            host: Database host
            port: Database port
            dbname: Database name
            user: Database user
            password: Database password
        """
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password or os.getenv("DB_PASSWORD"),
            connect_timeout=5,
            options='-c statement_timeout=5000'
        )

    def get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)

    def close_all(self):
        """Close all connections"""
        self.pool.closeall()

    def execute_query(self, query: str, params: tuple = None):
        """
        Execute query using pool

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        conn = None
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(query, params)

            if query.strip().upper().startswith('SELECT'):
                results = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in results]
            else:
                conn.commit()
                return cur.rowcount

        finally:
            if conn:
                self.return_connection(conn)


# Singleton instance
_instance = None

def get_db_pool(host: str = "localhost", port: int = 5432) -> DatabasePool:
    """Get or create singleton pool instance"""
    global _instance
    if _instance is None:
        _instance = DatabasePool(
            minconn=1,
            maxconn=5,
            host=host,
            port=port
        )
    return _instance