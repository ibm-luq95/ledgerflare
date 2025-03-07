from typing import Any, Literal, Optional, List

from django.conf import settings
from rich import print
from rich import inspect
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.pretty import pprint
from rich.tree import Tree

from core.utils.developments.debugging_print_types import DPOTableOptions


class DebuggingPrint:
    """
    A class representing an employee.

    Attributes:
        console (Console): The Console object
        is_debugging (bool): Whether or not debugging is enabled

    Methods:
        print_json(Any) -> None: Print the JSON representation of the object.
        log(Any) -> None: Log the object.
        print(Any) -> None: Print the object.
        pprint(Any) -> None: Print the object using rich pprint.
        rule(text) -> None: Draw a rule.
        print_exception(is_show_locales) -> None: Draw a rule.
        panel(text_content, title: str, subtitle: str) -> None: Draw a panel with content.
        tree(label: str, items: list) -> None: Draw a tree.
        table(columns_headers: list, rows: list, table_options: DPOTableOptions) -> None: Draw a table.
    """

    is_debugging = settings.DEBUG
    console = Console(color_system="truecolor", stderr=True)

    # console = Console(stderr=True)

    def __init__(self):
        try:
            __import__("rich")
        except ImportError:
            print("Rich is not installed!")
        if self.is_debugging is False:
            print("Debugging is not enabled!")

    @classmethod
    def get_console_obj(cls) -> Console:
        return cls.console

    @classmethod
    def print_json(cls, obj: Any, cast: bool = True) -> None:
        """
        Print the given object as JSON.

        Parameters:
            obj (Any): The object to be printed as JSON.

        Returns:
            None

        Parameters
        ----------
        obj
        cast
        """
        if cast is True:
            cls.console.print_json(str(obj))
        else:
            cls.console.print_json(obj)

    @classmethod
    def log(
        cls,
        *args,
        justify: Literal["center", "full", "right", "left"] = "full",
        highlight: bool = True,
        emoji: bool = True,
    ) -> None:
        """
        The log() method offers the same capabilities as print, but adds some features useful for debugging a running
        application. Logging writes the current time in a column to the left, and the file and line where the method
        was called to a column on the right.

        Parameters:
            obj (Any): The object to be printed as JSON.

        Returns:
            None

        Parameters
        ----------
        highlight
        emoji
        justify
        """
        cls.console.log(
            *args,
            justify=justify,
            highlight=highlight,
            emoji=emoji,
        )

    @classmethod
    def print_exception(cls, is_show_locales: bool = False) -> None:
        """
        Print the given exception.
        """
        cls.console.print_exception(show_locals=is_show_locales)

    @staticmethod
    def print(*args, sep=" ", end="\n", file=None, flush=False):
        print(*args, sep=sep, end=end, file=file, flush=flush)

    @staticmethod
    def dir(obj: Any):
        print(dir(obj))

    @classmethod
    def cprint(
        cls, obj: Any, justify: Literal["left", "center", "right"] = "left"
    ) -> None:
        """
        Print the given object.
        """
        cls.console.print(obj, justify=justify)

    @classmethod
    def rule(cls, text: str = "") -> None:
        """
        Print a rule with the given text.
        """
        cls.console.rule(text)

    @classmethod
    def pprint(cls, obj: Any) -> None:
        """
        Pretty print the given object.
        """
        pprint(obj, expand_all=True)

    @classmethod
    def panel(
        cls,
        text_content: Any,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> None:
        """
        Print a panel with the given text.
        """
        print(Panel(text_content, title=title, subtitle=subtitle))

    @classmethod
    def table(
        cls,
        columns_headers: list,
        rows: List[str | Any],
        table_options: Optional[DPOTableOptions] = None,
        return_table: Optional[bool] = False,
    ) -> None | Table:
        """
        Print a table with the given text.
        """
        if table_options is not None:
            table = Table(**table_options)
        else:
            table = Table()
        for header in columns_headers:
            table.add_column(header)
        for row in rows:
            table.add_row(*row)

        if return_table is False:
            cls.console.print(table)
        else:
            return table

    def tree(self, label: Optional[str] = None, items: Optional[list] = None) -> None:
        """
        Print a tree with the given text.
        """
        tree = Tree(label=label)
        for item in items:
            tree.add(item, highlight=True)
        print(tree)

    @staticmethod
    def inspect(
        obj: Any,
        title: str | None = None,
        is_all: bool = False,
        help: bool = False,
        methods: bool = False,
        docs: bool = True,
        private: bool = False,
        dunder: bool = False,
        sort: bool = True,
        value: bool = True,
    ) -> None:
        inspect(
            obj,
            title=title,
            all=is_all,
            value=value,
            help=help,
            methods=methods,
            docs=docs,
            private=private,
            dunder=dunder,
            sort=sort,
        )
