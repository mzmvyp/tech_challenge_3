"""
Dashboard Moderno - Sistema de Prevenção de Acidentes PRF

Interface web moderna e intuitiva para análise de risco de viagens
usando Streamlit com visualizações interativas.

IMPORTANTE: Este arquivo foi substituído por app_expandido.py
Execute: streamlit run src/dashboard/app_expandido.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import time

# Configuração da página
st.set_page_config(
    page_title="🛡️ Protetor de Viagens PRF",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .risk-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .risk-baixo {
        border-left: 5px solid #28a745;
    }
    
    .risk-medio {
        border-left: 5px solid #ffc107;
    }
    
    .risk-alto {
        border-left: 5px solid #fd7e14;
    }
    
    .risk-critico {
        border-left: 5px solid #dc3545;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .recommendation {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    
    .warning {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #ffc107;
    }
    
    .danger {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
    }
    
    .example-button {
        background: #6c757d;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.25rem;
        cursor: pointer;
    }
    
    .example-button:hover {
        background: #5a6268;
    }
    
    .resultado-persistente {
        background: #f8f9fa;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .status-saved {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Configurações da API
API_BASE_URL = "http://localhost:8000"

def obter_cor_risco(nivel_risco: str) -> str:
    """Retorna cor baseada no nível de risco"""
    cores = {
        "BAIXO": "#28a745",
        "MÉDIO": "#ffc107", 
        "ALTO": "#fd7e14",
        "CRÍTICO": "#dc3545"
    }
    return cores.get(nivel_risco, "#6c757d")

def obter_icone_risco(nivel_risco: str) -> str:
    """Retorna ícone baseado no nível de risco"""
    icones = {
        "BAIXO": "✅",
        "MÉDIO": "⚠️",
        "ALTO": "🚨",
        "CRÍTICO": "🔴"
    }
    return icones.get(nivel_risco, "❓")

def criar_gauge_risco(probabilidade: float, nivel_risco: str):
    """Cria gauge circular para visualizar risco"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = probabilidade,
        title = {'text': f"{obter_icone_risco(nivel_risco)} Risco de Acidente"},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': obter_cor_risco(nivel_risco)},
            'steps': [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 60], 'color': "yellow"},
                {'range': [60, 80], 'color': "orange"},
                {'range': [80, 100], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        font=dict(size=16),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def criar_mapa_rota(origem: str, destino: str):
    """Cria mapa interativo da rota"""
    # Coordenadas aproximadas (em produção, usar API do Google Maps)
    coordenadas = {
        'São Paulo': (-23.5505, -46.6333),
        'Santos': (-23.9608, -46.3331),
        'Campinas': (-22.9056, -47.0608),
        'Rio de Janeiro': (-22.9068, -43.1729),
        'Belo Horizonte': (-19.9167, -43.9345)
    }
    
    lat_origem, lon_origem = coordenadas.get(origem, (-23.5505, -46.6333))
    lat_destino, lon_destino = coordenadas.get(destino, (-23.9608, -46.3331))
    
    # Criar mapa
    mapa = folium.Map(
        location=[(lat_origem + lat_destino) / 2, (lon_origem + lon_destino) / 2],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Adicionar marcadores
    folium.Marker(
        [lat_origem, lon_origem],
        popup=f"Origem: {origem}",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(mapa)
    
    folium.Marker(
        [lat_destino, lon_destino],
        popup=f"Destino: {destino}",
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(mapa)
    
    # Adicionar linha da rota
    folium.PolyLine(
        [[lat_origem, lon_origem], [lat_destino, lon_destino]],
        color="blue",
        weight=3,
        opacity=0.7
    ).add_to(mapa)
    
    return mapa

def analisar_viagem_api(texto: str) -> Optional[Dict]:
    """Chama API para análise de viagem"""
    try:
        url = f"{API_BASE_URL}/analyze-trip-natural"
        payload = {"texto": texto}
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Erro ao analisar viagem: {e}")
        return None

def obter_alertas_api(rodovia: str) -> List[Dict]:
    """Obtém alertas de uma rodovia"""
    try:
        url = f"{API_BASE_URL}/alerts/realtime/{rodovia}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        return data.get('alertas', [])
    except Exception as e:
        st.warning(f"Erro ao obter alertas: {e}")
        return []

def main():
    """Função principal do dashboard"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🛡️ Protetor de Viagens PRF</h1>
        <p>Digite sua viagem e receba análise de risco em tempo real</p>
        <p><strong>PREVENÇÃO</strong> é a melhor proteção! 🚗💨</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Sobre o Sistema")
        st.markdown("""
        Este sistema analisa o **risco de acidentes** em viagens rodoviárias
        antes que elas aconteçam, usando:
        
        - 🧠 **IA Avançada**: Processamento de linguagem natural
        - 🌦️ **Dados Externos**: Clima, tráfego, alertas PRF
        - 📊 **Análise Multi-fatorial**: 16+ fatores de risco
        - 💡 **Recomendações**: Sugestões personalizadas
        
        **Como usar:**
        1. Digite sua viagem naturalmente
        2. Sistema analisa automaticamente
        3. Receba alertas e recomendações
        4. Viaje com mais segurança! 🛡️
        """)
        
        st.header("📊 Estatísticas")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Análises Hoje", "47", "12%")
        with col2:
            st.metric("Riscos Evitados", "23", "8%")
    
    # Layout principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🗣️ Descreva sua viagem")
        
        # Inicializar estado para exemplo selecionado
        if 'exemplo_selecionado' not in st.session_state:
            st.session_state.exemplo_selecionado = None
        
        # Input principal
        texto_viagem = st.text_input(
            "",
            value=st.session_state.exemplo_selecionado if st.session_state.exemplo_selecionado else "",
            placeholder="Ex: Vou de São Paulo para Santos amanhã às 18h",
            help="Digite naturalmente como você falaria",
            key="input_viagem"
        )
        
        # Botões de exemplo
        st.markdown("**💡 Exemplos de uso:**")
        exemplos = [
            "Vou para Santos amanhã às 18h",
            "Preciso ir para Campinas hoje à noite de moto",
            "Viagem para Rio de Janeiro sexta às 15h com a família",
            "Vou de São Paulo para Belo Horizonte segunda de manhã"
        ]
        
        cols = st.columns(len(exemplos))
        for idx, exemplo in enumerate(exemplos):
            with cols[idx]:
                if st.button(exemplo, key=f"ex_{idx}"):
                    st.session_state.exemplo_selecionado = exemplo
                    st.rerun()
        
        # Limpar exemplo selecionado após uso
        if st.session_state.exemplo_selecionado:
            st.session_state.exemplo_selecionado = None
    
    with col2:
        st.subheader("🔍 Análise")
        if st.button("🔍 Analisar Risco", type="primary", use_container_width=True):
            if texto_viagem:
                with st.spinner("Analisando sua viagem..."):
                    resultado = analisar_viagem_api(texto_viagem)
                    if resultado:
                        # Armazenar resultado no session_state
                        st.session_state.resultado_analise = resultado
                        st.session_state.texto_analisado = texto_viagem
                        st.rerun()
            else:
                st.warning("Digite sua viagem primeiro!")
    
    # Exibir resultado se existir
    if 'resultado_analise' in st.session_state and st.session_state.resultado_analise:
        st.markdown("---")
        
        # Container do resultado persistente
        st.markdown('<div class="resultado-persistente">', unsafe_allow_html=True)
        
        # Header com indicador de resultado persistente
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📊 Resultado da Análise")
        with col2:
            st.markdown('<div class="status-saved">✅ Resultado Salvo</div>', unsafe_allow_html=True)
        
        # Mostrar o texto analisado
        st.info(f"**Viagem analisada:** {st.session_state.texto_analisado}")
        
        # Exibir resultado
        exibir_resultado(st.session_state.resultado_analise)
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🗑️ Limpar Resultado", type="secondary", use_container_width=True):
                del st.session_state.resultado_analise
                del st.session_state.texto_analisado
                st.rerun()
        
        with col2:
            if st.button("🔄 Nova Análise", type="primary", use_container_width=True):
                st.session_state.resultado_analise = None
                st.session_state.texto_analisado = None
                st.rerun()
        
        with col3:
            if st.button("📋 Copiar Resultado", type="secondary", use_container_width=True):
                st.success("Resultado copiado! (funcionalidade em desenvolvimento)")
        
        # Fechar container CSS
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de alertas em tempo real
    st.markdown("---")
    st.subheader("🚨 Alertas em Tempo Real")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("SP-160 (Imigrantes)"):
            alertas = obter_alertas_api("SP-160")
            if alertas:
                for alerta in alertas:
                    st.warning(f"⚠️ {alerta.get('descricao', 'Alerta')} - {alerta.get('localizacao', 'N/A')}")
            else:
                st.success("✅ Nenhum alerta ativo")
    
    with col2:
        if st.button("SP-150 (Anchieta)"):
            alertas = obter_alertas_api("SP-150")
            if alertas:
                for alerta in alertas:
                    st.warning(f"⚠️ {alerta.get('descricao', 'Alerta')} - {alerta.get('localizacao', 'N/A')}")
            else:
                st.success("✅ Nenhum alerta ativo")
    
    with col3:
        if st.button("BR-116 (Dutra)"):
            alertas = obter_alertas_api("BR-116")
            if alertas:
                for alerta in alertas:
                    st.warning(f"⚠️ {alerta.get('descricao', 'Alerta')} - {alerta.get('localizacao', 'N/A')}")
            else:
                st.success("✅ Nenhum alerta ativo")

def exibir_resultado(resultado: Dict):
    """Exibe resultado da análise de forma visual"""
    
    nivel_risco = resultado.get('nivel_risco', 'BAIXO')
    probabilidade = resultado.get('risco_total', 0)
    segmentos_perigosos = resultado.get('segmentos_perigosos', [])
    recomendacoes = resultado.get('recomendacoes', [])
    alternativas = resultado.get('alternativas', {})
    dados_viagem = resultado.get('detalhes_viagem', {})
    
    # Determinar classe CSS baseada no risco
    classe_risco = f"risk-{nivel_risco.lower()}"
    
    # Header do resultado com timestamp
    timestamp = resultado.get('timestamp_analise', 'N/A')
    st.markdown(f"""
    <div class="risk-card {classe_risco}">
        <h2>{obter_icone_risco(nivel_risco)} Análise de Risco: {nivel_risco}</h2>
        <p><strong>Probabilidade de Acidente:</strong> {probabilidade:.1f}%</p>
        <p><strong>Análise realizada em:</strong> {timestamp}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Gauge de risco
        fig_gauge = criar_gauge_risco(probabilidade, nivel_risco)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col2:
        st.metric("📍 Distância", f"{dados_viagem.get('distancia_km', 0):.1f} km")
        st.metric("⏱️ Tempo Estimado", dados_viagem.get('tempo_estimado', 'N/A'))
    
    with col3:
        clima = dados_viagem.get('clima', {})
        st.metric("🌦️ Clima", clima.get('descricao', 'Bom'))
        st.metric("👁️ Visibilidade", f"{clima.get('visibilidade', 10):.1f} km")
    
    with col4:
        st.metric("🚦 Trânsito", dados_viagem.get('trafego', 'Normal'))
        st.metric("🚗 Veículo", dados_viagem.get('tipo_veiculo', 'carro').title())
    
    # Mapa interativo
    if dados_viagem.get('origem') and dados_viagem.get('destino'):
        st.subheader("🗺️ Sua Rota")
        mapa = criar_mapa_rota(
            dados_viagem['origem'], 
            dados_viagem['destino']
        )
        st_folium(mapa, width=700, height=400)
    
    # Fatores de risco
    if segmentos_perigosos:
        st.subheader("⚠️ Segmentos Perigosos Identificados")
        for segmento in segmentos_perigosos[:3]:  # Mostrar apenas os 3 mais perigosos
            st.warning(f"📍 BR-{segmento.get('br', 'N/A')} km {segmento.get('km', 'N/A')}: {segmento.get('nivel_risco', 'ALTO')} - {segmento.get('fatores_risco', ['Risco elevado'])[0] if segmento.get('fatores_risco') else 'Risco elevado'}")
    else:
        st.info("✅ Nenhum segmento de alto risco identificado nesta rota")
    
    # Recomendações
    if recomendacoes:
        st.subheader("💡 Recomendações Personalizadas")
        for rec in recomendacoes:
            st.markdown(f"""
            <div class="recommendation">
                <strong>{rec}</strong>
            </div>
            """, unsafe_allow_html=True)
    
    # Alternativas
    if alternativas:
        col1, col2 = st.columns(2)
        
        with col1:
            if alternativas.get('horarios_seguros'):
                st.subheader("⏰ Horários Mais Seguros")
                for horario in alternativas['horarios_seguros']:
                    st.success(f"✅ {horario}")
        
        with col2:
            if alternativas.get('rotas_alternativas'):
                st.subheader("🛣️ Rotas Alternativas")
                for rota in alternativas['rotas_alternativas']:
                    st.info(f"🛣️ {rota}")
    
    # Dicas gerais
    if alternativas.get('dicas_gerais'):
        st.subheader("📋 Dicas Gerais")
        for dica in alternativas['dicas_gerais']:
            st.markdown(f"• {dica}")
    
    # Seção de compartilhamento
    st.markdown("---")
    st.subheader("📤 Compartilhar Análise")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📱 Gerar Link"):
            st.success("Link gerado! (funcionalidade em desenvolvimento)")
    
    with col2:
        if st.button("📧 Enviar por Email"):
            st.success("Email enviado! (funcionalidade em desenvolvimento)")
    
    with col3:
        if st.button("🖨️ Imprimir Relatório"):
            st.success("Relatório salvo! (funcionalidade em desenvolvimento)")

if __name__ == "__main__":
    main()
