# Guia de Contribuição

Obrigado por considerar contribuir para o Sistema de Previsão de Acidentes PRF! 🚨

## Como Contribuir

### 1. Fork e Clone

1. Faça um fork do repositório
2. Clone seu fork localmente:
   ```bash
   git clone https://github.com/SEU_USUARIO/tech_challenge_3.git
   cd tech_challenge_3
   ```

### 2. Configurar Ambiente

1. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Para desenvolvimento
   ```

3. Instale pre-commit hooks:
   ```bash
   pre-commit install
   ```

### 3. Criar Branch

```bash
git checkout -b feature/nova-funcionalidade
# ou
git checkout -b bugfix/corrigir-problema
```

### 4. Desenvolver

- Faça suas mudanças
- Siga as convenções de código
- Adicione testes se necessário
- Atualize documentação

### 5. Testar

```bash
# Executar testes
pytest tests/

# Verificar linting
flake8 src/
black --check src/

# Verificar tipos
mypy src/
```

### 6. Commit

```bash
git add .
git commit -m "feat: adiciona nova funcionalidade X"
```

### 7. Push e Pull Request

```bash
git push origin feature/nova-funcionalidade
```

Depois crie um Pull Request no GitHub.

## Convenções de Código

### Python

- Siga PEP 8
- Use type hints
- Documente funções e classes
- Use nomes descritivos

### Commits

Use o padrão Conventional Commits:

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` mudanças na documentação
- `style:` formatação, ponto e vírgula, etc.
- `refactor:` refatoração de código
- `test:` adicionar ou corrigir testes
- `chore:` mudanças em ferramentas, configurações, etc.

### Exemplos

```bash
git commit -m "feat: adiciona endpoint para estatísticas"
git commit -m "fix: corrige erro de validação de dados"
git commit -m "docs: atualiza README com instruções de instalação"
```

## Estrutura do Projeto

```
tech_challenge_3/
├── src/                    # Código fonte
│   ├── api_predicao.py     # API FastAPI
│   ├── dashboard.py        # Dashboard Streamlit
│   ├── prf_scraper_2025.py # Coletor de dados
│   └── utils/              # Utilitários
├── tests/                  # Testes
├── data/                   # Dados (ignorado pelo Git)
├── docs/                   # Documentação
└── notebooks/              # Jupyter notebooks
```

## Tipos de Contribuição

### 🐛 Reportar Bugs

1. Verifique se o bug já foi reportado
2. Use o template de bug report
3. Inclua informações detalhadas

### ✨ Sugerir Features

1. Verifique se a feature já foi sugerida
2. Use o template de feature request
3. Descreva o problema e a solução

### 🔧 Contribuir com Código

1. Escolha uma issue ou crie uma nova
2. Siga o processo de desenvolvimento
3. Crie um Pull Request

### 📚 Melhorar Documentação

1. Identifique áreas de melhoria
2. Faça as mudanças necessárias
3. Crie um Pull Request

## Processo de Review

1. **Automatic Checks**: CI/CD verifica automaticamente
2. **Code Review**: Mantenedores revisam o código
3. **Testing**: Testes são executados
4. **Merge**: Após aprovação, o PR é mergeado

## Dúvidas?

- Abra uma issue para perguntas
- Use as discussões do GitHub
- Entre em contato com os mantenedores

## Agradecimentos

Obrigado por contribuir! Sua ajuda é muito valiosa para o projeto. 🙏
