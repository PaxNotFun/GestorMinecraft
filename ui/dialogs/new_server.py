import threading

import customtkinter as ctk

from config.general import CARD_BG, ACCENT, TEXT_LIGHT, TEXT_MUTED, INPUT_BG, INPUT_BORDER
from utils.helpers import center_window
from utils.windows_helper import apply_dark_title_bar
from utils.dialog_helper import safe_grab_set
from ui.components.scrollable_dropdown import ScrollableDropdown
from services import version_cache_service as vcs


class NewServerDialog(ctk.CTkToplevel):
    """Dialogo moderno para crear un nuevo servidor."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.result = None
        self.setup_window()
        self.build_dialog()

    def setup_window(self):
        self.title("Crear Nuevo Servidor")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        safe_grab_set(self)
        apply_dark_title_bar(self)
        self.configure(fg_color="#0a0a0f")
        self.update_idletasks()
        center_window(self, 520, 655)

    def build_dialog(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=30, pady=30)

        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 30))

        ctk.CTkLabel(header_frame, text="✨", font=ctk.CTkFont(size=48)).pack(pady=(0, 10))
        ctk.CTkLabel(
            header_frame, text="Crear Nuevo Servidor",
            font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack()
        ctk.CTkLabel(
            header_frame, text="Configura tu servidor en 3 simples pasos",
            font=ctk.CTkFont(size=14, family="Segoe UI"), text_color=TEXT_MUTED
        ).pack(pady=(5, 0))

        form_container = ctk.CTkFrame(
            main_container, fg_color=CARD_BG, corner_radius=20,
            border_width=1, border_color=INPUT_BORDER
        )
        form_container.pack(fill="both", expand=True, pady=(0, 20))
        form_content = ctk.CTkFrame(form_container, fg_color="transparent")
        form_content.pack(fill="both", expand=True, padx=25, pady=25)

        self.build_server_type_section(form_content)
        self.build_version_section(form_content)
        self.build_name_section(form_content)

        self.create_button = ctk.CTkButton(
            main_container, text="🚀  Crear Servidor",
            command=self.on_create, state="disabled", height=55,
            font=ctk.CTkFont(size=16, weight="bold", family="Segoe UI"),
            fg_color=ACCENT, hover_color="#a78bfa", corner_radius=15
        )
        self.create_button.pack(fill="x")

        self.name_entry.focus()
        self._on_type_change(self.type_menu.get())

    def build_server_type_section(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            section, text="Tipo de Servidor",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT, anchor="w"
        ).pack(fill="x", pady=(0, 10))

        self.type_menu = ctk.CTkOptionMenu(
            section,
            values=["Vanilla", "PaperMC", "Folia", "Forge", "Fabric"],
            command=self._on_type_change,
            height=48, fg_color=INPUT_BG, button_color=ACCENT,
            button_hover_color="#a78bfa", dropdown_fg_color=CARD_BG,
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            dropdown_font=ctk.CTkFont(size=13, family="Segoe UI"),
            corner_radius=12
        )
        self.type_menu.pack(fill="x")

    def build_version_section(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(0, 20))

        row = ctk.CTkFrame(section, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            row, text="Version de Minecraft",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT, anchor="w"
        ).grid(row=0, column=0, sticky="w")

        self.version_status_label = ctk.CTkLabel(
            row, text="",
            font=ctk.CTkFont(size=12, family="Segoe UI"),
            text_color=TEXT_MUTED
        )
        self.version_status_label.grid(row=0, column=1, sticky="e")

        self.version_var = ctk.StringVar(value="Cargando versiones...")
        self.version_dropdown = ScrollableDropdown(
            section,
            values=["Cargando versiones..."],
            variable=self.version_var,
            command=self._on_version_change,
            height=48, max_items=10, state="disabled",
        )
        self.version_dropdown.pack(fill="x")

    def build_name_section(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x")

        ctk.CTkLabel(
            section, text="Nombre del Servidor",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT, anchor="w"
        ).pack(fill="x", pady=(0, 10))

        self.name_entry = ctk.CTkEntry(
            section, placeholder_text="Mi Servidor Epico",
            height=48, fg_color=INPUT_BG, border_color=INPUT_BORDER,
            border_width=2, corner_radius=12,
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_LIGHT, placeholder_text_color=TEXT_MUTED
        )
        self.name_entry.pack(fill="x")
        self.name_entry.bind("<KeyRelease>", self._check_create_button)
        self.name_entry.bind("<FocusIn>",  lambda e: self.name_entry.configure(border_color=ACCENT))
        self.name_entry.bind("<FocusOut>", lambda e: self.name_entry.configure(border_color=INPUT_BORDER))

    # ── Logica de versiones ──────────────────────────────────────────────────

    def _on_type_change(self, server_type):
        """Al cambiar tipo, lee del cache (instantaneo) o descarga si no hay."""
        self.version_var.set("Cargando versiones...")
        self.version_dropdown.configure(state="disabled", values=["Cargando versiones..."])
        self.version_status_label.configure(text="🔍 Consultando...", text_color=TEXT_MUTED)
        self.create_button.configure(state="disabled")

        # Intentar cache en memoria primero (no bloquea UI)
        from services.version_cache_service import _memory_cache, _memory_lock
        import threading as _t
        with _memory_lock:
            cached = _memory_cache.get(server_type)
        if cached:
            self._apply_versions(server_type, cached)
            return

        # No hay en memoria: leer DB o API en background
        _t.Thread(
            target=self._fetch_versions_bg,
            args=(server_type,),
            daemon=True
        ).start()

    def _fetch_versions_bg(self, server_type):
        versions = vcs.get_versions(server_type)
        if self.winfo_exists():
            self.after(0, lambda: self._apply_versions(server_type, versions))

    def _apply_versions(self, server_type, versions):
        if not self.winfo_exists():
            return
        # Ignorar si el tipo cambio mientras esperabamos
        if self.type_menu.get() != server_type:
            return
        if versions:
            self.version_dropdown.configure(state="normal", values=versions)
            self.version_var.set(versions[0])
            self.version_status_label.configure(
                text=f"✅ {len(versions)} versiones", text_color="#10b981"
            )
        else:
            self.version_dropdown.configure(state="disabled", values=["Sin versiones disponibles"])
            self.version_var.set("Sin versiones disponibles")
            self.version_status_label.configure(text="❌ Sin conexion", text_color="#ef4444")
        self._check_create_button()

    def _on_version_change(self, value):
        self._check_create_button()

    def _check_create_button(self, event=None):
        version = self.version_var.get()
        version_ok = version and version not in ("Cargando versiones...", "Sin versiones disponibles")
        name_ok = bool(self.name_entry.get().strip())
        self.create_button.configure(state="normal" if (version_ok and name_ok) else "disabled")

    def on_create(self):
        self.result = {
            "type": self.type_menu.get(),
            "version": self.version_var.get(),
            "name": self.name_entry.get().strip()
        }
        self.on_close()

    def on_close(self):
        if self.result:
            self.parent_app.process_new_server_result(self.result)
        self.destroy()
