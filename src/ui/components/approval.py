"""
Approval Modals for Pulse IDE v2.6 (Phase 7).

Deterministic approval gates for:
- Patch approval: Show unified diff, require Approve/Deny
- Terminal approval: Show command + risk label, require Execute/Deny

These modals are the ONLY path for patch application and terminal execution.
Graph execution pauses until user provides approval decision.
"""

import flet as ft
from typing import Callable, Dict, Any, Optional, List, Tuple, TYPE_CHECKING
from pathlib import Path
from src.ui.theme import VSCodeColors, Fonts, Spacing

# Lazy import to avoid circular dependency
# SyntaxHighlighterFactory is imported at runtime inside methods that need it


class DiffColors:
    """Colors for diff visualization (VS Code style)."""
    ADDED_BG = "#1E3A1E"         # Dark green background for added lines
    ADDED_LINE_BG = "#2D4F2D"    # Slightly lighter for line highlight
    ADDED_TEXT = "#98C379"       # Green text for additions
    REMOVED_BG = "#3A1E1E"       # Dark red background for removed lines
    REMOVED_LINE_BG = "#4F2D2D"  # Slightly lighter for line highlight
    REMOVED_TEXT = "#E06C75"     # Red text for deletions
    CONTEXT_BG = "#1E1E2E"       # Dark background for context lines
    HUNK_HEADER_BG = "#2D2D5A"   # Purple-ish for @@ headers
    HUNK_HEADER_TEXT = "#61AFEF" # Blue text for hunk headers
    LINE_NUMBER_BG = "#252526"   # Background for line numbers
    LINE_NUMBER_TEXT = "#858585" # Gray text for line numbers
    SEPARATOR = "#3C3C3C"        # Border/separator color


class DiffLine:
    """Represents a single line in a diff view."""

    def __init__(
        self,
        line_type: str,  # 'added', 'removed', 'context', 'hunk_header', 'file_header'
        content: str,
        old_line_num: Optional[int] = None,
        new_line_num: Optional[int] = None,
    ):
        self.line_type = line_type
        self.content = content
        self.old_line_num = old_line_num
        self.new_line_num = new_line_num


def parse_unified_diff(diff: str) -> List[DiffLine]:
    """
    Parse unified diff format into structured DiffLine objects.

    Args:
        diff: Unified diff string

    Returns:
        List of DiffLine objects
    """
    lines = diff.split('\n')
    result = []
    old_line = 0
    new_line = 0

    for line in lines:
        if line.startswith('---') or line.startswith('+++'):
            result.append(DiffLine('file_header', line))
        elif line.startswith('@@'):
            result.append(DiffLine('hunk_header', line))
            # Parse hunk header to get line numbers: @@ -old,count +new,count @@
            try:
                parts = line.split(' ')
                old_part = parts[1]  # -old,count
                new_part = parts[2]  # +new,count
                old_line = int(old_part.split(',')[0].replace('-', ''))
                new_line = int(new_part.split(',')[0].replace('+', ''))
            except (IndexError, ValueError):
                old_line = 1
                new_line = 1
        elif line.startswith('+'):
            content = line[1:] if len(line) > 1 else ''
            result.append(DiffLine('added', content, None, new_line))
            new_line += 1
        elif line.startswith('-'):
            content = line[1:] if len(line) > 1 else ''
            result.append(DiffLine('removed', content, old_line, None))
            old_line += 1
        elif line.startswith(' ') or line == '':
            content = line[1:] if len(line) > 1 else line
            result.append(DiffLine('context', content, old_line, new_line))
            old_line += 1
            new_line += 1
        else:
            # Treat as context if doesn't match standard format
            result.append(DiffLine('context', line, old_line, new_line))
            old_line += 1
            new_line += 1

    return result


