"""
Sistema de Prevenção de Acidentes PRF - Main

Sistema simplificado que usa modelo treinado com dados reais da PRF
para PREVENIR acidentes, não prever gravidade.
"""

import subprocess
import sys
import time
import os
import logging
from pathlib import Path
import signal
import socket

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verificar_dependencias() -> bool:
    """Verifica se todas as dependências estão instaladas"""
    logger.info("🔍 Verificando dependências...")
    
    # Mapeamento de dependências para nomes de módulos
    dependencias = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn', 
        'streamlit': 'streamlit',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'scikit-learn': 'sklearn',
        'requests': 'requests',
        'python-dotenv': 'dotenv',
        'joblib': 'joblib'
    }
    
    dependencias_faltando = []
    
    for nome_dep, modulo in dependencias.items():
        try:
            __import__(modulo)
            logger.info(f"✅ {nome_dep}")
        except ImportError:
            dependencias_faltando.append(nome_dep)
            logger.error(f"❌ {nome_dep}")
    
    if dependencias_faltando:
        logger.error(f"Dependências faltando: {', '.join(dependencias_faltando)}")
        logger.info("Execute: pip install -r requirements.txt")
        return False
    
    logger.info("✅ Todas as dependências estão instaladas")
    return True


def verificar_modelo() -> bool:
    """Verifica se o modelo treinado existe"""
    logger.info("🤖 Verificando modelo treinado...")
    
    caminho_modelo = Path('data/models/accident_risk_model.pkl')
    
    if caminho_modelo.exists():
        tamanho = caminho_modelo.stat().st_size / 1024 / 1024  # MB
        logger.info(f"✅ Modelo encontrado: {tamanho:.2f} MB")
        return True
    else:
        logger.warning("⚠️ Modelo não encontrado")
        logger.info("💡 Execute: python src/train_pipeline.py para treinar o modelo")
        return False


def encontrar_porta_livre(porta_inicial: int, max_tentativas: int = 10) -> int:
    """Encontra uma porta livre"""
    import socket
    
    for i in range(max_tentativas):
        porta = porta_inicial + i
        try:
            # Tentar bind na porta
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', porta))
                s.listen(1)
                logger.info(f"✅ Porta {porta} disponível")
                return porta
        except (OSError, PermissionError) as e:
            logger.warning(f"⚠️ Porta {porta} ocupada: {e}")
            continue
    
    # Se não encontrar porta livre, usar uma porta aleatória
    import random
    porta_aleatoria = random.randint(8000, 8999)
    logger.warning(f"⚠️ Usando porta aleatória: {porta_aleatoria}")
    return porta_aleatoria


def iniciar_api() -> subprocess.Popen:
    """Inicia a API FastAPI"""
    logger.info("🚀 Iniciando API...")
    
    porta = encontrar_porta_livre(8000)
    
    try:
        comando = [
            sys.executable, '-m', 'uvicorn',
            'src.api.main:app',
            '--host', '127.0.0.1',
            '--port', str(porta),
            '--reload',
            '--log-level', 'warning'
        ]
        
        processo = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Aguardar inicialização
        time.sleep(5)
        
        if processo.poll() is None:
            logger.info(f"✅ API iniciada na porta {porta}")
            logger.info(f"📚 Documentação: http://localhost:{porta}/docs")
            return processo
        else:
            # Capturar erro
            stdout, stderr = processo.communicate()
            logger.error(f"❌ Erro ao iniciar API: {stderr}")
            raise RuntimeError(f"Falha ao iniciar API: {stderr}")
            
    except Exception as e:
        logger.error(f"❌ Erro crítico ao iniciar API: {e}")
        raise


def iniciar_dashboard() -> subprocess.Popen:
    """Inicia o Dashboard Streamlit"""
    logger.info("📊 Iniciando Dashboard...")
    
    porta = encontrar_porta_livre(8501)
    
    try:
        comando = [
            sys.executable, '-m', 'streamlit', 'run',
            'src/dashboard/app_expandido.py',
            '--server.port', str(porta),
            '--server.address', '127.0.0.1',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false',
            '--logger.level', 'error'
        ]
        
        processo = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Aguardar inicialização
        time.sleep(7)
        
        if processo.poll() is None:
            logger.info(f"✅ Dashboard iniciado na porta {porta}")
            logger.info(f"🌐 Interface: http://localhost:{porta}")
            return processo
        else:
            # Capturar erro
            stdout, stderr = processo.communicate()
            logger.error(f"❌ Erro ao iniciar Dashboard: {stderr}")
            raise RuntimeError(f"Falha ao iniciar Dashboard: {stderr}")
            
    except Exception as e:
        logger.error(f"❌ Erro crítico ao iniciar Dashboard: {e}")
        raise


def main():
    """Função principal"""
    logger.info("🛡️ SISTEMA DE PREVENÇÃO DE ACIDENTES PRF")
    logger.info("=" * 60)
    
    # Configurar handler para Ctrl+C
    def signal_handler(sig, frame):
        logger.info("\n🛑 Parando sistema...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 1. Verificar dependências
        if not verificar_dependencias():
            logger.error("❌ Dependências não satisfeitas")
            sys.exit(1)
        
        # 2. Verificar modelo
        modelo_ok = verificar_modelo()
        
        # 3. Treinar modelo se necessário
        if not modelo_ok:
            logger.info("🤖 Treinando modelo com dados sintéticos...")
            try:
                subprocess.run([sys.executable, 'src/train_pipeline.py'], check=True)
                logger.info("✅ Modelo treinado com sucesso")
                modelo_ok = True
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Erro no treinamento: {e}")
                logger.info("💡 Sistema funcionará com regras básicas")
        
        # 4. Iniciar API
        processo_api = iniciar_api()
        
        # 5. Iniciar Dashboard
        processo_dashboard = iniciar_dashboard()
        
        # 6. Mostrar resumo
        logger.info("\n" + "=" * 60)
        logger.info("🎉 SISTEMA INICIADO COM SUCESSO!")
        logger.info("=" * 60)
        logger.info(f"🤖 Modelo ML: {'✅ Carregado' if modelo_ok else '⚠️ Usando regras'}")
        logger.info("📚 URLs importantes:")
        logger.info("   • Documentação API: http://localhost:8000/docs")
        logger.info("   • Interface Web: http://localhost:8501")
        logger.info("   • Health Check: http://localhost:8000/health")
        logger.info("\n🛑 Para parar o sistema: Ctrl+C")
        logger.info("=" * 60)
        
        # 7. Aguardar interrupção
        try:
            while True:
                time.sleep(1)
                
                # Verificar se os processos ainda estão rodando
                if processo_api.poll() is not None:
                    logger.error("❌ API parou inesperadamente")
                    break
                if processo_dashboard.poll() is not None:
                    logger.error("❌ Dashboard parou inesperadamente")
                    break
                    
        except KeyboardInterrupt:
            logger.info("\n🛑 Parando sistema...")
        
        # 8. Parar processos
        try:
            processo_api.terminate()
            processo_dashboard.terminate()
            processo_api.wait(timeout=5)
            processo_dashboard.wait(timeout=5)
            logger.info("✅ Sistema finalizado com sucesso")
        except:
            processo_api.kill()
            processo_dashboard.kill()
            logger.info("🔪 Processos forçados a parar")
        
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()