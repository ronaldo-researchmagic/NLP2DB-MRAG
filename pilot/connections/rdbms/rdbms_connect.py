from __future__ import annotations

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

from pilot.connections.base import BaseConnect
from pilot.configs.config import Config

CFG = Config()


def _format_index(index: sqlalchemy.engine.interfaces.ReflectedIndex) -> str:
    return (
        f'Name: {index["name"]}, Unique: {index["unique"]},'
        f' Columns: {str(index["column_names"])}'
    )


class RDBMSDatabase(BaseConnect):
    """SQLAlchemy wrapper around a database."""

    def __init__(
        self,
        engine,
        schema: Optional[str] = None,
        metadata: Optional[MetaData] = None,
        ignore_tables: Optional[List[str]] = None,
        include_tables: Optional[List[str]] = None,
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

    @classmethod
    def from_config(cls) -> RDBMSDatabase:
        """
        Todo password encryption
        Returns:
        """
        return cls.from_uri_db(
            cls,
            CFG.LOCAL_DB_HOST,
            CFG.LOCAL_DB_PORT,
            CFG.LOCAL_DB_USER,
            CFG.LOCAL_DB_PASSWORD,
            engine_args={"pool_size": 10, "pool_recycle": 3600, "echo": True},
        )

    @classmethod
    def from_uri_db(
        cls,
        host: str,
        port: int,
        user: str,
        pwd: str,
        db_name: str = None,
        engine_args: Optional[dict] = None,
        **kwargs: Any,
    ) -> RDBMSDatabase:
        db_url: str = (
            cls.connect_driver
            + "://"
            + CFG.LOCAL_DB_USER
            + ":"
            + CFG.LOCAL_DB_PASSWORD
            + "@"
            + CFG.LOCAL_DB_HOST
            + ":"
            + str(CFG.LOCAL_DB_PORT)
        )
        if cls.dialect:
            db_url = cls.dialect + "+" + db_url
        if db_name:
            db_url = db_url + "/" + db_name
        return cls.from_uri(db_url, engine_args, **kwargs)

    @classmethod
    def from_uri(
        cls, database_uri: str, engine_args: Optional[dict] = None, **kwargs: Any
    ) -> RDBMSDatabase:
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

    def get_session(self, db_name: str):
        session = self._db_sessions()

        self._metadata = MetaData()
        # Para SQLite, não precisamos mudar de banco de dados com 'use'
        # Para outros bancos como MySQL, usamos o comando 'use'
        # Para PostgreSQL, usamos SET search_path
        if 'sqlite' in self._engine.dialect.name.lower():
            # SQLite não precisa do comando 'use'
            pass
        elif 'postgresql' in self._engine.dialect.name.lower() or 'postgres' in self._engine.dialect.name.lower():
            # Para PostgreSQL
            sql = text(f"SET search_path TO {db_name}")
            session.execute(sql)
        else:
            # Para outros bancos como MySQL
            sql = text(f"use `{db_name}`")
            session.execute(sql)

        # 处理表信息数据

        self._metadata.reflect(bind=self._engine, schema=db_name)

        # including view support by adding the views as well as tables to the all
        # tables list if view_support is True
        self._all_tables = set(
            self._inspector.get_table_names(schema=db_name)
            + (
                self._inspector.get_view_names(schema=db_name)
                if self.view_support
                else []
            )
        )

        return session

    def get_current_db_name(self, session) -> str:
        return session.execute(text("SELECT DATABASE()")).scalar()

    def table_simple_info(self, session):
        _sql = f"""
                select concat(table_name, "(" , group_concat(column_name), ")") as schema_info from information_schema.COLUMNS where table_schema="{self.get_current_db_name(session)}" group by TABLE_NAME;
            """
        cursor = session.execute(text(_sql))
        results = cursor.fetchall()
        return results

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

    def get_table_info_no_throw(self, table_names: Optional[List[str]] = None) -> str:
        """Get information about specified tables."""
        try:
            return self.get_table_info(table_names)
        except ValueError as e:
            """Format the error message"""
            return f"Error: {e}"

    def run(self, session, command: str, fetch: str = "all") -> List:
        """Execute a SQL command and return a string representing the results."""
        cursor = session.execute(text(command))
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
        # Para SQLite, não existe o conceito de múltiplos bancos de dados como em MySQL
        # Para PostgreSQL, os bancos de dados são diferentes dos esquemas
        try:
            session = self._db_sessions()
            # Verificar se estamos usando SQLite
            if 'sqlite' in self._engine.dialect.name.lower():
                # Obter o nome do arquivo do banco de dados SQLite
                cursor = session.execute(text("PRAGMA database_list;"))
                results = cursor.fetchall()
                return [db[1] for db in results]  # Nome do banco (geralmente 'main' para o principal)
            elif 'postgresql' in self._engine.dialect.name.lower() or 'postgres' in self._engine.dialect.name.lower():
                # Para PostgreSQL, listamos os esquemas disponíveis no banco atual
                cursor = session.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast');"))
                results = cursor.fetchall()
                schemas = [d[0] for d in results]
                # Se public estiver na lista, colocamos ele primeiro
                if 'public' in schemas:
                    schemas.remove('public')
                    schemas.insert(0, 'public')
                return schemas
            else:
                # Para outros bancos como MySQL
                cursor = session.execute(text("SHOW DATABASES;"))
                results = cursor.fetchall()
                return [
                    d[0]
                    for d in results
                    if d[0] not in ["information_schema", "performance_schema", "sys", "mysql"]
                ]
        except Exception as e:
            logger.error(f"Erro ao obter lista de bancos de dados: {e}")
            if 'postgresql' in self._engine.dialect.name.lower() or 'postgres' in self._engine.dialect.name.lower():
                return ['public']  # Retorna 'public' como fallback para PostgreSQL
            else:
                return ['main']  # Retorna 'main' como fallback para outros bancos
