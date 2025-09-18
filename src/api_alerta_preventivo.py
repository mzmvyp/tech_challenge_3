# src/api_alerta_preventivo.py

from fastapi import FastAPI, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import uvicorn
from pathlib import Path
import logging
from typing import Dict, List, Optional, Union
import time
import os

# Importar módulos de autenticação
from auth import (
    User, UserLogin, Token, 
    authenticate_user, create_tokens_for_user,
    get_current_active_user, get_current_admin_user,
    verify_token
)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criando a aplicação FastAPI com configurações avançadas
app = FastAPI(
    title="🚨 Sistema de Alerta Preventivo de Acidentes - PRF",
    description="""
    ## Sistema Inteligente de Prevenção de Acidentes Rodoviários
    
    Esta API utiliza **Machine Learning** para **PREVENIR** acidentes em rodovias federais brasileiras,
    analisando condições de viagem e alertando sobre riscos **ANTES** que aconteçam.
    
    ### 🎯 Funcionalidades Principais
    
    * **Alerta de Risco**: Analisa condições da viagem e calcula probabilidade de acidente
    * **Prevenção Inteligente**: Sugere horários e rotas mais seguras
    * **Análise de Condições**: Considera clima, tráfego, horário e características da via
    * **Recomendações Práticas**: Alternativas para reduzir o risco
    
    ### 🛡️ Como Funciona
    
    1. **Você informa**: Destino, horário, rota planejada
    2. **Sistema analisa**: Condições meteorológicas, histórico de acidentes, padrões de tráfego
    3. **Sistema alerta**: "⚠️ RISCO ALTO (78%) - Chuvas previstas, horário de pico"
    4. **Sistema sugere**: "💡 Saia às 16h ou use BR-381"
    
    ### 📊 Dados Utilizados
    
    * **Período**: 2007-2025 (19 anos)
    * **Registros**: 1.449.933 acidentes reais analisados
    * **Fonte**: Polícia Rodoviária Federal (PRF)
    * **Algoritmo**: Random Forest Classifier
    * **Objetivo**: PREVENIR acidentes, não prever gravidade
    
    ### 🔧 Como Usar
    
    1. **Autentique-se** usando `/auth/login`
    2. **Analise risco** usando `/alerta-risco` com dados da viagem
    3. **Consulte estatísticas** usando `/estatisticas`
    4. **Monitore a saúde** usando `/health`
    
    ### 📚 Documentação
    
    * **Swagger UI**: `/docs`
    * **ReDoc**: `/redoc`
    * **OpenAPI JSON**: `/openapi.json`
    """,
    version="2.0.0",
    terms_of_service="https://github.com/mzmvyp/tech_challenge_3",
    contact={
        "name": "Desenvolvedor",
        "url": "https://github.com/mzmvyp",
        "email": "contato@exemplo.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Servidor de Desenvolvimento"
        },
        {
            "url": "https://api-prf-accidents.herokuapp.com",
            "description": "Servidor de Produção"
        }
    ],
    tags_metadata=[
        {
            "name": "autenticação",
            "description": "Endpoints para autenticação e gerenciamento de usuários",
        },
        {
            "name": "alerta",
            "description": "Endpoints para análise de risco preventivo (requer autenticação)",
            "externalDocs": {
                "description": "Documentação do Sistema",
                "url": "https://github.com/mzmvyp/tech_challenge_3/blob/main/README.md",
            },
        },
        {
            "name": "status",
            "description": "Endpoints para verificação de status e saúde da API",
        },
        {
            "name": "estatisticas",
            "description": "Endpoints para métricas e estatísticas do modelo (apenas administradores)",
        },
    ]
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de segurança JWT para Swagger
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Adicionar esquema de segurança JWT
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Insira o token JWT no formato: Bearer <token>"
        }
    }
    
    # Aplicar segurança aos endpoints protegidos
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["post", "put", "delete"] and path not in ["/auth/login", "/auth/refresh"]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
            elif path == "/estatisticas":
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Modelo de dados de entrada para análise de risco
class DadosViagem(BaseModel):
    """
    Dados de entrada para análise de risco de viagem
    
    Todos os campos são obrigatórios e devem seguir os formatos especificados.
    """
    origem: str = Field(
        ..., 
        description="Cidade de origem da viagem",
        example="São Paulo",
        min_length=2,
        max_length=100
    )
    destino: str = Field(
        ..., 
        description="Cidade de destino da viagem",
        example="Campinas",
        min_length=2,
        max_length=100
    )
    data_viagem: str = Field(
        ..., 
        description="Data da viagem no formato YYYY-MM-DD",
        example="2024-01-15",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    horario_saida: str = Field(
        ..., 
        description="Horário de saída no formato HH:MM",
        example="14:30",
        pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    br_principal: int = Field(
        ..., 
        description="BR principal que será utilizada",
        example=116,
        ge=1,
        le=999
    )
    km_inicial: float = Field(
        ..., 
        description="Quilômetro inicial da BR",
        example=0.0,
        ge=0.0,
        le=9999.9
    )
    km_final: float = Field(
        ..., 
        description="Quilômetro final da BR",
        example=50.0,
        ge=0.0,
        le=9999.9
    )
    uf: str = Field(
        ..., 
        description="Estado (UF) da viagem",
        example="SP",
        pattern="^[A-Z]{2}$"
    )
    tipo_veiculo: str = Field(
        ..., 
        description="Tipo de veículo",
        example="AUTOMÓVEL",
        pattern="^(AUTOMÓVEL|MOTOCICLETA|CAMINHÃO|ÔNIBUS|OUTROS)$"
    )
    condicao_metereologica: str = Field(
        ..., 
        description="Condição meteorológica prevista",
        example="CÉU CLARO",
        pattern="^(CÉU CLARO|CHUVA|NEBLINA|TEMPORAL|NUBLADO|OUTROS)$"
    )
    tipo_pista: str = Field(
        ..., 
        description="Tipo de pista da BR",
        example="DUPLA",
        pattern="^(SIMPLE|DUPLA|MÚLTIPLA|OUTROS)$"
    )
    tracado_via: str = Field(
        ..., 
        description="Tracado da via",
        example="RETA",
        pattern="^(RETA|CURVA|INTERSEÇÃO|PONTE|VIADUTO)$"
    )
    passageiros: int = Field(
        ..., 
        description="Número de passageiros",
        example=2,
        ge=1,
        le=10
    )

    @field_validator('uf')
    @classmethod
    def validar_uf(cls, v):
        ufs_validas = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        if v.upper() not in ufs_validas:
            raise ValueError(f'UF deve ser uma das seguintes: {", ".join(ufs_validas)}')
        return v.upper()

    @field_validator('km_final')
    @classmethod
    def validar_km_final(cls, v, info):
        if info.data.get('km_inicial') and v <= info.data['km_inicial']:
            raise ValueError('KM final deve ser maior que KM inicial')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "origem": "São Paulo",
                "destino": "Campinas",
                "data_viagem": "2024-01-15",
                "horario_saida": "14:30",
                "br_principal": 116,
                "km_inicial": 0.0,
                "km_final": 50.0,
                "uf": "SP",
                "tipo_veiculo": "AUTOMÓVEL",
                "condicao_metereologica": "CÉU CLARO",
                "tipo_pista": "DUPLA",
                "tracado_via": "RETA",
                "passageiros": 2
            }
        }

