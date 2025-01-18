from peewee import *
from typing import List, Dict, Optional
import logging
from datetime import datetime
import os

db = SqliteDatabase(None)

class Message(Model):
    channel_id = IntegerField()
    role = CharField()
    content = TextField()
    image_url = CharField(null=True)
    timestamp = DateTimeField(default=datetime.now)

    class Meta:
        database = db

class DatabaseService:
    def __init__(self, db_path: str = "./db/database.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_path()
        db.init(self.db_path)
        db.connect()
        db.create_tables([Message])
        
    def init_path(self):
        if not os.path.exists("./db"):
            os.makedirs("./db")

    async def init_db(self):
        """Initialize database and create necessary tables."""
        if not Message.table_exists():
            db.create_tables([Message])

    async def add_message(self, channel_id: int, role: str, content: str, image_url: Optional[str]) -> None:
        """Add a message to the database."""
        try:
            Message.create(
                channel_id=channel_id,
                role=role,
                content=content,
                image_url=image_url
            )
        except Exception as e:
            self.logger.error(f"Error adding message to database: {e}")
            raise

    async def get_channel_history(self, channel_id: int) -> List[Dict[str, str]]:
        """Retrieve chat history for a specific channel."""
        try:
            messages = (Message
                    .select()
                    .where(Message.channel_id == channel_id)
                    .order_by(Message.timestamp))
            
            formatted_messages = []
            for msg in messages:
                if msg.image_url:
                    formatted_message = {
                        "role": msg.role,
                        "content": [
                            {"type": "text", "text": msg.content},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": msg.image_url,
                                },
                            },
                        ],
                    }
                else:
                    formatted_message = {
                        "role": msg.role,
                        "content": msg.content
                    }
                formatted_messages.append(formatted_message)
                
            return formatted_messages
        except Exception as e:
            self.logger.error(f"Error retrieving channel history: {e}")
            raise

    async def clear_channel_history(self, channel_id: int) -> None:
        """Clear all messages for a specific channel."""
        try:
            query = Message.delete().where(Message.channel_id == channel_id)
            query.execute()
        except Exception as e:
            self.logger.error(f"Error clearing channel history: {e}")
            raise

    def __del__(self):
        if not db.is_closed():
            db.close()