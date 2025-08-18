# Migração para PostgreSQL - Documentação

## Visão Geral
Este documento descreve as alterações realizadas para migrar o DB-GPT TELA Edition de MySQL para PostgreSQL, incluindo os problemas encontrados e as soluções implementadas.

## Problemas Encontrados

### 1. Erro: 'Database' object has no attribute 'engine'
O erro ocorria porque a classe `Database` no arquivo `pilot/common/sql_database.py` tinha um atributo privado `_engine`, mas não expunha uma propriedade pública `engine` para acesso externo. Algumas partes do código tentavam acessar `database.engine` diretamente.

### 2. Método `run_sql` não definido
A classe `Database` não possuía um método `run_sql` que era chamado em alguns scripts de teste.

### 3. Esquema de tabelas diferente
As consultas SQL precisaram ser ajustadas para o esquema específico do PostgreSQL, que difere do MySQL em alguns aspectos.

### 4. Comando SQL incompatível para mudança de banco de dados
O comando `USE database_name` é específico do MySQL e não funciona no PostgreSQL. No PostgreSQL, o equivalente é `SET search_path TO schema_name`.

### 5. Comando para listar bancos de dados incompatível
O comando `SHOW DATABASES` é específico do MySQL e não funciona no PostgreSQL. No PostgreSQL, é necessário consultar as tabelas do sistema para listar os esquemas disponíveis.

### 6. Tratamento do esquema 'main' inexistente no PostgreSQL
O código fazia referência ao esquema 'main' que é comumente usado em MySQL/SQLite, mas não existe por padrão no PostgreSQL, onde o esquema padrão é 'public'.

### 7. Funções de concatenação incompatíveis
O MySQL usa a função `GROUP_CONCAT` e `CONCAT` para concatenação de strings, enquanto o PostgreSQL usa `STRING_AGG` e o operador `||`.

## Soluções Implementadas

### 1. Adição da propriedade `engine` na classe `Database`
Foi adicionada uma propriedade `engine` à classe `Database` para expor o atributo privado `_engine`:

```python
@property
def engine(self):
    """Propriedade para acessar o engine do SQLAlchemy."""
    return self._engine
```

### 2. Implementação do método `run_sql`
Foi implementado o método `run_sql` na classe `Database` para executar consultas SQL diretamente:

```python
def run_sql(self, sql_query):
    """Execute uma consulta SQL e retorna o resultado.
    
    Args:
        sql_query (str): Consulta SQL a ser executada
        
    Returns:
        list: Resultado da consulta
    """
    try:
        session = self._db_sessions()
        cursor = session.execute(text(sql_query))
        if cursor.returns_rows:
            result = cursor.fetchall()
            return result
        else:
            session.commit()
            return None
    except Exception as e:
        import logging
        logging.error(f"Erro ao executar consulta SQL: {e}")
        session.rollback()
        raise
```

### 3. Ajuste das consultas SQL
As consultas SQL foram ajustadas para o esquema do PostgreSQL, utilizando os nomes corretos das colunas e tabelas:

- Substituição de `data_emissao` por `dt_emissao_nf`
- Substituição de `valor_total` por `nf_valor_bruto`
- Ajuste na junção entre tabelas, utilizando as chaves corretas (`nf_numero`, `nf_serie`, `filial`)

### 4. Correção do método `get_session` na classe `Database`
O método `get_session` na classe `Database` foi modificado para usar o comando correto para mudança de esquema no PostgreSQL, com tratamento especial para o esquema 'main' (mapeando para 'public') e verificação da existência do esquema antes de executar o comando:

```python
def get_session(self, db_name: str):
    session = self._db_sessions()

    self._metadata = MetaData()
    # Para SQLite, não precisamos mudar de banco de dados com 'use'
    # Para PostgreSQL, usamos SET search_path
    # Para outros bancos como MySQL, usamos o comando 'use'
    try:
        if 'sqlite' in self._engine.name.lower():
            # SQLite não precisa do comando 'use'
            pass
        elif 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            # Para PostgreSQL
            # Tratar o caso especial do 'main' que não existe no PostgreSQL
            schema_name = 'public' if db_name.lower() == 'main' else db_name
            
            # Verificar se o esquema existe
            check_sql = text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = :schema_name
                """)
            result = session.execute(check_sql, {"schema_name": schema_name}).fetchone()
            
            if result:
                # O esquema existe, definir o search_path
                sql = text(f"SET search_path TO {schema_name}")
                session.execute(sql)
            else:
                # Se o esquema não existir e for diferente de 'public', tentar usar 'public'
                if schema_name != 'public':
                    logging.warning(f"Esquema '{schema_name}' não encontrado, usando 'public' como fallback")
                    sql = text("SET search_path TO public")
                    session.execute(sql)
        else:
            # Para outros bancos como MySQL
            sql = text(f"use `{db_name}`")
            session.execute(sql)

        # Refletir metadados do banco
        if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            schema_name = 'public' if db_name.lower() == 'main' else db_name
            self._metadata.reflect(bind=self._engine, schema=schema_name)
        else:
            self._metadata.reflect(bind=self._engine)
    except Exception as e:
        logging.error(f"Erro ao configurar sessão para '{db_name}': {e}")
        session.rollback()
        raise
    
    return session
```

### 5. Correção do método `get_database_list` para listar esquemas no PostgreSQL
O método foi atualizado para consultar os esquemas disponíveis no PostgreSQL em vez de usar o comando `SHOW DATABASES`:

