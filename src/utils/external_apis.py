"""
Integrações com APIs Externas - Sistema de Prevenção de Acidentes PRF

Este módulo implementa integrações com APIs externas para obter dados
em tempo real de clima, tráfego, alertas de rodovias, etc.
"""

import requests
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class IntegracaoAPIsExternas:
    """
    Classe para integração com APIs externas
    """
    
    def __init__(self):
        """Inicializa as integrações"""
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY', '')
        self.google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        self.cache_ttl = int(os.getenv('CACHE_TTL', '3600'))  # 1 hora
        
        # Cache simples em memória
        self._cache = {}
        
        # URLs das APIs
        self.openweather_url = "https://api.openweathermap.org/data/2.5"
        self.google_maps_url = "https://maps.googleapis.com/maps/api"
    
    def obter_previsao_tempo(self, cidade: str, data: str) -> Dict:
        """
        Obtém previsão do tempo para uma cidade e data específica
        
        Args:
            cidade: Nome da cidade
            data: Data no formato YYYY-MM-DD
            
        Returns:
            Dict com dados meteorológicos
        """
        cache_key = f"weather_{cidade}_{data}"
        
        # Verificar cache
        if self._verificar_cache(cache_key):
            return self._cache[cache_key]['data']
        
        try:
            # Obter coordenadas da cidade
            lat, lon = self._obter_coordenadas_cidade(cidade)
            if not lat or not lon:
                return self._dados_clima_padrao()
            
            # Fazer requisição para API do OpenWeatherMap
            if self.openweather_api_key:
                url = f"{self.openweather_url}/forecast"
                params = {
                    'lat': lat,
                    'lon': lon,
                    'appid': self.openweather_api_key,
                    'units': 'metric',
                    'lang': 'pt_br'
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data_weather = response.json()
                dados_clima = self._processar_dados_clima(data_weather, data)
                
            else:
                # Usar dados simulados se não tiver API key
                dados_clima = self._dados_clima_simulados(cidade, data)
            
            # Salvar no cache
            self._salvar_cache(cache_key, dados_clima)
            
            logger.info(f"Previsão do tempo obtida para {cidade}: {dados_clima}")
            return dados_clima
            
        except Exception as e:
            logger.error(f"Erro ao obter previsão do tempo para {cidade}: {e}")
            return self._dados_clima_padrao()
    
    def obter_info_rota(self, origem: str, destino: str, data: str = None) -> Dict:
        """
        Obtém informações detalhadas da rota usando Google Maps
        
        Args:
            origem: Cidade de origem
            destino: Cidade de destino
            data: Data da viagem (opcional)
            
        Returns:
            Dict com informações da rota
        """
        cache_key = f"route_{origem}_{destino}"
        
        # Verificar cache
        if self._verificar_cache(cache_key):
            return self._cache[cache_key]['data']
        
        try:
            if self.google_maps_api_key:
                # Usar Google Maps Directions API
                url = f"{self.google_maps_url}/directions/json"
                params = {
                    'origin': origem,
                    'destination': destino,
                    'key': self.google_maps_api_key,
                    'language': 'pt-BR',
                    'units': 'metric'
                }
                
                # Adicionar data de partida se fornecida
                if data:
                    departure_time = datetime.strptime(data, '%Y-%m-%d')
                    params['departure_time'] = int(departure_time.timestamp())
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data_route = response.json()
                dados_rota = self._processar_dados_rota(data_route)
                
            else:
                # Usar dados simulados se não tiver API key
                dados_rota = self._dados_rota_simulados(origem, destino)
            
            # Salvar no cache
            self._salvar_cache(cache_key, dados_rota)
            
            logger.info(f"Informações de rota obtidas: {origem} -> {destino}")
            return dados_rota
            
        except Exception as e:
            logger.error(f"Erro ao obter informações de rota: {e}")
            return self._dados_rota_padrao(origem, destino)
    
    def obter_alertas_rodovia(self, rodovia: str) -> List[Dict]:
        """
        Obtém alertas em tempo real de uma rodovia
        
        Args:
            rodovia: Código da rodovia (ex: BR-101, SP-160)
            
        Returns:
            Lista de alertas da rodovia
        """
        cache_key = f"alerts_{rodovia}"
        
        # Verificar cache (cache mais curto para alertas)
        if self._verificar_cache(cache_key, ttl=1800):  # 30 minutos
            return self._cache[cache_key]['data']
        
        try:
            # Simular coleta de alertas (em produção, integrar com API da PRF)
            alertas = self._simular_alertas_rodovia(rodovia)
            
            # Salvar no cache
            self._salvar_cache(cache_key, alertas, ttl=1800)
            
            logger.info(f"Alertas obtidos para {rodovia}: {len(alertas)} alertas")
            return alertas
            
        except Exception as e:
            logger.error(f"Erro ao obter alertas da rodovia {rodovia}: {e}")
            return []
    
    def obter_feriados_brasil(self, ano: int = None) -> List[str]:
        """
        Obtém lista de feriados nacionais do Brasil
        
        Args:
            ano: Ano para consultar (padrão: ano atual)
            
        Returns:
            Lista de datas de feriados no formato YYYY-MM-DD
        """
        if not ano:
            ano = datetime.now().year
        
        cache_key = f"holidays_{ano}"
        
        # Verificar cache
        if self._verificar_cache(cache_key, ttl=86400):  # 24 horas
            return self._cache[cache_key]['data']
        
        # Feriados fixos do Brasil
        feriados = [
            f"{ano}-01-01",   # Ano Novo
            f"{ano}-04-21",   # Tiradentes
            f"{ano}-05-01",   # Dia do Trabalhador
            f"{ano}-09-07",   # Independência
            f"{ano}-10-12",   # Nossa Senhora Aparecida
            f"{ano}-11-02",   # Finados
            f"{ano}-11-15",   # Proclamação da República
            f"{ano}-12-25"    # Natal
        ]
        
        # Adicionar feriados móveis (simplificado)
        # Em produção, calcular Páscoa e derivados
        pascoa = self._calcular_pascoa(ano)
        feriados.extend([
            (pascoa - timedelta(days=47)).strftime('%Y-%m-%d'),  # Carnaval
            (pascoa - timedelta(days=2)).strftime('%Y-%m-%d'),   # Sexta-feira Santa
            (pascoa + timedelta(days=60)).strftime('%Y-%m-%d')   # Corpus Christi
        ])
        
        # Salvar no cache
        self._salvar_cache(cache_key, feriados, ttl=86400)
        
        return feriados
    
    def obter_coordenadas_cidade(self, cidade: str) -> Tuple[float, float]:
        """
        Obtém coordenadas geográficas de uma cidade
        
        Args:
            cidade: Nome da cidade
            
        Returns:
            Tupla (latitude, longitude) ou (None, None) se não encontrada
        """
        return self._obter_coordenadas_cidade(cidade)
    
    # Métodos privados
    
    def _verificar_cache(self, key: str, ttl: int = None) -> bool:
        """Verifica se item está no cache e não expirou"""
        if ttl is None:
            ttl = self.cache_ttl
        
        if key not in self._cache:
            return False
        
        timestamp = self._cache[key]['timestamp']
        return (time.time() - timestamp) < ttl
    
    def _salvar_cache(self, key: str, data: any, ttl: int = None) -> None:
        """Salva item no cache"""
        if ttl is None:
            ttl = self.cache_ttl
        
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _obter_coordenadas_cidade(self, cidade: str) -> Tuple[float, float]:
        """Obtém coordenadas de uma cidade"""
        # Mapeamento simplificado de cidades
        coordenadas = {
            'são paulo': (-23.5505, -46.6333),
            'santos': (-23.9608, -46.3331),
            'campinas': (-22.9056, -47.0608),
            'rio de janeiro': (-22.9068, -43.1729),
            'belo horizonte': (-19.9167, -43.9345),
            'curitiba': (-25.4284, -49.2733),
            'porto alegre': (-30.0346, -51.2177),
            'salvador': (-12.9714, -38.5014),
            'brasília': (-15.7801, -47.9292),
            'fortaleza': (-3.7319, -38.5267),
            'recife': (-8.0476, -34.8770),
            'manaus': (-3.1190, -60.0217),
            'goiânia': (-16.6864, -49.2643),
            'belém': (-1.4558, -48.5044)
        }
        
        cidade_lower = cidade.lower().strip()
        return coordenadas.get(cidade_lower, (None, None))
    
    def _processar_dados_clima(self, data_weather: Dict, data: str) -> Dict:
        """Processa dados do OpenWeatherMap"""
        try:
            # Buscar previsão para a data específica
            target_date = datetime.strptime(data, '%Y-%m-%d').date()
            
            for item in data_weather.get('list', []):
                item_date = datetime.fromtimestamp(item['dt']).date()
                if item_date == target_date:
                    weather = item['weather'][0]
                    main = item['main']
                    
                    return {
                        'temperatura': round(main['temp'], 1),
                        'sensacao_termica': round(main['feels_like'], 1),
                        'umidade': main['humidity'],
                        'visibilidade': round(item.get('visibility', 10000) / 1000, 1),  # km
                        'chuva': weather['main'] == 'Rain',
                        'precipitacao': item.get('rain', {}).get('3h', 0),
                        'neblina': weather['main'] == 'Mist' or weather['description'] == 'fog',
                        'vento': round(item.get('wind', {}).get('speed', 0) * 3.6, 1),  # km/h
                        'descricao': weather['description'],
                        'icone': weather['icon']
                    }
            
            # Se não encontrou data específica, usar o primeiro item
            first_item = data_weather['list'][0]
            weather = first_item['weather'][0]
            main = first_item['main']
            
            return {
                'temperatura': round(main['temp'], 1),
                'sensacao_termica': round(main['feels_like'], 1),
                'umidade': main['humidity'],
                'visibilidade': 10.0,
                'chuva': weather['main'] == 'Rain',
                'precipitacao': 0,
                'neblina': False,
                'vento': round(first_item.get('wind', {}).get('speed', 0) * 3.6, 1),
                'descricao': weather['description'],
                'icone': weather['icon']
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar dados de clima: {e}")
            return self._dados_clima_padrao()
    
    def _processar_dados_rota(self, data_route: Dict) -> Dict:
        """Processa dados do Google Maps Directions API"""
        try:
            if not data_route.get('routes'):
                return self._dados_rota_padrao('origem', 'destino')
            
            route = data_route['routes'][0]
            leg = route['legs'][0]
            
            return {
                'distancia_km': round(leg['distance']['value'] / 1000, 1),
                'tempo_estimado': leg['duration']['text'],
                'tempo_segundos': leg['duration']['value'],
                'rota_polyline': route['overview_polyline']['points'],
                'passos': [
                    {
                        'instrucao': step['html_instructions'],
                        'distancia': step['distance']['text'],
                        'tempo': step['duration']['text']
                    }
                    for step in leg['steps']
                ],
                'trafego': self._verificar_trafego(leg),
                'pedagios': self._identificar_pedagios(route)
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar dados de rota: {e}")
            return self._dados_rota_padrao('origem', 'destino')
    
    def _verificar_trafego(self, leg: Dict) -> str:
        """Verifica condições de tráfego"""
        try:
            # Verificar se há dados de tráfego
            if 'duration_in_traffic' in leg:
                tempo_normal = leg['duration']['value']
                tempo_com_trafego = leg['duration_in_traffic']['value']
                
                diferenca = ((tempo_com_trafego - tempo_normal) / tempo_normal) * 100
                
                if diferenca > 50:
                    return "Pesado"
                elif diferenca > 20:
                    return "Moderado"
                else:
                    return "Fluido"
            else:
                return "Normal"
                
        except Exception:
            return "Normal"
    
    def _identificar_pedagios(self, route: Dict) -> List[Dict]:
        """Identifica pedágios na rota"""
        # Implementação simplificada
        # Em produção, usar dados reais de pedágios
        pedagios = []
        
        # Verificar se a rota passa por rodovias com pedágios conhecidos
        summary = route.get('summary', '').upper()
        
        if 'ANCHIETA' in summary or 'SP-150' in summary:
            pedagios.append({
                'nome': 'Pedágio Anchieta',
                'preco': 12.50,
                'localizacao': 'Km 45'
            })
        
        if 'IMIGRANTES' in summary or 'SP-160' in summary:
            pedagios.append({
                'nome': 'Pedágio Imigrantes',
                'preco': 15.20,
                'localizacao': 'Km 38'
            })
        
        return pedagios
    
    def _simular_alertas_rodovia(self, rodovia: str) -> List[Dict]:
        """Simula alertas de rodovia"""
        alertas_base = [
            {
                'tipo': 'acidente',
                'descricao': 'Acidente com vítima',
                'localizacao': 'Km 45',
                'sentido': 'São Paulo',
                'severidade': 'alta',
                'timestamp': datetime.now().isoformat()
            },
            {
                'tipo': 'obras',
                'descricao': 'Obras na pista',
                'localizacao': 'Km 62-65',
                'sentido': 'Ambos',
                'severidade': 'media',
                'timestamp': datetime.now().isoformat()
            },
            {
                'tipo': 'interdicao',
                'descricao': 'Pista interditada',
                'localizacao': 'Km 78',
                'sentido': 'Santos',
                'severidade': 'alta',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Filtrar alertas baseados na rodovia
        alertas_filtrados = []
        for alerta in alertas_base:
            if rodovia.upper() in ['SP-160', 'IMIGRANTES'] and alerta['localizacao']:
                alertas_filtrados.append(alerta)
        
        return alertas_filtrados
    
    def _calcular_pascoa(self, ano: int) -> datetime:
        """Calcula a data da Páscoa para um ano"""
        # Algoritmo de Gauss para calcular Páscoa
        a = ano % 19
        b = ano // 100
        c = ano % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        n = (h + l - 7 * m + 114) // 31
        p = (h + l - 7 * m + 114) % 31
        
        return datetime(ano, n, p + 1)
    
    def _dados_clima_padrao(self) -> Dict:
        """Retorna dados de clima padrão quando não consegue obter dados reais"""
        return {
            'temperatura': 22.0,
            'sensacao_termica': 24.0,
            'umidade': 65,
            'visibilidade': 10.0,
            'chuva': False,
            'precipitacao': 0,
            'neblina': False,
            'vento': 15.0,
            'descricao': 'céu limpo',
            'icone': '01d'
        }
    
    def _dados_clima_simulados(self, cidade: str, data: str) -> Dict:
        """Gera dados de clima simulados"""
        import random
        
        base_temp = 22 + random.randint(-5, 8)
        chuva = random.random() < 0.3
        
        return {
            'temperatura': round(base_temp, 1),
            'sensacao_termica': round(base_temp + random.randint(-2, 3), 1),
            'umidade': random.randint(40, 90),
            'visibilidade': round(10 - (random.random() * 5), 1),
            'chuva': chuva,
            'precipitacao': random.uniform(0, 10) if chuva else 0,
            'neblina': random.random() < 0.1,
            'vento': round(random.uniform(5, 25), 1),
            'descricao': 'parcialmente nublado',
            'icone': '02d'
        }
    
    def _dados_rota_padrao(self, origem: str, destino: str) -> Dict:
        """Retorna dados de rota padrão"""
        return {
            'distancia_km': 50.0,
            'tempo_estimado': '1h 30min',
            'tempo_segundos': 5400,
            'rota_polyline': '',
            'passos': [],
            'trafego': 'Normal',
            'pedagios': []
        }
    
    def _dados_rota_simulados(self, origem: str, destino: str) -> Dict:
        """Gera dados de rota simulados"""
        import random
        
        # Distâncias aproximadas entre cidades
        distancias = {
            ('são paulo', 'santos'): 72,
            ('são paulo', 'campinas'): 100,
            ('são paulo', 'rio de janeiro'): 430,
            ('são paulo', 'belo horizonte'): 585
        }
        
        distancia = distancias.get((origem.lower(), destino.lower()), 100)
        tempo_horas = distancia / 60  # Velocidade média 60 km/h
        
        return {
            'distancia_km': round(distancia + random.uniform(-5, 5), 1),
            'tempo_estimado': f"{int(tempo_horas)}h {int((tempo_horas % 1) * 60)}min",
            'tempo_segundos': int(tempo_horas * 3600),
            'rota_polyline': '',
            'passos': [],
            'trafego': random.choice(['Fluido', 'Normal', 'Moderado']),
            'pedagios': []
        }


# Funções utilitárias para uso direto

def obter_clima(cidade: str, data: str = None) -> Dict:
    """
    Função utilitária para obter previsão do tempo
    
    Args:
        cidade: Nome da cidade
        data: Data no formato YYYY-MM-DD (padrão: hoje)
    
    Returns:
        Dict com dados meteorológicos
    """
    if not data:
        data = datetime.now().strftime('%Y-%m-%d')
    
    api = IntegracaoAPIsExternas()
    return api.obter_previsao_tempo(cidade, data)


def obter_rota(origem: str, destino: str, data: str = None) -> Dict:
    """
    Função utilitária para obter informações de rota
    
    Args:
        origem: Cidade de origem
        destino: Cidade de destino
        data: Data da viagem (opcional)
    
    Returns:
        Dict com informações da rota
    """
    api = IntegracaoAPIsExternas()
    return api.obter_info_rota(origem, destino, data)


def obter_alertas(rodovia: str) -> List[Dict]:
    """
    Função utilitária para obter alertas de rodovia
    
    Args:
        rodovia: Código da rodovia
    
    Returns:
        Lista de alertas
    """
    api = IntegracaoAPIsExternas()
    return api.obter_alertas_rodovia(rodovia)
