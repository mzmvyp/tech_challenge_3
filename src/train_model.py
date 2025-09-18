# src/train_model.py

import pandas as pd
import numpy as np
import joblib
import time
from pathlib import Path
import logging
from datetime import datetime

# Sklearn imports
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    confusion_matrix, classification_report
)

# XGBoost
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️ XGBoost não instalado. Use: pip install xgboost")

# Imports locais
from src.utils.preprocessing import PreprocessadorDados
from src.data_collector import ColetorDadosPRF

# Configuração
logging.basicConfig(level=logging.INFO)

class TreinadorModelos:
    """
    Classe para treinar e comparar múltiplos modelos de ML
    """
    
    def __init__(self, diretorio_modelos="data/models"):
        self.diretorio_modelos = Path(diretorio_modelos)
        self.diretorio_modelos.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.resultados = {}
        self.melhor_modelo = None
        
    def definir_modelos(self):
        """
        Define os modelos que serão treinados
        """
        
        modelos = {
            'Logistic Regression': LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'
            ),
            
            'Decision Tree': DecisionTreeClassifier(
                max_depth=10,
                min_samples_split=20,
                random_state=42,
                class_weight='balanced'
            ),
            
            'Random Forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=10,
                random_state=42,
                class_weight='balanced',
                n_jobs=-1
            ),
            
            'Naive Bayes': GaussianNB(),
            
            'SVM': SVC(
                kernel='rbf',
                random_state=42,
                class_weight='balanced',
                probability=True
            )
        }
        
        # Adicionando XGBoost se disponível
        if XGBOOST_AVAILABLE:
            modelos['XGBoost'] = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )
        
        return modelos
    
    def treinar_modelos(self, X_train, X_test, y_train, y_test):
        """
        Treina vários modelos e compara performance
        """
        
        self.logger.info("🤖 TREINANDO MODELOS")
        self.logger.info("="*80)
        
        modelos = self.definir_modelos()
        
        # Treinando cada modelo
        for nome, modelo in modelos.items():
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📚 Treinando: {nome}")
            self.logger.info(f"{'='*60}")
            
            inicio = time.time()
            
            try:
                # TREINAMENTO
                self.logger.info("   Treinando...")
                modelo.fit(X_train, y_train)
                
                # PREDIÇÃO
                self.logger.info("   Fazendo predições...")
                y_pred = modelo.predict(X_test)
                
                # MÉTRICAS
                tempo_treino = time.time() - inicio
                
                # Calculando métricas
                acc = accuracy_score(y_test, y_pred)
                prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                
                # Cross-validation score
                cv_scores = cross_val_score(modelo, X_train, y_train, cv=5, scoring='f1_weighted')
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
                
                # Salvando resultados
                self.resultados[nome] = {
                    'modelo': modelo,
                    'y_pred': y_pred,
                    'accuracy': acc,
                    'precision': prec,
                    'recall': rec,
                    'f1': f1,
                    'cv_mean': cv_mean,
                    'cv_std': cv_std,
                    'tempo': tempo_treino
                }
                
                # Exibindo resultados
                self.logger.info(f"\n   📊 RESULTADOS:")
                self.logger.info(f"   Acurácia:     {acc:.3f} ({acc*100:.1f}%)")
                self.logger.info(f"   Precisão:     {prec:.3f}")
                self.logger.info(f"   Recall:       {rec:.3f}")
                self.logger.info(f"   F1-Score:     {f1:.3f}")
                self.logger.info(f"   CV F1-Score:  {cv_mean:.3f} ± {cv_std:.3f}")
                self.logger.info(f"   Tempo:        {tempo_treino:.2f} segundos")
                
                # Matriz de confusão
                cm = confusion_matrix(y_test, y_pred)
                self.logger.info(f"\n   📋 MATRIZ DE CONFUSÃO:")
                self.logger.info(f"   Classes: 0=Ileso, 1=Leve, 2=Grave, 3=Fatal")
                self.logger.info(f"   {cm}")
                
            except Exception as e:
                self.logger.error(f"   ❌ Erro: {e}")
                self.resultados[nome] = None
        
        # COMPARAÇÃO FINAL
        self.exibir_ranking()
        
        return self.resultados
    
    def exibir_ranking(self):
        """
        Exibe ranking dos modelos
        """
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info("🏆 RANKING DOS MODELOS")
        self.logger.info(f"{'='*80}")
        
        # Ordenando por F1-Score
        ranking = sorted(
            [(nome, res['f1']) for nome, res in self.resultados.items() if res],
            key=lambda x: x[1],
            reverse=True
        )
        
        for i, (nome, f1) in enumerate(ranking, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            self.logger.info(f"{emoji} {i}. {nome}: F1-Score = {f1:.3f}")
        
        if ranking:
            melhor_nome = ranking[0][0]
            self.melhor_modelo = self.resultados[melhor_nome]['modelo']
            self.logger.info(f"\n🎯 MELHOR MODELO: {melhor_nome}")
            
            return melhor_nome
    
    def otimizar_melhor_modelo(self, X_train, y_train, X_test, y_test):
        """
        Otimiza os hiperparâmetros do melhor modelo
        """
        
        self.logger.info("🔧 OTIMIZAÇÃO DE HIPERPARÂMETROS")
        self.logger.info("="*80)
        
        # Usando Random Forest como padrão para otimização
        self.logger.info("\nUsando Random Forest para otimização")
        
        # Grid de hiperparâmetros mais conservador para não demorar muito
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        self.logger.info(f"\n📊 Configurações a testar:")
        total_combinacoes = 1
        for param, values in param_grid.items():
            self.logger.info(f"   {param}: {values}")
            total_combinacoes *= len(values)
        self.logger.info(f"\n   Total de combinações: {total_combinacoes}")
        
        # Modelo base
        rf = RandomForestClassifier(
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )
        
        # Grid Search com validação cruzada reduzida para acelerar
        grid_search = GridSearchCV(
            estimator=rf,
            param_grid=param_grid,
            cv=3,  # Reduzido para 3-fold para acelerar
            scoring='f1_weighted',
            n_jobs=-1,
            verbose=1
        )
        
        self.logger.info("\n🔍 Iniciando busca (pode demorar alguns minutos)...")
        inicio = time.time()
        
        # Executando busca
        grid_search.fit(X_train, y_train)
        
        tempo_busca = time.time() - inicio
        
        self.logger.info(f"\n✅ Busca concluída em {tempo_busca/60:.1f} minutos")
        
        # Melhores parâmetros
        self.logger.info("\n🏆 MELHORES HIPERPARÂMETROS:")
        for param, value in grid_search.best_params_.items():
            self.logger.info(f"   {param}: {value}")
        
        self.logger.info(f"\n📈 Score no cross-validation: {grid_search.best_score_:.3f}")
        
        # Testando o melhor modelo
        melhor_modelo = grid_search.best_estimator_
        y_pred_otimizado = melhor_modelo.predict(X_test)
        
        # Métricas do modelo otimizado
        acc_otimizado = accuracy_score(y_test, y_pred_otimizado)
        f1_otimizado = f1_score(y_test, y_pred_otimizado, average='weighted')
        
        self.logger.info(f"\n📊 PERFORMANCE NO TESTE:")
        self.logger.info(f"   Acurácia: {acc_otimizado:.3f}")
        self.logger.info(f"   F1-Score: {f1_otimizado:.3f}")
        
        # Relatório detalhado
        self.logger.info(f"\n📋 RELATÓRIO DETALHADO:")
        report = classification_report(y_test, y_pred_otimizado)
        self.logger.info(f"\n{report}")
        
        # Atualizando melhor modelo
        self.melhor_modelo = melhor_modelo
        
        return melhor_modelo, grid_search.best_params_
    
    def salvar_modelo(self, modelo=None, nome_arquivo=None):
        """
        Salva o modelo treinado
        """
        
        if modelo is None:
            modelo = self.melhor_modelo
        
        if nome_arquivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"modelo_acidentes_{timestamp}.pkl"
        
        caminho_modelo = self.diretorio_modelos / nome_arquivo
        
        # Salvando modelo
        joblib.dump(modelo, caminho_modelo)
        
        self.logger.info(f"💾 Modelo salvo em: {caminho_modelo}")
        
        # Salvando também como modelo principal
        modelo_principal = self.diretorio_modelos / "modelo_acidentes.pkl"
        joblib.dump(modelo, modelo_principal)
        self.logger.info(f"💾 Modelo principal salvo em: {modelo_principal}")
        
        return caminho_modelo
    
    def avaliar_feature_importance(self, modelo=None, feature_names=None, top_n=20):
        """
        Analisa importância das features
        """
        
        if modelo is None:
            modelo = self.melhor_modelo
        
        if hasattr(modelo, 'feature_importances_'):
            self.logger.info("📊 ANÁLISE DE IMPORTÂNCIA DAS FEATURES")
            self.logger.info("="*60)
            
            importancias = modelo.feature_importances_
            
            if feature_names is None:
                feature_names = [f"feature_{i}" for i in range(len(importancias))]
            
            # Criando DataFrame
            df_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': importancias
            }).sort_values('importance', ascending=False)
            
            # Top N features
            top_features = df_importance.head(top_n)
            
            self.logger.info(f"\n🏆 TOP {top_n} FEATURES MAIS IMPORTANTES:")
            for i, (_, row) in enumerate(top_features.iterrows(), 1):
                self.logger.info(f"   {i:2d}. {row['feature']}: {row['importance']:.4f}")
            
            return df_importance
        else:
            self.logger.warning("   ⚠️ Modelo não possui feature_importances_")
            return None

