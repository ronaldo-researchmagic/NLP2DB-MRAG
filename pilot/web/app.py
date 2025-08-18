#!/usr/bin/env python3
import asyncio
import uuid
import traceback
from typing import Dict, Any, List

from nicegui import app, ui, Client

from pilot.configs.config import Config
from pilot.scene.chat_factory import ChatFactory
from pilot.scene.base import ChatScene
from pilot.language.translation_handler import get_lang_text
from pilot.utils import build_logger
from pilot.initialize import initialize_app

# --- Setup ---
CFG = Config()
logger = build_logger("web_app", "web_app.log")
CHAT_FACTORY = ChatFactory()

# --- UI State & Session Management ---
sessions: Dict[str, Dict[str, Any]] = {}

def get_session():
    """Get or create a user session."""
    session_id = app.storage.user.get('session_id')
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        app.storage.user['session_id'] = session_id
        sessions[session_id] = {
            'chat_history': [],
            'db_selector': None,
            'sql_mode': get_lang_text("sql_generate_mode_direct"),
            'temperature_val': 0.7,
            'max_tokens_val': 1024,
        }
    return sessions[session_id]

def get_dbs():
    """Get list of available databases."""
    if CFG.local_db:
        try:
            return CFG.local_db.get_database_list()
        except Exception as e:
            logger.error(f"Failed to get database list: {e}")
            return []
    return []

# --- UI Components ---
def build_header():
    with ui.header(elevated=True).classes('justify-between items-center px-4 bg-primary text-white'):
        ui.label('DB-GPT TELA Edition').classes('text-2xl font-bold')
        ui.label('Advanced NLP-to-SQL Assistant')

def build_left_drawer(dbs):
    with ui.left_drawer().classes('bg-gray-100 p-4') as left_drawer:
        ui.label('Controls').classes('text-xl font-semibold mb-4')
        
        with ui.card().classes('w-full'):
            ui.label('Database').classes('text-lg font-medium')
            session = get_session()
            session['db_selector'] = ui.select(
                dbs, 
                label='Select Database', 
                value=dbs[0] if dbs else None
            ).classes('w-full')

        with ui.card().classes('w-full mt-4'):
            ui.label('SQL Mode').classes('text-lg font-medium')
            session['sql_mode'] = ui.radio(
                [get_lang_text("sql_generate_mode_direct"), get_lang_text("sql_generate_mode_none")],
                value=get_lang_text("sql_generate_mode_direct")
            ).props('dense')

        with ui.card().classes('w-full mt-4'):
            ui.label('Parameters').classes('text-lg font-medium')
            session['temperature'] = ui.slider(
                min=0.0, max=1.0, value=0.7, step=0.1
            ).props('label-always').bind_value(session, 'temperature_val')
            ui.label().bind_text_from(session, 'temperature_val', lambda v: f'Temperature: {v:.1f}')
            
            session['max_tokens'] = ui.slider(
                min=256, max=4096, value=1024, step=256
            ).props('label-always').bind_value(session, 'max_tokens_val')
            ui.label().bind_text_from(session, 'max_tokens_val', lambda v: f'Max Tokens: {v}')

    return left_drawer

# --- Core Application Logic ---
async def handle_user_message(text_input: ui.textarea, chat_container: ui.column):
    session = get_session()
    user_message = text_input.value
    text_input.value = ''
    if not user_message.strip():
        return

    with chat_container:
        ui.chat_message(user_message, sent=True, name='You')

    try:
        chat_params = {
            "chat_session_id": app.storage.user['session_id'],
            "user_input": user_message,
            "db_name": session['db_selector'].value if session['db_selector'] else None,
            "temperature": session.get('temperature_val', 0.7),
            "max_new_tokens": session.get('max_tokens_val', 1024),
        }
        
        scene = ChatScene.ChatWithDbExecute if session['sql_mode'].value == get_lang_text("sql_generate_mode_direct") else ChatScene.ChatWithDbQA
        chat = CHAT_FACTORY.get_implementation(scene.value, **chat_params)

        with chat_container:
            response_message = ui.chat_message(name='Assistant')
            with response_message:
                spinner = ui.spinner(size='lg')

        if not chat.prompt_template.stream_out:
            final_response = await chat.nostream_call()
            spinner.delete()
            with response_message:
                ui.markdown(final_response)
        else:
            # Streaming response
            full_response = ""
            async for chunk in chat.stream_call():
                full_response += chunk
                spinner.delete()
                with response_message:
                    ui.markdown(full_response)

    except Exception as e:
        logger.error(f"Error handling message: {traceback.format_exc()}")
        with chat_container:
            ui.chat_message(f"An error occurred: {e}", name='Error', sent=False).classes('text-red-500')

@ui.page('/')
async def main_page(client: Client):
    # Initialize session on first visit
    get_session()
    
    build_header()
    dbs = get_dbs()
    if not dbs:
        ui.notification("No database connections found. Please check your configuration.", type='warning')
    
    build_left_drawer(dbs)

    with ui.column().classes('w-full h-screen justify-between p-4'):
        chat_container = ui.column().classes('w-full flex-grow overflow-y-auto')
        
        with ui.row().classes('w-full items-center p-2 bg-white'):
            text_input = ui.textarea(placeholder='Ask your database a question...').classes('flex-grow')
            send_button = ui.button(
                icon='send', 
                on_click=lambda: asyncio.create_task(handle_user_message(text_input, chat_container))
            ).props('round dense flat')

    with chat_container:
        ui.chat_message("Hello! I'm your TELA-powered SQL assistant. How can I help you today?", name='Assistant')

def main():
    """Configures and runs the NiceGUI application."""
    # Inicializar a aplicação (carregar templates de prompt)
    logger.info("Initializing application and loading prompt templates...")
    initialize_app()
    logger.info("Prompt templates loaded successfully")
    
    ui.run(
        title="DB-GPT TELA Edition",
        host="0.0.0.0",
        port=CFG.WEB_SERVER_PORT,
        storage_secret="a_very_secret_key_for_nicegui_sessions",
        reload=CFG.debug_mode
    )
