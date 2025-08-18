#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from logging.handlers import RotatingFileHandler

def build_logger(name, log_file=None, level=logging.INFO):
    """
    Constrói e configura um logger com formatação padrão.
    
    Args:
        name (str): Nome do logger
        log_file (str, optional): Caminho para o arquivo de log. Se None, apenas log para console.
        level (int, optional): Nível de log. Padrão é logging.INFO.
        
    Returns:
        logging.Logger: O logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Definir formato do log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Adicionar handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Adicionar handler para arquivo se especificado
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
