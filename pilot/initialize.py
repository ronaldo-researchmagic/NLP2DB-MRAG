"""
Módulo de inicialização para o DB-GPT TELA Edition.
Este módulo carrega todos os templates de prompt necessários para o funcionamento do chat.
"""

import logging
import importlib
import os
import sys
from typing import List, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar o diretório raiz ao path para importações relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar a configuração global
from pilot.configs.config import Config
from pilot.scene.base import ChatScene

# Obter a instância global de configuração
CFG = Config()

def ensure_prompt_templates_loaded() -> Dict[str, Any]:
    """
    Garante que todos os templates de prompt necessários estejam carregados.
    Esta função deve ser chamada antes de usar qualquer chat.
    
    Returns:
        Dict[str, Any]: Dicionário com os templates de prompt carregados
    """
    # Verificar se o template de chat com execução automática já está carregado
    if ChatScene.ChatWithDbExecute.value not in CFG.prompt_templates:
        logger.info(f"Carregando template de prompt para {ChatScene.ChatWithDbExecute.value}")
        try:
            # Importar o módulo de prompt para carregar o template
            importlib.import_module("pilot.scene.chat_db.auto_execute.prompt")
            logger.info(f"Template carregado com sucesso para {ChatScene.ChatWithDbExecute.value}")
        except Exception as e:
            logger.error(f"Erro ao carregar template de prompt: {e}")
    
    # Verificar se outros templates necessários estão carregados
    chat_scenes = [
        "chat_normal",
        "chat_knowledge_default",
        "chat_knowledge_custom",
        "chat_knowledge_url",
        "chat_knowledge_db_summary",
        "chat_execution",
        "chat_db_professional_qa"
    ]
    
    for scene in chat_scenes:
        try:
            module_path = f"pilot.scene.{scene}.prompt"
            importlib.import_module(module_path)
            logger.info(f"Template carregado para {scene}")
        except Exception as e:
            logger.warning(f"Não foi possível carregar template para {scene}: {e}")
    
    # Listar os templates carregados
    if CFG.prompt_templates:
        logger.info(f"Templates carregados: {list(CFG.prompt_templates.keys())}")
    else:
        logger.warning("Nenhum template de prompt foi carregado!")
    
    return CFG.prompt_templates

def initialize_app():
    """
    Inicializa a aplicação, carregando todos os componentes necessários.
    
    Returns:
        Dict[str, Any]: Dicionário com os templates de prompt carregados
    """
    logger.info("Inicializando aplicação DB-GPT TELA Edition...")
    
    # Carregar templates de prompt
    prompt_templates = ensure_prompt_templates_loaded()
    
    # Verificar se os templates essenciais foram carregados
    essential_templates = [ChatScene.ChatWithDbExecute.value, "chat_normal", "chat_execution"]
    missing_templates = [t for t in essential_templates if t not in prompt_templates]
    
    if missing_templates:
        logger.warning(f"Templates essenciais não carregados: {missing_templates}")
        logger.warning("A aplicação pode não funcionar corretamente!")
    else:
        logger.info("Todos os templates essenciais foram carregados com sucesso.")
    
    logger.info("Inicialização concluída.")
    return prompt_templates

# Executar a inicialização se este script for executado diretamente
if __name__ == "__main__":
    initialize_app()
