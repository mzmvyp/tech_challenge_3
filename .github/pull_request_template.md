# Pull Request Template

## 📝 Descrição

Descreva brevemente as mudanças feitas neste PR.

## 🔧 Tipo de Mudança

- [ ] 🐛 Bug fix (mudança que corrige um problema)
- [ ] ✨ Nova feature (mudança que adiciona funcionalidade)
- [ ] 💥 Breaking change (mudança que quebra funcionalidade existente)
- [ ] 📚 Documentação (mudança apenas na documentação)
- [ ] 🔧 Refatoração (mudança que não adiciona funcionalidade nem corrige bug)
- [ ] ⚡ Performance (mudança que melhora performance)
- [ ] 🧪 Testes (mudança que adiciona ou corrige testes)
- [ ] 🐳 Docker (mudanças relacionadas ao Docker)
- [ ] 🔒 Segurança (mudanças relacionadas à segurança)

## ✅ Checklist

- [ ] Meu código segue as diretrizes de estilo do projeto
- [ ] Realizei uma auto-revisão do meu código
- [ ] Comentei meu código, especialmente em áreas difíceis de entender
- [ ] Fiz as mudanças correspondentes na documentação
- [ ] Minhas mudanças não geram novos warnings
- [ ] Adicionei testes que provam que minha correção é eficaz ou que minha feature funciona
- [ ] Testes novos e existentes passam localmente com minhas mudanças
- [ ] Quaisquer mudanças dependentes foram mergeadas e publicadas
- [ ] Atualizei o CHANGELOG.md (se aplicável)

## 🧪 Como Testar

Descreva os testes que você executou para verificar suas mudanças. Forneça instruções para que possamos reproduzir.

### Testes Locais
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar testes
pytest tests/

# Executar linting
flake8 src/
black --check src/

# Executar sistema
python main.py
```

### Testes de API
```bash
# Testar API
curl http://localhost:8000/

# Testar predição
curl -X POST "http://localhost:8000/prever" \
     -H "Content-Type: application/json" \
     -d '{"dados": "exemplo"}'
```

### Testes de Dashboard
- Acesse http://localhost:8501
- Teste todas as funcionalidades
- Verifique responsividade

## 📸 Screenshots (se aplicável)

Adicione screenshots para ajudar a explicar sua mudança.

### Antes
![Antes](url-da-imagem)

### Depois
![Depois](url-da-imagem)

## 🔗 Issues Relacionadas

Liste as issues que este PR resolve:
- Fixes #(issue)
- Closes #(issue)
- Related to #(issue)

## 📋 Notas Adicionais

Adicione qualquer outra informação relevante sobre o PR aqui.

### Dependências
- [ ] Nenhuma nova dependência
- [ ] Nova dependência adicionada (especificar)
- [ ] Dependência removida (especificar)

### Performance
- [ ] Nenhum impacto na performance
- [ ] Melhoria na performance
- [ ] Possível degradação na performance (explicar)

### Segurança
- [ ] Nenhum impacto na segurança
- [ ] Melhoria na segurança
- [ ] Possível impacto na segurança (explicar)

## 🎯 Reviewers

Mencione os revisores relevantes:
- @mzmvyp

## 📞 Contato

- **Desenvolvedor**: [@mzmvyp](https://github.com/mzmvyp)
- **Email**: [seu-email@exemplo.com](mailto:seu-email@exemplo.com)

---

**Desenvolvido com ❤️ para o Tech Challenge - Fase 3**