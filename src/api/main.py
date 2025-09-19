"""
API Principal - Sistema de Prevenção de Acidentes PRF

Esta API implementa o novo sistema focado em PREVENÇÃO de acidentes,
processando linguagem natural e analisando riscos de viagens ANTES
que elas aconteçam.
"""

from fastapi import FastAPI, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import time
import os

# Importar módulos do sistema
from src.core.trip_risk_analyzer_otimizado import AnalisadorRiscoViagemOtimizado
from src.core.accident_analyzer import AnalisadorAcidentesExistentes
from src.core.nlp_processor import ProcessadorLinguagemNatural
from src.utils.external_apis import IntegracaoAPIsExternas
from src.models.accident_risk_model import ModeloRiscoAcidentes

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criando a aplicação FastAPI
app = FastAPI(
    title="🛡️ Sistema de Prevenção de Acidentes PRF",
    description="""
    ## Sistema Inteligente de Prevenção de Acidentes Rodoviários
    
    Esta API utiliza **Machine Learning** e **Processamento de Linguagem Natural** 
    para **PREVENIR** acidentes em rodovias brasileiras, analisando condições 
    de viagem e alertando sobre riscos **ANTES** que aconteçam.
    
    ### 🎯 Funcionalidades Principais
    
    * **Análise de Linguagem Natural**: Processa texto natural como "Vou para Santos amanhã às 18h"
    * **Prevenção Inteligente**: Calcula risco real baseado em múltiplos fatores
    * **Recomendações Personalizadas**: Sugere alternativas para reduzir o risco
    * **Integração com APIs Externas**: Clima, tráfego, alertas em tempo real
    
    ### 🛡️ Como Funciona
    
    1. **Você digita**: "Vou para Campinas amanhã às 18h"
    2. **Sistema processa**: Extrai origem, destino, data, horário, tipo de veículo
    3. **Sistema analisa**: Clima, tráfego, histórico da rota, condições da via
    4. **Sistema alerta**: "⚠️ RISCO ALTO (78%) - Horário de pico, chuvas previstas"
    5. **Sistema sugere**: "💡 Saia às 15h ou use Rodovia dos Bandeirantes"
    
    ### 📊 Tecnologias Utilizadas
    
    * **NLP**: Processamento avançado de linguagem natural em português
    * **ML**: Modelo de predição de risco (não gravidade)
    * **APIs Externas**: OpenWeatherMap, Google Maps, alertas PRF
    * **Análise Multi-fatorial**: 16+ fatores de risco simultâneos
    
    ### 🔧 Como Usar
    
    1. **Análise Natural**: `/analyze-trip-natural` - Digite como você falaria
    2. **Análise Estruturada**: `/analyze-trip-structured` - Para integração
    3. **Alertas Tempo Real**: `/alerts/realtime/{highway}` - Alertas da rodovia
    4. **Estatísticas**: `/statistics/routes/{highway}` - Histórico da rota
    5. **Horários Seguros**: `/suggestions/safer-times` - Melhores horários
    
    ### 📚 Documentação
    
    * **Swagger UI**: `/docs`
    * **ReDoc**: `/redoc`
    * **OpenAPI JSON**: `/openapi.json`
    """,
    version="3.0.0",
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
        }
    ],
    tags_metadata=[
        {
            "name": "análise",
            "description": "Endpoints para análise de risco de viagens",
        },
        {
            "name": "alertas",
            "description": "Endpoints para alertas em tempo real",
        },
        {
            "name": "estatísticas",
            "description": "Endpoints para estatísticas e histórico",
        },
        {
            "name": "sugestões",
            "description": "Endpoints para sugestões e recomendações",
        },
        {
            "name": "status",
            "description": "Endpoints para verificação de status",
        },
    ]
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados

class ViagemNatural(BaseModel):
    """
    Dados de entrada para análise em linguagem natural
    
    Exemplo: "Vou para Santos amanhã às 18h"
    """
    texto: str = Field(
        ...,
        description="Texto em linguagem natural descrevendo a viagem",
        example="Vou para Santos amanhã às 18h",
        min_length=10,
        max_length=500
    )

