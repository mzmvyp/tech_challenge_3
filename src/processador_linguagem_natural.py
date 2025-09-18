# src/processador_linguagem_natural.py

import re
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ProcessadorLinguagemNatural:
    """
    Processa linguagem natural para extrair dados de viagem
    """
    
    def __init__(self):
        self.padroes_destino = [
            r'para\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+hoje|\s+amanhã|\s+às|\s+no|\s+na|\s+em|\s+de|\s+da|\s+do|\s+das|\s+dos|\s+$|$)',
            r'vou\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+hoje|\s+amanhã|\s+às|\s+no|\s+na|\s+em|\s+de|\s+da|\s+do|\s+das|\s+dos|\s+$|$)',
            r'destino\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+hoje|\s+amanhã|\s+às|\s+no|\s+na|\s+em|\s+de|\s+da|\s+do|\s+das|\s+dos|\s+$|$)',
        ]
        
        self.padroes_horario = [
            r'às\s+(\d{1,2}):?(\d{0,2})',
            r'(\d{1,2}):?(\d{0,2})\s+horas?',
            r'(\d{1,2}):?(\d{0,2})h',
            r'(\d{1,2}):?(\d{0,2})\s+da\s+(manhã|tarde|noite)',
        ]
        
        self.padroes_data = [
            r'hoje',
            r'amanhã',
            r'depois\s+de\s+amanhã',
            r'(\d{1,2})/(\d{1,2})',
            r'(\d{1,2})\s+de\s+(\w+)',
        ]
        
        # Mapeamento de cidades para coordenadas e BRs
        self.cidades_brasil = {
            'são paulo': {'uf': 'SP', 'br': 116, 'coords': (-23.5505, -46.6333)},
            'campinas': {'uf': 'SP', 'br': 116, 'coords': (-22.9056, -47.0608)},
            'rio de janeiro': {'uf': 'RJ', 'br': 101, 'coords': (-22.9068, -43.1729)},
            'belo horizonte': {'uf': 'MG', 'br': 381, 'coords': (-19.9167, -43.9345)},
            'salvador': {'uf': 'BA', 'br': 101, 'coords': (-12.9714, -38.5014)},
            'brasília': {'uf': 'DF', 'br': 153, 'coords': (-15.7801, -47.9292)},
            'fortaleza': {'uf': 'CE', 'br': 116, 'coords': (-3.7319, -38.5267)},
            'manaus': {'uf': 'AM', 'br': 174, 'coords': (-3.1190, -60.0217)},
            'curitiba': {'uf': 'PR', 'br': 116, 'coords': (-25.4244, -49.2654)},
            'recife': {'uf': 'PE', 'br': 101, 'coords': (-8.0476, -34.8770)},
            'porto alegre': {'uf': 'RS', 'br': 116, 'coords': (-30.0346, -51.2177)},
            'goiânia': {'uf': 'GO', 'br': 153, 'coords': (-16.6864, -49.2643)},
            'belém': {'uf': 'PA', 'br': 316, 'coords': (-1.4558, -48.5044)},
            'guarulhos': {'uf': 'SP', 'br': 116, 'coords': (-23.4538, -46.5331)},
            'são gonçalo': {'uf': 'RJ', 'br': 101, 'coords': (-22.8269, -43.0539)},
            'maceió': {'uf': 'AL', 'br': 101, 'coords': (-9.6658, -35.7353)},
            'duque de caxias': {'uf': 'RJ', 'br': 101, 'coords': (-22.7858, -43.3047)},
            'natal': {'uf': 'RN', 'br': 101, 'coords': (-5.7945, -35.2110)},
            'teresina': {'uf': 'PI', 'br': 316, 'coords': (-5.0892, -42.8019)},
            'campo grande': {'uf': 'MS', 'br': 163, 'coords': (-20.4697, -54.6201)},
        }
        
        # Mapeamento de meses
        self.meses = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
    
    def processar_texto(self, texto: str) -> Dict:
        """
        Processa texto em linguagem natural e retorna dados estruturados
        """
        texto = texto.lower().strip()
        
        # Extrair destino
        destino = self._extrair_destino(texto)
        
        # Extrair horário
        horario = self._extrair_horario(texto)
        
        # Extrair data
        data = self._extrair_data(texto)
        
        # Detectar origem (assumindo São Paulo por padrão)
        origem = self._detectar_origem(texto)
        
        # Buscar dados da rota
        dados_rota = self._buscar_dados_rota(origem, destino)
        
        # Buscar previsão do tempo
        previsao_tempo = self._buscar_previsao_tempo(destino)
        
        # Detectar tipo de veículo (assumindo automóvel por padrão)
        tipo_veiculo = self._detectar_tipo_veiculo(texto)
        
        # Detectar número de passageiros
        passageiros = self._detectar_passageiros(texto)
        
        return {
            'origem': origem,
            'destino': destino,
            'data_viagem': data,
            'horario_saida': horario,
            'br_principal': dados_rota.get('br', 116),
            'km_inicial': dados_rota.get('km_inicial', 0.0),
            'km_final': dados_rota.get('km_final', 50.0),
            'uf': dados_rota.get('uf', 'SP'),
            'tipo_veiculo': tipo_veiculo,
            'condicao_metereologica': previsao_tempo.get('condicao', 'CÉU CLARO'),
            'tipo_pista': dados_rota.get('tipo_pista', 'DUPLA'),
            'tracado_via': dados_rota.get('tracado_via', 'RETA'),
            'passageiros': passageiros
        }
    
    def _extrair_destino(self, texto: str) -> str:
        """Extrai destino do texto"""
        for padrao in self.padroes_destino:
            match = re.search(padrao, texto)
            if match:
                destino = match.group(1).strip()
                # Limpar destino
                destino = re.sub(r'\s+', ' ', destino)
                return destino.title()
        
        return "Campinas"  # Padrão
    
    def _extrair_horario(self, texto: str) -> str:
        """Extrai horário do texto"""
        for padrao in self.padroes_horario:
            match = re.search(padrao, texto)
            if match:
                hora = int(match.group(1))
                minuto = int(match.group(2)) if match.group(2) else 0
                
                # Ajustar para período do dia
                if 'tarde' in texto and hora < 12:
                    hora += 12
                elif 'noite' in texto and hora < 12:
                    hora += 12
                
                return f"{hora:02d}:{minuto:02d}"
        
        # Horário padrão baseado no período
        agora = datetime.now()
        if 'manhã' in texto:
            return "08:00"
        elif 'tarde' in texto:
            return "14:00"
        elif 'noite' in texto:
            return "20:00"
        else:
            return agora.strftime("%H:%M")
    
    def _extrair_data(self, texto: str) -> str:
        """Extrai data do texto"""
        agora = datetime.now()
        
        if 'hoje' in texto:
            return agora.strftime("%Y-%m-%d")
        elif 'amanhã' in texto:
            amanha = agora + timedelta(days=1)
            return amanha.strftime("%Y-%m-%d")
        elif 'depois de amanhã' in texto:
            depois = agora + timedelta(days=2)
            return depois.strftime("%Y-%m-%d")
        else:
            # Tentar extrair data específica
            for padrao in self.padroes_data:
                match = re.search(padrao, texto)
                if match:
                    if padrao == r'(\d{1,2})/(\d{1,2})':
                        dia, mes = match.groups()
                        return f"{agora.year}-{int(mes):02d}-{int(dia):02d}"
                    elif padrao == r'(\d{1,2})\s+de\s+(\w+)':
                        dia, mes_nome = match.groups()
                        mes = self.meses.get(mes_nome.lower(), agora.month)
                        return f"{agora.year}-{mes:02d}-{int(dia):02d}"
        
        return agora.strftime("%Y-%m-%d")
    
    def _detectar_origem(self, texto: str) -> str:
        """Detecta origem (assumindo São Paulo por padrão)"""
        # Em uma implementação real, usaria GPS ou histórico
        return "São Paulo"
    
    def _buscar_dados_rota(self, origem: str, destino: str) -> Dict:
        """Busca dados da rota entre origem e destino"""
        origem_lower = origem.lower()
        destino_lower = destino.lower()
        
        # Buscar dados das cidades
        dados_origem = self.cidades_brasil.get(origem_lower, self.cidades_brasil['são paulo'])
        dados_destino = self.cidades_brasil.get(destino_lower, self.cidades_brasil['campinas'])
        
        # Calcular distância aproximada (simplificado)
        distancia = self._calcular_distancia(
            dados_origem['coords'], 
            dados_destino['coords']
        )
        
        # Determinar tipo de pista baseado na distância
        tipo_pista = 'SIMPLE' if distancia < 100 else 'DUPLA'
        
        # Determinar traçado baseado na distância
        tracado_via = 'CURVA' if distancia > 200 else 'RETA'
        
        return {
            'br': dados_destino['br'],
            'uf': dados_destino['uf'],
            'km_inicial': 0.0,
            'km_final': distancia,
            'distancia': distancia,
            'tipo_pista': tipo_pista,
            'tracado_via': tracado_via,
            'tempo_estimado': f"{int(distancia / 80 * 60)} minutos"
        }
    
    def _calcular_distancia(self, coords1: Tuple[float, float], coords2: Tuple[float, float]) -> float:
        """Calcula distância aproximada entre duas coordenadas"""
        # Fórmula simplificada de distância
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        
        # Distância em km (aproximada)
        distancia = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 111
        return max(10, min(500, distancia))  # Limitar entre 10 e 500 km
    
    def _buscar_previsao_tempo(self, destino: str) -> Dict:
        """Busca previsão do tempo real para o destino"""
        # TODO: Implementar integração com API de previsão do tempo real
        # Por enquanto, retornar condição padrão baseada em dados históricos
        return {'condicao': 'CÉU CLARO'}
    
    def _detectar_tipo_veiculo(self, texto: str) -> str:
        """Detecta tipo de veículo no texto"""
        if any(palavra in texto for palavra in ['moto', 'motocicleta', 'moto']):
            return 'MOTOCICLETA'
        elif any(palavra in texto for palavra in ['caminhão', 'caminhao', 'truck']):
            return 'CAMINHÃO'
        elif any(palavra in texto for palavra in ['ônibus', 'onibus', 'bus']):
            return 'ÔNIBUS'
        else:
            return 'AUTOMÓVEL'
    
    def _detectar_passageiros(self, texto: str) -> int:
        """Detecta número de passageiros no texto"""
        # Procurar por números
        numeros = re.findall(r'\b(\d+)\b', texto)
        if numeros:
            return min(10, max(1, int(numeros[0])))
        return 2  # Padrão

# Exemplo de uso
if __name__ == "__main__":
    processador = ProcessadorLinguagemNatural()
    
    # Testes
    frases_teste = [
        "Vou para Campinas hoje às 16h",
        "Preciso ir para Rio de Janeiro amanhã de manhã",
        "Viagem para Belo Horizonte na terça-feira às 14:30",
        "Vou de moto para Santos hoje à noite",
        "Preciso ir para Brasília com 3 pessoas"
    ]
    
    for frase in frases_teste:
        print(f"\n📝 Frase: {frase}")
        resultado = processador.processar_texto(frase)
        print(f"✅ Resultado: {json.dumps(resultado, indent=2, ensure_ascii=False)}")
