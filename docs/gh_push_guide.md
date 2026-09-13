# Guia Rápido: Push para GitHub

## Opção 1: Usar GitHub CLI (Recomendado)

### 1. Instalar GitHub CLI (se não tiver):
```bash
# Ubuntu/Debian
sudo apt install gh

# macOS
brew install gh

# Windows
choco install gh
```

### 2. Autenticar no GitHub:
```bash
gh auth login
```

Siga as instruções:
- Selecione "GitHub.com"
- Escolha login via navegador
- Copie o código e abra no navegador
- Autorize o acesso

### 3. Fazer push:
```bash
cd /home/cesar/GCP_projects/customer-experience
git push -u origin main
```

## Opção 2: Usar Personal Access Token

### 1. Criar um token no GitHub:
1. Acesse https://github.com/settings/tokens
2. Clique em "Generate new token" → "Generate new token (classic)"
3. Configure:
   - Name: "GCP-Airflow-project"
   - Expiration: 30 days (recomendado)
   - Selecionar scopes: `repo` (full control of private repositories)
4. Clique em "Generate token"
5. Copie o token (não mostre para ninguém!)

### 2. Configurar credenciais:
```bash
cd /home/cesar/GCP_projects/customer-experience

# Armazenar credenciais (não esqueça de usar o token como senha)
git config --global credential.helper store

# Executar qualquer comando git para pedir credenciais
git ls-remote origin
```

Quando pedir username: `cesaraugustobr2014-oss`
Quando pedir password: cole seu token

### 3. Fazer push:
```bash
git push -u origin main
```

## Verificar se funcionou

```bash
# Verificar remotes
git remote -v

# Verificar branch
git branch -vv

# Ver histórico
git log --oneline
```

Acessar: https://github.com/cesaraugustobr2014-oss/GCP_Airflow_project
