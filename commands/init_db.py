# -*- coding: utf-8 -*-#
import getpass
import traceback
from argparse import ArgumentParser, Namespace
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from mysql.connector import MySQLConnection
from mysql.connector import errors
from prettyprinter import pprint

from commands_helpers import colored_print


class DbSettings(BaseSettings):
    WHEREAMI: str = "LOCAL"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )


def verbose_output(named_args: Namespace, msg: str, color: str = "yellow") -> None:
    if named_args.verbose is True:
        colored_print(text=msg, color=color)


def init_db_command():
    try:
        root_dir = Path(__file__).resolve().parent.parent
        env_file = root_dir / "src" / ".env" / ".env"
        
        # Load and validate settings via Pydantic
        db_settings = DbSettings(_env_file=env_file)
        
        whereami = db_settings.WHEREAMI
        parser = ArgumentParser()
        output_group = parser.add_mutually_exclusive_group()
        main_group = parser.add_mutually_exclusive_group()
        main_group.add_argument(
            "-i", "--init-db", help="Initialize the database and user", action="store_true"
        )
        main_group.add_argument(
            "-d", "--delete-db", help="Delete the database and user", action="store_true"
        )
        output_group.add_argument(
            "-v", "--verbose", help="Verbose output", action="store_true", required=False
        )
        output_group.add_argument(
            "-s", "--silence", help="Silence output", action="store_true", required=False
        )
        parser.add_argument(
            "-rw",
            "--rais-warning",
            help="Rais warning for MariaDB connection",
            required=False,
            action="store_true",
        )
        args: Namespace = parser.parse_args()
        pprint(args)
        # pprint(dir(output_group))
        try:
            colored_print(text="Enter MariaDB root password")
            mysql_root_password = getpass.getpass()
            # print(mysql_root_password)
            if mysql_root_password == "":
                colored_print(text="MariaDB password is blank...", color="yellow")
            conn_config = {
                "user": "root",
                "password": mysql_root_password,
                "host": db_settings.DB_HOST,
                "port": str(db_settings.DB_PORT),
                "autocommit": False,
            }
            if args.rais_warning is True:
                conn_config.update({"raise_on_warnings": True})
            if whereami == "LOCAL":
                conn_config.update({"option_files": "/opt/lampp/etc/my.cnf"})
            conn = MySQLConnection(**conn_config)
            if conn.is_connected():
                cursor = conn.cursor()
                conn.start_transaction()
                if args.init_db is True:
                    colored_print(text="Initializing the database and user", color="blue")
                    sql_statements = {
                        "create_db": (
                            "CREATE DATABASE IF NOT EXISTS"
                            f" {db_settings.DB_NAME} CHARACTER SET utf8;"
                        ),
                        "create_user": (
                            f"CREATE USER IF NOT EXISTS '{db_settings.DB_USER}'@'"
                            f"{db_settings.DB_HOST}' "
                            f"IDENTIFIED BY '{db_settings.DB_PASSWORD}';"
                        ),
                        "grant": (
                            f"GRANT ALL PRIVILEGES ON {db_settings.DB_NAME}.* TO '"
                            f"{db_settings.DB_USER}'@'{db_settings.DB_HOST}';"
                        ),
                        "flush": "FLUSH PRIVILEGES;",
                    }
                    colored_print(
                        text=(
                            f"Start initializing {db_settings.DB_NAME} and user"
                            f" {db_settings.DB_USER}"
                        ),
                        color="cyan",
                    )

                if args.delete_db is True:
                    colored_print(text="Deleting database and user...", color="yellow")
                    colored_print(
                        text=(
                            "Do you want to delete database"
                            f" {db_settings.DB_NAME} and user"
                            f" {db_settings.DB_USER}? [Y|N] "
                        ),
                        color="yellow",
                    )
                    confirm = input("> ")
                    confirm = confirm.lower()
                    if confirm == "n" or confirm == "" or confirm is None:
                        colored_print(text="Quiting...", color="red")
                        return
                    elif confirm == "y":
                        sql_statements = {
                            "drop_user": (
                                f"DROP USER IF EXISTS '{db_settings.DB_USER}'@'"
                                f"{db_settings.DB_HOST}';"
                            ),
                            "drop_db": (
                                f"DROP DATABASE IF EXISTS {db_settings.DB_NAME}"
                            ),
                            "flush": "FLUSH PRIVILEGES;",
                        }
                cnt = 1
                for query_key, query_stmt in sql_statements.items():
                    verbose_output(
                        args, f"{cnt}.Executing {query_key}: {query_stmt}", "yellow"
                    )
                    cursor.execute(query_stmt)
                    colored_print(text=f"Output: > {cursor.fetchone()}")
                    colored_print(text=f"{cnt}: completed successfully!", color="green")
                    cnt += 1
                conn.commit()

        except errors.Error as mysql_error:
            colored_print(text=mysql_error, color="red")
            conn.rollback()
            return
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
                colored_print(text="MariaDB connection closed!", color="cyan")
    except Exception as ex:
        colored_print(text=traceback.format_exc(), color="red")
        conn.rollback()
        return
    except KeyboardInterrupt:
        colored_print(text="Exit by the user...", color="red")
        return


if __name__ == "__main__":
    init_db_command()