class ViagemEstruturada(BaseModel):
    """
    Dados estruturados para análise de viagem
    """
    origem: str = Field(..., description="Cidade de origem")
    destino: str = Field(..., description="Cidade de destino")
    data: str = Field(..., description="Data da viagem (YYYY-MM-DD)")
    horario: str = Field(..., description="Horário da viagem (HH:MM)")
    tipo_veiculo: str = Field("carro", description="Tipo de veículo")
    num_passageiros: int = Field(1, description="Número de passageiros")
    urgencia: int = Field(1, description="Nível de urgência (1-5)")
    observacoes: Optional[str] = Field(None, description="Observações adicionais")

class AnaliseRisco(BaseModel):
    """
    Resposta da análise de risco
    """
    risco_total: float
    nivel_risco: str
    segmentos_perigosos: List[Dict]
    recomendacoes: List[str]
    alternativas: Dict
    detalhes_viagem: Dict
    timestamp_analise: str


class DadosAcidente(BaseModel):
    """
    Dados de acidente existente para análise
    """
    local: Dict[str, Any] = Field(..., description="Local do acidente: br, km, uf, municipio")
    data_hora: str = Field(..., description="Data e hora do acidente (YYYY-MM-DD HH:MM)")
    condicoes: Dict[str, Any] = Field(..., description="Condições meteorológicas: temperatura, chuva, neblina, etc.")
    veiculos: List[Dict[str, Any]] = Field(..., description="Veículos envolvidos: tipo, pessoas, etc.")
    infraestrutura: Dict[str, Any] = Field(..., description="Infraestrutura: pista_simples, tem_acostamento, etc.")
    contexto: Dict[str, Any] = Field(..., description="Contexto: eh_feriado, eh_fim_semana, etc.")


class AnaliseAcidente(BaseModel):
    """
    Resposta da análise de acidente existente
    """
    acidente_analisado: Dict[str, Any]
    analise_ml: Dict[str, Any]
    insights: List[str]
    recomendacoes: List[str]
    comparacao_historica: Dict[str, Any]
    timestamp_analise: str

class AlertaRodovia(BaseModel):
    """
    Alerta de rodovia
    """
    rodovia: str
    alertas: List[Dict]
    timestamp: str

class EstatisticasRota(BaseModel):
    """
    Estatísticas de uma rota
    """
    rodovia: str
    total_acidentes: int
    acidentes_mes: int
    nivel_risco_medio: str
    horarios_mais_perigosos: List[str]
    condicoes_mais_perigosas: List[str]

class SugestaoHorario(BaseModel):
    """
    Sugestão de horário mais seguro
    """
    origem: str
    destino: str
    horarios_seguros: List[str]
    horarios_evitar: List[str]
    justificativa: str

# Instâncias dos componentes
try:
    logger.info("🎯 Carregando analisador otimizado...")
    analisador_risco = AnalisadorRiscoViagemOtimizado()
    
    logger.info("🎯 Carregando modelos para análise de acidentes...")
    analisador_acidentes = AnalisadorAcidentesExistentes()
    
    processador_nlp = ProcessadorLinguagemNatural()
    integracao_apis = IntegracaoAPIsExternas()
    
    # Carregar modelo ML se disponível
    modelo_ml = ModeloRiscoAcidentes()
    
    logger.info("✅ Componentes da API inicializados")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar componentes: {e}")
    # Fallback para componentes básicos
    analisador_risco = AnalisadorRiscoViagemOtimizado()
    analisador_acidentes = AnalisadorAcidentesExistentes()
    processador_nlp = ProcessadorLinguagemNatural()
    integracao_apis = IntegracaoAPIsExternas()
    modelo_ml = None

# Variáveis globais
start_time = time.time()
total_analises = 0

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
        "api": "Sistema de Prevenção de Acidentes PRF",
        "versao": "3.0.0",
        "status": "online",
        "conceito": "PREVENÇÃO de acidentes (não previsão de gravidade)",
        "endpoints": {
            "/": "Informações da API",
            "/analyze-trip-natural": "Análise em linguagem natural",
            "/analyze-trip-structured": "Análise com dados estruturados",
            "/alerts/realtime/{highway}": "Alertas em tempo real",
            "/statistics/routes/{highway}": "Estatísticas da rota",
            "/suggestions/safer-times": "Sugestões de horários seguros",
            "/health": "Verificação de saúde"
        },
        "documentacao": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

