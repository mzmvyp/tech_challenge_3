"""
Modelo de Risco de Acidentes - Sistema de Prevenção de Acidentes

Este módulo implementa um modelo de ML que prevê PROBABILIDADE de acidentes
baseado em padrões históricos da PRF, focando em PREVENÇÃO.
"""

import pandas as pd
import numpy as np
import joblib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import warnings

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc,
    confusion_matrix, classification_report, roc_curve
)
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class ModeloRiscoAcidentes:
    """
    Modelo de ML para prever probabilidade de acidentes baseado em:
    - Dados históricos da PRF
    - Padrões temporais e espaciais
    - Condições ambientais e de via
    """
    
    def __init__(self, random_state: int = 42):
        """Inicializa o modelo"""
        self.random_state = random_state
        self.modelo = None
        self.scaler = StandardScaler()
        self.encoders = {}
        self.feature_columns = []
        self.feature_importance = None
        self.metricas = {}
        
        # Configurações do modelo
        self.config_modelo = {
            'max_iter': 200,
            'max_depth': 10,
            'learning_rate': 0.1,
            'min_samples_leaf': 20,
            'l2_regularization': 1.0,
            'random_state': random_state
        }
    
    def preparar_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepara features para treinamento
        
        Args:
            df: DataFrame com dados balanceados
            
        Returns:
            Tuple (X, y) - Features e target
        """
        logger.info("Preparando features para treinamento...")
        
        # Definir features do modelo
        features_categoricas = [
            'br', 'uf', 'municipio', 'dia_semana'
        ]
        
        features_numericas = [
            'km_intervalo', 'hora', 'mes', 'trimestre',
            'clima_ruim', 'pista_simples', 'tracado_curva',
            'eh_fim_semana', 'eh_feriado', 'periodo_risco',
            'taxa_historica_trecho', 'taxa_historica_br',
            'score_risco_composto', 'hora_sin', 'hora_cos',
            'mes_sin', 'mes_cos'
        ]
        
        features_interacao = [
            'clima_periodo_risco', 'br_periodo_risco', 'fim_semana_periodo'
        ]
        
        self.feature_columns = features_numericas + features_interacao
        
        # Filtrar colunas existentes
        features_existentes = [col for col in self.feature_columns if col in df.columns]
        
        # Preparar features numéricas
        X_numericas = df[features_existentes].copy()
        
        # Tratar valores faltantes
        X_numericas = X_numericas.fillna(0)
        
        # Codificar features categóricas
        X_categoricas = pd.DataFrame()
        for col in features_categoricas:
            if col in df.columns:
                # Label encoding para categorias
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    X_categoricas[col] = self.encoders[col].fit_transform(df[col].astype(str))
                else:
                    X_categoricas[col] = self.encoders[col].transform(df[col].astype(str))
        
        # Combinar features
        X = pd.concat([X_numericas, X_categoricas], axis=1)
        
        # Target
        y = df['teve_acidente'].copy()
        
        # Atualizar lista de features
        self.feature_columns = list(X.columns)
        
        logger.info(f"Features preparadas: {X.shape[1]} features, {X.shape[0]} amostras")
        logger.info(f"Target balanceado: {y.mean():.3f} (positivos)")
        
        return X, y
    
    def treinar_modelo(self, X: pd.DataFrame, y: pd.Series, 
                      validacao_temporal: bool = True) -> Dict[str, float]:
        """
        Treina o modelo de risco de acidentes
        
        Args:
            X: Features de treinamento
            y: Target (0 ou 1)
            validacao_temporal: Se True, usa validação temporal
            
        Returns:
            Dict com métricas de performance
        """
        logger.info("Iniciando treinamento do modelo...")
        
        if validacao_temporal:
            # Validação temporal: dados antigos para treino, recentes para teste
            X_train, X_test, y_train, y_test = self._split_temporal(X, y)
        else:
            # Split aleatório
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state, stratify=y
            )
        
        logger.info(f"Treino: {len(X_train)} amostras")
        logger.info(f"Teste: {len(X_test)} amostras")
        
        # Normalizar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Criar e treinar modelo
        modelo_base = HistGradientBoostingClassifier(**self.config_modelo)
        
        # Calibrar probabilidades (ajustar CV baseado no tamanho dos dados)
        if len(X_train) < 30:
            # Para datasets pequenos, usar validação simples
            self.modelo = modelo_base
        else:
            # Para datasets maiores, usar calibração
            self.modelo = CalibratedClassifierCV(
                modelo_base, 
                method='isotonic',
                cv=min(3, len(X_train) // 10)
            )
        
        # Treinar
        self.modelo.fit(X_train_scaled, y_train)
        
        # Avaliar
        metricas = self._avaliar_modelo(X_test_scaled, y_test)
        
        # Feature importance
        self._calcular_feature_importance(X_train_scaled)
        
        logger.info("✅ Modelo treinado com sucesso!")
        logger.info(f"ROC-AUC: {metricas['roc_auc']:.3f}")
        logger.info(f"Precision: {metricas['precision']:.3f}")
        logger.info(f"Recall: {metricas['recall']:.3f}")
        
        return metricas
    
    def _split_temporal(self, X: pd.DataFrame, y: pd.Series) -> Tuple:
        """Split temporal dos dados"""
        # Assumir que os dados estão ordenados por data
        # Usar 80% mais antigos para treino, 20% mais recentes para teste
        split_idx = int(len(X) * 0.8)
        
        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def _avaliar_modelo(self, X_test: np.ndarray, y_test: pd.Series) -> Dict[str, float]:
        """Avalia performance do modelo"""
        # Predições
        y_pred_proba = self.modelo.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Métricas
        metricas = {
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'precision': self._calcular_precision(y_test, y_pred_proba),
            'recall': self._calcular_recall(y_test, y_pred_proba),
            'f1': self._calcular_f1(y_test, y_pred_proba),
            'accuracy': (y_pred == y_test).mean(),
            'calibration_error': self._calcular_erro_calibracao(y_test, y_pred_proba)
        }
        
        # Precision-Recall AUC
        precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
        metricas['pr_auc'] = auc(recall, precision)
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        metricas['confusion_matrix'] = cm.tolist()
        
        self.metricas = metricas
        return metricas
    
    def _calcular_precision(self, y_true: pd.Series, y_pred_proba: np.ndarray, 
                          threshold: float = 0.5) -> float:
        """Calcula precision para um threshold específico"""
        y_pred = (y_pred_proba > threshold).astype(int)
        tp = ((y_pred == 1) & (y_true == 1)).sum()
        fp = ((y_pred == 1) & (y_true == 0)).sum()
        return tp / (tp + fp) if (tp + fp) > 0 else 0
    
    def _calcular_recall(self, y_true: pd.Series, y_pred_proba: np.ndarray, 
                        threshold: float = 0.5) -> float:
        """Calcula recall para um threshold específico"""
        y_pred = (y_pred_proba > threshold).astype(int)
        tp = ((y_pred == 1) & (y_true == 1)).sum()
        fn = ((y_pred == 0) & (y_true == 1)).sum()
        return tp / (tp + fn) if (tp + fn) > 0 else 0
    
    def _calcular_f1(self, y_true: pd.Series, y_pred_proba: np.ndarray, 
                    threshold: float = 0.5) -> float:
        """Calcula F1-score"""
        precision = self._calcular_precision(y_true, y_pred_proba, threshold)
        recall = self._calcular_recall(y_true, y_pred_proba, threshold)
        return 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    def _calcular_erro_calibracao(self, y_true: pd.Series, y_pred_proba: np.ndarray) -> float:
        """Calcula erro de calibração (ECE - Expected Calibration Error)"""
        # Dividir predições em bins
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Encontrar predições no bin
            in_bin = (y_pred_proba > bin_lower) & (y_pred_proba <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                # Accuracy no bin
                accuracy_in_bin = y_true[in_bin].mean()
                # Probabilidade média no bin
                avg_confidence_in_bin = y_pred_proba[in_bin].mean()
                
                # Erro de calibração no bin
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        
        return ece
    
    def _calcular_feature_importance(self, X_train: np.ndarray):
        """Calcula importância das features"""
        # Verificar se o modelo tem feature_importances_
        if hasattr(self.modelo, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.modelo.feature_importances_
            }).sort_values('importance', ascending=False)
        elif hasattr(self.modelo, 'base_estimator') and hasattr(self.modelo.base_estimator, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.modelo.base_estimator.feature_importances_
            }).sort_values('importance', ascending=False)
        else:
            logger.warning("Modelo não suporta feature importance")
    
    def predizer_risco(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Prediz risco de acidente para uma situação específica
        
        Args:
            features: Dict com features da situação
            
        Returns:
            Dict com predições e interpretação
        """
        if self.modelo is None:
            raise ValueError("Modelo não foi treinado ainda")
        
        # Preparar features
        X = self._preparar_features_predicao(features)
        
        # Normalizar
        X_scaled = self.scaler.transform(X)
        
        # Predizer
        prob_acidente = self.modelo.predict_proba(X_scaled)[0][1]
        
        # Interpretar resultado
        resultado = {
            'probabilidade_acidente': float(prob_acidente),
            'nivel_risco': self._classificar_nivel_risco(prob_acidente),
            'confianca': float(min(prob_acidente * 2, 1.0)),  # Confiança baseada na probabilidade
            'interpretacao': self._interpretar_risco(features, prob_acidente)
        }
        
        return resultado
    
    def _preparar_features_predicao(self, features: Dict[str, Any]) -> pd.DataFrame:
        """Prepara features para predição"""
        # Criar DataFrame com features padrão
        X = pd.DataFrame(columns=self.feature_columns)
        X.loc[0] = 0  # Inicializar com zeros
        
        # Mapear features fornecidas
        mapeamento = {
            'br': 'br',
            'km_intervalo': 'km_intervalo',
            'hora': 'hora',
            'dia_semana': 'dia_semana',
            'mes': 'mes',
            'clima_ruim': 'clima_ruim',
            'pista_simples': 'pista_simples',
            'tracado_curva': 'tracado_curva',
            'eh_fim_semana': 'eh_fim_semana',
            'eh_feriado': 'eh_feriado'
        }
        
        for feature_input, feature_modelo in mapeamento.items():
            if feature_input in features and feature_modelo in X.columns:
                valor = features[feature_input]
                
                # Codificar features categóricas
                if feature_input in self.encoders:
                    try:
                        valor = self.encoders[feature_input].transform([str(valor)])[0]
                    except ValueError:
                        # Valor não visto no treino, usar 0
                        valor = 0
                
                X.loc[0, feature_modelo] = valor
        
        # Calcular features derivadas
        X = self._calcular_features_derivadas(X, features)
        
        return X
    
    def _calcular_features_derivadas(self, X: pd.DataFrame, features: Dict[str, Any]) -> pd.DataFrame:
        """Calcula features derivadas para predição"""
        # Features cíclicas
        if 'hora' in X.columns:
            hora = X.loc[0, 'hora']
            X.loc[0, 'hora_sin'] = np.sin(2 * np.pi * hora / 24)
            X.loc[0, 'hora_cos'] = np.cos(2 * np.pi * hora / 24)
        
        if 'mes' in X.columns:
            mes = X.loc[0, 'mes']
            X.loc[0, 'mes_sin'] = np.sin(2 * np.pi * mes / 12)
            X.loc[0, 'mes_cos'] = np.cos(2 * np.pi * mes / 12)
        
        # Período de risco
        if 'hora' in X.columns:
            hora = X.loc[0, 'hora']
            if hora in [0, 1, 2, 3, 4, 5]:
                X.loc[0, 'periodo_risco'] = 3
            elif hora in [7, 8, 17, 18, 19]:
                X.loc[0, 'periodo_risco'] = 2
            elif hora in [22, 23]:
                X.loc[0, 'periodo_risco'] = 1
            else:
                X.loc[0, 'periodo_risco'] = 0
        
        # Features de interação
        if 'clima_ruim' in X.columns and 'periodo_risco' in X.columns:
            X.loc[0, 'clima_periodo_risco'] = X.loc[0, 'clima_ruim'] * X.loc[0, 'periodo_risco']
        
        # Taxa histórica (simulada se não disponível)
        if 'taxa_historica_trecho' not in X.columns:
            X.loc[0, 'taxa_historica_trecho'] = 0.1  # Valor padrão
        
        if 'taxa_historica_br' not in X.columns:
            X.loc[0, 'taxa_historica_br'] = 0.1  # Valor padrão
        
        return X
    
    def _classificar_nivel_risco(self, probabilidade: float) -> str:
        """Classifica nível de risco baseado na probabilidade"""
        if probabilidade <= 0.2:
            return "BAIXO"
        elif probabilidade <= 0.4:
            return "MÉDIO"
        elif probabilidade <= 0.6:
            return "ALTO"
        else:
            return "CRÍTICO"
    
    def _interpretar_risco(self, features: Dict[str, Any], probabilidade: float) -> str:
        """Interpreta o risco identificado"""
        fatores = []
        
        # Analisar fatores de risco
        if features.get('hora', 12) in [0, 1, 2, 3, 4, 5]:
            fatores.append("madrugada")
        elif features.get('hora', 12) in [7, 8, 17, 18, 19]:
            fatores.append("horário de pico")
        
        if features.get('clima_ruim', 0) == 1:
            fatores.append("clima adverso")
        
        if features.get('pista_simples', 0) == 1:
            fatores.append("pista simples")
        
        if features.get('tracado_curva', 0) == 1:
            fatores.append("traçado curvo")
        
        if features.get('eh_fim_semana', 0) == 1:
            fatores.append("fim de semana")
        
        if fatores:
            return f"Risco elevado devido a: {', '.join(fatores)}"
        else:
            return "Condições relativamente seguras"
    
    def salvar_modelo(self, caminho: str) -> bool:
        """Salva modelo treinado"""
        try:
            modelo_data = {
                'modelo': self.modelo,
                'scaler': self.scaler,
                'encoders': self.encoders,
                'feature_columns': self.feature_columns,
                'feature_importance': self.feature_importance,
                'metricas': self.metricas,
                'config_modelo': self.config_modelo,
                'random_state': self.random_state
            }
            
            joblib.dump(modelo_data, caminho)
            logger.info(f"✅ Modelo salvo em: {caminho}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar modelo: {e}")
            return False
    
    def carregar_modelo(self, caminho: str) -> bool:
        """Carrega modelo treinado"""
        try:
            modelo_data = joblib.load(caminho)
            
            self.modelo = modelo_data['modelo']
            self.scaler = modelo_data['scaler']
            self.encoders = modelo_data['encoders']
            self.feature_columns = modelo_data['feature_columns']
            self.feature_importance = modelo_data['feature_importance']
            self.metricas = modelo_data['metricas']
            self.config_modelo = modelo_data['config_modelo']
            self.random_state = modelo_data['random_state']
            
            logger.info(f"✅ Modelo carregado de: {caminho}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            return False
    
    def gerar_relatorio(self, caminho_saida: Optional[str] = None) -> str:
        """Gera relatório de performance do modelo"""
        if not self.metricas:
            return "Modelo não foi treinado ainda"
        
        relatorio = f"""
# Relatório do Modelo de Risco de Acidentes

## Métricas de Performance
- **ROC-AUC**: {self.metricas['roc_auc']:.3f}
- **Precision**: {self.metricas['precision']:.3f}
- **Recall**: {self.metricas['recall']:.3f}
- **F1-Score**: {self.metricas['f1']:.3f}
- **Accuracy**: {self.metricas['accuracy']:.3f}
- **PR-AUC**: {self.metricas['pr_auc']:.3f}
- **Calibration Error**: {self.metricas['calibration_error']:.3f}

## Features Mais Importantes
"""
        
        if self.feature_importance is not None:
            relatorio += "\n".join([
                f"- {row['feature']}: {row['importance']:.3f}"
                for _, row in self.feature_importance.head(10).iterrows()
            ])
        
        relatorio += f"""

## Configuração do Modelo
- **Algoritmo**: HistGradientBoostingClassifier
- **Max Iterations**: {self.config_modelo['max_iter']}
- **Max Depth**: {self.config_modelo['max_depth']}
- **Learning Rate**: {self.config_modelo['learning_rate']}
- **Random State**: {self.random_state}

## Interpretação
- ROC-AUC > 0.7: Modelo tem boa capacidade discriminativa
- Calibration Error < 0.1: Probabilidades bem calibradas
- Features importantes indicam os principais fatores de risco
"""
        
        if caminho_saida:
            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.write(relatorio)
            logger.info(f"✅ Relatório salvo em: {caminho_saida}")
        
        return relatorio


def treinar_modelo_otimizado(X_train: pd.DataFrame, y_train: pd.Series, 
                           X_test: pd.DataFrame, y_test: pd.Series) -> ModeloRiscoAcidentes:
    """
    Função utilitária para treinar modelo otimizado
    
    Args:
        X_train, y_train: Dados de treinamento
        X_test, y_test: Dados de teste
        
    Returns:
        Modelo treinado
    """
    modelo = ModeloRiscoAcidentes()
    
    # Combinar dados para preparação
    X = pd.concat([X_train, X_test], ignore_index=True)
    y = pd.concat([y_train, y_test], ignore_index=True)
    
    # Preparar features
    X_prepared, y_prepared = modelo.preparar_features(pd.concat([X, y], axis=1))
    
    # Dividir novamente
    split_idx = len(X_train)
    X_train_prep = X_prepared.iloc[:split_idx]
    X_test_prep = X_prepared.iloc[split_idx:]
    y_train_prep = y_prepared.iloc[:split_idx]
    y_test_prep = y_prepared.iloc[split_idx:]
    
    # Treinar
    modelo.treinar_modelo(X_train_prep, y_train_prep, validacao_temporal=False)
    
    return modelo


if __name__ == "__main__":
    # Teste do modelo
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("✅ Modelo de Risco de Acidentes carregado com sucesso!")
    print("Use a classe ModeloRiscoAcidentes para treinar e usar o modelo")
