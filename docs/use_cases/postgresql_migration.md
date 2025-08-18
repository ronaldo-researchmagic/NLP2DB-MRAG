# Migração para PostgreSQL

Este documento descreve o processo de migração do DB-GPT TELA Edition do MySQL para o PostgreSQL, incluindo os problemas encontrados e suas soluções.

## Problemas e Soluções

### 1. Erro no Carregamento de Templates de Prompt

**Problema:**

Ao migrar para PostgreSQL, o chat apresentava o erro `'NoneType' object has no attribute 'response_format'`. Este erro ocorria porque os templates de prompt não estavam sendo carregados antes do uso do chat.

**Solução:**

Foi criada uma função auxiliar `ensure_prompt_templates_loaded()` no módulo `pilot.scene.chat_db.auto_execute.chat_fix` que importa todos os módulos de prompt necessários para garantir que eles sejam carregados e registrados no dicionário `CFG.prompt_templates` antes do uso do chat.

```python
# Exemplo de uso
from pilot.scene.chat_db.auto_execute.chat_fix import ensure_prompt_templates_loaded

# Carregar templates antes de usar o chat
ensure_prompt_templates_loaded()
```

### 2. Consulta SQL Incompatível no PostgreSQL

**Problema:**

O método `table_simple_info` na classe `SQLDatabase` usava uma consulta SQL que não era totalmente compatível com PostgreSQL, resultando em erros ao tentar obter informações sobre as tabelas.

**Solução:**

A consulta SQL foi modificada para ser compatível com PostgreSQL, usando o esquema 'public' e formatando corretamente os resultados:

```python
# Para PostgreSQL
_sql = f"""
    SELECT table_name, '(' || string_agg(column_name, ',') || ')' as columns
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    GROUP BY table_name;
"""
```

### 3. Tratamento de Esquemas no PostgreSQL

**Problema:**

No PostgreSQL, os bancos de dados são tratados como esquemas, e o esquema padrão é 'public'. Era necessário adaptar o código para usar corretamente os esquemas do PostgreSQL.

**Solução:**

O código foi modificado para tratar o esquema 'public' como o esquema padrão no PostgreSQL, e para usar o search_path corretamente:

```python
# Exemplo de definição do search_path
session.execute(text(f"SET search_path TO {schema_name}"))
```

### 4. Comando 'USE' Incompatível com PostgreSQL

**Problema:**

O comando SQL `USE database_name` é específico do MySQL e não existe no PostgreSQL, causando erros de sintaxe quando executado em um banco de dados PostgreSQL.

**Solução:**

Foram feitas modificações em vários arquivos para tratar corretamente o comando `USE` dependendo do tipo de banco de dados:

1. Na classe `RDBMSDatabase` (arquivo `pilot/connections/rdbms/rdbms_connect.py`), o método `run` foi modificado para detectar comandos `USE` e convertê-los para `SET search_path TO` quando o banco de dados é PostgreSQL:

```python
def run(self, session, command: str, fetch: str = "all") -> List:
    # Verificar se o comando é 'use' e tratar de acordo com o tipo de banco de dados
    import re
    use_match = re.match(r"^\s*use\s+[`'\"]?([^`'\"]+)[`'\"]?\s*$", command, re.IGNORECASE)
    
    if use_match:
        db_name = use_match.group(1)
        # Tratar o comando 'use' de acordo com o tipo de banco de dados
        if 'postgresql' in self._engine.dialect.name.lower() or 'postgres' in self._engine.dialect.name.lower():
            # Para PostgreSQL, usar SET search_path
            command = f"SET search_path TO {db_name}"
        elif 'sqlite' in self._engine.dialect.name.lower():
            # SQLite não precisa do comando 'use'
            return []
    
    # Continua com a execução normal do comando
    # ...
```

2. Na classe `Database` (arquivo `pilot/common/sql_database.py`), o método `run_sql` foi modificado para usar o comando apropriado dependendo do tipo de banco de dados:

```python
def run_sql(self, sql_query, db_name="main"):
    try:
        session = self._db_sessions()
        if 'sqlite' in self._engine.name.lower():
            pass
        elif 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            try:
                session.execute(text(f"SET search_path TO {db_name}"))
            except Exception as e:
                import logging
                logging.warning(f"Erro ao definir search_path para {db_name}: {e}")
                session.rollback()
                session.execute(text("SET search_path TO public"))
        else:
            try:
                session.execute(text(f"use `{db_name}`"))
            except Exception as e:
                import logging
                logging.warning(f"Erro ao usar banco de dados {db_name}: {e}")
        # Continua com a execução da consulta
        # ...
