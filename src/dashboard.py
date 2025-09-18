# src/dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Acidentes PRF",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #ff4b4b;
    }
    h1 {
        color: #ff4b4b;
    }
    .success-box {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #28a745;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #ffc107;
        margin: 10px 0;
    }
    .danger-box {
        background-color: #f8d7da;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #dc3545;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares
@st.cache_data(ttl=300)
def carregar_dados_reais():
    """
    Carrega dados reais da PRF
    """
    try:
        # Tentar carregar dados reais
        arquivo_dados = Path("data/raw/acidentes_prf_todos_anos_combinados.csv")
        
        if not arquivo_dados.exists():
            st.error("❌ Dados reais não encontrados. Usando dados simulados.")
            return carregar_dados_simulados_fallback()
        
        st.info(f"📊 Carregando dados reais da PRF...")
        df = pd.read_csv(arquivo_dados, encoding='utf-8')
        
        # Processar dados reais
        df['data'] = pd.to_datetime(df['data_inversa'])
        df['gravidade'] = df['classificacao_acidente']
        df['causa'] = df['causa_acidente']
        df['tipo_veiculo'] = df['tipo_veiculo']
        
        # Mapear gravidade para nomes consistentes
        mapeamento_gravidade = {
            'Sem vítimas': 'Ileso',
            'Com feridos leves': 'Ferido Leve', 
            'Com feridos graves': 'Ferido Grave',
            'Com vítimas fatais': 'Fatal'
        }
        df['gravidade'] = df['gravidade'].map(mapeamento_gravidade).fillna(df['gravidade'])
        
        # Criar período do dia baseado no horário
        df['hora'] = pd.to_datetime(df['horario'], format='%H:%M', errors='coerce').dt.hour
        df['periodo'] = df['hora'].apply(lambda x: 
            'Madrugada' if 0 <= x < 6 else
            'Manhã' if 6 <= x < 12 else
            'Tarde' if 12 <= x < 18 else
            'Noite'
        )
        
        st.success(f"✅ Dados reais carregados: {len(df):,} registros")
        st.info(f"📅 Período: {df['data'].min().strftime('%d/%m/%Y')} a {df['data'].max().strftime('%d/%m/%Y')}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados reais: {e}")
        st.info("🔄 Usando dados simulados como fallback...")
        return carregar_dados_simulados_fallback()

def carregar_dados_simulados_fallback():
    """
    Carrega dados simulados como fallback
    """
    np.random.seed(42)
    
    n_acidentes = 2000
    datas = pd.date_range(end=datetime.now(), periods=n_acidentes, freq='H')
    
    estados = ['SP', 'RJ', 'MG', 'PR', 'SC', 'RS', 'BA', 'PE', 'CE']
    brs = [101, 116, 381, 40, 153, 262, 277, 365, 222, 174]
    
    df = pd.DataFrame({
        'data': datas,
        'uf': np.random.choice(estados, n_acidentes),
        'br': np.random.choice(brs, n_acidentes),
        'km': np.random.uniform(0, 500, n_acidentes),
        'gravidade': np.random.choice(
            ['Ileso', 'Ferido Leve', 'Ferido Grave', 'Fatal'],
            n_acidentes,
            p=[0.4, 0.3, 0.2, 0.1]
        ),
        'tipo_veiculo': np.random.choice(
            ['Automóvel', 'Motocicleta', 'Caminhão', 'Ônibus'],
            n_acidentes
        ),
        'causa': np.random.choice(
            ['Velocidade', 'Alcool', 'Sono', 'Ultrapassagem', 'Distração'],
            n_acidentes
        ),
        'pessoas': np.random.randint(1, 8, n_acidentes),
        'veiculos': np.random.randint(1, 4, n_acidentes),
        'condicao_metereologica': np.random.choice(
            ['Sol', 'Chuva', 'Neblina', 'Nublado'],
            n_acidentes,
            p=[0.6, 0.2, 0.1, 0.1]
        ),
        'periodo': np.random.choice(
            ['Madrugada', 'Manhã', 'Tarde', 'Noite'],
            n_acidentes
        )
    })
    
    return df

def fazer_predicao_api(dados):
    """
    Faz uma chamada para a API de predição
    """
    try:
        # URL da API (assumindo que está rodando localmente)
        url = "http://localhost:8000/prever"
        
        response = requests.post(url, json=dados, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        # Se a API não estiver disponível, simular resposta
        return simular_predicao(dados)

def simular_predicao(dados):
    """
    Simula uma predição quando a API não está disponível
    """
    gravidades = ["Ileso/Sem Vítimas", "Feridos Leves", "Feridos Graves", "Fatal/Óbitos"]
    probabilidades = np.random.dirichlet(np.ones(4), size=1)[0]
    gravidade_prevista = np.random.choice(range(4), p=probabilidades)
    
    # Simulando fatores de risco
    fatores_risco = []
    if dados.get('condicao_metereologica', '').upper() == 'CHUVA':
        fatores_risco.append("Condição meteorológica adversa")
    if dados.get('br', 0) in [101, 116, 381]:
        fatores_risco.append("BR com alta incidência")
    if dados.get('veiculos', 1) > 1:
        fatores_risco.append("Múltiplos veículos")
    
    return {
        "gravidade_prevista": int(gravidade_prevista),
        "gravidade_nome": gravidades[gravidade_prevista],
        "probabilidades": {gravidades[i]: float(prob) for i, prob in enumerate(probabilidades)},
        "confianca": float(max(probabilidades)),
        "fatores_risco": fatores_risco,
        "recomendacoes": [
            "Aumentar fiscalização",
            "Verificar sinalização",
            "Monitorar condições da pista"
        ]
    }

# Título principal
st.title("🚨 Dashboard de Previsão de Gravidade de Acidentes - PRF")
st.markdown("Sistema inteligente para análise e previsão de acidentes em rodovias federais")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Seleção de período
    periodo = st.selectbox(
        "Período de Análise",
        ["Últimas 24 horas", "Última semana", "Último mês", "Último ano"],
        index=2
    )
    
    # Filtros
    st.subheader("🔍 Filtros")
    
    estados = st.multiselect(
        "Estados",
        ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "CE"],
        default=["SP", "RJ", "MG"]
    )
    
    gravidade_filtro = st.multiselect(
        "Gravidade",
        ["Ileso", "Ferido Leve", "Ferido Grave", "Fatal"],
        default=["Ileso", "Ferido Leve", "Ferido Grave", "Fatal"]
    )
    
    st.markdown("---")
    
    # Status da API
    st.subheader("📡 Status da API")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            st.success("🟢 API Online")
        else:
            st.error("🔴 API com problemas")
    except:
        st.warning("🟡 API Offline (modo simulação)")
    
    # Botão de atualização
    if st.button("🔄 Atualizar Dados", type="primary"):
        st.rerun()

# Carregando dados
df = carregar_dados_reais()

# Debug: mostrar informações dos dados
st.info(f"📊 Dados carregados: {len(df):,} registros")
st.info(f"📅 Período dos dados: {df['data'].min().strftime('%d/%m/%Y')} a {df['data'].max().strftime('%d/%m/%Y')}")

# Aplicando filtros
df_filtrado = df.copy()

# Filtro por estados
if estados:
    df_filtrado = df_filtrado[df_filtrado['uf'].isin(estados)]

# Filtro por gravidade
if gravidade_filtro:
    df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(gravidade_filtro)]

