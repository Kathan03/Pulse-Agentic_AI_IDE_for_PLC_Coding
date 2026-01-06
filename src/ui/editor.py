"""
Tabbed Editor Manager Component for Pulse IDE.
"""

import flet as ft
import re
from pathlib import Path
from src.ui.theme import VSCodeColors, Fonts, Spacing, create_logo_image
from src.ui.log_panel import LogPanel
from src.ui.components.settings_page import SettingsPage

class SyntaxColors:
    """VS Code Dark+ inspired syntax colors."""
    KEYWORD = "#569CD6"       # Blue - language keywords
    CONTROL_FLOW = "#C586C0"  # Purple - control flow statements
    STRING = "#CE9178"        # Orange - string literals
    COMMENT = "#6A9955"       # Green - comments
    DECORATOR = "#DCDCAA"     # Yellow - decorators/attributes
    NUMBER = "#B5CEA8"        # Light Green - numeric literals
    CLASS_NAME = "#4EC9B0"    # Teal - class/type names
    FUNCTION = "#DCDCAA"      # Yellow - function names
    BUILTIN = "#4EC9B0"       # Teal/Cyan - built-in functions
    DEFAULT = "#D4D4D4"       # Light Grey - default text
    SELF = "#9CDCFE"          # Light Blue - self/this references
    OPERATOR = "#D4D4D4"      # Light Grey - operators
    VARIABLE = "#9CDCFE"      # Light Blue - variables/identifiers
    TYPE = "#4EC9B0"          # Teal - type annotations
    CONSTANT = "#4FC1FF"      # Bright Blue - constants
    PROPERTY = "#9CDCFE"      # Light Blue - properties/keys
    TAG = "#569CD6"           # Blue - markdown headers/tags
    LINK = "#3794FF"          # Bright Blue - links/URLs
    BOLD = "#D4D4D4"          # Light Grey - bold text
    ITALIC = "#D4D4D4"        # Light Grey - italic text


class BaseSyntaxHighlighter:
    """
    Base class for regex-based syntax highlighting.
    Subclasses define PATTERNS and COLOR_MAP for their language.
    """
    PATTERNS = []  # List of (regex_pattern, group_name) tuples
    COLOR_MAP = {}  # Map group_name -> color

    @classmethod
    def get_combined_pattern(cls):
        return "|".join([p[0] for p in cls.PATTERNS])

    @classmethod
    def highlight(cls, code: str, font_size: float, font_family: str, line_height: float) -> list[ft.TextSpan]:
        spans = []
        last_pos = 0
        combined = cls.get_combined_pattern()

        if not combined:
            return [ft.TextSpan(
                text=code,
                style=ft.TextStyle(
                    color=SyntaxColors.DEFAULT,
                    size=font_size,
                    font_family=font_family,
                    height=line_height
                )
            )]

        for match in re.finditer(combined, code, re.MULTILINE | re.IGNORECASE):
            start = match.start()
            end = match.end()

            if start > last_pos:
                spans.append(ft.TextSpan(
                    text=code[last_pos:start],
                    style=ft.TextStyle(
                        color=SyntaxColors.DEFAULT,
                        size=font_size,
                        font_family=font_family,
                        height=line_height
                    )
                ))

            group_name = match.lastgroup
            color = cls.COLOR_MAP.get(group_name, SyntaxColors.DEFAULT)

            spans.append(ft.TextSpan(
                text=match.group(),
                style=ft.TextStyle(
                    color=color,
                    size=font_size,
                    font_family=font_family,
                    height=line_height
                )
            ))

            last_pos = end

        if last_pos < len(code):
            spans.append(ft.TextSpan(
                text=code[last_pos:],
                style=ft.TextStyle(
                    color=SyntaxColors.DEFAULT,
                    size=font_size,
                    font_family=font_family,
                    height=line_height
                )
            ))

        return spans


