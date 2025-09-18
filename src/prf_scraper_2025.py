# src/prf_scraper_2025.py - Sistema de Scraping Atualizado para Dados PRF 2025

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import os
from pathlib import Path
import warnings
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import zipfile
import io
warnings.filterwarnings('ignore')

# Configurando logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PRFScraper2025:
    """
    Sistema de scraping atualizado para dados da PRF 2025
    
    Esta classe implementa:
    1. Scraping do site oficial da PRF
    2. Download automático dos CSVs
    3. Processamento e limpeza dos dados
    4. Integração com o sistema de ML existente
    """
    
    def __init__(self, diretorio_saida="data/raw", anos=None):
        self.diretorio_saida = Path(diretorio_saida)
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Anos para coletar (todos os disponíveis por padrão)
        self.anos = anos if anos else list(range(2007, 2026))  # 2007-2025
        
        # URLs base da PRF
        self.base_url = "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf"
        self.dados_url = "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-acidentes"
        
        # Headers para simular navegador
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Sessão para manter cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def obter_links_dados(self):
        """
        Obtém todos os links de download dos dados da PRF para todos os anos
        """
        self.logger.info("🔍 Obtendo links de download da PRF para todos os anos...")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procurando por links de download
            links_dados = []
            
            # Procurando por tabelas com links de download
            tabelas = soup.find_all('table')
            
            for tabela in tabelas:
                linhas = tabela.find_all('tr')
                for linha in linhas:
                    celulas = linha.find_all('td')
                    if len(celulas) >= 2:
                        # Primeira célula: descrição
                        descricao = celulas[0].get_text(strip=True)
                        
                        # Segunda célula: link
                        link_celula = celulas[1].find('a')
                        if link_celula and link_celula.get('href'):
                            link = link_celula.get('href')
                            
                            # Verificando se é um link de dados de acidentes
                            if 'acidente' in descricao.lower() and ('csv' in link.lower() or 'download' in link.lower()):
                                # Convertendo link relativo para absoluto
                                if link.startswith('/'):
                                    link = f"https://www.gov.br{link}"
                                elif not link.startswith('http'):
                                    link = urljoin(self.base_url, link)
                                
                                # Extraindo ano do link ou descrição
                                ano_match = re.search(r'20\d{2}', descricao)
                                ano = int(ano_match.group()) if ano_match else None
                                
                                # Determinando tipo de dados
                                tipo = 'ocorrencia'
                                if 'pessoa' in descricao.lower():
                                    if 'todas as causas' in descricao.lower():
                                        tipo = 'pessoa_completo'
                                    else:
                                        tipo = 'pessoa'
                                
                                links_dados.append({
                                    'ano': ano,
                                    'tipo': tipo,
                                    'descricao': descricao,
                                    'url': link
                                })
            
            # Se não encontrou links suficientes, tentar URLs diretas
            if len(links_dados) < 10:
                self.logger.info("🔄 Tentando URLs diretas para anos específicos...")
                links_diretos = self.gerar_urls_diretas()
                links_dados.extend(links_diretos)
            
            self.logger.info(f"✅ Encontrados {len(links_dados)} links de dados")
            
            # Ordenando por ano (mais recente primeiro)
            links_dados.sort(key=lambda x: x['ano'] or 0, reverse=True)
            
            return links_dados
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter links: {e}")
            # Tentar URLs diretas como fallback
            self.logger.info("🔄 Usando URLs diretas como fallback...")
            return self.gerar_urls_diretas()
    
    def gerar_urls_diretas(self):
        """
        Gera URLs diretas para todos os anos disponíveis
        """
        self.logger.info("🔗 Gerando URLs diretas para todos os anos...")
        
        links_diretos = []
        
        # Padrões de URL conhecidos da PRF
        padroes_url = [
            # Padrão 1: acidentes{ano}.csv
            "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-acidentes/acidentes{ano}.csv",
            # Padrão 2: acidentes{ano}_ocorrencia.csv
            "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-acidentes/acidentes{ano}_ocorrencia.csv",
            # Padrão 3: acidentes{ano}_pessoa.csv
            "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-acidentes/acidentes{ano}_pessoa.csv",
            # Padrão 4: acidentes{ano}_pessoa_completo.csv
            "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-acidentes/acidentes{ano}_pessoa_completo.csv"
        ]
        
        tipos = ['ocorrencia', 'ocorrencia', 'pessoa', 'pessoa_completo']
        
        for ano in self.anos:
            for i, padrao in enumerate(padroes_url):
                url = padrao.format(ano=ano)
                tipo = tipos[i]
                
                links_diretos.append({
                    'ano': ano,
                    'tipo': tipo,
                    'descricao': f"Documento CSV de Acidentes {ano} ({tipo.replace('_', ' ').title()})",
                    'url': url
                })
        
        self.logger.info(f"   Geradas {len(links_diretos)} URLs diretas")
        return links_diretos
    
    def baixar_arquivo_csv(self, url, nome_arquivo):
        """
        Baixa um arquivo CSV da URL fornecida
        """
        self.logger.info(f"📥 Baixando: {nome_arquivo}")
        
        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Verificando se é um arquivo ZIP
            if 'application/zip' in response.headers.get('content-type', ''):
                self.logger.info("   📦 Arquivo ZIP detectado, extraindo...")
                return self.extrair_csv_do_zip(response.content, nome_arquivo)
            
            # Tentando diferentes encodings e separadores
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            separators = [';', ',', '\t', '|']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        # Resetando o stream
                        response.raw.seek(0)
                        
                        # Lendo CSV
                        df = pd.read_csv(
                            response.raw,
                            encoding=encoding,
                            sep=sep,
                            decimal=',',
                            low_memory=False,
                            on_bad_lines='skip',
                            header=0
                        )
                        
                        # Verificando se tem dados válidos
                        if len(df) > 100 and len(df.columns) > 5:
                            self.logger.info(f"   ✅ Sucesso: {len(df):,} registros, {len(df.columns)} colunas")
                            self.logger.info(f"   📊 Encoding: {encoding}, Separador: '{sep}'")
                            
                            # Salvando arquivo
                            arquivo_path = self.diretorio_saida / f"{nome_arquivo}.csv"
                            df.to_csv(arquivo_path, index=False, encoding='utf-8')
                            self.logger.info(f"   💾 Salvo em: {arquivo_path}")
                            
                            return df
                            
                    except Exception as e:
                        continue
            
            self.logger.error(f"   ❌ Não foi possível ler o arquivo com nenhuma configuração")
            return None
            
        except Exception as e:
            self.logger.error(f"   ❌ Erro ao baixar arquivo: {e}")
            return None
    
    def extrair_csv_do_zip(self, conteudo_zip, nome_arquivo):
        """
        Extrai arquivo CSV de um ZIP
        """
        try:
            with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zip_file:
                # Listando arquivos no ZIP
                arquivos = zip_file.namelist()
                csv_files = [f for f in arquivos if f.endswith('.csv')]
                
                if not csv_files:
                    self.logger.error("   ❌ Nenhum arquivo CSV encontrado no ZIP")
                    return None
                
                # Usando o primeiro CSV encontrado
                csv_nome = csv_files[0]
                self.logger.info(f"   📄 Extraindo: {csv_nome}")
                
                # Lendo CSV do ZIP
                with zip_file.open(csv_nome) as csv_file:
                    # Tentando diferentes configurações
                    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
                    separators = [';', ',', '\t', '|']
                    
                    for encoding in encodings:
                        for sep in separators:
                            try:
                                csv_file.seek(0)
                                df = pd.read_csv(
                                    csv_file,
                                    encoding=encoding,
                                    sep=sep,
                                    decimal=',',
                                    low_memory=False,
                                    on_bad_lines='skip',
                                    header=0
                                )
                                
                                if len(df) > 100 and len(df.columns) > 5:
                                    self.logger.info(f"   ✅ Sucesso: {len(df):,} registros")
                                    
                                    # Salvando arquivo
                                    arquivo_path = self.diretorio_saida / f"{nome_arquivo}.csv"
                                    df.to_csv(arquivo_path, index=False, encoding='utf-8')
                                    self.logger.info(f"   💾 Salvo em: {arquivo_path}")
                                    
                                    return df
                                    
                            except Exception as e:
                                continue
                    
                    self.logger.error("   ❌ Não foi possível ler CSV do ZIP")
                    return None
                    
        except Exception as e:
            self.logger.error(f"   ❌ Erro ao extrair ZIP: {e}")
            return None
    
    def explorar_estrutura_dados(self, df, ano, tipo):
        """
        Explora a estrutura dos dados baixados
        """
        self.logger.info("="*80)
        self.logger.info(f"📊 ESTRUTURA DOS DADOS - {ano} ({tipo.upper()})")
        self.logger.info("="*80)
        
        # Dimensões
        self.logger.info(f"\n📏 Dimensões:")
        self.logger.info(f"   - Linhas: {df.shape[0]:,}")
        self.logger.info(f"   - Colunas: {df.shape[1]}")
        
        # Colunas
        self.logger.info(f"\n📋 Colunas disponíveis:")
        for i, col in enumerate(df.columns, 1):
            self.logger.info(f"   {i:2d}. {col}")
        
        # Tipos de dados
        self.logger.info(f"\n🔤 Tipos de dados:")
        tipos = df.dtypes.value_counts()
        for tipo_dados, count in tipos.items():
            self.logger.info(f"   {tipo_dados}: {count} colunas")
        
        # Valores ausentes
        self.logger.info(f"\n❓ Valores ausentes:")
        ausentes = df.isnull().sum()
        for col in df.columns:
            if ausentes[col] > 0:
                pct = (ausentes[col] / len(df)) * 100
                self.logger.info(f"   - {col}: {ausentes[col]:,} ({pct:.1f}%)")
        
        # Amostra dos dados
        self.logger.info(f"\n📄 Primeiras 3 linhas:")
        self.logger.info(f"{df.head(3).to_string()}")
        
        return df
    
    def limpar_dados_prf(self, df, ano, tipo):
        """
        Limpa e padroniza os dados da PRF
        """
        self.logger.info(f"🧹 LIMPEZA DOS DADOS - {ano} ({tipo.upper()})")
        self.logger.info("-" * 50)
        
        df_limpo = df.copy()
        inicial = len(df_limpo)
        
        # 1. Removendo duplicatas
        self.logger.info("\n1️⃣ Removendo duplicatas...")
        antes = len(df_limpo)
        df_limpo = df_limpo.drop_duplicates()
        depois = len(df_limpo)
        self.logger.info(f"   Removidas: {antes - depois:,} duplicatas")
        
        # 2. Padronizando nomes de colunas
        self.logger.info("\n2️⃣ Padronizando colunas...")
        df_limpo.columns = df_limpo.columns.str.strip().str.upper()
        
        # Mapeamento de colunas comuns
        mapeamento_colunas = {
            'DATA_INVERSA': 'data_inversa',
            'HORARIO': 'horario',
            'DIA_SEMANA': 'dia_semana',
            'UF': 'uf',
            'BR': 'br',
            'KM': 'km',
            'MUNICIPIO': 'municipio',
            'TIPO_OCORRENCIA': 'tipo_ocorrencia',
            'CAUSA_ACIDENTE': 'causa_acidente',
            'TIPO_VEICULO': 'tipo_veiculo',
            'CONDICAO_METEREOLOGICA': 'condicao_metereologica',
            'TIPO_PISTA': 'tipo_pista',
            'TRACADO_VIA': 'tracado_via',
            'PESSOAS': 'pessoas',
            'VEICULOS': 'veiculos',
            'CLASSIFICACAO_ACIDENTE': 'classificacao_acidente',
            'GRAVIDADE': 'classificacao_acidente',
            'VITIMA': 'classificacao_acidente'
        }
        
        df_limpo = df_limpo.rename(columns=mapeamento_colunas)
        self.logger.info("   ✅ Colunas padronizadas")
        
        # 3. Tratando valores ausentes
        self.logger.info("\n3️⃣ Tratando valores ausentes...")
        
        # Categóricas: substituir por 'Não Informado'
        colunas_categoricas = df_limpo.select_dtypes(include=['object']).columns
        for col in colunas_categoricas:
            ausentes_antes = df_limpo[col].isnull().sum()
            if ausentes_antes > 0:
                df_limpo[col] = df_limpo[col].fillna('Não Informado')
                self.logger.info(f"   {col}: {ausentes_antes} valores preenchidos")
        
        # Numéricas: substituir pela mediana
        colunas_numericas = df_limpo.select_dtypes(include=['int64', 'float64']).columns
        for col in colunas_numericas:
            ausentes_antes = df_limpo[col].isnull().sum()
            if ausentes_antes > 0:
                mediana = df_limpo[col].median()
                df_limpo[col] = df_limpo[col].fillna(mediana)
                self.logger.info(f"   {col}: {ausentes_antes} valores preenchidos com mediana {mediana:.2f}")
        
        # 4. Padronizando texto
        self.logger.info("\n4️⃣ Padronizando texto...")
        for col in colunas_categoricas:
            df_limpo[col] = df_limpo[col].astype(str).str.strip().str.upper()
        self.logger.info("   ✅ Texto padronizado")
        
        # 5. Verificando variável alvo
        self.logger.info("\n5️⃣ Verificando variável alvo...")
        if 'classificacao_acidente' in df_limpo.columns:
            valores_unicos = df_limpo['classificacao_acidente'].unique()
            self.logger.info(f"   Valores encontrados: {len(valores_unicos)}")
            self.logger.info(f"   Amostra: {valores_unicos[:5]}")
            
            # Removendo registros sem classificação válida
            antes = len(df_limpo)
            df_limpo = df_limpo[df_limpo['classificacao_acidente'].notna()]
            df_limpo = df_limpo[df_limpo['classificacao_acidente'] != 'NÃO INFORMADO']
            depois = len(df_limpo)
            if antes != depois:
                self.logger.info(f"   Removidos {antes - depois} registros sem classificação válida")
        
        self.logger.info("\n✅ LIMPEZA CONCLUÍDA")
        self.logger.info(f"   Registros iniciais: {inicial:,}")
        self.logger.info(f"   Registros finais: {len(df_limpo):,}")
        self.logger.info(f"   Registros removidos: {inicial - len(df_limpo):,} ({(inicial - len(df_limpo))/inicial*100:.1f}%)")
        
        return df_limpo
    
    def coletar_dados_completos(self, anos=None, tipos=None, max_retries=3):
        """
        Coleta todos os dados disponíveis da PRF para todos os anos
        """
        self.logger.info("🚀 INICIANDO COLETA COMPLETA DE DADOS PRF - TODOS OS ANOS")
        self.logger.info("="*80)
        self.logger.info(f"📅 Anos a processar: {self.anos}")
        self.logger.info(f"📊 Total de anos: {len(self.anos)}")
        
        # Obtendo links disponíveis
        links_dados = self.obter_links_dados()
        
        if not links_dados:
            self.logger.error("❌ Nenhum link de dados encontrado")
            return None
        
        # Filtrando por anos e tipos se especificados
        if anos:
            links_dados = [link for link in links_dados if link['ano'] in anos]
        if tipos:
            links_dados = [link for link in links_dados if link['tipo'] in tipos]
        
        self.logger.info(f"📅 Processando {len(links_dados)} arquivos...")
        
        dados_coletados = []
        sucessos = 0
        falhas = 0
        
        for i, link_info in enumerate(links_dados, 1):
            ano = link_info['ano']
            tipo = link_info['tipo']
            url = link_info['url']
            descricao = link_info['descricao']
            
            self.logger.info(f"\n📁 [{i}/{len(links_dados)}] Processando {ano} - {tipo}")
            self.logger.info(f"   Descrição: {descricao}")
            self.logger.info(f"   URL: {url}")
            
            # Verificando se já existe
            nome_arquivo = f"acidentes_{ano}_{tipo}"
            arquivo_existente = self.diretorio_saida / f"{nome_arquivo}.csv"
            
            df = None
            
            if arquivo_existente.exists():
                self.logger.info(f"   📁 Arquivo já existe, carregando...")
                try:
                    df = pd.read_csv(arquivo_existente, encoding='utf-8')
                    self.logger.info(f"   ✅ Carregado: {len(df):,} registros")
                except Exception as e:
                    self.logger.error(f"   ❌ Erro ao carregar: {e}")
                    df = None
            
            # Se não carregou do arquivo existente, tentar baixar
            if df is None:
                for tentativa in range(max_retries):
                    try:
                        self.logger.info(f"   🔄 Tentativa {tentativa + 1}/{max_retries}")
                        df = self.baixar_arquivo_csv(url, nome_arquivo)
                        if df is not None and len(df) > 0:
                            break
                    except Exception as e:
                        self.logger.warning(f"   ⚠️ Tentativa {tentativa + 1} falhou: {e}")
                        if tentativa < max_retries - 1:
                            time.sleep(5)  # Pausa antes da próxima tentativa
            
            if df is not None and len(df) > 0:
                # Explorando estrutura
                self.explorar_estrutura_dados(df, ano, tipo)
                
                # Limpando dados
                df_limpo = self.limpar_dados_prf(df, ano, tipo)
                
                # Salvando versão limpa
                arquivo_limpo = self.diretorio_saida / f"{nome_arquivo}_limpo.csv"
                df_limpo.to_csv(arquivo_limpo, index=False, encoding='utf-8')
                self.logger.info(f"   💾 Versão limpa salva: {arquivo_limpo}")
                
                dados_coletados.append(df_limpo)
                sucessos += 1
                
                # Pausa entre downloads para não sobrecarregar o servidor
                time.sleep(1)
            else:
                self.logger.warning(f"   ⚠️ Falha ao processar {ano} - {tipo}")
                falhas += 1
        
        # Relatório de coleta
        self.logger.info(f"\n📊 RELATÓRIO DE COLETA:")
        self.logger.info(f"   ✅ Sucessos: {sucessos}")
        self.logger.info(f"   ❌ Falhas: {falhas}")
        self.logger.info(f"   📈 Taxa de sucesso: {sucessos/(sucessos+falhas)*100:.1f}%")
        
        # Combinando todos os dados
        if dados_coletados:
            self.logger.info("\n🔗 COMBINANDO TODOS OS DADOS...")
            dados_completos = pd.concat(dados_coletados, ignore_index=True)
            
            # Estatísticas finais
            anos_coletados = [d['ano'] for d in dados_coletados if d['ano']]
            self.logger.info(f"📊 ESTATÍSTICAS FINAIS:")
            self.logger.info(f"   Total de registros: {len(dados_completos):,}")
            self.logger.info(f"   Colunas: {len(dados_completos.columns)}")
            if anos_coletados:
                self.logger.info(f"   Período: {min(anos_coletados)} a {max(anos_coletados)}")
            self.logger.info(f"   Arquivos processados: {len(dados_coletados)}")
            
            # Salvando arquivo combinado
            arquivo_combinado = self.diretorio_saida / "acidentes_prf_todos_anos_combinados.csv"
            dados_completos.to_csv(arquivo_combinado, index=False, encoding='utf-8')
            self.logger.info(f"   💾 Arquivo combinado salvo: {arquivo_combinado}")
            
            # Estatísticas por gravidade
            if 'classificacao_acidente' in dados_completos.columns:
                self.logger.info(f"\n📈 DISTRIBUIÇÃO POR GRAVIDADE:")
                distribuicao = dados_completos['classificacao_acidente'].value_counts()
                for gravidade, count in distribuicao.head(10).items():
                    pct = count / len(dados_completos) * 100
                    self.logger.info(f"   {gravidade}: {count:,} ({pct:.1f}%)")
            
            # Estatísticas por ano
            if 'data_inversa' in dados_completos.columns:
                try:
                    dados_completos['ano'] = pd.to_datetime(dados_completos['data_inversa']).dt.year
                    self.logger.info(f"\n📅 DISTRIBUIÇÃO POR ANO:")
                    distribuicao_ano = dados_completos['ano'].value_counts().sort_index()
                    for ano, count in distribuicao_ano.items():
                        self.logger.info(f"   {ano}: {count:,} registros")
                except:
                    pass
            
            return dados_completos
        else:
            self.logger.error("❌ Nenhum dado foi coletado com sucesso")
            return None

