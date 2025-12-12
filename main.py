#!/usr/bin/env python3
"""
Digital Footprint Dump - Main Entry Point

Export your digital footprints to local SQLite databases.

Usage:
    python main.py init             # Initialize all databases
    python main.py sync             # Sync all services
    python main.py readwise-sync    # Sync Readwise only
    python main.py foursquare-sync  # Sync Foursquare only
    python main.py letterboxd-sync  # Import Letterboxd data
    python main.py status           # Show sync status
"""

import sys
from src.config import Config


def cmd_init():
    """Initialize all databases."""
    print("Initializing databases...\n")
    
    # Readwise
    from src.readwise.database import DatabaseManager
    db = DatabaseManager()
    db.init_tables()
    
    # Foursquare
    from src.foursquare.database import FoursquareDatabase
    fsq_db = FoursquareDatabase()
    fsq_db.init_tables()
    
    # Letterboxd
    from src.letterboxd.database import LetterboxdDatabase
    lbxd_db = LetterboxdDatabase()
    lbxd_db.init_tables()
    
    print("\nDone!")


def cmd_readwise_sync():
    """Sync Readwise data only."""
    try:
        Config.validate_readwise()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    from src.readwise.api_client import ReadwiseAPIClient
    from src.readwise.database import DatabaseManager
    from src.readwise.sync import SyncManager
    
    api = ReadwiseAPIClient()
    
    print("Validating Readwise access token...")
    if not api.validate_token():
        print("Error: Invalid Readwise access token. Please check your .env file.")
        sys.exit(1)
    print("Token validated!\n")
    
    db = DatabaseManager()
    db.init_tables()
    
    sync_manager = SyncManager(db=db, api=api)
    sync_manager.sync_all()


def cmd_foursquare_sync():
    """Sync Foursquare data only."""
    from src.foursquare.sync import FoursquareSyncManager
    
    sync_manager = FoursquareSyncManager()
    sync_manager.sync()


def cmd_letterboxd_sync():
    """Import Letterboxd data from CSV export."""
    from src.letterboxd.importer import LetterboxdImporter
    
    importer = LetterboxdImporter()
    importer.sync()


def cmd_sync():
    """Sync all services."""
    print("=== Syncing All Services ===\n")
    
    # Readwise
    print("--- Readwise ---")
    try:
        Config.validate_readwise()
        cmd_readwise_sync()
    except ValueError as e:
        print(f"Skipping Readwise: {e}\n")
    
    print()
    
    # Foursquare
    print("--- Foursquare ---")
    cmd_foursquare_sync()
    
    print()
    
    # Letterboxd
    print("--- Letterboxd ---")
    cmd_letterboxd_sync()


def cmd_status():
    """Show sync status for all services."""
    print("=== Digital Footprint Status ===\n")
    
    # Readwise
    print("--- Readwise ---")
    try:
        from src.readwise.database import DatabaseManager
        from src.readwise.sync import SyncManager
        
        db = DatabaseManager()
        db.init_tables()
        sync_manager = SyncManager(db=db)
        status = sync_manager.get_sync_status()
        
        for entity, count in status["database_stats"].items():
            print(f"  {entity}: {count}")
        for entity, state in status["sync_states"].items():
            if state:
                print(f"  {entity} last synced: {state['last_sync_at']}")
            else:
                print(f"  {entity}: never synced")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Foursquare
    print("--- Foursquare ---")
    try:
        from src.foursquare.sync import FoursquareSyncManager
        
        sync_manager = FoursquareSyncManager()
        status = sync_manager.get_status()
        
        if "error" in status:
            print(f"  Error: {status['error']}")
        else:
            for entity, count in status.get("database_stats", {}).items():
                print(f"  {entity}: {count}")
            print(f"  has_token: {status.get('has_token', False)}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Letterboxd
    print("--- Letterboxd ---")
    try:
        from src.letterboxd.importer import LetterboxdImporter
        
        importer = LetterboxdImporter()
        status = importer.get_status()
        
        if "error" in status:
            print(f"  Error: {status['error']}")
        else:
            for entity, count in status.get("database_stats", {}).items():
                print(f"  {entity}: {count}")
            latest = status.get("latest_export")
            if latest:
                print(f"  latest_export: {latest.name}")
    except Exception as e:
        print(f"  Error: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    commands = {
        "init": cmd_init,
        "sync": cmd_sync,
        "readwise-sync": cmd_readwise_sync,
        "foursquare-sync": cmd_foursquare_sync,
        "letterboxd-sync": cmd_letterboxd_sync,
        "status": cmd_status,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)
    
    commands[command]()


if __name__ == "__main__":
    main()
