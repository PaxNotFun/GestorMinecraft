import re


ANSI_COLOR_MAP = {
    '30': 'black', '31': 'red', '32': 'green', '33': 'yellow',
    '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white',
    '90': 'grey', '91': 'light_red', '92': 'light_green', '93': 'light_yellow',
    '94': 'light_blue', '95': 'light_magenta', '96': 'light_cyan', '97': 'light_white'
}

COLOR_VALUES = {
    "red": "#ff6b6b", "green": "#1dd1a1", "yellow": "#feca57",
    "blue": "#54a0ff", "magenta": "#ff9ff3", "cyan": "#48dbfb",
    "white": "#f1f2f6", "black": "#222f3e",
    "grey": "#888888", "light_red": "#ff9999", "light_green": "#55efc4",
    "light_yellow": "#ffeaa7", "light_blue": "#74b9ff", "light_magenta": "#fd79a8",
    "light_cyan": "#81ecec", "light_white": "#dfe6e9"
}

# Códigos de color de Minecraft §X → nombre de tag
MINECRAFT_COLOR_MAP = {
    '0': 'mc_black',    '1': 'mc_dark_blue',   '2': 'mc_dark_green',
    '3': 'mc_dark_cyan','4': 'mc_dark_red',    '5': 'mc_dark_purple',
    '6': 'mc_gold',     '7': 'mc_gray',         '8': 'mc_dark_gray',
    '9': 'mc_blue',     'a': 'mc_green',        'b': 'mc_aqua',
    'c': 'mc_red',      'd': 'mc_light_purple', 'e': 'mc_yellow',
    'f': 'mc_white',
}

MINECRAFT_COLOR_VALUES = {
    'mc_black': '#000000',      'mc_dark_blue': '#0000aa',   'mc_dark_green': '#00aa00',
    'mc_dark_cyan': '#00aaaa',  'mc_dark_red': '#aa0000',    'mc_dark_purple': '#aa00aa',
    'mc_gold': '#ffaa00',       'mc_gray': '#aaaaaa',        'mc_dark_gray': '#555555',
    'mc_blue': '#5555ff',       'mc_green': '#55ff55',       'mc_aqua': '#55ffff',
    'mc_red': '#ff5555',        'mc_light_purple': '#ff55ff','mc_yellow': '#ffff55',
    'mc_white': '#ffffff',
}


def _get_inner(widget):
    """Devuelve el tk.Text interno de un CTkTextbox, o el widget si ya es tk.Text."""
    return getattr(widget, '_textbox', widget)


def setup_console_tags(console_widget):
    """Configura los tags de colores ANSI y Minecraft en el widget de texto."""
    inner = _get_inner(console_widget)
    for color_name, color in COLOR_VALUES.items():
        inner.tag_config(color_name, foreground=color)
    for tag, color in MINECRAFT_COLOR_VALUES.items():
        inner.tag_config(tag, foreground=color)


def parse_ansi_and_insert(console_widget, text):
    """Parsea texto con códigos ANSI y §Minecraft y lo inserta con colores."""
    if not console_widget or not console_widget.winfo_exists():
        return

    inner = _get_inner(console_widget)
    console_widget.configure(state='normal')

    # Patrón combinado: ANSI \x1b[Xm  o  Minecraft §X
    pattern = re.compile(r'(\x1b\[(\d+(?:;\d+)*)m)|(§([0-9a-fk-or]))', re.IGNORECASE)

    current_tag = None
    last_index = 0

    for match in pattern.finditer(text):
        # Insertar texto plano antes del código
        if match.start() > last_index:
            segment = text[last_index:match.start()]
            if current_tag:
                inner.insert('end', segment, (current_tag,))
            else:
                inner.insert('end', segment)

        last_index = match.end()

        if match.group(1):  # ANSI
            codes = match.group(2).split(';')
            if '0' in codes:
                current_tag = None
            else:
                new_tag = next(
                    (ANSI_COLOR_MAP[c] for c in codes if c in ANSI_COLOR_MAP),
                    None
                )
                if new_tag:
                    current_tag = new_tag
        elif match.group(3):  # Minecraft §
            code = match.group(4).lower()
            if code == 'r':
                current_tag = None
            elif code in MINECRAFT_COLOR_MAP:
                current_tag = MINECRAFT_COLOR_MAP[code]

    # Resto del texto después del último código
    if last_index < len(text):
        segment = text[last_index:]
        if current_tag:
            inner.insert('end', segment, (current_tag,))
        else:
            inner.insert('end', segment)

    inner.see('end')
    console_widget.configure(state='disabled')
