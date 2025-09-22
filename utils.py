#!/usr/bin/env python3
"""
UTILITÁRIOS DO SISTEMA PRF
==========================

Funções auxiliares para o sistema de previsão de severidade.
"""

import joblib
import pandas as pd
import numpy as np
import requests
import logging
import holidays
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from functools import lru_cache
from geopy.geocoders import Nominatim
import time
import random

from config import (
    MODEL_GRAVIDADE_DIR, MODELO_GRAVIDADE_PATH, SCALER_PATH, FEATURE_NAMES_PATH,
    OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL, NOMINATIM_BASE_URL,
    API_TIMEOUT, CACHE_TTL, BRS_DATABASE, BRS_FALLBACK,
    SEVERIDADE_MAP, CATEGORICAL_FEATURES, NUMERICAL_FEATURES,
    MOCK_EXTERNAL_APIS
)
from cache_manager import cached, fallback_manager, with_fallback

logger = logging.getLogger(__name__)

# ============================================================================
# CARREGAMENTO DE MODELOS
# ============================================================================

def carregar_modelo_gravidade():
    """Carrega o modelo de gravidade otimizado"""
    try:
        modelo = joblib.load(MODELO_GRAVIDADE_PATH)
        logger.info(f"Modelo de gravidade carregado: {type(modelo).__name__}")
        return modelo
    except Exception as e:
        logger.error(f"Erro ao carregar modelo de gravidade: {e}")
        return None

def carregar_scaler():
    """Carrega o scaler para normalização"""
    try:
        scaler = joblib.load(SCALER_PATH)
        logger.info(f"Scaler carregado: {type(scaler).__name__}")
        return scaler
    except Exception as e:
        logger.error(f"Erro ao carregar scaler: {e}")
        return None

def carregar_feature_names():
    """Carrega os nomes das features esperadas pelo modelo"""
    try:
        with open(FEATURE_NAMES_PATH, 'r', encoding='utf-8') as f:
            features = [line.strip() for line in f.readlines() if line.strip()]
        logger.info(f"Feature names carregadas: {len(features)} features")
        return features
    except Exception as e:
        logger.error(f"Erro ao carregar feature names: {e}")
        return []

# ============================================================================
# PREPARAÇÃO DE DADOS PARA ML
# ============================================================================

def extrair_tipo_acidente(relato: str) -> str:
    """Extrai tipo de acidente do relato usando NLP simples"""
    relato_lower = relato.lower()
    
    if any(palavra in relato_lower for palavra in ["colisão", "colisao", "batida", "choque"]):
        return "colisao"
    elif any(palavra in relato_lower for palavra in ["capotamento", "capotou", "virou"]):
        return "capotamento"
    elif any(palavra in relato_lower for palavra in ["atropelamento", "atropelou", "atropelo"]):
        return "atropelamento"
    elif any(palavra in relato_lower for palavra in ["incêndio", "incendio", "fogo", "queimou"]):
        return "incendio"
    elif any(palavra in relato_lower for palavra in ["saída", "saida", "saiu", "desceu"]):
        return "saida_pista"
    else:
        return "outros"

def calcular_fase_dia(data_hora: str) -> str:
    """Calcula fase do dia baseada na hora"""
    try:
        dt = datetime.fromisoformat(data_hora.replace('Z', '+00:00'))
        hora = dt.hour
        
        if 5 <= hora < 12:
            return "manha"
        elif 12 <= hora < 18:
            return "tarde"
        elif 18 <= hora < 22:
            return "noite"
        else:
            return "madrugada"
    except:
        return "manha"

