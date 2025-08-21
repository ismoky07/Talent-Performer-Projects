import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

# ============================
# Real-World Use Case: Personal Fitness Tracker with Neo4j
# ============================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", None)

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise ValueError("❗️ You must set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in your .env file")

def iso_timestamp_days_ago(days: int) -> str:
    """Return ISO timestamp N days ago"""
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

class FitnessTracker:
    def __init__(self):
        self.driver = None

    async def connect(self):
        """Initialize connection to Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            
            # Test connection
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            
            # Create constraints and indices
            async with self.driver.session() as session:
                await session.run("CREATE CONSTRAINT activity_id IF NOT EXISTS FOR (a:Activity) REQUIRE a.activity_id IS UNIQUE")
                await session.run("CREATE INDEX user_index IF NOT EXISTS FOR (a:Activity) ON (a.user)")
                await session.run("CREATE INDEX activity_type_index IF NOT EXISTS FOR (a:Activity) ON (a.activity_type)")
                await session.run("CREATE INDEX timestamp_index IF NOT EXISTS FOR (a:Activity) ON (a.timestamp)")
            
            logger.info("✅ Connected to Neo4j and created indices")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise

    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("✅ Neo4j connection closed")

    async def add_activity(self, activity_data):
        """Add a fitness activity to Neo4j"""
        try:
            async with self.driver.session() as session:
                query = """
                CREATE (a:Activity {
                    user: $user,
                    activity_id: $activity_id,
                    activity_type: $activity_type,
                    distance_km: $distance_km,
                    duration_min: $duration_min,
                    timestamp: $timestamp,
                    created_at: datetime()
                })
                """
                await session.run(query, activity_data)
            
            logger.info(f"✅ Added activity: {activity_data['activity_type']} - {activity_data['distance_km']}km")
        except Exception as e:
            logger.error(f"❌ Failed to add activity: {e}")
            raise

    async def query_recent_activities(self, user: str, days: int):
        """Query activities in the last N days"""
        try:
            since_time = iso_timestamp_days_ago(days)
            
            async with self.driver.session() as session:
                query = """
                MATCH (a:Activity)
                WHERE a.user = $user AND a.timestamp >= $since_time
                RETURN a.user as user, a.activity_type as activity_type,
                       a.distance_km as distance_km, a.duration_min as duration_min,
                       a.timestamp as timestamp
                ORDER BY a.timestamp DESC
                """
                result = await session.run(query, {"user": user, "since_time": since_time})
                activities = []
                async for record in result:
                    activities.append({
                        "user": record["user"],
                        "activity_type": record["activity_type"],
                        "distance_km": record["distance_km"],
                        "duration_min": record["duration_min"],
                        "timestamp": record["timestamp"]
                    })
                return activities
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return []

    async def query_running_over_distance(self, user: str, min_distance: float, days: int):
        """Query running activities over certain distance"""
        try:
            since_time = iso_timestamp_days_ago(days)
            
            async with self.driver.session() as session:
                query = """
                MATCH (a:Activity)
                WHERE a.user = $user AND a.activity_type = 'running'
                      AND a.distance_km >= $min_distance AND a.timestamp >= $since_time
                RETURN a.user as user, a.activity_type as activity_type,
                       a.distance_km as distance_km, a.duration_min as duration_min,
                       a.timestamp as timestamp
                ORDER BY a.timestamp DESC
                """
                result = await session.run(query, {
                    "user": user,
                    "min_distance": min_distance,
                    "since_time": since_time
                })
                activities = []
                async for record in result:
                    activities.append({
                        "user": record["user"],
                        "activity_type": record["activity_type"],
                        "distance_km": record["distance_km"],
                        "duration_min": record["duration_min"],
                        "timestamp": record["timestamp"]
                    })
                return activities
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return []

    async def query_by_activity_type(self, user: str, activity_type: str, days: int):
        """Query activities of specific type"""
        try:
            since_time = iso_timestamp_days_ago(days)
            
            async with self.driver.session() as session:
                query = """
                MATCH (a:Activity)
                WHERE a.user = $user AND a.activity_type = $activity_type AND a.timestamp >= $since_time
                RETURN a.user as user, a.activity_type as activity_type,
                       a.distance_km as distance_km, a.duration_min as duration_min,
                       a.timestamp as timestamp
                ORDER BY a.timestamp DESC
                """
                result = await session.run(query, {
                    "user": user,
                    "activity_type": activity_type,
                    "since_time": since_time
                })
                activities = []
                async for record in result:
                    activities.append({
                        "user": record["user"],
                        "activity_type": record["activity_type"],
                        "distance_km": record["distance_km"],
                        "duration_min": record["duration_min"],
                        "timestamp": record["timestamp"]
                    })
                return activities
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return []

def create_sample_activities():
    """Create sample fitness activities"""
    return [
        {
            "user": "ahmed_hassan",
            "activity_id": "activity_a1",
            "activity_type": "running",
            "distance_km": 6.0,
            "duration_min": 35,
            "timestamp": iso_timestamp_days_ago(7),
        },
        {
            "user": "fatima_ali",
            "activity_id": "activity_a2",
            "activity_type": "cycling",
            "distance_km": 20.0,
            "duration_min": 60,
            "timestamp": iso_timestamp_days_ago(3),
        },
        {
            "user": "omar_mahmoud",
            "activity_id": "activity_a3",
            "activity_type": "running",
            "distance_km": 4.0,
            "duration_min": 25,
            "timestamp": iso_timestamp_days_ago(2),
        },
        {
            "user": "ahmed_hassan",
            "activity_id": "activity_a4",
            "activity_type": "running",
            "distance_km": 8.0,
            "duration_min": 45,
            "timestamp": iso_timestamp_days_ago(1),
        },
        {
            "user": "fatima_ali",
            "activity_id": "activity_a5",
            "activity_type": "strength_training",
            "distance_km": 0,
            "duration_min": 60,
            "timestamp": iso_timestamp_days_ago(1),
        }
    ]

def print_results(results, title: str):
    """Print query results"""
    print(f"\n--- {title} ---")
    if not results:
        print("No results found.")
        return
    
    for activity in results:
        print(f"• User: {activity['user']}")
        print(f"  Activity: {activity['activity_type']}")
        print(f"  Distance: {activity['distance_km']} km")
        print(f"  Duration: {activity['duration_min']} minutes")
        print(f"  Timestamp: {activity['timestamp']}")
        print()

async def main():
    print("=== Neo4j Fitness Tracker (without Vector Search) ===")
    print(f"Connecting to: {NEO4J_URI}")
    
    tracker = FitnessTracker()
    
    try:
        # Connect to Neo4j
        print("🔄 Connecting to Neo4j...")
        await tracker.connect()
        
        # Add sample activities
        print("\n1. Adding sample fitness activities...")
        activities = create_sample_activities()
        for activity in activities:
            await tracker.add_activity(activity)
        
        print("\n2. Running fitness queries...")
        
        # Query: Ahmed's activities in the last 5 days
        recent_results = await tracker.query_recent_activities("ahmed_hassan", days=5)
        print_results(recent_results, "Ahmed's Activities in the last 5 days")
        
        # Query: Ahmed's running activities > 5 km in the last 7 days
        running_results = await tracker.query_running_over_distance("ahmed_hassan", min_distance=5, days=7)
        print_results(running_results, "Ahmed's Running > 5 km in the last 7 days")
        
        # Query: Fatima's cycling activities
        cycling_results = await tracker.query_by_activity_type("fatima_ali", "cycling", days=30)
        print_results(cycling_results, "Fatima's Cycling activities in the last 30 days")
        
        # Query: All users' activities
        all_users = ["ahmed_hassan", "fatima_ali", "omar_mahmoud"]
        for user in all_users:
            user_results = await tracker.query_recent_activities(user, days=30)
            print_results(user_results, f"{user}'s Activities in the last 30 days")
        
        print("\n✅ All queries completed successfully!")
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await tracker.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")