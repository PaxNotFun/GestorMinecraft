from tkinter import filedialog, messagebox

import customtkinter as ctk

from config import general
from config.general import CARD_BG, TEXT_LIGHT, TEXT_MUTED, ACCENT, INPUT_BG, INPUT_BORDER
from utils.helpers import center_window
from utils.windows_helper import apply_dark_title_bar
from utils.dialog_helper import safe_grab_set


class SettingsDialog(ctk.CTkToplevel):
    """Diálogo moderno de configuración general."""

    def __init__(self, parent):
        super().__init__(parent)

        self.parent_app = parent
        self.settings = general.load_all_settings()

        self.setup_window()
        self.build_dialog()

    def setup_window(self):
        """Configura la ventana moderna."""
        self.title("Configuración")
        safe_grab_set(self)
        apply_dark_title_bar(self)
        self.configure(fg_color="#0a0a0f")
        center_window(self, 580, 610)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def build_dialog(self):
        """Construye el contenido del diálogo moderno."""
        # Container principal
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=30, pady=30)

        # Header con icono
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))

        icon = ctk.CTkLabel(
            header_frame,
            text="⚙️",
            font=ctk.CTkFont(size=48)
        )
        icon.pack(pady=(0, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="Configuración",
            font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Personaliza GetMineHub a tu gusto",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_MUTED
        )
        subtitle.pack(pady=(5, 0))

        # Contenedor de configuraciones
        settings_container = ctk.CTkFrame(
            main_container,
            fg_color="transparent"
        )
        settings_container.pack(fill="both", expand=True, pady=(0, 20))

        # Directorio base
        self.build_directory_section(settings_container)

        # Límite de RAM
        self.build_ram_section(settings_container)

        # Notificaciones
        self.build_notifications_section(settings_container)

        # Botones de acción
        self.build_buttons(main_container)

    def build_directory_section(self, parent):
        """Construye la sección moderna de directorio."""
        section = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=INPUT_BORDER
        )
        section.pack(fill="x", pady=(0, 15))

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=20)

        # Label con icono
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            header,
            text="📁  Directorio de Servidores",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(side="left")

        # Input y botón
        input_frame = ctk.CTkFrame(content, fg_color="transparent")
        input_frame.pack(fill="x")
        input_frame.grid_columnconfigure(0, weight=1)

        self.dir_entry = ctk.CTkEntry(
            input_frame,
            height=45,
            fg_color=INPUT_BG,
            border_color=INPUT_BORDER,
            border_width=2,
            corner_radius=12,
            font=ctk.CTkFont(size=13, family="Segoe UI"),
            text_color=TEXT_LIGHT
        )
        self.dir_entry.insert(0, self.settings.get("servers_base_dir", ""))
        self.dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.dir_entry.bind("<FocusIn>", lambda e: self.dir_entry.configure(border_color=ACCENT))
        self.dir_entry.bind("<FocusOut>", lambda e: self.dir_entry.configure(border_color=INPUT_BORDER))

        browse_btn = ctk.CTkButton(
            input_frame,
            text="Examinar",
            width=110,
            height=45,
            command=self.browse_directory,
            fg_color=INPUT_BG,
            hover_color=CARD_BG,
            border_width=2,
            border_color=INPUT_BORDER,
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=13, weight="bold", family="Segoe UI"),
            corner_radius=12
        )
        browse_btn.grid(row=0, column=1)

    def build_ram_section(self, parent):
        """Construye la sección moderna de RAM."""
        section = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=INPUT_BORDER
        )
        section.pack(fill="x")

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=20)

        # Label con icono
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            header,
            text="💾  Límite de RAM",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(side="left")

        self.ram_entry = ctk.CTkEntry(
            content,
            height=45,
            fg_color=INPUT_BG,
            border_color=INPUT_BORDER,
            border_width=2,
            corner_radius=12,
            font=ctk.CTkFont(size=13, family="Segoe UI"),
            text_color=TEXT_LIGHT,
            placeholder_text="0 = Sin límite"
        )
        self.ram_entry.insert(0, str(self.settings.get("max_ram_limit", 0)))
        self.ram_entry.pack(fill="x")
        self.ram_entry.bind("<FocusIn>", lambda e: self.ram_entry.configure(border_color=ACCENT))
        self.ram_entry.bind("<FocusOut>", lambda e: self.ram_entry.configure(border_color=INPUT_BORDER))

        help_text = ctk.CTkLabel(
            content,
            text="Límite máximo de RAM por servidor en MB (0 = sin límite)",
            font=ctk.CTkFont(size=12, family="Segoe UI"),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        help_text.pack(fill="x", pady=(8, 0))

    def build_notifications_section(self, parent):
        """Construye la sección de notificaciones."""
        section = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=INPUT_BORDER
        )
        section.pack(fill="x", pady=(15, 0))

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=18)

        text_frame = ctk.CTkFrame(content, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            text_frame,
            text="🔔  Notificaciones de Escritorio",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_frame,
            text="Avisos al encender o apagar un servidor",
            font=ctk.CTkFont(size=12, family="Segoe UI"),
            text_color=TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", pady=(3, 0))

        self.notifications_var = ctk.IntVar(
            value=1 if self.settings.get("notifications_enabled", True) else 0
        )
        ctk.CTkSwitch(
            content,
            text="",
            variable=self.notifications_var,
            width=46,
            button_color=ACCENT,
            button_hover_color="#a78bfa",
            progress_color=ACCENT,
        ).pack(side="right")

    def build_buttons(self, parent):
        """Construye los botones de acción modernos."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")

        # Botón Cancelar
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self.destroy,
            height=50,
            width=140,
            fg_color="transparent",
            border_width=2,
            border_color=INPUT_BORDER,
            hover_color=CARD_BG,
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            corner_radius=12
        )
        cancel_btn.pack(side="left")

        # Spacer
        ctk.CTkFrame(btn_frame, fg_color="transparent").pack(side="left", fill="x", expand=True)

        # Botón Guardar
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾  Guardar",
            command=self.save_and_close,
            height=50,
            width=160,
            fg_color=ACCENT,
            hover_color="#a78bfa",
            text_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            corner_radius=12
        )
        save_btn.pack(side="right")

    def browse_directory(self):
        """Abre el explorador de archivos para seleccionar directorio."""
        directory = filedialog.askdirectory(
            mustexist=True,
            title="Selecciona el Directorio Base para Servidores",
            parent=self
        )
        if directory:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, directory)

    def save_and_close(self):
        """Guarda la configuración y cierra el diálogo."""
        new_dir = self.dir_entry.get().strip()

        try:
            new_ram_limit = int(self.ram_entry.get().strip())
            if new_ram_limit < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error",
                "El límite de RAM debe ser un número entero no negativo.",
                parent=self
            )
            return

        if not new_dir:
            messagebox.showerror(
                "Error",
                "El directorio base no puede estar vacío.",
                parent=self
            )
            return

        self.settings["servers_base_dir"] = new_dir
        self.settings["max_ram_limit"] = new_ram_limit
        self.settings["notifications_enabled"] = bool(self.notifications_var.get())

        general.save_all_settings(self.settings)
        general.ensure_config_exists()

        messagebox.showinfo(
            "✅  Configuración Guardada",
            "Los cambios se han aplicado correctamente.",
            parent=self
        )
        self.destroy()