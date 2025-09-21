#!/usr/bin/env python3
"""
DASHBOARD STANDALONE - Sistema PRF
==================================

Dashboard completamente independente que roda sozinho.
Não depende do main.py nem de outros arquivos.

Uso: streamlit run dashboard_standalone.py
URL: http://localhost:8501
"""

import streamlit as st
import requests
import json
from datetime import datetime, date
from typing import Dict, Optional
import time
import holidays

def buscar_localizacao_api_publica(br: int, km: int):
    """Busca localização usando API pública Nominatim (OpenStreetMap)"""
    try:
        query = f"BR-{br:03d} km {km} Brazil"
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": 1,
            "countrycodes": "br"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                address = result.get("address", {})
                
                municipio = address.get("city") or address.get("town") or address.get("village") or "Não identificado"
                uf = address.get("state", "Não identificado")
                
                # Mapear região
                regiao_map = {
                    "Acre": "Norte", "Alagoas": "Nordeste", "Amapá": "Norte", "Amazonas": "Norte",
                    "Bahia": "Nordeste", "Ceará": "Nordeste", "Distrito Federal": "Centro-Oeste",
                    "Espírito Santo": "Sudeste", "Goiás": "Centro-Oeste", "Maranhão": "Nordeste",
                    "Mato Grosso": "Centro-Oeste", "Mato Grosso do Sul": "Centro-Oeste",
                    "Minas Gerais": "Sudeste", "Pará": "Norte", "Paraíba": "Nordeste",
                    "Paraná": "Sul", "Pernambuco": "Nordeste", "Piauí": "Nordeste",
                    "Rio de Janeiro": "Sudeste", "Rio Grande do Norte": "Nordeste",
                    "Rio Grande do Sul": "Sul", "Rondônia": "Norte", "Roraima": "Norte",
                    "Santa Catarina": "Sul", "São Paulo": "Sudeste", "Sergipe": "Nordeste",
                    "Tocantins": "Norte"
                }
                
                regiao = regiao_map.get(uf, "Não identificado")
                
                return {
                    "municipio": municipio,
                    "uf": uf,
                    "regiao": regiao,
                    "bairro": address.get("suburb", "Não identificado"),
                    "fonte": "Nominatim API"
                }
        
        return None
        
    except Exception as e:
        st.error(f"Erro ao buscar localização: {e}")
        return None

