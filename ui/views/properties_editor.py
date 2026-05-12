import threading
from collections import OrderedDict
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from config.general import TEXT_LIGHT, CARD_BG, CARD_BG_HOVER, ACCENT, INPUT_BG, INPUT_BORDER, TEXT_MUTED, SUCCESS
from utils.helpers import fix_scroll_linux


# Metadatos conocidos: label, tooltip, tipo y default.
# Propiedades no listadas aquí se renderizan como campo de texto genérico.
KNOWN_PROPERTIES = {
    "level-name":                    {"label": "Nombre del Mundo",        "tooltip": "Nombre de la carpeta del mundo",           "type": "text",     "default": "world",       "category": "Mundo"},
    "level-seed":                    {"label": "Semilla del Mundo",        "tooltip": "Semilla para generar el mundo",            "type": "text",     "default": "",            "category": "Mundo"},
    "level-type":                    {"label": "Tipo de Mundo",            "tooltip": "Tipo de generación del mundo",             "type": "dropdown", "options": ["default", "flat", "largeBiomes", "amplified"], "default": "default", "category": "Mundo"},
    "generate-structures":           {"label": "Generar Estructuras",      "tooltip": "Generar aldeas, templos, etc.",            "type": "bool",     "default": "true",        "category": "Mundo"},
    "max-world-size":                {"label": "Tamaño Máximo",            "tooltip": "Radio máximo del mundo en bloques",        "type": "number",   "default": "29999984",    "category": "Mundo",       "min": 1,  "max": 29999984},
    "gamemode":                      {"label": "Modo de Juego",            "tooltip": "Modo de juego predeterminado",             "type": "dropdown", "options": ["survival", "creative", "adventure", "spectator"], "default": "survival", "category": "Juego"},
    "difficulty":                    {"label": "Dificultad",               "tooltip": "Dificultad del servidor",                  "type": "dropdown", "options": ["peaceful", "easy", "normal", "hard"], "default": "easy", "category": "Juego"},
    "hardcore":                      {"label": "Modo Hardcore",            "tooltip": "Si mueres, se cambia a espectador",        "type": "bool",     "default": "false",       "category": "Juego"},
    "pvp":                           {"label": "PvP Activado",             "tooltip": "Permitir combate entre jugadores",         "type": "bool",     "default": "true",        "category": "Juego"},
    "force-gamemode":                {"label": "Forzar Modo de Juego",     "tooltip": "Forzar el modo al conectarse",             "type": "bool",     "default": "false",       "category": "Juego"},
    "spawn-monsters":                {"label": "Generar Monstruos",        "tooltip": "Permitir spawn de mobs hostiles",          "type": "bool",     "default": "true",        "category": "Mobs"},
    "spawn-animals":                 {"label": "Generar Animales",         "tooltip": "Permitir spawn de animales pasivos",       "type": "bool",     "default": "true",        "category": "Mobs"},
    "spawn-npcs":                    {"label": "Generar NPCs",             "tooltip": "Permitir spawn de aldeanos",               "type": "bool",     "default": "true",        "category": "Mobs"},
    "max-tick-time":                 {"label": "Tiempo Máximo de Tick",    "tooltip": "Tiempo máximo antes de watchdog (-1=off)", "type": "number",   "default": "60000",       "category": "Mobs",        "min": -1},
    "server-port":                   {"label": "Puerto del Servidor",      "tooltip": "Puerto de escucha del servidor",           "type": "number",   "default": "25565",       "category": "Servidor",    "min": 1,  "max": 65535},
    "max-players":                   {"label": "Jugadores Máximos",        "tooltip": "Número máximo de jugadores",               "type": "number",   "default": "20",          "category": "Servidor",    "min": 1,  "max": 2147483647},
    "motd":                          {"label": "MOTD",                     "tooltip": "Mensaje en la lista de servidores",        "type": "text",     "default": "A Minecraft Server", "category": "Servidor"},
    "online-mode":                   {"label": "Modo Online",              "tooltip": "Verificar cuentas premium",                "type": "bool",     "default": "true",        "category": "Servidor"},
    "enable-command-block":          {"label": "Bloques de Comandos",      "tooltip": "Habilitar bloques de comandos",            "type": "bool",     "default": "false",       "category": "Servidor"},
    "white-list":                    {"label": "Whitelist",                "tooltip": "Activar lista blanca",                     "type": "bool",     "default": "false",       "category": "Servidor"},
    "enforce-whitelist":             {"label": "Forzar Whitelist",         "tooltip": "Kickear jugadores no whitelisteados",      "type": "bool",     "default": "false",       "category": "Servidor"},
    "view-distance":                 {"label": "Distancia de Vista",       "tooltip": "Chunks visibles (2-32)",                   "type": "number",   "default": "10",          "category": "Rendimiento", "min": 2,  "max": 32},
    "simulation-distance":           {"label": "Distancia de Simulación",  "tooltip": "Chunks donde se procesan mobs",            "type": "number",   "default": "10",          "category": "Rendimiento", "min": 3,  "max": 32},
    "max-build-height":              {"label": "Altura Máxima",            "tooltip": "Altura máxima de construcción",            "type": "number",   "default": "256",         "category": "Rendimiento", "min": 1,  "max": 256},
    "network-compression-threshold": {"label": "Umbral de Compresión",     "tooltip": "Tamaño de paquete antes de comprimir",     "type": "number",   "default": "256",         "category": "Rendimiento", "min": -1},
    "allow-flight":                  {"label": "Permitir Vuelo",           "tooltip": "Permitir modo vuelo en survival",          "type": "bool",     "default": "false",       "category": "Otros"},
    "allow-nether":                  {"label": "Permitir Nether",          "tooltip": "Permitir viajes al Nether",                "type": "bool",     "default": "true",        "category": "Otros"},
    "enable-query":                  {"label": "Habilitar Query",          "tooltip": "Habilitar protocolo de query",             "type": "bool",     "default": "false",       "category": "Otros"},
    "enable-rcon":                   {"label": "Habilitar RCON",           "tooltip": "Habilitar control remoto",                 "type": "bool",     "default": "false",       "category": "Otros"},
    "rcon.password":                 {"label": "Contraseña RCON",          "tooltip": "Contraseña para RCON",                     "type": "text",     "default": "",            "category": "Otros"},
    "rcon.port":                     {"label": "Puerto RCON",              "tooltip": "Puerto para RCON",                         "type": "number",   "default": "25575",       "category": "Otros",       "min": 1,  "max": 65535},
}

