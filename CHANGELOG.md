# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- Sistema de previsão de gravidade de acidentes
- API REST com FastAPI
- Dashboard interativo com Streamlit
- Coletor de dados da PRF
- Modelo de Machine Learning treinado
- Documentação completa
- Docker e Docker Compose
- CI/CD com GitHub Actions

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [1.0.0] - 2024-09-17

### Added
- 🚀 Lançamento inicial do projeto
- 📊 Sistema de previsão com 1.4M+ registros reais da PRF
- 🤖 Modelo Random Forest com 72.8% de acurácia
- 🌐 API REST completa com documentação automática
- 📈 Dashboard interativo com visualizações avançadas
- 🔍 Coletor de dados automático da PRF (2007-2025)
- 🐳 Containerização com Docker
- 📚 Documentação completa e README detalhado
- 🔧 CI/CD com GitHub Actions
- 🧪 Testes automatizados
- 📋 Templates para issues e PRs
- 🎯 Sistema de recomendações baseado em fatores de risco

### Technical Details
- **Dados**: 1.449.933 registros reais da PRF
- **Período**: 2007-2025 (19 anos)
- **Modelo**: Random Forest Classifier
- **Acurácia**: 72.8%
- **Features**: 71 características processadas
- **Classes**: 4 níveis de gravidade
- **API**: FastAPI com validação Pydantic
- **Dashboard**: Streamlit com Plotly
- **Deploy**: Docker + Docker Compose

### Performance
- Tempo de treinamento: ~2 minutos
- Tempo de predição: <100ms
- Suporte a 1000+ requisições/minuto
- Interface responsiva e otimizada

### Documentation
- README completo com instruções de instalação
- Documentação da API (Swagger/OpenAPI)
- Guia de contribuição
- Código de conduta
- Changelog detalhado
- Templates para issues e PRs

---

## Como Contribuir

Para adicionar uma nova entrada no changelog:

1. Adicione sua mudança na seção `[Unreleased]`
2. Use as categorias: Added, Changed, Deprecated, Removed, Fixed, Security
3. Siga o formato existente
4. Inclua detalhes técnicos quando relevante

## Formato das Versões

- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Funcionalidades adicionadas de forma compatível
- **PATCH**: Correções de bugs compatíveis

## Links

- [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)
- [Versionamento Semântico](https://semver.org/lang/pt-BR/)
- [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/)
