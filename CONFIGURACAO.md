# Guia de Configuração e Execução do DB-GPT TELA Edition

Este guia explica como configurar e executar o projeto DB-GPT TELA Edition usando SQLite, MySQL ou PostgreSQL como banco de dados.

## Pré-requisitos

- Python 3.9 ou superior
- UV (gerenciador de pacotes Python)
- SQLite, MySQL ou PostgreSQL (dependendo da sua escolha de banco de dados)

## Configuração do Ambiente

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/NLP2DB-MRAG.git
cd NLP2DB-MRAG
```

### 2. Configuração do arquivo .env

Crie um arquivo `.env` na raiz do projeto com o conteúdo apropriado para o banco de dados que deseja usar:

#### Para SQLite:

```
TELA_API_KEY=your_api_key_here
TELA_PROJECT=your_project_here
TELA_ORG=your_org_here
TELA_MODEL=qwen-3-235b-a22b-instruct
TELA_EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5

# Configurações da aplicação
LANGUAGE=pt
WEB_SERVER_PORT=7861
DEBUG_MODE=True
TEMPERATURE=0.15

# Configuração do banco de dados
DB_TYPE=sqlite
DB_PATH=data/faturamento.db
DB_NAME=db_faturamento

# Configurações do Vector Store
VECTOR_STORE_TYPE=Chroma
KNOWLEDGE_CHUNK_SIZE=200
KNOWLEDGE_SEARCH_TOP_SIZE=10
```

#### Para MySQL:

```
TELA_API_KEY=your_api_key_here
TELA_PROJECT=your_project_here
TELA_ORG=your_org_here
TELA_MODEL=qwen-3-235b-a22b-instruct
TELA_EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5

# Configurações da aplicação
LANGUAGE=pt
WEB_SERVER_PORT=7861
DEBUG_MODE=True
TEMPERATURE=0.15

# Configuração do banco de dados MySQL
DB_TYPE=mysql
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=3306
LOCAL_DB_USER=root
LOCAL_DB_PASSWORD=rootpass123

# Configurações do Vector Store
VECTOR_STORE_TYPE=Chroma
KNOWLEDGE_CHUNK_SIZE=200
KNOWLEDGE_SEARCH_TOP_SIZE=10
```

#### Para PostgreSQL:

```
TELA_API_KEY=your_api_key_here
TELA_PROJECT=your_project_here
TELA_ORG=your_org_here
TELA_MODEL=qwen-3-235b-a22b-instruct
TELA_EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5

# Configurações da aplicação
LANGUAGE=pt
WEB_SERVER_PORT=7861
DEBUG_MODE=True
TEMPERATURE=0.15

# Configuração do banco de dados PostgreSQL
DB_TYPE=postgres
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=5432
LOCAL_DB_USER=postgres
LOCAL_DB_PASSWORD=1234
LOCAL_DB_DATABASE=postgres

# Configurações do Vector Store
VECTOR_STORE_TYPE=Chroma
KNOWLEDGE_CHUNK_SIZE=200
KNOWLEDGE_SEARCH_TOP_SIZE=10
```

Substitua `your_api_key_here`, `your_project_here` e `your_org_here` com suas credenciais TELA.

### 3. Instalação de dependências

Instale as dependências usando UV:

```bash
uv venv
uv pip install -r requirements.txt
```

### 4. Dependências adicionais

Algumas dependências adicionais podem ser necessárias:

```bash
uv pip install gtts nltk pymilvus weaviate-client chromadb pydantic==1.10.8
```

### 5. Configuração do banco de dados

#### Para SQLite:

Execute o script de configuração do banco de dados SQLite:

```bash
uv run setup_sqlite_db.py
```

#### Para MySQL:

1. Certifique-se de que o servidor MySQL esteja em execução
2. Crie um banco de dados para o projeto:

```bash
mysql -u root -p
```

No prompt do MySQL:

```sql
CREATE DATABASE db_faturamento;
EXIT;
```

3. Execute o script de configuração do banco de dados MySQL:

```bash
uv run setup_db.py
```

#### Para PostgreSQL:

1. Certifique-se de que o servidor PostgreSQL esteja em execução
2. O banco de dados padrão `postgres` já deve existir, mas você pode criar um banco de dados específico se desejar:

```bash
psql -U postgres
```

No prompt do PostgreSQL:

```sql
CREATE DATABASE db_faturamento;
\q
```

3. Execute o script de configuração do banco de dados:

```bash
uv run setup_db.py
```

## Execução do Projeto

Para iniciar o servidor:

```bash
uv run run.py
```

O servidor estará disponível em `http://localhost:7861`.

## Solução de Problemas Comuns

### Porta em uso

Se a porta 7861 já estiver em uso, você pode alterá-la no arquivo `.env`:

```
WEB_SERVER_PORT=7862
```

### Erro de inicialização do NiceGUI

Se encontrar erros relacionados à inicialização do NiceGUI, verifique se o arquivo `run.py` contém:

```python
if __name__ in {'__main__', '__mp_main__'}:
    main()
```

### Erros de SQL

#### SQLite
O SQLite não suporta alguns comandos SQL como `USE database_name`. As adaptações necessárias já foram feitas no código para contornar essas limitações.

#### MySQL
Para MySQL, certifique-se de que:
1. O servidor MySQL esteja em execução
2. As credenciais no arquivo `.env` estejam corretas
3. O usuário tenha permissões adequadas para o banco de dados

#### PostgreSQL
Para PostgreSQL, certifique-se de que:
1. O servidor PostgreSQL esteja em execução
2. As credenciais no arquivo `.env` estejam corretas
3. O usuário tenha permissões adequadas para o banco de dados
4. O banco de dados especificado em `LOCAL_DB_DATABASE` exista

## Estrutura do Projeto

- `pilot/`: Contém o código principal do projeto
  - `connections/`: Módulos de conexão com bancos de dados
  - `web/`: Interface web usando NiceGUI
  - `configs/`: Configurações do projeto

## Recursos Adicionais

- Consulte a documentação em `docs/` para mais informações
- Para dúvidas específicas sobre o SQLite, consulte [a documentação oficial](https://www.sqlite.org/docs.html)
- Para dúvidas específicas sobre o MySQL, consulte [a documentação oficial do MySQL](https://dev.mysql.com/doc/)
- Para dúvidas específicas sobre o PostgreSQL, consulte [a documentação oficial do PostgreSQL](https://www.postgresql.org/docs/)

## Alternando entre SQLite, MySQL e PostgreSQL

Para alternar entre os diferentes bancos de dados, basta modificar o arquivo `.env` com as configurações apropriadas e reiniciar o aplicativo. Você pode manter diferentes arquivos de configuração (como `.env.sqlite`, `.env.mysql` e `.env.postgres`) e copiar o desejado para `.env` quando quiser alternar.

```bash
# Para usar SQLite
cp .env.sqlite .env

# Para usar MySQL
cp .env.mysql .env

# Para usar PostgreSQL
cp .env.postgres .env
```
