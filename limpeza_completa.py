import os
import shutil
from pathlib import Path

def limpeza_completa():
    """
    Limpa todos os arquivos de teste e temporários
    """
    print("🧹 LIMPEZA COMPLETA DE ARQUIVOS DESNECESSÁRIOS")
    print("=" * 60)
    
    # Lista de arquivos e diretórios para remover
    arquivos_para_remover = [
        # Scripts de teste e coleta
        "limpar_e_recoletar_tudo.py",
        "limpar_tudo_e_recoletar_robusto.py",
        "verificar_carga_completa.py",
        "limpeza_completa.py",
        
        # Scripts de debug e verificação
        "debug_gravidade.py",
        "test_insert.py",
        "recreate_table.py",
        "add_columns.py",
        "check_data.py",
        "test_api.py",
        "test_dashboard.py",
        "test_swagger.py",
        "test_jwt_api.py",
        "test_api_real.py",
        "test_api_completo.py",
        "test_simple.py",
        "test_endpoint.py",
        "check_preprocessador.py",
        "teste_final_sistema.py",
        "teste_sistema_preventivo.py",
        "teste_completo_preventivo.py",
        "teste_simples_preventivo.py",
        "teste_risco_alto.py",
        "teste_sistema_completo.py",
        "teste_linguagem_natural.py",
        
        # Scripts de processamento de dados
        "processar_dados_2025.py",
        "processar_dados_2025_corrigido.py",
        "testar_validador.py",
        "corrigir_arquivo_csv.py",
        "processar_csv_robusto.py",
        "verificar_dados_incorretos.py",
        "limpar_dados_incorretos.py",
        "verificar_dados_prf_2025.py",
        "verificar_urls_corretas_prf.py",
        "verificar_site_prf_direto.py",
        "encontrar_dados_acidentes_2025.py",
        "verificar_dados_incorretos.py",
        "limpar_dados_incorretos.py",
        "verificar_dados_prf_2025.py",
        "verificar_urls_corretas_prf.py",
        "verificar_site_prf_direto.py",
        "encontrar_dados_acidentes_2025.py",
        
        # Scripts de treinamento temporários
        "treinar_modelo_simples.py",
        "treinar_modelo_real.py",
        "executar_sistema.py",
        "testar_sistema.py",
        "testar_sistema_windows.py",
        "coletar_dados_alternativo.py",
        
        # Scripts de API temporários
        "api_simples.py",
        "main_real.py",
        "src/api_predicao_real.py",
        "src/sistema_alerta_preventivo.py",
        
        # Arquivos de relatório temporários
        "relatorio_validacao.md",
        
        # Arquivos de dados temporários (se existirem)
        "data/raw/extraido/",
        "data/raw/*.csv",
        "data/raw/*.zip",
        "*.normalizado.csv",
        "*.csv",
        "*.zip"
    ]
    
    # Diretórios para remover
    diretorios_para_remover = [
        "data/raw/extraido/",
        "__pycache__/",
        "src/__pycache__/",
        "src/utils/__pycache__/",
        ".pytest_cache/",
        "data/raw/",
        "data/models/",
        "data/processed/",
        "logs/",
        "temp/",
        "tmp/"
    ]
    
    # Contadores
    arquivos_removidos = 0
    diretorios_removidos = 0
    espaco_liberado = 0
    
    print("🗑️ REMOVENDO ARQUIVOS DE TESTE...")
    print("-" * 40)
    
    # Remover arquivos
    for arquivo in arquivos_para_remover:
        try:
            if os.path.exists(arquivo):
                if os.path.isfile(arquivo):
                    tamanho = os.path.getsize(arquivo)
                    os.remove(arquivo)
                    arquivos_removidos += 1
                    espaco_liberado += tamanho
                    print(f"✅ Removido: {arquivo} ({tamanho/1024/1024:.2f} MB)")
                elif os.path.isdir(arquivo):
                    tamanho = calcular_tamanho_diretorio(arquivo)
                    shutil.rmtree(arquivo)
                    diretorios_removidos += 1
                    espaco_liberado += tamanho
                    print(f"✅ Removido diretório: {arquivo} ({tamanho/1024/1024:.2f} MB)")
        except Exception as e:
            print(f"⚠️ Erro ao remover {arquivo}: {e}")
    
    print(f"\n🗑️ REMOVENDO DIRETÓRIOS TEMPORÁRIOS...")
    print("-" * 40)
    
    # Remover diretórios
    for diretorio in diretorios_para_remover:
        try:
            if os.path.exists(diretorio):
                tamanho = calcular_tamanho_diretorio(diretorio)
                shutil.rmtree(diretorio)
                diretorios_removidos += 1
                espaco_liberado += tamanho
                print(f"✅ Removido diretório: {diretorio} ({tamanho/1024/1024:.2f} MB)")
        except Exception as e:
            print(f"⚠️ Erro ao remover diretório {diretorio}: {e}")
    
    # Limpar cache do Python
    print(f"\n🗑️ LIMPANDO CACHE DO PYTHON...")
    print("-" * 40)
    
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc"):
                try:
                    caminho_completo = os.path.join(root, file)
                    tamanho = os.path.getsize(caminho_completo)
                    os.remove(caminho_completo)
                    arquivos_removidos += 1
                    espaco_liberado += tamanho
                except Exception as e:
                    pass
        
        # Remover diretórios __pycache__
        for dir_name in dirs:
            if dir_name == "__pycache__":
                try:
                    caminho_completo = os.path.join(root, dir_name)
                    tamanho = calcular_tamanho_diretorio(caminho_completo)
                    shutil.rmtree(caminho_completo)
                    diretorios_removidos += 1
                    espaco_liberado += tamanho
                except Exception as e:
                    pass
    
    # Recriar diretórios essenciais
    print(f"\n📁 RECRIANDO DIRETÓRIOS ESSENCIAIS...")
    print("-" * 40)
    
    diretorios_essenciais = [
        "data/raw",
        "data/models",
        "data/processed",
        "logs"
    ]
    
    for diretorio in diretorios_essenciais:
        try:
            os.makedirs(diretorio, exist_ok=True)
            print(f"✅ Criado: {diretorio}/")
        except Exception as e:
            print(f"⚠️ Erro ao criar {diretorio}: {e}")
    
    # Resumo final
    print(f"\n🎉 LIMPEZA CONCLUÍDA!")
    print("=" * 60)
    print(f"📊 Arquivos removidos: {arquivos_removidos}")
    print(f"📊 Diretórios removidos: {diretorios_removidos}")
    print(f"💾 Espaço liberado: {espaco_liberado/1024/1024:.2f} MB")
    print(f"✅ Sistema limpo e organizado!")
    
    return True

def calcular_tamanho_diretorio(diretorio):
    """
    Calcula o tamanho total de um diretório
    """
    total = 0
    try:
        for root, dirs, files in os.walk(diretorio):
            for file in files:
                try:
                    total += os.path.getsize(os.path.join(root, file))
                except:
                    pass
    except:
        pass
    return total

if __name__ == "__main__":
    limpeza_completa()
