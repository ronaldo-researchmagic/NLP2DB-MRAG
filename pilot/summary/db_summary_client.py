import json
import uuid
import asyncio
import importlib
from typing import List
from pilot.configs.config import Config
from pilot.scene.base import ChatScene
from pilot.source_embedding.string_embedding import StringEmbedding
from pilot.summary.mysql_db_summary import MysqlSummary
from pilot.utils import build_logger

logger = build_logger("DBSummaryClient", "db_summary_client.log")
CFG = Config()

class DBSummaryClient:
    """Client for creating and querying database summaries."""

    async def get_db_summary(self, dbname: str, query: str, topk: int) -> str:
        """Get a summary of the database schema relevant to the query."""
        # This method would typically involve embedding the query and finding
        # relevant table summaries from a vector store.
        # For now, we'll simulate by getting a full summary.
        if CFG.local_db:
            db_summary_client = MysqlSummary(dbname)
            return db_summary_client.get_summery()
        return "Database not connected."

    async def _get_llm_response(self, query: str, db_input: str, dbsummary: str) -> List[str]:
        """Uses an internal chat scene to determine relevant tables from a summary."""
        chat_param = {
            "chat_session_id": str(uuid.uuid4()),
            "user_input": query,
            "db_select": db_input,
            "db_summary": dbsummary,
        }
        # Importar dinamicamente para evitar importação circular
        ChatFactory = importlib.import_module('pilot.scene.chat_factory').ChatFactory
        chat = ChatFactory.get_implementation(ChatScene.InnerChatDBSummary.value, **chat_param)
        response_text = await chat.nostream_call()
        try:
            # The view response might be markdown, so we parse the underlying AI message
            ai_message = next(m.content for m in chat.current_message.messages if m.type == 'ai')
            return json.loads(ai_message).get("table", [])
        except (json.JSONDecodeError, StopIteration) as e:
            logger.error(f"Failed to get tables from LLM response: {e}")
            return []
