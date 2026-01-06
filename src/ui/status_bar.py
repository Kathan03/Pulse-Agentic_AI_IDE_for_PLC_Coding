"""
Status Bar Component for Pulse IDE.

Shows "Powered by AI" text and live token/cost usage from LLM calls.
"""

import flet as ft
from src.ui.theme import VSCodeColors, Fonts, Spacing


class StatusBar:
    """
    Status bar component showing AI branding and session usage.
    
    Usage display shows total tokens and estimated cost, updated
    after each LLM call via update_usage() method.
    """

    def __init__(self):
        """Initialize StatusBar."""
        # Usage display controls (initially hidden)
        self._usage_text = ft.Text(
            "",
            size=Fonts.FONT_SIZE_SMALL,
            color=VSCodeColors.STATUS_BAR_FOREGROUND,
            visible=False,
        )
        self._separator = ft.Text(
            "|",
            size=Fonts.FONT_SIZE_SMALL,
            color=VSCodeColors.STATUS_BAR_FOREGROUND,
            opacity=0.5,
            visible=False,
        )
        self.container = self._build()

    def _build(self):
        """Build the status bar UI component with theme-aware styling."""
        return ft.Container(
            bgcolor=VSCodeColors.STATUS_BAR_BACKGROUND,
            padding=ft.padding.symmetric(horizontal=Spacing.PADDING_MEDIUM, vertical=8),
            content=ft.Row(
                controls=[
                    # Left side: AI branding
                    ft.Icon(
                        ft.Icons.AUTO_AWESOME,
                        size=16,
                        color=VSCodeColors.STATUS_BAR_FOREGROUND,
                    ),
                    ft.Text(
                        "Powered by AI",
                        size=Fonts.FONT_SIZE_SMALL,
                        color=VSCodeColors.STATUS_BAR_FOREGROUND,
                        italic=True,
                    ),
                    # Separator (visible when usage exists)
                    self._separator,
                    # Usage display (visible when usage exists)
                    ft.Icon(
                        ft.Icons.ANALYTICS_OUTLINED,
                        size=14,
                        color=VSCodeColors.STATUS_BAR_FOREGROUND,
                        visible=False,
                        ref=ft.Ref[ft.Icon](),
                    ),
                    self._usage_text,
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

    def update_usage(self, tokens: int, cost: float) -> None:
        """
        Update the usage display with current session totals.
        
        Args:
            tokens: Total tokens used in session.
            cost: Estimated cost in USD.
        """
        if tokens > 0:
            self._usage_text.value = f"{tokens:,} tokens • ${cost:.4f}"
            self._usage_text.visible = True
            self._separator.visible = True
            # Also show the analytics icon
            row = self.container.content
            if isinstance(row, ft.Row) and len(row.controls) >= 4:
                row.controls[3].visible = True  # Analytics icon
            if self.container.page:
                self.container.update()
        else:
            self._usage_text.visible = False
            self._separator.visible = False
            row = self.container.content
            if isinstance(row, ft.Row) and len(row.controls) >= 4:
                row.controls[3].visible = False
            if self.container.page:
                self.container.update()

    def get_control(self):
        """Get the status bar control for adding to the page."""
        return self.container


__all__ = ["StatusBar"]
