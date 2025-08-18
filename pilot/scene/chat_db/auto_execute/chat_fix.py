#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Script para corrigir o erro 'NoneType' object has no attribute 'response_format'
no chat com execução automática de SQL.
"""

import importlib
import logging
from pilot.configs.config import Config
from pilot.scene.base import ChatScene

logger = logging.getLogger(__name__)

def ensure_prompt_templates_loaded():
    """
    Garante que todos os templates de prompt necessários estejam carregados.
    Esta função deve ser chamada antes de usar qualquer chat.
    """
    CFG = Config()
    
    # Verificar se o template já está carregado
    if ChatScene.ChatWithDbExecute.value not in CFG.prompt_templates:
        logger.info(f"Carregando template de prompt para {ChatScene.ChatWithDbExecute.value}")
        try:
            # Importar o módulo de prompt para carregar o template
            importlib.import_module("pilot.scene.chat_db.auto_execute.prompt")
            logger.info(f"Template carregado com sucesso para {ChatScene.ChatWithDbExecute.value}")
        except Exception as e:
            logger.error(f"Erro ao carregar template de prompt: {e}")
            raise
    
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
            module_path = f"pilot.scene.{scene.replace('_', '_')}.prompt"
            importlib.import_module(module_path)
            logger.info(f"Template carregado para {scene}")
        except Exception as e:
            logger.warning(f"Não foi possível carregar template para {scene}: {e}")
    
    return CFG.prompt_templates
