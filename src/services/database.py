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
    edited_timestamp = DateTimeField(null=True)
    message_id = IntegerField(null=True)

    class Meta:
        database = db
        
class EnabledChannels(Model):
    channel_id = IntegerField()
    
    class Meta:
        database = db
        
class DisabledChannels(Model):
    channel_id = IntegerField()
    
    class Meta:
        database = db
        
class DisabledTools(Model):
    guild_id = IntegerField()
    tool_type = CharField()
    
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
        if not Message.table_exists():
            db.create_tables([Message])
        if not EnabledChannels.table_exists():
            db.create_tables([EnabledChannels])
        if not DisabledChannels.table_exists():
            db.create_tables([DisabledChannels])
        if not DisabledTools.table_exists():
            db.create_tables([DisabledTools])
            
    async def update_message(self, channel_id: int, message_id: int, content: str, edited_timestamp: datetime) -> None:
        try:
            Message.update(
                content=content,
                edited_timestamp=edited_timestamp
            ).where(
                (Message.channel_id == channel_id) & 
                (Message.message_id == message_id)
            ).execute()
        except Exception as e:
            self.logger.error(f"Error updating message in database: {e}")
            raise
            
    async def get_disabled_tools(self, guild_id: int) -> List[str]:
        try:
            tools = DisabledTools.select().where(DisabledTools.guild_id == guild_id)
            return [tool.tool_type for tool in tools]
        except Exception as e:
            self.logger.error(f"Error retrieving disabled tools: {e}")
            raise
        
    async def remove_disabled_tool(self, tool_type: str, guild_id: int) -> None:
        try:
            query = DisabledTools.delete().where(
                (DisabledTools.tool_type == tool_type) & 
                (DisabledTools.guild_id == guild_id)
            )
            query.execute()
        except Exception as e:
            self.logger.error(f"Error removing disabled tool from database: {e}")
            raise
        
    async def add_disabled_tool(self, tool_type: str, guild_id: int) -> None:
        try:
            DisabledTools.create(tool_type=tool_type, guild_id=guild_id)
        except Exception as e:
            self.logger.error(f"Error adding disabled tool to database: {e}")
            raise
            
    async def get_disabled_channels(self) -> List[int]:
        try:
            channels = DisabledChannels.select()
            return [channel.channel_id for channel in channels]
        except Exception as e:
            self.logger.error(f"Error retrieving disabled channels: {e}")
            raise
        
    async def add_disabled_channel(self, channel_id: int) -> None:
        try:
            DisabledChannels.create(channel_id=channel_id)
        except Exception as e:
            self.logger.error(f"Error adding disabled channel to database: {e}")
            raise
        
    async def remove_disabled_channel(self, channel_id: int) -> None:
        try:
            query = DisabledChannels.delete().where(DisabledChannels.channel_id == channel_id)
            query.execute()
        except Exception as e:
            self.logger.error(f"Error removing disabled channel from database: {e}")
            raise
            
    async def get_enabled_channels(self) -> List[int]:
        try:
            channels = EnabledChannels.select()
            return [channel.channel_id for channel in channels]
        except Exception as e:
            self.logger.error(f"Error retrieving enabled channels: {e}")
            raise
        
    async def add_enabled_channel(self, channel_id: int) -> None:
        try:
            EnabledChannels.create(channel_id=channel_id)
        except Exception as e:
            self.logger.error(f"Error adding enabled channel to database: {e}")
            raise
        
    async def remove_enabled_channel(self, channel_id: int) -> None:
        try:
            query = EnabledChannels.delete().where(EnabledChannels.channel_id == channel_id)
            query.execute()
        except Exception as e:
            self.logger.error(f"Error removing enabled channel from database: {e}")
            raise

    async def add_message(self, channel_id: int, role: str, content: str, image_url: Optional[str], message_id: Optional[int] = None) -> None:
        try:
            Message.create(
                channel_id=channel_id,
                role=role,
                content=content,
                image_url=image_url,
                message_id=message_id
            )
        except Exception as e:
            self.logger.error(f"Error adding message to database: {e}")
            raise

    async def get_channel_history(self, channel_id: int) -> List[Dict[str, str]]:
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
        try:
            query = Message.delete().where(Message.channel_id == channel_id)
            query.execute()
        except Exception as e:
            self.logger.error(f"Error clearing channel history: {e}")
            raise

    def __del__(self):
        if not db.is_closed():
            db.close()