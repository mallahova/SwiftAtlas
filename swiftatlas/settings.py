import os

MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "mongoadmin")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "password")
MONGODB_URL = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@mongo:27017/"
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "swift_codes")