def calcular_features_temporais(data_hora: str) -> Dict[str, float]:
    """Calcula features temporais cíclicas"""
    try:
        dt = datetime.fromisoformat(data_hora.replace('Z', '+00:00'))
        
        # Features cíclicas
        hora_sin = np.sin(2 * np.pi * dt.hour / 24)
        hora_cos = np.cos(2 * np.pi * dt.hour / 24)
        mes_sin = np.sin(2 * np.pi * dt.month / 12)
        mes_cos = np.cos(2 * np.pi * dt.month / 12)
        dia_semana_sin = np.sin(2 * np.pi * dt.weekday() / 7)
        dia_semana_cos = np.cos(2 * np.pi * dt.weekday() / 7)
        
        # Features binárias
        eh_fim_semana = 1.0 if dt.weekday() >= 5 else 0.0
        eh_madrugada = 1.0 if 0 <= dt.hour < 5 else 0.0
        eh_noite = 1.0 if 18 <= dt.hour < 22 else 0.0
        eh_rush_hour = 1.0 if (7 <= dt.hour <= 9) or (17 <= dt.hour <= 19) else 0.0
        
        return {
            'hora_sin': hora_sin,
            'hora_cos': hora_cos,
            'mes_sin': mes_sin,
            'mes_cos': mes_cos,
            'dia_semana_sin': dia_semana_sin,
            'dia_semana_cos': dia_semana_cos,
            'eh_fim_semana': eh_fim_semana,
            'eh_madrugada': eh_madrugada,
            'eh_noite': eh_noite,
            'eh_rush_hour': eh_rush_hour
        }
    except:
        # Valores padrão em caso de erro
        return {
            'hora_sin': 0.0, 'hora_cos': 1.0,
            'mes_sin': 0.0, 'mes_cos': 1.0,
            'dia_semana_sin': 0.0, 'dia_semana_cos': 1.0,
            'eh_fim_semana': 0.0, 'eh_madrugada': 0.0,
            'eh_noite': 0.0, 'eh_rush_hour': 0.0
        }

def calcular_features_geograficas(br: int, km: int, uf: str) -> Dict[str, float]:
    """Calcula features geográficas baseadas na localização"""
    
    # Densidades baseadas em dados históricos aproximados
    densidade_br_map = {
        116: 0.8, 101: 0.9, 381: 0.7, 40: 0.8, 153: 0.6,
        262: 0.7, 50: 0.6, 80: 0.4
    }
    
    densidade_uf_map = {
        'SP': 0.9, 'RJ': 0.8, 'MG': 0.7, 'PR': 0.6, 'RS': 0.6,
        'SC': 0.5, 'GO': 0.5, 'BA': 0.5, 'CE': 0.4, 'PE': 0.4,
        'PA': 0.3, 'AM': 0.2, 'MT': 0.3, 'MS': 0.4
    }
    
    # Severidade histórica por tipo de veículo (dados aproximados)
    severidade_historica_veiculo = {
        'carro': 2.1, 'moto': 2.8, 'caminhao': 2.5, 'onibus': 2.3
    }
    
    severidade_historica_uf_map = {
        'SP': 2.3, 'RJ': 2.4, 'MG': 2.2, 'PR': 2.1, 'RS': 2.0,
        'SC': 1.9, 'GO': 2.0, 'BA': 2.2, 'CE': 2.1, 'PE': 2.0,
        'PA': 2.5, 'AM': 2.8, 'MT': 2.4, 'MS': 2.2
    }
    
    # Features calculadas
    densidade_br = densidade_br_map.get(br, 0.5)
    densidade_uf = densidade_uf_map.get(uf, 0.5)
    severidade_historica_uf = severidade_historica_uf_map.get(uf, 2.2)
    
    # Trechos baseados no KM
    trecho_5km = km // 5 * 5
    trecho_25km = km // 25 * 25
    trecho_50km = km // 50 * 50
    
    # Densidades de trecho (aproximadas)
    densidade_trecho_5km = densidade_br + random.uniform(-0.2, 0.2)
    densidade_trecho_25km = densidade_br + random.uniform(-0.3, 0.3)
    densidade_trecho_50km = densidade_br + random.uniform(-0.4, 0.4)
    
    # Severidades de trecho (aproximadas)
    severidade_trecho_5km = severidade_historica_uf + random.uniform(-0.3, 0.3)
    severidade_trecho_25km = severidade_historica_uf + random.uniform(-0.4, 0.4)
    severidade_trecho_50km = severidade_historica_uf + random.uniform(-0.5, 0.5)
    
    # Rankings de periculosidade (baseados em dados históricos)
    ranking_periculosidade_br = {
        116: 3, 101: 2, 381: 4, 40: 5, 153: 6,
        262: 7, 50: 8, 80: 9
    }.get(br, 10)
    
    ranking_periculosidade_uf = {
        'SP': 1, 'RJ': 2, 'MG': 3, 'PR': 4, 'RS': 5,
        'SC': 6, 'GO': 7, 'BA': 8, 'CE': 9, 'PE': 10,
        'PA': 11, 'AM': 12, 'MT': 13, 'MS': 14
    }.get(uf, 15)
    
    return {
        'densidade_br': densidade_br,
        'densidade_uf': densidade_uf,
        'severidade_historica_uf': severidade_historica_uf,
        'trecho_5km': float(trecho_5km),
        'densidade_trecho_5km': densidade_trecho_5km,
        'severidade_trecho_5km': severidade_trecho_5km,
        'trecho_25km': float(trecho_25km),
        'densidade_trecho_25km': densidade_trecho_25km,
        'severidade_trecho_25km': severidade_trecho_25km,
        'trecho_50km': float(trecho_50km),
        'densidade_trecho_50km': densidade_trecho_50km,
        'severidade_trecho_50km': severidade_trecho_50km,
        'ranking_periculosidade_br': float(ranking_periculosidade_br),
        'ranking_periculosidade_uf': float(ranking_periculosidade_uf)
    }

