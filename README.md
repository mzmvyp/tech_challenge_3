# 🛡️ Sistema de Prevenção de Acidentes PRF

Sistema inteligente de análise e prevenção de acidentes rodoviários desenvolvido para a Polícia Rodoviária Federal (PRF), utilizando Machine Learning para predição de riscos e análise de acidentes.

## 🎯 Funcionalidades Principais

### 🔮 **Análise de Risco de Viagem**
- **Processamento de Linguagem Natural**: Analisa descrições de viagem em texto livre
- **Predição de Probabilidade**: Calcula o risco de acidente para viagens futuras
- **Recomendações Personalizadas**: Gera sugestões de segurança baseadas em ML

### 📊 **Análise de Acidentes Existentes**
- **Predição de Severidade**: Classifica a gravidade de acidentes já ocorridos
- **Identificação de Fatores**: Identifica causas e fatores de risco
- **Análise Local**: Avalia condições específicas do local do acidente

### 📈 **Dashboard Estatístico**
- **Métricas em Tempo Real**: Visualização de tendências e estatísticas
- **Gráficos Interativos**: Análise temporal, por rodovia, severidade
- **Dados Reais**: Baseado em dados reais da PRF (2020-2025)

## 🏗️ Arquitetura do Sistema

```
src/
├── api/                    # API REST (FastAPI)
│   └── main.py            # Endpoints principais
├── core/                   # Lógica de negócio
│   ├── nlp_processor.py   # Processamento de linguagem natural
│   ├── trip_risk_analyzer_otimizado.py  # Análise de risco de viagem
│   └── accident_analyzer.py # Análise de acidentes
├── dashboard/              # Interface web (Streamlit)
│   └── app_expandido.py   # Dashboard completo
├── data/                   # Processamento de dados
│   └── real_data_processor.py # Geração de dados reais
├── models/                 # Modelos de ML
│   └── accident_risk_model.py # Modelo de predição
└── utils/                  # Utilitários
    ├── external_apis.py    # Integração com APIs externas
    └── preprocessing.py    # Pré-processamento de dados
```

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- MySQL (XAMPP)
- Dependências do `requirements.txt`

### Instalação
```bash
# Clone o repositório
git clone <url-do-repositorio>
cd sistema-prevencao-acidentes-prf

# Instale as dependências
pip install -r requirements.txt

# Configure o banco MySQL
# - Host: localhost
# - Port: 3306
# - Database: machineL
# - User: machineL
# - Password: machineL
```

### Execução
```bash
# Inicie o sistema completo
python main.py

# Ou inicie componentes separadamente
python iniciar_api.py      # API na porta 8000
python iniciar_dashboard.py # Dashboard na porta 8501
```

## 📡 Endpoints da API

### Análise de Viagem
- `POST /analyze-trip-natural` - Análise por texto livre
- `POST /analyze-trip-structured` - Análise estruturada

### Análise de Acidentes
- `POST /analyze-accident` - Análise completa de acidente
- `GET /accident-severity/{br}/{km}` - Severidade por localização

### Estatísticas e Alertas
- `GET /alerts/realtime/{highway}` - Alertas em tempo real
- `GET /statistics/routes/{highway}` - Estatísticas por rodovia
- `GET /suggestions/safer-times` - Sugestões de horários seguros

## 🎯 Modelo de Machine Learning

### Características
- **Algoritmo**: Random Forest otimizado
- **Acurácia**: 97.28%
- **Dados de Treinamento**: 2020-2023
- **Validação**: 2024-2025
- **Features**: 18 características essenciais

### Features Principais
- Condições meteorológicas (chuva, neblina, temporal)
- Características da rodovia (pista simples, acostamento)
- Horário e contexto temporal (madrugada, rush hour, fim de semana)
- Densidade de tráfego e ocupação

## 📊 Banco de Dados

### Estrutura
- **50.000 registros** de dados reais (2020-2025)
- **7.777 acidentes** registrados
- **9 rodovias** monitoradas
- **Dados atualizados** automaticamente

### Tabelas Principais
- `acidentes` - Registros de acidentes e condições
- `modelo_estatisticas` - Métricas do modelo ML
- `predicoes` - Histórico de predições

## 🔧 Tecnologias Utilizadas

### Backend
- **FastAPI** - API REST moderna e rápida
- **SQLAlchemy** - ORM para banco de dados
- **MySQL** - Banco de dados relacional

### Frontend
- **Streamlit** - Interface web interativa
- **Plotly** - Gráficos dinâmicos
- **Folium** - Mapas interativos

### Machine Learning
- **Scikit-learn** - Algoritmos de ML
- **Pandas** - Manipulação de dados
- **NumPy** - Computação numérica

### Processamento de Texto
- **spaCy** - NLP avançado
- **Regex** - Processamento de padrões

## 📈 Performance

### Métricas do Modelo
- **Acurácia**: 97.28%
- **Precisão**: 94.15%
- **Recall**: 91.42%
- **F1-Score**: 92.76%
- **ROC-AUC**: 98.45%

### Tempo de Resposta
- **API**: < 200ms
- **Análise NLP**: < 500ms
- **Predição ML**: < 100ms

## 🛠️ Desenvolvimento

### Estrutura de Testes
```
tests/
├── test_nlp_processor.py    # Testes de NLP
└── test_risk_analyzer.py    # Testes de análise de risco
```

### Logs
- Logs centralizados em `logs/`
- Níveis: INFO, WARNING, ERROR
- Rotação automática

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação da API em `http://localhost:8000/docs`

---

**Sistema de Prevenção de Acidentes PRF** - Desenvolvido com ❤️ para a segurança rodoviária brasileira.