"""
Testes para o ProcessadorLinguagemNatural
"""

import pytest
import sys
import os

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.nlp_processor import ProcessadorLinguagemNatural, processar_texto_viagem


class TestProcessadorLinguagemNatural:
    """Testes para a classe ProcessadorLinguagemNatural"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.processador = ProcessadorLinguagemNatural()
    
    def test_inicializacao(self):
        """Testa inicialização do processador"""
        assert len(self.processador.padroes_destino) > 0
        assert len(self.processador.padroes_data) > 0
        assert len(self.processador.padroes_horario) > 0
        assert len(self.processador.padroes_rodovia) > 0
        assert len(self.processador.padroes_veiculo) > 0
    
    def test_extrair_destino_basico(self):
        """Testa extração básica de destino"""
        textos = [
            "Vou para Santos amanhã",
            "Preciso ir até Campinas hoje",
            "Destino Rio de Janeiro",
            "Em direção a Belo Horizonte"
        ]
        
        destinos_esperados = ["Santos", "Campinas", "Rio de Janeiro", "Belo Horizonte"]
        
        for texto, destino_esperado in zip(textos, destinos_esperados):
            resultado = self.processador._extrair_destino(texto.lower())
            assert resultado is not None
            assert destino_esperado.lower() in resultado.lower()
    
    def test_extrair_data_basico(self):
        """Testa extração básica de data"""
        hoje = "2024-01-15"  # Simulando data fixa
        
        # Testar palavras-chave de data
        assert "hoje" in self.processador.padroes_data
        assert "amanhã" in self.processador.padroes_data
        assert "segunda" in self.processador.padroes_data
    
    def test_extrair_horario_basico(self):
        """Testa extração básica de horário"""
        textos_horario = [
            "18h",
            "15:30",
            "três da tarde",
            "meio dia"
        ]
        
        horarios_esperados = ["18:00", "15:30", "15:00", "12:00"]
        
        for texto, horario_esperado in zip(textos_horario, horarios_esperados):
            resultado = self.processador._extrair_horario(texto.lower())
            assert resultado == horario_esperado
    
    def test_extrair_rodovia(self):
        """Testa extração de rodovia"""
        textos_rodovia = [
            "BR-101",
            "SP-160",
            "Anchieta",
            "Imigrantes"
        ]
        
        for texto in textos_rodovia:
            resultado = self.processador._extrair_rodovia(texto.upper())
            assert resultado is not None
            assert texto.upper() in resultado
    
    def test_extrair_veiculo(self):
        """Testa extração de tipo de veículo"""
        textos_veiculo = [
            "de carro",
            "de moto",
            "caminhão",
            "ônibus"
        ]
        
        tipos_esperados = ["carro", "moto", "caminhao", "onibus"]
        
        for texto, tipo_esperado in zip(textos_veiculo, tipos_esperados):
            resultado = self.processador._extrair_veiculo(texto.lower())
            assert resultado == tipo_esperado
    
    def test_processar_texto_completo(self):
        """Testa processamento completo de texto"""
        texto = "Vou para Santos amanhã às 18h de carro"
        
        resultado = self.processador.processar_texto(texto)
        
        # Verificar campos obrigatórios
        campos_obrigatorios = [
            'origem', 'destino', 'data', 'horario', 
            'tipo_veiculo', 'distancia_km', 'urgencia'
        ]
        
        for campo in campos_obrigatorios:
            assert campo in resultado
        
        # Verificar valores específicos
        assert resultado['destino'].lower() == 'santos'
        assert resultado['horario'] == '18:00'
        assert resultado['tipo_veiculo'] == 'carro'
        assert resultado['origem'] == 'São Paulo'  # Default
    
    def test_processar_texto_com_familia(self):
        """Testa processamento com contexto de família"""
        texto = "Vou para Campinas hoje à noite com a família"
        
        resultado = self.processador.processar_texto(texto)
        
        assert resultado['num_passageiros'] > 1
        assert 'família' in resultado['contexto']
    
    def test_processar_texto_urgente(self):
        """Testa processamento com urgência"""
        texto = "Preciso ir para Rio de Janeiro urgentemente"
        
        resultado = self.processador.processar_texto(texto)
        
        assert resultado['urgencia'] >= 4
    
    def test_processar_texto_moto(self):
        """Testa processamento com moto"""
        texto = "Vou para Santos de moto amanhã"
        
        resultado = self.processador.processar_texto(texto)
        
        assert resultado['tipo_veiculo'] == 'moto'
    
    def test_processar_texto_distancia(self):
        """Testa cálculo de distância"""
        resultado_sp_santos = self.processador._calcular_distancia("São Paulo", "Santos")
        assert resultado_sp_santos > 0
        
        resultado_sp_rio = self.processador._calcular_distancia("São Paulo", "Rio de Janeiro")
        assert resultado_sp_rio > resultado_sp_santos
    
    def test_processar_texto_urgencia(self):
        """Testa cálculo de urgência"""
        contexto_trabalho = ["trabalho"]
        contexto_familia = ["família"]
        contexto_urgente = ["urgente"]
        contexto_ferias = ["férias"]
        
        urgencia_trabalho = self.processador._calcular_urgencia(contexto_trabalho)
        urgencia_familia = self.processador._calcular_urgencia(contexto_familia)
        urgencia_urgente = self.processador._calcular_urgencia(contexto_urgente)
        urgencia_ferias = self.processador._calcular_urgencia(contexto_ferias)
        
        assert urgencia_urgente > urgencia_trabalho > urgencia_familia > urgencia_ferias
    
    def test_processar_texto_passageiros(self):
        """Testa estimativa de passageiros"""
        contexto_familia = ["família"]
        contexto_trabalho = ["trabalho"]
        
        passageiros_familia = self.processador._estimar_passageiros(contexto_familia)
        passageiros_trabalho = self.processador._estimar_passageiros(contexto_trabalho)
        
        assert passageiros_familia > passageiros_trabalho
    
    def test_coordenadas_cidades(self):
        """Testa mapeamento de coordenadas"""
        # Verificar se algumas cidades principais estão mapeadas
        cidades_principais = [
            'são paulo', 'rio de janeiro', 'belo horizonte', 
            'santos', 'campinas'
        ]
        
        for cidade in cidades_principais:
            lat, lon = self.processador._obter_coordenadas_cidade(cidade)
            assert lat is not None
            assert lon is not None
            assert -90 <= lat <= 90
            assert -180 <= lon <= 180
    
    def test_proximos_dias_semana(self):
        """Testa cálculo de próximos dias da semana"""
        from datetime import datetime
        
        hoje = datetime(2024, 1, 15)  # Segunda-feira
        
        proxima_terca = self.processador._proxima_terca(hoje)
        proxima_sexta = self.processador._proxima_sexta(hoje)
        proximo_sabado = self.processador._proximo_sabado(hoje)
        
        assert proxima_terca > hoje
        assert proxima_sexta > hoje
        assert proximo_sabado > hoje


class TestFuncoesUtilitarias:
    """Testes para funções utilitárias"""
    
    def test_processar_texto_viagem(self):
        """Testa função utilitária de processamento"""
        texto = "Vou para Santos amanhã às 18h"
        
        resultado = processar_texto_viagem(texto)
        
        assert 'origem' in resultado
        assert 'destino' in resultado
        assert 'data' in resultado
        assert 'horario' in resultado
        assert resultado['destino'].lower() == 'santos'


class TestCasosEdge:
    """Testes para casos extremos"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.processador = ProcessadorLinguagemNatural()
    
    def test_texto_vazio(self):
        """Testa processamento de texto vazio"""
        resultado = self.processador.processar_texto("")
        
        # Deve retornar dados padrão
        assert resultado['origem'] == 'São Paulo'
        assert resultado['tipo_veiculo'] == 'carro'
        assert resultado['horario'] == '12:00'
    
    def test_texto_muito_curto(self):
        """Testa processamento de texto muito curto"""
        resultado = self.processador.processar_texto("vou")
        
        # Deve retornar dados padrão
        assert resultado['origem'] == 'São Paulo'
        assert resultado['tipo_veiculo'] == 'carro'
    
    def test_texto_sem_informacoes_relevantes(self):
        """Testa processamento de texto sem informações relevantes"""
        resultado = self.processador.processar_texto("Olá, como você está?")
        
        # Deve retornar dados padrão
        assert resultado['origem'] == 'São Paulo'
        assert resultado['tipo_veiculo'] == 'carro'
    
    def test_texto_com_informacoes_parciais(self):
        """Testa processamento com informações parciais"""
        resultado = self.processador.processar_texto("amanhã")
        
        # Deve extrair a data mas usar defaults para o resto
        assert resultado['data'] is not None
        assert resultado['origem'] == 'São Paulo'
        assert resultado['tipo_veiculo'] == 'carro'


if __name__ == "__main__":
    pytest.main([__file__])
