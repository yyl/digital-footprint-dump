"""Sync manager for Foursquare data synchronization."""

from typing import Optional

from .database import FoursquareDatabase
from .api_client import FoursquareAPIClient


class FoursquareSyncManager:
    """Orchestrates synchronization of Foursquare data."""
    
    def __init__(
        self,
        db: Optional[FoursquareDatabase] = None,
        api: Optional[FoursquareAPIClient] = None
    ):
        """Initialize sync manager."""
        self.db = db or FoursquareDatabase()
        self.api = api or FoursquareAPIClient()
    
    def ensure_auth(self) -> bool:
        """Ensure we have a valid access token, running OAuth if needed."""
        if self.api.needs_auth():
            print("No Foursquare access token found. Starting OAuth flow...")
            token = self.api.run_oauth_flow()
            if not token:
                print("Error: Failed to obtain access token")
                return False
        return True
    
    def sync(self) -> dict:
        """Sync all Foursquare data.
        
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "checkins": 0,
            "places": 0,
        }
        
        # Ensure authentication
        if not self.ensure_auth():
            return stats
        
        # Get user ID
        user_id = self.api.get_user_id()
        if not user_id:
            print("Error: Could not get Foursquare user ID")
            return stats
        
        print(f"Authenticated as Foursquare user: {user_id}")
        
        # Initialize database
        self.db.init_tables()
        
        # Ensure user exists BEFORE inserting checkins (FK constraint)
        self.db.upsert_user(user_id, 0)
        
        # Get last pulled timestamp for incremental sync
        last_timestamp = self.db.get_last_pulled_timestamp(user_id)
        if last_timestamp > 0:
            print(f"Incremental sync: fetching checkins after timestamp {last_timestamp}")
        else:
            print("Full sync: fetching all checkins...")
        
        # Fetch checkins
        checkins = self.api.fetch_checkins(after_timestamp=last_timestamp)
        print(f"Fetched {len(checkins)} new checkins")
        
        if not checkins:
            print("No new checkins to sync")
            return stats
        
        # Track highest timestamp for incremental sync
        highest_timestamp = last_timestamp
        
        # Process checkins
        for i, checkin in enumerate(checkins):
            created_at = checkin.get("createdAt", 0)
            venue = checkin.get("venue", {})
            place_id = venue.get("id")
            
            if not place_id:
                continue
            
            # MUST ensure place exists before inserting checkin (FK constraint)
            if not self.db.place_exists(place_id):
                # Try Places API first for richer data
                place_data = self.api.fetch_place_details(place_id)
                
                if not place_data:
                    # Fallback: use venue data from checkin (v2 API format)
                    venue_location = venue.get("location", {})
                    categories = venue.get("categories", [])
                    primary_category = categories[0] if categories else {}
                    
                    place_data = {
                        "fsq_place_id": place_id,
                        "name": venue.get("name"),
                        "latitude": venue_location.get("lat"),
                        "longitude": venue_location.get("lng"),
                        "location": {
                            "address": venue_location.get("address"),
                            "locality": venue_location.get("city"),
                            "region": venue_location.get("state"),
                            "postcode": venue_location.get("postalCode"),
                            "country": venue_location.get("country"),
                            "formatted_address": ", ".join(venue_location.get("formattedAddress", []))
                        },
                        "categories": [{
                            "id": primary_category.get("id"),
                            "name": primary_category.get("name")
                        }] if primary_category else []
                    }
                
                if not self.db.upsert_place(place_data):
                    # Place insert failed, skip this checkin
                    print(f"  Warning: Failed to insert place {place_id}, skipping checkin")
                    continue
                stats["places"] += 1
            
            # Now safe to insert checkin (place exists)
            try:
                if self.db.insert_checkin(checkin, user_id):
                    stats["checkins"] += 1
            except Exception as e:
                print(f"\n=== FK ERROR DEBUG ===")
                print(f"Error: {e}")
                print(f"Place ID: {place_id}")
                print(f"Place exists in DB: {self.db.place_exists(place_id)}")
                print(f"Venue from checkin: {venue}")
                print(f"Place data used: {place_data if 'place_data' in dir() else 'N/A (place already existed)'}")
                print(f"Checkin ID: {checkin.get('id')}")
                print(f"Checkin createdAt: {checkin.get('createdAt')}")
                print(f"======================\n")
                raise
            
            # Track highest timestamp
            if created_at > highest_timestamp:
                highest_timestamp = created_at
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(checkins)} checkins...")
        
        # Update last pulled timestamp
        if highest_timestamp > last_timestamp:
            self.db.upsert_user(user_id, highest_timestamp)
        
        print(f"\nFoursquare sync complete!")
        print(f"  Checkins: {stats['checkins']}")
        print(f"  Places: {stats['places']}")
        
        return stats
    
    def get_status(self) -> dict:
        """Get current sync status."""
        try:
            self.db.init_tables()
            return {
                "database_stats": self.db.get_stats(),
                "has_token": not self.api.needs_auth()
            }
        except Exception as e:
            return {
                "error": str(e),
                "has_token": not self.api.needs_auth()
            }
