import os

import customtkinter as ctk
from PIL import Image

from config.general import CARD_BG, TEXT_LIGHT, ACCENT, TEXT_MUTED, CARD_BG_HOVER


class Sidebar(ctk.CTkFrame):
    """Componente de barra lateral moderna con navegación mejorada."""

    def __init__(self, parent, server_info, on_view_change, on_main_menu):
        super().__init__(
            parent,
            width=280,
            corner_radius=0,
            fg_color=CARD_BG,
            border_width=0
        )
        
        self.grid_propagate(False)  # Mantener ancho fijo

        self.server_info = server_info
        self.on_view_change = on_view_change
        self.on_main_menu = on_main_menu

        self.build_sidebar()

    def build_sidebar(self):
        """Construye el contenido moderno de la sidebar."""
        # Configurar grid
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Separator
        self.grid_rowconfigure(2, weight=0)  # Server info
        self.grid_rowconfigure(3, weight=0)  # Navigation
        self.grid_rowconfigure(4, weight=1)  # Spacer
        self.grid_rowconfigure(5, weight=0)  # Toast
        self.grid_rowconfigure(6, weight=0)  # Main menu button
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=100)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(25, 20))
        header_frame.grid_propagate(False)

        # Logo
        logo_path = os.path.join("icon.png")
        logo_loaded = False

        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                logo_img = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(60, 60)
                )
                ctk.CTkLabel(header_frame, text="", image=logo_img).pack(pady=(0, 5))
                logo_loaded = True
            except Exception:
                pass

        if not logo_loaded:
            ctk.CTkLabel(
                header_frame,
                text="🎮",
                font=ctk.CTkFont(size=40, weight="bold"),
                text_color=ACCENT
            ).pack(pady=(10, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="GetMineHub",
            font=ctk.CTkFont(size=18, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        )
        title_label.pack()

        # Separador
        separator = ctk.CTkFrame(self, height=1, fg_color="#1e1e2e")
        separator.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Nombre del servidor
        server_name_frame = ctk.CTkFrame(self, fg_color=CARD_BG_HOVER, corner_radius=12, height=70)
        server_name_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 20))
        server_name_frame.grid_propagate(False)

        ctk.CTkLabel(
            server_name_frame,
            text="SERVIDOR ACTIVO",
            font=ctk.CTkFont(size=10, weight="bold", family="Segoe UI"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=15, pady=(12, 2))

        server_name = self.server_info['name']
        if len(server_name) > 22:
            server_name = server_name[:22] + "..."
            
        ctk.CTkLabel(
            server_name_frame,
            text=server_name,
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(anchor="w", padx=15, pady=(0, 12))

        # Botones de navegación
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=0)
        
        self.build_navigation_buttons(nav_frame)

        # Spacer
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.grid(row=4, column=0, sticky="nsew")

        # Toast notification area
        self.toast_container = ctk.CTkFrame(self, height=60, fg_color="transparent")
        self.toast_container.grid(row=5, column=0, sticky="ew", padx=15, pady=(10, 15))
        self.toast_container.grid_propagate(False)
        
        self.toast_label = ctk.CTkLabel(
            self.toast_container, 
            text="", 
            corner_radius=10, 
            font=ctk.CTkFont(size=12)
        )

        # Botón menú principal
        self.btn_main_menu = ctk.CTkButton(
            self,
            text="Menú Principal",
            command=self.on_main_menu,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            corner_radius=12,
            fg_color="transparent",
            border_color="#2d2d3f",
            border_width=2,
            text_color=TEXT_LIGHT,
            hover_color=CARD_BG_HOVER
        )
        self.btn_main_menu.grid(row=6, column=0, sticky="ew", padx=15, pady=(0, 20))

    def build_navigation_buttons(self, parent):
        """Construye los botones de navegación."""
        btn_style = {
            "height": 48,
            "fg_color": ACCENT,
            "hover_color": "#a78bfa",
            "anchor": "w",
            "text_color": "#ffffff",
            "font": ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            "corner_radius": 12
        }

        # Consola
        ctk.CTkButton(
            parent,
            text="Consola",
            command=lambda: self.on_view_change('console'),
            **btn_style
        ).pack(fill="x", pady=(0, 8))

        # Jugadores
        ctk.CTkButton(
            parent,
            text="Jugadores",
            command=lambda: self.on_view_change('players'),
            **btn_style
        ).pack(fill="x", pady=(0, 8))

        # Properties
        ctk.CTkButton(
            parent,
            text="Properties",
            command=lambda: self.on_view_change('properties'),
            **btn_style
        ).pack(fill="x", pady=(0, 8))

        # Opciones
        ctk.CTkButton(
            parent,
            text="Opciones",
            command=lambda: self.on_view_change('options'),
            **btn_style
        ).pack(fill="x", pady=(0, 8))

    def get_toast_label(self):
        return self.toast_label

    def set_main_menu_state(self, state):
        self.btn_main_menu.configure(state=state)
