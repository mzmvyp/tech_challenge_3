#!/usr/bin/env python3
"""
TESTES PARA SISTEMA ML REAL - PRF
==================================

Testes para validar funcionamento do sistema ML real.
"""

import pytest
import sys
import os
from pathlib import Path
import numpy as np
from datetime import datetime

# Adicionar o diretório raiz ao Python path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from utils import (
    carregar_modelo_gravidade, carregar_scaler, carregar_feature_names,
    preparar_features_para_ml, prever_severidade_ml_real,
    buscar_localizacao_real, buscar_clima_real, verificar_feriado
)

class TestCarregamentoModelos:
    """Testes para carregamento de modelos ML"""
    
    def test_modelo_gravidade_carregado(self):
        """Testa se modelo de gravidade está carregado"""
        modelo = carregar_modelo_gravidade()
        assert modelo is not None, "Modelo de gravidade não foi carregado"
        assert hasattr(modelo, 'predict'), "Modelo não tem método predict"
        assert hasattr(modelo, 'predict_proba'), "Modelo não tem método predict_proba"
    
    def test_scaler_carregado(self):
        """Testa se scaler está carregado"""
        scaler = carregar_scaler()
        # Scaler pode ser None, mas se existir deve ter método transform
        if scaler is not None:
            assert hasattr(scaler, 'transform'), "Scaler não tem método transform"
    
    def test_feature_names_carregadas(self):
        """Testa se feature names estão carregadas"""
        features = carregar_feature_names()
        assert len(features) > 0, "Feature names não foram carregadas"
        assert isinstance(features, list), "Feature names deve ser uma lista"
        assert all(isinstance(f, str) for f in features), "Todas as features devem ser strings"

class TestPreparacaoDados:
    """Testes para preparação de dados"""
    
    @pytest.fixture
    def dados_acidente_teste(self):
        """Dados de teste para acidente"""
        return {
            'local': {
                'br': 116,
                'km': 50,
                'uf': 'PR',
                'municipio': 'Curitiba'
            },
            'data_hora': '2024-01-15 14:30:00',
            'primeiro_relato': 'Acidente com múltiplos veículos, possível vítima presa',
            'condicoes': {
                'temperatura': 25,
                'chuva': False,
                'neblina': False,
                'clima_geral': 'bom'
            },
            'veiculos': [{
                'tipo': 'carro',
                'pessoas': 2,
                'idade_condutor': 35,
                'sexo_condutor': 'M'
            }],
            'infraestrutura': {
                'pista_simples': False,
                'tem_acostamento': True
            },
            'contexto': {
                'eh_feriado': False,
                'eh_fim_semana': False
            }
        }
    
    def test_preparar_features_para_ml(self, dados_acidente_teste):
        """Testa preparação de features para ML"""
        features = carregar_feature_names()
        
        X = preparar_features_para_ml(dados_acidente_teste, features)
        
        assert X is not None, "Features não foram preparadas"
        assert X.shape[1] == len(features), f"Features têm shape incorreto: {X.shape[1]} vs {len(features)}"
        assert not np.isnan(X).any(), "Features contêm valores NaN"
        assert not np.isinf(X).any(), "Features contêm valores infinitos"

