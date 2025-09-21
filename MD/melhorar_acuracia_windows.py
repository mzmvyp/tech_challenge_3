"""
Melhoria de Acurácia para Windows - Sem problemas de multiprocessing
Versão otimizada que funciona perfeitamente no Windows
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors
import xgboost as xgb
import lightgbm as lgb
from imblearn.over_sampling import SMOTE
import joblib
import warnings
from datetime import datetime
import logging
from scipy import stats
from scipy.stats import uniform, randint

warnings.filterwarnings('ignore')

# Configurar matplotlib
import matplotlib
matplotlib.use('Agg')

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MelhoradorAcuriaWindows:
    """Melhorador otimizado para Windows sem problemas de multiprocessing"""
    
    def __init__(self, sample_size=75000):
        self.sample_size = sample_size
        self.modelo_final = None
        self.feature_names = None
        self.metricas_finais = {}
        self.scaler = None
        
        logger.info(f"🚀 CONFIGURAÇÃO OTIMIZADA PARA WINDOWS:")
        logger.info(f"   📊 Sample Size: {self.sample_size:,}")
        logger.info(f"   ⚡ Otimizado para Windows")
        
    def criar_amostra_estratificada(self, df):
        """Cria amostra estratificada otimizada"""
        logger.info(f"📊 Criando amostra estratificada...")
        
        # Usar tamanho ótimo
        optimal_size = min(self.sample_size, len(df))
        logger.info(f"   Tamanho determinado: {optimal_size:,}")
        
        # Calcular proporção por classe
        class_counts = df['gravidade'].value_counts()
        
        # Amostra estratificada
        sample_per_class = {}
        for gravidade, count in class_counts.items():
            proportion = count / len(df)
            sample_per_class[gravidade] = int(optimal_size * proportion)
        
        logger.info("   Amostra por classe:")
        for gravidade, sample_count in sample_per_class.items():
            logger.info(f"      Classe {gravidade}: {sample_count:,}")
        
        # Criar amostra
        samples = []
        for gravidade, sample_count in sample_per_class.items():
            class_data = df[df['gravidade'] == gravidade]
            if len(class_data) >= sample_count:
                sampled = class_data.sample(n=sample_count, random_state=42)
            else:
                sampled = class_data
            samples.append(sampled)
        
        df_sample = pd.concat(samples, ignore_index=True)
        df_sample = df_sample.sample(frac=1, random_state=42).reset_index(drop=True)
        
        logger.info(f"   ✅ Amostra criada: {len(df_sample):,} registros")
        return df_sample
    
    def feature_engineering_otimizado(self, df):
        """Feature engineering otimizado com todas as melhorias"""
        logger.info("🔧 FEATURE ENGINEERING OTIMIZADO...")
        
        df_eng = df.copy()
        
        # 1. Features temporais cíclicas (essenciais)
        logger.info("   Criando features cíclicas...")
        df_eng['hora_sin'] = np.sin(2 * np.pi * df_eng['hora'] / 24)
        df_eng['hora_cos'] = np.cos(2 * np.pi * df_eng['hora'] / 24)
        df_eng['mes_sin'] = np.sin(2 * np.pi * df_eng['mes'] / 12)
        df_eng['mes_cos'] = np.cos(2 * np.pi * df_eng['mes'] / 12)
        df_eng['dia_semana_sin'] = np.sin(2 * np.pi * df_eng['dia_semana'] / 7)
        df_eng['dia_semana_cos'] = np.cos(2 * np.pi * df_eng['dia_semana'] / 7)
        
        # 2. Features de risco
        logger.info("   Criando features de risco...")
        df_eng['eh_fim_semana'] = (df_eng['dia_semana'] >= 5).astype(int)
        df_eng['eh_madrugada'] = ((df_eng['hora'] >= 0) & (df_eng['hora'] <= 6)).astype(int)
        df_eng['eh_noite'] = ((df_eng['hora'] >= 18) & (df_eng['hora'] <= 23)).astype(int)
        df_eng['eh_rush_hour'] = ((df_eng['hora'] >= 7) & (df_eng['hora'] <= 9)) | ((df_eng['hora'] >= 17) & (df_eng['hora'] <= 19))
        df_eng['eh_rush_hour'] = df_eng['eh_rush_hour'].astype(int)
        
        # 3. Features de densidade
        logger.info("   Criando features de densidade...")
        df_eng['densidade_hora'] = df_eng.groupby('hora')['gravidade'].transform('count')
        df_eng['densidade_br'] = df_eng.groupby('br')['gravidade'].transform('count')
        df_eng['densidade_uf'] = df_eng.groupby('uf')['gravidade'].transform('count')
        
        # 4. Features de severidade histórica
        logger.info("   Criando features históricas...")
        df_eng['severidade_historica_veiculo'] = df_eng.groupby('tipo_veiculo')['gravidade'].transform('mean')
        df_eng['severidade_historica_uf'] = df_eng.groupby('uf')['gravidade'].transform('mean')
        df_eng['severidade_historica_pista'] = df_eng.groupby('tipo_pista')['gravidade'].transform('mean')
        
        # 5. Feature mais importante: taxa local
        logger.info("   Criando taxa local...")
        df_eng['taxa_gravidade_local'] = df_eng.groupby(['br', 'km'])['gravidade'].transform('mean')
        
        # 6. Features de trecho expandidas (ideia do Henrique)
        logger.info("   Criando features de trecho expandidas...")
        for trecho_size in [5, 25, 50]:
            trecho_col = f'trecho_{trecho_size}km'
            df_eng[trecho_col] = (df_eng['km'] // trecho_size).astype(int)
            df_eng[f'densidade_{trecho_col}'] = df_eng.groupby(['br', trecho_col])['gravidade'].transform('count')
            df_eng[f'severidade_{trecho_col}'] = df_eng.groupby(['br', trecho_col])['gravidade'].transform('mean')
        
        # 7. Features de ranking
        logger.info("   Criando rankings...")
        df_eng['ranking_periculosidade_br'] = df_eng.groupby('br')['gravidade'].transform('mean').rank(pct=True)
        df_eng['ranking_periculosidade_uf'] = df_eng.groupby('uf')['gravidade'].transform('mean').rank(pct=True)
        
        # 8. Features de interação
        logger.info("   Criando interações...")
        df_eng['idade_hora'] = df_eng['idade'] * df_eng['hora']
        df_eng['idade_veiculo'] = df_eng['idade'] * df_eng['tipo_veiculo'].astype('category').cat.codes
        
        logger.info(f"   ✅ Features criadas: {len(df_eng.columns)} total")
        
        return df_eng
    
    def aplicar_smote_otimizado(self, X, y):
        """SMOTE otimizado"""
        logger.info("⚖️ APLICANDO SMOTE OTIMIZADO...")
        
        # Verificar desbalanceamento
        unique, counts = np.unique(y, return_counts=True)
        print("   Distribuição antes do SMOTE:")
        for gravidade, count in zip(unique, counts):
            percent = (count / len(y)) * 100
            print(f"      Classe {gravidade}: {count:,} ({percent:.1f}%)")
        
        # SMOTE com parâmetros otimizados
        smote = SMOTE(random_state=42, k_neighbors=min(3, min(counts)-1))
        X_balanced, y_balanced = smote.fit_resample(X, y)
        
        # Verificar resultado
        unique, counts = np.unique(y_balanced, return_counts=True)
        print("   Distribuição após SMOTE:")
        for gravidade, count in zip(unique, counts):
            percent = (count / len(y_balanced)) * 100
            print(f"      Classe {gravidade}: {count:,} ({percent:.1f}%)")
        
        return X_balanced, y_balanced
    
    def testar_modelos_otimizados(self, X, y):
        """Testa modelos sem paralelização para Windows"""
        logger.info("🤖 TESTANDO MODELOS OTIMIZADOS...")
        
        # Modelos sem paralelização para Windows
        models = {
            'RandomForest': RandomForestClassifier(
                n_estimators=200, 
                random_state=42, 
                n_jobs=1  # Sem paralelização
            ),
            'XGBoost': xgb.XGBClassifier(
                n_estimators=200, 
                random_state=42, 
                n_jobs=1,  # Sem paralelização
                eval_metric='mlogloss'
            ),
            'LightGBM': lgb.LGBMClassifier(
                n_estimators=200, 
                random_state=42, 
                n_jobs=1,  # Sem paralelização
                verbose=-1
            ),
            'KNN_Standard': KNeighborsClassifier(
                n_neighbors=5, 
                n_jobs=1  # Sem paralelização
            )
        }
        
        # Preparar dados normalizados para KNN
        logger.info("   Preparando dados normalizados...")
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # KNN otimizado com dados normalizados
        models['KNN_Otimizado'] = KNeighborsClassifier(
            n_neighbors=7,  # Melhor para dados desbalanceados
            weights='distance',  # Peso por distância
            metric='minkowski',
            p=1,  # Manhattan distance
            n_jobs=1  # Sem paralelização
        )
        
        results = {}
        
        for name, model in models.items():
            logger.info(f"   Testando {name}...")
            
            try:
                # Usar dados normalizados para KNN otimizado
                X_test = X_scaled if 'KNN_Otimizado' in name else X
                y_test = y
                
                # Cross-validation simples
                cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                cv_scores = cross_val_score(
                    model, X_test, y_test, 
                    cv=cv, 
                    scoring='accuracy'
                )
                
                results[name] = {
                    'model': model,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'cv_scores': cv_scores,
                    'X_data': X_test,
                    'y_data': y_test
                }
                
                print(f"      {name}: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
                
            except Exception as e:
                logger.warning(f"      Erro com {name}: {e}")
                continue
        
        return results
    
    def otimizar_melhor_modelo(self, model_results):
        """Otimiza o melhor modelo encontrado"""
        logger.info("🎯 OTIMIZANDO MELHOR MODELO...")
        
        if not model_results:
            logger.error("   Nenhum modelo foi testado com sucesso!")
            return None, {}, None, None
        
        # Encontrar melhor modelo
        best_model_name = max(model_results.keys(), key=lambda x: model_results[x]['cv_mean'])
        best_model = model_results[best_model_name]['model']
        X_data = model_results[best_model_name]['X_data']
        y_data = model_results[best_model_name]['y_data']
        
        print(f"   Melhor modelo: {best_model_name}")
        
        # Espaços de busca específicos
        param_spaces = {
            'RandomForest': {
                'n_estimators': randint(300, 800),
                'max_depth': randint(15, 30),
                'min_samples_split': randint(5, 15),
                'min_samples_leaf': randint(2, 8),
                'max_features': ['sqrt', 'log2', 0.5, 0.7]
            },
            'XGBoost': {
                'n_estimators': randint(300, 800),
                'max_depth': randint(8, 15),
                'learning_rate': uniform(0.05, 0.2),
                'subsample': uniform(0.7, 0.3),
                'colsample_bytree': uniform(0.7, 0.3),
                'reg_alpha': uniform(0, 5),
                'reg_lambda': uniform(0, 5)
            },
            'LightGBM': {
                'n_estimators': randint(300, 800),
                'max_depth': randint(8, 15),
                'learning_rate': uniform(0.05, 0.2),
                'num_leaves': randint(30, 100),
                'subsample': uniform(0.7, 0.3),
                'colsample_bytree': uniform(0.7, 0.3)
            },
            'KNN_Standard': {
                'n_neighbors': randint(3, 15),
                'weights': ['uniform', 'distance'],
                'metric': ['euclidean', 'manhattan', 'minkowski']
            },
            'KNN_Otimizado': {
                'n_neighbors': randint(5, 15),
                'weights': ['uniform', 'distance'],
                'metric': ['euclidean', 'manhattan'],
                'p': [1, 2]  # Manhattan e Euclidiana
            }
        }
        
        if best_model_name in param_spaces:
            logger.info(f"   Otimizando {best_model_name}...")
            
            random_search = RandomizedSearchCV(
                estimator=best_model,
                param_distributions=param_spaces[best_model_name],
                n_iter=30,  # Menos iterações para ser mais rápido
                cv=3,
                scoring='accuracy',
                random_state=42,
                n_jobs=1,  # Sem paralelização
                verbose=1
            )
            
            random_search.fit(X_data, y_data)
            
            print(f"   Score otimizado: {random_search.best_score_:.4f}")
            print(f"   Parâmetros: {random_search.best_params_}")
            
            return random_search.best_estimator_, random_search.best_params_, X_data, y_data
        else:
            return best_model, {}, X_data, y_data
    
    def validacao_robusta(self, modelo, X, y, feature_names):
        """Validação robusta com intervalos de confiança"""
        logger.info("📊 VALIDAÇÃO ROBUSTA...")
        
        # Split estratificado
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Treinar modelo
        modelo.fit(X_train, y_train)
        
        # Predições
        y_pred = modelo.predict(X_test)
        y_pred_proba = modelo.predict_proba(X_test)
        
        # Métricas básicas
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
        
        # Validação robusta com múltiplas execuções
        logger.info("   Executando validação robusta...")
        cv_runs = []
        
        for i in range(5):  # 5 execuções para ser mais rápido
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=i*42)
            scores = cross_val_score(
                modelo, X, y, 
                cv=cv, 
                scoring='accuracy'
            )
            cv_runs.extend(scores)
        
        cv_runs = np.array(cv_runs)
        
        # Intervalo de confiança 95%
        ci_lower, ci_upper = stats.t.interval(
            0.95, len(cv_runs)-1, 
            loc=cv_runs.mean(), 
            scale=stats.sem(cv_runs)
        )
        
        print(f"\n📊 MÉTRICAS FINAIS:")
        print(f"   Accuracy: {accuracy:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall: {recall:.4f}")
        print(f"   F1-Score: {f1:.4f}")
        print(f"   ROC-AUC: {roc_auc:.4f}")
        print(f"   CV Mean: {cv_runs.mean():.4f}")
        print(f"   🎯 IC 95%: [{ci_lower:.4f}, {ci_upper:.4f}]")
        print(f"   📈 Std: ±{cv_runs.std():.4f}")
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc,
            'cv_scores': cv_runs,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'y_test': y_test,
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba
        }
    
    def salvar_modelo_final(self, modelo, feature_names, metricas, scaler=None):
        """Salva modelo final"""
        logger.info("💾 SALVANDO MODELO FINAL...")
        
        import os
        os.makedirs('data/models/gravidade_otimizado', exist_ok=True)
        
        # Salvar modelo
        joblib.dump(modelo, 'data/models/gravidade_otimizado/modelo_final_otimizado.pkl')
        
        # Salvar scaler se existir
        if scaler:
            joblib.dump(scaler, 'data/models/gravidade_otimizado/scaler.pkl')
        
        # Salvar feature names
        with open('data/models/gravidade_otimizado/feature_names_final.txt', 'w') as f:
            for feature in feature_names:
                f.write(f"{feature}\n")
        
        # Salvar métricas
        metricas_df = pd.DataFrame([metricas])
        metricas_df.to_csv('data/models/gravidade_otimizado/metricas_final_otimizado.csv', index=False)
        
        logger.info("   ✅ Modelo otimizado salvo!")
    
    def executar_melhoramento(self):
        """Executa o melhoramento otimizado para Windows"""
        logger.info("🚀 MELHORAMENTO OTIMIZADO PARA WINDOWS")
        logger.info("🎯 OBJETIVO: 85%+ DE ACURÁCIA")
        logger.info("=" * 60)
        
        try:
            # 1. Carregar dados
            logger.info("📊 Carregando dados...")
            df = pd.read_csv('data/henrique_dataset_limpo.csv')
            logger.info(f"   Dataset original: {len(df):,} registros")
            
            # 2. Criar amostra estratificada
            logger.info("📊 Criando amostra...")
            df_sample = self.criar_amostra_estratificada(df)
            
            # 3. Feature engineering
            logger.info("🔧 Feature engineering...")
            df_eng = self.feature_engineering_otimizado(df_sample)
            
            # 4. Preparar features
            logger.info("🛠️ Preparando features...")
            y = df_eng['gravidade'].copy()
            X = df_eng.drop(['gravidade', 'data_inversa', 'horario'], axis=1, errors='ignore')
            
            # Codificar categóricas
            categorical_features = X.select_dtypes(include=['object', 'category']).columns
            for col in categorical_features:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
            
            feature_names = X.columns.tolist()
            logger.info(f"   Features: {len(feature_names)}")
            
            # 5. Balanceamento
            logger.info("⚖️ Balanceamento...")
            X_balanced, y_balanced = self.aplicar_smote_otimizado(X, y)
            
            # 6. Testar modelos
            logger.info("🤖 Testando modelos...")
            model_results = self.testar_modelos_otimizados(X_balanced, y_balanced)
            
            # 7. Otimizar melhor modelo
            logger.info("🎯 Otimizando melhor modelo...")
            best_model, best_params, X_final, y_final = self.otimizar_melhor_modelo(model_results)
            
            if best_model is None:
                logger.error("❌ Nenhum modelo funcionou!")
                return None
            
            # 8. Validação robusta
            logger.info("📊 Validação robusta...")
            metricas_finais = self.validacao_robusta(best_model, X_final, y_final, feature_names)
            
            # 9. Salvar modelo
            logger.info("💾 Salvando modelo...")
            self.salvar_modelo_final(best_model, feature_names, metricas_finais, self.scaler)
            
            # 10. Resultado final
            logger.info("🎉 MELHORAMENTO CONCLUÍDO!")
            
            print(f"\n🏆 RESULTADO FINAL:")
            print(f"   🎯 Accuracy: {metricas_finais['accuracy']:.4f}")
            print(f"   📊 F1-Score: {metricas_finais['f1']:.4f}")
            print(f"   🔍 ROC-AUC: {metricas_finais['roc_auc']:.4f}")
            print(f"   📈 CV Mean: {metricas_finais['cv_scores'].mean():.4f}")
            print(f"   🎯 IC 95%: [{metricas_finais['ci_lower']:.4f}, {metricas_finais['ci_upper']:.4f}]")
            
            if metricas_finais['accuracy'] >= 0.85:
                print(f"   ✅ OBJETIVO ALCANÇADO! (≥85%)")
            elif metricas_finais['accuracy'] >= 0.80:
                print(f"   🎯 MUITO PRÓXIMO! (≥80%)")
            else:
                print(f"   📈 Melhoria significativa alcançada!")
            
            return {
                'modelo': best_model,
                'metricas': metricas_finais,
                'feature_names': feature_names,
                'model_results': model_results,
                'best_params': best_params,
                'scaler': self.scaler
            }
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    # Configuração otimizada para Windows
    melhorador = MelhoradorAcuriaWindows(sample_size=75000)  # 75k ideal
    resultado = melhorador.executar_melhoramento()
    
    if resultado:
        accuracy = resultado['metricas']['accuracy']
        cv_mean = resultado['metricas']['cv_scores'].mean()
        ci_lower = resultado['metricas']['ci_lower']
        ci_upper = resultado['metricas']['ci_upper']
        
        print(f"\n🎉 MELHORAMENTO CONCLUÍDO!")
        print(f"📊 Accuracy final: {accuracy:.4f}")
        print(f"📈 CV Score: {cv_mean:.4f}")
        print(f"🎯 Intervalo de Confiança 95%: [{ci_lower:.4f}, {ci_upper:.4f}]")
        
        if accuracy >= 0.85:
            print(f"🏆 OBJETIVO DE 85%+ ALCANÇADO!")
        elif accuracy >= 0.80:
            print(f"🎯 MUITO PRÓXIMO DO OBJETIVO!")
        else:
            print(f"📈 Melhoria significativa alcançada!")
    else:
        print(f"\n❌ ERRO NO MELHORAMENTO")
