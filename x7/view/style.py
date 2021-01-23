# import tkinter as tk
from tkinter import ttk


STYLE_SETTINGS = {
    'ValidationBorder': {
        'layout': [('Frame.border', {'sticky': 'news'})],
        'map': {
            'background': [
                (['invalid', '!disabled'], '#ff4040'),
                (['invalid', 'disabled'], '#ffc0c0'),
            ],
        },
    },
}


def setup_style():
    style = ttk.Style()
    for theme in style.theme_names():
        style.theme_settings(theme, STYLE_SETTINGS)
    if style.theme_use() == 'default':
        style.theme_use('clam')


if __name__ == '__main__':
    from . import style_show
    # style_show.show_style()
    style_show.test_style()
