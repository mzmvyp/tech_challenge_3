# main.py - Sistema de Previsão de Gravidade de Acidentes em Rodovias Federais

import subprocess
import sys
import time
import requests
from pathlib import Path

def verificar_dependencias():
    """
    Verifica se as dependências estão instaladas
    """
    print("🔍 Verificando dependências...")
    
    dependencias = ['pandas', 'numpy', 'sklearn', 'requests', 'fastapi', 'uvicorn', 'streamlit']
    faltando = []
    
    for dep in dependencias:
        try:
            __import__(dep)
        except ImportError:
            faltando.append(dep)
    
    if faltando:
        print(f"❌ Dependências faltando: {faltando}")
        print("📦 Execute: pip install -r requirements.txt")
        return False
    
    print("✅ Todas as dependências estão instaladas")
    return True

def verificar_modelo():
    """
    Verifica se o modelo está treinado
    """
    print("🤖 Verificando modelo...")
    
    arquivos_modelo = [
        "data/models/modelo_acidentes.pkl",
        "data/models/scaler_acidentes.pkl",
        "data/models/feature_info.pkl"
    ]
    
    for arquivo in arquivos_modelo:
        if not Path(arquivo).exists():
            print(f"❌ Modelo não encontrado: {arquivo}")
            print("📊 Execute: python treinar_modelo.py")
            return False
    
    print("✅ Modelo treinado encontrado")
    return True

def iniciar_api():
    """
    Inicia a API FastAPI
    """
    print("🚀 Iniciando API...")
    try:
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.api_predicao:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Aguardar API inicializar
        print("⏳ Aguardando API inicializar...")
        time.sleep(5)
        
        # Testar se está funcionando com múltiplas tentativas
        max_tentativas = 10
        for tentativa in range(max_tentativas):
            try:
                response = requests.get("http://localhost:8000/", timeout=3)
                if response.status_code == 200:
                    print("✅ API iniciada: http://localhost:8000")
                    print("📚 Documentação: http://localhost:8000/docs")
                    return True
                else:
                    print(f"⏳ Tentativa {tentativa + 1}/{max_tentativas} - Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"⏳ Tentativa {tentativa + 1}/{max_tentativas} - Aguardando...")
                time.sleep(2)
        
        print("❌ API não conseguiu inicializar após 10 tentativas")
        return False
            
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")
        return False

def iniciar_dashboard():
    """
    Inicia o dashboard Streamlit
    """
    print("📊 Iniciando dashboard...")
    try:
        subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "src/dashboard.py", 
            "--server.port", "8501"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Aguardar dashboard inicializar
        time.sleep(5)
        
        # Testar se está funcionando
        response = requests.get("http://localhost:8501/", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard iniciado: http://localhost:8501")
            return True
        else:
            print("❌ Erro ao iniciar dashboard")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao iniciar dashboard: {e}")
        return False

def treinar_modelo():
    """
    Treina o modelo se necessário
    """
    print("🤖 Treinando modelo...")
    try:
        result = subprocess.run([
            sys.executable, "treinar_modelo.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Modelo treinado com sucesso")
            return True
        else:
            print(f"❌ Erro no treinamento: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao treinar modelo: {e}")
        return False

def main():
    """
    Função principal
    """
    print("🚨 SISTEMA DE PREVISÃO DE GRAVIDADE DE ACIDENTES")
    print("="*60)
    
    # Verificar dependências
    if not verificar_dependencias():
        return
    
    # Verificar modelo
    if not verificar_modelo():
        print("\n🔄 Treinando modelo...")
        if not treinar_modelo():
            print("❌ Falha no treinamento do modelo")
            return
    
    # Iniciar serviços
    print("\n🚀 Iniciando serviços...")
    
    api_ok = iniciar_api()
    dashboard_ok = iniciar_dashboard()
    
    if api_ok and dashboard_ok:
        print("\n✅ SISTEMA INICIADO COM SUCESSO!")
        print("="*60)
        print("🌐 Dashboard: http://localhost:8501")
        print("🔗 API: http://localhost:8000")
        print("📚 Documentação: http://localhost:8000/docs")
        print("\n💡 Pressione Ctrl+C para parar os serviços")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Parando serviços...")
            print("✅ Sistema finalizado")
            
    else:
        print("\n❌ ERRO AO INICIAR SISTEMA")
        if not api_ok:
            print("   - API não iniciou corretamente")
        if not dashboard_ok:
            print("   - Dashboard não iniciou corretamente")

if __name__ == "__main__":
    main()
