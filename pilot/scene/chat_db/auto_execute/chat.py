from typing import Dict, Any, List
from pilot.scene.base_chat import BaseChat
from pilot.scene.base import ChatScene
from pilot.configs.config import Config
from pilot.common.sql_database import Database

CFG = Config()

class ChatWithDbAutoExecute(BaseChat):
    chat_scene: str = ChatScene.ChatWithDbExecute.value

    def __init__(self, chat_session_id, db_name, user_input, **kwargs):
        super().__init__(
            chat_mode=ChatScene.ChatWithDbExecute,
            chat_session_id=chat_session_id,
            current_user_input=user_input,
            **kwargs,
        )
        if not db_name:
            raise ValueError("Database name is required for ChatWithDbExecute scene.")
        self.db_name = db_name
        self.database: Database = CFG.local_db
        if not self.database:
            raise ConnectionError("Database connection not initialized. Check your .env file.")
        self.db_connect = self.database.get_session(self.db_name)
        self.top_k = 10

    async def generate_input_values(self) -> Dict:
        """Generates input values for the prompt template."""
        # The original implementation fetched table info here.
        # This is still a valid approach for providing context to the LLM.
        try:
            # Use the new method to get schema and foreign key info
            table_info = self.database.get_table_info_with_foreign_keys(self.db_connect)
        except Exception as e:
            print(f"Error getting table info: {e}")
            table_info = "Error retrieving database schema."

        return {
            "input": self.current_user_input,
            "top_k": str(self.top_k),
            "dialect": self.database.dialect,
            "table_info": table_info,
            "response": self.prompt_template.response_format,
        }

    async def do_with_prompt_response(self, parsed_response: Any) -> List:
        """
        Executes the SQL query parsed from the LLM response.
        """
        sql = parsed_response.sql
        return self.database.run(self.db_connect, sql)
