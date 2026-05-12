import customtkinter as ctk

from config.general import SUCCESS, SUCCESS_HOVER, DANGER, DANGER_HOVER, WARNING, WARNING_HOVER, TEXT_LIGHT, CARD_BG, load_setting
from ui.components.console_widget import ConsoleWidget
from utils.notifications import send_notification


class ConsoleView(ctk.CTkFrame):
    def __init__(self, parent, server_info, app_instance):
        super().__init__(parent, fg_color="transparent")
        self.server_info = server_info
        self.app = app_instance
        self.initial_start_notification_sent = False
        self.build_view()
        self.restore_state()
        active_manager = getattr(self.app, 'active_server_manager', None)

        if active_manager and active_manager.server_info['path'] == self.server_info['path']:
            is_running = active_manager.is_running
        else:
            is_running = False

        self.update_status(is_running)

    def build_view(self):
        # Configurar grid
        self.grid_rowconfigure(0, weight=0)  # Header - tamaño fijo
        self.grid_rowconfigure(1, weight=0)  # Controls - tamaño fijo
        self.grid_rowconfigure(2, weight=1)  # Console - expandible
        self.grid_columnconfigure(0, weight=1)
        
        self.build_header()
        self.build_controls()

        self.console_widget = ConsoleWidget(
            self,
            on_command_send=self.on_widget_command
        )
        self.console_widget.grid(row=2, column=0, sticky="nsew", pady=(15, 0))

    def build_header(self):
        header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=15, height=80)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_propagate(False)

        info_container = ctk.CTkFrame(header, fg_color="transparent")
        info_container.pack(side="left", fill="both", expand=True, padx=25, pady=15)

        ctk.CTkLabel(
            info_container,
            text=self.server_info['name'],
            font=ctk.CTkFont(size=24, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(anchor="w")

        info_text = f"{self.server_info.get('type', 'N/A')} - {self.server_info.get('version', 'N/A')}"
        ctk.CTkLabel(
            info_container,
            text=info_text,
            font=ctk.CTkFont(size=13, family="Segoe UI"),
            text_color="#64748b",
            anchor="w"
        ).pack(anchor="w", pady=(5, 0))

    def build_controls(self):
        controls = ctk.CTkFrame(self, fg_color="transparent", height=60)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 0))
        controls.grid_propagate(False)

        btn_style = {"height": 50, "width": 140, "font": ctk.CTkFont(size=15, weight="bold"), "corner_radius": 12}

        self.btn_start = ctk.CTkButton(
            controls, text="Encender", command=self.app.start_server,
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER, **btn_style
        )
        self.btn_start.pack(side="left", padx=(0, 12))

        self.btn_stop = ctk.CTkButton(
            controls, text="Apagar", command=self.app.stop_server,
            fg_color=DANGER, hover_color=DANGER_HOVER, state="disabled", **btn_style
        )
        self.btn_stop.pack(side="left", padx=(0, 12))

        self.btn_restart = ctk.CTkButton(
            controls, text="Reiniciar", command=self.app.restart_server,
            fg_color=WARNING, hover_color=WARNING_HOVER, state="disabled", **btn_style
        )
        self.btn_restart.pack(side="left")

    def restore_state(self):
        active_manager = getattr(self.app, 'active_server_manager', None)

        if active_manager and active_manager.server_info['path'] == self.server_info['path']:
            if hasattr(active_manager, 'get_history'):
                history = active_manager.get_history()
                if history and hasattr(self.console_widget, 'append_text'):
                    self.console_widget.append_text(history)

            if hasattr(active_manager, 'set_console_callback') and hasattr(self.console_widget, 'append_text'):
                active_manager.set_console_callback(self.console_widget.append_text)

    def on_widget_command(self, cmd):
        if not cmd: return
        active_manager = getattr(self.app, 'active_server_manager', None)
        if active_manager and active_manager.is_running:
            active_manager.send_command(cmd)
        else:
            if hasattr(self.console_widget, 'append_text'):
                self.console_widget.append_text("\n❌ Error: El servidor no está corriendo.\n")

    def update_status(self, is_running):
        if is_running and not self.initial_start_notification_sent:
            if load_setting("notifications_enabled", True):
                send_notification("Servidor Encendido", f"El servidor '{self.server_info['name']}' está listo.")
            self.initial_start_notification_sent = True
        elif not is_running:
            self.initial_start_notification_sent = False

        if hasattr(self, 'btn_start'):
            self.btn_start.configure(state="disabled" if is_running else "normal")

        if hasattr(self, 'btn_stop'):
            self.btn_stop.configure(
                state="normal" if is_running else "disabled",
                text="Apagar",
                fg_color=DANGER
            )

        if hasattr(self, 'btn_restart'):
            self.btn_restart.configure(state="normal" if is_running else "disabled")

        if hasattr(self.console_widget, 'set_input_state'):
            self.console_widget.set_input_state("normal" if is_running else "disabled")

    def enable_force_kill(self):
        if hasattr(self, 'btn_stop'):
            self.btn_stop.configure(text="Forzar", state="normal")

    def clear_console(self):
        if hasattr(self.console_widget, 'clear_console'):
            self.console_widget.clear_console()
