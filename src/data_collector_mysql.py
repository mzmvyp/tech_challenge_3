# src/data_collector_mysql.py - Coletor de dados com persistência MySQL

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Importando o gerenciador de banco
from .database import DatabaseManager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ColetorDadosPRFMySQL:
    """
    Coletor de dados da PRF com persistência em MySQL
    
    Esta classe implementa:
    1. Download dos dados da PRF
    2. Limpeza e preprocessamento
    3. Persistência no banco MySQL
    4. Verificação de dados duplicados
    """
    
    def __init__(self, anos=None, diretorio_saida="data/raw"):
        """
        Inicializa o coletor
        
        Parâmetros:
        -----------
        anos : list
            Lista de anos para baixar (default: 2022-2024)
        diretorio_saida : str
            Diretório onde salvar os dados CSV (backup)
        """
        self.anos = anos if anos else [2022, 2023, 2024]  # Apenas anos com dados reais
        self.diretorio_saida = Path(diretorio_saida)
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Inicializando gerenciador de banco
        self.db = DatabaseManager()
        
        # URLs base da PRF (estrutura atualizada)
        self.base_url = "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-acidentes"
        
        # Mapeamento de URLs por ano e tipo
        self.urls_dados = {
            2025: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq'
            },
            2024: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq'
            },
            2023: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq'
            },
            2022: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1YjQqJqJqJqJqJqJqJqJqJqJqJqJqJqJq'
            }
        }
    
    def baixar_dados_prf(self, ano, tipo='ocorrencia'):
        """
        Baixa dados da PRF para um ano específico
        
        Parâmetros:
        -----------
        ano : int
            Ano dos dados
        tipo : str
            Tipo de dados (ocorrencia, pessoa, pessoa_completo)
            
        Returns:
        --------
        pd.DataFrame ou None : DataFrame com os dados ou None se erro
        """
        self.logger.info(f"📥 Baixando dados {ano} - {tipo}...")
        
        # Verificando se temos URL para este ano/tipo
        if ano not in self.urls_dados or tipo not in self.urls_dados[ano]:
            self.logger.warning(f"   ⚠️ URL não disponível para {ano} - {tipo}")
            return None
        
        url = self.urls_dados[ano][tipo]
        
        try:
            # Tentando diferentes encodings e separadores
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            separators = [';', ',', '\t']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        self.logger.info(f"   Tentando encoding: {encoding}, separador: '{sep}'")
                        
                        df = pd.read_csv(
                            url, 
                            encoding=encoding, 
                            sep=sep, 
                            decimal=',',
                            low_memory=False,
                            on_bad_lines='skip'
                        )
                        
                        if len(df) > 0:
                            self.logger.info(f"   ✅ Sucesso com encoding: {encoding}, separador: '{sep}'")
                            self.logger.info(f"   📊 Dados carregados: {len(df):,} registros")
                            return df
                            
                    except Exception as e:
                        self.logger.debug(f"   ❌ Falha com encoding: {encoding}, separador: '{sep}' - {e}")
                        continue
            
            self.logger.error(f"   ❌ Não foi possível ler o arquivo com nenhuma configuração")
            return None
            
        except Exception as e:
            self.logger.error(f"   ❌ Erro ao baixar dados: {e}")
            return None
    
    def limpar_dados(self, df, ano, tipo):
        """
        Limpa e padroniza os dados
        
        Parâmetros:
        -----------
        df : pd.DataFrame
            DataFrame com dados brutos
        ano : int
            Ano dos dados
        tipo : str
            Tipo dos dados
            
        Returns:
        --------
        pd.DataFrame : DataFrame limpo
        """
        self.logger.info(f"🧹 Limpando dados {ano} - {tipo}...")
        
        df_limpo = df.copy()
        inicial = len(df_limpo)
        
        # 1. Removendo duplicatas
        self.logger.info("   Removendo duplicatas...")
        antes = len(df_limpo)
        df_limpo = df_limpo.drop_duplicates()
        depois = len(df_limpo)
        self.logger.info(f"   Removidas: {antes - depois:,} duplicatas")
        
        # 2. Tratando valores ausentes
        self.logger.info("   Tratando valores ausentes...")
        
        # Para variáveis categóricas
        colunas_categoricas = df_limpo.select_dtypes(include=['object']).columns
        for col in colunas_categoricas:
            ausentes_antes = df_limpo[col].isnull().sum()
            df_limpo[col] = df_limpo[col].fillna('Não Informado')
            if ausentes_antes > 0:
                self.logger.info(f"   {col}: {ausentes_antes} valores preenchidos")
        
        # Para variáveis numéricas
        colunas_numericas = df_limpo.select_dtypes(include=['int64', 'float64']).columns
        for col in colunas_numericas:
            ausentes_antes = df_limpo[col].isnull().sum()
            if ausentes_antes > 0:
                mediana = df_limpo[col].median()
                df_limpo[col] = df_limpo[col].fillna(mediana)
                self.logger.info(f"   {col}: {ausentes_antes} valores preenchidos com mediana {mediana:.2f}")
        
        # 3. Padronizando texto
        self.logger.info("   Padronizando texto...")
        for col in colunas_categoricas:
            df_limpo[col] = df_limpo[col].str.strip().str.upper()
        
        # 4. Verificando coluna de classificação
        if 'classificacao_acidente' in df_limpo.columns:
            self.logger.info("   Verificando classificação de acidentes...")
            valores_unicos = df_limpo['classificacao_acidente'].unique()
            self.logger.info(f"   Valores encontrados: {valores_unicos}")
            
            # Removendo registros sem classificação
            antes = len(df_limpo)
            df_limpo = df_limpo[df_limpo['classificacao_acidente'].notna()]
            depois = len(df_limpo)
            self.logger.info(f"   Removidos {antes - depois} registros sem classificação")
        
        # 5. Adicionando metadados
        df_limpo['ano_coleta'] = ano
        df_limpo['tipo_dados'] = tipo
        df_limpo['data_coleta'] = datetime.now()
        
        self.logger.info(f"   Registros iniciais: {inicial:,}")
        self.logger.info(f"   Registros finais: {len(df_limpo):,}")
        self.logger.info(f"   Registros removidos: {inicial - len(df_limpo):,} ({(inicial - len(df_limpo))/inicial*100:.1f}%)")
        
        return df_limpo
    
    def verificar_duplicatas_banco(self, df, ano):
        """
        Verifica se os dados já existem no banco
        
        Parâmetros:
        -----------
        df : pd.DataFrame
            DataFrame para verificar
        ano : int
            Ano dos dados
            
        Returns:
        --------
        pd.DataFrame : DataFrame sem duplicatas do banco
        """
        if not self.db.connection or not self.db.connection.is_connected():
            return df
        
        try:
            # Buscando dados existentes do ano
            df_existente = self.db.buscar_acidentes(filtros={'ano_coleta': ano})
            
            if len(df_existente) == 0:
                self.logger.info(f"   ✅ Nenhum dado existente para {ano}")
                return df
            
            self.logger.info(f"   📊 Encontrados {len(df_existente):,} registros existentes para {ano}")
            
            # Removendo duplicatas baseado em campos chave
            campos_chave = ['data_inversa', 'horario', 'uf', 'br', 'km', 'municipio']
            
            # Criando chave composta para comparação
            df['chave'] = df[campos_chave].astype(str).agg('|'.join, axis=1)
            df_existente['chave'] = df_existente[campos_chave].astype(str).agg('|'.join, axis=1)
            
            # Removendo registros que já existem
            antes = len(df)
            df_novo = df[~df['chave'].isin(df_existente['chave'])]
            depois = len(df_novo)
            
            self.logger.info(f"   ✅ Removidas {antes - depois:,} duplicatas do banco")
            self.logger.info(f"   📊 {depois:,} registros novos para inserir")
            
            return df_novo.drop('chave', axis=1)
            
        except Exception as e:
            self.logger.error(f"   ❌ Erro ao verificar duplicatas: {e}")
            return df
    
    def coletar_todos_os_anos(self):
        """
        Coleta dados de todos os anos especificados e salva no MySQL
        """
        self.logger.info("🚀 INICIANDO COLETA COMPLETA - DADOS PRF + MYSQL")
        self.logger.info("="*80)
        
        # Conectando ao banco
        if not self.db.conectar():
            self.logger.error("❌ Falha ao conectar ao banco de dados")
            return None
        
        # Criando tabelas se necessário
        if not self.db.criar_tabelas():
            self.logger.error("❌ Falha ao criar tabelas")
            return None
        
        todos_dados = []
        total_inseridos = 0
        
        for ano in self.anos:
            self.logger.info(f"\n📅 Processando ano {ano}...")
            
            # Tentando diferentes tipos de dados
            tipos_para_tentar = ['ocorrencia', 'pessoa', 'pessoa_completo']
            df_ano = None
            
            for tipo in tipos_para_tentar:
                self.logger.info(f"   Tentando tipo: {tipo}")
                
                # Verificar se já existe no banco
                df_existente = self.db.buscar_acidentes(filtros={'ano_coleta': ano})
                if len(df_existente) > 0:
                    self.logger.info(f"   ✅ Dados de {ano} já existem no banco ({len(df_existente):,} registros)")
                    df_ano = df_existente
                    break
                
                # Baixando dados
                df = self.baixar_dados_prf(ano, tipo)
                
                if df is not None and len(df) > 0:
                    # Limpando dados
                    df_limpo = self.limpar_dados(df, ano, tipo)
                    
                    # Verificando duplicatas no banco
                    df_sem_duplicatas = self.verificar_duplicatas_banco(df_limpo, ano)
                    
                    if len(df_sem_duplicatas) > 0:
                        # Inserindo no banco
                        if self.db.inserir_acidentes(df_sem_duplicatas):
                            self.logger.info(f"   ✅ {len(df_sem_duplicatas):,} registros inseridos no banco")
                            total_inseridos += len(df_sem_duplicatas)
                            
                            # Salvando backup CSV
                            arquivo_backup = self.diretorio_saida / f"acidentes_{ano}_{tipo}_backup.csv"
                            df_sem_duplicatas.to_csv(arquivo_backup, index=False, encoding='utf-8')
                            self.logger.info(f"   💾 Backup salvo: {arquivo_backup}")
                        
                        df_ano = df_sem_duplicatas
                        break
                    else:
                        self.logger.info(f"   ⚠️ Nenhum registro novo para {ano} - {tipo}")
                else:
                    self.logger.warning(f"   ⚠️ Falha ao baixar dados para {ano} - {tipo}")
            
            if df_ano is not None:
                todos_dados.append(df_ano)
                self.logger.info(f"   ✅ Ano {ano} processado com sucesso")
            else:
                self.logger.error(f"   ❌ Falha ao processar ano {ano}")
        
        # Combinando todos os dados
        if todos_dados:
            self.logger.info(f"\n📊 COMBINANDO DADOS DE TODOS OS ANOS...")
            dados_combinados = pd.concat(todos_dados, ignore_index=True)
            
            # Salvando arquivo combinado
            arquivo_combinado = self.diretorio_saida / "acidentes_prf_todos_anos_combinados.csv"
            dados_combinados.to_csv(arquivo_combinado, index=False, encoding='utf-8')
            
            self.logger.info(f"✅ COLETA CONCLUÍDA COM SUCESSO!")
            self.logger.info(f"📊 Total de registros: {len(dados_combinados):,}")
            self.logger.info(f"💾 Dados salvos no MySQL: {total_inseridos:,} registros")
            self.logger.info(f"💾 Backup CSV: {arquivo_combinado}")
            
            # Obtendo estatísticas do banco
            stats = self.db.obter_estatisticas_gerais()
            if stats:
                self.logger.info(f"\n📈 ESTATÍSTICAS DO BANCO:")
                self.logger.info(f"   Total de acidentes: {stats.get('total_acidentes', 0):,}")
                self.logger.info(f"   Período: {stats.get('periodo_dados', {}).get('data_inicio', 'N/A')} a {stats.get('periodo_dados', {}).get('data_fim', 'N/A')}")
            
            self.db.desconectar()
            return dados_combinados
        else:
            self.logger.error("❌ Nenhum dado foi coletado com sucesso")
            self.db.desconectar()
            return None

def main():
    """
    Função principal para executar a coleta
    """
    print("🚨 SISTEMA DE PREVISÃO DE GRAVIDADE DE ACIDENTES - PRF + MYSQL")
    print("="*80)
    print("📥 Iniciando coleta de dados com persistência MySQL...")
    
    # Criando coletor
    coletor = ColetorDadosPRFMySQL(anos=[2022, 2023, 2024])  # Apenas anos com dados reais
    
    # Executando coleta
    dados = coletor.coletar_todos_os_anos()
    
    if dados is not None:
        print("\n✅ COLETA CONCLUÍDA COM SUCESSO!")
        print(f"📊 Total de registros: {len(dados):,}")
        print(f"💾 Dados salvos no MySQL")
        print(f"💾 Backup CSV em: data/raw/")
        print("\n🔄 Próximo passo: Executar o treinamento dos modelos")
        print("   python src/train_model_mysql.py")
    else:
        print("\n❌ ERRO NA COLETA DE DADOS")
        print("   Verifique sua conexão com a internet")
        print("   Verifique se o XAMPP está rodando")
        print("   Verifique se o banco 'machineL' existe")

if __name__ == "__main__":
    main()

