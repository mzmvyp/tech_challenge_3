#!/usr/bin/env python3
"""
START DASHBOARD - Inicializador do Dashboard
===========================================

Script simples para iniciar apenas o Dashboard.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Inicia o Dashboard"""
    print("🎨 INICIANDO DASHBOARD PRF...")
    print("=" * 40)
    
    # Verificar se dashboard_standalone.py existe
    if not Path("dashboard_standalone.py").exists():
        print("❌ Arquivo dashboard_standalone.py não encontrado!")
        return
    
    try:
        # Iniciar Dashboard
        print("📊 Iniciando Dashboard na porta 8501...")
        print("🌐 URL: http://localhost:8501")
        print("🛑 Pressione Ctrl+C para parar")
        print("=" * 40)
        
        # Executar Dashboard
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard_standalone.py", "--server.port", "8501"])
        
    except KeyboardInterrupt:
        print("\n✅ Dashboard parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar Dashboard: {e}")

if __name__ == "__main__":
    main()
