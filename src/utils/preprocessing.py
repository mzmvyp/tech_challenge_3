# src/utils/preprocessing.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

class PreprocessadorDados:
    """
    Classe para preprocessamento completo dos dados de acidentes
    
    Esta classe implementa:
    1. Engenharia de Features
    2. Codificação de variáveis categóricas
    3. Normalização
    4. Seleção de features
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = None
        
    def criar_novas_features(self, df):
        """
        Cria novas variáveis que podem melhorar a previsão
        """
        
        self.logger.info("🔨 CRIANDO NOVAS FEATURES")
        self.logger.info("-" * 50)
        
        df_novo = df.copy()
        
        # 1. FEATURES TEMPORAIS
        if 'data_inversa' in df_novo.columns:
            self.logger.info("\n1️⃣ Criando features temporais...")
            
            # Convertendo para datetime
            df_novo['data'] = pd.to_datetime(df_novo['data_inversa'], format='%Y-%m-%d', errors='coerce')
            
            # Extraindo componentes temporais
            df_novo['ano'] = df_novo['data'].dt.year
            df_novo['mes'] = df_novo['data'].dt.month
            df_novo['dia_mes'] = df_novo['data'].dt.day
            df_novo['trimestre'] = df_novo['data'].dt.quarter
            df_novo['dia_ano'] = df_novo['data'].dt.dayofyear
            
            # Identificando períodos especiais
            df_novo['fim_de_semana'] = df_novo['dia_semana'].isin(['SÁBADO', 'DOMINGO']).astype(int)
            
            # Feriados aproximados
            df_novo['periodo_festivo'] = (
                (df_novo['mes'] == 12) |  # Dezembro
                (df_novo['mes'] == 1) |   # Janeiro
                (df_novo['mes'] == 2) |   # Fevereiro
                (df_novo['mes'] == 6) |   # Junho
                (df_novo['mes'] == 7)     # Julho
            ).astype(int)
            
            self.logger.info("   ✅ Features temporais criadas")
        
        # 2. FEATURES DE HORÁRIO
        if 'horario' in df_novo.columns:
            self.logger.info("\n2️⃣ Criando features de horário...")
            
            # Extraindo hora
            try:
                df_novo['hora'] = pd.to_datetime(df_novo['horario'], format='%H:%M:%S', errors='coerce').dt.hour
            except:
                # Se falhar, tentar extrair de outra forma
                df_novo['hora'] = df_novo['horario'].str.split(':').str[0].astype(float)
            
            # Classificando períodos do dia
            def classificar_periodo(hora):
                if pd.isna(hora):
                    return 'NAO_INFORMADO'
                elif 0 <= hora < 6:
                    return 'MADRUGADA'
                elif 6 <= hora < 12:
                    return 'MANHA'
                elif 12 <= hora < 18:
                    return 'TARDE'
                else:
                    return 'NOITE'
            
            df_novo['periodo_detalhado'] = df_novo['hora'].apply(classificar_periodo)
            
            # Horários de pico
            df_novo['horario_pico'] = (
                ((df_novo['hora'] >= 7) & (df_novo['hora'] <= 9)) |
                ((df_novo['hora'] >= 17) & (df_novo['hora'] <= 19))
            ).astype(int)
            
            self.logger.info("   ✅ Features de horário criadas")
        
        # 3. FEATURES DE LOCALIZAÇÃO
        if 'br' in df_novo.columns:
            self.logger.info("\n3️⃣ Criando features de localização...")
            
            # BRs mais perigosas
            brs_frequentes = df_novo['br'].value_counts().head(10).index
            df_novo['br_perigosa'] = df_novo['br'].isin(brs_frequentes).astype(int)
            
            # Classificando por região
            regioes = {
                'NORTE': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
                'NORDESTE': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
                'CENTRO_OESTE': ['DF', 'GO', 'MT', 'MS'],
                'SUDESTE': ['ES', 'MG', 'RJ', 'SP'],
                'SUL': ['PR', 'RS', 'SC']
            }
            
            def classificar_regiao(uf):
                for regiao, estados in regioes.items():
                    if uf in estados:
                        return regiao
                return 'NAO_INFORMADO'
            
            if 'uf' in df_novo.columns:
                df_novo['regiao'] = df_novo['uf'].apply(classificar_regiao)
            
            self.logger.info("   ✅ Features de localização criadas")
        
        # 4. FEATURES DE GRAVIDADE POTENCIAL
        if 'pessoas' in df_novo.columns and 'veiculos' in df_novo.columns:
            self.logger.info("\n4️⃣ Criando features de gravidade...")
            
            # Razão pessoas/veículos
            df_novo['ocupacao_media'] = df_novo['pessoas'] / df_novo['veiculos'].replace(0, 1)
            
            # Indicadores de gravidade potencial
            df_novo['multiplos_veiculos'] = (df_novo['veiculos'] > 1).astype(int)
            df_novo['muitas_pessoas'] = (df_novo['pessoas'] > 4).astype(int)
            
            self.logger.info("   ✅ Features de gravidade criadas")
        
        # 5. FEATURES DE CONDIÇÕES
        if 'condicao_metereologica' in df_novo.columns:
            self.logger.info("\n5️⃣ Criando features de condições...")
            
            # Condições adversas
            condicoes_adversas = ['CHUVA', 'NEBLINA', 'NEVE', 'NUBLADO', 'GAROA']
            df_novo['condicao_adversa'] = df_novo['condicao_metereologica'].isin(condicoes_adversas).astype(int)
            
            self.logger.info("   ✅ Features de condições criadas")
        
        # 6. FEATURES DE TIPO DE ACIDENTE
        if 'tipo_ocorrencia' in df_novo.columns:
            self.logger.info("\n6️⃣ Criando features de tipo de acidente...")
            
            # Acidentes mais graves
            tipos_graves = ['COLISÃO FRONTAL', 'COLISÃO TRANSVERSAL', 'CAPOTAMENTO', 'TOMBAMENTO']
            df_novo['acidente_tipo_grave'] = df_novo['tipo_ocorrencia'].str.upper().isin(tipos_graves).astype(int)
            
            self.logger.info("   ✅ Features de tipo de acidente criadas")
        
        self.logger.info("\n✅ ENGENHARIA DE FEATURES CONCLUÍDA")
        self.logger.info(f"   Features originais: {len(df.columns)}")
        self.logger.info(f"   Features finais: {len(df_novo.columns)}")
        self.logger.info(f"   Novas features criadas: {len(df_novo.columns) - len(df.columns)}")
        
        return df_novo
    
    def codificar_variaveis(self, df, variavel_alvo='classificacao_acidente'):
        """
        Transforma variáveis categóricas em números
        """
        
        self.logger.info("🔢 CODIFICAÇÃO DE VARIÁVEIS")
        self.logger.info("-" * 50)
        
        df_cod = df.copy()
        
        # 1. CODIFICANDO A VARIÁVEL ALVO
        self.logger.info("\n1️⃣ Codificando variável alvo...")
        
        # Mapeamento específico para gravidade
        mapa_gravidade = {
            'SEM VÍTIMAS': 0,
            'SEM VITIMAS': 0,
            'ILESO': 0,
            'COM FERIDOS LEVES': 1,
            'FERIDOS LEVES': 1,
            'FERIDOS': 1,
            'FERIDO LEVE': 1,
            'COM FERIDOS GRAVES': 2,
            'FERIDOS GRAVES': 2,
            'FERIDO GRAVE': 2,
            'COM VÍTIMAS FATAIS': 3,
            'COM VITIMAS FATAIS': 3,
            'ÓBITOS': 3,
            'MORTOS': 3,
            'FATAL': 3
        }
        
        if variavel_alvo in df_cod.columns:
            # Padronizando os valores
            df_cod[variavel_alvo] = df_cod[variavel_alvo].astype(str).str.upper().str.strip()
            
            # Aplicando o mapeamento
            df_cod['gravidade_numerica'] = df_cod[variavel_alvo].map(mapa_gravidade)
            
            # Verificando não mapeados
            nao_mapeados = df_cod[df_cod['gravidade_numerica'].isna()][variavel_alvo].unique()
            if len(nao_mapeados) > 0:
                self.logger.warning(f"   ⚠️ Valores não mapeados: {nao_mapeados}")
                # Removendo não mapeados
                df_cod = df_cod[df_cod['gravidade_numerica'].notna()]
            
            self.logger.info(f"   ✅ Variável alvo codificada")
            distribuicao = df_cod['gravidade_numerica'].value_counts().sort_index()
            for codigo, qtd in distribuicao.items():
                pct = qtd / len(df_cod) * 100
                self.logger.info(f"      Classe {int(codigo)}: {qtd:,} ({pct:.1f}%)")
        
        # 2. ONE-HOT ENCODING PARA VARIÁVEIS NOMINAIS
        self.logger.info("\n2️⃣ Aplicando One-Hot Encoding...")
        
        # Variáveis categóricas para one-hot
        variaveis_nominais = []
        for col in df_cod.columns:
            if (df_cod[col].dtype == 'object' and 
                col not in [variavel_alvo, 'data'] and
                df_cod[col].nunique() < 50):  # Limite para evitar muitas colunas
                variaveis_nominais.append(col)
        
        for col in variaveis_nominais:
            self.logger.info(f"   Codificando {col}...")
            
            # Criando dummies
            dummies = pd.get_dummies(df_cod[col], prefix=col, drop_first=True)
            
            # Adicionando ao dataframe
            df_cod = pd.concat([df_cod, dummies], axis=1)
            
            # Removendo a coluna original
            df_cod = df_cod.drop(col, axis=1)
            
            self.logger.info(f"      ✅ Criadas {len(dummies.columns)} colunas binárias")
        
        # 3. REMOVENDO COLUNAS NÃO NUMÉRICAS RESTANTES
        self.logger.info("\n3️⃣ Limpando colunas não numéricas...")
        
        colunas_para_remover = []
        for col in df_cod.columns:
            if df_cod[col].dtype == 'object' and col != 'gravidade_numerica':
                colunas_para_remover.append(col)
        
        df_cod = df_cod.drop(colunas_para_remover, axis=1)
        self.logger.info(f"   Removidas {len(colunas_para_remover)} colunas não numéricas")
        
        self.logger.info("\n✅ CODIFICAÇÃO CONCLUÍDA")
        self.logger.info(f"   Total de features após codificação: {len(df_cod.columns)}")
        
        return df_cod
    
    def preparar_dados_para_modelo(self, df, coluna_alvo='gravidade_numerica', test_size=0.2):
        """
        Prepara dados finais para o modelo
        """
        
        self.logger.info("📊 PREPARANDO DADOS PARA MODELAGEM")
        self.logger.info("-" * 50)
        
        # Separando features e target
        if coluna_alvo not in df.columns:
            raise ValueError(f"Coluna alvo '{coluna_alvo}' não encontrada!")
        
        X = df.drop([coluna_alvo], axis=1, errors='ignore')
        y = df[coluna_alvo]
        
        # Garantindo que todas as features são numéricas
        X = X.select_dtypes(include=[np.number])
        
        # Convertendo todas as colunas para float64 para evitar problemas de tipo
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce')
        
        # Tratando valores infinitos e NaN
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        # Garantindo que todos os dados são float64
        X = X.astype(np.float64)
        
        self.logger.info(f"   Features (X): {X.shape}")
        self.logger.info(f"   Target (y): {y.shape}")
        
        # Salvando nomes das features
        self.feature_names = list(X.columns)
        
        return X, y
    
    def normalizar_dados(self, X_train, X_test=None):
        """
        Normaliza os dados usando StandardScaler
        """
        
        self.logger.info("📏 NORMALIZANDO DADOS")
        self.logger.info("-" * 30)
        
        # Treinando o scaler apenas no treino
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
        
        self.logger.info("   ✅ Dados de treino normalizados")
        
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
            X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
            self.logger.info("   ✅ Dados de teste normalizados")
            return X_train_scaled, X_test_scaled
        
        return X_train_scaled
    
    def processar_completo(self, df, salvar_preprocessador=True):
        """
        Executa todo o pipeline de preprocessamento
        """
        
        self.logger.info("🔄 INICIANDO PREPROCESSAMENTO COMPLETO")
        self.logger.info("="*80)
        
        # 1. Engenharia de features
        df_features = self.criar_novas_features(df)
        
        # 2. Codificação
        df_codificado = self.codificar_variaveis(df_features)
        
        # 3. Preparação final
        X, y = self.preparar_dados_para_modelo(df_codificado)
        
        self.logger.info("\n✅ PREPROCESSAMENTO CONCLUÍDO")
        self.logger.info(f"   Dimensões finais: {X.shape}")
        self.logger.info(f"   Features selecionadas: {len(self.feature_names)}")
        
        # 4. Salvando preprocessador se solicitado
        if salvar_preprocessador:
            import joblib
            
            preprocessador_data = {
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'label_encoders': self.label_encoders
            }
            
            joblib.dump(preprocessador_data, 'data/models/preprocessador.pkl')
            self.logger.info("   💾 Preprocessador salvo em: data/models/preprocessador.pkl")
        
        return X, y
