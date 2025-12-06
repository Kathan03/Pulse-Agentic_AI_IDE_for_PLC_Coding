"""
Pulse IDE - Main Flet Application
Entry point for the Flet-based desktop UI with VS Code-like layout
"""
import flet as ft
from pathlib import Path
from src.ui.sidebar import Sidebar
from src.ui.editor import EditorManager
from src.ui.log_panel import LogPanel
from src.ui.terminal import TerminalPanel
from src.ui.status_bar import StatusBar
from src.ui.components.resizable_splitter import VerticalSplitter, HorizontalSplitter
from src.ui.theme import VSCodeColors, Spacing


def main(page: ft.Page):
    """
    Main entry point for the Flet application.

    Sets up the VS Code-like layout with:
    - Resizable sidebar (left)
    - Tabbed editor manager (top right)
    - Integrated PowerShell terminal (bottom right)
    - Status bar (bottom) with dynamic mode indicator
    - All styled with VS Code Dark Modern theme

    Args:
        page: The Flet Page object representing the application window
    """
    # Configure page settings
    page.title = "Pulse IDE"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1400
    page.window_height = 900
    page.bgcolor = VSCodeColors.EDITOR_BACKGROUND

    # Get workspace path
    workspace_path = str(Path.cwd())

    # Create status bar (created first so it can be referenced by sidebar)
    status_bar = StatusBar(mode="Agent Mode", workspace_path=workspace_path)

    # Create log panel component with input handler
    def handle_user_input(text: str):
        """Handle user input from log panel (Pulse Chat)."""
        # TODO: Wire this to agent orchestration engine
        log_panel.add_log(f"User: {text}", "info")
        log_panel.add_log("Agent orchestration engine will process this request", "agent")

    log_panel = LogPanel(on_submit=handle_user_input)

    # Create editor manager with log panel for Pulse Chat tab
    editor_manager = EditorManager(log_panel=log_panel)

    # Create sidebar with editor manager reference for file opening
    sidebar = Sidebar(editor_manager=editor_manager)

    # Override sidebar's mode change handler to update status bar and agent tab
    original_on_mode_changed = sidebar._on_mode_changed

    def on_mode_changed_with_updates(e):
        """Handle mode change and update status bar."""
        original_on_mode_changed(e)
        status_bar.update_mode(e.control.value)
        # Note: Changing mode does not affect existing agent tabs
        # User can open a new agent tab with the new mode

    sidebar._on_mode_changed = on_mode_changed_with_updates

    # Create terminal panel with PowerShell integration
    def handle_terminal_command(command: str):
        """Handle custom commands from terminal (if needed)."""
        # Most commands are handled by PowerShell directly
        pass

    terminal = TerminalPanel(on_command=handle_terminal_command, workspace_path=workspace_path)

    # Create containers for the main content areas
    # These will be resized by the splitters
    sidebar_container = ft.Container(
        width=250,
        bgcolor=VSCodeColors.SIDEBAR_BACKGROUND,
        content=sidebar.get_control(),
    )

    terminal_container = ft.Container(
        height=200,
        bgcolor=VSCodeColors.PANEL_BACKGROUND,
        content=terminal.get_control(),
    )

    editor_container = ft.Container(
        expand=True,
        bgcolor=VSCodeColors.EDITOR_BACKGROUND,
        content=editor_manager.get_control(),
    )

    # Create splitters
    vertical_splitter = VerticalSplitter(
        left_container=sidebar_container,
        right_container=None,  # Right side is the editor + terminal column
        initial_left_width=250,
        min_width=150,
        max_width=500
    )

    horizontal_splitter = HorizontalSplitter(
        top_container=editor_container,
        bottom_container=terminal_container,
        initial_bottom_height=200,
        min_height=100,
        max_height=400
    )

    # Create the right side column (editor on top, terminal on bottom)
    right_column = ft.Column(
        controls=[
            editor_container,
            horizontal_splitter.get_control(),
            terminal_container,
        ],
        spacing=0,
        expand=True,
    )

    # Create the main content layout: sidebar | splitter | (editor / splitter / terminal)
    main_content = ft.Row(
        controls=[
            sidebar_container,
            vertical_splitter.get_control(),
            right_column,
        ],
        spacing=0,
        expand=True,
    )

    # Create the complete layout with status bar at bottom
    complete_layout = ft.Column(
        controls=[
            main_content,
            status_bar.get_control(),
        ],
        spacing=0,
        expand=True,
    )

    # Add layout to page
    page.add(complete_layout)

    # Initialize FilePicker for the sidebar
    sidebar.initialize_file_picker(page)

    # Initialize sidebar with current working directory as workspace root
    sidebar.load_directory(".", set_as_root=True)

    # Note: Welcome messages are added to log panel when Pulse Agent tab is opened
