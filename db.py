import sqlite3
from contextlib import closing
from datetime import datetime
import json
from config import Config
from logger import logger

class Database:
    def __init__(self, db_name=Config.DATABASE_NAME):
        self.conn = sqlite3.connect(db_name)
        self._init_db()
        
    def _init_db(self):
        with closing(self.conn.cursor()) as c:
            # Users table
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (telegram_id INTEGER PRIMARY KEY,
                          steam_id TEXT,
                          language TEXT DEFAULT 'en',
                          check_interval INTEGER DEFAULT 6,
                          silent_mode BOOLEAN DEFAULT FALSE,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Games table
            c.execute('''CREATE TABLE IF NOT EXISTS games
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          telegram_id INTEGER,
                          game_id INTEGER,
                          name TEXT,
                          installed BOOLEAN DEFAULT FALSE,
                          last_played INTEGER DEFAULT 0,
                          last_buildid TEXT,
                          last_checked TIMESTAMP,
                          FOREIGN KEY(telegram_id) REFERENCES users(telegram_id),
                          UNIQUE(telegram_id, game_id))''')
            
            # Updates history
            c.execute('''CREATE TABLE IF NOT EXISTS updates
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          telegram_id INTEGER,
                          game_id INTEGER,
                          game_name TEXT,
                          build_id TEXT,
                          update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          changelog_url TEXT,
                          notified BOOLEAN DEFAULT FALSE,
                          FOREIGN KEY(telegram_id) REFERENCES users(telegram_id))''')
            
            # Statistics
            c.execute('''CREATE TABLE IF NOT EXISTS stats
                         (telegram_id INTEGER PRIMARY KEY,
                          total_updates INTEGER DEFAULT 0,
                          last_update TIMESTAMP,
                          FOREIGN KEY(telegram_id) REFERENCES users(telegram_id))''')
            
            self.conn.commit()
    
    # User methods
    def add_user(self, telegram_id, steam_id=None):
        try:
            with closing(self.conn.cursor()) as c:
                c.execute('''INSERT OR IGNORE INTO users (telegram_id, steam_id) 
                            VALUES (?, ?)''', (telegram_id, steam_id))
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error adding user: {e}")
            return False
    
    def update_steam_id(self, telegram_id, steam_id):
        try:
            with closing(self.conn.cursor()) as c:
                c.execute('''UPDATE users SET steam_id = ? 
                            WHERE telegram_id = ?''', (steam_id, telegram_id))
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error updating Steam ID: {e}")
            return False
    
    def get_user(self, telegram_id):
        try:
            with closing(self.conn.cursor()) as c:
                c.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
                return c.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Database error getting user: {e}")
            return None
    
    def update_user_setting(self, telegram_id, setting, value):
        try:
            with closing(self.conn.cursor()) as c:
                c.execute(f'''UPDATE users SET {setting} = ? 
                            WHERE telegram_id = ?''', (value, telegram_id))
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error updating user setting: {e}")
            return False
    
    # Game methods
    def add_or_update_game(self, telegram_id, game_id, name, installed=False, last_played=0):
        try:
            with closing(self.conn.cursor()) as c:
                c.execute('''INSERT OR REPLACE INTO games 
                            (telegram_id, game_id, name, installed, last_played) 
                            VALUES (?, ?, ?, ?, ?)''', 
                            (telegram_id, game_id, name, installed, last_played))
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error adding/updating game: {e}")
            return False
    
    def get_installed_games(self, telegram_id):
        try:
            with closing(self.conn.cursor()) as c:
                c.execute('''SELECT game_id, name, last_buildid, last_played 
                            FROM games 
                            WHERE telegram_id = ? AND installed = TRUE
                            ORDER BY last_played DESC''', (telegram_id,))
                return c.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error getting installed games: {e}")
            return []
    
    def update_game_buildid(self, telegram_id, game_id, build_id):
        try:
            with closing(self.conn.cursor()) as c:
                c.execute('''UPDATE games SET last_buildid = ?, last_checked = CURRENT_TIMESTAMP
                            WHERE telegram_id = ? AND game_id = ?''', 
                            (build_id, telegram_id, game_id))
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error updating game buildid: {e}")
            return False
    
    # Update methods
    def record_update(self, telegram_id, game_id, game_name, build_id, changelog_url):
        try:
            with closing(self.conn.cursor()) as c:
                # Record the update
                c.execute('''INSERT INTO updates 
                            (telegram_id, game_id, game_name, build_id, changelog_url) 
                            VALUES (?, ?, ?, ?, ?)''', 
                            (telegram_id, game_id, game_name, build_id, changelog_url))
                
                # Update stats
                c.execute('''INSERT OR IGNORE INTO stats (telegram_id, total_updates) 
                            VALUES (?, 0)''', (telegram_id,))
                c.execute('''UPDATE stats SET total_updates = total_updates + 1, 
                            last_update = CURRENT_TIMESTAMP 
                            WHERE telegram_id = ?''', (telegram_id,))
                
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error recording update: {e}")
            return False
    
    # Stats methods
    def get_user_stats(self, telegram_id):
        try:
            with closing(self.conn.cursor()) as c:
                c.execute('''SELECT total_updates, last_update FROM stats 
                            WHERE telegram_id = ?''', (telegram_id,))
                stats = c.fetchone()
                
                c.execute('''SELECT COUNT(*) FROM games 
                            WHERE telegram_id = ? AND installed = TRUE''', (telegram_id,))
                installed_count = c.fetchone()[0]
                
                c.execute('''SELECT game_name, MAX(update_time) as last_update 
                            FROM updates 
                            WHERE telegram_id = ? 
                            GROUP BY game_name 
                            ORDER BY last_update DESC LIMIT 5''', (telegram_id,))
                recent_updates = c.fetchall()
                
                return {
                    'total_updates': stats[0] if stats else 0,
                    'last_update': stats[1] if stats else None,
                    'installed_count': installed_count,
                    'recent_updates': recent_updates
                }
        except sqlite3.Error as e:
            logger.error(f"Database error getting user stats: {e}")
            return None
    
    def close(self):
        self.conn.close()