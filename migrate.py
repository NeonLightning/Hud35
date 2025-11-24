#!/usr/bin/env python3
import os
import sqlite3
import pickle
import zlib
import hashlib

def load_old_song_counts():
    """Load song counts from the old binary format"""
    file_path = '/opt/hud35/song_counts.bin'
    print(f"Looking for file: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    print(f"File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 0} bytes")
    
    if not os.path.exists(file_path):
        print("File does not exist")
        return {}
        
    try:
        with open(file_path, 'rb') as f:
            compressed_data = f.read()
            print(f"Read {len(compressed_data)} bytes")
            
            if not compressed_data:
                print("File is empty")
                return {}
                
            print("Decompressing data...")
            try:
                decompressed_data = zlib.decompress(compressed_data)
                print(f"Decompressed to {len(decompressed_data)} bytes")
            except zlib.error as e:
                print(f"Zlib decompression error: {e}")
                return {}
                
            print("Unpickling data...")
            try:
                all_data = pickle.loads(decompressed_data)
                print(f"Unpickled data structure: {type(all_data)}")
            except Exception as e:
                print(f"Pickle load error: {e}")
                return {}
            
        named_counts = {}
        if 'counts' in all_data and 'mapping' in all_data:
            print(f"Found {len(all_data['counts'])} song entries")
            for song_hash, count in all_data['counts'].items():
                song_name = all_data['mapping'].get(song_hash, f"Unknown_{song_hash[:8]}")
                named_counts[song_name] = count
            print(f"Successfully loaded {len(named_counts)} named songs")
        else:
            print("Invalid data structure - missing 'counts' or 'mapping' keys")
            print(f"Available keys: {list(all_data.keys())}")
            
        return named_counts
        
    except Exception as e:
        print(f"Error loading old song counts: {e}")
        import traceback
        traceback.print_exc()
        return {}

def migrate_to_sqlite():
    """Migrate existing binary data to SQLite"""
    print("Starting migration from binary to SQLite...")
    print("=" * 50)
    
    # Load old data
    old_counts = load_old_song_counts()
    
    if not old_counts:
        print("No song data found to migrate.")
        return
        
    print(f"Found {len(old_counts)} songs to migrate...")
    
    # Initialize database
    db_path = '/opt/hud35/song_stats.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS song_plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_hash TEXT UNIQUE,
            song_data TEXT,
            play_count INTEGER DEFAULT 0,
            last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migrate data
    migrated_count = 0
    for song, count in old_counts.items():
        song_hash = hashlib.md5(song.encode('utf-8')).hexdigest()[:16]
        try:
            cursor.execute('''
                INSERT INTO song_plays (song_hash, song_data, play_count)
                VALUES (?, ?, ?)
            ''', (song_hash, song, count))
            migrated_count += 1
            if migrated_count % 100 == 0:
                print(f"Migrated {migrated_count} songs...")
        except Exception as e:
            print(f"Error migrating song '{song[:50]}...': {e}")
    
    conn.commit()
    
    # Create indexes
    print("Creating indexes...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_count ON song_plays(play_count)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON song_plays(song_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_played ON song_plays(last_played)')
    conn.commit()
    conn.close()
    
    # Backup old file
    if os.path.exists('/opt/hud35/song_counts.bin'):
        backup_path = '/opt/hud35/song_counts.bin.backup'
        os.rename('/opt/hud35/song_counts.bin', backup_path)
        print(f"Backed up old file to {backup_path}")
    
    print("=" * 50)
    print(f"Migration completed! Migrated {migrated_count} songs.")
    print(f"Database created at: {db_path}")
    print("You can now delete song_counts.bin.backup if everything looks good.")

if __name__ == '__main__':
    migrate_to_sqlite()