class TestPredicaoML:
    """Testes para predição ML real"""
    
    @pytest.fixture
    def dados_acidente_teste(self):
        """Dados de teste para acidente"""
        return {
            'local': {
                'br': 116,
                'km': 50,
                'uf': 'PR',
                'municipio': 'Curitiba'
            },
            'data_hora': '2024-01-15 14:30:00',
            'primeiro_relato': 'Acidente com múltiplos veículos, possível vítima presa',
            'condicoes': {
                'temperatura': 25,
                'chuva': False,
                'neblina': False,
                'clima_geral': 'bom'
            },
            'veiculos': [{
                'tipo': 'carro',
                'pessoas': 2,
                'idade_condutor': 35,
                'sexo_condutor': 'M'
            }],
            'infraestrutura': {
                'pista_simples': False,
                'tem_acostamento': True
            },
            'contexto': {
                'eh_feriado': False,
                'eh_fim_semana': False
            }
        }
    
    def test_predicao_ml_real(self, dados_acidente_teste):
        """Testa predição ML real"""
        modelo = carregar_modelo_gravidade()
        scaler = carregar_scaler()
        features = carregar_feature_names()
        
        if modelo is None:
            pytest.skip("Modelo não carregado")
        
        resultado = prever_severidade_ml_real(dados_acidente_teste, modelo, scaler, features)
        
        # Verificar estrutura da resposta
        assert 'severidade_predita' in resultado, "Resultado não contém severidade_predita"
        assert 'modelo_usado' in resultado, "Resultado não contém modelo_usado"
        assert 'features_usadas' in resultado, "Resultado não contém features_usadas"
        assert 'acuracia_modelo' in resultado, "Resultado não contém acuracia_modelo"
        
        # Verificar severidade predita
        severidade = resultado['severidade_predita']
        assert 'nivel' in severidade, "Severidade não contém nível"
        assert 'score' in severidade, "Severidade não contém score"
        assert 'confianca' in severidade, "Severidade não contém confiança"
        assert 'probabilidades' in severidade, "Severidade não contém probabilidades"
        
        # Verificar valores válidos
        assert severidade['nivel'] in ['SEM FERIDOS', 'FERIDOS LEVES', 'FERIDOS GRAVES', 'MORTOS'], \
            f"Nível inválido: {severidade['nivel']}"
        assert 0 <= severidade['score'] <= 3, f"Score inválido: {severidade['score']}"
        assert 0 <= severidade['confianca'] <= 100, f"Confiança inválida: {severidade['confianca']}"
        
        # Verificar probabilidades
        probs = severidade['probabilidades']
        assert 'sem_feridos' in probs, "Probabilidades não contém sem_feridos"
        assert 'feridos_leves' in probs, "Probabilidades não contém feridos_leves"
        assert 'feridos_graves' in probs, "Probabilidades não contém feridos_graves"
        assert 'mortos' in probs, "Probabilidades não contém mortos"
        
        # Verificar que probabilidades somam aproximadamente 1
        soma_probs = sum(probs.values())
        assert abs(soma_probs - 1.0) < 0.01, f"Probabilidades não somam 1: {soma_probs}"
        
        # Verificar que todas as probabilidades estão entre 0 e 1
        for prob in probs.values():
            assert 0 <= prob <= 1, f"Probabilidade inválida: {prob}"

class TestAPIsExternas:
    """Testes para APIs externas"""
    
    def test_buscar_localizacao_real(self):
        """Testa busca de localização real"""
        dados = buscar_localizacao_real(116, 50)
        
        assert dados is not None, "Localização não encontrada"
        assert 'uf' in dados, "Localização não contém UF"
        assert 'municipio' in dados, "Localização não contém município"
        assert 'regiao' in dados, "Localização não contém região"
        assert 'limite_velocidade' in dados, "Localização não contém limite de velocidade"
    
    def test_buscar_clima_real(self):
        """Testa busca de clima real"""
        dados = buscar_clima_real('Curitiba', 'PR')
        
        assert dados is not None, "Clima não encontrado"
        assert 'temperatura_atual' in dados, "Clima não contém temperatura"
        assert 'condicao_chuva' in dados, "Clima não contém condição de chuva"
        assert 'condicao_neblina' in dados, "Clima não contém condição de neblina"
        assert 'umidade' in dados, "Clima não contém umidade"
        assert 'visibilidade' in dados, "Clima não contém visibilidade"
        
        # Verificar tipos e valores válidos
        assert isinstance(dados['temperatura_atual'], (int, float)), "Temperatura deve ser numérica"
        assert isinstance(dados['condicao_chuva'], bool), "Condição de chuva deve ser booleana"
        assert isinstance(dados['condicao_neblina'], bool), "Condição de neblina deve ser booleana"
        assert isinstance(dados['umidade'], (int, float)), "Umidade deve ser numérica"
        assert isinstance(dados['visibilidade'], (int, float)), "Visibilidade deve ser numérica"
    
    def test_verificar_feriado(self):
        """Testa verificação de feriado"""
        # Testar data que é feriado
        data_feriado = datetime(2024, 1, 1).date()  # Ano Novo
        assert verificar_feriado(data_feriado) == True, "Ano Novo deve ser feriado"
        
        # Testar data que não é feriado
        data_normal = datetime(2024, 1, 15).date()  # Dia normal
        assert verificar_feriado(data_normal) == False, "Dia normal não deve ser feriado"

