import customtkinter as ctk

from config.general import CARD_BG, TEXT_LIGHT, TEXT_MUTED, CARD_BG_HOVER, ACCENT
from utils.helpers import center_window, fix_scroll_linux
from utils.windows_helper import apply_dark_title_bar
from utils.dialog_helper import safe_grab_set


class OpenServerDialog(ctk.CTkToplevel):
    """Diálogo moderno para abrir un servidor existente."""

    def __init__(self, parent, servers):
        super().__init__(parent)
        self.parent_app = parent
        self.servers = servers
        self.setup_window()
        self.build_dialog()

    def setup_window(self):
        """Configura la ventana moderna."""
        self.title("Abrir Servidor")
        safe_grab_set(self)
        apply_dark_title_bar(self)
        self.configure(fg_color="#0a0a0f")
        self.update_idletasks()
        center_window(self, 520, 695)

    def build_dialog(self):
        """Construye el contenido del diálogo moderno."""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=30, pady=30)
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))

        icon = ctk.CTkLabel(
            header_frame,
            text="📂",
            font=ctk.CTkFont(size=48)
        )
        icon.pack(pady=(0, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="Tus Servidores",
            font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            header_frame,
            text=f"{len(self.servers)} servidor{'es' if len(self.servers) != 1 else ''} disponible{'s' if len(self.servers) != 1 else ''}",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_MUTED
        )
        subtitle.pack(pady=(5, 0))

        scroll_frame = ctk.CTkScrollableFrame(
            main_container,
            fg_color="transparent",
            scrollbar_button_color="#2d2d3f",
            scrollbar_button_hover_color="#3d3d4f"
        )
        scroll_frame.pack(fill="both", expand=True)
        fix_scroll_linux(scroll_frame)

        if not self.servers:
            empty_frame = ctk.CTkFrame(scroll_frame, fg_color=CARD_BG, corner_radius=20)
            empty_frame.pack(fill="both", expand=True, padx=10, pady=40)

            ctk.CTkLabel(
                empty_frame,
                text="🎮",
                font=ctk.CTkFont(size=48)
            ).pack(pady=(40, 10))

            ctk.CTkLabel(
                empty_frame,
                text="No hay servidores",
                font=ctk.CTkFont(size=18, weight="bold", family="Segoe UI"),
                text_color=TEXT_LIGHT
            ).pack(pady=(0, 5))

            ctk.CTkLabel(
                empty_frame,
                text="Crea tu primer servidor para comenzar",
                font=ctk.CTkFont(size=13, family="Segoe UI"),
                text_color=TEXT_MUTED
            ).pack(pady=(0, 40))
        else:
            for server in sorted(self.servers, key=lambda x: x.get('name', '').lower()):
                self.create_server_card(scroll_frame, server)

    def create_server_card(self, parent, server):
        """Crea una tarjeta moderna de servidor."""
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=2,
            border_color=CARD_BG,
            height=100
        )
        card.pack(pady=8, padx=10, fill="x")
        card.pack_propagate(False)
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        type_icons = {
            "Vanilla": "⚡",
            "PaperMC": "📄",
            "Folia": "🌿",
            "Forge": "⚒️",
            "Fabric": "🧵"
        }
        server_type = server.get('type', 'N/A')
        icon = type_icons.get(server_type, "🎮")

        icon_label = ctk.CTkLabel(
            content,
            text=icon,
            font=ctk.CTkFont(size=32),
            width=50
        )
        icon_label.pack(side="left", padx=(0, 15))

        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        name_label = ctk.CTkLabel(
            info_frame,
            text=server['name'],
            font=ctk.CTkFont(size=16, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        )
        name_label.pack(anchor="w", fill="x")

        details_text = f"{server_type} • MC {server.get('version', 'N/A')}"
        details_label = ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=13, family="Segoe UI"),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        details_label.pack(anchor="w", pady=(5, 0))

        arrow_label = ctk.CTkLabel(
            content,
            text="→",
            font=ctk.CTkFont(size=24),
            text_color=TEXT_MUTED,
            width=30
        )
        arrow_label.pack(side="right")

        def on_enter(e):
            card.configure(border_color=ACCENT, fg_color=CARD_BG_HOVER)
            arrow_label.configure(text_color=ACCENT)
            card.configure(cursor="hand2")

        def on_leave(e):
            card.configure(border_color=CARD_BG, fg_color=CARD_BG)
            arrow_label.configure(text_color=TEXT_MUTED)

        def on_click(e):
            self.select_server(server)

        for widget in [card, content, icon_label, info_frame, name_label, details_label, arrow_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def select_server(self, server):
        """Selecciona un servidor y cierra el diálogo."""
        self.parent_app.show_server_dashboard(server)
        self.destroy()