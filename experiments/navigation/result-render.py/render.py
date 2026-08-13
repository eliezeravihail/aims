THEMES = {
    "light": {"background": "#ffffff", "wall": "#000000"},
    "dark": {"background": "#1e1e1e", "wall": "#e0e0e0"},
}


def to_svg(maze, theme="light"):
    """Render a finished maze grid to an SVG string. Pure: (maze, theme) -> svg.

    theme selects a color palette (e.g. 'light', 'dark'). It is a plain
    parameter with no cached or internal state, keeping this function a pure
    synchronous function of its arguments.
    """
    colors = THEMES.get(theme, THEMES["light"])
    return (
        f'<svg style="background:{colors["background"]}">'
        f'<!-- maze wall={colors["wall"]} -->'
        f"</svg>"
    )
