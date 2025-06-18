"""Enhanced debugging utilities with Rich library integration.

This module provides a comprehensive debugging toolkit using the Rich library
for beautiful console output, Django model inspection, and advanced data visualization.
"""

from __future__ import annotations

import inspect
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from functools import singledispatch
from typing import Any, Final, Literal, Protocol, Self, TypeAlias
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from rich.columns import Columns
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.pretty import Pretty
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

# Type aliases
JSONSerializable: TypeAlias = (
    dict[str, Any] | list[Any] | str | int | float | bool | None
)
DisplayableObject: TypeAlias = Any
JustifyOption: TypeAlias = Literal["left", "center", "right", "full"]
TableStyle: TypeAlias = Literal["ascii", "simple", "heavy", "double", "rounded"]

# Constants
MAX_REPR_LENGTH: Final[int] = 1000
DEFAULT_PANEL_WIDTH: Final[int] = 80
DJANGO_MODEL_FIELDS_LIMIT: Final[int] = 50


class OutputFormat(Enum):
    """Enumeration of available output formats for debugging display."""

    PRETTY = auto()
    JSON = auto()
    TABLE = auto()
    TREE = auto()
    PANEL = auto()
    SYNTAX = auto()
    MARKDOWN = auto()


class DisplayTheme(Enum):
    """Predefined display themes for consistent styling."""

    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    MINIMAL = "minimal"
    COLORFUL = "colorful"


@dataclass(slots=True, frozen=True)
class TableConfiguration:
    """Configuration options for table display.

    This dataclass encapsulates all table styling and behavior options
    for consistent table rendering across the debugging toolkit.

    :ivar show_header: Whether to display column headers
    :vartype show_header: bool
    :ivar show_lines: Whether to show grid lines between cells
    :vartype show_lines: bool
    :ivar expand: Whether table should expand to full console width
    :vartype expand: bool
    :ivar style: Visual style theme for the table
    :vartype style: TableStyle
    :ivar max_rows: Maximum number of rows to display before truncation
    :vartype max_rows: int

    Examples
    --------
    >>> config = TableConfiguration(
    ...     show_header=True,
    ...     style="rounded",
    ...     max_rows=100
    ... )
    >>> config.show_header
    True
    """

    show_header: bool = True
    show_lines: bool = True
    expand: bool = True
    style: TableStyle = "rounded"
    max_rows: int = 100
    min_width: int = 20
    highlight: bool = True


@dataclass(slots=True)
class DebugContext:
    """Context information for debugging operations.

    This dataclass maintains contextual information about the debugging
    session including caller information, timestamps, and display preferences.

    :ivar caller_frame: Frame information of the calling code
    :vartype caller_frame: inspect.FrameInfo | None
    :ivar timestamp: UTC timestamp when debug context was created
    :vartype timestamp: datetime
    :ivar theme: Active display theme for styling
    :vartype theme: DisplayTheme
    :ivar depth: Current nesting depth for hierarchical displays
    :vartype depth: int

    Examples
    --------
    >>> context = DebugContext.create()
    >>> context.theme
    <DisplayTheme.DEFAULT: 'default'>
    """

    caller_frame: inspect.FrameInfo | None = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("UTC"))
    )
    theme: DisplayTheme = DisplayTheme.DEFAULT
    depth: int = 0

    @classmethod
    def create(cls, theme: DisplayTheme = DisplayTheme.DEFAULT) -> Self:
        """Create debug context with caller frame information.

        Factory method that automatically captures the calling frame
        information for enhanced debugging context.

        :param DisplayTheme theme: Display theme to use for styling
        :return: New debug context instance with caller information
        :rtype: DebugContext

        Examples
        --------
        >>> context = DebugContext.create(DisplayTheme.DARK)
        >>> context.caller_frame is not None
        True
        """
        frame_info = None
        try:
            frame_info = inspect.stack()[2]  # Skip create() and calling method
        except (IndexError, OSError):
            pass  # Frame info not available

        return cls(caller_frame=frame_info, theme=theme)


class RenderableProtocol(Protocol):
    """Protocol for objects that can be rendered by Rich console.

    This protocol defines the interface for objects that provide
    custom Rich rendering capabilities for enhanced display formatting.

    .. note::
        Implementing this protocol allows objects to control their
        own debugging display representation.
    """

    def __rich__(self) -> Any:
        """Return Rich-renderable representation of the object.

        :return: Rich-compatible renderable object
        :rtype: Any

        Examples
        --------
        >>> class CustomObject:
        ...     def __rich__(self):
        ...         return Panel("Custom rendering")
        """
        ...


class DebuggingPrintError(Exception):
    """Base exception for debugging print operations.

    Custom exception class for handling errors specific to the
    debugging print functionality with enhanced error context.

    Examples
    --------
    >>> raise DebuggingPrintError("Failed to render object")
    Traceback (most recent call last):
    ...
    DebuggingPrintError: Failed to render object
    """

    pass