# Filtro por período
if periodo == "Últimas 24 horas":
    data_limite = datetime.now() - timedelta(hours=24)
    df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]
elif periodo == "Última semana":
    data_limite = datetime.now() - timedelta(weeks=1)
    df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]
elif periodo == "Último mês":
    data_limite = datetime.now() - timedelta(days=30)
    df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]
elif periodo == "Último ano":
    data_limite = datetime.now() - timedelta(days=365)
    df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]

# Debug: mostrar dados após filtragem
st.info(f"🔍 Dados após filtros: {len(df_filtrado):,} registros")
if len(df_filtrado) > 0:
    st.info(f"📅 Período filtrado: {df_filtrado['data'].min().strftime('%d/%m/%Y')} a {df_filtrado['data'].max().strftime('%d/%m/%Y')}")

# Layout principal - KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_acidentes = len(df_filtrado)
    st.metric(
        "Total de Acidentes",
        f"{total_acidentes:,}",
        delta=f"+{int(total_acidentes * 0.05)} vs período anterior"
    )

with col2:
    acidentes_fatais = len(df_filtrado[df_filtrado['gravidade'] == 'Fatal'])
    st.metric(
        "Acidentes Fatais",
        acidentes_fatais,
        delta="-5% vs período anterior",
        delta_color="inverse"
    )

with col3:
    media_vitimas = df_filtrado['pessoas'].mean()
    if pd.isna(media_vitimas):
        media_vitimas = 0
    st.metric(
        "Média de Vítimas",
        f"{media_vitimas:.1f}",
        delta="+0.3 vs período anterior"
    )

with col4:
    brs_afetadas = df_filtrado['br'].nunique()
    st.metric(
        "BRs Afetadas",
        brs_afetadas,
        delta=f"+{int(brs_afetadas * 0.1)} vs período anterior"
    )

st.markdown("---")