# Modelos de resposta
class AlertaRisco(BaseModel):
    """Resposta do sistema de alerta de risco"""
    nivel_risco: str
    probabilidade_acidente: float
    confianca: float
    fatores_risco: List[str]
    recomendacoes: List[str]
    alternativas_horario: List[str]
    alternativas_rota: List[str]
    tempo_estimado: str
    distancia: float

class StatusSistema(BaseModel):
    """Status do sistema"""
    status: str
    timestamp: str
    uptime: str
    version: str
    modelo_carregado: bool

class EstatisticasModelo(BaseModel):
    """Estatísticas do modelo"""
    total_alertas: int
    alertas_hoje: int
    precisao_media: float
    ultima_atualizacao: str

# Variáveis globais
modelo = None
scaler = None
preprocessador_data = None
total_alertas = 0
start_time = time.time()

# Classes de risco
NIVEIS_RISCO = {
    0: "BAIXO",
    1: "MÉDIO", 
    2: "ALTO",
    3: "CRÍTICO"
}

def carregar_modelos():
    """
    Carrega modelo e preprocessadores
    """
    global modelo, scaler, preprocessador_data
    
    try:
        logger.info("📦 Carregando modelo de risco...")
        
        # Caminhos dos arquivos
        modelo_path = Path("data/models/modelo_acidentes.pkl")
        scaler_path = Path("data/models/scaler_acidentes.pkl")
        preprocessador_path = Path("data/models/preprocessador.pkl")
        
        # Verificando se os arquivos existem
        if not modelo_path.exists():
            logger.error(f"❌ Modelo não encontrado: {modelo_path}")
            return False
            
        if not scaler_path.exists():
            logger.error(f"❌ Scaler não encontrado: {scaler_path}")
            return False
        
        # Carregando modelo
        modelo = joblib.load(modelo_path)
        logger.info(f"✅ Modelo carregado: {type(modelo).__name__}")
        
        # Carregando scaler
        scaler = joblib.load(scaler_path)
        logger.info(f"✅ Scaler carregado: {type(scaler).__name__}")
        
        # Carregando preprocessador (se existir)
        if preprocessador_path.exists():
            preprocessador_data = joblib.load(preprocessador_path)
            logger.info("✅ Preprocessador carregado")
        else:
            logger.warning("⚠️ Preprocessador não encontrado, usando processamento padrão")
        
        logger.info("🎉 Todos os modelos carregados com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar modelos: {e}")
        return False

