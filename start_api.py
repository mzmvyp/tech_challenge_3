#!/usr/bin/env python3
"""
START API - Inicializador da API
===============================

Script simples para iniciar apenas a API.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Inicia a API"""
    print("🚀 INICIANDO API PRF...")
    print("=" * 40)
    
    # Verificar se api.py existe
    if not Path("api.py").exists():
        print("❌ Arquivo api.py não encontrado!")
        return
    
    try:
        # Iniciar API
        print("📡 Iniciando API na porta 8000...")
        print("📚 Documentação: http://localhost:8000/docs")
        print("🛑 Pressione Ctrl+C para parar")
        print("=" * 40)
        
        # Executar API
        subprocess.run([sys.executable, "api.py"])
        
    except KeyboardInterrupt:
        print("\n✅ API parada pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")

if __name__ == "__main__":
    main()
