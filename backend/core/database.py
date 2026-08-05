import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from core.config import Config
from core.logger import logger

class Database:
    def __init__(self):
        self._client = None
        self._collection = None
        self._db_enabled = False
        self._fallback_store = []
        self._connect()

    def _connect(self):
        uri = Config.MONGODB_URI
        if not uri:
            logger.info("MONGODB_URI not set -- using in-memory storage (resets on restart).")
            return

        try:
            self._client = MongoClient(
                uri, 
                server_api=ServerApi("1"), 
                serverSelectionTimeoutMS=5000, 
                tlsCAFile=certifi.where()
            )
            self._client.admin.command("ping")
            db = self._client["harassment_detection"]
            self._collection = db["flagged_messages"]
            self._db_enabled = True
            logger.info("Connected to MongoDB -- flagged messages will persist.")
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB ({e}) -- falling back to in-memory storage.")
            self._client = None
            self._collection = None
            self._db_enabled = False

    @property
    def is_persistent(self):
        return self._db_enabled

    @property
    def collection(self):
        return self._collection

    @property
    def fallback_store(self):
        return self._fallback_store

# Global instance
db_instance = Database()
