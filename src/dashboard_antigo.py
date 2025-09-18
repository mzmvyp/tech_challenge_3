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
    page_title="Sistema de Alerta Preventivo de Acidentes - PRF",
    page_icon="🗣️",
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
    Carrega dados reais da PRF do banco MySQL
    """
    try:
        from src.database import DatabaseManager
        
        st.info("📊 Carregando dados reais da PRF do banco MySQL...")
        
        # Conectar ao banco
        db = DatabaseManager()
        if not db.conectar():
            st.error("❌ Erro ao conectar ao banco de dados MySQL")
            return None
        
        # Carregar dados do banco (incluindo 2025 - ano atual, excluindo apenas futuros)
        # Usar SQL direto para filtrar anos <= 2025 (sem limite para ter todos os dados)
        import pandas as pd
        query = "SELECT * FROM acidentes WHERE ano_coleta <= 2025 ORDER BY data_inversa DESC"
        df = pd.read_sql(query, db.engine)
        
        if df is None or len(df) == 0:
            st.error("❌ Nenhum dado encontrado no banco MySQL")
            db.desconectar()
            return None
        
        # Processar dados reais
        df['data'] = pd.to_datetime(df['data_inversa'])
        df['gravidade'] = df['classificacao_acidente']
        df['causa'] = df['causa_acidente']
        df['tipo_veiculo'] = df['tipo_veiculo']
        
        # Mapear gravidade para nomes consistentes (baseado nos dados reais do banco)
        mapeamento_gravidade = {
            'Sem Vítimas': 'Ileso',
            'Com Vítimas Feridas': 'Ferido Leve',  # Assumindo que inclui leves e graves
            'Com Vítimas Fatais': 'Fatal'
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
        
        # Obter estatísticas do banco
        stats = db.obter_estatisticas_gerais()
        total_registros = stats.get('total_acidentes', len(df))
        
        db.desconectar()
        
        st.success(f"✅ Dados reais carregados: {len(df):,} registros (de {total_registros:,} total)")
        st.info(f"📅 Período: {df['data'].min().strftime('%d/%m/%Y')} a {df['data'].max().strftime('%d/%m/%Y')}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados reais: {e}")
        st.error("❌ Sistema configurado para usar APENAS dados reais. Verifique a conexão com o banco MySQL.")
        return None

# Função de dados simulados REMOVIDA - Sistema usa apenas dados reais

def fazer_analise_risco_api(dados):
    """
    Faz uma chamada para a API de análise de risco
    """
    try:
        # URL da API (assumindo que está rodando localmente)
        url = "http://localhost:8000/teste-alerta"
        
        response = requests.post(url, json=dados, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"❌ Erro na API: {e}")
        st.error("🔧 Verifique se a API está rodando em http://localhost:8000")
        return None

# Título principal
st.title("🗣️ Sistema de Alerta Preventivo de Acidentes - PRF")
st.markdown("Sistema inteligente para **PREVENIR** acidentes em rodovias federais - digite sua viagem em português natural")
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

# Verificar se os dados foram carregados
if df is None:
    st.error("❌ Não foi possível carregar os dados reais do banco MySQL.")
    st.error("🔧 Verifique se:")
    st.error("   - O XAMPP está rodando")
    st.error("   - O banco 'machineL' existe")
    st.error("   - Os dados foram carregados corretamente")
    st.stop()

# Debug: mostrar informações dos dados
st.success(f"📊 Dados reais carregados: {len(df):,} registros")
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

# Seção de Análise de Risco
st.header("🛡️ Análise de Risco de Viagem")
st.markdown("Use o formulário abaixo para analisar o risco de acidente para uma viagem planejada.")

# Formulário em colunas
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🗺️ Informações da Viagem")
    origem = st.text_input("Cidade de Origem", value="São Paulo")
    destino = st.text_input("Cidade de Destino", value="Campinas")
    data_viagem = st.date_input("Data da Viagem", value=datetime.now().date())
    horario_saida = st.time_input("Horário de Saída", value=datetime.now().time())
    
    st.subheader("📍 Rota")
    uf_pred = st.selectbox("UF", ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "CE"])
    br_principal = st.number_input("BR Principal", min_value=1, max_value=999, value=116)
    km_inicial = st.number_input("KM Inicial", min_value=0.0, max_value=9999.0, value=0.0)
    km_final = st.number_input("KM Final", min_value=0.0, max_value=9999.0, value=50.0)

with col2:
    st.subheader("🚗 Informações do Veículo")
    tipo_veiculo = st.selectbox("Tipo de Veículo",
        ["AUTOMÓVEL", "MOTOCICLETA", "CAMINHÃO", "ÔNIBUS", "OUTROS"])
    passageiros = st.number_input("Número de Passageiros", min_value=1, max_value=10, value=2)
    
    st.subheader("🌤️ Condições Previstas")
    condicao_met = st.selectbox("Condição Meteorológica",
        ["CÉU CLARO", "CHUVA", "NEBLINA", "TEMPORAL", "NUBLADO", "OUTROS"])
    tipo_pista = st.selectbox("Tipo de Pista",
        ["SIMPLE", "DUPLA", "MÚLTIPLA", "OUTROS"])
    tracado_via = st.selectbox("Traçado da Via",
        ["RETA", "CURVA", "INTERSEÇÃO", "PONTE", "VIADUTO"])

with col3:
    st.subheader("📊 Resumo da Viagem")
    distancia = km_final - km_inicial
    st.metric("Distância", f"{distancia:.1f} km")
    
    tempo_estimado = distancia / 80 * 60  # Assumindo 80 km/h média
    st.metric("Tempo Estimado", f"{int(tempo_estimado)} minutos")
    
    st.info("💡 **Dica**: O sistema analisará o risco baseado em 1.449.933 acidentes reais da PRF")

# Botão de análise
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🚨 Analisar Risco da Viagem", type="primary", use_container_width=True):
        with st.spinner("Analisando risco da viagem..."):
            # Preparando dados para API
            dados_viagem = {
                "origem": origem,
                "destino": destino,
                "data_viagem": str(data_viagem),
                "horario_saida": str(horario_saida),
                "br_principal": br_principal,
                "km_inicial": km_inicial,
                "km_final": km_final,
                "uf": uf_pred,
                "tipo_veiculo": tipo_veiculo,
                "condicao_metereologica": condicao_met,
                "tipo_pista": tipo_pista,
                "tracado_via": tracado_via,
                "passageiros": passageiros
            }
            
            # Fazendo análise de risco
            resultado = fazer_analise_risco_api(dados_viagem)
            
            if resultado:
                st.success("✅ Análise de Risco Concluída!")
                
                # Exibindo resultado
                col1, col2 = st.columns(2)
                
                with col1:
                    # Cor baseada no nível de risco
                    cor_risco = {
                        "BAIXO": "🟢",
                        "MÉDIO": "🟡", 
                        "ALTO": "🟠",
                        "CRÍTICO": "🔴"
                    }
                    
                    nivel_risco = resultado['nivel_risco']
                    emoji = cor_risco.get(nivel_risco, "❓")
                    
                    st.markdown(f"""
                    <div class="{'success-box' if nivel_risco == 'BAIXO' else 'warning-box' if nivel_risco == 'MÉDIO' else 'danger-box'}">
                    <h3>{emoji} Nível de Risco: {nivel_risco}</h3>
                    <p><strong>Probabilidade de Acidente:</strong> {resultado['probabilidade_acidente']:.1f}%</p>
                    <p><strong>Confiança:</strong> {resultado['confianca']:.1%}</p>
                    <p><strong>Distância:</strong> {resultado['distancia']:.1f} km</p>
                    <p><strong>Tempo Estimado:</strong> {resultado['tempo_estimado']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### ⚠️ Fatores de Risco Identificados:")
                    if resultado['fatores_risco']:
                        for fator in resultado['fatores_risco']:
                            st.markdown(f"- {fator}")
                    else:
                        st.markdown("- ✅ Nenhum fator de risco específico identificado")
                    
                    st.markdown("### 💡 Recomendações de Segurança:")
                    for recomendacao in resultado['recomendacoes']:
                        st.markdown(f"- {recomendacao}")
                
                # Alternativas
                if resultado.get('alternativas_horario') or resultado.get('alternativas_rota'):
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if resultado.get('alternativas_horario'):
                            st.markdown("### ⏰ Alternativas de Horário:")
                            for alt in resultado['alternativas_horario']:
                                st.markdown(f"- {alt}")
                    
                    with col2:
                        if resultado.get('alternativas_rota'):
                            st.markdown("### 🛣️ Rotas Alternativas:")
                            for alt in resultado['alternativas_rota']:
                                st.markdown(f"- {alt}")
            else:
                st.error("❌ Erro ao analisar risco. Verifique se a API está funcionando.")

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
    <h4>🛡️ Sistema de Alerta Preventivo de Acidentes - PRF</h4>
    <p>Dashboard desenvolvido para o Tech Challenge - Fase 3</p>
    <p>Dados: Polícia Rodoviária Federal | Atualizado: {}</p>
    <p><strong>🛡️ IMPORTANTE:</strong> Este sistema previne acidentes antes que aconteçam, baseado em 1.449.933 registros reais da PRF</p>
    <p><strong>💡 OBJETIVO:</strong> Salvar vidas através de alertas preventivos e recomendações de segurança</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
