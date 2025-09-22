#!/usr/bin/env python3
"""
CACHE MANAGER - Sistema PRF
===========================

Sistema de cache inteligente para otimizar chamadas de API externas.
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, Callable
from functools import wraps, lru_cache
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Gerencia cache de dados externos"""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        Inicializa o cache manager
        
        Args:
            default_ttl: TTL padrão em segundos (1 hora)
            max_size: Tamanho máximo do cache
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Gera chave única para o cache"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Verifica se entrada do cache está expirada"""
        if 'expires_at' not in cache_entry:
            return True
        
        return datetime.now() > cache_entry['expires_at']
    
    def _cleanup_expired(self):
        """Remove entradas expiradas do cache"""
        expired_keys = []
        for key, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            self.stats['evictions'] += 1
    
    def _evict_oldest(self):
        """Remove entrada mais antiga quando cache está cheio"""
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].get('created_at', datetime.min))
            del self.cache[oldest_key]
            self.stats['evictions'] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache"""
        self.stats['total_requests'] += 1
        
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[key]
        
        if self._is_expired(entry):
            del self.cache[key]
            self.stats['misses'] += 1
            self.stats['evictions'] += 1
            return None
        
        self.stats['hits'] += 1
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Armazena valor no cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        # Limpar entradas expiradas
        self._cleanup_expired()
        
        # Evict se necessário
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl)
        }
    
    def delete(self, key: str) -> bool:
        """Remove entrada do cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """Limpa todo o cache"""
        self.cache.clear()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        hit_rate = 0
        if self.stats['total_requests'] > 0:
            hit_rate = self.stats['hits'] / self.stats['total_requests']
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': hit_rate,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'total_requests': self.stats['total_requests']
        }

# Instância global do cache
cache_manager = CacheManager(default_ttl=3600, max_size=1000)

def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """
    Decorator para cache de funções
    
    Args:
        ttl: TTL em segundos
        key_func: Função para gerar chave customizada
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave do cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(func.__name__, *args, **kwargs)
            
            # Tentar recuperar do cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Executar função e cachear resultado
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            
            # Cachear apenas se resultado não for None
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# ============================================================================
# CACHE ESPECÍFICO PARA APIS EXTERNAS
# ============================================================================

@cached(ttl=1800)  # 30 minutos
def cached_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Cache para dados de clima"""
    # Esta função será implementada em utils.py
    pass

@cached(ttl=86400)  # 24 horas
def cached_location(br: int, km: int) -> Dict[str, Any]:
    """Cache para dados de localização"""
    # Esta função será implementada em utils.py
    pass

@cached(ttl=3600)  # 1 hora
def cached_traffic(br: int, km: int, hour: int) -> Dict[str, Any]:
    """Cache para dados de tráfego"""
    # Esta função será implementada em utils.py
    pass

# ============================================================================
# SISTEMA DE FALLBACK
# ============================================================================

