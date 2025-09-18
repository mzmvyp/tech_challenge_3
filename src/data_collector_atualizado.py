# src/data_collector_atualizado.py - Coletor atualizado para dados PRF 2025

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configurando logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ColetorDadosPRFAtualizado:
    """
    Coletor atualizado para dados de acidentes da PRF (2025)
    
    Esta classe implementa:
    1. Download dos dados atualizados da PRF
    2. Suporte para dados de 2025
    3. Tratamento de diferentes formatos (ocorrência/pessoa)
    4. Limpeza e normalização
    """
    
    def __init__(self, anos=None, diretorio_saida="data/raw"):
        """
        Inicializa o coletor
        
        Parâmetros:
        -----------
        anos : list
            Lista de anos para baixar (default: 2022-2025)
        diretorio_saida : str
            Diretório onde salvar os dados
        """
        self.anos = anos if anos else [2022, 2023, 2024, 2025]
        self.diretorio_saida = Path(diretorio_saida)
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # URLs base da PRF (estrutura atualizada)
        self.base_url = "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-acidentes"
        
        # Mapeamento de URLs por ano e tipo
        self.urls_dados = {
            # 2025
            2025: {
                'ocorrencia': f"{self.base_url}/acidentes2025_ocorrencia.csv",
                'pessoa': f"{self.base_url}/acidentes2025_pessoa.csv",
                'pessoa_completo': f"{self.base_url}/acidentes2025_pessoa_completo.csv"
            },
            # 2024
            2024: {
                'ocorrencia': f"{self.base_url}/acidentes2024_ocorrencia.csv",
                'pessoa': f"{self.base_url}/acidentes2024_pessoa.csv",
                'pessoa_completo': f"{self.base_url}/acidentes2024_pessoa_completo.csv"
            },
            # 2023
            2023: {
                'ocorrencia': f"{self.base_url}/acidentes2023_ocorrencia.csv",
                'pessoa': f"{self.base_url}/acidentes2023_pessoa.csv",
                'pessoa_completo': f"{self.base_url}/acidentes2023_pessoa_completo.csv"
            },
            # 2022
            2022: {
                'ocorrencia': f"{self.base_url}/acidentes2022_ocorrencia.csv",
                'pessoa': f"{self.base_url}/acidentes2022_pessoa.csv",
                'pessoa_completo': f"{self.base_url}/acidentes2022_pessoa_completo.csv"
            }
        }
    
    def baixar_dados_prf(self, ano, tipo='ocorrencia'):
        """
        Baixa dados de acidentes da PRF para um ano específico
        
        Parâmetros:
        -----------
        ano : int
            Ano dos dados que queremos baixar
        tipo : str
            Tipo de dados: 'ocorrencia', 'pessoa', 'pessoa_completo'
        
        Retorna:
        --------
        DataFrame com os dados de acidentes
        """
        
        if ano not in self.urls_dados:
            self.logger.error(f"Ano {ano} não suportado. Anos disponíveis: {list(self.urls_dados.keys())}")
            return None
            
        if tipo not in self.urls_dados[ano]:
            self.logger.error(f"Tipo {tipo} não disponível para {ano}. Tipos: {list(self.urls_dados[ano].keys())}")
            return None
        
        url = self.urls_dados[ano][tipo]
        
        self.logger.info(f"Baixando dados de {ano} ({tipo})...")
        self.logger.info(f"URL: {url}")
        
        try:
            # Headers para simular navegador
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/csv,application/csv,*/*',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Fazendo requisição com timeout
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Tentando diferentes encodings e separadores
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            separators = [';', ',', '\t', '|']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        # Lendo CSV com diferentes configurações
                        df = pd.read_csv(
                            url, 
                            encoding=encoding, 
                            sep=sep, 
                            decimal=',',
                            low_memory=False,
                            on_bad_lines='skip',
                            header=0
                        )
                        
                        # Verificando se tem dados válidos
                        if len(df) > 100 and len(df.columns) > 5:
                            self.logger.info(f"✅ Dados baixados: {len(df):,} registros")
                            self.logger.info(f"   Encoding: {encoding}, Separador: '{sep}'")
                            self.logger.info(f"   Colunas: {len(df.columns)}")
                            
                            # Salvando arquivo raw
                            arquivo_saida = self.diretorio_saida / f"acidentes_{ano}_{tipo}.csv"
                            df.to_csv(arquivo_saida, index=False, encoding='utf-8')
                            self.logger.info(f"💾 Salvo em: {arquivo_saida}")
                            
                            return df
                    except Exception as e:
                        continue
            
            self.logger.error(f"❌ Não foi possível ler o arquivo com nenhuma configuração")
            return None
        
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"❌ Erro HTTP ao baixar dados de {ano}: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"❌ Erro de conexão ao baixar dados de {ano}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado ao baixar dados de {ano}: {e}")
            return None

    def explorar_dados(self, df, ano, tipo):
        """
        Explora e entende completamente os dados
        """
        
        self.logger.info("="*80)
        self.logger.info(f"ESTRUTURA DOS DADOS - {ano} ({tipo.upper()})")
        self.logger.info("="*80)
        
        # 1. Dimensões
        self.logger.info(f"\n📏 Dimensões:")
        self.logger.info(f"   - Linhas (registros): {df.shape[0]:,}")
        self.logger.info(f"   - Colunas (variáveis): {df.shape[1]}")
        
        # 2. Colunas disponíveis
        self.logger.info(f"\n📋 Colunas disponíveis:")
        for i, col in enumerate(df.columns, 1):
            self.logger.info(f"   {i:2d}. {col}")
        
        # 3. Tipos de dados
        self.logger.info(f"\n🔤 Tipos de dados:")
        tipos = df.dtypes.value_counts()
        for tipo_dados, count in tipos.items():
            self.logger.info(f"   {tipo_dados}: {count} colunas")
        
        # 4. Valores ausentes
        self.logger.info(f"\n❓ Valores ausentes por coluna:")
        ausentes = df.isnull().sum()
        ausentes_pct = (ausentes / len(df)) * 100
        
        for col in df.columns:
            if ausentes[col] > 0:
                self.logger.info(f"   - {col}: {ausentes[col]:,} ({ausentes_pct[col]:.1f}%)")
        
        # 5. Análise da variável alvo (se existir)
        colunas_gravidade = [col for col in df.columns if 'gravidade' in col.lower() or 'classificacao' in col.lower() or 'vitima' in col.lower()]
        
        if colunas_gravidade:
            for col in colunas_gravidade:
                self.logger.info(f"\n🎯 Variável alvo ({col}):")
                valores = df[col].value_counts()
                for valor, count in valores.head(10).items():
                    pct = count / len(df) * 100
                    self.logger.info(f"   {valor}: {count:,} ({pct:.1f}%)")
        
        return df.head()

    def limpar_dados(self, df, ano, tipo):
        """
        Limpa e prepara os dados inicialmente
        """
        
        self.logger.info(f"🧹 INICIANDO LIMPEZA DOS DADOS - {ano} ({tipo.upper()})")
        self.logger.info("-" * 50)
        
        # Fazendo uma cópia
        df_limpo = df.copy()
        inicial = len(df_limpo)
        
        # 1. REMOVENDO DUPLICATAS
        self.logger.info("\n1️⃣ Removendo duplicatas...")
        antes = len(df_limpo)
        df_limpo = df_limpo.drop_duplicates()
        depois = len(df_limpo)
        self.logger.info(f"   Removidas: {antes - depois:,} duplicatas")
        
        # 2. TRATANDO VALORES AUSENTES
        self.logger.info("\n2️⃣ Tratando valores ausentes...")
        
        # Para variáveis categóricas: substituir por 'Não Informado'
        colunas_categoricas = df_limpo.select_dtypes(include=['object']).columns
        for col in colunas_categoricas:
            ausentes_antes = df_limpo[col].isnull().sum()
            if ausentes_antes > 0:
                df_limpo[col] = df_limpo[col].fillna('Não Informado')
                self.logger.info(f"   {col}: {ausentes_antes} valores preenchidos")
        
        # Para variáveis numéricas: substituir pela mediana
        colunas_numericas = df_limpo.select_dtypes(include=['int64', 'float64']).columns
        for col in colunas_numericas:
            ausentes_antes = df_limpo[col].isnull().sum()
            if ausentes_antes > 0:
                mediana = df_limpo[col].median()
                df_limpo[col] = df_limpo[col].fillna(mediana)
                self.logger.info(f"   {col}: {ausentes_antes} valores preenchidos com mediana {mediana:.2f}")
        
        # 3. PADRONIZANDO TEXTO
        self.logger.info("\n3️⃣ Padronizando texto...")
        for col in colunas_categoricas:
            # Remove espaços extras e converte para maiúsculas
            df_limpo[col] = df_limpo[col].astype(str).str.strip().str.upper()
        self.logger.info("   Texto padronizado para maiúsculas")
        
        # 4. VERIFICANDO A VARIÁVEL ALVO
        self.logger.info("\n4️⃣ Verificando variável alvo...")
        colunas_gravidade = [col for col in df_limpo.columns if 'gravidade' in col.lower() or 'classificacao' in col.lower() or 'vitima' in col.lower()]
        
        if colunas_gravidade:
            for col in colunas_gravidade:
                valores_unicos = df_limpo[col].unique()
                self.logger.info(f"   {col}: {len(valores_unicos)} valores únicos")
                
                # Removendo registros sem classificação
                antes = len(df_limpo)
                df_limpo = df_limpo[df_limpo[col].notna()]
                df_limpo = df_limpo[df_limpo[col] != 'NÃO INFORMADO']
                depois = len(df_limpo)
                if antes != depois:
                    self.logger.info(f"   Removidos {antes - depois} registros sem classificação válida")
        
        self.logger.info("\n✅ LIMPEZA CONCLUÍDA")
        self.logger.info(f"   Registros iniciais: {inicial:,}")
        self.logger.info(f"   Registros finais: {len(df_limpo):,}")
        self.logger.info(f"   Registros removidos: {inicial - len(df_limpo):,} ({(inicial - len(df_limpo))/inicial*100:.1f}%)")
        
        return df_limpo

    def coletar_todos_os_anos(self):
        """
        Coleta dados de todos os anos especificados
        """
        
        self.logger.info("🚀 INICIANDO COLETA COMPLETA - DADOS ATUALIZADOS PRF")
        self.logger.info("="*80)
        
        todos_dados = []
        
        for ano in self.anos:
            self.logger.info(f"\n📅 Processando ano {ano}...")
            
            # Tentando diferentes tipos de dados
            tipos_para_tentar = ['ocorrencia', 'pessoa', 'pessoa_completo']
            df_ano = None
            
            for tipo in tipos_para_tentar:
                self.logger.info(f"   Tentando tipo: {tipo}")
                
                # Verificar se já existe
                arquivo_existente = self.diretorio_saida / f"acidentes_{ano}_{tipo}.csv"
                
                if arquivo_existente.exists():
                    self.logger.info(f"   📁 Arquivo já existe, carregando: {arquivo_existente}")
                    try:
                        df = pd.read_csv(arquivo_existente, encoding='utf-8')
                        self.logger.info(f"   ✅ Carregado: {len(df):,} registros")
                    except Exception as e:
                        self.logger.error(f"   ❌ Erro ao carregar arquivo existente: {e}")
                        df = self.baixar_dados_prf(ano, tipo)
                else:
                    df = self.baixar_dados_prf(ano, tipo)
                
                if df is not None and len(df) > 0:
                    df_ano = df
                    self.logger.info(f"   ✅ Sucesso com tipo: {tipo}")
                    break
                else:
                    self.logger.warning(f"   ⚠️ Falha com tipo: {tipo}")
            
            if df_ano is not None:
                # Explorar dados
                self.explorar_dados(df_ano, ano, tipo)
                
                # Limpar dados
                df_limpo = self.limpar_dados(df_ano, ano, tipo)
                
                # Salvar versão limpa
                arquivo_limpo = self.diretorio_saida / f"acidentes_{ano}_{tipo}_limpo.csv"
                df_limpo.to_csv(arquivo_limpo, index=False, encoding='utf-8')
                self.logger.info(f"   💾 Versão limpa salva: {arquivo_limpo}")
                
                todos_dados.append(df_limpo)
            else:
                self.logger.error(f"   ❌ Falha ao obter dados de {ano}")
        
        # Combinando todos os anos
        if todos_dados:
            self.logger.info("\n🔗 COMBINANDO TODOS OS ANOS...")
            dados_completos = pd.concat(todos_dados, ignore_index=True)
            
            self.logger.info(f"📊 ESTATÍSTICAS FINAIS:")
            self.logger.info(f"   Total de registros: {len(dados_completos):,}")
            self.logger.info(f"   Período: {min(self.anos)} a {max(self.anos)}")
            self.logger.info(f"   Colunas: {len(dados_completos.columns)}")
            
            # Salvando arquivo combinado
            arquivo_combinado = self.diretorio_saida / "acidentes_reais_combinados.csv"
            dados_completos.to_csv(arquivo_combinado, index=False, encoding='utf-8')
            self.logger.info(f"   💾 Arquivo combinado salvo: {arquivo_combinado}")
            
            # Estatísticas por gravidade (se existir)
            colunas_gravidade = [col for col in dados_completos.columns if 'gravidade' in col.lower() or 'classificacao' in col.lower() or 'vitima' in col.lower()]
            
            if colunas_gravidade:
                for col in colunas_gravidade:
                    self.logger.info(f"\n📈 DISTRIBUIÇÃO POR GRAVIDADE ({col}):")
                    distribuicao = dados_completos[col].value_counts()
                    for gravidade, count in distribuicao.head(10).items():
                        pct = count / len(dados_completos) * 100
                        self.logger.info(f"   {gravidade}: {count:,} ({pct:.1f}%)")
            
            return dados_completos
        else:
            self.logger.error("❌ Nenhum dado foi coletado com sucesso")
            return None

def main():
    """
    Função principal para executar a coleta
    """
    print("🚨 SISTEMA DE PREVISÃO DE GRAVIDADE DE ACIDENTES - PRF ATUALIZADO")
    print("="*80)
    print("📥 Iniciando coleta de dados atualizados...")
    print("📅 Dados disponíveis: 2022, 2023, 2024, 2025")
    print("📊 Tipos: Ocorrência, Pessoa, Pessoa Completo")
    
    # Criando coletor
    coletor = ColetorDadosPRFAtualizado(anos=[2022, 2023, 2024, 2025])
    
    # Executando coleta
    dados = coletor.coletar_todos_os_anos()
    
    if dados is not None:
        print("\n✅ COLETA CONCLUÍDA COM SUCESSO!")
        print(f"📊 Total de registros coletados: {len(dados):,}")
        print(f"💾 Dados salvos em: data/raw/")
        print("\n🔄 Próximo passo: Treinar o modelo")
        print("   python treinar_modelo.py")
    else:
        print("\n❌ ERRO NA COLETA DE DADOS")
        print("   Verifique sua conexão com a internet")
        print("   Verifique se as URLs da PRF estão funcionando")

if __name__ == "__main__":
    main()