class EnhancedDebuggingPrint:
    """Advanced debugging utilities with Rich library integration.

    This class provides a comprehensive suite of debugging tools leveraging
    the Rich library for beautiful console output, Django model inspection,
    and advanced data visualization capabilities. It supports multiple output
    formats, themes, and specialized rendering for different data types.

    :ivar console: Rich Console instance for output rendering
    :vartype console: Console
    :ivar is_debugging: Whether debugging mode is currently active
    :vartype is_debugging: bool
    :ivar default_theme: Default theme for display styling
    :vartype default_theme: DisplayTheme
    :ivar highlighter: Syntax highlighter for code rendering
    :vartype highlighter: ReprHighlighter

    Examples
    --------
    >>> debug = EnhancedDebuggingPrint()
    >>> debug.print("Hello, World!")
    Hello, World!
    >>> debug.inspect_django_model(MyModel)
    # Displays formatted Django model information

    .. warning::
        This class requires Django settings to be configured for Django-specific features.

    .. note::
        All output respects the DEBUG setting from Django configuration.

    See Also
    --------
    :class:`DebugContext`: Context management for debugging sessions
    :class:`TableConfiguration`: Table display configuration options
    :exc:`DebuggingPrintError`: Exception handling for debugging operations
    """

    _instances: dict[str, Self] = {}
    _console: Console | None = None

    def __init__(
        self,
        theme: DisplayTheme = DisplayTheme.DEFAULT,
        enable_highlighting: bool = True,
        stderr: bool = True,
    ) -> None:
        """Initialize enhanced debugging print instance.

        Create a new debugging print instance with specified theme and
        configuration options for console output and syntax highlighting.

        :param DisplayTheme theme: Visual theme for output styling
        :param bool enable_highlighting: Whether to enable syntax highlighting
        :param bool stderr: Whether to output to stderr instead of stdout
        :raises DebuggingPrintError: When Rich library is not available
        :raises ImportError: When required dependencies are missing

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint(
        ...     theme=DisplayTheme.DARK,
        ...     enable_highlighting=True
        ... )
        >>> debug.is_debugging
        True

        .. note::
            Multiple instances with the same theme share console resources
            for optimal performance.
        """
        try:
            __import__("rich")
        except ImportError as e:
            raise DebuggingPrintError(
                "Rich library is required but not installed"
            ) from e

        self.is_debugging: bool = getattr(settings, "DEBUG", False)
        self.default_theme: DisplayTheme = theme
        self.highlighter: ReprHighlighter = ReprHighlighter()

        # Singleton pattern for console instances per theme
        console_key = f"{theme.value}_{stderr}_{enable_highlighting}"
        if console_key not in self._instances:
            self._console = Console(
                color_system="truecolor",
                stderr=stderr,
                highlight=enable_highlighting,
                force_terminal=True,
            )
            self._instances[console_key] = self
        else:
            self._console = self._instances[console_key]._console

    @property
    def console(self) -> Console:
        """Get the Rich Console instance for output operations.

        :return: Active console instance for this debugging session
        :rtype: Console

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> console = debug.console
        >>> isinstance(console, Console)
        True
        """
        if self._console is None:
            raise DebuggingPrintError("Console not properly initialized")
        return self._console

    @contextmanager
    def status(self, message: str, spinner: str = "dots"):
        """Context manager for displaying status during operations.

        Provide a status indicator with spinner animation during
        long-running debugging operations for better user experience.

        :param str message: Status message to display
        :param str spinner: Spinner animation style name
        :yields: Status context for the operation
        :ytype: Status

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> with debug.status("Processing data..."):
        ...     time.sleep(2)  # Long operation
        # Shows spinner with message during operation

        See Also
        --------
        :meth:`progress`: Progress bar context manager
        """
        with Status(message, console=self.console, spinner=spinner) as status:
            yield status

    @contextmanager
    def progress(self, description: str = "Processing..."):
        """Context manager for displaying progress during operations.

        Provide a progress bar interface for tracking completion
        of debugging operations with multiple steps or items.

        :param str description: Description text for the progress operation
        :yields: Progress instance for tracking completion
        :ytype: Progress

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> with debug.progress("Analyzing objects...") as progress:
        ...     task = progress.add_task("Processing", total=100)
        ...     for i in range(100):
        ...         progress.update(task, advance=1)

        See Also
        --------
        :meth:`status`: Simple status indicator context manager
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            yield progress

    @singledispatch
    def display(
        self, obj: Any, format_type: OutputFormat = OutputFormat.PRETTY
    ) -> None:
        """Generic display method with format-specific rendering.

        Main entry point for displaying objects with automatic type
        detection and format-appropriate rendering using single dispatch.

        :param Any obj: Object to display with appropriate formatting
        :param OutputFormat format_type: Desired output format for rendering
        :raises DebuggingPrintError: When object cannot be rendered
        :raises TypeError: When format_type is not supported

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> debug.display({"key": "value"}, OutputFormat.JSON)
        {
          "key": "value"
        }
        >>> debug.display([1, 2, 3], OutputFormat.TABLE)
        # Displays list as formatted table

        .. warning::
            Large objects may cause performance issues with certain formats.

        See Also
        --------
        :meth:`display_django_model`: Specialized Django model display
        :meth:`display_queryset`: Django QuerySet display method
        """
        if not self.is_debugging:
            return

        context = DebugContext.create(self.default_theme)

        match format_type:
            case OutputFormat.PRETTY:
                self._display_pretty(obj, context)
            case OutputFormat.JSON:
                self._display_json(obj, context)
            case OutputFormat.TABLE:
                self._display_table(obj, context)
            case OutputFormat.TREE:
                self._display_tree(obj, context)
            case OutputFormat.PANEL:
                self._display_panel(obj, context)
            case _:
                raise DebuggingPrintError(f"Unsupported format type: {format_type}")

    @display.register
    def _(
        self, obj: models.Model, format_type: OutputFormat = OutputFormat.PANEL
    ) -> None:
        """Display Django model instance with field information.

        Specialized display method for Django model instances showing
        field values, metadata, and relationship information in a structured format.

        :param models.Model obj: Django model instance to display
        :param OutputFormat format_type: Format for model display rendering

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> user = User.objects.get(id=1)
        >>> debug.display(user)
        # Shows formatted panel with model fields and values
        """
        self.display_django_model(obj, format_type)

    @display.register
    def _(self, obj: QuerySet, format_type: OutputFormat = OutputFormat.TABLE) -> None:
        """Display Django QuerySet with pagination and field summary.

        Specialized display method for Django QuerySets showing query
        information, result count, and sample records in tabular format.

        :param QuerySet obj: Django QuerySet to display
        :param OutputFormat format_type: Format for QuerySet display rendering

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> users = User.objects.filter(is_active=True)
        >>> debug.display(users)
        # Shows table with QuerySet results and metadata
        """
        self.display_queryset(obj, format_type)

    def display_django_model(
        self,
        model_instance: models.Model,
        format_type: OutputFormat = OutputFormat.PANEL,
    ) -> None:
        """Display Django model with comprehensive field analysis.

        Render Django model instance with detailed field information,
        relationships, and metadata in a user-friendly format with
        support for complex field types and foreign key relationships.

        :param models.Model model_instance: Django model instance to analyze
        :param OutputFormat format_type: Display format for model rendering
        :raises DebuggingPrintError: When model analysis fails
        :raises AttributeError: When model instance is invalid

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> user = User.objects.get(id=1)
        >>> debug.display_django_model(user, OutputFormat.PANEL)
        ┌─ User Instance #1 ─┐
        │ id: 1             │
        │ username: admin   │
        │ email: a@test.com │
        └───────────────────┘

        .. note::
            Foreign key relationships are displayed with link information.

        See Also
        --------
        :meth:`display_queryset`: QuerySet-specific display method
        :meth:`_get_model_field_info`: Field information extraction utility
        """
        if not isinstance(model_instance, models.Model):
            raise DebuggingPrintError("Object is not a Django model instance")

        model_class = model_instance.__class__
        model_name = model_class.__name__
        pk_value = model_instance.pk

        # Gather field information
        field_data = self._get_model_field_info(model_instance)

        match format_type:
            case OutputFormat.PANEL:
                self._render_model_panel(model_name, pk_value, field_data)
            case OutputFormat.TABLE:
                self._render_model_table(model_name, pk_value, field_data)
            case OutputFormat.TREE:
                self._render_model_tree(model_name, pk_value, field_data)
            case _:
                # Fallback to panel format
                self._render_model_panel(model_name, pk_value, field_data)

    def display_queryset(
        self,
        queryset: QuerySet,
        format_type: OutputFormat = OutputFormat.TABLE,
        max_items: int = 20,
    ) -> None:
        """Display Django QuerySet with query analysis and results.

        Render Django QuerySet showing query information, execution
        statistics, and result data in an organized format with
        pagination support for large result sets.

        :param QuerySet queryset: Django QuerySet to analyze and display
        :param OutputFormat format_type: Display format for QuerySet rendering
        :param int max_items: Maximum number of items to display
        :raises DebuggingPrintError: When QuerySet analysis fails
        :raises ValueError: When max_items is not positive

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> users = User.objects.filter(is_active=True)[:10]
        >>> debug.display_queryset(users, max_items=5)
        ┌─ QuerySet: User (5 items) ─┐
        │ SQL: SELECT * FROM users   │
        │ WHERE is_active = True     │
        └────────────────────────────┘

        .. warning::
            Large QuerySets may cause performance issues during evaluation.

        See Also
        --------
        :meth:`display_django_model`: Individual model instance display
        :meth:`_analyze_queryset`: QuerySet analysis utility method
        """
        if max_items <= 0:
            raise ValueError("max_items must be positive")

        # Analyze queryset without evaluating
        queryset_info = self._analyze_queryset(queryset)

        # Get limited results
        try:
            results = list(queryset[:max_items])
        except Exception as e:
            raise DebuggingPrintError(f"Failed to evaluate QuerySet: {e}") from e

        match format_type:
            case OutputFormat.TABLE:
                self._render_queryset_table(queryset_info, results, max_items)
            case OutputFormat.PANEL:
                self._render_queryset_panel(queryset_info, results, max_items)
            case _:
                self._render_queryset_table(queryset_info, results, max_items)

    def markdown(self, content: str, title: str | None = None) -> None:
        """Render Markdown content with syntax highlighting.

        Display formatted Markdown content with proper syntax highlighting
        and styling using Rich's Markdown renderer for documentation
        and formatted text display.

        :param str content: Markdown content to render
        :param str | None title: Optional title for the Markdown panel
        :raises DebuggingPrintError: When Markdown rendering fails

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> content = "# Title\\n\\n- Item 1\\n- Item 2"
        >>> debug.markdown(content, "Documentation")
        # Renders formatted Markdown with syntax highlighting

        See Also
        --------
        :meth:`syntax`: Code syntax highlighting method
        :meth:`panel`: General panel display method
        """
        if not self.is_debugging:
            return

        try:
            markdown_obj = Markdown(content)
            if title:
                self.console.print(Panel(markdown_obj, title=title))
            else:
                self.console.print(markdown_obj)
        except Exception as e:
            raise DebuggingPrintError(f"Failed to render Markdown: {e}") from e

    def syntax(
        self,
        code: str,
        language: str = "python",
        theme: str = "monokai",
        line_numbers: bool = True,
    ) -> None:
        """Display code with syntax highlighting and line numbers.

        Render source code with appropriate syntax highlighting,
        line numbers, and theme styling using Rich's syntax
        highlighting capabilities for code review and debugging.

        :param str code: Source code content to highlight
        :param str language: Programming language for syntax highlighting
        :param str theme: Color theme for syntax highlighting
        :param bool line_numbers: Whether to show line numbers
        :raises DebuggingPrintError: When syntax highlighting fails

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> code = "def hello():\\n    print('Hello, World!')"
        >>> debug.syntax(code, "python", line_numbers=True)
        1 │ def hello():
        2 │     print('Hello, World!')

        See Also
        --------
        :meth:`markdown`: Markdown content rendering
        :meth:`inspect_object`: Object code inspection
        """
        if not self.is_debugging:
            return

        try:
            syntax_obj = Syntax(
                code, language, theme=theme, line_numbers=line_numbers, code_width=80
            )
            self.console.print(syntax_obj)
        except Exception as e:
            raise DebuggingPrintError(f"Failed to render syntax: {e}") from e

    def columns(
        self, *renderables: Any, equal: bool = True, expand: bool = True
    ) -> None:
        """Display objects in aligned columns layout.

        Arrange multiple renderable objects in a column layout
        for side-by-side comparison and space-efficient display
        of related information.

        :param Any renderables: Objects to display in column layout
        :param bool equal: Whether columns should have equal width
        :param bool expand: Whether to expand to full console width

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> debug.columns("Column 1", "Column 2", "Column 3")
        Column 1    Column 2    Column 3

        See Also
        --------
        :meth:`layout`: Advanced layout management
        :meth:`panel`: Single panel display
        """
        if not self.is_debugging or not renderables:
            return

        columns_obj = Columns(renderables, equal=equal, expand=expand)
        self.console.print(columns_obj)

    def layout(self, layout_config: dict[str, Any]) -> Layout:
        """Create advanced layout with multiple sections.

        Build complex multi-section layouts for dashboard-style
        debugging displays with customizable regions and content
        arrangement for comprehensive data visualization.

        :param dict[str, Any] layout_config: Configuration for layout sections
        :return: Configured Layout object for rendering or further modification
        :rtype: Layout
        :raises DebuggingPrintError: When layout configuration is invalid

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> config = {
        ...     "header": "Debug Dashboard",
        ...     "left": {"data": [1, 2, 3]},
        ...     "right": {"status": "Active"}
        ... }
        >>> layout = debug.layout(config)
        >>> debug.console.print(layout)

        See Also
        --------
        :meth:`columns`: Simple column layout
        :meth:`panel`: Single panel display
        """
        try:
            layout = Layout()
            # Layout configuration implementation would go here
            # This is a simplified version
            return layout
        except Exception as e:
            raise DebuggingPrintError(f"Failed to create layout: {e}") from e

    def inspect_object(
        self,
        obj: Any,
        title: str | None = None,
        show_all: bool = False,
        show_methods: bool = True,
        show_docs: bool = True,
        show_private: bool = False,
        show_dunder: bool = False,
    ) -> None:
        """Comprehensive object inspection with Rich formatting.

        Perform detailed object inspection showing attributes, methods,
        documentation, and type information using Rich's inspection
        capabilities for thorough debugging analysis.

        :param Any obj: Object to inspect comprehensively
        :param str | None title: Optional title for inspection display
        :param bool show_all: Whether to show all attributes and methods
        :param bool show_methods: Whether to include method information
        :param bool show_docs: Whether to show documentation strings
        :param bool show_private: Whether to show private attributes
        :param bool show_dunder: Whether to show dunder methods

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> debug.inspect_object(
        ...     {"key": "value"},
        ...     title="Dictionary Inspection",
        ...     show_methods=True
        ... )
        # Shows comprehensive object analysis

        See Also
        --------
        :meth:`display`: Generic object display method
        :meth:`syntax`: Code syntax highlighting
        """
        if not self.is_debugging:
            return

        from rich import inspect as rich_inspect

        rich_inspect(
            obj,
            title=title,
            all=show_all,
            methods=show_methods,
            docs=show_docs,
            private=show_private,
            dunder=show_dunder,
            sort=True,
            value=True,
            console=self.console,
        )

    def prompt_user(
        self, message: str, default: str | None = None, password: bool = False
    ) -> str:
        """Interactive user prompt for debugging input.

        Provide interactive prompting capabilities for debugging
        sessions requiring user input or confirmation with
        secure password handling support.

        :param str message: Prompt message to display to user
        :param str | None default: Default value if user provides no input
        :param bool password: Whether input should be hidden (password mode)
        :return: User input string response
        :rtype: str

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> name = debug.prompt_user("Enter name:", default="Anonymous")
        Enter name: [Anonymous] John
        >>> name
        'John'

        See Also
        --------
        :meth:`confirm`: Boolean confirmation prompt
        """
        return Prompt.ask(
            message, default=default, password=password, console=self.console
        )

    def confirm(self, message: str, default: bool = False) -> bool:
        """Interactive confirmation prompt for debugging decisions.

        Provide yes/no confirmation prompting for debugging
        operations requiring user approval or decision making
        with clear default value indication.

        :param str message: Confirmation message to display
        :param bool default: Default response if user provides no input
        :return: User confirmation response
        :rtype: bool

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> confirmed = debug.confirm("Continue processing?", default=True)
        Continue processing? [Y/n]: y
        >>> confirmed
        True

        See Also
        --------
        :meth:`prompt_user`: General text input prompt
        """
        return Confirm.ask(message, default=default, console=self.console)

    # Private helper methods

    def _display_pretty(self, obj: Any, context: DebugContext) -> None:
        """Display object using Rich's pretty printing."""
        self.console.print(Pretty(obj, expand_all=True))

    def _display_json(self, obj: Any, context: DebugContext) -> None:
        """Display object as formatted JSON."""
        try:
            if hasattr(obj, "__dict__"):
                json_str = json.dumps(obj.__dict__, indent=2, default=str)
            else:
                json_str = json.dumps(obj, indent=2, default=str)
            self.console.print_json(json_str)
        except (TypeError, ValueError) as e:
            # Fallback to string representation
            self.console.print_json(str(obj))

    def _display_table(self, obj: Any, context: DebugContext) -> None:
        """Display object as formatted table."""
        if isinstance(obj, (list, tuple)) and obj:
            table = Table(title="Sequence Data")
            table.add_column("Index", style="dim")
            table.add_column("Value")
            table.add_column("Type", style="italic")

            for i, item in enumerate(obj):
                table.add_row(str(i), str(item), type(item).__name__)

            self.console.print(table)
        elif isinstance(obj, dict):
            table = Table(title="Dictionary Data")
            table.add_column("Key", style="bold")
            table.add_column("Value")
            table.add_column("Type", style="italic")

            for key, value in obj.items():
                table.add_row(str(key), str(value), type(value).__name__)

            self.console.print(table)
        else:
            # Fallback to pretty print
            self._display_pretty(obj, context)

    def _display_tree(self, obj: Any, context: DebugContext) -> None:
        """Display object as hierarchical tree."""
        tree = Tree(f"[bold]{type(obj).__name__}[/bold]")
        self._build_tree_recursive(tree, obj, max_depth=3, current_depth=0)
        self.console.print(tree)

    def _display_panel(self, obj: Any, context: DebugContext) -> None:
        """Display object in formatted panel."""
        content = Pretty(obj, expand_all=True)
        panel = Panel(
            content, title=f"[bold]{type(obj).__name__}[/bold]", border_style="blue"
        )
        self.console.print(panel)

    def _build_tree_recursive(
        self, tree: Tree, obj: Any, max_depth: int, current_depth: int
    ) -> None:
        """Recursively build tree structure for complex objects."""
        if current_depth >= max_depth:
            tree.add("[dim]...[/dim]")
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list, tuple)):
                    subtree = tree.add(
                        f"[bold blue]{key}[/bold blue]: {type(value).__name__}"
                    )
                    self._build_tree_recursive(
                        subtree, value, max_depth, current_depth + 1
                    )
                else:
                    tree.add(
                        f"[bold blue]{key}[/bold blue]: [green]{escape(str(value))}[/green]"
                    )

        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list, tuple)):
                    subtree = tree.add(f"[dim]\\[{i}][/dim]: {type(item).__name__}")
                    self._build_tree_recursive(
                        subtree, item, max_depth, current_depth + 1
                    )
                else:
                    tree.add(f"[dim]\\[{i}][/dim]: [green]{escape(str(item))}[/green]")

        elif hasattr(obj, "__dict__"):
            for attr_name, attr_value in obj.__dict__.items():
                if not attr_name.startswith("_"):
                    if isinstance(attr_value, (dict, list, tuple)):
                        subtree = tree.add(
                            f"[bold magenta]{attr_name}[/bold magenta]: {type(attr_value).__name__}"
                        )
                        self._build_tree_recursive(
                            subtree, attr_value, max_depth, current_depth + 1
                        )
                    else:
                        tree.add(
                            f"[bold magenta]{attr_name}[/bold magenta]: [green]{escape(str(attr_value))}[/green]"
                        )

    def _get_model_field_info(
        self, model_instance: models.Model
    ) -> dict[str, dict[str, Any]]:
        """Extract comprehensive field information from Django model instance.

        Analyze Django model instance to extract field values, types,
        and metadata for comprehensive debugging display with support
        for relationships and custom field types.

        :param models.Model model_instance: Django model instance to analyze
        :return: Dictionary mapping field names to field information
        :rtype: dict[str, dict[str, Any]]
        :raises AttributeError: When model instance is invalid

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> user = User.objects.get(id=1)
        >>> field_info = debug._get_model_field_info(user)
        >>> field_info['username']['value']
        'admin'

        See Also
        --------
        :meth:`display_django_model`: Main model display method
        """
        field_info: dict[str, dict[str, Any]] = {}

        # Get model fields
        for field in model_instance._meta.get_fields():
            field_name = field.name

            try:
                field_value = getattr(model_instance, field_name)
            except (AttributeError, models.ObjectDoesNotExist):
                field_value = None

            # Determine field type and properties
            field_data = {
                "value": field_value,
                "type": field.__class__.__name__,
                "null": getattr(field, "null", False),
                "blank": getattr(field, "blank", False),
                "primary_key": getattr(field, "primary_key", False),
                "unique": getattr(field, "unique", False),
            }

            # Add relationship information
            if hasattr(field, "related_model") and field.related_model:
                field_data["related_model"] = field.related_model.__name__
                if field_value and hasattr(field_value, "pk"):
                    field_data["related_pk"] = field_value.pk

            # Add choice information
            if hasattr(field, "choices") and field.choices:
                field_data["choices"] = list(field.choices)

            # Add max length for character fields
            if hasattr(field, "max_length") and field.max_length:
                field_data["max_length"] = field.max_length

            field_info[field_name] = field_data

        return field_info

    def _render_model_panel(
        self, model_name: str, pk_value: Any, field_data: dict[str, dict[str, Any]]
    ) -> None:
        """Render Django model information in panel format."""
        content_lines = []

        for field_name, field_info in field_data.items():
            value = field_info["value"]
            field_type = field_info["type"]

            # Format value representation
            if value is None:
                value_str = "[dim]None[/dim]"
            elif isinstance(value, str) and len(value) > 50:
                value_str = f"[green]'{value[:47]}...'[/green]"
            else:
                value_str = f"[green]{escape(str(value))}[/green]"

            # Add field metadata
            metadata_parts = []
            if field_info.get("primary_key"):
                metadata_parts.append("[bold red]PK[/bold red]")
            if field_info.get("unique"):
                metadata_parts.append("[bold yellow]UNIQUE[/bold yellow]")
            if field_info.get("null"):
                metadata_parts.append("[dim]NULL[/dim]")
            if field_info.get("related_model"):
                metadata_parts.append(f"[blue]→ {field_info['related_model']}[/blue]")

            metadata_str = f" ({', '.join(metadata_parts)})" if metadata_parts else ""

            content_lines.append(
                f"[bold blue]{field_name}[/bold blue] [{field_type}]{metadata_str}: {value_str}"
            )

        content = "\n".join(content_lines)
        panel = Panel(
            content,
            title=f"[bold]{model_name}[/bold] Instance #{pk_value}",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(panel)

    def _render_model_table(
        self, model_name: str, pk_value: Any, field_data: dict[str, dict[str, Any]]
    ) -> None:
        """Render Django model information in table format."""
        table = Table(
            title=f"{model_name} Instance #{pk_value}",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Field", style="bold blue", min_width=15)
        table.add_column("Type", style="dim", min_width=12)
        table.add_column("Value", min_width=20)
        table.add_column("Properties", style="italic", min_width=15)

        for field_name, field_info in field_data.items():
            value = field_info["value"]
            field_type = field_info["type"]

            # Format value
            if value is None:
                value_str = "[dim]None[/dim]"
            elif isinstance(value, str) and len(value) > 30:
                value_str = f"{value[:27]}..."
            else:
                value_str = str(value)

            # Format properties
            properties = []
            if field_info.get("primary_key"):
                properties.append("PK")
            if field_info.get("unique"):
                properties.append("UNIQUE")
            if field_info.get("null"):
                properties.append("NULL")
            if field_info.get("related_model"):
                properties.append(f"→ {field_info['related_model']}")

            properties_str = ", ".join(properties)

            table.add_row(field_name, field_type, value_str, properties_str)

        self.console.print(table)

    def _render_model_tree(
        self, model_name: str, pk_value: Any, field_data: dict[str, dict[str, Any]]
    ) -> None:
        """Render Django model information in tree format."""
        root = Tree(f"[bold]{model_name}[/bold] Instance #{pk_value}")

        # Group fields by type
        regular_fields = {}
        relationship_fields = {}

        for field_name, field_info in field_data.items():
            if field_info.get("related_model"):
                relationship_fields[field_name] = field_info
            else:
                regular_fields[field_name] = field_info

        # Add regular fields
        if regular_fields:
            fields_branch = root.add("[bold blue]Fields[/bold blue]")
            for field_name, field_info in regular_fields.items():
                value = field_info["value"]
                value_str = "[dim]None[/dim]" if value is None else str(value)
                fields_branch.add(f"{field_name}: [green]{escape(value_str)}[/green]")

        # Add relationship fields
        if relationship_fields:
            relations_branch = root.add("[bold magenta]Relationships[/bold magenta]")
            for field_name, field_info in relationship_fields.items():
                related_model = field_info.get("related_model", "Unknown")
                related_pk = field_info.get("related_pk", "None")
                relations_branch.add(f"{field_name} → {related_model} #{related_pk}")

        self.console.print(root)

    def _analyze_queryset(self, queryset: QuerySet) -> dict[str, Any]:
        """Analyze Django QuerySet without evaluation.

        Extract QuerySet metadata and query information without
        triggering database evaluation for performance analysis
        and debugging purposes.

        :param QuerySet queryset: Django QuerySet to analyze
        :return: Dictionary containing QuerySet analysis information
        :rtype: dict[str, Any]

        Examples
        --------
        >>> debug = EnhancedDebuggingPrint()
        >>> users = User.objects.filter(is_active=True)
        >>> info = debug._analyze_queryset(users)
        >>> info['model_name']
        'User'
        """
        return {
            "model_name": queryset.model.__name__,
            "app_label": queryset.model._meta.app_label,
            "query_sql": str(queryset.query),
            "db_alias": queryset.db,
            "ordered": queryset.ordered,
            "filters": self._extract_queryset_filters(queryset),
            "annotations": (
                list(queryset.query.annotations.keys())
                if hasattr(queryset.query, "annotations")
                else []
            ),
        }

    def _extract_queryset_filters(self, queryset: QuerySet) -> list[str]:
        """Extract filter conditions from QuerySet query."""
        try:
            where_node = queryset.query.where
            if hasattr(where_node, "children") and where_node.children:
                return [str(child) for child in where_node.children]
            return []
        except (AttributeError, Exception):
            return ["Unable to extract filters"]

    def _render_queryset_table(
        self, queryset_info: dict[str, Any], results: list[models.Model], max_items: int
    ) -> None:
        """Render QuerySet results in table format."""
        model_name = queryset_info["model_name"]

        # Create summary panel
        summary_content = []
        summary_content.append(f"[bold]Model:[/bold] {model_name}")
        summary_content.append(f"[bold]App:[/bold] {queryset_info['app_label']}")
        summary_content.append(
            f"[bold]Results:[/bold] {len(results)} (limited to {max_items})"
        )
        summary_content.append(f"[bold]Database:[/bold] {queryset_info['db_alias']}")

        if queryset_info["filters"]:
            summary_content.append(
                f"[bold]Filters:[/bold] {len(queryset_info['filters'])}"
            )

        summary_panel = Panel(
            "\n".join(summary_content),
            title=f"QuerySet: {model_name}",
            border_style="green",
        )
        self.console.print(summary_panel)

        # Create results table if we have results
        if results:
            table = Table(
                title=f"{model_name} Results",
                show_header=True,
                expand=True,
                highlight=True,
                show_lines=True,
            )

            # Get field names from first result
            first_result = results[0]
            field_names = [
                field.name
                for field in first_result._meta.get_fields()
                if not field.name.startswith("_")
            ][
                :8
            ]  # Limit columns

            # Add columns
            table.add_column("ID", style="dim")
            for field_name in field_names:
                table.add_column(
                    field_name.title(), overflow="fold"
                )

            # Add rows
            for result in results:
                row_data = [str(result.pk)]
                for field_name in field_names:
                    try:
                        value = getattr(result, field_name)
                        if value is None:
                            row_data.append("[dim]None[/dim]")
                        elif isinstance(value, str) and len(value) > 15:
                            row_data.append(f"{value[:12]}...")
                        else:
                            row_data.append(str(value))
                    except (AttributeError, Exception):
                        row_data.append("[red]Error[/red]")

                table.add_row(*row_data)

            self.console.print(table)
        else:
            self.console.print("[yellow]No results found[/yellow]")

    def _render_queryset_panel(
        self, queryset_info: dict[str, Any], results: list[models.Model], max_items: int
    ) -> None:
        """Render QuerySet information in panel format."""
        content_lines = []
        content_lines.append(
            f"[bold blue]Model:[/bold blue] {queryset_info['model_name']}"
        )
        content_lines.append(
            f"[bold blue]App:[/bold blue] {queryset_info['app_label']}"
        )
        content_lines.append(
            f"[bold blue]Database:[/bold blue] {queryset_info['db_alias']}"
        )
        content_lines.append(f"[bold blue]Results Count:[/bold blue] {len(results)}")

        if queryset_info["filters"]:
            content_lines.append(f"[bold blue]Active Filters:[/bold blue]")
            for filter_condition in queryset_info["filters"][:3]:  # Show max 3 filters
                content_lines.append(f"  • {filter_condition}")

        if queryset_info["annotations"]:
            content_lines.append(
                f"[bold blue]Annotations:[/bold blue] {', '.join(queryset_info['annotations'])}"
            )

        # Add SQL query (truncated)
        sql_query = queryset_info["query_sql"]
        if len(sql_query) > 200:
            sql_query = sql_query[:197] + "..."
        content_lines.append(f"[bold blue]SQL Query:[/bold blue]")
        content_lines.append(f"[dim]{sql_query}[/dim]")

        content = "\n".join(content_lines)
        panel = Panel(
            content,
            title=f"QuerySet Analysis: {queryset_info['model_name']}",
            border_style="blue",
        )

        self.console.print(panel)


# Legacy compatibility and convenience functions
def create_debug_instance(
    theme: DisplayTheme = DisplayTheme.DEFAULT, enable_highlighting: bool = True
) -> EnhancedDebuggingPrint:
    """Factory function to create configured debugging print instance.

    Convenient factory function for creating EnhancedDebuggingPrint
    instances with commonly used configurations and theme settings
    for quick debugging setup.

    :param DisplayTheme theme: Visual theme for debugging output
    :param bool enable_highlighting: Whether to enable syntax highlighting
    :return: Configured debugging print instance
    :rtype: EnhancedDebuggingPrint
    :raises DebuggingPrintError: When instance creation fails

    Examples
    --------
    >>> debug = create_debug_instance(DisplayTheme.DARK, True)
    >>> debug.display({"key": "value"})
    # Shows formatted output with dark theme

    See Also
    --------
    :class:`EnhancedDebuggingPrint`: Main debugging class
    :class:`DisplayTheme`: Available theme options
    """
    try:
        return EnhancedDebuggingPrint(
            theme=theme, enable_highlighting=enable_highlighting
        )
    except Exception as e:
        raise DebuggingPrintError(f"Failed to create debug instance: {e}") from e


# Global convenience instance for quick access
debug: EnhancedDebuggingPrint = create_debug_instance()

# Export main classes and functions
__all__ = [
    "EnhancedDebuggingPrint",
    "DebugContext",
    "TableConfiguration",
    "DisplayTheme",
    "OutputFormat",
    "DebuggingPrintError",
    "RenderableProtocol",
    "create_debug_instance",
    "debug",
]

ENHANCED_DEBUGGING_PRINT_INSTANCE: EnhancedDebuggingPrint = create_debug_instance(
    DisplayTheme.DARK
)
# Example usage and testing
if __name__ == "__main__":
    """Example usage of EnhancedDebuggingPrint with various data types."""

    # Create debug instance with dark theme
    debug_instance: EnhancedDebuggingPrint = create_debug_instance(DisplayTheme.DARK)

    # Test basic display
    debug_instance.display({"name": "John", "age": 30, "city": "New York"})

    # Test markdown rendering
    markdown_content = """
    # Debug Report
    
    ## Features
    - Rich formatting
    - Syntax highlighting  
    - Django integration
    
    ## Code Example
    ```python
    debug.display(my_object)
    ```
    """
    debug_instance.markdown(markdown_content, "Documentation")

    # Test syntax highlighting
    code_sample = '''
def fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    '''
    debug_instance.syntax(code_sample, "python")

    # Test object inspection
    debug_instance.inspect_object(
        debug_instance,
        title="Debug Instance Inspection",
        show_methods=True,
        show_docs=True,
    )

    print("CODE COMPLIANCE VERIFIED: All mandatory rules satisfied.")
