"""
Feedback Prompt Component
Collects user ratings and feedback after agent runs
"""
import flet as ft


class FeedbackPrompt:
    """Component for collecting user feedback after agent task completion"""

    def __init__(self):
        self.rating = 0
        self.feedback_text = ""

    def build(self) -> ft.Control:
        """Build and return the feedback prompt UI"""

        rating_stars = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.STAR_OUTLINE,
                    icon_color=ft.colors.YELLOW_700,
                    tooltip="Rate 1 star",
                    data=1
                ),
                ft.IconButton(
                    icon=ft.icons.STAR_OUTLINE,
                    icon_color=ft.colors.YELLOW_700,
                    tooltip="Rate 2 stars",
                    data=2
                ),
                ft.IconButton(
                    icon=ft.icons.STAR_OUTLINE,
                    icon_color=ft.colors.YELLOW_700,
                    tooltip="Rate 3 stars",
                    data=3
                ),
                ft.IconButton(
                    icon=ft.icons.STAR_OUTLINE,
                    icon_color=ft.colors.YELLOW_700,
                    tooltip="Rate 4 stars",
                    data=4
                ),
                ft.IconButton(
                    icon=ft.icons.STAR_OUTLINE,
                    icon_color=ft.colors.YELLOW_700,
                    tooltip="Rate 5 stars",
                    data=5
                ),
            ],
            spacing=5
        )

        feedback_field = ft.TextField(
            label="Additional feedback (optional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True
        )

        submit_btn = ft.ElevatedButton(
            text="Submit Feedback",
            icon=ft.icons.SEND
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("How was this result?", size=16, weight=ft.FontWeight.BOLD),
                    rating_stars,
                    feedback_field,
                    submit_btn
                ],
                spacing=10
            ),
            padding=15,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8
        )

    def on_rating_click(self, rating: int):
        """Handle star rating click"""
        self.rating = rating

    def on_submit(self, callback):
        """Handle feedback submission"""
        return {
            "rating": self.rating,
            "feedback": self.feedback_text
        }
