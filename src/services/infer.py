from openai import AsyncOpenAI
import chromadb
from chromadb.config import Settings
import uuid
from typing import *
from decouple import config

from utils.models import ReasoningModel
from utils.get_prompt import generate_system_prompt

class OpenAI:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=config('OPENAI_API_KEY'))
        self.chroma_client = chromadb.PersistentClient(path="./db", settings=Settings(anonymized_telemetry=False))
        self.collection = self.chroma_client.get_or_create_collection(name="memory")
        
    async def retrieve_memory(self, query: str) -> str:
        response = await self.client.embeddings.create(
            model=config('OPENAI_EMBEDDING_MODEL'),
            input=query
        )
        results = self.collection.query(
            query_embeddings=[response.data[0].embedding],
            n_results=1
        )
        if len(results['documents'][0]) < 1:
            return "Memory not found."
        
        return results['documents'][0][0]
    
    async def store_memory(self, memory: str) -> str:
        response = await self.client.embeddings.create(
            model=config('OPENAI_EMBEDDING_MODEL'),
            input=memory
        )
        self.collection.add(
            ids=[uuid.uuid4().hex],
            embeddings=[response.data[0].embedding],
            documents=[memory]
        )
        
        return "Memory stored successfully."
        
    async def generate_response(self, messages: List[Dict[str, str]]) -> ReasoningModel:
        response = await self.client.beta.chat.completions.parse(
            model=config('OPENAI_MODEL'),
            messages=messages,
            response_format=ReasoningModel
        )
        
        return response.choices[0].message.parsed