```

3. O método `run` na classe `Database` também foi modificado para tratar comandos `USE` diretamente enviados pelo usuário ou pelo modelo de linguagem:

```python
def run(self, session, command: str, fetch: str = "all") -> List:
    # Verificar se o comando é 'use' e tratar de acordo com o tipo de banco de dados
    import re
    use_match = re.match(r"^\s*use\s+[`'\"]?([^`'\"]+)[`'\"]?\s*;?\s*$", command, re.IGNORECASE)
    
    if use_match:
        db_name = use_match.group(1)
        # Tratar o comando 'use' de acordo com o tipo de banco de dados
        if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            # Para PostgreSQL, usar SET search_path
            command = f"SET search_path TO {db_name}"
            print(f"Convertendo 'use {db_name}' para 'SET search_path TO {db_name}' para PostgreSQL")
        elif 'sqlite' in self._engine.name.lower():
            # SQLite não precisa do comando 'use'
            print(f"Ignorando comando 'use {db_name}' para SQLite")
            return []
    
    # Continua com a execução normal do comando
    # ...
```

4. Também foi corrigido o método `parse_prompt_response` no arquivo `pilot/scene/chat_db/auto_execute/out_parser.py` para lidar corretamente com respostas JSON do modelo de linguagem, evitando erros quando a resposta já é um dicionário Python:

```python
def parse_prompt_response(self, model_out_text):
    clean_str = super().parse_prompt_response(model_out_text)
    print("clean prompt response:", clean_str)
    
    # Verificar se clean_str já é um dicionário
    if isinstance(clean_str, dict):
        response = clean_str
    else:
        # Tentar carregar como JSON string
        try:
            response = json.loads(clean_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Erro ao processar resposta JSON: {e}")
            # Fallback para um formato básico
            response = {"sql": "SELECT 1;", "thoughts": "Erro ao processar resposta."}
    
    sql, thoughts = response["sql"], response["thoughts"]
    return SqlAction(sql, thoughts)
```

## Recomendações para Uso com PostgreSQL

1. **Inicialização de Templates de Prompt:**
   - Sempre chame `ensure_prompt_templates_loaded()` antes de usar qualquer funcionalidade de chat.

2. **Esquemas e Bancos de Dados:**
   - No PostgreSQL, use o esquema 'public' como equivalente ao banco de dados principal.
   - Ao criar novos esquemas, use `CREATE SCHEMA nome_esquema` em vez de `CREATE DATABASE`.

3. **Consultas SQL:**
   - Adapte as consultas SQL para usar a sintaxe do PostgreSQL, especialmente para funções de agregação e concatenação.
   - Use `string_agg()` em vez de `group_concat()` para concatenação de strings.
   - Use o operador `||` para concatenação de strings em vez da função `concat()`.
   - Substitua o comando `USE database_name` do MySQL por `SET search_path TO schema_name` no PostgreSQL.
   - Evite usar crase (`) para delimitar nomes de tabelas ou colunas; use aspas duplas (") se necessário.
   - **Importante:** Especifique o esquema `public` explicitamente nas consultas SQL para evitar erros de tabela não encontrada. Por exemplo, use `FROM public.tabela` em vez de apenas `FROM tabela`.

4. **Tratamento do Comando USE:**
   - Não use o comando `USE database_name` diretamente em consultas SQL para PostgreSQL.
   - O sistema agora converte automaticamente comandos `USE` para `SET search_path TO` quando detecta que o banco de dados é PostgreSQL.
   - Para mudar de esquema manualmente, use `SET search_path TO nome_esquema`.
   - Lembre-se que no PostgreSQL, o equivalente a um banco de dados do MySQL é um esquema, e o esquema padrão é `public`.

5. **Tratamento de Erros:**
   - O sistema foi modificado para tratar erros de sintaxe relacionados ao comando `USE` em PostgreSQL.
   - Se ocorrerem erros ao executar consultas SQL, verifique se não há comandos específicos do MySQL sendo usados.
   - Os logs do sistema agora mostram mensagens informativas quando um comando `USE` é convertido para `SET search_path TO`.

### Exemplo de consulta SQL com esquema explícito

```sql
-- Consulta com esquema explícito (recomendado para PostgreSQL)
SELECT 
    c.cliente_nome,
    c.cliente_loja,
    SUM(i.receita_liquida_item) AS receita_liquida_total
FROM public.ft_faturamento_itens i
JOIN public.ft_faturamento_cabecalho c
ON (c.filial, c.nf_numero, c.nf_serie) = (i.filial, i.nf_numero, i.nf_serie)
GROUP BY c.cliente_nome, c.cliente_loja
ORDER BY receita_liquida_total DESC
LIMIT 10;
```

## Script de Inicialização

Para garantir que todos os templates de prompt sejam carregados corretamente, foi criado um script de inicialização em `pilot/initialize.py` que carrega automaticamente todos os templates de prompt necessários.

### Como usar o script de inicialização

```python
# Importar o módulo de inicialização
from pilot.initialize import initialize_app

# Inicializar a aplicação (carregar templates de prompt)
initialize_app()

# Agora você pode usar os chats sem o erro 'NoneType' object has no attribute 'response_format'
```

Alternativamente, você pode usar a função `ensure_prompt_templates_loaded()` diretamente:

```python
from pilot.initialize import ensure_prompt_templates_loaded

# Carregar templates de prompt
ensure_prompt_templates_loaded()
```

### Execução direta do script

Você também pode executar o script diretamente para verificar se os templates estão sendo carregados corretamente:

```bash
python -m pilot.initialize
```

O script irá exibir informações sobre os templates carregados e alertar sobre quaisquer problemas encontrados.
