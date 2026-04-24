"""MongoDB connection and collection access."""
import os
from motor.motor_asyncio import AsyncIOMotorClient

_mongo_url = os.environ["MONGO_URL"]
_db_name = os.environ["DB_NAME"]

client = AsyncIOMotorClient(_mongo_url)
db = client[_db_name]

# Collections
users = db.users
documents = db.documents
sessions = db.sessions
messages = db.messages
share_links = db.share_links
feedback = db.feedback
audit_log = db.audit_log
analytics_events = db.analytics_events


async def init_indexes():
    """Create indexes for common queries."""
    await users.create_index("email", unique=True)
    await documents.create_index([("owner_id", 1), ("created_at", -1)])
    await sessions.create_index([("user_id", 1), ("updated_at", -1)])
    await messages.create_index([("session_id", 1), ("created_at", 1)])
    await share_links.create_index("token", unique=True)
    await audit_log.create_index([("created_at", -1)])
    await audit_log.create_index([("actor_id", 1), ("created_at", -1)])
    await analytics_events.create_index([("created_at", -1)])