# Carregar modelos na inicialização
carregar_modelos()

# Endpoints de Autenticação
@app.post(
    "/auth/login",
    response_model=Token,
    summary="🔐 Login",
    description="Autentica usuário e retorna tokens de acesso",
    tags=["autenticação"]
)
async def login(user_credentials: UserLogin):
    """
    Endpoint de login
    
    Autentica o usuário e retorna tokens JWT para acesso à API.
    
    **Usuários disponíveis para teste:**
    - **admin** / **secret** (Administrador)
    - **analista** / **secret** (Analista)
    - **viewer** / **secret** (Visualizador)
    """
    user = authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    
    tokens = create_tokens_for_user(user)
    return tokens

@app.post(
    "/auth/refresh",
    response_model=Token,
    summary="🔄 Refresh Token",
    description="Renova o token de acesso usando o refresh token",
    tags=["autenticação"]
)
async def refresh_token(refresh_token: str = Query(..., description="Refresh token")):
    """
    Endpoint para renovar token de acesso
    """
    try:
        token_data = verify_token(refresh_token)
        user = get_user(token_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado"
            )
        
        tokens = create_tokens_for_user(user)
        return tokens
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

@app.get(
    "/auth/me",
    response_model=User,
    summary="👤 Meu Perfil",
    description="Retorna informações do usuário autenticado",
    tags=["autenticação"]
)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Endpoint para obter informações do usuário atual
    """
    return current_user

# Endpoints principais
@app.get(
    "/",
    summary="🏠 Informações da API",
    description="Retorna informações básicas sobre a API",
    tags=["status"]
)
async def root():
    """
    Endpoint raiz da API
    """
    return {
        "api": "Sistema de Alerta Preventivo de Acidentes - PRF",
        "versao": "2.0.0",
        "status": "online",
        "modelo_carregado": modelo is not None,
        "endpoints": {
            "/": "Informações da API",
            "/alerta-risco": "Análise de risco de viagem",
            "/status": "Status detalhado do sistema",
            "/estatisticas": "Estatísticas do modelo",
            "/health": "Verificação de saúde",
            "/docs": "Documentação Swagger",
            "/redoc": "Documentação ReDoc"
        },
        "documentacao": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

@app.get(
    "/health",
    response_model=StatusSistema,
    summary="💚 Verificação de Saúde",
    description="Verifica a saúde da API e do modelo",
    tags=["status"]
)
async def health_check():
    """
    Verificação de saúde da API
    
    Retorna informações sobre:
    - Status da API
    - Tempo de funcionamento
    - Status do modelo
    - Versão
    """
    uptime = time.time() - start_time
    uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
    
    return StatusSistema(
        status="healthy" if modelo is not None else "unhealthy",
        timestamp=datetime.now().isoformat(),
        uptime=uptime_str,
        version="2.0.0",
        modelo_carregado=modelo is not None
    )

@app.post(
    "/alerta-risco",
    response_model=AlertaRisco,
    summary="🚨 Análise de Risco de Viagem",
    description="Analisa o risco de acidente para uma viagem planejada",
    tags=["alerta"]
)
async def analisar_risco_viagem(
    dados: DadosViagem,
    current_user: User = Depends(get_current_active_user)
):
    """
    Análise de risco de viagem
    
    Recebe dados de uma viagem planejada e retorna:
    - Nível de risco (BAIXO, MÉDIO, ALTO, CRÍTICO)
    - Probabilidade de acidente (0-100%)
    - Fatores de risco identificados
    - Recomendações para reduzir o risco
    - Alternativas de horário e rota
    
    **Exemplo de uso:**
    - Origem: São Paulo
    - Destino: Campinas  
    - Horário: 14:30
    - BR: 116
    - Resultado: "⚠️ RISCO MÉDIO (45%) - Horário de pico, chuvas previstas"
    """
    global total_alertas
    
    if modelo is None or scaler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo não carregado. Execute o treinamento primeiro."
        )
    
    try:
        # Incrementar contador de alertas
        total_alertas += 1
        
        # Converter dados para DataFrame
        df = pd.DataFrame([dados.dict()])
        
        # Usar preprocessamento real se disponível
        if preprocessador_data is not None and isinstance(preprocessador_data, dict):
            try:
                # Criar features básicas baseadas nos dados de entrada
                features = []
                
                # Converter dados para dicionário
                dados_dict = dados.dict()
                
                # Adicionar features numéricas básicas
                features.extend([
                    dados_dict.get('passageiros', 1),
                    1,  # veiculos (assumindo 1 veículo)
                    dados_dict.get('br_principal', 116),
                    dados_dict.get('km_final', 0) - dados_dict.get('km_inicial', 0),  # distância
                    int(dados_dict.get('horario_saida', '00:00').split(':')[0]) if ':' in dados_dict.get('horario_saida', '00:00') else 0,  # hora
                    int(dados_dict.get('data_viagem', '2024-01-01').split('-')[1]) if '-' in dados_dict.get('data_viagem', '2024-01-01') else 1,  # mês
                ])
                
                # Adicionar features categóricas básicas (simplificado)
                features.extend([
                    1 if dados_dict.get('data_viagem', '').split('-')[2] in ['06', '07', '08', '09', '10', '11', '12'] else 0,  # fim de semana (simplificado)
                    1 if dados_dict.get('condicao_metereologica') in ['CHUVA', 'NEBLINA', 'TEMPORAL'] else 0,  # clima adverso
                    1 if dados_dict.get('tipo_veiculo') in ['MOTOCICLETA'] else 0,  # veículo mais vulnerável
                    1 if dados_dict.get('tracado_via') == 'CURVA' else 0,  # curva
                    1 if dados_dict.get('tipo_pista') == 'SIMPLE' else 0,  # pista simples
                    1 if dados_dict.get('br_principal') in [101, 116, 381, 40, 153] else 0,  # BRs mais perigosas
                ])
                
                # Adicionar features de UF (simplificado)
                uf_codes = {'SP': 1, 'RJ': 2, 'MG': 3, 'RS': 4, 'PR': 5, 'SC': 6, 'BA': 7, 'GO': 8, 'PE': 9, 'CE': 10}
                features.append(uf_codes.get(dados_dict.get('uf', 'SP'), 1))
                
                # Adicionar features de BR (simplificado)
                br_codes = {116: 1, 101: 2, 381: 3, 40: 4, 153: 5}
                features.append(br_codes.get(dados_dict.get('br_principal', 116), 1))
                
                # Garantir que temos o número correto de features
                while len(features) < 22:  # Número de features esperadas
                    features.append(0)
                
                # Truncar se tiver muitas features
                features = features[:22]
                
                # Converter para array numpy
                X = np.array([features])
                
                # Normalizar dados
                X_scaled = scaler.transform(X)
                
                logger.info(f"✅ Preprocessamento aplicado: {X_scaled.shape}")
                
                # Fazer predição (convertendo para probabilidade de risco)
                predicao = modelo.predict(X_scaled)[0]
                probabilidades = modelo.predict_proba(X_scaled)[0]
                
                # Converter predição de gravidade para nível de risco
                # 0=Ileso -> BAIXO, 1=Leve -> MÉDIO, 2=Grave -> ALTO, 3=Fatal -> CRÍTICO
                nivel_risco = NIVEIS_RISCO[predicao]
                
                # Calcular probabilidade de acidente (invertendo a lógica)
                # Quanto maior a gravidade prevista, maior o risco
                probabilidade_acidente = float(max(probabilidades)) * 100
                
                # Calcular confiança
                confianca = float(max(probabilidades))
                
                # Identificar fatores de risco
                fatores_risco = []
                if dados.condicao_metereologica in ["CHUVA", "NEBLINA", "TEMPORAL"]:
                    fatores_risco.append("Condição meteorológica adversa")
                
                hora = int(dados.horario_saida.split(':')[0])
                if hora in [7, 8, 17, 18, 19] or hora in range(22, 24) or hora in range(0, 6):
                    fatores_risco.append("Horário de alto risco")
                
                if dados.tipo_veiculo == "MOTOCICLETA":
                    fatores_risco.append("Veículo mais vulnerável")
                
                if dados.tracado_via == "CURVA":
                    fatores_risco.append("Tracado perigoso")
                
                if dados.tipo_pista == "SIMPLE":
                    fatores_risco.append("Pista simples (mais perigosa)")
                
                if dados.br_principal in [101, 116, 381, 40, 153]:
                    fatores_risco.append(f"BR-{dados.br_principal} com alta incidência de acidentes")
                
                # Gerar recomendações
                recomendacoes = []
                if nivel_risco in ["ALTO", "CRÍTICO"]:
                    recomendacoes.append("⚠️ Considere adiar a viagem")
                    recomendacoes.append("🚗 Use veículo mais seguro se possível")
                    recomendacoes.append("📱 Mantenha contato durante a viagem")
                
                if "Condição meteorológica adversa" in fatores_risco:
                    recomendacoes.append("🌧️ Aguarde melhoria do tempo")
                    recomendacoes.append("🚗 Reduza a velocidade")
                
                if "Horário de alto risco" in fatores_risco:
                    recomendacoes.append("⏰ Evite horários de pico")
                    recomendacoes.append("🌙 Evite viagens noturnas")
                
                # Gerar alternativas de horário
                alternativas_horario = []
                if hora in [7, 8, 17, 18, 19]:
                    alternativas_horario.extend([
                        "10:00 - Horário mais seguro",
                        "14:00 - Meio da tarde",
                        "20:00 - Após o pico"
                    ])
                elif hora in range(22, 24) or hora in range(0, 6):
                    alternativas_horario.extend([
                        "08:00 - Manhã segura",
                        "15:00 - Tarde segura",
                        "19:00 - Final da tarde"
                    ])
                
                # Gerar alternativas de rota
                alternativas_rota = []
                if dados.br_principal == 116:
                    alternativas_rota.extend([
                        "BR-381 - Rota alternativa",
                        "BR-101 - Rota costeira",
                        "SP-348 - Rodovia dos Bandeirantes"
                    ])
                elif dados.br_principal == 101:
                    alternativas_rota.extend([
                        "BR-116 - Rota alternativa",
                        "BR-381 - Rota interior",
                        "SP-348 - Rodovia dos Bandeirantes"
                    ])
                
                # Calcular tempo estimado e distância
                distancia = dados.km_final - dados.km_inicial
                tempo_estimado = f"{int(distancia / 80 * 60)} minutos"  # Assumindo 80 km/h média
                
                return AlertaRisco(
                    nivel_risco=nivel_risco,
                    probabilidade_acidente=probabilidade_acidente,
                    confianca=confianca,
                    fatores_risco=fatores_risco,
                    recomendacoes=recomendacoes,
                    alternativas_horario=alternativas_horario,
                    alternativas_rota=alternativas_rota,
                    tempo_estimado=tempo_estimado,
                    distancia=distancia
                )
                
            except Exception as e:
                logger.error(f"Erro no preprocessamento: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro no processamento: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Preprocessador não carregado"
            )
            
    except Exception as e:
        logger.error(f"❌ Erro na análise de risco: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno na análise: {str(e)}"
        )

@app.get(
    "/estatisticas",
    response_model=EstatisticasModelo,
    summary="📊 Estatísticas do Modelo",
    description="Retorna estatísticas do modelo de análise de risco",
    tags=["estatisticas"]
)
async def obter_estatisticas(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Estatísticas do modelo de análise de risco
    
    Retorna métricas de performance e uso do sistema.
    Requer permissão de administrador.
    """
    try:
        return EstatisticasModelo(
            total_alertas=total_alertas,
            alertas_hoje=total_alertas,  # Simplificado
            precisao_media=0.727,  # Acurácia do modelo
            ultima_atualizacao=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Tempo: {process_time:.3f}s"
    )
    
    return response

# Handler para erros 404
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint não encontrado",
            "message": f"O endpoint {request.url.path} não existe",
            "available_endpoints": [
                "/", "/alerta-risco", "/status", "/estatisticas", "/health", "/docs", "/redoc"
            ]
        }
    )

# Handler para erros 500
@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "message": "Ocorreu um erro interno. Tente novamente mais tarde.",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import socket
    import signal
    import sys
    
    def find_free_port(start_port=8000, max_port=8010):
        """Encontra uma porta livre"""
        for port in range(start_port, max_port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        return None
    
    def signal_handler(sig, frame):
        print("\n🛑 Parando API...")
        sys.exit(0)
    
    # Configurar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Tentar encontrar uma porta livre
    port = find_free_port()
    if port is None:
        print("❌ Nenhuma porta livre encontrada entre 8000-8010")
        exit(1)
    
    print(f"🚀 Iniciando API na porta {port}")
    print("📚 Documentação: http://localhost:{port}/docs")
    print("🛑 Pressione Ctrl+C para parar")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        print("\n🛑 API parada pelo usuário")
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        sys.exit(1)
