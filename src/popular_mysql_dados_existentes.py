# src/popular_mysql_dados_existentes.py - Popular MySQL com dados existentes

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Importando o gerenciador de banco
from database import DatabaseManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def carregar_dados_existentes():
    """
    Carrega dados existentes do CSV
    """
    logger.info("📊 CARREGANDO DADOS EXISTENTES")
    logger.info("-" * 50)
    
    # Verificando arquivos existentes
    arquivos_csv = [
        "data/raw/acidentes_reais_combinados.csv",
        "data/raw/acidentes_prf_todos_anos_combinados.csv"
    ]
    
    df = None
    arquivo_usado = None
    
    for arquivo in arquivos_csv:
        if Path(arquivo).exists():
            logger.info(f"📁 Encontrado: {arquivo}")
            try:
                df = pd.read_csv(arquivo, encoding='utf-8')
                arquivo_usado = arquivo
                logger.info(f"✅ {len(df):,} registros carregados")
                break
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar {arquivo}: {e}")
                continue
    
    if df is None:
        logger.error("❌ Nenhum arquivo de dados encontrado")
        return None
    
    logger.info(f"📊 Arquivo usado: {arquivo_usado}")
    logger.info(f"📊 Colunas: {list(df.columns)}")
    logger.info(f"📊 Período: {df['data_inversa'].min()} a {df['data_inversa'].max()}")
    
    return df