class PythonHighlighter(BaseSyntaxHighlighter):
    """Syntax highlighter for Python."""

    PATTERNS = [
        (r'(?P<PY_STRING>(\"\"\"[\s\S]*?\"\"\")|(\'\'\'[\s\S]*?\'\'\')|(\"[^\"\\]*(?:\\.[^\"\\]*)*\")|(\'[^\'\\]*(?:\\.[^\'\\]*)*\'))', "PY_STRING"),
        (r'(?P<PY_COMMENT>#.*?$)', "PY_COMMENT"),
        (r'\b(?P<PY_KEYWORD>def|class|lambda|None|True|False|await|async|del|global|nonlocal|assert)\b', "PY_KEYWORD"),
        (r'\b(?P<PY_CONTROL>if|else|elif|return|import|from|while|for|in|try|except|with|as|pass|break|continue|raise|yield|finally|is|not|and|or|match|case)\b', "PY_CONTROL"),
        (r'\b(?P<PY_BUILTIN>print|len|range|open|str|int|float|bool|list|dict|set|tuple|super|type|input|enumerate|zip|isinstance|issubclass|abs|all|any|bin|chr|dir|divmod|eval|exec|exit|filter|format|getattr|hasattr|help|hex|id|iter|map|max|min|next|object|oct|ord|pow|property|repr|reversed|round|setattr|slice|sorted|staticmethod|classmethod|sum|vars|__init__|__str__|__repr__|__call__|__len__|__iter__|__next__|__enter__|__exit__)\b', "PY_BUILTIN"),
        (r'\b(?P<PY_SELF>self|cls)\b', "PY_SELF"),
        (r'(?P<PY_DECORATOR>@[\w\.]+)', "PY_DECORATOR"),
        (r'\bclass\s+(?P<PY_CLASS>\w+)', "PY_CLASS"),
        (r'\bdef\s+(?P<PY_FUNC>\w+)', "PY_FUNC"),
        (r'\b(?P<PY_NUMBER>\d+(\.\d+)?(e[+-]?\d+)?|0x[0-9a-fA-F]+|0b[01]+|0o[0-7]+)\b', "PY_NUMBER"),
        (r'(?P<PY_TYPE>:\s*(int|str|float|bool|list|dict|set|tuple|None|Any|Optional|Union|List|Dict|Set|Tuple|Callable))', "PY_TYPE"),
    ]

    COLOR_MAP = {
        "PY_STRING": SyntaxColors.STRING,
        "PY_COMMENT": SyntaxColors.COMMENT,
        "PY_KEYWORD": SyntaxColors.KEYWORD,
        "PY_CONTROL": SyntaxColors.CONTROL_FLOW,
        "PY_BUILTIN": SyntaxColors.BUILTIN,
        "PY_SELF": SyntaxColors.SELF,
        "PY_DECORATOR": SyntaxColors.DECORATOR,
        "PY_CLASS": SyntaxColors.CLASS_NAME,
        "PY_FUNC": SyntaxColors.FUNCTION,
        "PY_NUMBER": SyntaxColors.NUMBER,
        "PY_TYPE": SyntaxColors.TYPE,
    }


class StructuredTextHighlighter(BaseSyntaxHighlighter):
    """
    Syntax highlighter for IEC 61131-3 Structured Text (ST).
    Used for PLC programming.
    """

    PATTERNS = [
        # Comments (single-line // and block (* *))
        (r'(?P<ST_COMMENT>//.*?$|\(\*[\s\S]*?\*\))', "ST_COMMENT"),
        # Strings
        (r'(?P<ST_STRING>\'[^\']*\'|\"[^\"]*\")', "ST_STRING"),
        # Program structure keywords
        (r'\b(?P<ST_STRUCTURE>PROGRAM|END_PROGRAM|FUNCTION|END_FUNCTION|FUNCTION_BLOCK|END_FUNCTION_BLOCK|VAR|VAR_INPUT|VAR_OUTPUT|VAR_IN_OUT|VAR_TEMP|VAR_GLOBAL|END_VAR|CONSTANT|RETAIN|PERSISTENT|TYPE|END_TYPE|STRUCT|END_STRUCT|ARRAY|OF)\b', "ST_STRUCTURE"),
        # Control flow keywords
        (r'\b(?P<ST_CONTROL>IF|THEN|ELSE|ELSIF|END_IF|CASE|OF|END_CASE|FOR|TO|BY|DO|END_FOR|WHILE|END_WHILE|REPEAT|UNTIL|END_REPEAT|EXIT|RETURN|CONTINUE)\b', "ST_CONTROL"),
        # Data types
        (r'\b(?P<ST_TYPE>BOOL|BYTE|WORD|DWORD|LWORD|SINT|INT|DINT|LINT|USINT|UINT|UDINT|ULINT|REAL|LREAL|TIME|DATE|TIME_OF_DAY|TOD|DATE_AND_TIME|DT|STRING|WSTRING|ANY|ANY_NUM|ANY_INT|ANY_REAL|ANY_BIT)\b', "ST_TYPE"),
        # Boolean literals
        (r'\b(?P<ST_BOOL>TRUE|FALSE)\b', "ST_BOOL"),
        # Operators
        (r'\b(?P<ST_OPERATOR>AND|OR|XOR|NOT|MOD)\b', "ST_OPERATOR"),
        # Standard function blocks (Timers, Counters, Triggers)
        (r'\b(?P<ST_FB>TON|TOF|TP|CTU|CTD|CTUD|R_TRIG|F_TRIG|SR|RS|SEMA)\b', "ST_FB"),
        # Standard functions
        (r'\b(?P<ST_FUNC>ABS|SQRT|LN|LOG|EXP|SIN|COS|TAN|ASIN|ACOS|ATAN|ADD|SUB|MUL|DIV|GT|GE|EQ|LE|LT|NE|SEL|MAX|MIN|LIMIT|MUX|SHL|SHR|ROL|ROR|LEN|LEFT|RIGHT|MID|CONCAT|INSERT|DELETE|REPLACE|FIND)\b', "ST_FUNC"),
        # Time literals (T#, TIME#)
        (r'(?P<ST_TIME>T#[\d_]+(?:d|h|m|s|ms|us|ns)?(?:[\d_]+(?:h|m|s|ms|us|ns)?)*|TIME#[\d_]+(?:d|h|m|s|ms|us|ns)?(?:[\d_]+(?:h|m|s|ms|us|ns)?)*)', "ST_TIME"),
        # Numbers (including typed literals like INT#123)
        (r'(?P<ST_NUMBER>\b\d+(\.\d+)?(e[+-]?\d+)?|\b16#[0-9A-Fa-f]+|\b8#[0-7]+|\b2#[01]+|\b\w+#\d+)\b', "ST_NUMBER"),
        # I/O addresses (%IX0.0, %QW1, %MW100)
        (r'(?P<ST_ADDRESS>%[IQM][XBWDL]?[\d\.]+)', "ST_ADDRESS"),
    ]

    COLOR_MAP = {
        "ST_COMMENT": SyntaxColors.COMMENT,
        "ST_STRING": SyntaxColors.STRING,
        "ST_STRUCTURE": SyntaxColors.KEYWORD,
        "ST_CONTROL": SyntaxColors.CONTROL_FLOW,
        "ST_TYPE": SyntaxColors.TYPE,
        "ST_BOOL": SyntaxColors.CONSTANT,
        "ST_OPERATOR": SyntaxColors.KEYWORD,
        "ST_FB": SyntaxColors.CLASS_NAME,
        "ST_FUNC": SyntaxColors.BUILTIN,
        "ST_TIME": SyntaxColors.NUMBER,
        "ST_NUMBER": SyntaxColors.NUMBER,
        "ST_ADDRESS": SyntaxColors.VARIABLE,
    }