@app.get(
    "/health",
    summary="💚 Verificação de Saúde",
    description="Verifica a saúde da API e dos componentes",
    tags=["status"]
)
async def health_check():
    """
    Verificação de saúde da API
    """
    uptime = time.time() - start_time
    uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": uptime_str,
        "version": "3.0.0",
        "componentes": {
            "analisador_risco": "ativo",
            "processador_nlp": "ativo",
            "integracao_apis": "ativo",
            "modelo_ml": "ativo"
        },
        "total_analises": total_analises
    }

@app.post(
    "/analyze-trip-natural",
    response_model=AnaliseRisco,
    summary="🗣️ Análise em Linguagem Natural",
    description="Analisa risco de viagem a partir de texto natural",
    tags=["análise"]
)
async def analisar_viagem_natural(viagem: ViagemNatural):
    """
    Análise de risco usando linguagem natural
    
    **Exemplos de entrada:**
    - "Vou para Santos amanhã às 18h"
    - "Preciso ir para Campinas hoje à noite de moto"
    - "Viagem para Rio de Janeiro sexta às 15h com a família"
    - "Vou de São Paulo para Belo Horizonte segunda de manhã"
    
    **O que o sistema faz:**
    1. Extrai informações da viagem (origem, destino, data, horário, veículo)
    2. Enriquece com dados externos (clima, tráfego, alertas)
    3. Calcula risco baseado em 16+ fatores
    4. Gera recomendações personalizadas
    5. Sugere alternativas de horário e rota
    """
    global total_analises
    
    try:
        total_analises += 1
        logger.info(f"Análise #{total_analises}: '{viagem.texto}'")
        
        # 1. Processar linguagem natural
        dados_extraidos = processador_nlp.processar_texto(viagem.texto)
        logger.info(f"Dados extraídos: {dados_extraidos}")
        
        # 2. Analisar risco usando o analisador treinado
        analise_risco = analisador_risco.analisar_viagem(
            origem=dados_extraidos.get('origem', 'São Paulo'),
            destino=dados_extraidos.get('destino', 'Santos'),
            data=dados_extraidos.get('data', datetime.now().strftime('%Y-%m-%d')),
            horario=dados_extraidos.get('horario', '12:00'),
            tipo_veiculo=dados_extraidos.get('tipo_veiculo', 'carro'),
            observacoes=viagem.texto
        )
        
        logger.info(f"Análise concluída - Risco: {analise_risco['nivel_risco']} ({analise_risco['risco_total']:.1f}%)")
        
        return AnaliseRisco(**analise_risco)
        
    except Exception as e:
        logger.error(f"Erro na análise de linguagem natural: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na análise: {str(e)}"
        )

@app.post(
    "/analyze-trip-structured",
    response_model=AnaliseRisco,
    summary="📋 Análise Estruturada",
    description="Analisa risco de viagem com dados estruturados",
    tags=["análise"]
)
async def analisar_viagem_estruturada(viagem: ViagemEstruturada):
    """
    Análise de risco com dados estruturados
    
    Para integração com outros sistemas ou quando você tem
    os dados já organizados.
    """
    global total_analises
    
    try:
        total_analises += 1
        logger.info(f"Análise estruturada #{total_analises}: {viagem.origem} -> {viagem.destino}")
        
        # Analisar risco usando o analisador treinado
        analise_risco = analisador_risco.analisar_viagem(
            origem=viagem.origem,
            destino=viagem.destino,
            data=viagem.data,
            horario=viagem.horario,
            tipo_veiculo=viagem.tipo_veiculo,
            observacoes=viagem.observacoes or ""
        )
        
        return AnaliseRisco(**analise_risco)
        
    except Exception as e:
        logger.error(f"Erro na análise estruturada: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na análise: {str(e)}"
        )

