"""
Agent Activity Log Panel Component for Pulse IDE.

Displays agent execution logs and provides user input interface.
"""

import flet as ft
from src.ui.theme import VSCodeColors, Fonts, Spacing


class LogPanel:
    """
    Agent activity log and user input panel with VS Code styling.

    Features:
    - ListView for displaying agent logs
    - TextField for user input at the bottom
    - Auto-scrolling to latest log entries
    - VS Code Dark Modern theme colors
    """

    def __init__(self, on_submit=None):
        """
        Initialize LogPanel.

        Args:
            on_submit: Callback function when user submits input (receives text as parameter)
        """
        self.on_submit = on_submit
        self.log_view = None
        self.input_field = None
        self.container = self._build()

    def _build(self):
        """Build the log panel UI component with VS Code styling."""
        # Log display area
        self.log_view = ft.ListView(
            expand=True,
            spacing=Spacing.PADDING_SMALL,
            padding=Spacing.PADDING_MEDIUM,
            auto_scroll=True,
        )

        # User input field
        self.input_field = ft.TextField(
            hint_text="Enter your requirement or question...",
            hint_style=ft.TextStyle(color=VSCodeColors.INPUT_PLACEHOLDER_FOREGROUND),
            multiline=False,
            on_submit=self._handle_submit,
            border=ft.InputBorder.OUTLINE,
            text_size=Fonts.FONT_SIZE_NORMAL,
            bgcolor=VSCodeColors.INPUT_BACKGROUND,
            color=VSCodeColors.INPUT_FOREGROUND,
            border_color=VSCodeColors.INPUT_BORDER,
            focused_border_color=VSCodeColors.INPUT_ACTIVE_BORDER,
        )

        # Send button
        send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            tooltip="Send",
            on_click=self._handle_submit,
            icon_color=VSCodeColors.BUTTON_BACKGROUND,
            bgcolor=VSCodeColors.BUTTON_SECONDARY_BACKGROUND,
            hover_color=VSCodeColors.BUTTON_SECONDARY_HOVER,
        )

        # Input row with text field and send button
        input_row = ft.Row(
            controls=[
                ft.Container(
                    content=self.input_field,
                    expand=True,
                ),
                send_button,
            ],
            spacing=Spacing.PADDING_SMALL,
        )

        # Main column layout
        return ft.Column(
            controls=[
                ft.Container(
                    content=self.log_view,
                    expand=True,
                    bgcolor=VSCodeColors.EDITOR_BACKGROUND,
                    border=ft.border.all(Spacing.BORDER_WIDTH, VSCodeColors.PANEL_BORDER),
                    border_radius=Spacing.BORDER_RADIUS_SMALL,
                ),
                input_row,
            ],
            spacing=Spacing.PADDING_MEDIUM,
            expand=True,
        )

    def get_control(self):
        """Get the log panel control for adding to the page."""
        return self.container

    def _handle_submit(self, e):
        """Handle user input submission."""
        if self.input_field.value and self.input_field.value.strip():
            # Call the callback if provided
            if self.on_submit:
                self.on_submit(self.input_field.value.strip())

            # Clear input field
            self.input_field.value = ""
            self.input_field.update()

    def add_log(self, message: str, log_type: str = "info"):
        """
        Add a log entry to the panel with VS Code color coding.

        Args:
            message: Log message to display
            log_type: Type of log ("info", "success", "warning", "error", "agent")
        """
        # Color mapping using VS Code theme colors
        color_map = {
            "info": VSCodeColors.INFO_FOREGROUND,
            "success": VSCodeColors.SUCCESS_FOREGROUND,
            "warning": VSCodeColors.WARNING_FOREGROUND,
            "error": VSCodeColors.ERROR_FOREGROUND,
            "agent": VSCodeColors.ACTIVITY_BAR_ACTIVE_BORDER,
        }

        # Icon mapping for different log types
        icon_map = {
            "info": ft.Icons.INFO_OUTLINE,
            "success": ft.Icons.CHECK_CIRCLE_OUTLINE,
            "warning": ft.Icons.WARNING_AMBER,
            "error": ft.Icons.ERROR_OUTLINE,
            "agent": ft.Icons.SMART_TOY_OUTLINED,
        }

        log_entry = ft.Row(
            controls=[
                ft.Icon(
                    name=icon_map.get(log_type, ft.Icons.INFO_OUTLINE),
                    color=color_map.get(log_type, VSCodeColors.INFO_FOREGROUND),
                    size=16,
                ),
                ft.Text(
                    message,
                    size=Fonts.FONT_SIZE_SMALL,
                    color=color_map.get(log_type, VSCodeColors.INFO_FOREGROUND),
                    font_family=Fonts.SANS_SERIF_PRIMARY,
                    expand=True,
                    selectable=True,
                ),
            ],
            spacing=Spacing.PADDING_SMALL,
        )

        self.log_view.controls.append(log_entry)
        if self.log_view.page:
            self.log_view.update()

    def clear_logs(self):
        """Clear all log entries."""
        self.log_view.controls.clear()
        if self.log_view.page:
            self.log_view.update()