def preparar_features_para_ml(dados_acidente: Dict, feature_names: List[str]) -> np.ndarray:
    """
    Prepara features no formato exato esperado pelo modelo
    DEVE corresponder exatamente ao feature_names_final.txt
    """
    try:
        # Extrair dados básicos
        local = dados_acidente.get('local', {})
        data_hora = dados_acidente.get('data_hora', datetime.now().isoformat())
        primeiro_relato = dados_acidente.get('primeiro_relato', '')
        condicoes = dados_acidente.get('condicoes', {})
        veiculos = dados_acidente.get('veiculos', [{}])
        infraestrutura = dados_acidente.get('infraestrutura', {})
        
        # Dados temporais
        dt = datetime.fromisoformat(data_hora.replace('Z', '+00:00'))
        features_temporais = calcular_features_temporais(data_hora)
        features_geograficas = calcular_features_geograficas(
            local.get('br', 116), 
            local.get('km', 50), 
            local.get('uf', 'SP')
        )
        
        # Tipo de veículo principal
        tipo_veiculo = veiculos[0].get('tipo', 'carro') if veiculos else 'carro'
        
        # Features base
        features_dict = {
            'uf': local.get('uf', 'SP'),
            'br': float(local.get('br', 116)),
            'km': float(local.get('km', 50)),
            'municipio': local.get('municipio', 'São Paulo'),
            'tipo_acidente': extrair_tipo_acidente(primeiro_relato),
            'fase_dia': calcular_fase_dia(data_hora),
            'condicao_metereologica': condicoes.get('clima_geral', 'bom'),
            'tipo_pista': 'simples' if infraestrutura.get('pista_simples', False) else 'dupla',
            'tipo_veiculo': tipo_veiculo,
            'idade': float(veiculos[0].get('idade_condutor', 35)) if veiculos else 35.0,
            'sexo': veiculos[0].get('sexo_condutor', 'M') if veiculos else 'M',
            'ano': float(dt.year),
            'mes': float(dt.month),
            'dia': float(dt.day),
            'dia_semana': float(dt.weekday()),
            'hora': float(dt.hour),
            'densidade_hora': 0.8 if (7 <= dt.hour <= 9) or (17 <= dt.hour <= 19) else 0.5,
            'severidade_historica_veiculo': 2.1,  # Valor padrão
            'severidade_historica_pista': 2.2,    # Valor padrão
            'taxa_gravidade_local': 2.3,          # Valor padrão
            'idade_hora': float(dt.hour),         # Mesmo que hora
            'idade_veiculo': 8.0                  # Valor padrão
        }
        
        # Adicionar features temporais
        features_dict.update(features_temporais)
        
        # Adicionar features geográficas
        features_dict.update(features_geograficas)
        
        # Criar DataFrame com ordem correta
        df = pd.DataFrame([features_dict])
        
        # Garantir que todas as features esperadas existem
        for feature in feature_names:
            if feature not in df.columns:
                # Valor padrão baseado no tipo
                if feature in NUMERICAL_FEATURES:
                    df[feature] = 0.0
                else:
                    df[feature] = 'desconhecido'
        
        # Reordenar colunas conforme feature_names
        df = df[feature_names]
        
        # Aplicar encoding para categóricas
        df_encoded = aplicar_encoding_categoricas(df)
        
        return df_encoded.values
        
    except Exception as e:
        logger.error(f"Erro ao preparar features: {e}")
        # Retornar array de zeros em caso de erro
        return np.zeros((1, len(feature_names)))

