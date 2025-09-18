#!/usr/bin/env python3
# dashboard_novo.py - Dashboard moderno com linguagem natural

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from src.database import DatabaseManager
from src.processador_linguagem_natural import ProcessadorLinguagemNatural

# Configuração da página
st.set_page_config(
    page_title="🗣️ Sistema de Alerta Preventivo - PRF",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2e7d32);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2e7d32;
    }
    .risk-high { border-left-color: #d32f2f !important; }
    .risk-medium { border-left-color: #f57c00 !important; }
    .risk-low { border-left-color: #2e7d32 !important; }
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar processador de linguagem natural
@st.cache_resource
def get_nlp_processor():
    return ProcessadorLinguagemNatural()

# Função para carregar dados reais
@st.cache_data(ttl=300)
def carregar_dados_reais():
    """Carrega dados reais da PRF do banco MySQL"""
    try:
        st.info("📊 Carregando dados reais da PRF do banco MySQL...")
        
        db = DatabaseManager()
        if not db.conectar():
            st.error("❌ Erro ao conectar ao banco de dados MySQL")
            return None
        
        # Carregar todos os dados (sem limite)
        query = "SELECT * FROM acidentes WHERE ano_coleta <= 2025 ORDER BY data_inversa DESC"
        df = pd.read_sql(query, db.engine)
        
        if df is None or len(df) == 0:
            st.error("❌ Nenhum dado encontrado no banco MySQL")
            db.desconectar()
            return None
        
        # Processar dados
        df['data'] = pd.to_datetime(df['data_inversa'])
        df['gravidade'] = df['classificacao_acidente']
        df['causa'] = df['causa_acidente']
        df['tipo_veiculo'] = df['tipo_veiculo']
        
        # Mapear gravidade
        mapeamento_gravidade = {
            'Sem Vítimas': 'Ileso',
            'Com Vítimas Feridas': 'Ferido Leve',
            'Com Vítimas Fatais': 'Fatal'
        }
        df['gravidade'] = df['gravidade'].map(mapeamento_gravidade).fillna(df['gravidade'])
        
        # Criar período do dia
        df['hora'] = pd.to_datetime(df['horario'], format='%H:%M', errors='coerce').dt.hour
        df['periodo'] = df['hora'].apply(lambda x: 
            'Madrugada' if 0 <= x < 6 else
            'Manhã' if 6 <= x < 12 else
            'Tarde' if 12 <= x < 18 else
            'Noite'
        )
        
        # Obter estatísticas
        stats = db.obter_estatisticas_gerais()
        total_registros = stats.get('total_acidentes', len(df))
        
        db.desconectar()
        
        st.success(f"✅ Dados reais carregados: {len(df):,} registros (de {total_registros:,} total)")
        st.info(f"📅 Período: {df['data'].min().strftime('%d/%m/%Y')} a {df['data'].max().strftime('%d/%m/%Y')}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados reais: {e}")
        return None

# Função para análise de risco via API
def fazer_analise_risco_api(dados):
    """Faz análise de risco via API"""
    try:
        response = requests.post(
            "http://localhost:8000/analise-linguagem-natural",
            json={"texto_viagem": dados},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Erro na API: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Erro na API: {e}")
        return None

# Função para análise de risco via linguagem natural
def fazer_analise_risco_nlp(texto_viagem):
    """Faz análise de risco usando processamento de linguagem natural"""
    try:
        nlp_processor = get_nlp_processor()
        resultado = nlp_processor.processar_texto(texto_viagem)
        
        if resultado:
            # Fazer chamada para API com dados processados
            dados_viagem = {
                "origem": resultado.get('origem', 'São Paulo'),
                "destino": resultado.get('destino', 'Campinas'),
                "data_viagem": resultado.get('data_viagem', datetime.now().strftime('%Y-%m-%d')),
                "horario_saida": resultado.get('horario_saida', '16:00'),
                "br_principal": resultado.get('br_principal', 101),
                "km_inicial": resultado.get('km_inicial', 0.0),
                "km_final": resultado.get('km_final', 50.0),
                "uf": resultado.get('uf', 'SP'),
                "tipo_veiculo": resultado.get('tipo_veiculo', 'AUTOMOVEL'),
                "condicao_metereologica": resultado.get('condicao_metereologica', 'CÉU CLARO'),
                "tipo_pista": resultado.get('tipo_pista', 'DUPLA'),
                "tracado_via": resultado.get('tracado_via', 'RETO'),
                "passageiros": resultado.get('passageiros', 1)
            }
            
            return fazer_analise_risco_api(dados_viagem)
        
        return None
    except Exception as e:
        st.error(f"❌ Erro no processamento NLP: {e}")
        return None

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🗣️ Sistema de Alerta Preventivo de Acidentes - PRF</h1>
    <p>Sistema inteligente para <strong>PREVENIR</strong> acidentes em rodovias federais - digite sua viagem em português natural</p>
</div>
""", unsafe_allow_html=True)

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Status da API
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            st.success("🟢 API Online")
        else:
            st.warning("🟡 API com problemas")
    except:
        st.error("🔴 API Offline")
    
    st.markdown("---")
    
    # Filtros inteligentes
    st.header("🔍 Filtros Inteligentes")
    
    # Filtro por período (mais inteligente)
    periodo_opcoes = {
        "Hoje": 1,
        "Últimos 3 dias": 3,
        "Última semana": 7,
        "Últimos 15 dias": 15,
        "Último mês": 30,
        "Últimos 3 meses": 90,
        "Último ano": 365,
        "Todos os dados": 0
    }
    
    periodo = st.selectbox(
        "📅 Período de Análise",
        list(periodo_opcoes.keys()),
        index=2
    )
    
    # Filtro por estados (com busca)
    st.subheader("🏛️ Estados")
    estados_todos = st.checkbox("Todos os estados", value=True)
    
    if not estados_todos:
        estados_selecionados = st.multiselect(
            "Selecione os estados:",
            ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'],
            default=['SP', 'RJ', 'MG']
        )
    else:
        estados_selecionados = []
    
    # Filtro por gravidade
    st.subheader("🚨 Gravidade")
    gravidade_todos = st.checkbox("Todas as gravidades", value=True)
    
    if not gravidade_todos:
        gravidade_selecionada = st.multiselect(
            "Selecione as gravidades:",
            ['Ileso', 'Ferido Leve', 'Ferido Grave', 'Fatal'],
            default=['Ileso', 'Ferido Leve', 'Ferido Grave', 'Fatal']
        )
    else:
        gravidade_selecionada = []
    
    # Botão de atualização
    if st.button("🔄 Atualizar Dados", type="primary"):
        st.rerun()

# Seção principal - Análise de Risco por Linguagem Natural
st.header("🗣️ Análise de Risco por Linguagem Natural")

# Input de linguagem natural
texto_viagem = st.text_input(
    "💬 Descreva sua viagem em português natural:",
    placeholder="Ex: Vou para Campinas hoje às 16h pela BR-101",
    help="Exemplos: 'Vou para São Paulo amanhã de manhã', 'Viagem para Rio de Janeiro na sexta à tarde'"
)

if texto_viagem:
    if st.button("🚨 Analisar Risco da Viagem", type="primary"):
        with st.spinner("🔍 Analisando risco da viagem..."):
            resultado = fazer_analise_risco_nlp(texto_viagem)
            
            if resultado:
                # Exibir resultado da análise
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    nivel_risco = resultado.get('nivel_risco', 'DESCONHECIDO')
                    cor_risco = {
                        'BAIXO': '🟢',
                        'MÉDIO': '🟡', 
                        'ALTO': '🟠',
                        'CRÍTICO': '🔴'
                    }.get(nivel_risco, '⚪')
                    
                    st.metric(
                        "Nível de Risco",
                        f"{cor_risco} {nivel_risco}",
                        delta=None
                    )
                
                with col2:
                    probabilidade = resultado.get('probabilidade_acidente', 0)
                    st.metric(
                        "Probabilidade de Acidente",
                        f"{probabilidade:.1f}%",
                        delta=None
                    )
                
                with col3:
                    confianca = resultado.get('confianca', 0)
                    st.metric(
                        "Confiança da Análise",
                        f"{confianca:.1f}%",
                        delta=None
                    )
                
                # Fatores de risco
                st.subheader("⚠️ Fatores de Risco Identificados")
                fatores = resultado.get('fatores_risco', [])
                if fatores:
                    for fator in fatores:
                        st.warning(f"• {fator}")
                else:
                    st.info("✅ Nenhum fator de risco específico identificado")
                
                # Recomendações
                st.subheader("💡 Recomendações de Segurança")
                recomendacoes = resultado.get('recomendacoes', [])
                if recomendacoes:
                    for rec in recomendacoes:
                        st.success(f"• {rec}")
                else:
                    st.info("✅ Nenhuma recomendação específica")
                
                # Alternativas
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("⏰ Alternativas de Horário")
                    alternativas_horario = resultado.get('alternativas_horario', [])
                    if alternativas_horario:
                        for alt in alternativas_horario:
                            st.info(f"• {alt}")
                
                with col2:
                    st.subheader("🛣️ Rotas Alternativas")
                    alternativas_rota = resultado.get('alternativas_rota', [])
                    if alternativas_rota:
                        for alt in alternativas_rota:
                            st.info(f"• {alt}")
            else:
                st.error("❌ Não foi possível analisar a viagem. Tente novamente.")

# Carregar dados para visualizações
df = carregar_dados_reais()

if df is not None:
    # Aplicar filtros
    df_filtrado = df.copy()
    
    # Filtro por período
    if periodo != "Todos os dados":
        dias = periodo_opcoes[periodo]
        data_limite = datetime.now() - timedelta(days=dias)
        df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]
    
    # Filtro por estados
    if estados_selecionados:
        df_filtrado = df_filtrado[df_filtrado['uf'].isin(estados_selecionados)]
    
    # Filtro por gravidade
    if gravidade_selecionada:
        df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(gravidade_selecionada)]
    
    st.info(f"🔍 Dados após filtros: {len(df_filtrado):,} registros")
    
    if len(df_filtrado) > 0:
        # Métricas principais
        st.header("📊 Métricas Principais")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_acidentes = len(df_filtrado)
            st.metric("Total de Acidentes", f"{total_acidentes:,}")
        
        with col2:
            acidentes_fatais = len(df_filtrado[df_filtrado['gravidade'] == 'Fatal'])
            st.metric("Acidentes Fatais", f"{acidentes_fatais:,}")
        
        with col3:
            media_vitimas = df_filtrado['pessoas'].mean()
            st.metric("Média de Vítimas", f"{media_vitimas:.1f}")
        
        with col4:
            brs_afetadas = df_filtrado['br'].nunique()
            st.metric("BRs Afetadas", f"{brs_afetadas:,}")
        
        # Gráficos
        st.header("📈 Visualizações")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de gravidade
            gravidade_counts = df_filtrado['gravidade'].value_counts()
            fig_gravidade = px.pie(
                values=gravidade_counts.values,
                names=gravidade_counts.index,
                title="Distribuição por Gravidade",
                color_discrete_map={
                    'Ileso': '#4caf50',
                    'Ferido Leve': '#ff9800',
                    'Ferido Grave': '#ff5722',
                    'Fatal': '#f44336'
                }
            )
            st.plotly_chart(fig_gravidade, use_container_width=True)
        
        with col2:
            # Gráfico de estados
            estado_counts = df_filtrado['uf'].value_counts().head(10)
            fig_estados = px.bar(
                x=estado_counts.index,
                y=estado_counts.values,
                title="Top 10 Estados com Mais Acidentes",
                labels={'x': 'Estado', 'y': 'Número de Acidentes'}
            )
            st.plotly_chart(fig_estados, use_container_width=True)
        
        # Gráfico temporal
        df_temporal = df_filtrado.groupby(df_filtrado['data'].dt.date).size().reset_index()
        df_temporal.columns = ['data', 'acidentes']
        
        fig_temporal = px.line(
            df_temporal,
            x='data',
            y='acidentes',
            title="Evolução Temporal dos Acidentes",
            labels={'data': 'Data', 'acidentes': 'Número de Acidentes'}
        )
        st.plotly_chart(fig_temporal, use_container_width=True)
        
        # Gráfico de horários
        hora_counts = df_filtrado['hora'].value_counts().sort_index()
        fig_horas = px.bar(
            x=hora_counts.index,
            y=hora_counts.values,
            title="Distribuição por Horário do Dia",
            labels={'x': 'Hora', 'y': 'Número de Acidentes'}
        )
        st.plotly_chart(fig_horas, use_container_width=True)
        
    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados")
else:
    st.error("❌ Não foi possível carregar os dados")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🛡️ <strong>Sistema de Alerta Preventivo de Acidentes - PRF</strong></p>
    <p>Prevenindo acidentes e salvando vidas através da inteligência artificial</p>
</div>
""", unsafe_allow_html=True)