def main():
    """
    Função principal para executar o treinamento
    """
    
    print("🚨 SISTEMA DE PREVISÃO DE GRAVIDADE DE ACIDENTES - PRF")
    print("="*80)
    print("🤖 Iniciando treinamento dos modelos...")
    
    # 1. VERIFICANDO SE EXISTEM DADOS
    arquivo_dados = Path("data/raw/acidentes_combinados.csv")
    
    if not arquivo_dados.exists():
        print("\n❌ Dados não encontrados!")
        print("🔄 Executando coleta de dados primeiro...")
        
        # Coletando dados
        coletor = ColetorDadosPRF()
        dados = coletor.coletar_todos_os_anos()
        
        if dados is None:
            print("❌ Falha na coleta de dados. Verifique sua conexão.")
            return
    else:
        print(f"✅ Carregando dados de: {arquivo_dados}")
        dados = pd.read_csv(arquivo_dados, encoding='utf-8')
    
    print(f"📊 Total de registros: {len(dados):,}")
    
    # 2. PREPROCESSAMENTO
    print("\n🔄 Iniciando preprocessamento...")
    preprocessador = PreprocessadorDados()
    
    X, y = preprocessador.processar_completo(dados)
    
    # 3. DIVISÃO TREINO/TESTE
    print("\n📊 Dividindo dados em treino e teste...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Treino: {len(X_train):,} amostras")
    print(f"   Teste:  {len(X_test):,} amostras")
    
    # 4. NORMALIZAÇÃO
    print("\n📏 Normalizando dados...")
    X_train_scaled, X_test_scaled = preprocessador.normalizar_dados(X_train, X_test)
    
    # Salvando scaler
    scaler_path = Path("data/models/scaler_acidentes.pkl")
    scaler_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessador.scaler, scaler_path)
    print(f"💾 Scaler salvo em: {scaler_path}")
    
    # 5. TREINAMENTO DOS MODELOS
    print("\n🤖 Iniciando treinamento...")
    treinador = TreinadorModelos()
    
    resultados = treinador.treinar_modelos(
        X_train_scaled, X_test_scaled, y_train, y_test
    )
    
    # 6. OTIMIZAÇÃO
    print("\n🔧 Otimizando melhor modelo...")
    melhor_modelo, melhores_params = treinador.otimizar_melhor_modelo(
        X_train_scaled, y_train, X_test_scaled, y_test
    )
    
    # 7. ANÁLISE DE IMPORTÂNCIA
    print("\n📊 Analisando importância das features...")
    df_importance = treinador.avaliar_feature_importance(
        melhor_modelo, preprocessador.feature_names
    )
    
    # Salvando importância
    if df_importance is not None:
        importance_path = Path("data/models/feature_importance.csv")
        df_importance.to_csv(importance_path, index=False)
        print(f"💾 Importância das features salva em: {importance_path}")
    
    # 8. SALVANDO MODELO FINAL
    print("\n💾 Salvando modelo final...")
    modelo_path = treinador.salvar_modelo(melhor_modelo)
    
    # 9. RESUMO FINAL
    print("\n" + "="*80)
    print("✅ TREINAMENTO CONCLUÍDO COM SUCESSO!")
    print("="*80)
    print(f"📊 Modelos treinados: {len([r for r in resultados.values() if r])}")
    print(f"🎯 Melhor modelo: Random Forest Otimizado")
    print(f"📈 Performance:")
    
    # Métricas finais do melhor modelo
    y_pred_final = melhor_modelo.predict(X_test_scaled)
    acc_final = accuracy_score(y_test, y_pred_final)
    f1_final = f1_score(y_test, y_pred_final, average='weighted')
    
    print(f"   - Acurácia: {acc_final:.3f} ({acc_final*100:.1f}%)")
    print(f"   - F1-Score: {f1_final:.3f}")
    
    print(f"\n💾 Arquivos salvos:")
    print(f"   - Modelo: {modelo_path}")
    print(f"   - Scaler: {scaler_path}")
    print(f"   - Preprocessador: data/models/preprocessador.pkl")
    
    print(f"\n🔄 Próximo passo: Executar a API")
    print(f"   python src/api_predicao.py")

if __name__ == "__main__":
    main()
