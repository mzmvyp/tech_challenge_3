"""
Processador de Linguagem Natural - Sistema de Prevenção de Acidentes PRF

Este módulo implementa processamento avançado de linguagem natural para
extrair informações de viagem a partir de texto natural em português.
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProcessadorLinguagemNatural:
    """
    Processa texto em linguagem natural para extrair dados de viagem
    
    Exemplo de entrada: "Vou para Santos amanhã às 18h"
    Exemplo de saída: {
        'origem': 'São Paulo',
        'destino': 'Santos',
        'data': '2024-01-16',
        'horario': '18:00',
        'rodovia': 'SP-160',
        'tipo_veiculo': 'carro'
    }
    """
    
    def __init__(self):
        """Inicializa o processador NLP"""
        self.padroes_destino = [
            r'para\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+hoje|\s+amanhã|\s+segunda|\s+terça|\s+quarta|\s+quinta|\s+sexta|\s+sábado|\s+domingo|\s+às|\s+as)',
            r'até\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+hoje|\s+amanhã|\s+segunda|\s+terça|\s+quarta|\s+quinta|\s+sexta|\s+sábado|\s+domingo|\s+às|\s+as)',
            r'em\s+direção\s+a\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+hoje|\s+amanhã|\s+segunda|\s+terça|\s+quarta|\s+quinta|\s+sexta|\s+sábado|\s+domingo|\s+às|\s+as)',
            r'destino\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+hoje|\s+amanhã|\s+segunda|\s+terça|\s+quarta|\s+quinta|\s+sexta|\s+sábado|\s+domingo|\s+às|\s+as)',
            r'([A-Za-zÀ-ÿ\s]+?)\s+hoje',
            r'([A-Za-zÀ-ÿ\s]+?)\s+amanhã',
            r'([A-Za-zÀ-ÿ\s]+?)\s+segunda',
            r'([A-Za-zÀ-ÿ\s]+?)\s+terça',
            r'([A-Za-zÀ-ÿ\s]+?)\s+quarta',
            r'([A-Za-zÀ-ÿ\s]+?)\s+quinta',
            r'([A-Za-zÀ-ÿ\s]+?)\s+sexta',
            r'([A-Za-zÀ-ÿ\s]+?)\s+sábado',
            r'([A-Za-zÀ-ÿ\s]+?)\s+domingo',
            # Padrões mais genéricos
            r'para\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+às|\s+as|\s+hoje|\s+amanhã)',
            r'vou\s+para\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+às|\s+as|\s+hoje|\s+amanhã)',
            r'preciso\s+ir\s+para\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+às|\s+as|\s+hoje|\s+amanhã)'
        ]
        
        self.padroes_data = [
            r'hoje',
            r'amanhã',
            r'segunda(?:\s+feira)?',
            r'terça(?:\s+feira)?',
            r'quarta(?:\s+feira)?',
            r'quinta(?:\s+feira)?',
            r'sexta(?:\s+feira)?',
            r'sábado',
            r'domingo',
            r'(\d{1,2})/(\d{1,2})',
            r'(\d{1,2})\s+de\s+(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)',
            r'(\d{1,2})\s+de\s+(\d{4})'
        ]
        
        self.padroes_horario = [
            r'(\d{1,2})h',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s+horas',
            r'(\d{1,2})\s+da\s+(manhã|tarde|noite|madrugada)',
            r'meio\s+dia',
            r'meia\s+noite',
            r'de\s+(manhã|tarde|noite|madrugada)',
            r'pela\s+(manhã|tarde|noite|madrugada)'
        ]
        
        self.padroes_rodovia = [
            r'(BR-\d{3})',
            r'(SP-\d{2,3})',
            r'(RJ-\d{2,3})',
            r'(MG-\d{2,3})',
            r'(Anchieta)',
            r'(Imigrantes)',
            r'(Dutra)',
            r'(Raposo\s+Tavares)',
            r'(Régis\s+Bittencourt)',
            r'(Fernão\s+Dias)',
            r'(Castello\s+Branco)',
            r'(Bandeirantes)',
            r'(Ayrton\s+Senna)'
        ]
        
        self.padroes_veiculo = [
            r'(carro|automóvel|veículo)',
            r'(moto|motocicleta|motoneta)',
            r'(caminhão|truck|veículo\s+pesado)',
            r'(ônibus|bus)',
            r'(van|utilitário)'
        ]
        
        self.padroes_contexto = [
            r'(família|com\s+a\s+família)',
            r'(trabalho|a\s+trabalho|para\s+o\s+trabalho)',
            r'(urgente|urgência|com\s+pressa)',
            r'(férias|viagem\s+de\s+férias)',
            r'(negócios|a\s+negócios)'
        ]
        
        # Mapeamento de cidades para coordenadas (simplificado)
        self.coordenadas_cidades = {
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
            'belém': (-1.4558, -48.5044),
            'guarulhos': (-23.4538, -46.5333),
            'são bernardo do campo': (-23.6939, -46.5650),
            'santo andré': (-23.6637, -46.5382),
            'osasco': (-23.5329, -46.7919),
            'são josé dos campos': (-23.1791, -45.8872),
            'ribeirão preto': (-21.1775, -47.8103)
        }
        
        # Mapeamento de rodovias para distâncias típicas
        self.distancias_rodovias = {
            'são paulo-santos': 72,
            'são paulo-campinas': 100,
            'são paulo-rio de janeiro': 430,
            'são paulo-belo horizonte': 585,
            'rio de janeiro-belo horizonte': 445,
            'são paulo-curitiba': 408,
            'curitiba-porto alegre': 710,
            'são paulo-brasília': 1030
        }
    
    def processar_texto(self, texto: str) -> Dict:
        """
        Processa texto em linguagem natural e extrai dados de viagem
        
        Args:
            texto: Texto em português descrevendo a viagem
            
        Returns:
            Dict com dados estruturados da viagem
        """
        logger.info(f"Processando texto: '{texto}'")
        
        texto_lower = texto.lower()
        
        # Extrair informações
        destino = self._extrair_destino(texto_lower)
        data = self._extrair_data(texto_lower)
        horario = self._extrair_horario(texto_lower)
        rodovia = self._extrair_rodovia(texto_lower)
        tipo_veiculo = self._extrair_veiculo(texto_lower)
        contexto = self._extrair_contexto(texto_lower)
        
        # Detectar origem (se não mencionada, usar São Paulo como padrão)
        origem = self._detectar_origem(texto_lower, destino)
        
        # Calcular distância
        distancia = self._calcular_distancia(origem, destino)
        
        # Calcular urgencia baseada no contexto
        urgencia = self._calcular_urgencia(contexto)
        
        resultado = {
            'origem': origem,
            'destino': destino,
            'data': data,
            'horario': horario,
            'rodovia': rodovia,
            'distancia_km': distancia,
            'tipo_veiculo': tipo_veiculo,
            'num_passageiros': self._estimar_passageiros(contexto),
            'urgencia': urgencia,
            'contexto': contexto,
            'texto_original': texto
        }
        
        logger.info(f"Dados extraídos: {resultado}")
        return resultado
    
    def _extrair_destino(self, texto: str) -> Optional[str]:
        """Extrai o destino da viagem"""
        for padrao in self.padroes_destino:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                destino = match.group(1).strip()
                # Limpar palavras comuns e temporais
                destino = re.sub(r'\b(de|para|até|em|a|o|da|do|hoje|amanhã|segunda|terça|quarta|quinta|sexta|sábado|domingo|às|as)\b', '', destino).strip()
                
                # Limpar espaços extras
                destino = re.sub(r'\s+', ' ', destino).strip()
                
                # Verificar se é uma cidade conhecida
                destino_lower = destino.lower()
                for cidade in self.coordenadas_cidades.keys():
                    # Busca mais flexível - verifica se as palavras principais estão presentes
                    palavras_cidade = cidade.split()
                    palavras_destino = destino_lower.split()
                    
                    # Se todas as palavras da cidade estão no destino
                    if all(palavra in destino_lower for palavra in palavras_cidade):
                        return cidade.title()
                    
                    # Busca por similaridade (para casos como "rio de janeiro" vs "rio janeiro")
                    if len(palavras_cidade) > 1 and len(palavras_destino) > 1:
                        if palavras_cidade[0] in destino_lower and palavras_cidade[-1] in destino_lower:
                            return cidade.title()
                
                return destino.title()
        return None
    
    def _extrair_data(self, texto: str) -> str:
        """Extrai a data da viagem"""
        hoje = datetime.now()
        
        # Verificar palavras-chave de data
        if 'hoje' in texto:
            return hoje.strftime('%Y-%m-%d')
        elif 'amanhã' in texto:
            amanha = hoje + timedelta(days=1)
            return amanha.strftime('%Y-%m-%d')
        elif 'segunda' in texto:
            return self._proxima_segunda(hoje).strftime('%Y-%m-%d')
        elif 'terça' in texto:
            return self._proxima_terca(hoje).strftime('%Y-%m-%d')
        elif 'quarta' in texto:
            return self._proxima_quarta(hoje).strftime('%Y-%m-%d')
        elif 'quinta' in texto:
            return self._proxima_quinta(hoje).strftime('%Y-%m-%d')
        elif 'sexta' in texto:
            return self._proxima_sexta(hoje).strftime('%Y-%m-%d')
        elif 'sábado' in texto:
            return self._proximo_sabado(hoje).strftime('%Y-%m-%d')
        elif 'domingo' in texto:
            return self._proximo_domingo(hoje).strftime('%Y-%m-%d')
        
        # Verificar formato DD/MM
        match = re.search(r'(\d{1,2})/(\d{1,2})', texto)
        if match:
            dia, mes = match.groups()
            ano = hoje.year
            return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
        
        # Se não encontrou data específica, assumir hoje
        return hoje.strftime('%Y-%m-%d')
    
    def _extrair_horario(self, texto: str) -> str:
        """Extrai o horário da viagem"""
        # Verificar horários específicos
        match = re.search(r'(\d{1,2})h', texto)
        if match:
            hora = int(match.group(1))
            return f"{hora:02d}:00"
        
        match = re.search(r'(\d{1,2}):(\d{2})', texto)
        if match:
            hora, minuto = match.groups()
            return f"{int(hora):02d}:{int(minuto):02d}"
        
        # Verificar períodos do dia
        if 'meio dia' in texto:
            return "12:00"
        elif 'meia noite' in texto:
            return "00:00"
        elif 'manhã' in texto:
            return "08:00"
        elif 'tarde' in texto:
            return "15:00"
        elif 'noite' in texto:
            return "20:00"
        elif 'madrugada' in texto:
            return "02:00"
        
        # Se não encontrou horário específico, assumir meio-dia
        return "12:00"
    
    def _extrair_rodovia(self, texto: str) -> Optional[str]:
        """Extrai a rodovia mencionada"""
        for padrao in self.padroes_rodovia:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Tentar inferir rodovia baseada no destino
        if 'santos' in texto:
            return "SP-160"  # Imigrantes
        elif 'campinas' in texto:
            return "SP-348"  # Bandeirantes
        elif 'rio de janeiro' in texto or 'rio' in texto:
            return "BR-116"  # Dutra
        
        return None
    
    def _extrair_veiculo(self, texto: str) -> str:
        """Extrai o tipo de veículo"""
        for padrao in self.padroes_veiculo:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                veiculo = match.group(1).lower()
                if 'moto' in veiculo:
                    return 'moto'
                elif 'caminhão' in veiculo or 'truck' in veiculo:
                    return 'caminhao'
                elif 'ônibus' in veiculo or 'bus' in veiculo:
                    return 'onibus'
                elif 'van' in veiculo:
                    return 'van'
                else:
                    return 'carro'
        
        # Se não encontrou, assumir carro
        return 'carro'
    
    def _extrair_contexto(self, texto: str) -> List[str]:
        """Extrai contexto da viagem"""
        contexto = []
        for padrao in self.padroes_contexto:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                contexto.append(match.group(1).lower())
        return contexto
    
    def _detectar_origem(self, texto: str, destino: Optional[str]) -> str:
        """Detecta a origem da viagem"""
        # Verificar se origem é mencionada explicitamente
        padroes_origem = [
            r'de\s+([A-Za-zÀ-ÿ\s]+?)\s+para',
            r'partindo\s+de\s+([A-Za-zÀ-ÿ\s]+)',
            r'saindo\s+de\s+([A-Za-zÀ-ÿ\s]+)'
        ]
        
        for padrao in padroes_origem:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                origem = match.group(1).strip()
                origem = re.sub(r'\b(de|para|até|em|a|o|da|do)\b', '', origem).strip()
                return origem.title()
        
        # Se não encontrou origem explícita, usar São Paulo como padrão
        return "São Paulo"
    
    def _calcular_distancia(self, origem: str, destino: Optional[str]) -> float:
        """Calcula distância entre origem e destino"""
        if not destino:
            return 0.0
        
        # Normalizar nomes das cidades
        origem_norm = origem.lower().replace(' ', '-')
        destino_norm = destino.lower().replace(' ', '-')
        
        # Tentar encontrar distância conhecida
        rota = f"{origem_norm}-{destino_norm}"
        if rota in self.distancias_rodovias:
            return self.distancias_rodovias[rota]
        
        # Distâncias aproximadas baseadas em conhecimento geral
        distancias_aproximadas = {
            ('são-paulo', 'santos'): 72,
            ('são-paulo', 'campinas'): 100,
            ('são-paulo', 'rio-de-janeiro'): 430,
            ('são-paulo', 'belo-horizonte'): 585,
            ('são-paulo', 'curitiba'): 408,
            ('rio-de-janeiro', 'belo-horizonte'): 445,
            ('curitiba', 'porto-alegre'): 710,
            ('são-paulo', 'brasília'): 1030
        }
        
        return distancias_aproximadas.get((origem_norm, destino_norm), 50.0)
    
    def _calcular_urgencia(self, contexto: List[str]) -> int:
        """Calcula nível de urgência baseado no contexto"""
        if not contexto:
            return 1
        
        urgencia = 1
        
        if any('urgente' in c or 'pressa' in c for c in contexto):
            urgencia = 5
        elif any('trabalho' in c for c in contexto):
            urgencia = 3
        elif any('família' in c for c in contexto):
            urgencia = 2
        elif any('férias' in c for c in contexto):
            urgencia = 1
        
        return urgencia
    
    def _estimar_passageiros(self, contexto: List[str]) -> int:
        """Estima número de passageiros baseado no contexto"""
        if any('família' in c for c in contexto):
            return 4
        elif any('trabalho' in c for c in contexto):
            return 1
        else:
            return 1
    
    # Métodos auxiliares para calcular próximos dias da semana
    def _proxima_segunda(self, hoje: datetime) -> datetime:
        dias_para_segunda = (7 - hoje.weekday()) % 7
        if dias_para_segunda == 0:
            dias_para_segunda = 7
        return hoje + timedelta(days=dias_para_segunda)
    
    def _proxima_terca(self, hoje: datetime) -> datetime:
        dias_para_terca = (1 - hoje.weekday()) % 7
        if dias_para_terca == 0:
            dias_para_terca = 7
        return hoje + timedelta(days=dias_para_terca)
    
    def _proxima_quarta(self, hoje: datetime) -> datetime:
        dias_para_quarta = (2 - hoje.weekday()) % 7
        if dias_para_quarta == 0:
            dias_para_quarta = 7
        return hoje + timedelta(days=dias_para_quarta)
    
    def _proxima_quinta(self, hoje: datetime) -> datetime:
        dias_para_quinta = (3 - hoje.weekday()) % 7
        if dias_para_quinta == 0:
            dias_para_quinta = 7
        return hoje + timedelta(days=dias_para_quinta)
    
    def _proxima_sexta(self, hoje: datetime) -> datetime:
        dias_para_sexta = (4 - hoje.weekday()) % 7
        if dias_para_sexta == 0:
            dias_para_sexta = 7
        return hoje + timedelta(days=dias_para_sexta)
    
    def _proximo_sabado(self, hoje: datetime) -> datetime:
        dias_para_sabado = (5 - hoje.weekday()) % 7
        if dias_para_sabado == 0:
            dias_para_sabado = 7
        return hoje + timedelta(days=dias_para_sabado)
    
    def _proximo_domingo(self, hoje: datetime) -> datetime:
        dias_para_domingo = (6 - hoje.weekday()) % 7
        if dias_para_domingo == 0:
            dias_para_domingo = 7
        return hoje + timedelta(days=dias_para_domingo)


def processar_texto_viagem(texto: str) -> Dict:
    """
    Função utilitária para processamento rápido de texto
    
    Args:
        texto: Texto em português descrevendo a viagem
    
    Returns:
        Dict com dados estruturados da viagem
    """
    processador = ProcessadorLinguagemNatural()
    return processador.processar_texto(texto)
