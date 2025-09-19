"""
Script para iniciar apenas a API do Sistema de Prevenção de Acidentes PRF

Este script evita problemas de porta/socket iniciando apenas a API
"""

import sys
import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verificar_dependencias():
    """Verifica dependências essenciais"""
    dependencias = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'sklearn': 'sklearn',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    for nome, modulo in dependencias.items():
        try:
            __import__(modulo)
            logger.info(f"✅ {nome}")
        except ImportError:
            logger.error(f"❌ {nome}")
            return False
    
    return True

def verificar_modelo():
    """Verifica se o modelo existe"""
    caminho_modelo = Path('data/models/accident_risk_model.pkl')
    if caminho_modelo.exists():
        tamanho = caminho_modelo.stat().st_size / 1024 / 1024
        logger.info(f"✅ Modelo encontrado: {tamanho:.2f} MB")
        return True
    else:
        logger.warning("⚠️ Modelo não encontrado - sistema funcionará com regras")
        return False

def main():
    """Inicia apenas a API"""
    logger.info("🚀 INICIANDO API - SISTEMA DE PREVENÇÃO DE ACIDENTES PRF")
    logger.info("=" * 60)
    
    # Verificar dependências
    if not verificar_dependencias():
        logger.error("❌ Dependências não satisfeitas")
        return
    
    # Verificar modelo
    modelo_ok = verificar_modelo()
    
    # Importar e iniciar API
    try:
        import uvicorn
        from src.api.main import app
        
        logger.info("✅ API carregada com sucesso")
        logger.info("📚 Documentação: http://localhost:8000/docs")
        logger.info("🛑 Pressione Ctrl+C para parar")
        logger.info("=" * 60)
        
        # Iniciar servidor
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            reload=False
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
