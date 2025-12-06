"""
Status Bar Component for Pulse IDE.

Provides a VS Code-like status bar with mode indicator and workspace info.
"""

import flet as ft
from src.ui.theme import VSCodeColors, Fonts, Spacing


class StatusBar:
    """
    VS Code-style status bar component.

    Features:
    - Current mode indicator (Agent/Plan/Ask)
    - Workspace path display
    - Dynamic updates when mode changes
    - VS Code blue background
    """

    def __init__(self, mode="Agent Mode", workspace_path=""):
        """
        Initialize StatusBar.

        Args:
            mode: Initial mode to display
            workspace_path: Current workspace path
        """
        self.current_mode = mode
        self.workspace_path = workspace_path
        self.mode_text = None
        self.workspace_text = None
        self.container = self._build()

    def _build(self):
        """Build the status bar UI component with dark theme styling."""
        # Mode indicator
        self.mode_text = ft.Text(
            self._format_mode(self.current_mode),
            size=Fonts.FONT_SIZE_SMALL,
            color="#FFFFFF",
            weight=ft.FontWeight.W_500,
        )

        # Workspace path
        self.workspace_text = ft.Text(
            self._format_workspace(self.workspace_path),
            size=Fonts.FONT_SIZE_SMALL,
            color="#CCCCCC",
        )

        # Status bar container with darker theme - Simple centered "Powered by AI"
        return ft.Container(
            bgcolor="#1E1E1E",  # Darker background matching editor theme
            padding=ft.padding.symmetric(horizontal=Spacing.PADDING_MEDIUM, vertical=8),
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.AUTO_AWESOME,
                        size=16,
                        color="#61DAFB",
                    ),
                    ft.Text(
                        "Powered by AI",
                        size=Fonts.FONT_SIZE_SMALL,
                        color="#CCCCCC",
                        italic=True,
                    ),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

    def _format_mode(self, mode):
        """Format mode text for display."""
        return f"Mode: {mode}"

    def _format_workspace(self, path):
        """Format workspace path for display."""
        if not path or path == ".":
            return "No workspace"
        # Show just the folder name, not the full path
        from pathlib import Path
        return f"{Path(path).name}"

    def get_control(self):
        """Get the status bar control for adding to the page."""
        return self.container

    def update_mode(self, mode):
        """
        Update the displayed mode dynamically.

        Args:
            mode: New mode string ("Agent Mode", "Plan Mode", or "Ask Mode")
        """
        self.current_mode = mode
        self.mode_text.value = self._format_mode(mode)

        # Update UI if page is available
        if self.mode_text.page:
            self.mode_text.update()

    def update_workspace(self, workspace_path):
        """
        Update the displayed workspace path.

        Args:
            workspace_path: New workspace path
        """
        self.workspace_path = workspace_path
        self.workspace_text.value = self._format_workspace(workspace_path)

        # Update UI if page is available
        if self.workspace_text.page:
            self.workspace_text.update()

    def set_color(self, color):
        """
        Set custom background color for the status bar.

        Args:
            color: Hex color string
        """
        self.container.bgcolor = color
        if self.container.page:
            self.container.update()