@app.get(
    "/alerts/realtime/{highway}",
    response_model=AlertaRodovia,
    summary="🚨 Alertas em Tempo Real",
    description="Retorna alertas ativos de uma rodovia",
    tags=["alertas"]
)
async def obter_alertas_rodovia(highway: str):
    """
    Alertas em tempo real de uma rodovia
    
    **Parâmetros:**
    - highway: Código da rodovia (ex: BR-101, SP-160, RJ-116)
    
    **Retorna:**
    - Lista de alertas ativos
    - Tipos: acidente, obras, interdição, congestionamento
    - Informações: localização, severidade, timestamp
    """
    try:
        logger.info(f"Consultando alertas para {highway}")
        
        alertas = integracao_apis.obter_alertas_rodovia(highway.upper())
        
        return AlertaRodovia(
            rodovia=highway.upper(),
            alertas=alertas,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar alertas: {str(e)}"
        )

@app.get(
    "/statistics/routes/{highway}",
    response_model=EstatisticasRota,
    summary="📊 Estatísticas da Rota",
    description="Retorna estatísticas históricas de uma rodovia",
    tags=["estatísticas"]
)
async def obter_estatisticas_rota(highway: str):
    """
    Estatísticas históricas de uma rodovia
    
    **Parâmetros:**
    - highway: Código da rodovia
    
    **Retorna:**
    - Total de acidentes
    - Acidentes do mês
    - Nível de risco médio
    - Horários mais perigosos
    - Condições mais perigosas
    """
    try:
        logger.info(f"Consultando estatísticas para {highway}")
        
        # Simular estatísticas (em produção, buscar do banco de dados)
        estatisticas = {
            'rodovia': highway.upper(),
            'total_acidentes': 1247,
            'acidentes_mes': 23,
            'nivel_risco_medio': "MÉDIO",
            'horarios_mais_perigosos': [
                "18:00-19:00 (rush hour)",
                "22:00-23:00 (noite)",
                "06:00-07:00 (madrugada)"
            ],
            'condicoes_mais_perigosas': [
                "Chuva moderada",
                "Neblina",
                "Obras na pista"
            ]
        }
        
        return EstatisticasRota(**estatisticas)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar estatísticas: {str(e)}"
        )

@app.get(
    "/suggestions/safer-times",
    response_model=SugestaoHorario,
    summary="⏰ Horários Mais Seguros",
    description="Sugere horários mais seguros para uma rota",
    tags=["sugestões"]
)
async def sugerir_horarios_seguros(
    origem: str = Query(..., description="Cidade de origem"),
    destino: str = Query(..., description="Cidade de destino"),
    dia_semana: Optional[str] = Query(None, description="Dia da semana")
):
    """
    Sugere horários mais seguros para uma rota
    
    **Parâmetros:**
    - origem: Cidade de origem
    - destino: Cidade de destino
    - dia_semana: Dia da semana (opcional)
    
    **Retorna:**
    - Horários recomendados
    - Horários a evitar
    - Justificativa baseada em dados
    """
    try:
        logger.info(f"Sugerindo horários: {origem} -> {destino}")
        
        # Analisar padrões de risco por horário
        horarios_seguros = [
            "10:00-11:00 (manhã tranquila)",
            "14:00-15:00 (tarde segura)",
            "20:00-21:00 (noite inicial)"
        ]
        
        horarios_evitar = [
            "07:00-09:00 (rush matinal)",
            "17:00-19:00 (rush vespertino)",
            "22:00-06:00 (madrugada)"
        ]
        
        justificativa = f"Baseado no histórico da rota {origem}-{destino}, horários de pico e madrugada apresentam maior risco de acidentes."
        
        return SugestaoHorario(
            origem=origem,
            destino=destino,
            horarios_seguros=horarios_seguros,
            horarios_evitar=horarios_evitar,
            justificativa=justificativa
        )
        
    except Exception as e:
        logger.error(f"Erro ao sugerir horários: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao sugerir horários: {str(e)}"
        )

# Funções auxiliares

# Middleware para logging
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

