"""
Script para iniciar apenas o Dashboard do Sistema de Prevenção de Acidentes PRF
"""

import sys
import os
import logging
from pathlib import Path
import subprocess

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verificar_dependencias():
    """Verifica dependências essenciais para o dashboard"""
    dependencias = {
        'streamlit': 'streamlit',
        'plotly': 'plotly',
        'folium': 'folium',
        'requests': 'requests',
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

def verificar_api():
    """Verifica se a API está rodando"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API está rodando")
            return True
        else:
            logger.warning("⚠️ API não está respondendo corretamente")
            return False
    except Exception as e:
        logger.warning(f"⚠️ API não está acessível: {e}")
        return False

def main():
    """Inicia apenas o Dashboard"""
    logger.info("📊 INICIANDO DASHBOARD - SISTEMA DE PREVENÇÃO DE ACIDENTES PRF")
    logger.info("=" * 70)
    
    # Verificar dependências
    if not verificar_dependencias():
        logger.error("❌ Dependências não satisfeitas")
        return
    
    # Verificar API
    api_ok = verificar_api()
    if not api_ok:
        logger.warning("⚠️ API não está rodando. Inicie a API primeiro com: python iniciar_api.py")
    
    # Iniciar dashboard
    try:
        logger.info("✅ Iniciando Dashboard Streamlit...")
        logger.info("🌐 Dashboard será aberto em: http://localhost:8501")
        logger.info("🛑 Pressione Ctrl+C para parar")
        logger.info("=" * 70)
        
        # Iniciar streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "src/dashboard/app_expandido.py",
            "--server.port", "8501",
            "--server.address", "127.0.0.1",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Dashboard parado pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