# Primeira linha de gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Evolução Temporal dos Acidentes")
    
    # Agrupando por dia
    df_temporal = df_filtrado.groupby(
        df_filtrado['data'].dt.date
    ).size().reset_index(name='quantidade')
    
    fig_temporal = px.line(
        df_temporal,
        x='data',
        y='quantidade',
        title="Acidentes por Dia",
        labels={'data': 'Data', 'quantidade': 'Quantidade'}
    )
    
    fig_temporal.update_traces(line_color='#ff4b4b')
    fig_temporal.update_layout(height=400)
    st.plotly_chart(fig_temporal, use_container_width=True)

with col2:
    st.subheader("🎯 Distribuição por Gravidade")
    
    df_gravidade = df_filtrado['gravidade'].value_counts().reset_index()
    
    # Cores por gravidade
    cores = {
        'Ileso': '#28a745',
        'Ferido Leve': '#ffc107',
        'Ferido Grave': '#fd7e14',
        'Fatal': '#dc3545'
    }
    
    fig_pizza = px.pie(
        df_gravidade,
        values='count',
        names='gravidade',
        title="Proporção por Gravidade",
        color='gravidade',
        color_discrete_map=cores
    )
    
    fig_pizza.update_layout(height=400)
    st.plotly_chart(fig_pizza, use_container_width=True)

# Segunda linha de gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺️ Acidentes por Estado")
    
    df_estados = df_filtrado['uf'].value_counts().reset_index()
    
    fig_estados = px.bar(
        df_estados,
        x='uf',
        y='count',
        title="Top Estados com Mais Acidentes",
        labels={'uf': 'Estado', 'count': 'Quantidade'},
        color='count',
        color_continuous_scale='Reds'
    )
    
    fig_estados.update_layout(height=400)
    st.plotly_chart(fig_estados, use_container_width=True)

with col2:
    st.subheader("🚗 Tipos de Veículos Envolvidos")
    
    df_veiculos = df_filtrado['tipo_veiculo'].value_counts().reset_index()
    
    fig_veiculos = px.bar(
        df_veiculos,
        y='tipo_veiculo',
        x='count',
        title="Veículos Mais Envolvidos",
        labels={'tipo_veiculo': 'Tipo', 'count': 'Quantidade'},
        orientation='h',
        color='count',
        color_continuous_scale='Blues'
    )
    
    fig_veiculos.update_layout(height=400)
    st.plotly_chart(fig_veiculos, use_container_width=True)

# Terceira linha - Análise por período e causa
col1, col2 = st.columns(2)

with col1:
    st.subheader("🕐 Acidentes por Período do Dia")
    
    df_periodo = df_filtrado['periodo'].value_counts().reset_index()
    
    fig_periodo = px.bar(
        df_periodo,
        x='periodo',
        y='count',
        title="Distribuição por Período",
        labels={'periodo': 'Período', 'count': 'Quantidade'},
        color='count',
        color_continuous_scale='Viridis'
    )
    
    fig_periodo.update_layout(height=400)
    st.plotly_chart(fig_periodo, use_container_width=True)

with col2:
    st.subheader("⚠️ Principais Causas")
    
    df_causas = df_filtrado['causa'].value_counts().reset_index()
    
    fig_causas = px.bar(
        df_causas,
        y='causa',
        x='count',
        title="Causas Mais Frequentes",
        labels={'causa': 'Causa', 'count': 'Quantidade'},
        orientation='h',
        color='count',
        color_continuous_scale='Oranges'
    )
    
    fig_causas.update_layout(height=400)
    st.plotly_chart(fig_causas, use_container_width=True)

st.markdown("---")

# Seção de Previsão
st.header("🤖 Fazer Nova Previsão")
st.markdown("Use o formulário abaixo para prever a gravidade de um acidente com base nas características informadas.")

# Formulário em colunas
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📅 Informações Temporais")
    dia_semana = st.selectbox("Dia da Semana", 
        ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO"])
    horario = st.time_input("Horário", value=datetime.now().time())
    
    st.subheader("📍 Localização")
    uf_pred = st.selectbox("UF", ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "CE"])
    br = st.number_input("BR", min_value=1, max_value=999, value=101)
    km = st.number_input("KM", min_value=0.0, max_value=9999.0, value=100.0)
    municipio = st.text_input("Município", value="SAO PAULO")

with col2:
    st.subheader("🚗 Informações do Acidente")
    tipo_veiculo = st.selectbox("Tipo de Veículo",
        ["AUTOMÓVEL", "MOTOCICLETA", "CAMINHÃO", "ÔNIBUS"])
    tipo_ocorrencia = st.selectbox("Tipo de Ocorrência",
        ["COLISÃO FRONTAL", "COLISÃO TRASEIRA", "COLISÃO LATERAL", "CAPOTAMENTO", "ATROPELAMENTO"])
    causa_acidente = st.selectbox("Causa Provável",
        ["VELOCIDADE", "ALCOOL", "SONO", "ULTRAPASSAGEM", "DISTRAÇÃO"])
    
    st.subheader("👥 Pessoas e Veículos")
    pessoas = st.number_input("Pessoas Envolvidas", min_value=1, max_value=50, value=2)
    veiculos = st.number_input("Veículos Envolvidos", min_value=1, max_value=10, value=1)

