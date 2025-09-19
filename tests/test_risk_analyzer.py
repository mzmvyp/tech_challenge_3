"""
Testes para o AnalisadorRiscoViagem
"""

import pytest
import sys
import os

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.risk_analyzer import AnalisadorRiscoViagem, calcular_risco_rapido


class TestAnalisadorRiscoViagem:
    """Testes para a classe AnalisadorRiscoViagem"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.analisador = AnalisadorRiscoViagem()
    
    def test_inicializacao(self):
        """Testa inicialização do analisador"""
        assert self.analisador.fatores_risco == []
        assert self.analisador.pontos_risco == 0
        assert len(self.analisador.config_risco) > 0
    
    def test_analise_viagem_basica(self):
        """Testa análise básica de viagem"""
        dados = {
            'origem': 'São Paulo',
            'destino': 'Santos',
            'data': '2024-01-15',
            'horario': '12:00',
            'rodovia': 'SP-160',
            'distancia_km': 72,
            'tipo_veiculo': 'carro',
            'num_passageiros': 2,
            'urgencia': 1
        }
        
        resultado = self.analisador.analisar_viagem(dados)
        
        assert 'nivel_risco' in resultado
        assert 'probabilidade_acidente' in resultado
        assert 'fatores_risco' in resultado
        assert 'recomendacoes' in resultado
        assert resultado['probabilidade_acidente'] >= 0
        assert resultado['probabilidade_acidente'] <= 100
    
    def test_fator_temporal_madrugada(self):
        """Testa detecção de risco por horário de madrugada"""
        dados = {
            'origem': 'São Paulo',
            'destino': 'Santos',
            'data': '2024-01-15',
            'horario': '02:00',  # Madrugada
            'rodovia': 'SP-160',
            'distancia_km': 72,
            'tipo_veiculo': 'carro',
            'num_passageiros': 1,
            'urgencia': 1
        }
        
        resultado = self.analisador.analisar_viagem(dados)
        
        # Deve ter risco alto por ser madrugada
        assert resultado['probabilidade_acidente'] > 20
        assert any('madrugada' in fator.lower() for fator in resultado['fatores_risco'])
    
    def test_fator_clima_chuva(self):
        """Testa detecção de risco por clima chuvoso"""
        dados = {
            'origem': 'São Paulo',
            'destino': 'Santos',
            'data': '2024-01-15',
            'horario': '12:00',
            'rodovia': 'SP-160',
            'distancia_km': 72,
            'tipo_veiculo': 'carro',
            'num_passageiros': 1,
            'urgencia': 1,
            'clima': {
                'chuva': True,
                'precipitacao': 5.0
            }
        }
        
        resultado = self.analisador.analisar_viagem(dados)
        
        # Deve ter risco aumentado por chuva
        assert resultado['probabilidade_acidente'] > 15
        assert any('chuva' in fator.lower() for fator in resultado['fatores_risco'])
    
    def test_fator_veiculo_moto(self):
        """Testa detecção de risco por tipo de veículo (moto)"""
        dados = {
            'origem': 'São Paulo',
            'destino': 'Santos',
            'data': '2024-01-15',
            'horario': '12:00',
            'rodovia': 'SP-160',
            'distancia_km': 72,
            'tipo_veiculo': 'moto',
            'num_passageiros': 1,
            'urgencia': 1
        }
        
        resultado = self.analisador.analisar_viagem(dados)
        
        # Deve ter risco aumentado por ser moto
        assert resultado['probabilidade_acidente'] > 15
        assert any('motocicleta' in fator.lower() for fator in resultado['fatores_risco'])
    
    def test_fator_distancia_longa(self):
        """Testa detecção de risco por distância longa"""
        dados = {
            'origem': 'São Paulo',
            'destino': 'Rio de Janeiro',
            'data': '2024-01-15',
            'horario': '12:00',
            'rodovia': 'BR-116',
            'distancia_km': 430,  # Distância longa
            'tipo_veiculo': 'carro',
            'num_passageiros': 2,
            'urgencia': 1
        }
        
        resultado = self.analisador.analisar_viagem(dados)
        
        # Deve ter risco aumentado por distância longa
        assert resultado['probabilidade_acidente'] > 10
        assert any('longa' in fator.lower() for fator in resultado['fatores_risco'])
    
    def test_classificacao_nivel_risco(self):
        """Testa classificação de níveis de risco"""
        # Risco baixo
        dados_baixo = {
            'origem': 'São Paulo',
            'destino': 'Santos',
            'data': '2024-01-15',
            'horario': '10:00',
            'rodovia': 'SP-160',
            'distancia_km': 72,
            'tipo_veiculo': 'carro',
            'num_passageiros': 2,
            'urgencia': 1,
            'clima': {'chuva': False}
        }
        
        resultado = self.analisador.analisar_viagem(dados_baixo)
        assert resultado['nivel_risco'] in ['BAIXO', 'MÉDIO']
        
        # Risco alto
        dados_alto = {
            'origem': 'São Paulo',
            'destino': 'Rio de Janeiro',
            'data': '2024-01-15',
            'horario': '02:00',  # Madrugada
            'rodovia': 'BR-116',
            'distancia_km': 430,
            'tipo_veiculo': 'moto',  # Moto
            'num_passageiros': 1,
            'urgencia': 5,  # Alta urgência
            'clima': {'chuva': True, 'precipitacao': 10.0}
        }
        
        resultado = self.analisador.analisar_viagem(dados_alto)
        assert resultado['nivel_risco'] in ['ALTO', 'CRÍTICO']
    
    def test_recomendacoes_personalizadas(self):
        """Testa geração de recomendações personalizadas"""
        dados = {
            'origem': 'São Paulo',
            'destino': 'Santos',
            'data': '2024-01-15',
            'horario': '02:00',  # Madrugada
            'rodovia': 'SP-160',
            'distancia_km': 72,
            'tipo_veiculo': 'carro',
            'num_passageiros': 2,
            'urgencia': 1,
            'clima': {'chuva': True}
        }
        
        resultado = self.analisador.analisar_viagem(dados)
        
        # Deve ter recomendações específicas
        assert len(resultado['recomendacoes']) > 0
        assert any('madrugada' in rec.lower() or 'chuva' in rec.lower() 
                  for rec in resultado['recomendacoes'])
    
    def test_alternativas_horario_rota(self):
        """Testa geração de alternativas"""
        dados = {
            'origem': 'São Paulo',
            'destino': 'Santos',
            'data': '2024-01-15',
            'horario': '18:00',  # Rush
            'rodovia': 'SP-160',
            'distancia_km': 72,
            'tipo_veiculo': 'carro',
            'num_passageiros': 2,
            'urgencia': 1
        }
        
        resultado = self.analisador.analisar_viagem(dados)
        
        # Deve ter alternativas
        assert 'alternativas' in resultado
        assert len(resultado['alternativas'].get('horarios_seguros', [])) > 0
    
    def test_calcular_probabilidade(self):
        """Testa cálculo de probabilidade"""
        # Testa diferentes pontuações
        self.analisador.pontos_risco = 0
        prob = self.analisador._calcular_probabilidade()
        assert prob == 0
        
        self.analisador.pontos_risco = 10
        prob = self.analisador._calcular_probabilidade()
        assert prob == 55.0
        
        self.analisador.pontos_risco = 20
        prob = self.analisador._calcular_probabilidade()
        assert prob == 95.0  # Máximo
    
    def test_classificar_nivel(self):
        """Testa classificação de níveis"""
        assert self.analisador._classificar_nivel(20) == "BAIXO"
        assert self.analisador._classificar_nivel(45) == "MÉDIO"
        assert self.analisador._classificar_nivel(70) == "ALTO"
        assert self.analisador._classificar_nivel(85) == "CRÍTICO"


class TestFuncoesUtilitarias:
    """Testes para funções utilitárias"""
    
    def test_calcular_risco_rapido(self):
        """Testa função de cálculo rápido"""
        dados = {
            'origem': 'São Paulo',
            'destino': 'Santos',
            'data': '2024-01-15',
            'horario': '12:00',
            'rodovia': 'SP-160',
            'distancia_km': 72,
            'tipo_veiculo': 'carro',
            'num_passageiros': 2,
            'urgencia': 1
        }
        
        resultado = calcular_risco_rapido(dados)
        
        assert 'nivel_risco' in resultado
        assert 'probabilidade_acidente' in resultado
        assert resultado['probabilidade_acidente'] >= 0
        assert resultado['probabilidade_acidente'] <= 100


if __name__ == "__main__":
    pytest.main([__file__])