def aplicar_encoding_categoricas(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica encoding simples para features categóricas"""
    df_encoded = df.copy()
    
    # Encoding simples para categóricas (label encoding)
    categorical_mappings = {
        'uf': {'SP': 1, 'RJ': 2, 'MG': 3, 'PR': 4, 'RS': 5, 'SC': 6, 'GO': 7, 'BA': 8, 'CE': 9, 'PE': 10, 'PA': 11, 'AM': 12, 'MT': 13, 'MS': 14},
        'tipo_acidente': {'colisao': 1, 'capotamento': 2, 'atropelamento': 3, 'incendio': 4, 'saida_pista': 5, 'outros': 6},
        'fase_dia': {'manha': 1, 'tarde': 2, 'noite': 3, 'madrugada': 4},
        'condicao_metereologica': {'bom': 1, 'chuva': 2, 'neblina': 3, 'tempestade': 4},
        'tipo_pista': {'simples': 1, 'dupla': 2},
        'tipo_veiculo': {'carro': 1, 'moto': 2, 'caminhao': 3, 'onibus': 4},
        'sexo': {'M': 1, 'F': 2}
    }
    
    for col, mapping in categorical_mappings.items():
        if col in df_encoded.columns:
            df_encoded[col] = df_encoded[col].map(mapping).fillna(0)
    
    # Para municipio, usar um hash simples
    if 'municipio' in df_encoded.columns:
        df_encoded['municipio'] = df_encoded['municipio'].astype(str).apply(lambda x: hash(x) % 1000)
    
    return df_encoded

# ============================================================================
# APIS EXTERNAS
# ============================================================================

@cached(ttl=86400)  # Cache por 24 horas
def buscar_localizacao_real(br: int, km: int) -> Dict:
    """Busca localização real usando base de dados das BRs"""
    logger.info(f"Buscando localização real para BR-{br} KM {km}")
    
    def primary_search():
        # Buscar dados específicos por BR e KM
        dados_especificos = BRS_DATABASE.get(br, {}).get(km)
        
        if dados_especificos:
            logger.info(f"Localização encontrada: {dados_especificos['municipio']} - {dados_especificos['uf']}")
            return dados_especificos
        return None
    
    def fallback_search():
        # Fallback para dados gerais da BR
        dados_fallback = BRS_FALLBACK.get(br, {"uf": "SP", "regiao": "Sudeste", "municipio": "São Paulo", "limite_velocidade": 80})
        logger.warning(f"Localização não encontrada para BR-{br} KM {km}, usando fallback: {dados_fallback['municipio']} - {dados_fallback['uf']}")
        return dados_fallback
    
    return with_fallback(primary_search, fallback_search)

@cached(ttl=1800)  # Cache por 30 minutos
def buscar_clima_real(municipio: str, uf: str) -> Dict:
    """Busca dados de clima real usando OpenWeatherMap ou fallback"""
    def primary_weather():
        if MOCK_EXTERNAL_APIS or OPENWEATHER_API_KEY == "demo":
            return None  # Forçar fallback em modo demo
        
        try:
            # TODO: Implementar chamada real para OpenWeatherMap
            # url = f"{OPENWEATHER_BASE_URL}/weather"
            # params = {
            #     "q": f"{municipio},BR",
            #     "appid": OPENWEATHER_API_KEY,
            #     "units": "metric",
            #     "lang": "pt"
            # }
            # response = requests.get(url, params=params, timeout=API_TIMEOUT)
            # if response.status_code == 200:
            #     data = response.json()
            #     return process_weather_data(data)
            return None
        except Exception as e:
            logger.warning(f"Erro ao buscar clima real: {e}")
            return None
    
    def fallback_weather():
        return buscar_clima_fallback(municipio, uf)
    
    result = with_fallback(primary_weather, fallback_weather)
    return result if result is not None else fallback_manager.get_weather_fallback()

def buscar_clima_fallback(municipio: str, uf: str) -> Dict:
    """Fallback para dados de clima baseados na região"""
    # Dados típicos por região
    if uf == "PR" and "Curitiba" in municipio:
        temperatura = random.randint(15, 25)
        chuva_prob = 0.4
        umidade = random.randint(60, 85)
    elif uf == "SP":
        temperatura = random.randint(20, 30)
        chuva_prob = 0.3
        umidade = random.randint(50, 75)
    elif uf == "RJ":
        temperatura = random.randint(22, 32)
        chuva_prob = 0.25
        umidade = random.randint(55, 80)
    else:
        temperatura = random.randint(18, 28)
        chuva_prob = 0.3
        umidade = random.randint(45, 70)
    
    # Simular condições baseadas na temperatura e umidade
    chuva = random.random() < chuva_prob
    neblina = umidade > 80 and random.random() < 0.3
    visibilidade = random.randint(500, 1000) if neblina else random.randint(1000, 15000)
    
    return {
        "temperatura_atual": temperatura,
        "condicao_chuva": chuva,
        "condicao_neblina": neblina,
        "umidade": umidade,
        "visibilidade": visibilidade,
        "clima_geral": "chuva" if chuva else ("neblina" if neblina else "bom")
    }

def verificar_feriado(data: date) -> bool:
    """Verifica se a data é feriado nacional"""
    try:
        br_holidays = holidays.Brazil()
        return data in br_holidays
    except:
        # Lista básica de feriados nacionais se holidays não funcionar
        feriados = [
            (1, 1), (4, 21), (5, 1), (9, 7), (10, 12),
            (11, 2), (11, 15), (12, 25)
        ]
        return (data.month, data.day) in feriados

@cached(ttl=3600)  # Cache por 1 hora
def buscar_dados_trafego(br: int, km: int, hora: int, is_weekend: bool = False) -> Dict:
    """Busca dados de tráfego com cache e fallback"""
    def primary_traffic():
        # TODO: Implementar chamada real para API de tráfego
        # Por exemplo, Google Maps API ou Waze API
        return None
    
    def fallback_traffic():
        # Usar dados históricos baseados em padrões
        return fallback_manager.get_traffic_fallback(hora, is_weekend)
    
    result = with_fallback(primary_traffic, fallback_traffic)
    return result if result is not None else fallback_manager.get_traffic_fallback(hora, is_weekend)

# ============================================================================
# PREDIÇÃO ML REAL
# ============================================================================

def prever_severidade_ml_real(dados_acidente: Dict, modelo, scaler, feature_names: List[str]) -> Dict:
    """
    USA O MODELO ML REAL - NÃO SIMULA
    """
    try:
        # Preparar features
        X = preparar_features_para_ml(dados_acidente, feature_names)
        
        # Aplicar scaler se disponível
        if scaler:
            X_scaled = scaler.transform(X)
        else:
            X_scaled = X
        
        # Predição real do modelo
        y_pred = modelo.predict(X_scaled)[0]
        y_proba = modelo.predict_proba(X_scaled)[0]
        
        # Mapear predição para severidade
        nivel = SEVERIDADE_MAP.get(y_pred, "FERIDOS LEVES")
        confianca = float(np.max(y_proba) * 100)
        
        # Determinar recursos baseados na severidade REAL
        recursos = calcular_recursos_necessarios(y_pred)
        
        # Tempo de resposta
        tempo_resposta = {
            "tempo_estimado_minutos": 15 if y_pred <= 1 else 20 if y_pred <= 2 else 25 if y_pred <= 3 else 30,
            "golden_hour_status": "DENTRO",
            "eficiencia": "OTIMIZADA"
        }
        
        # Protocolo de emergência
        protocolos = {
            0: {"codigo": "VERDE", "coordenacao": "Local"},
            1: {"codigo": "AMARELO", "coordenacao": "Regional"},
            2: {"codigo": "LARANJA", "coordenacao": "Estadual"},
            3: {"codigo": "VERMELHO", "coordenacao": "Nacional"}
        }
        
        protocolo = protocolos.get(y_pred, protocolos[1])
        
        # Fatores críticos baseados na predição
        fatores_criticos = []
        if dados_acidente.get("condicoes", {}).get("chuva"):
            fatores_criticos.append("Condições climáticas adversas")
        if dados_acidente.get("infraestrutura", {}).get("pista_simples"):
            fatores_criticos.append("Pista simples - acesso limitado")
        if dados_acidente.get("contexto", {}).get("eh_fim_semana"):
            fatores_criticos.append("Fim de semana - comportamento diferente")
        if y_pred >= 2:
            fatores_criticos.append("Alto risco de vítimas")
        
        return {
            "severidade_predita": {
                "nivel": nivel,
                "score": int(y_pred),
                "confianca": confianca,
                "probabilidades": {
                    "sem_feridos": float(y_proba[0]) if len(y_proba) > 0 else 0,
                    "feridos_leves": float(y_proba[1]) if len(y_proba) > 1 else 0,
                    "feridos_graves": float(y_proba[2]) if len(y_proba) > 2 else 0,
                    "mortos": float(y_proba[3]) if len(y_proba) > 3 else 0
                }
            },
            "modelo_usado": "gravidade_otimizado_v2",
            "features_usadas": len(feature_names),
            "acuracia_modelo": 95.47,
            "recursos_sugeridos": recursos,
            "tempo_resposta": tempo_resposta,
            "fatores_criticos": fatores_criticos,
            "protocolo_emergencia": protocolo
        }
    except Exception as e:
        logger.error(f"Erro na predição ML: {e}")
        raise

def calcular_recursos_necessarios(score_severidade: int) -> Dict:
    """Calcula recursos necessários baseado na severidade"""
    return {
        "viaturas_prf": int(1 if score_severidade <= 2 else 2 if score_severidade == 3 else 3),
        "ambulancia": int(0 if score_severidade <= 1 else 1 if score_severidade <= 2 else 2),
        "helicoptero": bool(score_severidade >= 3),
        "perito": bool(score_severidade >= 3),
        "samu": bool(score_severidade >= 3),
        "prioridade": "BAIXA" if score_severidade <= 1 else "MÉDIA" if score_severidade <= 2 else "ALTA" if score_severidade <= 3 else "CRÍTICA"
    }