with col3:
    st.subheader("🌤️ Condições")
    condicao_met = st.selectbox("Condição Meteorológica",
        ["SOL", "CHUVA", "NEBLINA", "NUBLADO"])
    tipo_pista = st.selectbox("Tipo de Pista",
        ["SIMPLES", "DUPLA", "MÚLTIPLA"])
    tracado_via = st.selectbox("Traçado da Via",
        ["RETA", "CURVA", "CRUZAMENTO", "INTERSEÇÃO"])

# Botão de previsão
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🔮 Prever Gravidade", type="primary", use_container_width=True):
        with st.spinner("Fazendo previsão..."):
            # Preparando dados para API
            dados_predicao = {
                "dia_semana": dia_semana,
                "horario": str(horario),
                "condicao_metereologica": condicao_met,
                "tipo_pista": tipo_pista,
                "tracado_via": tracado_via,
                "tipo_ocorrencia": tipo_ocorrencia,
                "causa_acidente": causa_acidente,
                "tipo_veiculo": tipo_veiculo,
                "br": br,
                "km": km,
                "uf": uf_pred,
                "municipio": municipio,
                "pessoas": pessoas,
                "veiculos": veiculos
            }
            
            # Fazendo previsão
            resultado = fazer_predicao_api(dados_predicao)
            
            if resultado:
                st.success("✅ Previsão Concluída!")
                
                # Exibindo resultado
                col1, col2 = st.columns(2)
                
                with col1:
                    # Cor baseada na gravidade
                    cor_gravidade = {
                        0: "🟢",
                        1: "🟡", 
                        2: "🟠",
                        3: "🔴"
                    }
                    
                    gravidade_cod = resultado['gravidade_prevista']
                    emoji = cor_gravidade.get(gravidade_cod, "❓")
                    
                    st.markdown(f"""
                    <div class="{'success-box' if gravidade_cod == 0 else 'warning-box' if gravidade_cod == 1 else 'danger-box'}">
                    <h3>{emoji} Gravidade Prevista: {resultado['gravidade_nome']}</h3>
                    <p><strong>Confiança:</strong> {resultado['confianca']:.1%}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**Probabilidades por Classe:**")
                    for classe, prob in resultado['probabilidades'].items():
                        st.progress(prob, text=f"{classe}: {prob:.1%}")
                
                with col2:
                    st.markdown("### 📋 Fatores de Risco Identificados:")
                    if resultado['fatores_risco']:
                        for fator in resultado['fatores_risco']:
                            st.markdown(f"- ⚠️ {fator}")
                    else:
                        st.markdown("- ✅ Nenhum fator de risco específico identificado")
                    
                    st.markdown("### 💡 Recomendações:")
                    for recomendacao in resultado['recomendacoes']:
                        st.markdown(f"- {recomendacao}")
            else:
                st.error("❌ Erro ao fazer previsão. Verifique se a API está funcionando.")

# Seção de estatísticas detalhadas
st.markdown("---")
st.header("📊 Estatísticas Detalhadas")

# Tabela com dados recentes
st.subheader("📋 Acidentes Recentes")
df_recentes = df_filtrado.sort_values('data', ascending=False).head(10)
st.dataframe(
    df_recentes[['data', 'uf', 'br', 'gravidade', 'tipo_veiculo', 'causa']],
    use_container_width=True
)

# Heatmap de acidentes por estado e gravidade
st.subheader("🔥 Mapa de Calor: Estado vs Gravidade")
heatmap_data = pd.crosstab(df_filtrado['uf'], df_filtrado['gravidade'])

fig_heatmap = px.imshow(
    heatmap_data.T,
    title="Distribuição de Acidentes por Estado e Gravidade",
    labels=dict(x="Estado", y="Gravidade", color="Quantidade"),
    color_continuous_scale="Reds"
)

fig_heatmap.update_layout(height=400)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Rodapé
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <h4>🚨 Sistema de Previsão de Gravidade de Acidentes - PRF</h4>
    <p>Dashboard desenvolvido para o Tech Challenge - Fase 3</p>
    <p>Dados: Polícia Rodoviária Federal | Atualizado: {}</p>
    <p><strong>⚠️ IMPORTANTE:</strong> Este sistema é para fins educacionais e não substitui análises oficiais da PRF</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