def main():
    """
    Função principal para executar o scraping de todos os anos
    """
    print("SISTEMA DE SCRAPING PRF - TODOS OS ANOS")
    print("="*80)
    print("Iniciando coleta de dados de TODOS os anos da PRF...")
    print("Fonte: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf")
    print("Anos: 2007-2025 (19 anos de dados)")
    print("ATENCAO: Esta operacao pode demorar varias horas devido ao volume de dados")
    
    # Perguntando se o usuário quer continuar
    resposta = input("\nDeseja continuar com a coleta completa? (s/N): ").lower().strip()
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("Operacao cancelada pelo usuario")
        return
    
    # Criando scraper para todos os anos
    scraper = PRFScraper2025()
    
    print(f"\nIniciando coleta de {len(scraper.anos)} anos de dados...")
    print(f"Anos: {min(scraper.anos)} a {max(scraper.anos)}")
    
    # Executando coleta
    inicio_coleta = time.time()
    dados = scraper.coletar_dados_completos()
    tempo_total = time.time() - inicio_coleta
    
    if dados is not None:
        print("\nCOLETA CONCLUIDA COM SUCESSO!")
        print("="*80)
        print(f"Total de registros coletados: {len(dados):,}")
        print(f"Tempo total: {tempo_total/60:.1f} minutos")
        print(f"Dados salvos em: data/raw/")
        print(f"Arquivo principal: acidentes_prf_todos_anos_combinados.csv")
        
        # Estatísticas adicionais
        if 'data_inversa' in dados.columns:
            try:
                dados['ano'] = pd.to_datetime(dados['data_inversa']).dt.year
                anos_disponiveis = sorted(dados['ano'].unique())
                print(f"Anos com dados: {len(anos_disponiveis)} anos")
                print(f"   Periodo: {min(anos_disponiveis)} a {max(anos_disponiveis)}")
            except:
                pass
        
        print("\nProximo passo: Treinar o modelo com dados reais")
        print("   python treinar_modelo_real.py")
        print("\nDica: O treinamento com este volume de dados pode demorar mais tempo")
    else:
        print("\nERRO NA COLETA DE DADOS")
        print("   Verifique sua conexao com a internet")
        print("   Verifique se o site da PRF esta acessivel")
        print("   Tente executar novamente mais tarde")

if __name__ == "__main__":
    main()
