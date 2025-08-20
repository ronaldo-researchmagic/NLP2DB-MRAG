from __future__ import annotations
import sqlparse
import regex as re
import warnings
import logging
from typing import Any, Iterable, List, Optional
from pydantic import BaseModel, Field, root_validator, validator, Extra
from abc import ABC, abstractmethod
import sqlalchemy
from sqlalchemy import (
    MetaData,
    Table,
    create_engine,
    inspect,
    select,
    text,
)
from sqlalchemy.engine import CursorResult, Engine
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import sessionmaker, scoped_session

logger = logging.getLogger(__name__)


def _format_index(index: sqlalchemy.engine.interfaces.ReflectedIndex) -> str:
    return (
        f'Name: {index["name"]}, Unique: {index["unique"]},'
        f' Columns: {str(index["column_names"])}'
    )


class Database:
    """SQLAlchemy wrapper around a database."""


    @property
    def engine(self):
        # Propriedade para acessar o engine do SQLAlchemy
        return self._engine
        
    def __init__(
        self,
        engine,
        schema: Optional[str] = None,
        metadata: Optional[MetaData] = None,
        ignore_tables: Optional[List[str]] = None,
        include_tables: Optional[List[str]] = None,
        sample_rows_in_table_info: int = 3,
        indexes_in_table_info: bool = False,
        custom_table_info: Optional[dict] = None,
        view_support: bool = False,
    ):
        """Create engine from database URI."""
        self._engine = engine
        self._schema = schema
        if include_tables and ignore_tables:
            raise ValueError("Cannot specify both include_tables and ignore_tables")

        self._inspector = inspect(self._engine)
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)

        self._db_sessions = Session

        self._all_tables = set()
        self.view_support = view_support
        self._metadata = MetaData()
        self._ignore_tables = set(ignore_tables) if ignore_tables else set()
        self._include_tables = set(include_tables) if include_tables else set()
        self._sample_rows_in_table_info = sample_rows_in_table_info
        self._indexes_in_table_info = indexes_in_table_info
        self._custom_table_info = custom_table_info or {}

        # Initialize _all_tables and _usable_tables
        self._all_tables = self._get_all_table_names()
        self._usable_tables = self.get_usable_table_names()

    @classmethod
    def from_uri(
        cls, database_uri: str, engine_args: Optional[dict] = None, **kwargs: Any
    ) -> Database:
        """Construct a SQLAlchemy engine from URI."""
        _engine_args = engine_args or {}
        return cls(create_engine(database_uri, **_engine_args), **kwargs)

    @property
    def engine(self):
        """Propriedade para acessar o engine do SQLAlchemy."""
        return self._engine
        
    @property
    def dialect(self) -> str:
        """Return string representation of dialect to use."""
        return self._engine.dialect.name

    def get_usable_table_names(self) -> Iterable[str]:
        """Get names of tables available."""
        if self._include_tables:
            return self._include_tables
        return self._all_tables - self._ignore_tables

    def get_table_names(self) -> Iterable[str]:
        """Get names of tables available."""
        warnings.warn(
            "This method is deprecated - please use `get_usable_table_names`."
        )
        return self.get_usable_table_names()

    def get_session_db(self, connect):
        # Usar função compatível com diferentes bancos de dados
        if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            sql = text(f"SELECT current_database()")
        else:
            sql = text(f"SELECT DATABASE()")
        cursor = connect.execute(sql)
        result = cursor.fetchone()[0]
        return result

    def _get_all_table_names(self) -> set:
        """Get all table names in the database."""
        all_schemas = self._inspector.get_schema_names()
        all_tables = set()
        for schema in all_schemas:
            if schema in ('information_schema', 'pg_catalog', 'performance_schema', 'sys', 'mysql'):
                continue
            try:
                tables = self._inspector.get_table_names(schema=schema)
                all_tables.update(tables)
                if self.view_support:
                    views = self._inspector.get_view_names(schema=schema)
                    all_tables.update(views)
            except Exception as e:
                logger.warning(f"Could not get tables for schema {schema}: {e}")
        return all_tables

    def get_session(self, db_name: str):
        session = self._db_sessions()
        schema_to_set = db_name

        if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            if db_name == 'main' or not db_name:
                schema_to_set = 'public'
            try:
                session.execute(text(f"SET search_path TO {schema_to_set}"))
            except Exception as e:
                logger.error(f"Error setting search_path to {schema_to_set}: {e}")
                session.rollback()
        elif 'mysql' in self._engine.name.lower():
            try:
                session.execute(text(f"USE `{db_name}`"))
            except Exception as e:
                logger.error(f"Error using database {db_name}: {e}")
                session.rollback()

        # Reflect metadata for all usable tables
        self._metadata.reflect(bind=self._engine, only=list(self._usable_tables))

        return session

    def get_current_db_name(self, session) -> str:
        # Usar função compatível com diferentes bancos de dados
        if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
            return session.execute(text("SELECT current_database()")).scalar()
        else:
            return session.execute(text("SELECT DATABASE()")).scalar()

    def table_simple_info(self, session):
        # Usar consulta compatível com diferentes bancos de dados
        try:
            if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
                # No PostgreSQL, precisamos usar o esquema atual (search_path)
                # Para PostgreSQL, usamos 'public' como esquema padrão
                _sql = f"""
                    SELECT table_name, '(' || string_agg(column_name, ',') || ')' as columns
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    GROUP BY table_name;
                """
            else:
                _sql = f"""
                    SELECT table_name, concat("(" , group_concat(column_name), ")") as columns
                    FROM information_schema.COLUMNS 
                    WHERE table_schema="{self.get_current_db_name(session)}" 
                    GROUP BY TABLE_NAME;
                """
            cursor = session.execute(text(_sql))
            results = cursor.fetchall()
            
            # Formatar os resultados como tuplas (table_name, columns)
            formatted_results = [(row[0], row[1]) for row in results]
            return formatted_results
        except Exception as e:
            print(f"Error in table_simple_info: {e}")
            # Retornar uma lista vazia em caso de erro
            return []

    @property
    def table_info(self) -> str:
        """Information about all tables in the database."""
        return self.get_table_info()

    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """Get information about specified tables.

        Follows best practices as specified in: Rajkumar et al, 2022
        (https://arxiv.org/abs/2204.00498)

        If `sample_rows_in_table_info`, the specified number of sample rows will be
        appended to each table description. This can increase performance as
        demonstrated in the paper.
        """
        all_table_names = self.get_usable_table_names()
        if table_names is not None:
            missing_tables = set(table_names).difference(all_table_names)
            if missing_tables:
                raise ValueError(f"table_names {missing_tables} not found in database")
            all_table_names = table_names

        meta_tables = [
            tbl
            for tbl in self._metadata.sorted_tables
            if tbl.name in set(all_table_names)
            and not (self.dialect == "sqlite" and tbl.name.startswith("sqlite_"))
        ]

        tables = []
        for table in meta_tables:
            if self._custom_table_info and table.name in self._custom_table_info:
                tables.append(self._custom_table_info[table.name])
                continue

            # add create table command
            create_table = str(CreateTable(table).compile(self._engine))
            table_info = f"{create_table.rstrip()}"
            has_extra_info = (
                self._indexes_in_table_info or self._sample_rows_in_table_info
            )
            if has_extra_info:
                table_info += "\n\n/*"
            if self._indexes_in_table_info:
                table_info += f"\n{self._get_table_indexes(table)}\n"
            if self._sample_rows_in_table_info:
                table_info += f"\n{self._get_sample_rows(table)}\n"
            if has_extra_info:
                table_info += "*/"
            tables.append(table_info)
        final_str = "\n\n".join(tables)
        return final_str

    def _get_sample_rows(self, table: Table) -> str:
        # build the select command
        command = select(table).limit(self._sample_rows_in_table_info)

        # save the columns in string format
        columns_str = "\t".join([col.name for col in table.columns])

        try:
            # get the sample rows
            with self._engine.connect() as connection:
                sample_rows_result: CursorResult = connection.execute(command)
                # shorten values in the sample rows
                sample_rows = list(
                    map(lambda ls: [str(i)[:100] for i in ls], sample_rows_result)
                )

            # save the sample rows in string format
            sample_rows_str = "\n".join(["\t".join(row) for row in sample_rows])

        # in some dialects when there are no rows in the table a
        # 'ProgrammingError' is returned
        except ProgrammingError:
            sample_rows_str = ""

        return (
            f"{self._sample_rows_in_table_info} rows from {table.name} table:\n"
            f"{columns_str}\n"
            f"{sample_rows_str}"
        )

    def _get_table_indexes(self, table: Table) -> str:
        indexes = self._inspector.get_indexes(table.name)
        indexes_formatted = "\n".join(map(_format_index, indexes))
        return f"Table Indexes:\n{indexes_formatted}"

    def get_table_info_with_foreign_keys(self, session):
        """Gets table schema information and foreign key relationships."""
        # Get basic table info (name and columns)
        table_info_tuples = self.table_simple_info(session)
        table_info_str = "\n".join([f"{name}{columns}" for name, columns in table_info_tuples])

        # Get foreign key info
        all_foreign_keys = self._get_all_foreign_keys(session)
        
        if all_foreign_keys:
            fk_info_str = "\nFOREIGN KEY RELATIONSHIPS:\n" + "\n".join(all_foreign_keys)
            return table_info_str + fk_info_str
        
        return table_info_str

    def _get_all_foreign_keys(self, session):
        """Retrieves all foreign key relationships in the current database/schema."""
        all_fks = []
        all_schemas = self._inspector.get_schema_names()

        for schema in all_schemas:
            # Ignore system schemas
            if schema.startswith('pg_') or schema in ['information_schema', 'mysql', 'sys', 'performance_schema']:
                continue

            for table_name in self._inspector.get_table_names(schema=schema):
                try:
                    fks = self._inspector.get_foreign_keys(table_name, schema=schema)
                    for fk in fks:
                        constrained_columns = fk['constrained_columns']
                        referred_table = fk['referred_table']
                        referred_columns = fk['referred_columns']
                        
                        fk_info = f"{schema}.{table_name}({', '.join(constrained_columns)}) -> {schema}.{referred_table}({', '.join(referred_columns)})"
                        all_fks.append(fk_info)
                except Exception as e:
                    logger.warning(f"Could not get foreign keys for table {schema}.{table_name}: {e}")
                
        return all_fks

    def get_table_info_no_throw(self, table_names: Optional[List[str]] = None) -> str:
        """Get information about specified tables."""
        try:
            return self.get_table_info(table_names)
        except ValueError as e:
            """Format the error message"""
            return f"Error: {e}"

    def __write(self, session, write_sql):
        print(f"Write[{write_sql}]")
        db_cache = self.get_session_db(session)
        result = session.execute(text(write_sql))
        session.commit()
        # TODO  Subsequent optimization of dynamically specified database submission loss target problem
        # Para SQLite, não precisamos mudar de banco de dados com 'use'
        if 'sqlite' not in self._engine.name.lower():
            if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
                # PostgreSQL usa SET search_path em vez de USE
                session.execute(text(f"SET search_path TO {db_cache}"))
            else:
                # MySQL e outros
                session.execute(text(f"use `{db_cache}`"))
        print(f"SQL[{write_sql}], result:{result.rowcount}")
        return result.rowcount

    def __query(self, session, query, fetch: str = "all"):
        """
        only for query
        Args:
            session:
            query:
            fetch:

        Returns:

        """
        print(f"Query[{query}]")
        if not query:
            return []
        cursor = session.execute(text(query))
        if cursor.returns_rows:
            if fetch == "all":
                result = cursor.fetchall()
            elif fetch == "one":
                result = cursor.fetchone()[0]  # type: ignore
            else:
                raise ValueError("Fetch parameter must be either 'one' or 'all'")
            field_names = tuple(i[0:] for i in cursor.keys())

            result = list(result)
            result.insert(0, field_names)
            return result

    def run(self, session, command: str, fetch: str = "all") -> List:
        """Execute a SQL command and return a string representing the results."""
        print("SQL:" + command)
        if not command:
            return []
            
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
        
        parsed, ttype, sql_type = self.__sql_parse(command)
        if ttype == sqlparse.tokens.DML:
            if sql_type == "SELECT":
                return self.__query(session, command, fetch)
            else:
                self.__write(session, command)
                select_sql = self.convert_sql_write_to_select(command)
                print(f"write result query:{select_sql}")
                return self.__query(session, select_sql)

        else:
            print(f"DDL execution determines whether to enable through configuration ")
            cursor = session.execute(text(command))
            session.commit()
            if cursor.returns_rows:
                result = cursor.fetchall()
                field_names = tuple(i[0:] for i in cursor.keys())
                result = list(result)
                result.insert(0, field_names)
                print("DDL Result:" + str(result))

                return result
            else:
                return []

    def run_no_throw(self, session, command: str, fetch: str = "all") -> List:
        """Execute a SQL command and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.

        If the statement throws an error, the error message is returned.
        """
        try:
            return self.run(session, command, fetch)
        except SQLAlchemyError as e:
            """Format the error message"""
            return f"Error: {e}"

    def get_database_list(self):
        # Retorna a lista de bancos de dados (MySQL) ou esquemas (PostgreSQL)
        try:
            session = self._db_sessions()
            # Verificar o tipo de banco de dados
            if 'sqlite' in self._engine.name.lower():
                # Para SQLite, obter o nome do arquivo do banco de dados
                cursor = session.execute(text("PRAGMA database_list;"))
                results = cursor.fetchall()
                return [db[1] for db in results]  # Nome do banco (geralmente 'main' para o principal)
            elif 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
                # Para PostgreSQL, listar esquemas disponíveis
                cursor = session.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                """))
                results = cursor.fetchall()
                schemas = [d[0] for d in results]
                # Se não houver esquemas personalizados, usar 'public' como padrão
                if not schemas:
                    return ['public']
                return schemas
            else:
                # Para MySQL e outros
                cursor = session.execute(text("SHOW DATABASES;"))
                results = cursor.fetchall()
                return [
                    d[0]
                    for d in results
                    if d[0] not in ["information_schema", "performance_schema", "sys", "mysql"]
                ]
        except Exception as e:
            logger.error(f"Erro ao obter lista de bancos de dados: {e}")
            # Retorna um valor padrão dependendo do tipo de banco
            if 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
                return ['public']  # Esquema padrão para PostgreSQL
            else:
                return ['main']  # Fallback para outros bancos

    def convert_sql_write_to_select(self, write_sql):
        """
        SQL classification processing
        author:xiangh8
        Args:
            sql:

        Returns:

        """
        # 将SQL命令转换为小写，并按空格拆分
        parts = write_sql.lower().split()
        # 获取命令类型（insert, delete, update）
        cmd_type = parts[0]

        # 根据命令类型进行处理
        if cmd_type == "insert":
            match = re.match(
                r"insert into (\w+) \((.*?)\) values \((.*?)\)", write_sql.lower()
            )
            if match:
                table_name, columns, values = match.groups()
                # 将字段列表和值列表分割为单独的字段和值
                columns = columns.split(",")
                values = values.split(",")
                # 构造 WHERE 子句
                where_clause = " AND ".join(
                    [
                        f"{col.strip()}={val.strip()}"
                        for col, val in zip(columns, values)
                    ]
                )
                return f"SELECT * FROM {table_name} WHERE {where_clause}"

        elif cmd_type == "delete":
            table_name = parts[2]  # delete from <table_name> ...
            # 返回一个select语句，它选择该表的所有数据
            return f"SELECT * FROM {table_name}"

        elif cmd_type == "update":
            table_name = parts[1]
            set_idx = parts.index("set")
            where_idx = parts.index("where")
            # 截取 `set` 子句中的字段名
            set_clause = parts[set_idx + 1 : where_idx][0].split("=")[0].strip()
            # 截取 `where` 之后的条件语句
            where_clause = " ".join(parts[where_idx + 1 :])
            # 返回一个select语句，它选择更新的数据
            return f"SELECT {set_clause} FROM {table_name} WHERE {where_clause}"
        else:
            raise ValueError(f"Unsupported SQL command type: {cmd_type}")

    def __sql_parse(self, sql):
        sql = sql.strip()
        parsed = sqlparse.parse(sql)[0]
        sql_type = parsed.get_type()

        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        ttype = first_token.ttype
        print(f"SQL:{sql}, ttype:{ttype}, sql_type:{sql_type}")
        return parsed, ttype, sql_type

    def get_indexes(self, table_name):
        """Get table indexes about specified table."""
        session = self._db_sessions()
        cursor = session.execute(text(f"SHOW INDEXES FROM {table_name}"))
        indexes = cursor.fetchall()
        return [(index[2], index[4]) for index in indexes]

    def get_show_create_table(self, table_name):
        """Get table show create table about specified table."""
        session = self._db_sessions()
        cursor = session.execute(text(f"SHOW CREATE TABLE  {table_name}"))
        ans = cursor.fetchall()
        return ans[0][1]

    def get_fields(self, table_name):
        """Get column fields about specified table."""
        session = self._db_sessions()
        cursor = session.execute(
            text(
                f"SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT, IS_NULLABLE, COLUMN_COMMENT  from information_schema.COLUMNS where table_name='{table_name}'".format(
                    table_name
                )
            )
        )
        fields = cursor.fetchall()
        return [(field[0], field[1], field[2], field[3], field[4]) for field in fields]

    def get_charset(self):
        """Get character_set."""
        session = self._db_sessions()
        cursor = session.execute(text(f"SELECT @@character_set_database"))
        character_set = cursor.fetchone()[0]
        return character_set

    def get_collation(self):
        """Get collation."""
        session = self._db_sessions()
        cursor = session.execute(text(f"SELECT @@collation_database"))
        collation = cursor.fetchone()[0]
        return collation

    def get_grants(self):
        """Get grant info."""
        session = self._db_sessions()
        cursor = session.execute(text(f"SHOW GRANTS"))
        grants = cursor.fetchall()
        return grants
        
    def run_sql(self, sql_query, db_name="main"):
        """Execute uma consulta SQL e retorna o resultado.
        
        Args:
            sql_query (str): Consulta SQL a ser executada
            db_name (str): Nome do banco de dados/esquema a ser usado
            
        Returns:
            list: Resultado da consulta
        """
        try:
            session = self._db_sessions()
            
            # Configurar o esquema/banco de dados antes de executar a consulta
            if 'sqlite' in self._engine.name.lower():
                # SQLite não precisa de seleção de banco de dados
                pass
            elif 'postgresql' in self._engine.name.lower() or 'postgres' in self._engine.name.lower():
                # PostgreSQL usa SET search_path em vez de USE
                try:
                    session.execute(text(f"SET search_path TO {db_name}"))
                except Exception as e:
                    import logging
                    logging.warning(f"Erro ao definir search_path para {db_name}: {e}")
                    # Em caso de erro, tentar usar 'public'
                    session.rollback()  # Limpar transação com erro
                    session.execute(text("SET search_path TO public"))
            else:
                # MySQL e outros
                try:
                    session.execute(text(f"use `{db_name}`"))
                except Exception as e:
                    import logging
                    logging.warning(f"Erro ao usar banco de dados {db_name}: {e}")
            
            # Executar a consulta
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

    def get_users(self):
        """Get user info."""
        session = self._db_sessions()
        cursor = session.execute(text(f"SELECT user, host FROM mysql.user"))
        users = cursor.fetchall()
        return [(user[0], user[1]) for user in users]

    def get_table_comments(self, database):
        session = self._db_sessions()
        cursor = session.execute(
            text(
                f"""SELECT table_name, table_comment    FROM information_schema.tables   WHERE table_schema = '{database}'""".format(
                    database
                )
            )
        )
        table_comments = cursor.fetchall()
        return [
            (table_comment[0], table_comment[1]) for table_comment in table_comments
        ]
