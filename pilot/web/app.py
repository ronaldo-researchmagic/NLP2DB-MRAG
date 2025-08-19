#!/usr/bin/env python3
import asyncio
import uuid
import traceback
import json
from typing import Dict, Any, List

from nicegui import app, ui, Client
import plotly.graph_objects as go

from pilot.configs.config import Config
from pilot.scene.chat_factory import ChatFactory
from pilot.scene.base import ChatScene
from pilot.language.translation_handler import get_lang_text
from pilot.utils import build_logger
import sys

# Set console encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from pilot.initialize import initialize_app

# --- Setup ---
CFG = Config()
logger = build_logger("web_app", "web_app.log")
CHAT_FACTORY = ChatFactory()

# --- UI State & Session Management ---
sessions: Dict[str, Dict[str, Any]] = {}

# Store the current language in a global variable that can be modified
current_language = CFG.LANGUAGE

def change_language(language: str):
    """Change the application language and refresh the UI."""
    global current_language
    # Update the global language variable
    current_language = language
    # Update the config language (this won't persist after restart)
    CFG.LANGUAGE = language
    # Show notification to the user
    language_names = {
        'en': 'English',
        'pt': 'Português',
       
    }
    ui.notify(f"Language changed to {language_names.get(language, language)}", type='positive')
    # Refresh the page to apply changes
    ui.open('/', new_tab=False)

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
            ui.label('Language / Idioma').classes('text-lg font-medium')
            session = get_session()
            # Create a simple dictionary mapping for display labels
            language_labels = {
                'en': 'English',
                'pt': 'Português',

            }
            
            # Create simple list of language codes
            language_options = ['en', 'pt']
            
            # Use the language code directly as the value
            session['language_selector'] = ui.select(
                options={code: language_labels[code] for code in language_options},
                value=current_language if current_language in language_options else 'en',
                on_change=lambda e: change_language(e.value)
            ).classes('w-full')
        
        with ui.card().classes('w-full mt-4'):
            ui.label('Database').classes('text-lg font-medium')
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
                # Process the response to extract chart data if present
                chart_data = extract_chart_data(final_response)
                if chart_data:
                    # Remove the chart data div from the response
                    final_response = remove_chart_data_div(final_response)
                    ui.markdown(final_response)
                    # Display the chart
                    display_chart(chart_data)
                else:
                    ui.markdown(final_response)
        else:
            # Streaming response
            full_response = ""
            async for chunk in chat.stream_call():
                full_response += chunk
                spinner.delete()
                # Process the response to extract chart data if present
                chart_data = extract_chart_data(full_response)
                if chart_data:
                    # Remove the chart data div from the response
                    clean_response = remove_chart_data_div(full_response)
                    with response_message:
                        ui.markdown(clean_response)
                        # Display the chart
                        display_chart(chart_data)
                else:
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

    # Estrutura principal com layout fixo
    with ui.column().classes('w-full h-screen flex flex-col'):
        # Área de chat com scroll
        chat_container = ui.column().classes('w-full flex-grow overflow-y-auto p-4')
        
        # Função para processar o envio da mensagem
        def send_message():
            if text_input.value.strip():  # Só envia se tiver texto
                asyncio.create_task(handle_user_message(text_input, chat_container))
        
        # Área de input fixada na parte inferior
        with ui.row().classes('w-full items-center p-2 bg-white sticky bottom-0 shadow-lg'):
            # Cria um campo de input
            text_input = ui.input(placeholder=get_lang_text('ask_database_placeholder')).classes('flex-grow')
            
            # Adiciona evento de tecla usando JavaScript diretamente
            ui.add_body_html("""
            <script>
            document.addEventListener('keydown', function(event) {
                const activeElement = document.activeElement;
                // Verifica se o elemento ativo é um input e se a tecla é Enter
                if (activeElement.tagName === 'INPUT' && event.key === 'Enter') {
                    // Aciona o botão de envio
                    const sendButton = document.querySelector('button[title="send"]');
                    if (sendButton) {
                        sendButton.click();
                        event.preventDefault();
                    }
                }
            });
            </script>
            """)
            
            send_button = ui.button(
                icon='send', 
                on_click=lambda: send_message()
            ).props('round dense flat title="send"')

    with chat_container:
        welcome_messages = {
            "en": "Hello! I'm your TELA-powered SQL assistant. How can I help you today?",
            "pt": "Olá! Sou seu assistente SQL com tecnologia TELA. Como posso ajudá-lo hoje?",

        }
        welcome_message = welcome_messages.get(current_language, welcome_messages["en"])
        ui.chat_message(welcome_message, name='Assistant')

def extract_chart_data(response: str) -> Dict:
    """Extract chart data from the response if present."""
    import re
    import html
    
    # Debug the response content
    logger.info(f"Checking response for chart data, length: {len(response)}")
    
    # Look for the chart data div
    chart_match = re.search(r"<div id='chart-data'.*?data-chart='(.*?)'></div>", response)
    if chart_match:
        try:
            # Extract and unescape the chart JSON
            chart_json = chart_match.group(1)
            logger.info(f"Found chart data, length: {len(chart_json)}")
            
            # Unescape HTML entities
            unescaped_json = html.unescape(chart_json)
            
            # Parse the JSON
            chart_data = json.loads(unescaped_json)
            logger.info("Successfully parsed chart JSON")
            return chart_data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding chart JSON: {e}")
            # Log a sample of the problematic JSON for debugging
            sample = chart_json[:100] + '...' if len(chart_json) > 100 else chart_json
            logger.error(f"JSON sample: {sample}")
    else:
        logger.info("No chart data found in response")
    return None

def remove_chart_data_div(response: str) -> str:
    """Remove the chart data div from the response."""
    import re
    return re.sub(r"<div id='chart-data'.*?</div>", "", response)

def display_chart(chart_data: Dict):
    """Display a Plotly chart from the provided chart data."""
    try:
        # Create a card for the chart
        with ui.card().classes('w-full chart-container'):
            ui.label("Chart Visualization").classes('text-lg font-medium')
            # Create a Plotly figure from the JSON data
            fig = go.Figure(**chart_data)
            # Display the figure
            ui.plotly(fig).classes('w-full h-64')
    except Exception as e:
        logger.error(f"Error displaying chart: {e}")
        ui.label(f"Error displaying chart: {str(e)}").classes('text-red-500')

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
