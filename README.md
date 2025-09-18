# 🚨 Sistema de Previsão de Gravidade de Acidentes - PRF

Sistema inteligente de Machine Learning para análise e previsão da gravidade de acidentes em rodovias federais brasileiras, utilizando dados reais da Polícia Rodoviária Federal (PRF).

## 📊 Sobre o Projeto

Este projeto foi desenvolvido para o **Tech Challenge - Fase 3** e implementa um sistema completo de análise preditiva de acidentes rodoviários, incluindo:

- **Coleta de dados** reais da PRF (2007-2025)
- **Modelo de Machine Learning** treinado com 1.4M+ registros
- **API REST** para predições em tempo real
- **Dashboard interativo** com visualizações avançadas
- **Sistema de recomendações** baseado em fatores de risco

## 🎯 Funcionalidades

### 🤖 Modelo de Machine Learning
- **Algoritmo**: Random Forest Classifier
- **Dados**: 1.449.933 registros reais da PRF
- **Período**: 2007-2025 (19 anos)
- **Acurácia**: 72.8%
- **Classes**: 4 níveis de gravidade
  - Ileso/Sem Vítimas
  - Feridos Leves
  - Feridos Graves
  - Fatal/Óbitos

### 📈 Dashboard Interativo
- Visualizações em tempo real
- Filtros por período, estado e gravidade
- Métricas de performance
- Análise temporal e geográfica
- Interface responsiva e intuitiva

### 🔗 API REST
- Endpoints para predição de gravidade
- Validação de dados com Pydantic
- Documentação automática (Swagger)
- Sistema de recomendações
- Análise de fatores de risco

## 🚀 Instalação e Uso

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)

### 1. Clone o repositório
```bash
git clone https://github.com/mzmvyp/tech_challenge_3.git
cd tech_challenge_3
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Treine o modelo (primeira execução)
```bash
python treinar_modelo.py
```

### 4. Execute o sistema
```bash
python main.py
```

### 5. Acesse as interfaces
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs

## 📁 Estrutura do Projeto

```
tech_challenge_3/
├── 📊 data/
│   ├── raw/                    # Dados brutos da PRF
│   └── models/                 # Modelos treinados
├── 🧠 src/
│   ├── api_predicao.py         # API FastAPI
│   ├── dashboard.py            # Dashboard Streamlit
│   ├── prf_scraper_2025.py     # Coletor de dados PRF
│   ├── train_model.py          # Treinamento de modelos
│   └── utils/
│       └── preprocessing.py    # Preprocessamento de dados
├── 📓 notebooks/
│   └── 01_exploracao_dados.ipynb
├── 🐳 docker-compose.yml       # Containerização
├── 🐳 Dockerfile
├── 📋 requirements.txt         # Dependências
├── 🚀 main.py                  # Execução principal
├── 🤖 treinar_modelo.py        # Treinamento
└── 📖 README.md
```

## 🔧 Tecnologias Utilizadas

### Backend
- **Python 3.8+**
- **FastAPI** - Framework web moderno
- **scikit-learn** - Machine Learning
- **pandas** - Manipulação de dados
- **numpy** - Computação numérica

### Frontend
- **Streamlit** - Dashboard interativo
- **Plotly** - Visualizações avançadas
- **HTML/CSS** - Interface customizada

### Dados
- **Dados reais da PRF** (2007-2025)
- **1.4M+ registros** de acidentes
- **19 anos** de dados históricos
- **4 classes** de gravidade

## 📊 Dados Utilizados

O sistema utiliza dados reais da Polícia Rodoviária Federal, incluindo:

- **Período**: 2007-2025
- **Registros**: 1.449.933 acidentes
- **Estados**: Todos os estados brasileiros
- **BRs**: Principais rodovias federais
- **Variáveis**: 17 características por acidente

### Principais Variáveis
- Data e horário do acidente
- Localização (UF, BR, KM, município)
- Tipo de ocorrência e causa
- Veículos e pessoas envolvidas
- Condições meteorológicas
- Classificação da gravidade

## 🎯 Como Usar

### 1. Fazer uma Predição
Acesse o dashboard em http://localhost:8501 e use o formulário de previsão:

1. Preencha as informações do acidente
2. Clique em "Prever Gravidade"
3. Visualize a predição e recomendações

### 2. Usar a API
```python
import requests

# Exemplo de predição via API
dados = {
    "dia_semana": "SEXTA",
    "horario": "18:30:00",
    "condicao_metereologica": "CHUVA",
    "tipo_pista": "DUPLA",
    "tracado_via": "RETA",
    "tipo_ocorrencia": "COLISÃO FRONTAL",
    "causa_acidente": "VELOCIDADE",
    "tipo_veiculo": "AUTOMÓVEL",
    "br": 101,
    "km": 150.5,
    "uf": "SP",
    "municipio": "CAMPINAS",
    "pessoas": 3,
    "veiculos": 2
}

response = requests.post("http://localhost:8000/prever", json=dados)
resultado = response.json()
```

## 📈 Performance do Modelo

- **Acurácia**: 72.8%
- **F1-Score**: 0.73
- **Precisão**: 0.74
- **Recall**: 0.73

### Features Mais Importantes
1. Ocupação média (pessoas/veículos)
2. Número de veículos
3. Quilometragem
4. Número da BR
5. Condições meteorológicas

## 🐳 Docker

### Executar com Docker Compose
```bash
docker-compose up -d
```

### Executar apenas o container
```bash
docker build -t prf-accidents .
docker run -p 8000:8000 -p 8501:8501 prf-accidents
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ⚠️ Aviso Importante

Este sistema é desenvolvido para fins **educacionais e de demonstração**. Não substitui análises oficiais da PRF e não deve ser usado para tomada de decisões críticas em segurança viária.

## 📞 Contato

- **Desenvolvedor**: [mzmvyp](https://github.com/mzmvyp)
- **Projeto**: [Tech Challenge 3](https://github.com/mzmvyp/tech_challenge_3)
- **Dados**: [Polícia Rodoviária Federal](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf)

## 🙏 Agradecimentos

- Polícia Rodoviária Federal (PRF) pelos dados abertos
- Comunidade Python e Streamlit
- FastAPI e scikit-learn
- Todos os contribuidores do projeto

---

**Desenvolvido com ❤️ para o Tech Challenge - Fase 3**