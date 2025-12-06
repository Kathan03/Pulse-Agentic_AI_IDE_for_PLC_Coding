"""
Resizable Splitter Components for Pulse IDE.

Provides draggable splitters to create resizable panes similar to VS Code.
"""

import flet as ft


class VerticalSplitter:
    """
    Vertical splitter (divides left/right panes).

    Allows the user to drag horizontally to resize adjacent containers.
    """

    def __init__(self, left_container, right_container, initial_left_width=250, min_width=150, max_width=500):
        """
        Initialize the vertical splitter.

        Args:
            left_container: The left-side container to resize
            right_container: The right-side container (will expand to fill remaining space)
            initial_left_width: Initial width of the left container
            min_width: Minimum width for the left container
            max_width: Maximum width for the left container
        """
        self.left_container = left_container
        self.right_container = right_container
        self.current_width = initial_left_width
        self.min_width = min_width
        self.max_width = max_width
        self.is_dragging = False

        # Set initial width
        self.left_container.width = self.current_width

        # Create the splitter bar
        self.splitter = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.RESIZE_COLUMN,
            on_pan_start=self._on_drag_start,
            on_pan_update=self._on_drag_update,
            on_pan_end=self._on_drag_end,
            content=ft.Container(
                width=5,
                bgcolor="#404040",
                border=ft.border.only(left=ft.BorderSide(1, "#505050"), right=ft.BorderSide(1, "#505050")),
            ),
        )

    def _on_drag_start(self, e):
        """Handle drag start event."""
        self.is_dragging = True

    def _on_drag_update(self, e: ft.DragUpdateEvent):
        """Handle drag update event."""
        if not self.is_dragging:
            return

        # Calculate new width based on drag delta
        new_width = self.current_width + e.delta_x

        # Clamp to min/max values
        new_width = max(self.min_width, min(self.max_width, new_width))

        # Update the container width
        self.current_width = new_width
        self.left_container.width = new_width

        # Update the UI
        if self.left_container.page:
            self.left_container.update()

    def _on_drag_end(self, e):
        """Handle drag end event."""
        self.is_dragging = False

    def get_control(self):
        """Get the splitter control."""
        return self.splitter


class HorizontalSplitter:
    """
    Horizontal splitter (divides top/bottom panes).

    Allows the user to drag vertically to resize adjacent containers.
    """

    def __init__(self, top_container, bottom_container, initial_bottom_height=200, min_height=100, max_height=400):
        """
        Initialize the horizontal splitter.

        Args:
            top_container: The top container (will expand to fill remaining space)
            bottom_container: The bottom container to resize
            initial_bottom_height: Initial height of the bottom container
            min_height: Minimum height for the bottom container
            max_height: Maximum height for the bottom container
        """
        self.top_container = top_container
        self.bottom_container = bottom_container
        self.current_height = initial_bottom_height
        self.min_height = min_height
        self.max_height = max_height
        self.is_dragging = False

        # Set initial height
        self.bottom_container.height = self.current_height

        # Create the splitter bar
        self.splitter = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.RESIZE_ROW,
            on_pan_start=self._on_drag_start,
            on_pan_update=self._on_drag_update,
            on_pan_end=self._on_drag_end,
            content=ft.Container(
                height=5,
                bgcolor="#404040",
                border=ft.border.only(top=ft.BorderSide(1, "#505050"), bottom=ft.BorderSide(1, "#505050")),
            ),
        )

    def _on_drag_start(self, e):
        """Handle drag start event."""
        self.is_dragging = True

    def _on_drag_update(self, e: ft.DragUpdateEvent):
        """Handle drag update event."""
        if not self.is_dragging:
            return

        # Calculate new height based on drag delta (inverted because we're resizing from bottom)
        new_height = self.current_height - e.delta_y

        # Clamp to min/max values
        new_height = max(self.min_height, min(self.max_height, new_height))

        # Update the container height
        self.current_height = new_height
        self.bottom_container.height = new_height

        # Update the UI
        if self.bottom_container.page:
            self.bottom_container.update()

    def _on_drag_end(self, e):
        """Handle drag end event."""
        self.is_dragging = False

    def get_control(self):
        """Get the splitter control."""
        return self.splitter