PRESETS = {
    "Survival":  {"gamemode": "survival",  "difficulty": "normal",   "pvp": "true",  "spawn-monsters": "true",  "spawn-animals": "true",  "generate-structures": "true"},
    "Creative":  {"gamemode": "creative",  "difficulty": "peaceful", "pvp": "false", "spawn-monsters": "false", "spawn-animals": "true",  "generate-structures": "true"},
    "Hardcore":  {"gamemode": "survival",  "difficulty": "hard",     "pvp": "true",  "spawn-monsters": "true",  "hardcore": "true"},
    "Peaceful":  {"gamemode": "survival",  "difficulty": "peaceful", "pvp": "false", "spawn-monsters": "false", "spawn-animals": "true"},
}

CATEGORY_ORDER = ["Mundo", "Juego", "Mobs", "Servidor", "Rendimiento", "Otros"]
BATCH_SIZE = 8  # Widgets a construir por tick para no congelar la UI


class PropertiesEditorView(ctk.CTkFrame):
    """Editor visual de server.properties — I/O en thread separado, widgets dinámicos."""

    def __init__(self, parent, server_info):
        super().__init__(parent, fg_color="transparent")
        self.server_info = server_info
        self.server_path = Path(server_info['path'])
        self.properties_file = self.server_path / 'server.properties'

        # {key: {'widget': widget, 'type': str, 'info': dict|None}}
        self.widgets = {}
        # Orden de inserción de todas las claves leídas del archivo
        self.key_order = []
        # Comentarios del encabezado para preservarlos al guardar
        self._header_comments = []

        self._build_skeleton()
        self._start_load()

    # ── Estructura base ───────────────────────────────────────────────────────

    def _build_skeleton(self):
        """Construye la UI estática (header + scroll vacío + botones)."""
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=15, height=90)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            header_content,
            text="Editor de server.properties",
            font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(side="left")

        preset_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        preset_frame.pack(side="right")

        ctk.CTkLabel(
            preset_frame, text="Presets:",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_MUTED
        ).pack(side="left", padx=(0, 10))

        self.preset_menu = ctk.CTkOptionMenu(
            preset_frame,
            values=list(PRESETS.keys()),
            command=self._apply_preset,
            width=160, height=40,
            fg_color=INPUT_BG, button_color=ACCENT, button_hover_color="#a78bfa",
            dropdown_fg_color=CARD_BG,
            font=ctk.CTkFont(size=14, family="Segoe UI")
        )
        self.preset_menu.set("Seleccionar preset")
        self.preset_menu.pack(side="left")

        # Scrollable area
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#2d2d3f",
            scrollbar_button_hover_color="#3d3d4f"
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        fix_scroll_linux(self.scroll_frame)

        self._show_loading_indicator()

        # Botones fijos al fondo
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0), padx=10)
        btn_frame.grid_propagate(False)
        btn_frame.grid_columnconfigure(0, weight=0)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkButton(
            btn_frame, text="Recargar",
            command=self._start_load,
            height=55, width=150,
            fg_color=CARD_BG_HOVER, hover_color="#3f3f46",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            corner_radius=12
        ).grid(row=0, column=0, sticky="w")

        self.btn_save = ctk.CTkButton(
            btn_frame, text="Guardar Cambios",
            command=self._start_save,
            height=55, width=190,
            fg_color=ACCENT, hover_color="#a78bfa",
            text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            corner_radius=12
        )
        self.btn_save.grid(row=0, column=2, sticky="e")

    def _show_loading_indicator(self):
        ctk.CTkLabel(
            self.scroll_frame,
            text="Cargando server.properties...",
            font=ctk.CTkFont(size=16, family="Segoe UI"),
            text_color=TEXT_MUTED
        ).pack(pady=40)

        self._build_progress = ctk.CTkProgressBar(
            self.scroll_frame, mode="indeterminate",
            height=6, progress_color=ACCENT,
            corner_radius=3, border_width=0
        )
        self._build_progress.pack(fill="x", padx=40, pady=(0, 20))
        self._build_progress.start()

    # ── Carga ─────────────────────────────────────────────────────────────────

    def _start_load(self):
        """Lanza la lectura del archivo en un thread de I/O."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.widgets.clear()
        self.key_order.clear()
        self._header_comments.clear()
        self._show_loading_indicator()
        threading.Thread(target=self._read_file_thread, daemon=True).start()

    def _read_file_thread(self):
        """Lee el archivo en el thread de I/O. Nunca toca widgets."""
        header_comments = []
        ordered_props = OrderedDict()
        try:
            if not self.properties_file.exists():
                self.after(0, self._on_load_error, "No se encontró server.properties.")
                return
            with open(self.properties_file, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    stripped = line.rstrip('\n').rstrip('\r')
                    if stripped.startswith('#') or stripped == '':
                        header_comments.append(stripped)
                    elif '=' in stripped:
                        key, _, value = stripped.partition('=')
                        ordered_props[key.strip()] = value.strip()
            self.after(0, self._on_read_done, header_comments, ordered_props)
        except Exception as e:
            self.after(0, self._on_load_error, str(e))

    def _on_load_error(self, message):
        if not self.winfo_exists():
            return
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll_frame,
            text=f"❌ {message}",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color="#ef4444"
        ).pack(pady=40)

    def _on_read_done(self, header_comments, ordered_props):
        """Recibe los datos del thread de I/O y construye widgets por lotes."""
        if not self.winfo_exists():
            return

        self._header_comments = header_comments
        self.key_order = list(ordered_props.keys())

        # Agrupar por categoría; las desconocidas van al final
        categorized = OrderedDict()
        for cat in CATEGORY_ORDER:
            categorized[cat] = []
        categorized["Desconocidas"] = []

        for key, value in ordered_props.items():
            info = KNOWN_PROPERTIES.get(key)
            cat = info["category"] if info else "Desconocidas"
            categorized[cat].append((key, value, info))

        # Lista plana para el batch builder
        build_queue = []
        for cat_name, items in categorized.items():
            if not items:
                continue
            build_queue.append(('header', cat_name, None, None, None))
            for key, value, info in items:
                build_queue.append(('field', key, value, info, cat_name))

        self._build_queue = build_queue
        self._build_index = 0
        self._category_frames = {}

        for w in self.scroll_frame.winfo_children():
            w.destroy()

        self._do_build_batch()

    # ── Construcción de widgets por lotes ────────────────────────────────────

    def _do_build_batch(self):
        """Construye BATCH_SIZE widgets y se re-agenda hasta terminar."""
        if not self.winfo_exists():
            return

        queue = self._build_queue
        total = len(queue)
        end = min(self._build_index + BATCH_SIZE, total)

        for i in range(self._build_index, end):
            item_type = queue[i][0]

            if item_type == 'header':
                _, cat_name, _, _, _ = queue[i]
                frame = ctk.CTkFrame(
                    self.scroll_frame, fg_color=CARD_BG,
                    corner_radius=15, border_width=1, border_color=INPUT_BORDER
                )
                frame.pack(fill="x", pady=(0, 15), padx=10)
                ctk.CTkLabel(
                    frame, text=cat_name,
                    font=ctk.CTkFont(size=18, weight="bold", family="Segoe UI"),
                    text_color=TEXT_LIGHT, anchor="w"
                ).pack(anchor="w", padx=25, pady=(25, 18))
                self._category_frames[cat_name] = frame
            else:
                _, key, value, info, cat_name = queue[i]
                parent_frame = self._category_frames.get(cat_name)
                if parent_frame:
                    self._create_field(parent_frame, key, value, info)

        self._build_index = end

        if self._build_index < total:
            self.after(0, self._do_build_batch)

    def _create_field(self, parent_frame, key, value, info):
        """Crea el widget adecuado para una propiedad."""
        container = ctk.CTkFrame(parent_frame, fg_color="transparent")
        container.pack(fill="x", padx=25, pady=(0, 18))

        label_row = ctk.CTkFrame(container, fg_color="transparent")
        label_row.pack(fill="x", pady=(0, 8))

        if info:
            label_text = info['label']
            tooltip_text = info['tooltip']
            prop_type = info['type']
        else:
            label_text = key
            tooltip_text = "Propiedad no reconocida — se preservará tal cual"
            prop_type = "text"

        ctk.CTkLabel(
            label_row, text=label_text,
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT, anchor="w"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            label_row, text=tooltip_text,
            font=ctk.CTkFont(size=12, family="Segoe UI"),
            text_color=TEXT_MUTED, anchor="w"
        ).pack(side="left")

        if prop_type == 'bool':
            widget = ctk.CTkSwitch(
                container, text="",
                width=65, height=30,
                fg_color=INPUT_BG, progress_color=SUCCESS,
                button_color=CARD_BG_HOVER, button_hover_color=CARD_BG
            )
            widget.pack(anchor="w")
            widget.select() if value.lower() == 'true' else widget.deselect()

        elif prop_type == 'dropdown' and info:
            options = info.get('options', [])
            widget = ctk.CTkOptionMenu(
                container, values=options,
                width=320, height=44,
                fg_color=INPUT_BG, button_color=ACCENT, button_hover_color="#a78bfa",
                dropdown_fg_color=CARD_BG,
                font=ctk.CTkFont(size=14, family="Segoe UI")
            )
            widget.pack(anchor="w")
            widget.set(value if value in options else info.get('default', options[0]))

        else:  # text, number, o desconocida
            widget = ctk.CTkEntry(
                container,
                width=520 if prop_type == 'text' else 320,
                height=44,
                fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=2,
                font=ctk.CTkFont(size=14, family="Segoe UI"),
                text_color=TEXT_LIGHT
            )
            widget.pack(anchor="w")
            widget.insert(0, value)

        self.widgets[key] = {'widget': widget, 'type': prop_type, 'info': info}

    # ── Guardado ──────────────────────────────────────────────────────────────

    def _start_save(self):
        """Valida en el hilo principal y lanza la escritura en thread de I/O."""
        new_properties = OrderedDict()

        for key in self.key_order:
            if key not in self.widgets:
                continue
            wd = self.widgets[key]
            widget = wd['widget']
            prop_type = wd['type']
            info = wd['info']

            try:
                if prop_type == 'bool':
                    value = 'true' if widget.get() == 1 else 'false'
                elif prop_type == 'dropdown':
                    value = widget.get()
                elif prop_type == 'number':
                    raw = widget.get().strip()
                    if raw == '' and info and info.get('default'):
                        value = info['default']
                    else:
                        num = int(raw)
                        if info:
                            if 'min' in info and num < info['min']:
                                raise ValueError(f"Debe ser >= {info['min']}")
                            if 'max' in info and num > info['max']:
                                raise ValueError(f"Debe ser <= {info['max']}")
                        value = str(num)
                else:
                    value = widget.get().strip()

                new_properties[key] = value

            except ValueError as e:
                label = info['label'] if info else key
                messagebox.showerror("Error de Validación", f"Error en '{label}':\n{e}", parent=self)
                return

        self.btn_save.configure(state="disabled", text="Guardando...")
        threading.Thread(target=self._write_file_thread, args=(new_properties,), daemon=True).start()

    def _write_file_thread(self, new_properties):
        """Escribe el archivo en el thread de I/O. Nunca toca widgets."""
        try:
            with open(self.properties_file, 'w', encoding='utf-8') as f:
                for comment in self._header_comments:
                    f.write(comment + '\n')
                if self._header_comments:
                    f.write('\n')
                for key, value in new_properties.items():
                    f.write(f"{key}={value}\n")
            self.after(0, self._on_save_done, None)
        except Exception as e:
            self.after(0, self._on_save_done, str(e))

    def _on_save_done(self, error):
        if not self.winfo_exists():
            return
        self.btn_save.configure(state="normal", text="Guardar Cambios")
        if error:
            messagebox.showerror("Error", f"Error al guardar:\n{error}", parent=self)
        else:
            messagebox.showinfo(
                "Guardado Exitoso",
                "server.properties actualizado.\n\nReinicia el servidor para aplicar cambios.",
                parent=self
            )

    # ── Presets ───────────────────────────────────────────────────────────────

    def _apply_preset(self, preset_name):
        if preset_name not in PRESETS:
            return
        for key, value in PRESETS[preset_name].items():
            if key not in self.widgets:
                continue
            wd = self.widgets[key]
            widget = wd['widget']
            prop_type = wd['type']
            if prop_type == 'bool':
                widget.select() if value.lower() == 'true' else widget.deselect()
            elif prop_type == 'dropdown':
                widget.set(value)
            else:
                widget.delete(0, 'end')
                widget.insert(0, value)

    def _get_app_instance(self):
        widget = self.master
        while widget:
            if hasattr(widget, 'server_manager'):
                return widget
            widget = getattr(widget, 'master', None)
        return None
