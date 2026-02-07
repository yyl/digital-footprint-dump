#!/usr/bin/env python3
"""
Digital Footprint Dump - Main Entry Point

Export your digital footprints to local SQLite databases.

Usage:
    python main.py init              # Initialize all databases
    python main.py sync              # Sync all services
    python main.py analyze           # Analyze all sources
    python main.py readwise-sync     # Sync Readwise only
    python main.py readwise-analyze  # Analyze Readwise archive
    python main.py foursquare-sync   # Sync Foursquare only
    python main.py letterboxd-sync   # Import Letterboxd data
    python main.py letterboxd-analyze # Analyze Letterboxd movies
    python main.py overcast-sync     # Import Overcast data
    python main.py overcast-analyze  # Analyze Overcast podcasts
    python main.py publish           # Publish monthly summary to blog
    python main.py publish --dry-run # Validate config without publishing
    python main.py status            # Show sync status
"""

import sys
import argparse
from src.config import Config


def cmd_init():
    """Initialize all databases."""
    print("Initializing databases...\n")
    
    # Readwise
    from src.readwise.database import ReadwiseDatabase
    db = ReadwiseDatabase()
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
    from src.readwise.database import ReadwiseDatabase
    from src.readwise.sync import SyncManager
    
    api = ReadwiseAPIClient()
    
    print("Validating Readwise access token...")
    if not api.validate_token():
        print("Error: Invalid Readwise access token. Please check your .env file.")
        sys.exit(1)
    print("Token validated!\n")
    
    db = ReadwiseDatabase()
    db.init_tables()
    
    sync_manager = SyncManager(db=db, api=api)
    sync_manager.sync_all()


def cmd_readwise_analyze():
    """Analyze Readwise archived articles."""
    # Ensure latest data
    cmd_readwise_sync()

    from src.readwise.database import ReadwiseDatabase
    from src.readwise.analytics import ReadwiseAnalytics

    print("Analyzing Readwise archive...")

    db = ReadwiseDatabase()

    if not db.check_tables_exist():
        print("Error: Readwise database tables not found.")
        print("Please run 'python main.py readwise-sync' first to populate the database.")
        sys.exit(1)

    analytics = ReadwiseAnalytics(db=db)
    record_count = analytics.analyze_archived()

    print(f"Analysis complete! {record_count} monthly records written to the analysis table in readwise.db")