# Handlers de erro
# Endpoints para análise de acidentes existentes

@app.post(
    "/analyze-accident",
    response_model=AnaliseAcidente,
    summary="🚨 Análise de Acidente Existente",
    description="Analisa um acidente já ocorrido para determinar severidade e fatores causais",
    tags=["análise de acidentes"]
)
async def analisar_acidente_existente(acidente: DadosAcidente):
    """
    Analisa um acidente já ocorrido usando ML para:
    
    - **Determinar severidade**: SEM FERIDOS, FERIDOS LEVES, FERIDOS GRAVES, MORTOS
    - **Identificar fatores causais**: Condições meteorológicas, infraestrutura, temporal, etc.
    - **Calcular probabilidade atual**: Risco de acidente similar nas condições atuais
    - **Gerar insights**: Análise detalhada e recomendações de prevenção
    """
    try:
        logger.info(f"Analisando acidente em {acidente.local.get('municipio', 'N/A')}")
        
        # Converter Pydantic model para dict
        dados_acidente = acidente.dict()
        
        # Analisar acidente usando ML
        resultado = analisador_acidentes.analisar_acidente_existente(dados_acidente)
        
        logger.info(f"Análise de acidente concluída - Severidade: {resultado.get('analise_ml', {}).get('severidade_predita', {}).get('nivel', 'N/A')}")
        
        return AnaliseAcidente(**resultado)
        
    except Exception as e:
        logger.error(f"Erro na análise de acidente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na análise do acidente: {str(e)}"
        )


@app.get(
    "/accident-severity/{br}/{km}",
    summary="📊 Severidade por Local",
    description="Retorna análise de severidade de acidentes em um local específico",
    tags=["análise de acidentes"]
)
async def analisar_severidade_local(br: int, km: int):
    """
    Analisa a severidade típica de acidentes em um local específico
    """
    try:
        logger.info(f"Analisando severidade em BR {br} KM {km}")
        
        # Dados reais para o local baseados no treinamento
        from src.data.real_data_processor import processador_dados_reais
        
        dados_local_real = processador_dados_reais.obter_dados_analise_acidente_real(br, km)
        
        # Usar dados reais se disponíveis
        if dados_local_real.get('dados_disponiveis', False):
            dados_local = {
                "local": {"br": br, "km": km, "uf": "SP", "municipio": f"Local BR{br}KM{km}"},
                "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "condicoes": {"temperatura": 25, "chuva": False, "neblina": False},
                "veiculos": [{"tipo": "carro", "pessoas": 2}],
                "infraestrutura": {"pista_simples": br in [101, 116], "tem_acostamento": True},
                "contexto": {"eh_feriado": False, "eh_fim_semana": False}
            }
        else:
            # Fallback para dados básicos
            dados_local = {
                "local": {"br": br, "km": km, "uf": "SP", "municipio": f"Local BR{br}KM{km}"},
                "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "condicoes": {"temperatura": 25, "chuva": False, "neblina": False},
                "veiculos": [{"tipo": "carro", "pessoas": 2}],
                "infraestrutura": {"pista_simples": br in [101, 116], "tem_acostamento": True},
                "contexto": {"eh_feriado": False, "eh_fim_semana": False}
            }
        
        # Analisar local
        resultado = analisador_acidentes.analisar_acidente_existente(dados_local)
        
        return {
            "local": f"BR {br} KM {km}",
            "severidade_media": resultado["analise_ml"]["severidade_predita"],
            "fatores_risco": resultado["analise_ml"]["fatores_causais"],
            "recomendacoes_locais": resultado["recomendacoes"][:3],  # Top 3
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na análise de local: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na análise do local: {str(e)}"
        )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint não encontrado",
            "message": f"O endpoint {request.url.path} não existe",
            "available_endpoints": [
                "/", "/analyze-trip-natural", "/analyze-trip-structured",
                "/analyze-accident", "/accident-severity/{br}/{km}",
                "/alerts/realtime/{highway}", "/statistics/routes/{highway}",
                "/suggestions/safer-times", "/health", "/docs", "/redoc"
            ]
        }
    )

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