# Configuração da página
st.set_page_config(
    page_title="🔮 Dashboard PRF Standalone",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS moderno e limpo
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .prediction-card {
        background: white;
        border: 2px solid #e1e8ed;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .prediction-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .severity-verde { 
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 5px solid #28a745;
        color: #155724;
    }
    
    .severity-amarelo { 
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 5px solid #ffc107;
        color: #856404;
    }
    
    .severity-laranja { 
        background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
        border-left: 5px solid #fd7e14;
        color: #8b4513;
    }
    
    .severity-vermelho { 
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 5px solid #dc3545;
        color: #721c24;
    }
    
    .metric-large {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .api-status-online {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    
    .api-status-offline {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }
    
    .protocol-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .protocol-verde { background-color: #28a745; color: white; }
    .protocol-amarelo { background-color: #ffc107; color: black; }
    .protocol-laranja { background-color: #fd7e14; color: white; }
    .protocol-vermelho { background-color: #dc3545; color: white; }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Configuração da API
API_BASE_URL = "http://localhost:8000"

# BRs Reais do Sistema PRF
BRS_REAIS = {
    "BR-101": "BR-101 (Rio Grande do Norte até Rio Grande do Sul)",
    "BR-104": "BR-104 (Alagoas até Pernambuco)",
    "BR-110": "BR-110 (Rondônia até Acre)",
    "BR-116": "BR-116 (Ceará até Rio Grande do Sul)",
    "BR-153": "BR-153 (São Paulo até Rio Grande do Sul)",
    "BR-163": "BR-163 (Mato Grosso até Pará)",
    "BR-174": "BR-174 (Roraima até Amazonas)",
    "BR-230": "BR-230 (Transamazônica - Pará)",
    "BR-262": "BR-262 (Minas Gerais até Mato Grosso do Sul)",
    "BR-316": "BR-316 (Pará até Maranhão)",
    "BR-319": "BR-319 (Amazonas até Rondônia)",
    "BR-364": "BR-364 (São Paulo até Rondônia)",
    "BR-381": "BR-381 (Minas Gerais)",
    "BR-386": "BR-386 (Rio Grande do Sul)",
    "BR-392": "BR-392 (Rio Grande do Sul)",
    "BR-393": "BR-393 (Rio de Janeiro)",
    "BR-101": "BR-101 (Rio Grande do Norte até Rio Grande do Sul)",
    "BR-104": "BR-104 (Alagoas até Pernambuco)",
    "BR-110": "BR-110 (Rondônia até Acre)",
    "BR-116": "BR-116 (Ceará até Rio Grande do Sul)",
    "BR-153": "BR-153 (São Paulo até Rio Grande do Sul)",
    "BR-163": "BR-163 (Mato Grosso até Pará)",
    "BR-174": "BR-174 (Roraima até Amazonas)",
    "BR-230": "BR-230 (Transamazônica - Pará)",
    "BR-262": "BR-262 (Minas Gerais até Mato Grosso do Sul)",
    "BR-316": "BR-316 (Pará até Maranhão)",
    "BR-319": "BR-319 (Amazonas até Rondônia)",
    "BR-364": "BR-364 (São Paulo até Rondônia)",
    "BR-381": "BR-381 (Minas Gerais)",
    "BR-386": "BR-386 (Rio Grande do Sul)",
    "BR-392": "BR-392 (Rio Grande do Sul)",
    "BR-393": "BR-393 (Rio de Janeiro)",
    "BR-040": "BR-040 (Rio de Janeiro até Bahia)",
    "BR-050": "BR-050 (São Paulo até Minas Gerais)",
    "BR-060": "BR-060 (Distrito Federal até Goiás)",
    "BR-070": "BR-070 (São Paulo até Mato Grosso do Sul)",
    "BR-080": "BR-080 (Pará até Maranhão)",
    "BR-090": "BR-090 (Goiás até Tocantins)"
}

def is_feriado(data: date) -> bool:
    """Verifica se a data é feriado nacional"""
    try:
        # Feriados nacionais do Brasil
        br_holidays = holidays.Brazil()
        return data in br_holidays
    except:
        # Lista básica de feriados nacionais se holidays não funcionar
        feriados = [
            (1, 1),   # Ano Novo
            (4, 21),  # Tiradentes
            (5, 1),   # Dia do Trabalhador
            (9, 7),   # Independência
            (10, 12), # Nossa Senhora Aparecida
            (11, 2),  # Finados
            (11, 15), # Proclamação da República
            (12, 25)  # Natal
        ]
        return (data.month, data.day) in feriados

def is_fim_semana(data: date) -> bool:
    """Verifica se a data é fim de semana"""
    return data.weekday() >= 5  # 5 = sábado, 6 = domingo

def get_contexto_automatico() -> Dict:
    """Obtém contexto automático baseado na data atual"""
    agora = datetime.now()
    data_atual = agora.date()
    
    return {
        "data_hora": agora.strftime("%Y-%m-%d %H:%M:%S"),
        "eh_feriado": is_feriado(data_atual),
        "eh_fim_semana": is_fim_semana(data_atual),
        "dia_semana": agora.strftime("%A"),
        "mes": agora.month,
        "ano": agora.year,
        "hora": agora.hour,
        "minuto": agora.minute
    }

# Inicializar session state
if 'analises_realizadas' not in st.session_state:
    st.session_state.analises_realizadas = []
if 'dados_automaticos' not in st.session_state:
    st.session_state.dados_automaticos = {}

def verificar_api():
    """Verifica se a API está rodando"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, {}
    except:
        return False, {}

def obter_dados_api(endpoint: str) -> Optional[Dict]:
    """Obtém dados da API"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com API: {e}")
        return None

def post_dados_api(endpoint: str, payload: Dict) -> Optional[Dict]:
    """Envia dados para a API"""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com API: {e}")
        return None

def buscar_dados_automaticos(br_numero: str, km: int):
    """Busca dados automáticos usando API pública Nominatim"""
    # Extrair número da BR (ex: "BR-116" -> "116")
    br_clean = br_numero.replace("BR-", "").replace("BR", "")
    
    # Primeiro tentar API pública
    dados_publica = buscar_localizacao_api_publica(int(br_clean), km)
    
    if dados_publica:
        # Usar dados da API pública
        dados = {
            "localizacao": {
                "br": int(br_clean),
                "km": km,
                "municipio": dados_publica["municipio"],
                "uf": dados_publica["uf"],
                "regiao": dados_publica["regiao"]
            },
            "clima": {
                "temperatura_atual": 25,  # Padrão
                "condicao_chuva": False,
                "condicao_neblina": False,
                "umidade": 60,
                "visibilidade": 10000
            },
            "rodovia": {
                "tipo_pista": "dupla",
                "tem_acostamento": True,
                "limite_velocidade": 80,
                "condicoes_via": "boa"
            },
            "trafego": {
                "fluxo_atual": "NORMAL",
                "tempo_viagem": "30 min",
                "incidentes_ativos": 1
            },
            "historico": {
                "acidentes_30_dias": 2,
                "severidade_media": 2.1,
                "horarios_criticos": [18, 19, 20]
            },
            "fonte": "API Pública Nominatim"
        }
        st.session_state.dados_automaticos = dados
        return dados
    else:
        # Fallback: tentar nossa API
        dados = obter_dados_api(f"/dados/auto-location/{br_clean}/{km}")
        if dados:
            st.session_state.dados_automaticos = dados
            return dados
        else:
            # Último fallback: dados não encontrados
            dados = {
                "localizacao": {
                    "br": int(br_clean),
                    "km": km,
                    "municipio": "Não identificado",
                    "uf": "Não identificado",
                    "regiao": "Não identificado"
                },
                "clima": {
                    "temperatura_atual": 25,
                    "condicao_chuva": False,
                    "condicao_neblina": False,
                    "umidade": 60,
                    "visibilidade": 10000
                },
                "rodovia": {
                    "tipo_pista": "dupla",
                    "tem_acostamento": True,
                    "limite_velocidade": 80,
                    "condicoes_via": "boa"
                },
                "trafego": {
                    "fluxo_atual": "NORMAL",
                    "tempo_viagem": "30 min",
                    "incidentes_ativos": 1
                },
                "historico": {
                    "acidentes_30_dias": 2,
                    "severidade_media": 2.1,
                    "horarios_criticos": [18, 19, 20]
                },
                "fonte": "Dados não encontrados"
            }
            st.session_state.dados_automaticos = dados
            return dados

def main():
    """Função principal do dashboard standalone"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🔮 Dashboard PRF Standalone</h1>
        <h3>Sistema de Previsão de Severidade - Independente</h3>
        <p>Roda sozinho • Conecta na API • Interface moderna</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar status da API
    api_ok, api_info = verificar_api()
    if api_ok:
        st.markdown(f"""
        <div class="api-status-online">
            <strong>✅ API Online</strong><br>
            Uptime: {api_info.get('uptime', 'N/A')} | 
            Análises: {api_info.get('total_analises', 0)} | 
            Status: {api_info.get('status', 'healthy')}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="api-status-offline">
            <strong>❌ API Offline</strong><br>
            Para usar o dashboard, inicie a API: <code>python api.py</code>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Layout principal
    col1, col2 = st.columns([1, 1])
    
    # ============================================================================
    # COLUNA 1: ENTRADA DE DADOS
    # ============================================================================
    with col1:
        st.markdown("### 📋 Dados da Ocorrência")
        
        with st.form("severity_prediction_form"):
            # Localização (campos principais)
            st.markdown("#### 🌍 Localização")
            col_br, col_km = st.columns(2)
            with col_br:
                br_selecionada = st.selectbox(
                    "BR:", 
                    options=list(BRS_REAIS.keys()),
                    index=list(BRS_REAIS.keys()).index("BR-116"),  # Default BR-116
                    help="Selecione a rodovia federal",
                    format_func=lambda x: BRS_REAIS[x]
                )
            with col_km:
                km = st.number_input("KM:", min_value=1, max_value=999, value=50, help="Quilômetro da ocorrência")
            
            # Botão para buscar dados automáticos
            if st.form_submit_button("🔍 Buscar Dados Automáticos", type="secondary"):
                with st.spinner("Buscando dados automáticos..."):
                    dados_auto = buscar_dados_automaticos(br_selecionada, km)
                    if dados_auto:
                        st.success("✅ Dados automáticos carregados!")
                    else:
                        st.warning("⚠️ Erro ao buscar dados automáticos")
            
            # Mostrar dados automáticos se disponíveis
            if st.session_state.dados_automaticos:
                dados_auto = st.session_state.dados_automaticos
                
                st.markdown("#### 🤖 Dados Automáticos")
                
                # Informações de localização
                with st.expander("📍 Localização Automática", expanded=True):
                    st.write(f"**Município:** {dados_auto['localizacao']['municipio']} - {dados_auto['localizacao']['uf']}")
                    st.write(f"**Região:** {dados_auto['localizacao']['regiao']}")
                
                # Condições meteorológicas
                with st.expander("🌤️ Clima Atual", expanded=True):
                    clima = dados_auto['clima']
                    st.write(f"**Temperatura:** {clima['temperatura_atual']}°C")
                    st.write(f"**Chuva:** {'Sim' if clima['condicao_chuva'] else 'Não'}")
                    st.write(f"**Neblina:** {'Sim' if clima['condicao_neblina'] else 'Não'}")
                    st.write(f"**Umidade:** {clima['umidade']}%")
                    st.write(f"**Visibilidade:** {clima['visibilidade']}m")
                
                # Informações da rodovia
                with st.expander("🛣️ Rodovia", expanded=True):
                    rodovia = dados_auto['rodovia']
                    st.write(f"**Tipo de Pista:** {rodovia['tipo_pista']}")
                    st.write(f"**Acostamento:** {'Sim' if rodovia['tem_acostamento'] else 'Não'}")
                    st.write(f"**Limite de Velocidade:** {rodovia['limite_velocidade']} km/h")
                    st.write(f"**Condições da Via:** {rodovia['condicoes_via']}")
                
                # Dados de tráfego
                with st.expander("🚗 Tráfego", expanded=True):
                    trafego = dados_auto['trafego']
                    st.write(f"**Fluxo:** {trafego['fluxo_atual']}")
                    st.write(f"**Tempo de Viagem:** {trafego['tempo_viagem']} min")
                    st.write(f"**Incidentes Ativos:** {trafego['incidentes_ativos']}")
                
                # Histórico
                with st.expander("📊 Histórico", expanded=True):
                    historico = dados_auto['historico']
                    st.write(f"**Acidentes (30 dias):** {historico['acidentes_30_dias']}")
                    st.write(f"**Severidade Média:** {historico['severidade_media']}")
                    st.write(f"**Horários Críticos:** {historico['horarios_criticos']}")
            
            # Campos manuais (mínimos)
            st.markdown("#### ✍️ Informações Adicionais")
            
            # Data e hora automáticas
            contexto_auto = get_contexto_automatico()
            st.info(f"📅 **Data/Hora Automática:** {contexto_auto['data_hora']}")
            st.info(f"📊 **Contexto:** {contexto_auto['dia_semana']} - {'Feriado' if contexto_auto['eh_feriado'] else 'Dia útil'} - {'Fim de semana' if contexto_auto['eh_fim_semana'] else 'Dia útil'}")
            
            # Primeiro relato (campo essencial)
            primeiro_relato = st.text_area(
                "Primeiro Relato:",
                placeholder="Ex: Acidente com múltiplos veículos, possível vítima presa...",
                height=100,
                help="Descrição inicial da ocorrência"
            )
            
            # Veículos envolvidos
            st.markdown("#### 🚗 Veículos Envolvidos")
            col_tipo, col_pessoas = st.columns(2)
            with col_tipo:
                tipo_veiculo = st.selectbox("Tipo:", ["carro", "moto", "caminhão", "ônibus"], help="Tipo do veículo principal")
            with col_pessoas:
                pessoas = st.number_input("Pessoas:", min_value=1, max_value=10, value=2, help="Número de pessoas envolvidas")
            
            # Contexto automático (não editável)
            st.markdown("#### 📅 Contexto Automático")
            st.success(f"✅ **Feriado:** {'Sim' if contexto_auto['eh_feriado'] else 'Não'}")
            st.success(f"✅ **Fim de Semana:** {'Sim' if contexto_auto['eh_fim_semana'] else 'Não'}")
            st.success(f"✅ **Dia da Semana:** {contexto_auto['dia_semana']}")
            
            # Botão de previsão
            if st.form_submit_button("🔮 PREVER SEVERIDADE", type="primary"):
                if primeiro_relato:
                    with st.spinner("Analisando severidade com ML..."):
                        # Preparar payload com dados automáticos e contexto real
                        br_numero = br_selecionada.replace("BR-", "").replace("BR", "")
                        
                        # Buscar dados automáticos se não existirem
                        if not st.session_state.dados_automaticos:
                            dados_auto = buscar_dados_automaticos(br_selecionada, km)
                        else:
                            dados_auto = st.session_state.dados_automaticos
                        
                        payload = {
                            "local": {
                                "br": int(br_numero), 
                                "km": km, 
                                "uf": dados_auto['localizacao']['uf'],
                                "municipio": dados_auto['localizacao']['municipio']
                            },
                            "data_hora": contexto_auto['data_hora'],
                            "primeiro_relato": primeiro_relato,
                            "condicoes": {
                                "temperatura": dados_auto['clima']['temperatura_atual'],
                                "chuva": dados_auto['clima']['condicao_chuva'],
                                "neblina": dados_auto['clima']['condicao_neblina']
                            },
                            "veiculos": [{"tipo": tipo_veiculo, "pessoas": pessoas}],
                            "infraestrutura": {
                                "pista_simples": dados_auto['rodovia']['tipo_pista'] == "simples",
                                "tem_acostamento": dados_auto['rodovia']['tem_acostamento']
                            },
                            "contexto": {
                                "eh_feriado": contexto_auto['eh_feriado'],
                                "eh_fim_semana": contexto_auto['eh_fim_semana']
                            }
                        }
                        
                        resultado = post_dados_api("/predict-severity", payload)
                        
                        if resultado:
                            st.session_state.analises_realizadas.append(resultado)
                            st.success("✅ Previsão de severidade concluída!")
                            st.rerun()
                else:
                    st.warning("⚠️ Preencha o primeiro relato")
    
    # ============================================================================
    # COLUNA 2: RESULTADOS
    # ============================================================================
    with col2:
        st.markdown("### 🔮 Resultados da Previsão")
        
        if st.session_state.analises_realizadas:
            ultima_previsao = st.session_state.analises_realizadas[-1]
            
            # Severidade
            severidade = ultima_previsao["severidade_predita"]
            confianca = ultima_previsao["confianca"]
            
            # Card de severidade com cores
            if severidade["nivel"] == "MORTOS":
                st.markdown('<div class="prediction-card severity-vermelho">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-large">🔴 {severidade["nivel"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem;">Confiança: {confianca:.1f}%</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            elif severidade["nivel"] == "FERIDOS GRAVES":
                st.markdown('<div class="prediction-card severity-laranja">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-large">🟠 {severidade["nivel"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem;">Confiança: {confianca:.1f}%</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            elif severidade["nivel"] == "FERIDOS LEVES":
                st.markdown('<div class="prediction-card severity-amarelo">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-large">🟡 {severidade["nivel"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem;">Confiança: {confianca:.1f}%</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="prediction-card severity-verde">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-large">🟢 {severidade["nivel"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem;">Confiança: {confianca:.1f}%</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Protocolo
            protocolo = ultima_previsao["protocolo_emergencia"]
            protocolo_class = f"protocol-{protocolo['codigo'].lower()}"
            st.markdown(f'<div class="protocol-badge {protocolo_class}">Protocolo {protocolo["codigo"]} - {protocolo["coordenacao"]}</div>', unsafe_allow_html=True)
            
            # Recursos sugeridos
            st.markdown("#### 📋 Recursos Sugeridos")
            recursos = ultima_previsao["recursos_sugeridos"]
            
            col1_res, col2_res = st.columns(2)
            with col1_res:
                st.metric("🚔 Viaturas PRF", recursos['viaturas_prf'])
                st.metric("🚑 Ambulâncias", recursos['ambulancia'])
            with col2_res:
                st.metric("🚁 Helicóptero", "Sim" if recursos['helicoptero'] else "Não")
                st.metric("👮 Perito", "Sim" if recursos['perito'] else "Não")
            
            # Tempo de resposta
            st.markdown("#### ⏱️ Tempo de Resposta")
            tempo = ultima_previsao["tempo_resposta"]
            
            col1_time, col2_time = st.columns(2)
            with col1_time:
                st.metric("Tempo Estimado", f"{tempo['tempo_estimado_minutos']} min")
            with col2_time:
                st.metric("Golden Hour", tempo["golden_hour_status"])
            
            # Fatores críticos
            if ultima_previsao["fatores_criticos"]:
                st.markdown("#### ⚠️ Fatores Críticos")
                for fator in ultima_previsao["fatores_criticos"]:
                    st.write(f"• {fator}")
            
            # Botão para ver relatório completo
            if st.button("📄 Ver Relatório Completo PRF", type="secondary"):
                st.session_state.mostrar_relatorio = True
            
            # Modal/Expander para relatório completo
            if st.session_state.get('mostrar_relatorio', False):
                relatorio = ultima_previsao["relatorio_prf"]
                
                with st.expander("📄 Relatório Completo PRF", expanded=True):
                    st.markdown("### 🚨 RELATÓRIO DE PREVISÃO DE SEVERIDADE - PRF")
                    
                    # Cabeçalho
                    st.markdown(f"**Protocolo:** {relatorio['cabecalho']['protocolo']}")
                    st.markdown(f"**Data/Hora:** {relatorio['cabecalho']['data_hora']}")
                    st.markdown(f"**Sistema:** {relatorio['cabecalho']['sistema']}")
                    
                    # Ocorrência
                    st.markdown("### 📍 Ocorrência")
                    st.write(f"**Local:** {relatorio['ocorrencia']['local']}")
                    st.write(f"**Município:** {relatorio['ocorrencia']['municipio']} - {relatorio['ocorrencia']['uf']}")
                    st.write(f"**Data/Hora:** {relatorio['ocorrencia']['data_hora']}")
                    st.write(f"**Relato:** {relatorio['ocorrencia']['primeiro_relato']}")
                    
                    # Previsão ML
                    st.markdown("### 🔮 Previsão ML")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Severidade", relatorio['previsao_ml']['severidade_predita'])
                    with col2:
                        st.metric("Confiança", relatorio['previsao_ml']['confianca'])
                    with col3:
                        st.metric("Acurácia Modelo", relatorio['previsao_ml']['acuracia_modelo'])
                    
                    # Recursos necessários
                    st.markdown("### 📋 Recursos Necessários")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"🚔 **Viaturas PRF:** {relatorio['recursos_necessarios']['viaturas_prf']}")
                        st.write(f"🚑 **Ambulâncias:** {relatorio['recursos_necessarios']['ambulancias']}")
                        st.write(f"🚁 **Helicóptero:** {relatorio['recursos_necessarios']['helicoptero']}")
                    with col2:
                        st.write(f"👮 **Perito:** {relatorio['recursos_necessarios']['perito']}")
                        st.write(f"🏥 **SAMU:** {relatorio['recursos_necessarios']['samu']}")
                        st.write(f"⚡ **Prioridade:** {relatorio['recursos_necessarios']['prioridade']}")
                    
                    # Protocolo de emergência
                    st.markdown("### 🚨 Protocolo de Emergência")
                    st.write(f"**Código:** {relatorio['protocolo_emergencia']['codigo']}")
                    st.write(f"**Coordenação:** {relatorio['protocolo_emergencia']['coordenacao']}")
                    st.write("**Ações Imediatas:**")
                    for acao in relatorio['protocolo_emergencia']['acoes_imediata']:
                        st.write(f"• {acao}")
                    
                    # Recomendações operacionais
                    st.markdown("### 💡 Recomendações Operacionais")
                    for rec in relatorio['recomendacoes_operacionais']:
                        st.write(f"• {rec}")
                    
                    # Contatos de emergência
                    st.markdown("### 📞 Contatos de Emergência")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"🚨 **SAMU:** {relatorio['contatos_emergencia']['samu']}")
                        st.write(f"🚒 **Bombeiros:** {relatorio['contatos_emergencia']['bombeiros']}")
                    with col2:
                        st.write(f"🚔 **PRF Emergência:** {relatorio['contatos_emergencia']['prf_emergencia']}")
                        st.write(f"🏥 **Coordenação:** {relatorio['contatos_emergencia']['coordenacao_regional']}")
                    
                    # Observações
                    st.markdown("### 📝 Observações")
                    for obs in relatorio['observacoes']:
                        st.write(f"• {obs}")
                    
                    # Botão para fechar
                    if st.button("❌ Fechar Relatório"):
                        st.session_state.mostrar_relatorio = False
                        st.rerun()
        
        else:
            st.info("ℹ️ Nenhuma análise realizada ainda")
    
    # ============================================================================
    # FOOTER
    # ============================================================================
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
        🔮 Dashboard PRF Standalone v2.0<br>
        Roda sozinho • Conecta na API • Interface moderna<br>
        📚 API Docs: <a href="http://localhost:8000/docs" target="_blank">localhost:8000/docs</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
