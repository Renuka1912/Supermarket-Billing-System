import sqlite3
import os
from flask import g
import config

def get_db():
    """Get database connection for current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(config.DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database from schema.sql."""
    db = sqlite3.connect(config.DATABASE)
    db.row_factory = sqlite3.Row
    with open(os.path.join(config.BASE_DIR, 'schema.sql'), 'r') as f:
        db.executescript(f.read())
    db.commit()
    db.close()

def query_db(query, args=(), one=False):
    """Execute a query and return results as list of dicts."""
    db = get_db()
    cur = db.execute(query, args)
    rv = [dict(row) for row in cur.fetchall()]
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Execute an insert/update/delete and return lastrowid."""
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    lastrowid = cur.lastrowid
    cur.close()
    return lastrowid