def cmd_publish(dry_run: bool = False):
    """Publish monthly summary to blog repository.
    
    Args:
        dry_run: If True, validate config and sync data but skip actual publish.
    """
    if dry_run:
        print("=== DRY RUN MODE ===")
        print("Validating configuration and connectivity...\n")
        
        # Validate all configs
        try:
            Config.validate_readwise()
            print("✓ Readwise config valid")
        except ValueError as e:
            print(f"✗ Readwise: {e}")
        
        try:
            Config.validate_foursquare()
            print("✓ Foursquare config valid")
        except ValueError as e:
            print(f"✗ Foursquare: {e}")
        
        try:
            Config.validate_github()
            print("✓ GitHub config valid")
        except ValueError as e:
            print(f"✗ GitHub: {e}")
        
        # Test API connectivity
        print("\nTesting API connectivity...")
        
        try:
            from src.readwise.api_client import ReadwiseAPIClient
            api = ReadwiseAPIClient()
            if api.validate_token():
                print("✓ Readwise API accessible")
            else:
                print("✗ Readwise API: invalid token")
        except Exception as e:
            print(f"✗ Readwise API: {e}")
        
        print("\n=== DRY RUN COMPLETE ===")
        print("No changes were made.")
        return
    
    # First ensure we have the latest analysis from all sources
    print("=== Updating Analysis ===\n")
    
    print("--- Readwise ---")
    cmd_readwise_analyze()
    
    print("\n--- Letterboxd ---")
    cmd_letterboxd_analyze()
    
    print("\n--- Foursquare ---")
    cmd_foursquare_analyze()
    
    print("\n--- Overcast ---")
    cmd_overcast_analyze()
    
    print("\n=== Publishing ===")
    print("Publishing monthly summary...")
    
    from src.publish import Publisher
    
    try:
        publisher = Publisher()
        result = publisher.publish()
        print(f"\nPublished successfully!")
        print(f"Commit: {result['url']}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_foursquare_sync():
    """Sync Foursquare data only."""
    from src.foursquare.sync import FoursquareSyncManager
    
    sync_manager = FoursquareSyncManager()
    sync_manager.sync()


def cmd_foursquare_analyze():
    """Analyze Foursquare checkins."""
    # Ensure latest data
    cmd_foursquare_sync()

    from src.foursquare.database import FoursquareDatabase
    from src.foursquare.analytics import FoursquareAnalytics

    print("Analyzing Foursquare checkins...")

    db = FoursquareDatabase()
    db.init_tables()

    analytics = FoursquareAnalytics(db=db)
    record_count = analytics.analyze_checkins()

    print(f"Analysis complete! {record_count} monthly records written to the analysis table in foursquare.db")


def cmd_letterboxd_sync():
    """Import Letterboxd data from CSV export."""
    from src.letterboxd.importer import LetterboxdImporter
    
    importer = LetterboxdImporter()
    importer.sync()


def cmd_letterboxd_analyze():
    """Analyze Letterboxd watched movies."""
    # Ensure latest data
    cmd_letterboxd_sync()

    from src.letterboxd.database import LetterboxdDatabase
    from src.letterboxd.analytics import LetterboxdAnalytics

    print("Analyzing Letterboxd movies...")

    db = LetterboxdDatabase()
    db.init_tables()

    analytics = LetterboxdAnalytics(db=db)
    record_count = analytics.analyze_watched()

    print(f"Analysis complete! {record_count} monthly records written to the analysis table in letterboxd.db")


def cmd_analyze():
    """Analyze all sources."""
    print("=== Analyzing All Sources ===\n")
    
    # Readwise
    print("--- Readwise ---")
    try:
        from src.readwise.database import ReadwiseDatabase
        from src.readwise.analytics import ReadwiseAnalytics
        
        # Sync first
        cmd_readwise_sync()
        
        db = ReadwiseDatabase()
        analytics = ReadwiseAnalytics(db=db)
        count = analytics.analyze_archived()
        print(f"  {count} monthly records written")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Foursquare
    print("--- Foursquare ---")
    try:
        from src.foursquare.database import FoursquareDatabase
        from src.foursquare.analytics import FoursquareAnalytics
        
        # Sync first
        cmd_foursquare_sync()
        
        db = FoursquareDatabase()
        db.init_tables()
        analytics = FoursquareAnalytics(db=db)
        count = analytics.analyze_checkins()
        print(f"  {count} monthly records written")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Letterboxd
    print("--- Letterboxd ---")
    try:
        from src.letterboxd.database import LetterboxdDatabase
        from src.letterboxd.analytics import LetterboxdAnalytics
        
        # Sync first
        cmd_letterboxd_sync()
        
        db = LetterboxdDatabase()
        db.init_tables()
        analytics = LetterboxdAnalytics(db=db)
        count = analytics.analyze_watched()
        print(f"  {count} monthly records written")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Overcast
    print("--- Overcast ---")
    try:
        from src.overcast.analytics import OvercastAnalytics
        
        # Sync first
        cmd_overcast_sync()
        
        analytics = OvercastAnalytics()
        count = analytics.analyze_podcasts()
        print(f"  {count} monthly records written")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\nAnalysis complete!")


def cmd_overcast_sync():
    """Import Overcast data from OPML export."""
    from src.overcast.importer import OvercastImporter
    
    importer = OvercastImporter()
    importer.sync()


def cmd_overcast_analyze():
    """Analyze Overcast podcast data."""
    # Ensure latest data
    cmd_overcast_sync()

    from src.overcast.analytics import OvercastAnalytics

    print("Analyzing Overcast podcasts...")

    analytics = OvercastAnalytics()
    record_count = analytics.analyze_podcasts()

    print(f"Analysis complete! {record_count} monthly records written to the analysis table in overcast.db")


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
    
    print()
    
    # Overcast
    print("--- Overcast ---")
    cmd_overcast_sync()


def cmd_status():
    """Show sync status for all services."""
    print("=== Digital Footprint Status ===\n")
    
    # Readwise
    print("--- Readwise ---")
    try:
        from src.readwise.database import ReadwiseDatabase
        from src.readwise.sync import SyncManager
        
        db = ReadwiseDatabase()
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
        
        # Analysis status
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM analysis")
            analysis_count = cursor.fetchone()[0]
            cursor.execute("SELECT year_month, updated_at FROM analysis ORDER BY year_month DESC LIMIT 1")
            latest = cursor.fetchone()
        
        if analysis_count > 0 and latest:
            print(f"  analysis records: {analysis_count}")
            print(f"  latest analysis: {latest['year_month']} (updated: {latest['updated_at']})")
        else:
            print(f"  analysis: no records")
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
        from src.letterboxd.database import LetterboxdDatabase
        
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
        
        # Analysis status
        db = LetterboxdDatabase()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM analysis")
            analysis_count = cursor.fetchone()[0]
            cursor.execute("SELECT year_month, updated_at FROM analysis ORDER BY year_month DESC LIMIT 1")
            latest_analysis = cursor.fetchone()
        
        if analysis_count > 0 and latest_analysis:
            print(f"  analysis records: {analysis_count}")
            print(f"  latest analysis: {latest_analysis['year_month']} (updated: {latest_analysis['updated_at']})")
        else:
            print(f"  analysis: no records")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Overcast
    print("--- Overcast ---")
    try:
        from src.overcast.importer import OvercastImporter
        
        importer = OvercastImporter()
        status = importer.get_status()
        
        for entity, count in status.get("database_stats", {}).items():
            print(f"  {entity}: {count}")
        latest = status.get("latest_export")
        if latest:
            print(f"  latest_export: {latest.name}")
        
        # Analysis status
        import sqlite3
        db_path = Config.OVERCAST_DATABASE_PATH
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM analysis")
                analysis_count = cursor.fetchone()[0]
                cursor.execute("SELECT year_month, updated_at FROM analysis ORDER BY year_month DESC LIMIT 1")
                latest_analysis = cursor.fetchone()
                
                if analysis_count > 0 and latest_analysis:
                    print(f"  analysis records: {analysis_count}")
                    print(f"  latest analysis: {latest_analysis['year_month']} (updated: {latest_analysis['updated_at']})")
                else:
                    print(f"  analysis: no records")
            except sqlite3.OperationalError:
                print(f"  analysis: no records")
            conn.close()
    except Exception as e:
        print(f"  Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Digital Footprint Dump - Export your digital footprints to local SQLite databases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Simple commands (no arguments)
    subparsers.add_parser("init", help="Initialize all databases")
    subparsers.add_parser("sync", help="Sync all services")
    subparsers.add_parser("analyze", help="Analyze all sources")
    subparsers.add_parser("readwise-sync", help="Sync Readwise only")
    subparsers.add_parser("readwise-analyze", help="Analyze Readwise archive")
    subparsers.add_parser("foursquare-sync", help="Sync Foursquare only")
    subparsers.add_parser("foursquare-analyze", help="Analyze Foursquare checkins")
    subparsers.add_parser("letterboxd-sync", help="Import Letterboxd data")
    subparsers.add_parser("letterboxd-analyze", help="Analyze Letterboxd movies")
    subparsers.add_parser("overcast-sync", help="Import Overcast data")
    subparsers.add_parser("overcast-analyze", help="Analyze Overcast podcasts")
    subparsers.add_parser("status", help="Show sync status")
    
    # Publish command with --dry-run flag
    publish_parser = subparsers.add_parser("publish", help="Publish monthly summary to blog")
    publish_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and connectivity without publishing"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        "init": cmd_init,
        "sync": cmd_sync,
        "analyze": cmd_analyze,
        "readwise-sync": cmd_readwise_sync,
        "readwise-analyze": cmd_readwise_analyze,
        "foursquare-sync": cmd_foursquare_sync,
        "foursquare-analyze": cmd_foursquare_analyze,
        "letterboxd-sync": cmd_letterboxd_sync,
        "letterboxd-analyze": cmd_letterboxd_analyze,
        "overcast-sync": cmd_overcast_sync,
        "overcast-analyze": cmd_overcast_analyze,
        "status": cmd_status,
    }
    
    if args.command == "publish":
        cmd_publish(dry_run=args.dry_run)
    elif args.command in commands:
        commands[args.command]()
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