def processar_dados_para_mysql(df):
    """
    Processa dados para inserção no MySQL
    """
    logger.info("🔄 PROCESSANDO DADOS PARA MYSQL")
    logger.info("-" * 50)
    
    df_processado = df.copy()
    
    # 1. Mapeamento de gravidade para números
    logger.info("   Mapeando gravidade...")
    mapa_gravidade = {
        'SEM VÍTIMAS': 0,
        'ILESO': 0,
        'FERIDOS LEVES': 1,
        'FERIDOS': 1,
        'FERIDOS GRAVES': 2,
        'ÓBITOS': 3,
        'MORTOS': 3
    }
    
    if 'classificacao_acidente' in df_processado.columns:
        # Primeiro, vamos ver quais valores únicos existem
        valores_unicos = df_processado['classificacao_acidente'].unique()
        logger.info(f"   Valores únicos encontrados: {valores_unicos}")
        
        # Mapeamento baseado nos valores reais encontrados
        mapa_gravidade_expandido = {
            'Sem vítimas': 0,
            'Com feridos leves': 1,
            'Com feridos graves': 2,
            'Com vítimas fatais': 3,
            # Variações possíveis
            'SEM VÍTIMAS': 0,
            'SEM VITIMAS': 0,
            'ILESO': 0,
            'FERIDOS LEVES': 1,
            'FERIDOS': 1,
            'FERIDOS GRAVES': 2,
            'ÓBITOS': 3,
            'MORTOS': 3,
            'FATAL': 3
        }
        
        # Função de mapeamento mais robusta
        def mapear_gravidade(valor):
            if pd.isna(valor) or valor is None:
                return 0
            
            valor_str = str(valor).strip().upper()
            
            # Verificar fatal primeiro (mais específico)
            if 'FATAL' in valor_str or 'ÓBITO' in valor_str or 'MORTO' in valor_str or 'FATAIS' in valor_str:
                return 3
            elif 'GRAVE' in valor_str:
                return 2
            elif 'LEVE' in valor_str:
                return 1
            elif 'SEM' in valor_str and ('VÍTIMA' in valor_str or 'VITIMA' in valor_str):
                return 0
            elif 'ILESO' in valor_str:
                return 0
            else:
                return 0  # Default para casos não mapeados
        
        df_processado['gravidade_numerica'] = df_processado['classificacao_acidente'].apply(mapear_gravidade)
        
        # Garantir que não há valores None
        df_processado['gravidade_numerica'] = df_processado['gravidade_numerica'].fillna(0).astype(int)
        
        # Verificando distribuição
        dist_gravidade = df_processado['gravidade_numerica'].value_counts().sort_index()
        logger.info("   Distribuição de gravidade:")
        for grav, qtd in dist_gravidade.items():
            pct = qtd / len(df_processado) * 100
            logger.info(f"     {grav}: {qtd:,} ({pct:.1f}%)")
    
    # 2. Adicionando metadados
    logger.info("   Adicionando metadados...")
    df_processado['ano_coleta'] = pd.to_datetime(df_processado['data_inversa']).dt.year
    df_processado['tipo_dados'] = 'dados_reais'
    df_processado['data_coleta'] = datetime.now()
    
    # 3. Renomeando colunas para corresponder ao schema
    logger.info("   Renomeando colunas...")
    df_processado = df_processado.rename(columns={
        'tipo_de_ocorrencia': 'tipo_ocorrencia',
        'causa_acidente': 'causa_acidente',
        'tipo_veiculo': 'tipo_veiculo',
        'condicao_metereologica': 'condicao_metereologica',
        'tipo_pista': 'tipo_pista',
        'tracado_via': 'tracado_via'
    })
    
    # 4. Tratando valores ausentes
    logger.info("   Tratando valores ausentes...")
    
    # Para variáveis categóricas
    colunas_categoricas = df_processado.select_dtypes(include=['object']).columns
    for col in colunas_categoricas:
        ausentes = df_processado[col].isnull().sum()
        if ausentes > 0:
            df_processado[col] = df_processado[col].fillna('Não Informado')
            logger.info(f"     {col}: {ausentes} valores preenchidos")
    
    # Para variáveis numéricas
    colunas_numericas = df_processado.select_dtypes(include=['int64', 'float64']).columns
    for col in colunas_numericas:
        ausentes = df_processado[col].isnull().sum()
        if ausentes > 0:
            mediana = df_processado[col].median()
            df_processado[col] = df_processado[col].fillna(mediana)
            logger.info(f"     {col}: {ausentes} valores preenchidos com mediana {mediana:.2f}")
    
    # 5. Convertendo tipos de dados
    logger.info("   Convertendo tipos de dados...")
    
    # Data
    if 'data_inversa' in df_processado.columns:
        df_processado['data_inversa'] = pd.to_datetime(df_processado['data_inversa']).dt.date
    
    # Horário - tratando diferentes formatos
    if 'horario' in df_processado.columns:
        try:
            # Tentando formato HH:MM:SS
            df_processado['horario'] = pd.to_datetime(df_processado['horario'], format='%H:%M:%S').dt.time
        except ValueError:
            try:
                # Tentando formato HH:MM
                df_processado['horario'] = pd.to_datetime(df_processado['horario'], format='%H:%M').dt.time
            except ValueError:
                # Usando inferência de formato
                df_processado['horario'] = pd.to_datetime(df_processado['horario'], format='mixed').dt.time
    
    # Números inteiros
    int_columns = ['br', 'pessoas', 'veiculos', 'gravidade_numerica', 'ano_coleta']
    for col in int_columns:
        if col in df_processado.columns:
            df_processado[col] = df_processado[col].astype('Int64')
    
    # Decimais
    if 'km' in df_processado.columns:
        df_processado['km'] = pd.to_numeric(df_processado['km'], errors='coerce')
    
    logger.info(f"✅ Processamento concluído: {len(df_processado):,} registros")
    
    return df_processado

