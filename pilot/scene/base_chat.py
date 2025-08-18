import datetime
import json
import traceback
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator

from pilot.configs.config import Config
from pilot.llm_providers.tela_provider import TelaLLMProvider
from pilot.memory.chat_history.mem_history import MemHistoryMemory
from pilot.prompts.prompt_new import PromptTemplate
from pilot.scene.base_message import (ViewMessage, HumanMessage, AIMessage)
from pilot.scene.message import OnceConversation
from pilot.utils import build_logger

logger = build_logger("BaseChat", "BaseChat.log")
CFG = Config()

class BaseChat(ABC):
    chat_scene: str = None
    llm_provider: TelaLLMProvider

    def __init__(
        self,
        chat_mode,
        chat_session_id,
        current_user_input,
        temperature=None,
        max_new_tokens=None,
        **kwargs,
    ):
        self.chat_session_id = chat_session_id
        self.chat_mode = chat_mode
        self.current_user_input = current_user_input
        self.llm_provider = TelaLLMProvider()
        self.memory = MemHistoryMemory(chat_session_id)
        self.prompt_template: PromptTemplate = CFG.prompt_templates.get(self.chat_mode.value)
        
        self.history_message: List[OnceConversation] = self.memory.messages()
        self.current_message: OnceConversation = OnceConversation()
        
        self.temperature = temperature if temperature is not None else CFG.temperature
        self.max_new_tokens = max_new_tokens if max_new_tokens is not None else 2048
        self.chat_retention_rounds = 4

    @abstractmethod
    async def generate_input_values(self) -> Dict[str, Any]:
        """Generate the specific input values for the prompt template."""
        pass

    def get_history_messages(self) -> List[Dict[str, str]]:
        """Construct a message list from history for the TELA API."""
        messages = []
        rounds_to_include = self.history_message[-self.chat_retention_rounds:]
        for conversation in rounds_to_include:
            for msg in conversation.messages:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})
        return messages

    async def stream_call(self) -> AsyncGenerator[str, None]:
        """Stream call to the TELA provider."""
        self.current_message.add_user_message(self.current_user_input)
        
        messages = self.get_history_messages()
        
        # Add the current user input
        messages.append({"role": "user", "content": self.current_user_input})
        
        # Add system prompt if available
        if self.prompt_template and self.prompt_template.template_define:
            messages.insert(0, {"role": "system", "content": self.prompt_template.template_define})
        
        ai_response_text = ""
        try:
            async for chunk in self.llm_provider.generate_stream(messages, self.temperature, self.max_new_tokens):
                ai_response_text += chunk
                yield chunk
            
            self.current_message.add_ai_message(ai_response_text)
            self.memory.append(self.current_message)
        except Exception as e:
            logger.error(f"stream_call error: {traceback.format_exc()}")
            yield f"Error in stream call: {e}"

    async def nostream_call(self) -> str:
        """Non-streaming call to the TELA provider."""
        self.current_message.add_user_message(self.current_user_input)
        
        input_values = await self.generate_input_values()
        
        # Format the final prompt using the scene's template
        prompt = self.prompt_template.format(**input_values)
        
        messages = self.get_history_messages()
        messages.append({"role": "user", "content": prompt})

        # Add system prompt if available
        if self.prompt_template and self.prompt_template.template_define:
            messages.insert(0, {"role": "system", "content": self.prompt_template.template_define})

        try:
            response_text = await self.llm_provider.generate(messages, self.temperature, self.max_new_tokens)
            
            self.current_message.add_ai_message(response_text)
            
            # Use the output parser from the prompt template
            parsed_response = self.prompt_template.output_parser.parse_prompt_response(response_text)
            
            # Let the specific scene handle the parsed response
            final_result = await self.do_with_prompt_response(parsed_response)
            
            # Generate a user-facing view message
            view_message_content = self.prompt_template.output_parser.parse_view_response(
                parsed_response, 
                final_result
            )
            self.current_message.add_view_message(view_message_content)
            
            self.memory.append(self.current_message)
            return view_message_content
        except Exception as e:
            logger.error(f"nostream_call error: {traceback.format_exc()}")
            view_content = f"<span style='color:red'>**An error occurred:**</span>\n\n```\n{e}\n```"
            self.current_message.add_view_message(view_content)
            self.memory.append(self.current_message)
            return view_content

    async def do_with_prompt_response(self, parsed_response: Any) -> Any:
        """
        Abstract method for scenes to process the parsed LLM response.
        This is where SQL execution or command execution would happen.
        """
        # Default implementation returns the parsed response itself.
        return parsed_response