class JsonHighlighter(BaseSyntaxHighlighter):
    """Syntax highlighter for JSON."""

    PATTERNS = [
        # Strings (property names and values)
        (r'(?P<JSON_KEY>\"[^\"]+\"\s*(?=:))', "JSON_KEY"),
        (r'(?P<JSON_STRING>\"[^\"]*\")', "JSON_STRING"),
        # Numbers
        (r'(?P<JSON_NUMBER>-?\b\d+(\.\d+)?([eE][+-]?\d+)?\b)', "JSON_NUMBER"),
        # Booleans and null
        (r'\b(?P<JSON_BOOL>true|false)\b', "JSON_BOOL"),
        (r'\b(?P<JSON_NULL>null)\b', "JSON_NULL"),
    ]

    COLOR_MAP = {
        "JSON_KEY": SyntaxColors.PROPERTY,
        "JSON_STRING": SyntaxColors.STRING,
        "JSON_NUMBER": SyntaxColors.NUMBER,
        "JSON_BOOL": SyntaxColors.CONSTANT,
        "JSON_NULL": SyntaxColors.CONSTANT,
    }


class MarkdownHighlighter(BaseSyntaxHighlighter):
    """Syntax highlighter for Markdown."""

    PATTERNS = [
        # Code blocks (fenced)
        (r'(?P<MD_CODEBLOCK>```[\s\S]*?```)', "MD_CODEBLOCK"),
        # Inline code
        (r'(?P<MD_CODE>`[^`]+`)', "MD_CODE"),
        # Headers
        (r'(?P<MD_HEADER>^#{1,6}\s+.*$)', "MD_HEADER"),
        # Bold
        (r'(?P<MD_BOLD>\*\*[^*]+\*\*|__[^_]+__)', "MD_BOLD"),
        # Italic
        (r'(?P<MD_ITALIC>\*[^*]+\*|_[^_]+_)', "MD_ITALIC"),
        # Links
        (r'(?P<MD_LINK>\[([^\]]+)\]\([^\)]+\))', "MD_LINK"),
        # URLs
        (r'(?P<MD_URL>https?://[^\s\)]+)', "MD_URL"),
        # Blockquotes
        (r'(?P<MD_QUOTE>^>\s+.*$)', "MD_QUOTE"),
        # Lists
        (r'(?P<MD_LIST>^[\s]*[-*+]\s+|^\s*\d+\.\s+)', "MD_LIST"),
    ]

    COLOR_MAP = {
        "MD_CODEBLOCK": SyntaxColors.STRING,
        "MD_CODE": SyntaxColors.STRING,
        "MD_HEADER": SyntaxColors.TAG,
        "MD_BOLD": SyntaxColors.BOLD,
        "MD_ITALIC": SyntaxColors.ITALIC,
        "MD_LINK": SyntaxColors.LINK,
        "MD_URL": SyntaxColors.LINK,
        "MD_QUOTE": SyntaxColors.COMMENT,
        "MD_LIST": SyntaxColors.KEYWORD,
    }


class PlainTextHighlighter(BaseSyntaxHighlighter):
    """No highlighting - plain text."""
    PATTERNS = []
    COLOR_MAP = {}


