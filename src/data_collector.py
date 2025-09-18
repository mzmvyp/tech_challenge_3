# src/data_collector.py

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

class ColetorDadosPRF:
    """
    Classe para coletar dados de acidentes da PRF
    
    Esta classe implementa:
    1. Download automático dos dados
    2. Limpeza inicial
    3. Salvamento em formato estruturado
    """
    
    def __init__(self, anos=None, diretorio_saida="data/raw"):
        """
        Inicializa o coletor
        
        Parâmetros:
        -----------
        anos : list
            Lista de anos para baixar (default: 2022-2024)
        diretorio_saida : str
            Diretório onde salvar os dados
        """
        self.anos = anos if anos else [2022, 2023, 2024]
        self.diretorio_saida = Path(diretorio_saida)
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def baixar_dados_prf(self, ano):
        """
        Baixa dados de acidentes da PRF para um ano específico
        
        Parâmetros:
        -----------
        ano : int
            Ano dos dados que queremos baixar (2007 a 2024)
        
        Retorna:
        --------
        DataFrame com os dados de acidentes
        """
        
        # URL padrão dos dados da PRF
        url = f"https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-acidentes/acidentes{ano}.csv"
        
        self.logger.info(f"Baixando dados de {ano}...")
        self.logger.info(f"URL: {url}")
        
        try:
            # Baixa o arquivo CSV diretamente para um DataFrame
            # encoding='latin1' porque os dados da PRF usam essa codificação
            df = pd.read_csv(url, encoding='latin1', sep=';', decimal=',')
            self.logger.info(f"✅ Dados baixados: {len(df):,} acidentes registrados")
            
            # Salvando arquivo raw
            arquivo_saida = self.diretorio_saida / f"acidentes_{ano}.csv"
            df.to_csv(arquivo_saida, index=False, encoding='utf-8')
            self.logger.info(f"💾 Salvo em: {arquivo_saida}")
            
            return df
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao baixar dados de {ano}: {e}")
            return None

    def explorar_dados(self, df):
        """
        Explora e entende completamente os dados
        """
        
        self.logger.info("="*80)
        self.logger.info("ESTRUTURA DOS DADOS")
        self.logger.info("="*80)
        
        # 1. Dimensões
        self.logger.info(f"\n📏 Dimensões:")
        self.logger.info(f"   - Linhas (acidentes): {df.shape[0]:,}")
        self.logger.info(f"   - Colunas (variáveis): {df.shape[1]}")
        
        # 2. Colunas disponíveis
        self.logger.info(f"\n📋 Colunas disponíveis:")
        for i, col in enumerate(df.columns, 1):
            self.logger.info(f"   {i:2d}. {col}")
        
        # 3. Tipos de dados
        self.logger.info(f"\n🔤 Tipos de dados:")
        tipos = df.dtypes.value_counts()
        for tipo, count in tipos.items():
            self.logger.info(f"   {tipo}: {count} colunas")
        
        # 4. Valores ausentes
        self.logger.info(f"\n❓ Valores ausentes por coluna:")
        ausentes = df.isnull().sum()
        ausentes_pct = (ausentes / len(df)) * 100
        
        for col in df.columns:
            if ausentes[col] > 0:
                self.logger.info(f"   - {col}: {ausentes[col]:,} ({ausentes_pct[col]:.1f}%)")
        
        # 5. Análise da variável alvo
        if 'classificacao_acidente' in df.columns:
            self.logger.info(f"\n🎯 Variável alvo (classificacao_acidente):")
            valores = df['classificacao_acidente'].value_counts()
            for valor, count in valores.items():
                pct = count / len(df) * 100
                self.logger.info(f"   {valor}: {count:,} ({pct:.1f}%)")
        
        return df.head()

    def limpar_dados(self, df):
        """
        Limpa e prepara os dados inicialmente
        """
        
        self.logger.info("🧹 INICIANDO LIMPEZA DOS DADOS")
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
        if 'classificacao_acidente' in df_limpo.columns:
            valores_unicos = df_limpo['classificacao_acidente'].unique()
            self.logger.info(f"   Valores encontrados: {valores_unicos}")
            
            # Removendo registros sem classificação
            antes = len(df_limpo)
            df_limpo = df_limpo[df_limpo['classificacao_acidente'].notna()]
            df_limpo = df_limpo[df_limpo['classificacao_acidente'] != 'NÃO INFORMADO']
            depois = len(df_limpo)
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
        
        self.logger.info("🚀 INICIANDO COLETA COMPLETA")
        self.logger.info("="*80)
        
        todos_dados = []
        
        for ano in self.anos:
            self.logger.info(f"\n📅 Processando ano {ano}...")
            
            # Verificar se já existe
            arquivo_existente = self.diretorio_saida / f"acidentes_{ano}.csv"
            
            if arquivo_existente.exists():
                self.logger.info(f"   📁 Arquivo já existe, carregando: {arquivo_existente}")
                try:
                    df = pd.read_csv(arquivo_existente, encoding='utf-8')
                    self.logger.info(f"   ✅ Carregado: {len(df):,} registros")
                except Exception as e:
                    self.logger.error(f"   ❌ Erro ao carregar arquivo existente: {e}")
                    df = self.baixar_dados_prf(ano)
            else:
                df = self.baixar_dados_prf(ano)
            
            if df is not None:
                # Explorar dados
                self.explorar_dados(df)
                
                # Limpar dados
                df_limpo = self.limpar_dados(df)
                
                # Salvar versão limpa
                arquivo_limpo = self.diretorio_saida / f"acidentes_{ano}_limpo.csv"
                df_limpo.to_csv(arquivo_limpo, index=False, encoding='utf-8')
                self.logger.info(f"   💾 Versão limpa salva: {arquivo_limpo}")
                
                todos_dados.append(df_limpo)
        
        # Combinando todos os anos
        if todos_dados:
            self.logger.info("\n🔗 COMBINANDO TODOS OS ANOS...")
            dados_completos = pd.concat(todos_dados, ignore_index=True)
            
            self.logger.info(f"📊 ESTATÍSTICAS FINAIS:")
            self.logger.info(f"   Total de acidentes: {len(dados_completos):,}")
            self.logger.info(f"   Período: {min(self.anos)} a {max(self.anos)}")
            
            # Salvando arquivo combinado
            arquivo_combinado = self.diretorio_saida / "acidentes_combinados.csv"
            dados_completos.to_csv(arquivo_combinado, index=False, encoding='utf-8')
            self.logger.info(f"   💾 Arquivo combinado salvo: {arquivo_combinado}")
            
            # Estatísticas por gravidade
            if 'classificacao_acidente' in dados_completos.columns:
                self.logger.info(f"\n📈 DISTRIBUIÇÃO POR GRAVIDADE:")
                distribuicao = dados_completos['classificacao_acidente'].value_counts()
                for gravidade, count in distribuicao.items():
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
    print("🚨 SISTEMA DE PREVISÃO DE GRAVIDADE DE ACIDENTES - PRF")
    print("="*80)
    print("📥 Iniciando coleta de dados...")
    
    # Criando coletor
    coletor = ColetorDadosPRF(anos=[2022, 2023, 2024])
    
    # Executando coleta
    dados = coletor.coletar_todos_os_anos()
    
    if dados is not None:
        print("\n✅ COLETA CONCLUÍDA COM SUCESSO!")
        print(f"📊 Total de registros coletados: {len(dados):,}")
        print(f"💾 Dados salvos em: data/raw/")
        print("\n🔄 Próximo passo: Executar o preprocessamento")
        print("   python src/preprocessing.py")
    else:
        print("\n❌ ERRO NA COLETA DE DADOS")
        print("   Verifique sua conexão com a internet")
        print("   Verifique se as URLs da PRF estão funcionando")

if __name__ == "__main__":
    main()
