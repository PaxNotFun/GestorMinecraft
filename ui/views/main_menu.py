import shutil
from pathlib import Path

import customtkinter as ctk

from config.general import TEXT_LIGHT, TEXT_MUTED, CARD_BG, CARD_BG_HOVER, ACCENT, INPUT_BORDER
from services.server import server_data
from utils.helpers import fix_scroll_linux


class MainMenuView(ctk.CTkFrame):
    """Vista del menú principal con dashboard informativo y diseño responsivo."""

    def __init__(self, parent, on_new_server, on_open_server, on_settings):
        super().__init__(parent, fg_color="transparent")
        self.on_new_server = on_new_server
        self.on_open_server = on_open_server
        self.on_settings = on_settings
        
        # Configurar grid para responsividad
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.build_menu()

    def build_menu(self):
        """Construye el menú principal mejorado y responsivo."""
        # Scrollable frame principal
        scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#2d2d3f",
            scrollbar_button_hover_color="#3d3d4f"
        )
        scroll_container.grid(row=0, column=0, sticky="nsew")
        fix_scroll_linux(scroll_container)
        
        # Container principal con padding consistente
        main_container = ctk.CTkFrame(scroll_container, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Title
        title_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        title_frame.pack(fill="x", pady=(20, 40))

        title = ctk.CTkLabel(
            title_frame,
            text="GetMineHub",
            font=ctk.CTkFont(size=60, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            title_frame,
            text="Gestiona servidores Minecraft con estilo",
            font=ctk.CTkFont(size=20, family="Segoe UI"),
            text_color=TEXT_MUTED
        )
        subtitle.pack(pady=(10, 0))
        
        # Servidores recientes (primero, después del título)
        self.build_recent_servers(main_container)
        
        # Dashboard de estadísticas (segundo)
        self.build_dashboard(main_container)
        
        # Botones de acción principales (al final)
        btns_container = ctk.CTkFrame(main_container, fg_color="transparent")
        btns_container.pack(fill="x", pady=(20, 20))
        btns_container.grid_columnconfigure(0, weight=1)
        btns_container.grid_columnconfigure(1, weight=1)
        btns_container.grid_columnconfigure(2, weight=1)

        self.create_modern_card(
            btns_container,
            icon="✨",
            title="Crear Servidor",
            description="Configura un nuevo\nservidor desde cero",
            command=self.on_new_server,
            accent_color=ACCENT,
            grid_pos=(0, 0)
        )

        self.create_modern_card(
            btns_container,
            icon="📂",
            title="Abrir Servidor",
            description="Gestiona un servidor\nexistente",
            command=self.on_open_server,
            accent_color="#3b82f6",
            grid_pos=(0, 1)
        )

        self.create_modern_card(
            btns_container,
            icon="⚙️",
            title="Configuración",
            description="Personaliza tu\nexperiencia",
            command=self.on_settings,
            accent_color="#6366f1",
            grid_pos=(0, 2)
        )
    
    def build_dashboard(self, parent):
        """Construye el dashboard de estadísticas con diseño responsivo."""
        stats = server_data.get_database_stats()
        
        dashboard_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dashboard_frame.pack(fill="x", pady=(0, 25))
        dashboard_frame.grid_columnconfigure(0, weight=1)
        dashboard_frame.grid_columnconfigure(1, weight=1)
        dashboard_frame.grid_columnconfigure(2, weight=1)
        dashboard_frame.grid_columnconfigure(3, weight=1)
        
        # Calcular espacio usado
        total_size = 0
        servers = server_data.load_servers()
        for server in servers:
            server_path = Path(server['path'])
            if server_path.exists():
                total_size += self.get_directory_size(server_path)
        
        size_gb = total_size / (1024 ** 3)
        
        # Estadísticas
        self.create_stat_card(
            dashboard_frame,
            icon="🎮",
            value=str(stats['total_servers']),
            label="Servidores Totales",
            color="#8b5cf6",
            grid_pos=(0, 0)
        )
        
        self.create_stat_card(
            dashboard_frame,
            icon="💾",
            value=f"{size_gb:.2f} GB",
            label="Espacio Usado",
            color="#3b82f6",
            grid_pos=(0, 1)
        )
        
        # Tipo más común
        most_common_type = "N/A"
        if stats['by_type']:
            most_common_type = max(stats['by_type'], key=stats['by_type'].get)
        
        self.create_stat_card(
            dashboard_frame,
            icon="⚡",
            value=most_common_type,
            label="Tipo Más Usado",
            color="#10b981",
            grid_pos=(0, 2)
        )
        
        # Versión más común
        most_common_version = "N/A"
        if stats['by_version']:
            most_common_version = max(stats['by_version'], key=stats['by_version'].get)
        
        self.create_stat_card(
            dashboard_frame,
            icon="📦",
            value=most_common_version,
            label="Versión Popular",
            color="#f59e0b",
            grid_pos=(0, 3)
        )
    
    def create_stat_card(self, parent, icon, value, label, color, grid_pos):
        """Crea una tarjeta de estadística con grid."""
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=15,
            border_width=2,
            border_color=INPUT_BORDER
        )
        card.grid(row=grid_pos[0], column=grid_pos[1], sticky="ew", padx=8, pady=5)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=22, pady=28)
        
        ctk.CTkLabel(
            content,
            text=icon,
            font=ctk.CTkFont(size=44),
            text_color=color
        ).pack(pady=(0, 14))
        
        ctk.CTkLabel(
            content,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(pady=(0, 8))
        
        ctk.CTkLabel(
            content,
            text=label,
            font=ctk.CTkFont(size=13, family="Segoe UI"),
            text_color=TEXT_MUTED
        ).pack()
    
    def build_recent_servers(self, parent):
        """Construye la sección de servidores recientes."""
        servers = server_data.load_servers()
        
        if not servers:
            return
        
        # Ordenar por última modificación
        recent_servers = sorted(
            servers,
            key=lambda s: s.get('updated_at', s.get('created_at', '')),
            reverse=True
        )[:3]
        
        recent_frame = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=15,
            border_width=2,
            border_color=INPUT_BORDER
        )
        recent_frame.pack(fill="x", pady=(0, 25))
        
        header = ctk.CTkFrame(recent_frame, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(
            header,
            text="🕒 Servidores Recientes",
            font=ctk.CTkFont(size=18, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(side="left")
        
        # Lista de servidores recientes
        for server in recent_servers:
            self.create_recent_server_item(recent_frame, server)
    
    def create_recent_server_item(self, parent, server):
        """Crea un item de servidor reciente con acceso rápido."""
        type_icons = {
            "Vanilla": "⚡",
            "PaperMC": "📄",
            "Folia": "🌿",
            "Forge": "⚒️",
            "Fabric": "🧵"
        }
        
        item_frame = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG_HOVER,
            corner_radius=12,
            height=78
        )
        item_frame.pack(fill="x", padx=25, pady=(0, 12))
        item_frame.pack_propagate(False)
        
        content = ctk.CTkFrame(item_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=13)
        
        # Icono
        server_type = server.get('type', 'N/A')
        icon = type_icons.get(server_type, "🎮")
        
        icon_label = ctk.CTkLabel(
            content,
            text=icon,
            font=ctk.CTkFont(size=32),
            width=48
        )
        icon_label.pack(side="left", padx=(0, 16))
        
        # Info
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            info_frame,
            text=server['name'],
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(anchor="w", fill="x")
        
        details_text = f"{server_type} • MC {server.get('version', 'N/A')}"
        ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=12, family="Segoe UI"),
            text_color=TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", pady=(4, 0))
        
        # Botón de acceso rápido
        quick_btn = ctk.CTkButton(
            content,
            text="Abrir",
            width=105,
            height=48,
            fg_color=ACCENT,
            hover_color="#a78bfa",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold", family="Segoe UI"),
            corner_radius=10,
            command=lambda s=server: self.open_server_quick(s)
        )
        quick_btn.pack(side="right")
        
        # Hover effect
        def on_enter(e):
            item_frame.configure(fg_color="#1f1f29")
        
        def on_leave(e):
            item_frame.configure(fg_color=CARD_BG_HOVER)
        
        for widget in [item_frame, content, icon_label, info_frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
    
    def open_server_quick(self, server):
        """Abre un servidor rápidamente desde la lista reciente."""
        app = self._get_app_instance()
        if app and hasattr(app, 'show_server_dashboard'):
            app.show_server_dashboard(server)
    
    def get_directory_size(self, path):
        """Calcula el tamaño de un directorio en bytes."""
        total = 0
        try:
            for entry in Path(path).rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total
    
    def _get_app_instance(self):
        """Obtiene la instancia de la aplicación principal."""
        widget = self.master
        while widget:
            if hasattr(widget, 'show_server_dashboard'):
                return widget
            widget = widget.master if hasattr(widget, 'master') else None
        return None

    def create_modern_card(self, parent, icon, title, description, command, accent_color, grid_pos):
        """Crea una tarjeta moderna con hover effect y grid."""
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=20,
            border_width=2,
            border_color=CARD_BG
        )
        card.grid(row=grid_pos[0], column=grid_pos[1], sticky="ew", padx=8, pady=5)
        
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=28, pady=32)
        
        icon_label = ctk.CTkLabel(
            content_frame, 
            text=icon, 
            font=ctk.CTkFont(size=70), 
            text_color=accent_color
        )
        icon_label.pack(pady=(0, 16))
        
        title_label = ctk.CTkLabel(
            content_frame, 
            text=title, 
            font=ctk.CTkFont(size=23, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        )
        title_label.pack(pady=(0, 12))
        
        desc_label = ctk.CTkLabel(
            content_frame, 
            text=description, 
            font=ctk.CTkFont(size=14, family="Segoe UI"), 
            text_color=TEXT_MUTED
        )
        desc_label.pack()

        def on_enter(e):
            card.configure(border_color=accent_color, fg_color=CARD_BG_HOVER)
            icon_label.configure(cursor="hand2")

        def on_leave(e):
            try:
                x, y = card.winfo_pointerxy()
                widget = card.winfo_containing(x, y)
                if widget is not None:
                    if str(widget).startswith(str(card)):
                        return
            except Exception:
                pass
            card.configure(border_color=CARD_BG, fg_color=CARD_BG)
            icon_label.configure(cursor="arrow")

        def on_click(e):
            command()

        for w in [card, content_frame, icon_label, title_label, desc_label]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
