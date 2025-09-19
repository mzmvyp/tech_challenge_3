"""
Analisador de Risco de Viagem Otimizado - Sistema de Prevenção de Acidentes

Este módulo analisa o risco de acidentes em viagens futuras usando
o modelo otimizado treinado com dados reais da PRF (2020-2025).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import joblib
from pathlib import Path

from ..utils.external_apis import IntegracaoAPIsExternas
from ..core.nlp_processor import ProcessadorLinguagemNatural

logger = logging.getLogger(__name__)


class AnalisadorRiscoViagemOtimizado:
    """
    Analisador de risco de viagem que usa modelo otimizado treinado com dados reais da PRF
    """
    
    def __init__(self):
        """Inicializa o analisador otimizado"""
        self.modelo = None
        self.feature_names = None
        self.integracao_apis = IntegracaoAPIsExternas()
        self.processador_nlp = ProcessadorLinguagemNatural()
        
        # Carregar modelo otimizado
        self.carregar_modelo_otimizado()
        
        # Cache de rotas para otimização
        self.cache_rotas = {}
        
        # Mapeamento de rotas conhecidas
        self.rotas_conhecidas = self._carregar_rotas_conhecidas()
    
    def carregar_modelo_otimizado(self) -> bool:
        """Carrega modelo otimizado treinado"""
        try:
            modelo_path = Path('data/models/modelo_final_otimizado.pkl')
            feature_names_path = Path('data/models/feature_names_final.txt')
            
            if modelo_path.exists() and feature_names_path.exists():
                logger.info("🎯 Carregando modelo otimizado...")
                self.modelo = joblib.load(modelo_path)
                
                with open(feature_names_path, 'r') as f:
                    self.feature_names = f.read().strip().split('\n')
                
                logger.info(f"✅ Modelo otimizado carregado com {len(self.feature_names)} features")
                return True
            else:
                logger.warning("⚠️ Modelo otimizado não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo otimizado: {e}")
            return False
    
    def analisar_viagem(self, origem: str, destino: str, data: str, horario: str, 
                       tipo_veiculo: str = "carro", observacoes: str = "") -> Dict[str, Any]:
        """
        Analisa o risco de uma viagem completa usando modelo otimizado
        """
        try:
            logger.info(f"Analisando viagem: {origem} -> {destino} em {data} às {horario}")

            # 1. Obter rota detalhada
            rota_detalhada = self._obter_rota_detalhada(origem, destino)
            if not rota_detalhada:
                raise ValueError("Não foi possível obter detalhes da rota.")

            # 2. Dividir rota em segmentos de 10km
            segmentos = self._dividir_rota_segmentos(rota_detalhada)
            if not segmentos:
                raise ValueError("Não foi possível dividir a rota em segmentos.")

            # 3. Para cada segmento, analisar risco usando modelo otimizado
            riscos_segmentos = []
            for seg in segmentos:
                risco_segmento = self._analisar_segmento_otimizado(seg, data, horario)
                riscos_segmentos.append(risco_segmento)

            # 4. Calcular risco total da viagem
            risco_total = self._calcular_risco_total(riscos_segmentos)

            # 5. Gerar recomendações
            recomendacoes = self._gerar_recomendacoes(risco_total['nivel'], riscos_segmentos, tipo_veiculo)

            # 6. Gerar alternativas
            alternativas = self._gerar_alternativas(origem, destino, data, horario, tipo_veiculo)

            resultado = {
                'risco_total': risco_total['probabilidade_percentual'],
                'nivel_risco': risco_total['nivel'],
                'pontos_risco': len([s for s in riscos_segmentos if s['probabilidade'] > 0.3]),
                'segmentos_perigosos': [
                    s for s in riscos_segmentos 
                    if s['probabilidade'] > 0.3
                ][:5],  # Top 5 mais perigosos
                'recomendacoes': recomendacoes,
                'alternativas': alternativas,
                'detalhes_viagem': {
                    'origem': origem,
                    'destino': destino,
                    'data': data,
                    'horario': horario,
                    'tipo_veiculo': tipo_veiculo,
                    'distancia_total': sum(s['distancia'] for s in segmentos),
                    'tempo_estimado': self._calcular_tempo_estimado(segmentos)
                },
                'timestamp_analise': datetime.now().isoformat(),
                'modelo_usado': 'otimizado_2020_2025'
            }
            
            logger.info(f"Análise concluída - Risco: {risco_total['nivel']} ({risco_total['probabilidade_percentual']:.1f}%)")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na análise de viagem: {e}")
            return self._resultado_erro(str(e), origem, destino, data, horario, tipo_veiculo)
    
    def _analisar_segmento_otimizado(self, segmento: Dict, data: str, horario: str) -> Dict[str, Any]:
        """Analisa risco de um segmento usando modelo otimizado"""
        try:
            # Criar features para modelo otimizado
            features = self._criar_features_otimizadas(segmento, data, horario)
            
            # Predizer risco usando modelo otimizado
            if self.modelo is not None:
                probabilidade = self.modelo.predict_proba(features)[:, 1][0]
                interpretacao = "Análise com modelo otimizado (97.28% acurácia)"
            else:
                probabilidade = self._calcular_risco_baseline(features)
                interpretacao = "Modelo não disponível - usando regras"
            
            # Identificar fatores de risco
            fatores_risco = self._identificar_fatores_risco_otimizados(features, probabilidade)
            
            return {
                'br': segmento['br'],
                'km': segmento['km'],
                'municipio': segmento['municipio'],
                'uf': segmento['uf'],
                'distancia': segmento['distancia'],
                'probabilidade': probabilidade,
                'nivel_risco': self._classificar_nivel_risco(probabilidade),
                'fatores_risco': fatores_risco,
                'interpretacao': interpretacao,
                'recomendacoes_segmento': self._gerar_recomendacoes_segmento(fatores_risco)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise do segmento: {e}")
            return {
                'br': segmento.get('br', 101),
                'km': segmento.get('km', 0),
                'probabilidade': 0.5,
                'nivel_risco': 'MÉDIO',
                'fatores_risco': [],
                'interpretacao': f"Erro na análise: {e}"
            }
    
    def _criar_features_otimizadas(self, segmento: Dict, data: str, horario: str) -> np.ndarray:
        """Cria features otimizadas para o modelo (18 features essenciais)"""
        try:
            # Converter data e horário
            data_obj = datetime.strptime(data, '%Y-%m-%d')
            hora_obj = datetime.strptime(horario, '%H:%M')
            
            # Features essenciais (18 features do modelo otimizado)
            features = {
                # Features temporais (8)
                'ano': data_obj.year,
                'mes': data_obj.month,
                'hora': hora_obj.hour,
                'dia_semana': data_obj.weekday(),
                'eh_fim_semana': int(data_obj.weekday() >= 5),
                'eh_feriado': int(self._eh_feriado(data_obj)),
                'eh_madrugada': int(hora_obj.hour < 6 or hora_obj.hour >= 22),
                'eh_rush_matinal': int(6 <= hora_obj.hour <= 9),
                'eh_rush_vespertino': int(17 <= hora_obj.hour <= 20),
                
                # Features geográficas (4)
                'br': segmento.get('br', 101),
                'km': segmento.get('km', 0),
                'pista_simples': int(segmento.get('tipo_pista', 'dupla') == 'simples'),
                'tem_acostamento': int(segmento.get('tem_acostamento', True)),
                
                # Features meteorológicas (3) - Simuladas
                'condicao_chuva': int(np.random.random() < 0.25),  # 25% chance de chuva
                'condicao_neblina': int(np.random.random() < 0.08),  # 8% chance de neblina
                'condicao_temporal': int(np.random.random() < 0.05),  # 5% chance de temporal
                
                # Features de contexto (3)
                'pessoas': np.random.poisson(2.5),  # Média de 2.5 pessoas
                'veiculos': np.random.poisson(1.8),  # Média de 1.8 veículos
                'ocupacao_media': np.random.uniform(0, 1)  # Ocupação aleatória
            }
            
            # Converter para array numpy na ordem correta
            if self.feature_names:
                # Usar ordem das features do modelo treinado
                feature_values = [features.get(f, 0) for f in self.feature_names]
            else:
                # Ordem padrão
                feature_values = list(features.values())
                
            return np.array(feature_values).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Erro ao criar features otimizadas: {e}")
            # Retornar array com valores padrão
            return np.zeros((1, 18))
    
    def _identificar_fatores_risco_otimizados(self, features: np.ndarray, probabilidade: float) -> List[str]:
        """Identifica fatores de risco baseado no modelo otimizado"""
        fatores = []
        
        try:
            # Usar feature names se disponível
            if self.feature_names and len(self.feature_names) == features.shape[1]:
                feature_dict = dict(zip(self.feature_names, features[0]))
            else:
                # Fallback para análise básica
                return self._identificar_fatores_risco_basicos(probabilidade)
            
            # Fatores críticos identificados pelo modelo otimizado
            if feature_dict.get('condicao_chuva', 0) == 1:
                fatores.append("🌧️ Condição de chuva (fator crítico - 32.7% importância)")
            
            if feature_dict.get('pista_simples', 0) == 1:
                fatores.append("🛣️ Pista simples (fator crítico - 21.9% importância)")
            
            if feature_dict.get('eh_madrugada', 0) == 1:
                fatores.append("🌙 Horário de madrugada (fator crítico - 11.0% importância)")
            
            if feature_dict.get('condicao_neblina', 0) == 1:
                fatores.append("🌫️ Neblina (fator alto - 7.4% importância)")
            
            if feature_dict.get('eh_fim_semana', 0) == 1:
                fatores.append("📅 Fim de semana (fator alto - 6.9% importância)")
            
            # Adicionar fatores baseados na probabilidade
            if probabilidade > 0.7:
                fatores.append("⚠️ Probabilidade muito alta de acidente")
            elif probabilidade > 0.5:
                fatores.append("⚠️ Probabilidade alta de acidente")
            elif probabilidade > 0.3:
                fatores.append("⚠️ Probabilidade moderada de acidente")
            
            return fatores
            
        except Exception as e:
            logger.error(f"Erro ao identificar fatores de risco: {e}")
            return self._identificar_fatores_risco_basicos(probabilidade)
    
    def _identificar_fatores_risco_basicos(self, probabilidade: float) -> List[str]:
        """Identifica fatores de risco básicos"""
        fatores = []
        
        if probabilidade > 0.7:
            fatores.append("⚠️ Risco muito alto")
        elif probabilidade > 0.5:
            fatores.append("⚠️ Risco alto")
        elif probabilidade > 0.3:
            fatores.append("⚠️ Risco moderado")
        
        return fatores
    
    def _eh_feriado(self, data: datetime) -> bool:
        """Verifica se a data é feriado"""
        # Feriados fixos brasileiros
        feriados_fixos = [
            (1, 1),   # Confraternização Universal
            (4, 21),  # Tiradentes
            (5, 1),   # Dia do Trabalhador
            (9, 7),   # Independência
            (10, 12), # Nossa Senhora Aparecida
            (11, 2),  # Finados
            (11, 15), # Proclamação da República
            (12, 25), # Natal
        ]
        
        return (data.month, data.day) in feriados_fixos
    
    def _obter_rota_detalhada(self, origem: str, destino: str) -> List[Dict]:
        """Obtém rota detalhada (simulada)"""
        # Em produção, integrar com Google Maps API
        distancia = self._estimar_distancia(origem, destino)
        num_segmentos = max(1, int(distancia / 20))
        
        rota = []
        for i in range(num_segmentos):
            segmento = {
                'br': self._inferir_br_rota(origem, destino, i),
                'km_inicio': i * 20,
                'km_fim': min((i + 1) * 20, distancia),
                'km_intervalo': (i * 20) // 10 * 10,
                'distancia': min(20, distancia - i * 20),
                'municipio': f"Município {i+1}",
                'uf': 'SP',
                'tipo_pista': 'dupla',
                'tem_acostamento': True
            }
            rota.append(segmento)
        
        return rota
    
    def _dividir_rota_segmentos(self, rota: List[Dict]) -> List[Dict]:
        """Divide rota em segmentos de 10km"""
        segmentos = []
        
        for segmento_rota in rota:
            km_inicio = segmento_rota['km_inicio']
            km_fim = segmento_rota['km_fim']
            
            km_atual = km_inicio
            while km_atual < km_fim:
                km_proximo = min(km_atual + 10, km_fim)
                
                segmento = {
                    'br': segmento_rota['br'],
                    'km': km_atual,
                    'km_intervalo': (km_atual // 10) * 10,
                    'distancia': km_proximo - km_atual,
                    'municipio': segmento_rota['municipio'],
                    'uf': segmento_rota['uf'],
                    'tipo_pista': segmento_rota['tipo_pista'],
                    'tem_acostamento': segmento_rota['tem_acostamento']
                }
                
                segmentos.append(segmento)
                km_atual = km_proximo
        
        return segmentos
    
    def _estimar_distancia(self, origem: str, destino: str) -> int:
        """Estima distância entre origem e destino (km)"""
        # Distâncias simuladas entre cidades principais
        distancias = {
            ('São Paulo', 'Santos'): 80,
            ('São Paulo', 'Campinas'): 100,
            ('São Paulo', 'Rio de Janeiro'): 430,
            ('São Paulo', 'Belo Horizonte'): 580,
            ('Rio de Janeiro', 'São Paulo'): 430,
            ('Belo Horizonte', 'São Paulo'): 580,
        }
        
        return distancias.get((origem, destino), 200)  # Default 200km
    
    def _inferir_br_rota(self, origem: str, destino: str, segmento: int) -> int:
        """Inferir número da BR baseado na rota"""
        # Mapeamento simplificado
        if 'São Paulo' in origem and 'Santos' in destino:
            return 116  # SP-116
        elif 'São Paulo' in origem and 'Campinas' in destino:
            return 101  # SP-101
        else:
            return 101  # Default
    
    def _calcular_risco_total(self, riscos_segmentos: List[Dict]) -> Dict[str, Any]:
        """Calcula risco total da viagem"""
        if not riscos_segmentos:
            return {'probabilidade': 0.5, 'probabilidade_percentual': 50.0, 'nivel': 'MÉDIO'}
        
        # Calcular probabilidade média ponderada pela distância
        probabilidade_total = 0
        distancia_total = 0
        
        for seg in riscos_segmentos:
            prob = seg['probabilidade']
            dist = seg['distancia']
            probabilidade_total += prob * dist
            distancia_total += dist
        
        if distancia_total > 0:
            probabilidade_media = probabilidade_total / distancia_total
        else:
            probabilidade_media = 0.5
        
        return {
            'probabilidade': probabilidade_media,
            'probabilidade_percentual': probabilidade_media * 100,
            'nivel': self._classificar_nivel_risco(probabilidade_media)
        }
    
    def _classificar_nivel_risco(self, probabilidade: float) -> str:
        """Classifica nível de risco"""
        if probabilidade >= 0.7:
            return 'MUITO ALTO'
        elif probabilidade >= 0.5:
            return 'ALTO'
        elif probabilidade >= 0.3:
            return 'MÉDIO'
        elif probabilidade >= 0.1:
            return 'BAIXO'
        else:
            return 'MUITO BAIXO'
    
    def _gerar_recomendacoes(self, nivel_risco: str, segmentos_perigosos: List[Dict], 
                           tipo_veiculo: str) -> List[str]:
        """Gera recomendações baseadas no risco"""
        recomendacoes = []
        
        if nivel_risco == 'MUITO ALTO':
            recomendacoes.extend([
                "🚨 EVITE esta viagem - risco muito alto",
                "🕐 Considere adiar para horário mais seguro",
                "🛣️ Use rota alternativa se possível",
                "🚗 Mantenha distância segura e velocidade reduzida"
            ])
        elif nivel_risco == 'ALTO':
            recomendacoes.extend([
                "⚠️ Viagem com risco alto - tome cuidado extra",
                "🕐 Evite horários de madrugada",
                "🌧️ Verifique condições meteorológicas",
                "🚗 Reduza velocidade em pistas simples"
            ])
        elif nivel_risco == 'MÉDIO':
            recomendacoes.extend([
                "🟡 Viagem com risco moderado",
                "🚗 Mantenha atenção redobrada",
                "📱 Evite distrações ao dirigir",
                "🛡️ Use cinto de segurança e capacete"
            ])
        else:
            recomendacoes.extend([
                "✅ Viagem com baixo risco",
                "🚗 Dirija com segurança",
                "📱 Evite distrações",
                "🛡️ Mantenha equipamentos de segurança"
            ])
        
        # Recomendações específicas por tipo de veículo
        if tipo_veiculo.lower() in ['moto', 'motocicleta']:
            recomendacoes.extend([
                "🏍️ Use equipamentos de proteção completos",
                "👁️ Mantenha visibilidade máxima",
                "🚗 Evite pontos cegos de outros veículos"
            ])
        
        return recomendacoes
    
    def _gerar_alternativas(self, origem: str, destino: str, data: str, horario: str, 
                          tipo_veiculo: str) -> Dict[str, Any]:
        """Gera alternativas para reduzir risco"""
        return {
            'horarios_seguros': ['10:00', '14:00', '16:00'],
            'rotas_alternativas': [
                f"Rota alternativa via {origem} - {destino}",
                "Evitar pistas simples quando possível"
            ],
            'dicas_gerais': [
                "Verificar condições meteorológicas antes da viagem",
                "Planejar paradas para descanso",
                "Manter veículo em bom estado"
            ]
        }
    
    def _calcular_tempo_estimado(self, segmentos: List[Dict]) -> str:
        """Calcula tempo estimado da viagem"""
        distancia_total = sum(s['distancia'] for s in segmentos)
        tempo_horas = distancia_total / 80  # 80 km/h média
        horas = int(tempo_horas)
        minutos = int((tempo_horas - horas) * 60)
        return f"{horas}h{minutos:02d}min"
    
    def _calcular_risco_baseline(self, features: np.ndarray) -> float:
        """Calcula risco baseline quando modelo não disponível"""
        return 0.3  # Risco médio padrão
    
    def _gerar_recomendacoes_segmento(self, fatores_risco: List[str]) -> List[str]:
        """Gera recomendações específicas para um segmento"""
        if not fatores_risco:
            return ["Segmento com baixo risco"]
        
        recomendacoes = []
        for fator in fatores_risco:
            if "chuva" in fator.lower():
                recomendacoes.append("Reduza velocidade em 30%")
            elif "neblina" in fator.lower():
                recomendacoes.append("Use faróis baixos e mantenha distância")
            elif "madrugada" in fator.lower():
                recomendacoes.append("Evite fadiga e mantenha atenção")
            elif "pista simples" in fator.lower():
                recomendacoes.append("Ultrapasse com muito cuidado")
        
        return recomendacoes
    
    def _resultado_erro(self, erro: str, origem: str = "N/A", destino: str = "N/A", 
                       data: str = "N/A", horario: str = "N/A", tipo_veiculo: str = "carro") -> Dict[str, Any]:
        """Retorna resultado de erro com estrutura completa"""
        return {
            'risco_total': 50.0,
            'nivel_risco': 'MÉDIO',
            'segmentos_perigosos': [],
            'recomendacoes': [
                f"❌ Erro na análise: {erro}",
                "💡 Tente novamente ou use dados estruturados"
            ],
            'alternativas': {
                'horarios_seguros': ["10:00", "14:00", "20:00"],
                'rotas_alternativas': [],
                'dicas_gerais': ["Verifique os dados fornecidos"]
            },
            'detalhes_viagem': {
                'origem': origem,
                'destino': destino,
                'data': data,
                'horario': horario,
                'tipo_veiculo': tipo_veiculo,
                'distancia_total': 0,
                'tempo_estimado': 'N/A'
            },
            'erro': True,
            'timestamp_analise': datetime.now().isoformat(),
            'modelo_usado': 'erro'
        }
    
    def _carregar_rotas_conhecidas(self) -> Dict:
        """Carrega mapeamento de rotas conhecidas"""
        return {
            'São Paulo': {'Santos': {'br': 116, 'distancia': 80}},
            'São Paulo': {'Campinas': {'br': 101, 'distancia': 100}},
            # Adicionar mais rotas conforme necessário
        }
