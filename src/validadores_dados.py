# src/validadores_dados.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import chardet
import re
from pathlib import Path

class ValidadorDadosPRF:
    """
    Validador e normalizador de dados da PRF
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Mapeamento de gravidade
        self.mapa_gravidade = {
            'Ileso': 0,
            'Ferido Leve': 1,
            'Ferido Grave': 2,
            'Fatal': 3,
            'Com vítimas fatais': 3,
            'Com feridos graves': 2,
            'Com feridos leves': 1,
            'Sem vítimas': 0,
            'COM VÍTIMAS FATAIS': 3,
            'COM FERIDOS GRAVES': 2,
            'COM FERIDOS LEVES': 1,
            'SEM VÍTIMAS': 0,
            'COM FERIDOS LEVES': 1,
            'COM FERIDOS GRAVES': 2,
            'COM VÍTIMAS FATAIS': 3
        }
        
        # UFs válidas
        self.ufs_validas = {
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        }
        
        # BRs válidas
        self.brs_validas = set(range(1, 1000))
    
    def detectar_codificacao(self, arquivo):
        """
        Detecta a codificação do arquivo
        """
        try:
            with open(arquivo, 'rb') as f:
                raw_data = f.read(10000)  # Ler apenas os primeiros 10KB
                result = chardet.detect(raw_data)
                return result['encoding']
        except Exception as e:
            self.logger.error(f"Erro ao detectar codificação: {e}")
            return 'utf-8'
    
    def corrigir_codificacao(self, arquivo):
        """
        Tenta corrigir a codificação do arquivo
        """
        codificacoes = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
        
        for encoding in codificacoes:
            try:
                df = pd.read_csv(arquivo, encoding=encoding, low_memory=False)
                self.logger.info(f"✅ Codificação {encoding} funcionou")
                return df, encoding
            except Exception as e:
                self.logger.debug(f"❌ Codificação {encoding} falhou: {e}")
                continue
        
        return None, None
    
    def normalizar_data(self, data_str):
        """
        Normaliza data para formato padrão
        """
        if pd.isna(data_str) or data_str == '':
            return None
        
        # Converter para string
        data_str = str(data_str).strip()
        
        # Padrões de data
        padroes_data = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
        ]
        
        for padrao in padroes_data:
            match = re.match(padrao, data_str)
            if match:
                if padrao.startswith(r'(\d{4})'):  # YYYY-MM-DD
                    return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                else:  # DD/MM/YYYY ou DD-MM-YYYY
                    return f"{match.group(3)}-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
        
        return None
    
    def validar_data(self, data_str):
        """
        Valida se a data é real (não futura)
        """
        data_normalizada = self.normalizar_data(data_str)
        
        if not data_normalizada:
            return False, None
        
        try:
            data_obj = datetime.strptime(data_normalizada, '%Y-%m-%d')
            data_atual = datetime.now()
            
            # Verificar se não é futura
            if data_obj > data_atual:
                return False, data_normalizada
            
            # Verificar se não é muito antiga (antes de 2000)
            data_limite = datetime(2000, 1, 1)
            if data_obj < data_limite:
                return False, data_normalizada
            
            return True, data_normalizada
            
        except Exception:
            return False, data_normalizada
    
    def normalizar_gravidade(self, gravidade_str):
        """
        Normaliza gravidade para valor numérico
        """
        if pd.isna(gravidade_str) or gravidade_str == '':
            return 0
        
        gravidade_str = str(gravidade_str).strip().upper()
        
        # Buscar no mapeamento
        for key, value in self.mapa_gravidade.items():
            if key.upper() in gravidade_str:
                return value
        
        # Se não encontrou, retornar 0 (sem vítimas)
        return 0
    
    def validar_uf(self, uf_str):
        """
        Valida se UF é válida
        """
        if pd.isna(uf_str) or uf_str == '':
            return False, None
        
        uf_str = str(uf_str).strip().upper()
        
        if uf_str in self.ufs_validas:
            return True, uf_str
        
        return False, None
    
    def validar_br(self, br_value):
        """
        Valida se BR é válida
        """
        if pd.isna(br_value) or br_value == '':
            return False, None
        
        try:
            br_int = int(float(br_value))
            if 1 <= br_int <= 999:
                return True, br_int
        except (ValueError, TypeError):
            pass
        
        return False, None
    
    def normalizar_horario(self, horario_str):
        """
        Normaliza horário para formato HH:MM:SS
        """
        if pd.isna(horario_str) or horario_str == '':
            return '00:00:00'
        
        horario_str = str(horario_str).strip()
        
        # Padrões de horário
        padroes_horario = [
            r'(\d{1,2}):(\d{2}):(\d{2})',  # HH:MM:SS
            r'(\d{1,2}):(\d{2})',          # HH:MM
            r'(\d{1,2})',                  # HH
        ]
        
        for padrao in padroes_horario:
            match = re.match(padrao, horario_str)
            if match:
                hora = int(match.group(1))
                minuto = int(match.group(2)) if len(match.groups()) > 1 else 0
                segundo = int(match.group(3)) if len(match.groups()) > 2 else 0
                
                # Validar valores
                if 0 <= hora <= 23 and 0 <= minuto <= 59 and 0 <= segundo <= 59:
                    return f"{hora:02d}:{minuto:02d}:{segundo:02d}"
        
        return '00:00:00'
    
    def validar_e_corrigir_dataframe(self, df, nome_arquivo):
        """
        Valida e corrige um DataFrame
        """
        self.logger.info(f"🔍 Validando {nome_arquivo}...")
        
        # Verificar se tem dados
        if len(df) == 0:
            self.logger.warning(f"⚠️ {nome_arquivo} está vazio")
            return None
        
        # Verificar colunas essenciais
        colunas_essenciais = ['data_inversa', 'uf', 'br']
        colunas_faltando = [col for col in colunas_essenciais if col not in df.columns]
        
        if colunas_faltando:
            self.logger.warning(f"⚠️ {nome_arquivo} não tem colunas: {colunas_faltando}")
            return None
        
        # Aplicar validações e correções
        df_corrigido = df.copy()
        
        # Corrigir datas
        if 'data_inversa' in df_corrigido.columns:
            self.logger.info("📅 Corrigindo datas...")
            df_corrigido['data_inversa'] = df_corrigido['data_inversa'].apply(self.normalizar_data)
            
            # Remover registros com datas inválidas
            registros_antes = len(df_corrigido)
            df_corrigido = df_corrigido.dropna(subset=['data_inversa'])
            registros_depois = len(df_corrigido)
            
            if registros_antes != registros_depois:
                self.logger.info(f"🗑️ Removidos {registros_antes - registros_depois} registros com datas inválidas")
        
        # Corrigir gravidade
        if 'gravidade' in df_corrigido.columns:
            self.logger.info("🏥 Corrigindo gravidade...")
            df_corrigido['gravidade_numerica'] = df_corrigido['gravidade'].apply(self.normalizar_gravidade)
        elif 'classificacao_acidente' in df_corrigido.columns:
            self.logger.info("🏥 Corrigindo classificação...")
            df_corrigido['gravidade_numerica'] = df_corrigido['classificacao_acidente'].apply(self.normalizar_gravidade)
        else:
            self.logger.warning("⚠️ Nenhuma coluna de gravidade encontrada")
            df_corrigido['gravidade_numerica'] = 0
        
        # Corrigir UF
        if 'uf' in df_corrigido.columns:
            self.logger.info("🗺️ Corrigindo UF...")
            ufs_validas = []
            for uf in df_corrigido['uf']:
                valida, uf_corrigida = self.validar_uf(uf)
                ufs_validas.append(uf_corrigida if valida else None)
            df_corrigido['uf'] = ufs_validas
        
        # Corrigir BR
        if 'br' in df_corrigido.columns:
            self.logger.info("🛣️ Corrigindo BR...")
            brs_validas = []
            for br in df_corrigido['br']:
                valida, br_corrigida = self.validar_br(br)
                brs_validas.append(br_corrigida if valida else None)
            df_corrigido['br'] = brs_validas
        
        # Corrigir horário
        if 'horario' in df_corrigido.columns:
            self.logger.info("⏰ Corrigindo horário...")
            df_corrigido['horario'] = df_corrigido['horario'].apply(self.normalizar_horario)
        
        # Adicionar colunas de controle
        df_corrigido['ano_coleta'] = datetime.now().year
        df_corrigido['tipo_dados'] = 'dados_reais'
        df_corrigido['data_coleta'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Remover registros com dados essenciais inválidos
        registros_antes = len(df_corrigido)
        df_corrigido = df_corrigido.dropna(subset=['data_inversa', 'uf', 'br'])
        registros_depois = len(df_corrigido)
        
        if registros_antes != registros_depois:
            self.logger.info(f"🗑️ Removidos {registros_antes - registros_depois} registros com dados essenciais inválidos")
        
        # Verificar se ainda tem dados
        if len(df_corrigido) == 0:
            self.logger.warning(f"⚠️ {nome_arquivo} ficou vazio após correções")
            return None
        
        self.logger.info(f"✅ {nome_arquivo} validado: {len(df_corrigido)} registros válidos")
        return df_corrigido
    
    def processar_arquivo_csv(self, arquivo):
        """
        Processa um arquivo CSV completo
        """
        self.logger.info(f"📁 Processando {arquivo.name}...")
        
        # Detectar codificação
        encoding = self.detectar_codificacao(arquivo)
        self.logger.info(f"🔍 Codificação detectada: {encoding}")
        
        # Tentar ler com diferentes codificações
        df, encoding_usada = self.corrigir_codificacao(arquivo)
        
        if df is None:
            self.logger.error(f"❌ Não foi possível ler {arquivo.name}")
            return None
        
        # Validar e corrigir
        df_corrigido = self.validar_e_corrigir_dataframe(df, arquivo.name)
        
        if df_corrigido is None:
            self.logger.error(f"❌ {arquivo.name} não pôde ser processado")
            return None
        
        return df_corrigido

def main():
    """
    Função principal para teste
    """
    logging.basicConfig(level=logging.INFO)
    
    validador = ValidadorDadosPRF()
    
    # Testar com arquivo existente
    arquivo_teste = "data/raw/acidentes2025_ocorrencia.csv"
    
    if Path(arquivo_teste).exists():
        df = validador.processar_arquivo_csv(Path(arquivo_teste))
        if df is not None:
            print(f"✅ Arquivo processado: {len(df)} registros")
            print(f"Colunas: {list(df.columns)}")
            print(f"Primeiras linhas:")
            print(df.head())
        else:
            print("❌ Falha ao processar arquivo")
    else:
        print("❌ Arquivo de teste não encontrado")

if __name__ == "__main__":
    main()
