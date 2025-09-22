#!/usr/bin/env python3
"""
CONFIGURAÇÕES DO SISTEMA PRF
============================

Configurações centralizadas para o sistema de previsão de severidade.
"""

import os
from pathlib import Path
from typing import Dict, Any

# ============================================================================
# CONFIGURAÇÕES DE PATHS
# ============================================================================

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).parent

# Paths dos modelos ML
MODEL_DIR = ROOT_DIR / "data" / "models"
MODEL_GRAVIDADE_DIR = MODEL_DIR / "gravidade_otimizado"

# Arquivos dos modelos
MODELO_GRAVIDADE_PATH = MODEL_GRAVIDADE_DIR / "modelo_final_otimizado.pkl"
SCALER_PATH = MODEL_GRAVIDADE_DIR / "scaler.pkl"
FEATURE_NAMES_PATH = MODEL_GRAVIDADE_DIR / "feature_names_final.txt"

# ============================================================================
# CONFIGURAÇÕES DE API
# ============================================================================

# APIs Externas
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "demo")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "demo")

# URLs das APIs
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
GOOGLE_MAPS_BASE_URL = "https://maps.googleapis.com/maps/api"

# Timeouts
API_TIMEOUT = 10
CACHE_TTL = 3600  # 1 hora

# ============================================================================
# CONFIGURAÇÕES DO MODELO ML
# ============================================================================

# Mapeamento de severidade
SEVERIDADE_MAP = {
    0: "SEM FERIDOS",
    1: "FERIDOS LEVES", 
    2: "FERIDOS GRAVES",
    3: "MORTOS"
}

# Features categóricas que precisam de encoding
CATEGORICAL_FEATURES = [
    'uf', 'municipio', 'tipo_acidente', 'fase_dia', 
    'condicao_metereologica', 'tipo_pista', 'tipo_veiculo', 'sexo'
]

# Features numéricas
NUMERICAL_FEATURES = [
    'br', 'km', 'idade', 'ano', 'mes', 'dia', 'dia_semana', 'hora',
    'hora_sin', 'hora_cos', 'mes_sin', 'mes_cos', 'dia_semana_sin', 
    'dia_semana_cos', 'eh_fim_semana', 'eh_madrugada', 'eh_noite', 
    'eh_rush_hour', 'densidade_hora', 'densidade_br', 'densidade_uf',
    'severidade_historica_veiculo', 'severidade_historica_uf', 
    'severidade_historica_pista', 'taxa_gravidade_local', 'trecho_5km',
    'densidade_trecho_5km', 'severidade_trecho_5km', 'trecho_25km',
    'densidade_trecho_25km', 'severidade_trecho_25km', 'trecho_50km',
    'densidade_trecho_50km', 'severidade_trecho_50km', 
    'ranking_periculosidade_br', 'ranking_periculosidade_uf', 
    'idade_hora', 'idade_veiculo'
]

# ============================================================================
# CONFIGURAÇÕES DE DADOS AUTOMÁTICOS
# ============================================================================