def inserir_dados_em_lotes(df, db, tamanho_lote=1000):
    """
    Insere dados em lotes para melhor performance
    """
    logger.info("💾 INSERINDO DADOS NO MYSQL")
    logger.info("-" * 50)
    
    total_registros = len(df)
    registros_inseridos = 0
    
    # Dividindo em lotes
    num_lotes = (total_registros + tamanho_lote - 1) // tamanho_lote
    
    logger.info(f"📊 Total de registros: {total_registros:,}")
    logger.info(f"📦 Número de lotes: {num_lotes}")
    logger.info(f"📦 Tamanho do lote: {tamanho_lote:,}")
    
    for i in range(0, total_registros, tamanho_lote):
        lote_num = (i // tamanho_lote) + 1
        lote_df = df.iloc[i:i + tamanho_lote]
        
        logger.info(f"   Processando lote {lote_num}/{num_lotes} ({len(lote_df):,} registros)...")
        
        try:
            if db.inserir_acidentes(lote_df):
                registros_inseridos += len(lote_df)
                logger.info(f"   ✅ Lote {lote_num} inserido com sucesso")
            else:
                logger.error(f"   ❌ Erro ao inserir lote {lote_num}")
                break
                
        except Exception as e:
            logger.error(f"   ❌ Erro no lote {lote_num}: {e}")
            break
    
    logger.info(f"✅ Inserção concluída: {registros_inseridos:,}/{total_registros:,} registros")
    return registros_inseridos

def main():
    """
    Função principal
    """
    print("🚨 POPULANDO MYSQL COM DADOS EXISTENTES")
    print("="*80)
    
    # 1. Carregando dados existentes
    print("\n📊 Carregando dados existentes...")
    df = carregar_dados_existentes()
    
    if df is None:
        print("❌ Falha ao carregar dados")
        return
    
    print(f"✅ {len(df):,} registros carregados")
    
    # 2. Conectando ao banco
    print("\n🔌 Conectando ao MySQL...")
    db = DatabaseManager()
    
    if not db.conectar():
        print("❌ Falha ao conectar ao banco")
        return
    
    print("✅ Conectado ao MySQL")
    
    # 3. Criando/verificando tabelas
    print("\n📋 Criando/verificando tabelas...")
    if not db.criar_tabelas():
        print("❌ Falha ao criar tabelas")
        return
    
    print("✅ Tabelas criadas/verificadas")
    
    # 4. Limpando dados existentes
    print("\n🧹 Limpando dados existentes...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("DELETE FROM acidentes")
        db.connection.commit()
        cursor.close()
        print("✅ Dados existentes removidos")
    except Exception as e:
        print(f"⚠️ Erro ao limpar dados: {e}")
        print("   Continuando mesmo assim...")
    
    # 5. Processando dados
    print("\n🔄 Processando dados...")
    df_processado = processar_dados_para_mysql(df)
    
    if df_processado is None:
        print("❌ Falha no processamento")
        return
    
    # 6. Inserindo dados
    print("\n💾 Inserindo dados no MySQL...")
    registros_inseridos = inserir_dados_em_lotes(df_processado, db)
    
    # 7. Verificando resultado
    print("\n📊 Verificando resultado...")
    stats = db.obter_estatisticas_gerais()
    
    if stats:
        print(f"✅ Total de acidentes no banco: {stats.get('total_acidentes', 0):,}")
        print(f"📅 Período: {stats.get('periodo_dados', {}).get('data_inicio', 'N/A')} a {stats.get('periodo_dados', {}).get('data_fim', 'N/A')}")
        
        # Distribuição por gravidade
        dist_gravidade = stats.get('distribuicao_gravidade', [])
        if dist_gravidade:
            print("\n📊 Distribuição por gravidade:")
            for item in dist_gravidade:
                grav = item['gravidade_numerica']
                qtd = item['quantidade']
                nome_grav = {0: 'Ileso', 1: 'Ferido Leve', 2: 'Ferido Grave', 3: 'Fatal'}.get(grav, f'Classe {grav}')
                print(f"   {nome_grav}: {qtd:,}")
    
    # 8. Fechando conexão
    db.desconectar()
    
    print("\n" + "="*80)
    print("✅ POPULAÇÃO DO MYSQL CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print(f"📊 Registros inseridos: {registros_inseridos:,}")
    print(f"💾 Dados salvos no banco: machineL")
    print(f"\n🔄 Próximo passo: Executar treinamento dos modelos")
    print(f"   python src/train_model_mysql.py")

if __name__ == "__main__":
    main()