class TestIntegracao:
    """Testes de integração"""
    
    def test_fluxo_completo_predicao(self):
        """Testa fluxo completo de predição"""
        # Dados de entrada
        dados_acidente = {
            'local': {
                'br': 116,
                'km': 50,
                'uf': 'PR',
                'municipio': 'Curitiba'
            },
            'data_hora': '2024-01-15 14:30:00',
            'primeiro_relato': 'Acidente com múltiplos veículos, possível vítima presa',
            'condicoes': {
                'temperatura': 25,
                'chuva': False,
                'neblina': False,
                'clima_geral': 'bom'
            },
            'veiculos': [{
                'tipo': 'carro',
                'pessoas': 2,
                'idade_condutor': 35,
                'sexo_condutor': 'M'
            }],
            'infraestrutura': {
                'pista_simples': False,
                'tem_acostamento': True
            },
            'contexto': {
                'eh_feriado': False,
                'eh_fim_semana': False
            }
        }
        
        # Carregar componentes
        modelo = carregar_modelo_gravidade()
        scaler = carregar_scaler()
        features = carregar_feature_names()
        
        if modelo is None:
            pytest.skip("Modelo não carregado")
        
        # Executar predição
        resultado = prever_severidade_ml_real(dados_acidente, modelo, scaler, features)
        
        # Verificar resultado
        assert resultado is not None, "Predição falhou"
        assert 'severidade_predita' in resultado, "Resultado não contém severidade"
        assert 'recursos_sugeridos' in resultado, "Resultado não contém recursos"
        
        # Verificar que recursos foram calculados corretamente
        recursos = resultado['recursos_sugeridos']
        assert 'viaturas_prf' in recursos, "Recursos não contém viaturas PRF"
        assert 'ambulancia' in recursos, "Recursos não contém ambulância"
        assert 'helicoptero' in recursos, "Recursos não contém helicóptero"
        assert 'perito' in recursos, "Recursos não contém perito"
        assert 'prioridade' in recursos, "Recursos não contém prioridade"

def test_performance_predicao():
    """Testa performance da predição"""
    import time
    
    modelo = carregar_modelo_gravidade()
    scaler = carregar_scaler()
    features = carregar_feature_names()
    
    if modelo is None:
        pytest.skip("Modelo não carregado")
    
    dados_acidente = {
        'local': {'br': 116, 'km': 50, 'uf': 'PR', 'municipio': 'Curitiba'},
        'data_hora': '2024-01-15 14:30:00',
        'primeiro_relato': 'Acidente com múltiplos veículos',
        'condicoes': {'temperatura': 25, 'chuva': False, 'neblina': False, 'clima_geral': 'bom'},
        'veiculos': [{'tipo': 'carro', 'pessoas': 2, 'idade_condutor': 35, 'sexo_condutor': 'M'}],
        'infraestrutura': {'pista_simples': False, 'tem_acostamento': True},
        'contexto': {'eh_feriado': False, 'eh_fim_semana': False}
    }
    
    # Medir tempo de predição
    inicio = time.time()
    resultado = prever_severidade_ml_real(dados_acidente, modelo, scaler, features)
    tempo = time.time() - inicio
    
    assert resultado is not None, "Predição falhou"
    assert tempo < 5.0, f"Predição muito lenta: {tempo:.2f}s"
    print(f"Tempo de predição: {tempo:.3f}s")

if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])