class EnhancedDiffViewer:
    """
    Enhanced side-by-side diff viewer with syntax highlighting.

    Features:
    - Side-by-side view (original vs modified)
    - Line numbers
    - Syntax highlighting based on file extension
    - Background colors for added/removed lines
    - VS Code-style appearance
    """

    def __init__(self, file_path: str, diff: str, view_mode: str = "split"):
        """
        Initialize the diff viewer.

        Args:
            file_path: Path to the file being modified
            diff: Unified diff content
            view_mode: "split" for side-by-side, "unified" for inline
        """
        self.file_path = file_path
        self.diff = diff
        self.view_mode = view_mode
        self.file_extension = Path(file_path).suffix if file_path else '.txt'
        self.diff_lines = parse_unified_diff(diff)

    def _create_line_number(self, num: Optional[int], line_type: str) -> ft.Container:
        """Create a line number cell."""
        bg_color = DiffColors.LINE_NUMBER_BG
        if line_type == 'added':
            bg_color = DiffColors.ADDED_BG
        elif line_type == 'removed':
            bg_color = DiffColors.REMOVED_BG

        return ft.Container(
            content=ft.Text(
                str(num) if num else '',
                font_family=Fonts.MONOSPACE_PRIMARY,
                size=Fonts.FONT_SIZE_SMALL - 1,
                color=DiffColors.LINE_NUMBER_TEXT,
                text_align=ft.TextAlign.RIGHT,
            ),
            width=40,
            padding=ft.padding.only(right=8, left=4, top=2, bottom=2),
            bgcolor=bg_color,
        )

    def _create_content_cell(self, content: str, line_type: str, show_prefix: bool = False) -> ft.Container:
        """Create a content cell with syntax highlighting."""
        # Determine colors based on line type
        if line_type == 'added':
            bg_color = DiffColors.ADDED_BG
            prefix = '+ ' if show_prefix else ''
            prefix_color = DiffColors.ADDED_TEXT
        elif line_type == 'removed':
            bg_color = DiffColors.REMOVED_BG
            prefix = '- ' if show_prefix else ''
            prefix_color = DiffColors.REMOVED_TEXT
        elif line_type == 'hunk_header':
            bg_color = DiffColors.HUNK_HEADER_BG
            prefix = ''
            prefix_color = DiffColors.HUNK_HEADER_TEXT
        elif line_type == 'file_header':
            bg_color = DiffColors.CONTEXT_BG
            prefix = ''
            prefix_color = DiffColors.HUNK_HEADER_TEXT
        else:  # context
            bg_color = DiffColors.CONTEXT_BG
            prefix = '  ' if show_prefix else ''
            prefix_color = VSCodeColors.EDITOR_FOREGROUND

        # For headers, use simple text
        if line_type in ['hunk_header', 'file_header']:
            text_content = ft.Text(
                content,
                font_family=Fonts.MONOSPACE_PRIMARY,
                size=Fonts.FONT_SIZE_SMALL,
                color=DiffColors.HUNK_HEADER_TEXT,
                selectable=True,
                no_wrap=True,
            )
        else:
            # Try to apply syntax highlighting for code content
            # Lazy import to avoid circular dependency
            try:
                from src.ui.editor import SyntaxHighlighterFactory
                spans = SyntaxHighlighterFactory.highlight(
                    content,
                    self.file_extension,
                    Fonts.FONT_SIZE_SMALL,
                    Fonts.MONOSPACE_PRIMARY,
                    1.2
                )
                text_content = ft.Text(
                    spans=spans,
                    font_family=Fonts.MONOSPACE_PRIMARY,
                    size=Fonts.FONT_SIZE_SMALL,
                    selectable=True,
                    no_wrap=True,
                )
            except Exception:
                # Fallback to plain text
                text_content = ft.Text(
                    content,
                    font_family=Fonts.MONOSPACE_PRIMARY,
                    size=Fonts.FONT_SIZE_SMALL,
                    color=VSCodeColors.EDITOR_FOREGROUND,
                    selectable=True,
                    no_wrap=True,
                )

        row_controls = []
        if show_prefix:
            row_controls.append(
                ft.Text(
                    prefix,
                    font_family=Fonts.MONOSPACE_PRIMARY,
                    size=Fonts.FONT_SIZE_SMALL,
                    color=prefix_color,
                    weight=ft.FontWeight.BOLD,
                )
            )
        row_controls.append(text_content)

        return ft.Container(
            content=ft.Row(
                controls=row_controls,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.only(left=8, right=8, top=2, bottom=2),
            bgcolor=bg_color,
            expand=True,
        )

    def _build_unified_view(self) -> ft.Control:
        """Build unified (inline) diff view."""
        rows = []

        for diff_line in self.diff_lines:
            if diff_line.line_type == 'file_header':
                rows.append(
                    ft.Container(
                        content=ft.Text(
                            diff_line.content,
                            font_family=Fonts.MONOSPACE_PRIMARY,
                            size=Fonts.FONT_SIZE_SMALL,
                            color=DiffColors.HUNK_HEADER_TEXT,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=DiffColors.CONTEXT_BG,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    )
                )
            elif diff_line.line_type == 'hunk_header':
                rows.append(
                    ft.Container(
                        content=ft.Text(
                            diff_line.content,
                            font_family=Fonts.MONOSPACE_PRIMARY,
                            size=Fonts.FONT_SIZE_SMALL,
                            color=DiffColors.HUNK_HEADER_TEXT,
                        ),
                        bgcolor=DiffColors.HUNK_HEADER_BG,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    )
                )
            else:
                # Build line with line numbers and content
                old_num = self._create_line_number(diff_line.old_line_num, diff_line.line_type)
                new_num = self._create_line_number(diff_line.new_line_num, diff_line.line_type)
                content = self._create_content_cell(diff_line.content, diff_line.line_type, show_prefix=True)

                rows.append(
                    ft.Row(
                        controls=[old_num, new_num, content],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    )
                )

        return ft.Column(
            controls=rows,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

    def _build_split_view(self) -> ft.Control:
        """Build side-by-side split diff view."""
        left_rows = []   # Original (removed/context)
        right_rows = []  # Modified (added/context)

        for diff_line in self.diff_lines:
            if diff_line.line_type in ['file_header', 'hunk_header']:
                # Span across both sides
                header = ft.Container(
                    content=ft.Text(
                        diff_line.content,
                        font_family=Fonts.MONOSPACE_PRIMARY,
                        size=Fonts.FONT_SIZE_SMALL,
                        color=DiffColors.HUNK_HEADER_TEXT,
                        weight=ft.FontWeight.BOLD if diff_line.line_type == 'file_header' else None,
                    ),
                    bgcolor=DiffColors.HUNK_HEADER_BG if diff_line.line_type == 'hunk_header' else DiffColors.CONTEXT_BG,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    expand=True,
                )
                left_rows.append(header)
                right_rows.append(
                    ft.Container(
                        bgcolor=DiffColors.HUNK_HEADER_BG if diff_line.line_type == 'hunk_header' else DiffColors.CONTEXT_BG,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        expand=True,
                    )
                )
            elif diff_line.line_type == 'removed':
                # Only on left side
                left_rows.append(
                    ft.Row(
                        controls=[
                            self._create_line_number(diff_line.old_line_num, 'removed'),
                            self._create_content_cell(diff_line.content, 'removed'),
                        ],
                        spacing=0,
                    )
                )
                right_rows.append(
                    ft.Container(
                        bgcolor=DiffColors.REMOVED_BG,
                        height=22,  # Match line height
                        expand=True,
                    )
                )
            elif diff_line.line_type == 'added':
                # Only on right side
                left_rows.append(
                    ft.Container(
                        bgcolor=DiffColors.ADDED_BG,
                        height=22,  # Match line height
                        expand=True,
                    )
                )
                right_rows.append(
                    ft.Row(
                        controls=[
                            self._create_line_number(diff_line.new_line_num, 'added'),
                            self._create_content_cell(diff_line.content, 'added'),
                        ],
                        spacing=0,
                    )
                )
            else:  # context
                left_rows.append(
                    ft.Row(
                        controls=[
                            self._create_line_number(diff_line.old_line_num, 'context'),
                            self._create_content_cell(diff_line.content, 'context'),
                        ],
                        spacing=0,
                    )
                )
                right_rows.append(
                    ft.Row(
                        controls=[
                            self._create_line_number(diff_line.new_line_num, 'context'),
                            self._create_content_cell(diff_line.content, 'context'),
                        ],
                        spacing=0,
                    )
                )

        return ft.Row(
            controls=[
                # Left panel (Original)
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    "Original",
                                    size=Fonts.FONT_SIZE_SMALL,
                                    weight=ft.FontWeight.BOLD,
                                    color=DiffColors.REMOVED_TEXT,
                                ),
                                bgcolor=DiffColors.LINE_NUMBER_BG,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                            ft.Column(
                                controls=left_rows,
                                spacing=0,
                                scroll=ft.ScrollMode.AUTO,
                                expand=True,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    border=ft.border.only(right=ft.BorderSide(1, DiffColors.SEPARATOR)),
                    expand=True,
                ),
                # Right panel (Modified)
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    "Modified",
                                    size=Fonts.FONT_SIZE_SMALL,
                                    weight=ft.FontWeight.BOLD,
                                    color=DiffColors.ADDED_TEXT,
                                ),
                                bgcolor=DiffColors.LINE_NUMBER_BG,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                            ft.Column(
                                controls=right_rows,
                                spacing=0,
                                scroll=ft.ScrollMode.AUTO,
                                expand=True,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        )

    def build(self) -> ft.Control:
        """Build the diff viewer control."""
        if self.view_mode == "split":
            diff_content = self._build_split_view()
        else:
            diff_content = self._build_unified_view()

        return ft.Container(
            content=diff_content,
            bgcolor=DiffColors.CONTEXT_BG,
            border_radius=Spacing.BORDER_RADIUS_SMALL,
            border=ft.border.all(1, DiffColors.SEPARATOR),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )


class PatchApprovalModal:
    """
    Patch approval modal dialog.

    Shows unified diff preview with syntax highlighting.
    Requires explicit Approve/Deny decision.
    """

    def __init__(
        self,
        page: ft.Page,
        on_approve: Callable[[], None],
        on_deny: Callable[[str], None],
    ):
        """
        Initialize PatchApprovalModal.

        Args:
            page: Flet Page for dialog display.
            on_approve: Callback when user approves.
            on_deny: Callback when user denies (receives feedback text).
        """
        self.page = page
        self.on_approve = on_approve
        self.on_deny = on_deny

        self._dialog: Optional[ft.AlertDialog] = None
        self._diff_text: Optional[ft.Text] = None
        self._feedback_field: Optional[ft.TextField] = None
        self._file_path_text: Optional[ft.Text] = None
        self._rationale_text: Optional[ft.Text] = None

    def show(self, patch_data: Dict[str, Any], view_mode: str = "unified") -> None:
        """
        Show the patch approval modal.

        Args:
            patch_data: PatchPlan as dict with keys:
                - file_path: Target file path
                - diff: Unified diff content
                - rationale: Why this patch is being applied
            view_mode: "unified" for inline view, "split" for side-by-side
        """
        file_path = patch_data.get("file_path", "unknown")
        diff = patch_data.get("diff", "")
        rationale = patch_data.get("rationale", "No rationale provided")

        # Create enhanced diff viewer with syntax highlighting
        diff_viewer = EnhancedDiffViewer(file_path, diff, view_mode=view_mode)

        # View mode toggle button
        self._view_mode = view_mode

        def toggle_view_mode(e):
            # Toggle between unified and split view
            new_mode = "split" if self._view_mode == "unified" else "unified"
            self._close_dialog()
            patch_data_copy = dict(patch_data)
            self.show(patch_data_copy, view_mode=new_mode)

        view_toggle = ft.IconButton(
            icon=ft.Icons.VIEW_COLUMN if view_mode == "unified" else ft.Icons.VIEW_STREAM,
            tooltip="Toggle split/unified view",
            on_click=toggle_view_mode,
            icon_color=VSCodeColors.LINK_FOREGROUND,
            icon_size=18,
        )

        # Feedback field for rejection
        self._feedback_field = ft.TextField(
            label="Feedback (optional)",
            hint_text="Explain what's wrong or what you'd like instead...",
            multiline=True,
            min_lines=2,
            max_lines=4,
            visible=False,
            width=500,
            text_size=Fonts.FONT_SIZE_NORMAL,
        )

        # Build dialog
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.DIFFERENCE,
                        color=VSCodeColors.WARNING_FOREGROUND,
                        size=24,
                    ),
                    ft.Text(
                        "Patch Approval Required",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # File path
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "File:",
                                    weight=ft.FontWeight.BOLD,
                                    color=VSCodeColors.DESCRIPTION_FOREGROUND,
                                ),
                                ft.Text(
                                    file_path,
                                    color=VSCodeColors.LINK_FOREGROUND,
                                    selectable=True,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Container(height=4),
                        # Rationale
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        "Rationale:",
                                        weight=ft.FontWeight.BOLD,
                                        size=Fonts.FONT_SIZE_SMALL,
                                        color=VSCodeColors.DESCRIPTION_FOREGROUND,
                                    ),
                                    ft.Text(
                                        rationale,
                                        size=Fonts.FONT_SIZE_SMALL,
                                        color=VSCodeColors.EDITOR_FOREGROUND,
                                    ),
                                ],
                                spacing=4,
                            ),
                            padding=8,
                            bgcolor=VSCodeColors.EDITOR_BACKGROUND,
                            border_radius=Spacing.BORDER_RADIUS_SMALL,
                        ),
                        ft.Container(height=8),
                        # Diff preview header with view toggle
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "Changes:",
                                    weight=ft.FontWeight.BOLD,
                                    size=Fonts.FONT_SIZE_SMALL,
                                    color=VSCodeColors.DESCRIPTION_FOREGROUND,
                                ),
                                ft.Container(expand=True),
                                ft.Text(
                                    "Split" if view_mode == "split" else "Unified",
                                    size=Fonts.FONT_SIZE_SMALL - 1,
                                    color=VSCodeColors.DESCRIPTION_FOREGROUND,
                                ),
                                view_toggle,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        # Enhanced diff viewer
                        ft.Container(
                            content=diff_viewer.build(),
                            height=300,
                            expand=True,
                        ),
                        ft.Container(height=8),
                        # Feedback field
                        self._feedback_field,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=800 if view_mode == "split" else 650,
                height=550,
            ),
            actions=[
                ft.TextButton(
                    "Deny",
                    icon=ft.Icons.CLOSE,
                    on_click=self._handle_deny_click,
                    style=ft.ButtonStyle(
                        color=VSCodeColors.ERROR_FOREGROUND,
                    ),
                ),
                ft.ElevatedButton(
                    "Approve",
                    icon=ft.Icons.CHECK,
                    on_click=self._handle_approve,
                    style=ft.ButtonStyle(
                        bgcolor=VSCodeColors.SUCCESS_FOREGROUND,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Show dialog
        self.page.dialog = self._dialog
        self._dialog.open = True
        self.page.update()

    def _handle_approve(self, e) -> None:
        """Handle Approve button click."""
        self._close_dialog()
        self.on_approve()

    def _handle_deny_click(self, e) -> None:
        """Handle Deny button click - show feedback field or submit."""
        if not self._feedback_field.visible:
            # First click: show feedback field
            self._feedback_field.visible = True
            self.page.update()
        else:
            # Second click: submit denial with feedback
            feedback = self._feedback_field.value or ""
            self._close_dialog()
            self.on_deny(feedback)

    def _close_dialog(self) -> None:
        """Close the dialog."""
        if self._dialog:
            self._dialog.open = False
            self.page.update()


class TerminalApprovalModal:
    """
    Terminal command approval modal dialog.

    Shows command preview with risk label and rationale.
    Requires explicit Execute/Deny decision.
    """

    # Risk level colors
    RISK_COLORS = {
        "LOW": VSCodeColors.SUCCESS_FOREGROUND,
        "MEDIUM": VSCodeColors.WARNING_FOREGROUND,
        "HIGH": VSCodeColors.ERROR_FOREGROUND,
    }

    def __init__(
        self,
        page: ft.Page,
        on_execute: Callable[[], None],
        on_deny: Callable[[str], None],
    ):
        """
        Initialize TerminalApprovalModal.

        Args:
            page: Flet Page for dialog display.
            on_execute: Callback when user approves execution.
            on_deny: Callback when user denies (receives feedback text).
        """
        self.page = page
        self.on_execute = on_execute
        self.on_deny = on_deny

        self._dialog: Optional[ft.AlertDialog] = None
        self._feedback_field: Optional[ft.TextField] = None

    def show(self, command_data: Dict[str, Any]) -> None:
        """
        Show the terminal approval modal.

        Args:
            command_data: CommandPlan as dict with keys:
                - command: Command string to execute
                - rationale: Why this command is being executed
                - risk_label: "LOW", "MEDIUM", or "HIGH"
        """
        command = command_data.get("command", "")
        rationale = command_data.get("rationale", "No rationale provided")
        risk_label = command_data.get("risk_label", "MEDIUM")

        risk_color = self.RISK_COLORS.get(risk_label, VSCodeColors.WARNING_FOREGROUND)

        # Feedback field for rejection
        self._feedback_field = ft.TextField(
            label="Feedback (optional)",
            hint_text="Explain why this command shouldn't run...",
            multiline=True,
            min_lines=2,
            max_lines=4,
            visible=False,
            width=450,
            text_size=Fonts.FONT_SIZE_NORMAL,
        )

        # Build dialog
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.TERMINAL,
                        color=risk_color,
                        size=24,
                    ),
                    ft.Text(
                        "Terminal Command Approval",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # Risk label badge
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        f"RISK: {risk_label}",
                                        size=Fonts.FONT_SIZE_SMALL,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                    ),
                                    bgcolor=risk_color,
                                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                    border_radius=4,
                                ),
                            ],
                        ),
                        ft.Container(height=12),
                        # Command display
                        ft.Text(
                            "Command:",
                            weight=ft.FontWeight.BOLD,
                            size=Fonts.FONT_SIZE_SMALL,
                            color=VSCodeColors.DESCRIPTION_FOREGROUND,
                        ),
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Text(
                                        "$ ",
                                        font_family=Fonts.MONOSPACE_PRIMARY,
                                        size=Fonts.FONT_SIZE_NORMAL,
                                        color=VSCodeColors.TERMINAL_ANSI_BRIGHT_GREEN,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        command,
                                        font_family=Fonts.MONOSPACE_PRIMARY,
                                        size=Fonts.FONT_SIZE_NORMAL,
                                        color=VSCodeColors.TERMINAL_FOREGROUND,
                                        selectable=True,
                                    ),
                                ],
                                spacing=0,
                            ),
                            bgcolor=VSCodeColors.TERMINAL_BACKGROUND,
                            padding=12,
                            border_radius=Spacing.BORDER_RADIUS_SMALL,
                            border=ft.border.all(1, risk_color),
                        ),
                        ft.Container(height=12),
                        # Rationale
                        ft.Text(
                            "Rationale:",
                            weight=ft.FontWeight.BOLD,
                            size=Fonts.FONT_SIZE_SMALL,
                            color=VSCodeColors.DESCRIPTION_FOREGROUND,
                        ),
                        ft.Container(
                            content=ft.Text(
                                rationale,
                                size=Fonts.FONT_SIZE_SMALL,
                                color=VSCodeColors.EDITOR_FOREGROUND,
                            ),
                            padding=8,
                            bgcolor=VSCodeColors.EDITOR_BACKGROUND,
                            border_radius=Spacing.BORDER_RADIUS_SMALL,
                        ),
                        ft.Container(height=12),
                        # Warning for HIGH risk
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.WARNING,
                                        color=VSCodeColors.WARNING_FOREGROUND,
                                        size=16,
                                    ),
                                    ft.Text(
                                        "This command will be executed in your terminal. "
                                        "Review carefully before approving.",
                                        size=Fonts.FONT_SIZE_SMALL - 1,
                                        color=VSCodeColors.WARNING_FOREGROUND,
                                    ),
                                ],
                                spacing=6,
                            ),
                            visible=risk_label in ["MEDIUM", "HIGH"],
                        ),
                        ft.Container(height=8),
                        # Feedback field
                        self._feedback_field,
                    ],
                ),
                width=500,
                padding=8,
            ),
            actions=[
                ft.TextButton(
                    "Deny",
                    icon=ft.Icons.CLOSE,
                    on_click=self._handle_deny_click,
                    style=ft.ButtonStyle(
                        color=VSCodeColors.ERROR_FOREGROUND,
                    ),
                ),
                ft.ElevatedButton(
                    "Execute",
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=self._handle_execute,
                    style=ft.ButtonStyle(
                        bgcolor=risk_color if risk_label != "HIGH" else VSCodeColors.ERROR_FOREGROUND,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Show dialog
        self.page.dialog = self._dialog
        self._dialog.open = True
        self.page.update()

    def _handle_execute(self, e) -> None:
        """Handle Execute button click."""
        self._close_dialog()
        self.on_execute()

    def _handle_deny_click(self, e) -> None:
        """Handle Deny button click - show feedback field or submit."""
        if not self._feedback_field.visible:
            # First click: show feedback field
            self._feedback_field.visible = True
            self.page.update()
        else:
            # Second click: submit denial with feedback
            feedback = self._feedback_field.value or ""
            self._close_dialog()
            self.on_deny(feedback)

    def _close_dialog(self) -> None:
        """Close the dialog."""
        if self._dialog:
            self._dialog.open = False
            self.page.update()


def show_patch_approval(
    page: ft.Page,
    patch_data: Dict[str, Any],
    on_approve: Callable[[], None],
    on_deny: Callable[[str], None],
) -> PatchApprovalModal:
    """
    Helper function to show patch approval modal.

    Args:
        page: Flet Page.
        patch_data: PatchPlan as dict.
        on_approve: Callback for approval.
        on_deny: Callback for denial.

    Returns:
        PatchApprovalModal instance.
    """
    modal = PatchApprovalModal(page, on_approve, on_deny)
    modal.show(patch_data)
    return modal


def show_terminal_approval(
    page: ft.Page,
    command_data: Dict[str, Any],
    on_execute: Callable[[], None],
    on_deny: Callable[[str], None],
) -> TerminalApprovalModal:
    """
    Helper function to show terminal approval modal.

    Args:
        page: Flet Page.
        command_data: CommandPlan as dict.
        on_execute: Callback for execution.
        on_deny: Callback for denial.

    Returns:
        TerminalApprovalModal instance.
    """
    modal = TerminalApprovalModal(page, on_execute, on_deny)
    modal.show(command_data)
    return modal


__all__ = [
    "DiffColors",
    "DiffLine",
    "EnhancedDiffViewer",
    "PatchApprovalModal",
    "TerminalApprovalModal",
    "parse_unified_diff",
    "show_patch_approval",
    "show_terminal_approval",
]