class SyntaxHighlighterFactory:
    """
    Factory to get the appropriate syntax highlighter based on file extension.
    """

    EXTENSION_MAP = {
        # Python
        '.py': PythonHighlighter,
        '.pyw': PythonHighlighter,
        '.pyi': PythonHighlighter,
        # Structured Text (PLC)
        '.st': StructuredTextHighlighter,
        '.scl': StructuredTextHighlighter,  # Siemens SCL
        '.pou': StructuredTextHighlighter,  # Program Organization Unit
        # JSON
        '.json': JsonHighlighter,
        '.jsonc': JsonHighlighter,
        # Markdown
        '.md': MarkdownHighlighter,
        '.markdown': MarkdownHighlighter,
        '.mdown': MarkdownHighlighter,
        # Config files (use JSON highlighting)
        '.toml': JsonHighlighter,
        '.yaml': JsonHighlighter,
        '.yml': JsonHighlighter,
    }

    @classmethod
    def get_highlighter(cls, file_extension: str) -> type:
        """
        Get the appropriate highlighter class for a file extension.
        Returns PlainTextHighlighter if no specific highlighter is found.
        """
        ext = file_extension.lower()
        return cls.EXTENSION_MAP.get(ext, PlainTextHighlighter)

    @classmethod
    def highlight(cls, code: str, file_extension: str, font_size: float,
                  font_family: str, line_height: float) -> list[ft.TextSpan]:
        """
        Highlight code using the appropriate highlighter for the file extension.
        """
        highlighter = cls.get_highlighter(file_extension)
        return highlighter.highlight(code, font_size, font_family, line_height)