class FallbackManager:
    """Gerencia fallbacks quando APIs externas falham"""
    
    def __init__(self):
        self.fallback_data = {
            'weather': self._load_weather_fallbacks(),
            'traffic': self._load_traffic_fallbacks(),
            'location': self._load_location_fallbacks()
        }
    
    def _load_weather_fallbacks(self) -> Dict[str, Any]:
        """Carrega dados de clima de fallback"""
        return {
            'default': {
                'temperatura_atual': 25,
                'condicao_chuva': False,
                'condicao_neblina': False,
                'umidade': 60,
                'visibilidade': 10000,
                'clima_geral': 'bom'
            },
            'regions': {
                'Norte': {'temperatura_atual': 28, 'umidade': 80, 'clima_geral': 'quente'},
                'Nordeste': {'temperatura_atual': 30, 'umidade': 70, 'clima_geral': 'seco'},
                'Sudeste': {'temperatura_atual': 25, 'umidade': 60, 'clima_geral': 'bom'},
                'Sul': {'temperatura_atual': 20, 'umidade': 75, 'clima_geral': 'frio'},
                'Centro-Oeste': {'temperatura_atual': 27, 'umidade': 65, 'clima_geral': 'seco'}
            }
        }
    
    def _load_traffic_fallbacks(self) -> Dict[str, Any]:
        """Carrega dados de tráfego de fallback"""
        return {
            'patterns': {
                'rush_hour': {'fluxo': 'CONGESTIONADO', 'tempo_viagem': 60, 'incidentes': 5},
                'normal': {'fluxo': 'MODERADO', 'tempo_viagem': 30, 'incidentes': 2},
                'night': {'fluxo': 'FLUIDO', 'tempo_viagem': 20, 'incidentes': 1},
                'weekend': {'fluxo': 'MODERADO', 'tempo_viagem': 35, 'incidentes': 3}
            }
        }
    
    def _load_location_fallbacks(self) -> Dict[str, Any]:
        """Carrega dados de localização de fallback"""
        return {
            'default': {
                'uf': 'SP',
                'regiao': 'Sudeste',
                'municipio': 'São Paulo',
                'limite_velocidade': 80
            }
        }
    
    def get_weather_fallback(self, region: str = None) -> Dict[str, Any]:
        """Obtém dados de clima de fallback"""
        if region and region in self.fallback_data['weather']['regions']:
            return {**self.fallback_data['weather']['default'], 
                   **self.fallback_data['weather']['regions'][region]}
        return self.fallback_data['weather']['default'].copy()
    
    def get_traffic_fallback(self, hour: int, is_weekend: bool = False) -> Dict[str, Any]:
        """Obtém dados de tráfego de fallback"""
        if is_weekend:
            pattern = 'weekend'
        elif 7 <= hour <= 9 or 17 <= hour <= 19:
            pattern = 'rush_hour'
        elif 22 <= hour or hour <= 5:
            pattern = 'night'
        else:
            pattern = 'normal'
        
        return self.fallback_data['traffic']['patterns'][pattern].copy()
    
    def get_location_fallback(self, br: int) -> Dict[str, Any]:
        """Obtém dados de localização de fallback"""
        # Tentar usar dados da BR específica se disponível
        from config import BRS_FALLBACK
        if br in BRS_FALLBACK:
            return BRS_FALLBACK[br].copy()
        
        return self.fallback_data['location']['default'].copy()

# Instância global do fallback manager
fallback_manager = FallbackManager()

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def with_fallback(primary_func: Callable, fallback_func: Callable, *args, **kwargs):
    """
    Executa função primária com fallback em caso de erro
    
    Args:
        primary_func: Função primária
        fallback_func: Função de fallback
        *args, **kwargs: Argumentos para as funções
    """
    try:
        result = primary_func(*args, **kwargs)
        if result is not None:
            return result
    except Exception as e:
        logger.warning(f"Primary function failed: {e}")
    
    try:
        logger.info("Using fallback function")
        return fallback_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Fallback function also failed: {e}")
        return None

def get_cache_stats() -> Dict[str, Any]:
    """Retorna estatísticas do cache"""
    return cache_manager.get_stats()

def clear_cache():
    """Limpa todo o cache"""
    cache_manager.clear()
    logger.info("Cache cleared")

if __name__ == "__main__":
    # Teste do cache manager
    import random
    
    # Testar cache
    @cached(ttl=60)
    def expensive_function(x: int) -> int:
        time.sleep(0.1)  # Simular operação cara
        return x * x
    
    # Primeira chamada (cache miss)
    start = time.time()
    result1 = expensive_function(5)
    time1 = time.time() - start
    
    # Segunda chamada (cache hit)
    start = time.time()
    result2 = expensive_function(5)
    time2 = time.time() - start
    
    print(f"Resultado 1: {result1}, Tempo: {time1:.3f}s")
    print(f"Resultado 2: {result2}, Tempo: {time2:.3f}s")
    print(f"Estatísticas: {get_cache_stats()}")
    
    # Testar fallback
    def primary_api():
        raise Exception("API falhou")
    
    def fallback_api():
        return {"status": "fallback"}
    
    result = with_fallback(primary_api, fallback_api)
    print(f"Fallback result: {result}")
