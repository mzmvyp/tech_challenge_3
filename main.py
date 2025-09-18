# main.py - Sistema de Alerta Preventivo de Acidentes em Rodovias Federais

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
        "data/models/scaler_acidentes.pkl"
    ]
    
    for arquivo in arquivos_modelo:
        if not Path(arquivo).exists():
            print(f"❌ Modelo não encontrado: {arquivo}")
            print("📊 Execute: python src/train_model_mysql.py")
            return False
    
    print("✅ Modelo de análise de risco encontrado")
    return True

def verificar_api_rodando():
    """
    Verifica se a API já está rodando
    """
    for port in range(8000, 8011):
        try:
            response = requests.get(f"http://localhost:{port}/", timeout=1)
            if response.status_code == 200:
                print(f"🔍 API encontrada na porta {port}")
                return port
        except requests.exceptions.RequestException as e:
            print(f"🔍 Porta {port}: {type(e).__name__}")
            continue
    print("🔍 Nenhuma API encontrada")
    return None

def iniciar_api():
    """
    Inicia a API FastAPI
    """
    print("🚀 Iniciando API...")
    
    # Primeiro verificar se já está rodando
    print("🔍 Verificando se API já está rodando...")
    porta_existente = verificar_api_rodando()
    if porta_existente:
        print(f"✅ API já está rodando na porta {porta_existente}")
        print(f"📚 Documentação: http://localhost:{porta_existente}/docs")
        return True
    
    try:
        print("🚀 Iniciando nova instância da API...")
        # Iniciar nova instância da API
        processo = subprocess.Popen([
            sys.executable, "src/api_alerta_preventivo.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Processo iniciado com PID: {processo.pid}")
        
        # Aguardar API inicializar com verificações mais frequentes
        print("⏳ Aguardando API inicializar...")
        time.sleep(3)  # Tempo inicial menor
        
        # Testar se está funcionando com verificações mais frequentes
        max_tentativas = 20
        for tentativa in range(max_tentativas):
            print(f"🔍 Tentativa {tentativa + 1}/{max_tentativas} - Verificando API...")
            porta_encontrada = verificar_api_rodando()
            if porta_encontrada:
                print(f"✅ API iniciada com sucesso: http://localhost:{porta_encontrada}")
                print(f"📚 Documentação: http://localhost:{porta_encontrada}/docs")
                return True
            
            # Verificar se o processo ainda está rodando
            if processo.poll() is not None:
                print(f"❌ Processo da API terminou inesperadamente (código: {processo.returncode})")
                stdout, stderr = processo.communicate()
                if stdout:
                    print(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
                if stderr:
                    print(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
                return False
            
            print(f"⏳ Aguardando mais 1 segundo...")
            time.sleep(1)
        
        # Se chegou aqui, falhou
        print("❌ API não conseguiu inicializar após 20 tentativas")
        processo.terminate()
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
        # Verificar se dashboard já está rodando
        try:
            response = requests.get("http://localhost:8501/", timeout=2)
            if response.status_code == 200:
                print("✅ Dashboard já está rodando: http://localhost:8501")
                return True
        except:
            pass
        
        # Iniciar novo dashboard
        processo = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "src/dashboard.py", 
            "--server.port", "8501",
            "--server.headless", "true"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Processo dashboard iniciado com PID: {processo.pid}")
        
        # Aguardar dashboard inicializar com verificações
        print("⏳ Aguardando dashboard inicializar...")
        time.sleep(3)
        
        # Testar se está funcionando com múltiplas tentativas
        max_tentativas = 10
        for tentativa in range(max_tentativas):
            try:
                response = requests.get("http://localhost:8501/", timeout=3)
                if response.status_code == 200:
                    print("✅ Dashboard iniciado: http://localhost:8501")
                    return True
            except requests.exceptions.RequestException as e:
                print(f"🔍 Tentativa {tentativa + 1}/{max_tentativas} - {type(e).__name__}")
            
            # Verificar se processo ainda está rodando
            if processo.poll() is not None:
                print(f"❌ Processo dashboard terminou (código: {processo.returncode})")
                stdout, stderr = processo.communicate()
                if stderr:
                    print(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
                return False
            
            time.sleep(1)
        
        print("❌ Dashboard não conseguiu inicializar")
        processo.terminate()
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
    print("🚨 SISTEMA DE ALERTA PREVENTIVO DE ACIDENTES")
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