class EditorManager:
    """
    Tabbed editor manager component.
    """

    def __init__(self, log_panel=None, file_manager=None, dirty_callback=None, query_handler=None):
        self.log_panel_template = log_panel
        self.file_manager = file_manager
        self.query_handler = query_handler
        self.tabs_control = None
        self.welcome_screen = None
        self.open_files = {}
        self.tab_editors = {}
        self.tab_highlighters = {}
        self.tab_line_numbers = {}
        self.agent_tabs = {}
        self.agent_session_counter = 0
        self.current_mode = "Agent Mode"
        self.dirty_files = set()
        self.dirty_callback = dirty_callback
        self.original_contents = {}
        self.container = self._build()

    def _build(self):
        self.welcome_screen = self._create_welcome_screen()
        divider_color = getattr(VSCodeColors, 'BORDER', ft.Colors.OUTLINE)

        self.tabs_control = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            tabs=[],
            expand=True,
            on_change=self._on_tab_changed,
            indicator_color=VSCodeColors.TAB_ACTIVE_BORDER,
            label_color=VSCodeColors.TAB_ACTIVE_FOREGROUND,
            unselected_label_color=VSCodeColors.TAB_INACTIVE_FOREGROUND,
            visible=False,
            divider_color=divider_color,
        )

        return ft.Container(
            content=ft.Stack(
                controls=[
                    self.welcome_screen,
                    self.tabs_control,
                ],
            ),
            expand=True,
            bgcolor=VSCodeColors.EDITOR_BACKGROUND,
        )

    def _create_welcome_screen(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.DESCRIPTION_OUTLINED,
                        size=64,
                        color=VSCodeColors.EDITOR_LINE_NUMBER,
                    ),
                    ft.Text(
                        "Please select a file to view",
                        size=Fonts.FONT_SIZE_LARGE,
                        color=VSCodeColors.EDITOR_FOREGROUND,
                        weight=ft.FontWeight.W_300,
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        "Open a file from the workspace or start a Pulse Agent session",
                        size=Fonts.FONT_SIZE_SMALL,
                        color=VSCodeColors.EDITOR_LINE_NUMBER,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            bgcolor=VSCodeColors.EDITOR_BACKGROUND,
        )

    def _update_visibility(self):
        has_tabs = len(self.tabs_control.tabs) > 0
        self.welcome_screen.visible = not has_tabs
        self.tabs_control.visible = has_tabs
        if self.container.page:
            self.welcome_screen.update()
            self.tabs_control.update()

    def get_control(self):
        return self.container

    def _handle_theme_change(self, theme_name: str):
        if self.container.page:
            self.container.page.update()

    def open_settings_page(self):
        for idx, tab in enumerate(self.tabs_control.tabs):
            is_settings = False
            if hasattr(tab, 'tab_content') and tab.tab_content:
                if hasattr(tab.tab_content, 'controls'):
                    is_settings = any(
                        isinstance(c, ft.Text) and "Pulse Settings" in c.value
                        for c in tab.tab_content.controls
                    )
            if is_settings:
                self.tabs_control.selected_index = idx
                self.tabs_control.visible = True
                if self.welcome_screen:
                    self.welcome_screen.visible = False
                if self.tabs_control.page:
                    self.container.update()
                return

        try:
            settings_page = SettingsPage(on_theme_change=self._handle_theme_change)
        except Exception as e:
            print(f"Error creating SettingsPage: {e}")
            return

        def close_settings_tab(e):
            for idx, tab in enumerate(self.tabs_control.tabs):
                if hasattr(tab, 'tab_content') and any(
                    isinstance(c, ft.Text) and "Pulse Settings" in c.value
                    for c in (tab.tab_content.controls if hasattr(tab.tab_content, 'controls') else [])
                ):
                    self.tabs_control.tabs.pop(idx)
                    if self.tabs_control.tabs:
                        self.tabs_control.selected_index = max(0, idx - 1)
                    if self.tabs_control.page:
                        self.container.update()
                    return

        close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=14,
            tooltip="Close settings",
            on_click=close_settings_tab,
            icon_color=VSCodeColors.TAB_INACTIVE_FOREGROUND,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.HOVERED: VSCodeColors.BUTTON_SECONDARY_HOVER,
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                },
                overlay_color=VSCodeColors.ERROR_FOREGROUND,
                padding=ft.padding.all(2),
            ),
        )

        tab_label = ft.Row(
            controls=[
                ft.Icon(ft.Icons.SETTINGS, size=16),
                ft.Text("Pulse Settings", size=13),
                close_button,
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.START,
        )

        new_tab = ft.Tab(
            tab_content=tab_label,
            content=settings_page.get_control(),
        )

        self.tabs_control.tabs.append(new_tab)
        self.tabs_control.selected_index = len(self.tabs_control.tabs) - 1
        self.tabs_control.visible = True
        if self.welcome_screen:
            self.welcome_screen.visible = False
        if self.tabs_control.page:
            self.container.update()

    def open_agent(self, mode="Agent Mode"):
        self.current_mode = mode
        self.agent_session_counter += 1

        def handle_user_input(text: str):
            if self.query_handler:
                self.query_handler(text, new_log_panel)
            else:
                new_log_panel.add_log("❌ Query handler not configured", "error")

        new_log_panel = LogPanel(on_submit=handle_user_input)
        session_label = f" (Session {self.agent_session_counter})" if self.agent_session_counter > 1 else ""
        tab_title = f"Pulse Agent - {mode}{session_label}"
        tab_logo = create_logo_image(width=42, height=42)

        def close_this_agent_tab(e):
            for idx, panel in self.agent_tabs.items():
                if panel == new_log_panel:
                    self.close_tab_by_index(idx)
                    break

        close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=14,
            tooltip="Close tab",
            on_click=close_this_agent_tab,
            icon_color=VSCodeColors.TAB_INACTIVE_FOREGROUND,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.HOVERED: VSCodeColors.BUTTON_SECONDARY_HOVER,
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                },
                overlay_color=VSCodeColors.ERROR_FOREGROUND,
                padding=ft.padding.all(2),
            ),
        )

        tab_label = ft.Row(
            controls=[
                ft.Icon(name=tab_logo, size=16),
                ft.Text(tab_title, size=13),
                close_button,
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.START,
        )

        tab_content = ft.Container(
            content=new_log_panel.get_control(),
            expand=True,
            bgcolor=VSCodeColors.EDITOR_BACKGROUND,
            padding=Spacing.PADDING_MEDIUM,
        )

        agent_tab = ft.Tab(
            tab_content=tab_label,
            content=tab_content,
        )

        self.tabs_control.tabs.insert(0, agent_tab)
        new_tab_index = 0

        files_to_update = list(self.open_files.items())
        for file_path, old_index in files_to_update:
            self.open_files[file_path] = old_index + 1

        editors_to_update = list(self.tab_editors.items())
        self.tab_editors = {}
        for old_index, editor in editors_to_update:
            self.tab_editors[old_index + 1] = editor
        
        highlighters_to_update = list(self.tab_highlighters.items())
        self.tab_highlighters = {}
        for old_index, hl in highlighters_to_update:
            self.tab_highlighters[old_index + 1] = hl

        lines_to_update = list(self.tab_line_numbers.items())
        self.tab_line_numbers = {}
        for old_index, lines in lines_to_update:
            self.tab_line_numbers[old_index + 1] = lines

        agent_tabs_to_update = list(self.agent_tabs.items())
        self.agent_tabs = {}
        for old_index, log_panel in agent_tabs_to_update:
            self.agent_tabs[old_index + 1] = log_panel
        self.agent_tabs[new_tab_index] = new_log_panel

        self.tabs_control.selected_index = 0
        self._update_visibility()
        if self.tabs_control.page:
            self.tabs_control.update()

    def open_file(self, file_path: str):
        if file_path in self.open_files:
            tab_index = self.open_files[file_path]
            self.tabs_control.selected_index = tab_index
            self.tabs_control.update()
            return

        try:
            path = Path(file_path)
            if self.file_manager:
                content = self.file_manager.read_file(str(path))
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            content = content.replace('\t', '    ')

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            content = f"Error loading file: {str(e)}"

        normalized_path = str(path.resolve())
        self.original_contents[normalized_path] = content

        # ===================================================================
        #  SUPER-ULTRA ALIGNMENT & SCROLLBAR CONFIG
        # ===================================================================
        EDITOR_FONT_SIZE = 14
        EDITOR_FONT_FAMILY = "Consolas, 'Roboto Mono', 'Courier New', 'Segoe UI Emoji', 'Apple Color Emoji', monospace"
        
        # Reduced line height slightly to work better with dense=True
        # 1.2 is a standard "tight" coding multiplier.
        EDITOR_LINE_HEIGHT_VAL = 1.2 
        
        # 1. Line Numbers
        line_numbers_text = ft.Text(
            value="",
            size=EDITOR_FONT_SIZE,
            font_family=EDITOR_FONT_FAMILY,
            color=VSCodeColors.EDITOR_LINE_NUMBER,
            text_align=ft.TextAlign.RIGHT,
            selectable=False,
            style=ft.TextStyle(height=EDITOR_LINE_HEIGHT_VAL),
        )

        line_numbers_container = ft.Container(
            content=line_numbers_text,
            width=50, 
            padding=ft.padding.only(
                top=0, 
                right=10, 
            ),
            bgcolor=VSCodeColors.SIDEBAR_BACKGROUND,
            alignment=ft.alignment.top_right,
        )

        # 2. Syntax Highlighter (Background)
        syntax_spans = SyntaxHighlighterFactory.highlight(
            content, path.suffix, EDITOR_FONT_SIZE, EDITOR_FONT_FAMILY, EDITOR_LINE_HEIGHT_VAL
        )
        highlighter_text = ft.Text(
            spans=syntax_spans,
            size=EDITOR_FONT_SIZE,
            font_family=EDITOR_FONT_FAMILY,
            no_wrap=False, 
            style=ft.TextStyle(height=EDITOR_LINE_HEIGHT_VAL),
        )

        # Container for Highlighter
        # RESET ALIGNMENT:
        # We removed top=3 because it was pushing the text down too far relative to the cursor.
        # We start at top=0. With dense=True, TextField is compact and aligns at top.
        highlighter_container = ft.Container(
            content=highlighter_text,
            padding=ft.padding.only(left=2, top=0), 
            alignment=ft.alignment.top_left,
        )

        # 3. Editor (Foreground)
        def on_text_changed(e):
            current_content = e.control.value
            
            if '\t' in current_content:
                current_content = current_content.replace('\t', '    ')
                
            if current_content != self.original_contents.get(normalized_path, ""):
                self._mark_file_dirty(file_path, True)
            else:
                self._mark_file_dirty(file_path, False)
            
            self._update_line_numbers(line_numbers_text, current_content)

            # Use factory to get appropriate highlighter for file type
            highlighter_text.spans = SyntaxHighlighterFactory.highlight(
                current_content,
                path.suffix,
                EDITOR_FONT_SIZE,
                EDITOR_FONT_FAMILY,
                EDITOR_LINE_HEIGHT_VAL
            )
            
            if highlighter_text.page:
                highlighter_text.update()

        editor_textfield = ft.TextField(
            value=content,
            multiline=True,
            min_lines=1,
            # RESTORED dense=True
            # This is critical to prevent the TextField lines from being "taller"
            # than the background Text lines (the cause of the drift).
            dense=True, 
            text_size=EDITOR_FONT_SIZE,
            text_style=ft.TextStyle(
                font_family=EDITOR_FONT_FAMILY,
                height=EDITOR_LINE_HEIGHT_VAL, 
            ),
            cursor_height=EDITOR_FONT_SIZE, 
            border=ft.InputBorder.NONE,
            bgcolor=ft.Colors.TRANSPARENT,
            color=ft.Colors.TRANSPARENT,
            cursor_color=VSCodeColors.EDITOR_CURSOR,
            selection_color=VSCodeColors.EDITOR_SELECTION_BACKGROUND,
            content_padding=ft.padding.all(0), 
            on_change=on_text_changed,
            expand=False, 
        )

        # 4. Stack
        editor_stack = ft.Stack(
            controls=[
                highlighter_container,
                editor_textfield,
            ],
        )

        # 5. Row Layout (Lines + Editor)
        editor_row = ft.Row(
            controls=[
                line_numbers_container,
                ft.Container(
                    content=editor_stack, 
                    expand=True,
                    padding=ft.padding.only(top=0, left=10)
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=0,
        )

        # 6. Main Scroll Container (With Scrollbar Enabled)
        scroll_container = ft.Column(
            controls=[
                ft.Container(
                    content=editor_row,
                    padding=ft.padding.only(top=10, bottom=50) 
                )
            ],
            # ENABLE SCROLLBAR
            scroll=ft.ScrollMode.ALWAYS, 
            expand=True,
            spacing=0,
        )

        self._update_line_numbers(line_numbers_text, content)

        # Tab Setup
        filename = path.name
        icon = self._get_file_icon(path.suffix)

        def close_this_file_tab(e):
            if e.control.page:
                e.control.page.overlay.clear()
            self.close_file(file_path)
            if e.control.page:
                e.control.page.update()

        close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=14,
            tooltip="Close file",
            on_click=close_this_file_tab,
            icon_color=VSCodeColors.TAB_INACTIVE_FOREGROUND,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.HOVERED: VSCodeColors.BUTTON_SECONDARY_HOVER,
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                },
                overlay_color=VSCodeColors.ERROR_FOREGROUND,
                padding=ft.padding.all(2),
            ),
        )

        tab_label = ft.Row(
            controls=[
                ft.Icon(name=icon, size=16),
                ft.Text(filename, size=13),
                close_button,
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.START,
        )

        tab_content = ft.Container(
            content=scroll_container,
            expand=True,
            padding=0,
            bgcolor=VSCodeColors.EDITOR_BACKGROUND,
        )

        new_tab = ft.Tab(
            tab_content=tab_label,
            content=tab_content,
        )

        self.tabs_control.tabs.append(new_tab)
        tab_index = len(self.tabs_control.tabs) - 1

        self.open_files[file_path] = tab_index
        self.tab_editors[tab_index] = editor_textfield
        self.tab_highlighters[tab_index] = highlighter_text
        self.tab_line_numbers[tab_index] = line_numbers_text

        self.tabs_control.selected_index = tab_index
        self._update_visibility()

        if self.tabs_control.page:
            self.tabs_control.update()

    def _close_file_click(self, e, file_path):
        self.close_file(file_path)

    def close_file(self, file_path: str):
        if file_path not in self.open_files:
            return

        normalized_path = str(Path(file_path).resolve())
        if normalized_path in self.dirty_files:
            filename = Path(file_path).name
            self._show_unsaved_changes_dialog(file_path, filename)
            return

        self._perform_close(file_path)

    def _perform_close(self, file_path: str):
        if file_path not in self.open_files:
            return

        tab_index = self.open_files[file_path]
        normalized_path = str(Path(file_path).resolve())
        self.dirty_files.discard(normalized_path)
        if normalized_path in self.original_contents:
            del self.original_contents[normalized_path]

        if self.dirty_callback:
            self.dirty_callback(normalized_path, False)

        del self.tabs_control.tabs[tab_index]
        del self.open_files[file_path]
        
        if tab_index in self.tab_editors:
            del self.tab_editors[tab_index]
        if tab_index in self.tab_highlighters:
            del self.tab_highlighters[tab_index]
        if tab_index in self.tab_line_numbers:
            del self.tab_line_numbers[tab_index]

        files_to_update = [(fp, idx) for fp, idx in self.open_files.items() if idx > tab_index]
        for fp, idx in files_to_update:
            self.open_files[fp] = idx - 1

        editors_to_update = [(idx, editor) for idx, editor in self.tab_editors.items() if idx > tab_index]
        for idx, editor in editors_to_update:
            del self.tab_editors[idx]
            self.tab_editors[idx - 1] = editor

        highlighters_to_update = [(idx, hl) for idx, hl in self.tab_highlighters.items() if idx > tab_index]
        for idx, hl in highlighters_to_update:
            del self.tab_highlighters[idx]
            self.tab_highlighters[idx - 1] = hl

        lines_to_update = [(idx, ln) for idx, ln in self.tab_line_numbers.items() if idx > tab_index]
        for idx, ln in lines_to_update:
            del self.tab_line_numbers[idx]
            self.tab_line_numbers[idx - 1] = ln

        agent_tabs_to_update = [(idx, log_panel) for idx, log_panel in self.agent_tabs.items() if idx > tab_index]
        for idx, log_panel in agent_tabs_to_update:
            del self.agent_tabs[idx]
            self.agent_tabs[idx - 1] = log_panel

        if self.tabs_control.selected_index >= len(self.tabs_control.tabs):
            self.tabs_control.selected_index = max(0, len(self.tabs_control.tabs) - 1)

        self._update_visibility()
        if self.tabs_control.page:
            self.tabs_control.update()

    def _show_unsaved_changes_dialog(self, file_path: str, filename: str):
        def handle_save(e):
            self.save_current_file()
            dialog.open = False
            dialog.page.update()
            self._perform_close(file_path)

        def handle_dont_save(e):
            dialog.open = False
            dialog.page.update()
            self._perform_close(file_path)

        def handle_cancel(e):
            dialog.open = False
            dialog.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Unsaved Changes"),
            content=ft.Text(f"Do you want to save the changes to '{filename}'?"),
            actions=[
                ft.TextButton("Save", on_click=handle_save),
                ft.TextButton("Don't Save", on_click=handle_dont_save),
                ft.TextButton("Cancel", on_click=handle_cancel),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if self.container.page:
            self.container.page.overlay.append(dialog)
            dialog.open = True
            self.container.page.update()

    def close_tab_by_index(self, tab_index: int):
        if tab_index < 0 or tab_index >= len(self.tabs_control.tabs):
            return

        if tab_index in self.agent_tabs:
            del self.tabs_control.tabs[tab_index]

            new_agent_tabs = {}
            new_tab_editors = {}
            new_tab_highlighters = {}
            new_tab_line_numbers = {}
            new_open_files = {}

            for idx, log_panel in self.agent_tabs.items():
                if idx < tab_index: new_agent_tabs[idx] = log_panel
                elif idx > tab_index: new_agent_tabs[idx - 1] = log_panel

            for idx, editor in self.tab_editors.items():
                if idx < tab_index: new_tab_editors[idx] = editor
                elif idx > tab_index: new_tab_editors[idx - 1] = editor

            for idx, hl in self.tab_highlighters.items():
                if idx < tab_index: new_tab_highlighters[idx] = hl
                elif idx > tab_index: new_tab_highlighters[idx - 1] = hl

            for idx, lines in self.tab_line_numbers.items():
                if idx < tab_index: new_tab_line_numbers[idx] = lines
                elif idx > tab_index: new_tab_line_numbers[idx - 1] = lines

            for fp, idx in self.open_files.items():
                if idx < tab_index: new_open_files[fp] = idx
                elif idx > tab_index: new_open_files[fp] = idx - 1

            self.agent_tabs = new_agent_tabs
            self.tab_editors = new_tab_editors
            self.tab_highlighters = new_tab_highlighters
            self.tab_line_numbers = new_tab_line_numbers
            self.open_files = new_open_files

            if self.tabs_control.selected_index >= len(self.tabs_control.tabs):
                self.tabs_control.selected_index = max(0, len(self.tabs_control.tabs) - 1)

            self._update_visibility()
            if self.tabs_control.page:
                self.tabs_control.update()
            return

        file_path = None
        for fp, idx in self.open_files.items():
            if idx == tab_index:
                file_path = fp
                break

        if file_path:
            self.close_file(file_path)

    def _on_tab_changed(self, e):
        pass

    def get_current_file_content(self):
        current_index = self.tabs_control.selected_index
        if current_index in self.tab_editors:
            return self.tab_editors[current_index].value
        return None

    def save_current_file(self):
        current_index = self.tabs_control.selected_index
        if current_index in self.agent_tabs:
            return

        file_path = None
        for fp, idx in self.open_files.items():
            if idx == current_index:
                file_path = fp
                break

        if not file_path or current_index not in self.tab_editors:
            return

        content = self.tab_editors[current_index].value
        try:
            if self.file_manager:
                self.file_manager.write_file(file_path, content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            print(f"Saved: {file_path}")

            normalized_path = str(Path(file_path).resolve())
            self.original_contents[normalized_path] = content
            self._mark_file_dirty(file_path, False)
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")

    def _mark_file_dirty(self, file_path: str, is_dirty: bool):
        normalized_path = str(Path(file_path).resolve())
        if is_dirty:
            self.dirty_files.add(normalized_path)
        else:
            self.dirty_files.discard(normalized_path)
        self._update_tab_title(normalized_path, is_dirty)
        if self.dirty_callback:
            self.dirty_callback(normalized_path, is_dirty)

    def _update_tab_title(self, file_path: str, is_dirty: bool):
        if file_path not in self.open_files:
            return
        tab_index = self.open_files[file_path]
        if tab_index >= len(self.tabs_control.tabs):
            return

        tab = self.tabs_control.tabs[tab_index]
        filename = Path(file_path).name
        if is_dirty:
            tab.text = f"{filename} *"
        else:
            tab.text = filename
        if self.tabs_control.page:
            self.tabs_control.update()

    def _get_file_icon(self, extension: str):
        icon_map = {
            '.st': ft.Icons.CODE,
            '.py': ft.Icons.CODE,
            '.md': ft.Icons.DESCRIPTION,
            '.txt': ft.Icons.TEXT_SNIPPET,
            '.json': ft.Icons.DATA_OBJECT,
        }
        return icon_map.get(extension.lower(), ft.Icons.INSERT_DRIVE_FILE)

    def _update_line_numbers(self, line_numbers_text: ft.Text, content: str):
        if not content:
            count = 1
        else:
            count = content.count('\n') + 1
            if content.endswith('\n'):
                count += 1
            
        new_text = "\n".join(str(i) for i in range(1, count + 1))
        
        if line_numbers_text.value != new_text:
            line_numbers_text.value = new_text
            if line_numbers_text.page:
                line_numbers_text.update()

    def update_chat_log(self, message: str, log_type: str = "agent"):
        current_index = self.tabs_control.selected_index
        if current_index in self.agent_tabs:
            agent_log_panel = self.agent_tabs[current_index]
            agent_log_panel.add_log(message, log_type)
        else:
            if self.agent_tabs:
                most_recent_agent_index = min(self.agent_tabs.keys())
                agent_log_panel = self.agent_tabs[most_recent_agent_index]
                agent_log_panel.add_log(message, log_type)

    def update_chat_stream(self, message: str):
        self.update_chat_log(message, "agent")

    def reload_tabs(self):
        for file_path, tab_index in list(self.open_files.items()):
            if tab_index not in self.tab_editors:
                continue

            editor = self.tab_editors[tab_index]
            highlighter = self.tab_highlighters.get(tab_index)
            normalized_path = str(Path(file_path).resolve())

            try:
                if self.file_manager:
                    new_content = self.file_manager.read_file(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()

                # Fix tabs on reload
                new_content = new_content.replace('\t', '    ')

                if normalized_path in self.dirty_files:
                    print(f"Skipping reload of {file_path} - has unsaved changes")
                    continue

                editor.value = new_content
                self.original_contents[normalized_path] = new_content
                
                if tab_index in self.tab_line_numbers:
                    self._update_line_numbers(self.tab_line_numbers[tab_index], new_content)

                if highlighter:
                    # Use factory to get appropriate highlighter for file type
                    highlighter.spans = SyntaxHighlighterFactory.highlight(
                        new_content,
                        Path(file_path).suffix,
                        14,  # font_size
                        "Consolas, 'Roboto Mono', 'Courier New', 'Segoe UI Emoji', 'Apple Color Emoji', monospace",
                        1.2  # line_height
                    )
                    if highlighter.page:
                        highlighter.update()

                if editor.page:
                    editor.update()

            except Exception as e:
                print(f"Error reloading file {file_path}: {e}")