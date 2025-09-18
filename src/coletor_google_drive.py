# src/coletor_google_drive.py

import requests
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import time
import re

class ColetorDadosPRFGoogleDrive:
    """
    Coletor de dados da PRF via Google Drive
    """
    
    def __init__(self, anos=None, diretorio_saida="data/raw"):
        """
        Inicializa o coletor
        
        Parâmetros:
        -----------
        anos : list
            Lista de anos para baixar (default: 2022-2025)
        diretorio_saida : str
            Diretório onde salvar os dados CSV (backup)
        """
        self.anos = anos if anos else [2022, 2023, 2024, 2025]
        self.diretorio_saida = Path(diretorio_saida)
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # URLs do Google Drive para cada ano e tipo
        self.urls_google_drive = {
            2025: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1-G3MdmHBt6CprDwcW99xxC4BZ2DU5ryR',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1-Gp9S-ALO0D1nT8S_OKoC8xlW7BY8F82',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1-PJGRbfSe7PVjU37A3wTCls_NRXyVGRD'
            },
            2024: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=14lB0vqMFkaZj8HZ44b0njYgxs9nAN8KO',
                'pessoa': 'https://drive.google.com/uc?export=download&id=14lVfqdoE2gxDliaKZu7K9Mx6847maPtl',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=14qBOhrE1gioVtuXgxkCJ9kCA8YtUGXKA'
            },
            2023: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1-WO3SfNrwwZ5_l7fRTiwBKRw7mi1-HUq',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1-Yk6TV00CH3PixTkKmkoUJQsNiUc5xLm',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1-caam_dahYOf2eorq4mez04Om6DD5d_3'
            },
            2022: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1PRQjuV5gOn_nn6UNvaJyVURDIfbSAK4-',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1sd8YIqIHapYaxQeaa-6yeWMdVLTl6hgD',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1wskEgRC3ame7rncSDQ7qWhKsoKw1lohY'
            },
            2021: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=12xH8LX9aN2gObR766YN3cMcuycwyCJDz',
                'pessoa': 'https://drive.google.com/uc?export=download&id=15W_l07-6taOh8Ycn8uk2Er9PnSj0vq3f',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1Gk3U6cMOZIevsDZHLi6J503xoCRS_lnI'
            },
            2020: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1esu6IiH5TVTxFoedv6DBGDd01Gvi8785',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1iQvs2D9a2XO9vIukrjEIIhtjzkNkgD7Z',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1yQtVOsAlupPHQVVTmbJo0NR3XMzgHANO'
            },
            2019: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1pN3fn2wY34GH6cY-gKfbxRJJBFE0lb_l',
                'pessoa': 'https://drive.google.com/uc?export=download&id=14r_9zudjjndgcnjRddzD5lvn9MX5VvZZ',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1DAJYKVfkTcPhQodSmHp9rsG1Q8XJW-m3'
            },
            2018: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1cM4IgGMIiR-u4gBIH5IEe3DcvBvUzedi',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1Ja1dN8R_-Dw7sjQVo63UQHicO3jfyzIS',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1J-012nSnIafOASNFvIYY_vDKKpM51w5_'
            },
            2017: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1HPLWt5f_l4RIX3tKjI4tUXyZOev52W0N',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1mw2CerP_ZEZwREy4WYM_Kxd4rjUHQjbk',
                'pessoa_completo': 'https://drive.google.com/uc?export=download&id=1Kv5mNgZvxtl0xwqsmDrxcaLY2KELxR-3'
            },
            2016: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=16qooQl_ySoW61CrtsBbreBVNPYlEkoYm',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1zaBGNLk50krRVOxZmB-kfJl6zSOTdmMP'
            },
            2015: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1DyqR5FFcwGsamSag-fGm13feQt0Y-3Da',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1oisqFB_DD3jAChYxBmiyQVR9WrGOwvQt'
            },
            2014: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1FpF5wTBsRDkEhLm3z2g8XDiXr9SO9Uk8',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1qmCExfnS3nTYIZhDdJblJnn0jlTLWR3K'
            },
            2013: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1p_7lw9RzkINfscYAZSmc-Z9Ci4ZPJyEr',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1-zd3x9aTHD5cQH7SWGMDOQ-4-DuxVV1T'
            },
            2012: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=18Yz2prqKSLthrMmW-73vrOiDmKTCL6xE',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1FYqtz2_QMvk0eOMhs9TOQHrmF4uOvv_W'
            },
            2011: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1HHhgLF-kSR6Gde2qOaTXL3T5ieD33hpG',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1XTcOujBbP_8AEYYrOfjxGxzqHcQYLNy2'
            },
            2010: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1_yU6FRh8M7USjiChQwyF20NtY48GTmEX',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1Zg9SdeQa72Gu49ZhJosBuM7TkJcEYiaI'
            },
            2009: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1qkVatg0pC_zosuBs0NCSgEXDJvBbnTYC',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1gysMdwpeT3h4CUOGDkQMvFJzPp1Fn-bg'
            },
            2008: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1_OSeHlyKJw8cIhMS_JzSg1RlYX8k6vSG',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1gabSVTay5faBo4r9VNksgxhKXuuxu71U'
            },
            2007: {
                'ocorrencia': 'https://drive.google.com/uc?export=download&id=1EFpZF5F6cB0DOHd2Uxnj7X948WE69a8e',
                'pessoa': 'https://drive.google.com/uc?export=download&id=1v2tz5wJYFlPBb-8ZIf-pchbSO-JT4YZG'
            }
        }
    
    def baixar_arquivo_google_drive(self, url, nome_arquivo):
        """
        Baixa arquivo do Google Drive
        """
        try:
            self.logger.info(f"📥 Baixando {nome_arquivo}...")
            
            # Headers para simular navegador
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Fazer requisição
            response = requests.get(url, headers=headers, timeout=60)
            
            if response.status_code == 200:
                # Salvar arquivo
                caminho_arquivo = self.diretorio_saida / nome_arquivo
                with open(caminho_arquivo, 'wb') as f:
                    f.write(response.content)
                
                self.logger.info(f"✅ {nome_arquivo} baixado com sucesso")
                return caminho_arquivo
            else:
                self.logger.error(f"❌ Erro ao baixar {nome_arquivo}: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao baixar {nome_arquivo}: {e}")
            return None
    
    def validar_dados_csv(self, caminho_arquivo):
        """
        Valida dados do CSV baixado
        """
        try:
            self.logger.info(f"🔍 Validando {caminho_arquivo.name}...")
            
            # Ler CSV
            df = pd.read_csv(caminho_arquivo, encoding='utf-8', low_memory=False)
            
            # Validações básicas
            validacoes = {
                'total_registros': len(df),
                'colunas': list(df.columns),
                'tem_data_inversa': 'data_inversa' in df.columns,
                'tem_gravidade': 'gravidade' in df.columns or 'classificacao_acidente' in df.columns,
                'tem_uf': 'uf' in df.columns,
                'tem_br': 'br' in df.columns
            }
            
            # Verificar se há dados
            if validacoes['total_registros'] == 0:
                self.logger.warning(f"⚠️ {caminho_arquivo.name} está vazio")
                return False
            
            # Verificar colunas essenciais
            colunas_essenciais = ['data_inversa', 'uf', 'br']
            colunas_faltando = [col for col in colunas_essenciais if col not in df.columns]
            
            if colunas_faltando:
                self.logger.warning(f"⚠️ {caminho_arquivo.name} não tem colunas: {colunas_faltando}")
            
            # Verificar datas
            if 'data_inversa' in df.columns:
                # Converter para datetime
                df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')
                
                # Verificar datas futuras
                data_atual = datetime.now()
                datas_futuras = df[df['data_inversa'] > data_atual]
                
                if len(datas_futuras) > 0:
                    self.logger.warning(f"⚠️ {caminho_arquivo.name} tem {len(datas_futuras)} registros com datas futuras")
                
                # Verificar datas muito antigas
                data_limite = datetime(2000, 1, 1)
                datas_antigas = df[df['data_inversa'] < data_limite]
                
                if len(datas_antigas) > 0:
                    self.logger.warning(f"⚠️ {caminho_arquivo.name} tem {len(datas_antigas)} registros com datas muito antigas")
            
            self.logger.info(f"✅ {caminho_arquivo.name} validado: {validacoes['total_registros']} registros")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao validar {caminho_arquivo.name}: {e}")
            return False
    
    def coletar_ano(self, ano):
        """
        Coleta dados de um ano específico
        """
        self.logger.info(f"📅 Coletando dados de {ano}...")
        
        dados_ano = {}
        
        # Verificar se o ano tem dados disponíveis
        if ano not in self.urls_google_drive:
            self.logger.warning(f"⚠️ Ano {ano} não disponível")
            return None
        
        # Baixar cada tipo de arquivo
        for tipo, url in self.urls_google_drive[ano].items():
            nome_arquivo = f"acidentes{ano}_{tipo}.csv"
            
            # Baixar arquivo
            caminho_arquivo = self.baixar_arquivo_google_drive(url, nome_arquivo)
            
            if caminho_arquivo:
                # Validar dados
                if self.validar_dados_csv(caminho_arquivo):
                    dados_ano[tipo] = caminho_arquivo
                else:
                    self.logger.warning(f"⚠️ Dados de {ano}_{tipo} inválidos")
            else:
                self.logger.error(f"❌ Falha ao baixar {ano}_{tipo}")
        
        return dados_ano if dados_ano else None
    
    def coletar_todos_os_anos(self):
        """
        Coleta dados de todos os anos configurados
        """
        self.logger.info("🚀 Iniciando coleta de dados da PRF via Google Drive...")
        
        todos_dados = {}
        
        for ano in self.anos:
            self.logger.info(f"📅 Processando ano {ano}...")
            
            dados_ano = self.coletar_ano(ano)
            
            if dados_ano:
                todos_dados[ano] = dados_ano
                self.logger.info(f"✅ Ano {ano} coletado com sucesso")
            else:
                self.logger.error(f"❌ Falha ao coletar ano {ano}")
            
            # Pausa entre downloads
            time.sleep(2)
        
        self.logger.info(f"🏁 Coleta concluída: {len(todos_dados)} anos coletados")
        return todos_dados

def main():
    """
    Função principal para teste
    """
    logging.basicConfig(level=logging.INFO)
    
    print("🚨 SISTEMA DE COLETA DE DADOS PRF - GOOGLE DRIVE")
    print("="*80)
    print("📥 Iniciando coleta de dados via Google Drive...")
    
    # Criando coletor
    coletor = ColetorDadosPRFGoogleDrive(anos=[2025, 2024, 2023])  # Testar com anos recentes
    
    # Executando coleta
    dados = coletor.coletar_todos_os_anos()
    
    if dados:
        print(f"✅ Coleta concluída: {len(dados)} anos coletados")
        for ano, tipos in dados.items():
            print(f"  📅 {ano}: {len(tipos)} arquivos")
    else:
        print("❌ Falha na coleta de dados")

if __name__ == "__main__":
    main()