# Base de dados das BRs brasileiras
BRS_DATABASE = {
    116: {
        50: {"uf": "PR", "regiao": "Sul", "municipio": "Curitiba", "limite_velocidade": 80},
        100: {"uf": "PR", "regiao": "Sul", "municipio": "Curitiba", "limite_velocidade": 80},
        150: {"uf": "PR", "regiao": "Sul", "municipio": "Ponta Grossa", "limite_velocidade": 80},
        200: {"uf": "PR", "regiao": "Sul", "municipio": "Guarapuava", "limite_velocidade": 80},
        250: {"uf": "PR", "regiao": "Sul", "municipio": "Pato Branco", "limite_velocidade": 80},
        300: {"uf": "RS", "regiao": "Sul", "municipio": "Passo Fundo", "limite_velocidade": 80},
        350: {"uf": "RS", "regiao": "Sul", "municipio": "Santa Maria", "limite_velocidade": 80},
        400: {"uf": "RS", "regiao": "Sul", "municipio": "Porto Alegre", "limite_velocidade": 80},
    },
    101: {
        50: {"uf": "SP", "regiao": "Sudeste", "municipio": "São Paulo", "limite_velocidade": 80},
        100: {"uf": "SP", "regiao": "Sudeste", "municipio": "Santos", "limite_velocidade": 80},
        150: {"uf": "RJ", "regiao": "Sudeste", "municipio": "Rio de Janeiro", "limite_velocidade": 80},
        200: {"uf": "RJ", "regiao": "Sudeste", "municipio": "Niterói", "limite_velocidade": 80},
    },
    381: {
        50: {"uf": "SP", "regiao": "Sudeste", "municipio": "Campinas", "limite_velocidade": 90},
        100: {"uf": "MG", "regiao": "Sudeste", "municipio": "Belo Horizonte", "limite_velocidade": 90},
        150: {"uf": "MG", "regiao": "Sudeste", "municipio": "Uberaba", "limite_velocidade": 90},
    },
    40: {
        50: {"uf": "RJ", "regiao": "Sudeste", "municipio": "Rio de Janeiro", "limite_velocidade": 80},
        100: {"uf": "RJ", "regiao": "Sudeste", "municipio": "Nova Friburgo", "limite_velocidade": 80},
        150: {"uf": "ES", "regiao": "Sudeste", "municipio": "Vitória", "limite_velocidade": 80},
    },
    153: {
        50: {"uf": "MG", "regiao": "Sudeste", "municipio": "Belo Horizonte", "limite_velocidade": 90},
        100: {"uf": "MG", "regiao": "Sudeste", "municipio": "Uberaba", "limite_velocidade": 90},
        150: {"uf": "GO", "regiao": "Centro-Oeste", "municipio": "Goiânia", "limite_velocidade": 90},
    },
    262: {
        50: {"uf": "RS", "regiao": "Sul", "municipio": "Porto Alegre", "limite_velocidade": 80},
        100: {"uf": "RS", "regiao": "Sul", "municipio": "Santa Maria", "limite_velocidade": 80},
        150: {"uf": "SC", "regiao": "Sul", "municipio": "Florianópolis", "limite_velocidade": 80},
    },
    50: {
        50: {"uf": "PR", "regiao": "Sul", "municipio": "Curitiba", "limite_velocidade": 80},
        100: {"uf": "PR", "regiao": "Sul", "municipio": "Londrina", "limite_velocidade": 80},
        150: {"uf": "PR", "regiao": "Sul", "municipio": "Maringá", "limite_velocidade": 80},
    },
    80: {
        50: {"uf": "PA", "regiao": "Norte", "municipio": "Belém", "limite_velocidade": 80},
        67: {"uf": "PA", "regiao": "Norte", "municipio": "Ananindeua", "limite_velocidade": 80},
        100: {"uf": "MA", "regiao": "Nordeste", "municipio": "São Luís", "limite_velocidade": 80},
        150: {"uf": "MA", "regiao": "Nordeste", "municipio": "Imperatriz", "limite_velocidade": 80},
    }
}

# Fallback para BRs não encontradas
BRS_FALLBACK = {
    116: {"uf": "PR", "regiao": "Sul", "municipio": "Curitiba", "limite_velocidade": 80},
    101: {"uf": "SP", "regiao": "Sudeste", "municipio": "São Paulo", "limite_velocidade": 80},
    381: {"uf": "SP", "regiao": "Sudeste", "municipio": "Campinas", "limite_velocidade": 90},
    40: {"uf": "RJ", "regiao": "Sudeste", "municipio": "Rio de Janeiro", "limite_velocidade": 80},
    153: {"uf": "MG", "regiao": "Sudeste", "municipio": "Belo Horizonte", "limite_velocidade": 90},
    262: {"uf": "RS", "regiao": "Sul", "municipio": "Porto Alegre", "limite_velocidade": 80},
    50: {"uf": "PR", "regiao": "Sul", "municipio": "Curitiba", "limite_velocidade": 80},
    80: {"uf": "PA", "regiao": "Norte", "municipio": "Belém", "limite_velocidade": 80},
}

# ============================================================================
# CONFIGURAÇÕES DE LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# CONFIGURAÇÕES DE PERFORMANCE
# ============================================================================

# Cache settings
CACHE_MAX_SIZE = 1000
CACHE_DEFAULT_TTL = 3600  # 1 hora

# Model loading
MODEL_RELOAD_INTERVAL = 3600  # 1 hora

# API rate limiting
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_BURST = 10

# ============================================================================
# CONFIGURAÇÕES DE DESENVOLVIMENTO
# ============================================================================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
TESTING = os.getenv("TESTING", "False").lower() == "true"

# Mock external APIs em desenvolvimento
MOCK_EXTERNAL_APIS = DEBUG or TESTING
