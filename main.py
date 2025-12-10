#!/usr/bin/env python3
"""
Readwise Data Exporter - Main Entry Point

A tool to export all your Readwise and Reader data to a local SQLite database.

Usage:
    python main.py init     # Initialize database tables
    python main.py sync     # Sync data from Readwise
    python main.py status   # Show sync status and statistics
"""

import sys
from src.config import Config
from src.database import DatabaseManager
from src.sync import SyncManager


def cmd_init():
    """Initialize the database with all required tables."""
    print("Initializing database...")
    db = DatabaseManager()
    db.init_tables()
    print("Done!")


def cmd_sync():
    """Sync all data from Readwise APIs."""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Validate token
    from src.api_client import ReadwiseAPIClient
    api = ReadwiseAPIClient()
    
    print("Validating access token...")
    if not api.validate_token():
        print("Error: Invalid access token. Please check your .env file.")
        sys.exit(1)
    print("Token validated successfully!\n")
    
    # Initialize database if needed
    db = DatabaseManager()
    db.init_tables()
    
    # Run sync
    sync_manager = SyncManager(db=db, api=api)
    sync_manager.sync_all()


def cmd_status():
    """Show current sync status and statistics."""
    db = DatabaseManager()
    
    # Check if database exists
    try:
        db.init_tables()
    except Exception as e:
        print(f"Error: Could not access database. Run 'python main.py init' first.")
        sys.exit(1)
    
    sync_manager = SyncManager(db=db)
    status = sync_manager.get_sync_status()
    
    print("=== Database Statistics ===")
    for entity, count in status["database_stats"].items():
        print(f"  {entity}: {count}")
    
    print("\n=== Sync State ===")
    for entity, state in status["sync_states"].items():
        if state:
            print(f"  {entity}: last synced at {state['last_sync_at']}")
        else:
            print(f"  {entity}: never synced")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    commands = {
        "init": cmd_init,
        "sync": cmd_sync,
        "status": cmd_status,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)
    
    commands[command]()


if __name__ == "__main__":
    main()
