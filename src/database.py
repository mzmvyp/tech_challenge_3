# src/database.py - Sistema de Banco de Dados MySQL

import mysql.connector
from mysql.connector import Error
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
import os
from typing import Optional, List, Dict, Any
import sqlalchemy
from sqlalchemy import create_engine, text

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Gerenciador de banco de dados MySQL para o sistema de acidentes PRF
    """
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 3306,
                 database: str = "machineL",
                 user: str = "machineL",
                 password: str = "machineL"):
        """
        Inicializa o gerenciador de banco de dados
        
        Parâmetros:
        -----------
        host : str
            Host do MySQL (default: localhost)
        port : int
            Porta do MySQL (default: 3306)
        database : str
            Nome do banco de dados (default: machineL)
        user : str
            Usuário do MySQL (default: machineL)
        password : str
            Senha do MySQL (default: machineL)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.engine = None
        
    def conectar(self) -> bool:
        """
        Conecta ao banco de dados MySQL
        
        Returns:
        --------
        bool : True se conectou com sucesso, False caso contrário
        """
        try:
            # Conexão direta com mysql-connector
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            # Engine SQLAlchemy para pandas
            connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
            self.engine = create_engine(connection_string, echo=False)
            
            logger.info(f"✅ Conectado ao MySQL: {self.host}:{self.port}/{self.database}")
            return True
            
        except Error as e:
            logger.error(f"❌ Erro ao conectar ao MySQL: {e}")
            return False
    
    def desconectar(self):
        """
        Desconecta do banco de dados
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("🔌 Desconectado do MySQL")
    
    def criar_tabelas(self) -> bool:
        """
        Cria as tabelas necessárias no banco de dados
        
        Returns:
        --------
        bool : True se criou com sucesso, False caso contrário
        """
        if not self.connection or not self.connection.is_connected():
            logger.error("❌ Não conectado ao banco de dados")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Tabela principal de acidentes
            create_acidentes_sql = """
            CREATE TABLE IF NOT EXISTS acidentes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data_inversa DATE,
                dia_semana VARCHAR(20),
                horario TIME,
                uf VARCHAR(2),
                br INT,
                km DECIMAL(10,2),
                municipio VARCHAR(100),
                tipo_ocorrencia VARCHAR(100),
                causa_acidente VARCHAR(200),
                tipo_veiculo VARCHAR(100),
                condicao_metereologica VARCHAR(50),
                tipo_pista VARCHAR(50),
                tracado_via VARCHAR(50),
                pessoas INT,
                veiculos INT,
                classificacao_acidente VARCHAR(50),
                gravidade_numerica INT,
                ano_coleta INT,
                tipo_dados VARCHAR(50),
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_data (data_inversa),
                INDEX idx_uf (uf),
                INDEX idx_br (br),
                INDEX idx_gravidade (gravidade_numerica),
                INDEX idx_ano_coleta (ano_coleta),
                INDEX idx_data_coleta (data_coleta)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # Tabela de estatísticas do modelo
            create_modelo_stats_sql = """
            CREATE TABLE IF NOT EXISTS modelo_estatisticas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome_modelo VARCHAR(100),
                acuracia DECIMAL(5,4),
                precisao DECIMAL(5,4),
                recall DECIMAL(5,4),
                f1_score DECIMAL(5,4),
                data_treinamento TIMESTAMP,
                total_amostras INT,
                parametros JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # Tabela de predições
            create_predicoes_sql = """
            CREATE TABLE IF NOT EXISTS predicoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                dados_entrada JSON,
                gravidade_prevista INT,
                gravidade_nome VARCHAR(50),
                probabilidades JSON,
                confianca DECIMAL(5,4),
                fatores_risco JSON,
                recomendacoes JSON,
                modelo_usado VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_gravidade_prevista (gravidade_prevista),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # Executando criação das tabelas
            cursor.execute(create_acidentes_sql)
            cursor.execute(create_modelo_stats_sql)
            cursor.execute(create_predicoes_sql)
            
            self.connection.commit()
            cursor.close()
            
            logger.info("✅ Tabelas criadas com sucesso")
            return True
            
        except Error as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            return False
    
    def inserir_acidentes(self, df: pd.DataFrame) -> bool:
        """
        Insere dados de acidentes no banco
        
        Parâmetros:
        -----------
        df : pd.DataFrame
            DataFrame com dados de acidentes
            
        Returns:
        --------
        bool : True se inseriu com sucesso, False caso contrário
        """
        if not self.engine:
            logger.error("❌ Engine SQLAlchemy não disponível")
            return False
        
        try:
            # Mapeamento de gravidade para números
            mapa_gravidade = {
                'SEM VÍTIMAS': 0,
                'ILESO': 0,
                'FERIDOS LEVES': 1,
                'FERIDOS': 1,
                'FERIDOS GRAVES': 2,
                'ÓBITOS': 3,
                'MORTOS': 3
            }
            
            # Adicionando coluna de gravidade numérica
            if 'classificacao_acidente' in df.columns:
                df['gravidade_numerica'] = df['classificacao_acidente'].map(mapa_gravidade)
            
            # Renomeando colunas para corresponder ao schema
            df_renamed = df.rename(columns={
                'tipo_de_ocorrencia': 'tipo_ocorrencia',
                'causa_acidente': 'causa_acidente',
                'tipo_veiculo': 'tipo_veiculo',
                'condicao_metereologica': 'condicao_metereologica',
                'tipo_pista': 'tipo_pista',
                'tracado_via': 'tracado_via'
            })
            
            # Inserindo dados
            df_renamed.to_sql(
                'acidentes', 
                self.engine, 
                if_exists='append', 
                index=False,
                method='multi',
                chunksize=1000
            )
            
            logger.info(f"✅ {len(df)} registros inseridos na tabela acidentes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir acidentes: {e}")
            return False
    
    def buscar_acidentes(self, 
                        limit: Optional[int] = None,
                        filtros: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Busca acidentes do banco de dados
        
        Parâmetros:
        -----------
        limit : int, optional
            Limite de registros
        filtros : dict, optional
            Filtros para aplicar na busca
            
        Returns:
        --------
        pd.DataFrame : DataFrame com os acidentes
        """
        if not self.engine:
            logger.error("❌ Engine SQLAlchemy não disponível")
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM acidentes"
            
            # Aplicando filtros
            if filtros:
                conditions = []
                for campo, valor in filtros.items():
                    if isinstance(valor, list):
                        conditions.append(f"{campo} IN {tuple(valor)}")
                    else:
                        conditions.append(f"{campo} = '{valor}'")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Ordenando por data
            query += " ORDER BY data_inversa DESC"
            
            # Aplicando limite
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ {len(df)} registros carregados do banco")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar acidentes: {e}")
            return pd.DataFrame()
    
    def salvar_estatisticas_modelo(self, 
                                  nome_modelo: str,
                                  acuracia: float,
                                  precisao: float,
                                  recall: float,
                                  f1_score: float,
                                  total_amostras: int,
                                  parametros: Dict[str, Any]) -> bool:
        """
        Salva estatísticas de um modelo no banco
        
        Parâmetros:
        -----------
        nome_modelo : str
            Nome do modelo
        acuracia : float
            Acurácia do modelo
        precisao : float
            Precisão do modelo
        recall : float
            Recall do modelo
        f1_score : float
            F1-Score do modelo
        total_amostras : int
            Total de amostras de treinamento
        parametros : dict
            Parâmetros do modelo
            
        Returns:
        --------
        bool : True se salvou com sucesso, False caso contrário
        """
        if not self.engine:
            logger.error("❌ Engine SQLAlchemy não disponível")
            return False
        
        try:
            import json
            
            stats_data = {
                'nome_modelo': nome_modelo,
                'acuracia': acuracia,
                'precisao': precisao,
                'recall': recall,
                'f1_score': f1_score,
                'data_treinamento': datetime.now(),
                'total_amostras': total_amostras,
                'parametros': json.dumps(parametros)
            }
            
            df_stats = pd.DataFrame([stats_data])
            df_stats.to_sql('modelo_estatisticas', self.engine, if_exists='append', index=False)
            
            logger.info(f"✅ Estatísticas do modelo {nome_modelo} salvas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar estatísticas: {e}")
            return False
    
    def salvar_predicao(self, 
                       dados_entrada: Dict[str, Any],
                       gravidade_prevista: int,
                       gravidade_nome: str,
                       probabilidades: Dict[str, float],
                       confianca: float,
                       fatores_risco: List[str],
                       recomendacoes: List[str],
                       modelo_usado: str) -> bool:
        """
        Salva uma predição no banco
        
        Parâmetros:
        -----------
        dados_entrada : dict
            Dados de entrada da predição
        gravidade_prevista : int
            Gravidade prevista (0-3)
        gravidade_nome : str
            Nome da gravidade prevista
        probabilidades : dict
            Probabilidades para cada classe
        confianca : float
            Confiança da predição
        fatores_risco : list
            Lista de fatores de risco
        recomendacoes : list
            Lista de recomendações
        modelo_usado : str
            Nome do modelo usado
            
        Returns:
        --------
        bool : True se salvou com sucesso, False caso contrário
        """
        if not self.engine:
            logger.error("❌ Engine SQLAlchemy não disponível")
            return False
        
        try:
            import json
            
            predicao_data = {
                'dados_entrada': json.dumps(dados_entrada),
                'gravidade_prevista': gravidade_prevista,
                'gravidade_nome': gravidade_nome,
                'probabilidades': json.dumps(probabilidades),
                'confianca': confianca,
                'fatores_risco': json.dumps(fatores_risco),
                'recomendacoes': json.dumps(recomendacoes),
                'modelo_usado': modelo_usado
            }
            
            df_pred = pd.DataFrame([predicao_data])
            df_pred.to_sql('predicoes', self.engine, if_exists='append', index=False)
            
            logger.info(f"✅ Predição salva no banco")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar predição: {e}")
            return False
    
    def obter_estatisticas_gerais(self) -> Dict[str, Any]:
        """
        Obtém estatísticas gerais do banco de dados
        
        Returns:
        --------
        dict : Estatísticas gerais
        """
        if not self.engine:
            logger.error("❌ Engine SQLAlchemy não disponível")
            return {}
        
        try:
            stats = {}
            
            # Total de acidentes
            total_acidentes = pd.read_sql("SELECT COUNT(*) as total FROM acidentes", self.engine)
            stats['total_acidentes'] = total_acidentes['total'].iloc[0]
            
            # Distribuição por gravidade
            gravidade_dist = pd.read_sql("""
                SELECT gravidade_numerica, COUNT(*) as quantidade 
                FROM acidentes 
                GROUP BY gravidade_numerica 
                ORDER BY gravidade_numerica
            """, self.engine)
            stats['distribuicao_gravidade'] = gravidade_dist.to_dict('records')
            
            # Acidentes por estado
            uf_dist = pd.read_sql("""
                SELECT uf, COUNT(*) as quantidade 
                FROM acidentes 
                GROUP BY uf 
                ORDER BY quantidade DESC 
                LIMIT 10
            """, self.engine)
            stats['top_estados'] = uf_dist.to_dict('records')
            
            # Período dos dados
            periodo = pd.read_sql("""
                SELECT 
                    MIN(data_inversa) as data_inicio,
                    MAX(data_inversa) as data_fim
                FROM acidentes
            """, self.engine)
            stats['periodo_dados'] = periodo.to_dict('records')[0]
            
            logger.info("✅ Estatísticas gerais obtidas")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}

def testar_conexao():
    """
    Função para testar a conexão com o banco
    """
    print("🔍 Testando conexão com MySQL...")
    
    db = DatabaseManager()
    
    if db.conectar():
        print("✅ Conexão estabelecida com sucesso!")
        
        # Criando tabelas
        if db.criar_tabelas():
            print("✅ Tabelas criadas/verificadas com sucesso!")
        else:
            print("❌ Erro ao criar tabelas")
        
        # Testando inserção
        df_teste = pd.DataFrame({
            'data_inversa': ['2024-01-01'],
            'dia_semana': ['SEGUNDA'],
            'horario': ['10:30:00'],
            'uf': ['SP'],
            'br': [101],
            'km': [150.5],
            'municipio': ['TESTE'],
            'tipo_ocorrencia': ['COLISÃO'],
            'causa_acidente': ['VELOCIDADE'],
            'tipo_veiculo': ['AUTOMÓVEL'],
            'condicao_metereologica': ['SOL'],
            'tipo_pista': ['DUPLA'],
            'tracado_via': ['RETA'],
            'pessoas': [2],
            'veiculos': [1],
            'classificacao_acidente': ['FERIDOS LEVES']
        })
        
        if db.inserir_acidentes(df_teste):
            print("✅ Teste de inserção bem-sucedido!")
        else:
            print("❌ Erro no teste de inserção")
        
        db.desconectar()
        print("🎉 Teste de conexão concluído!")
    else:
        print("❌ Falha na conexão com MySQL")
        print("💡 Verifique se o XAMPP está rodando e o banco 'machineL' existe")

if __name__ == "__main__":
    testar_conexao()