```python
def get_database_list(self):
    """Retorna a lista de bancos de dados disponíveis."""
    try:
        session = self._db_sessions()
        
        if 'sqlite' in self._engine.name.lower():
            # Para SQLite, retornamos apenas 'main'
            return ['main']
        elif 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            # Para PostgreSQL, consultamos os esquemas disponíveis
            sql = text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                """)
            result = session.execute(sql).fetchall()
            schemas = [row[0] for row in result]
            
            # Se não houver esquemas personalizados, retornar pelo menos 'public'
            if not schemas:
                return ['public']
            return schemas
        else:
            # Para outros bancos como MySQL
            sql = text("SHOW DATABASES")
            result = session.execute(sql).fetchall()
            return [row[0] for row in result]
    except Exception as e:
        logging.error(f"Erro ao listar bancos de dados: {e}")
        return []
```

### 6. Correção do método `table_simple_info` para usar funções compatíveis com PostgreSQL
O método foi atualizado para usar funções de concatenação compatíveis com PostgreSQL:

```python
def table_simple_info(self, db_name):
    """Retorna informações simples sobre as tabelas do banco de dados."""
    try:
        session = self.get_session(db_name)
        
        if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            # Para PostgreSQL
            schema_name = 'public' if db_name.lower() == 'main' else db_name
            sql = text(f"""
                SELECT table_name || '(' || string_agg(column_name, ',') || ')' as schema_info 
                FROM information_schema.columns 
                WHERE table_schema = '{schema_name}' 
                GROUP BY table_name;
            """)
        else:
            # Para MySQL e outros
            sql = text(f"""
                SELECT CONCAT(table_name, '(', GROUP_CONCAT(column_name), ')') as schema_info 
                FROM information_schema.columns 
                WHERE table_schema = '{db_name}' 
                GROUP BY table_name;
            """)
            
        result = session.execute(sql).fetchall()
        return [row[0] for row in result]
    except Exception as e:
        logging.error(f"Erro ao obter informações das tabelas: {e}")
        return []
```

## Scripts de Teste Criados

### 1. `test_sql_query.py`
Testa a conexão com o banco de dados e executa uma consulta simples para contar notas fiscais.

### 2. `fix_database_engine.py`
Script para adicionar automaticamente a propriedade `engine` à classe `Database`.

### 3. `test_model_sql_generation.py`
Testa a interação com o modelo para gerar SQL (encontrou problemas de importação).

### 4. `test_sql_generation.py`
Testa a classe `Database` e a execução de consultas SQL.

### 5. `check_table_schema.py`
Verifica o esquema das tabelas no PostgreSQL para entender a estrutura correta.

### 6. `test_model_sql_query.py`
Testa a execução de várias consultas SQL ajustadas para o esquema do PostgreSQL.

### 7. `test_chat_functionality.py`
Testa a funcionalidade do chat com banco PostgreSQL, incluindo listagem de bancos (esquemas), criação de sessão e execução de consultas.

### 8. `test_db_session.py`
Testa especificamente a funcionalidade de sessão de banco de dados, verificando a listagem de esquemas e a obtenção de sessões para 'main' e 'public'.

## Configuração do Ambiente

### Variáveis de Ambiente para PostgreSQL
```
DB_TYPE=postgres
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=5432
LOCAL_DB_USER=postgres
LOCAL_DB_PASSWORD=1234
LOCAL_DB_DATABASE=postgres
```

## Próximos Passos

1. ✅ Verificar se todas as partes da aplicação estão utilizando corretamente a classe `Database`
2. ✅ Realizar testes mais abrangentes com diferentes tipos de consultas
3. Otimizar as consultas SQL para melhor desempenho no PostgreSQL
4. Implementar índices e chaves estrangeiras no banco de dados PostgreSQL para melhorar o desempenho e a integridade dos dados
5. ✅ Revisar todos os comandos SQL específicos do MySQL e substituí-los por equivalentes do PostgreSQL
6. Considerar o uso de funções específicas do PostgreSQL para melhorar o desempenho (como índices GIN para busca textual)
7. ✅ Implementar tratamento adequado para esquemas no PostgreSQL (equivalentes aos bancos de dados no MySQL)
8. ✅ Revisar e atualizar os métodos que dependem de funções específicas do MySQL como `DATABASE()` para usar equivalentes do PostgreSQL como `current_database()`

## Considerações Importantes para PostgreSQL

1. No PostgreSQL, o equivalente a bancos de dados do MySQL são os esquemas (schemas)
2. O esquema padrão no PostgreSQL é `public`, não `main` como em alguns sistemas
3. PostgreSQL é case-sensitive para nomes de objetos não entre aspas
4. PostgreSQL usa aspas duplas para identificadores e aspas simples para strings
5. Funções de data e hora são diferentes entre MySQL e PostgreSQL
6. PostgreSQL usa `string_agg` em vez de `group_concat` para concatenação de strings em agregações
7. PostgreSQL usa o operador `||` em vez da função `concat` para concatenação de strings
8. No PostgreSQL, o comando `SET search_path TO schema_name` é usado em vez de `USE database_name`
9. Para listar esquemas no PostgreSQL, é necessário consultar `information_schema.schemata` em vez de usar `SHOW DATABASES`
10. Transações no PostgreSQL são mais rigorosas e requerem tratamento adequado de erros com rollback
