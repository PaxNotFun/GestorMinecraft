import re
import shutil
import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from config.general import (DARK_BG, get_servers_base_dir, save_setting, load_setting, CARD_BG, TEXT_LIGHT, TEXT_MUTED,
                            ACCENT, INPUT_BORDER)
from services.installers import get_installer
from services.server import server_data, server_process
from ui.components.sidebar import Sidebar
from ui.dialogs.new_server import NewServerDialog
from ui.dialogs.open_server import OpenServerDialog
from ui.dialogs.settings import SettingsDialog
from ui.views.console import ConsoleView
from ui.views.main_menu import MainMenuView
from ui.views.server_options import ServerOptionsView
from ui.views.properties_editor import PropertiesEditorView
from ui.views.players_view import PlayersView
from utils.helpers import center_window, check_internet_connection
from utils.notifications import send_notification
from utils.windows_helper import apply_dark_title_bar
from services import version_cache_service as vcs


class MainWindow(ctk.CTk):
    """Ventana principal moderna de la aplicación."""

    def __init__(self):
        super().__init__()
        self.title("GetMineHub")
        self.configure(fg_color=DARK_BG)
        apply_dark_title_bar(self)
        self.update_idletasks()
        center_window(self, 1280, 745)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.active_server_info = None
        self.server_manager = None
        self.active_server_manager = None
        self.current_view = None
        self._restart_pending = False
        self.sidebar = None
        self.content_area = None
        self.setup_layout()
        self.show_main_menu()
        self.after(100, self.try_open_last_server)
        # Poblar cache de versiones en background al arrancar
        self.after(500, lambda: vcs.prefetch_all_in_background())

    def setup_layout(self):
        """Configura el layout principal moderno."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=0)  # Sidebar - tamaño fijo
        self.main_container.grid_columnconfigure(1, weight=1)  # Content - expandible

    def try_open_last_server(self):
        """Intenta abrir el último servidor usado si existe en la configuración."""
        last_path = load_setting("last_server_path")

        if not last_path:
            return

        servers = server_data.load_servers()
        target_server = next((s for s in servers if Path(s['path']) == Path(last_path)), None)

        if target_server:
            self.show_server_dashboard(target_server)

    def clear_content(self):
        """Limpia el área de contenido."""
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.sidebar = None
        self.content_area = None

    def show_main_menu(self):
        """Muestra el menú principal."""
        self.active_server_info = None
        if self.server_manager and self.server_manager.is_running:
            self.server_manager.kill()
        self.server_manager = None
        self.active_server_manager = None
        self.current_view = None
        self.clear_content()

        # Resetear columnas para menú principal
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=0)

        menu_view = MainMenuView(
            self.main_container,
            on_new_server=self.handle_new_server,
            on_open_server=self.handle_open_server,
            on_settings=self.open_settings
        )
        menu_view.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

    def handle_new_server(self):
        """Maneja la creación de un nuevo servidor."""
        if not check_internet_connection():
            messagebox.showerror(
                "Error de Red",
                "No se puede crear un nuevo servidor sin conexión a internet.",
                parent=self
            )
            return
        NewServerDialog(self)

    def handle_open_server(self):
        """Maneja la apertura de un servidor existente."""
        servers = server_data.load_servers()
        if not servers:
            messagebox.showinfo(
                "Info",
                "No hay servidores guardados. ¡Crea uno nuevo!",
                parent=self
            )
            return
        OpenServerDialog(self, servers)

    def open_settings(self):
        """Abre la ventana de configuración."""
        SettingsDialog(self)

    def process_new_server_result(self, result, is_reinstall=False, is_update=False):
        """Procesa el resultado del diálogo de nuevo servidor, reinstalación o actualización."""
        if not result:
            self.focus()
            return

        server_name = result['name']

        if not is_reinstall and not is_update:
            if not re.match(r'^[a-zA-Z0-9_.\s-]+$', server_name) or ".." in server_name:
                messagebox.showerror(
                    "Error",
                    "El nombre del servidor contiene caracteres inválidos.\n"
                    "Solo se permiten letras, números, espacios, guiones y guiones bajos.",
                    parent=self
                )
                return

        if is_reinstall or is_update:
            server_path = Path(result['original_path'])
            if 'path' not in result:
                result['path'] = str(server_path)
        else:
            folder_name = server_data.generate_server_folder_name()
            server_path = get_servers_base_dir() / folder_name

            if server_path.exists():
                messagebox.showerror(
                    "Error",
                    "Error generando carpeta única. Por favor, intenta de nuevo.",
                    parent=self
                )
                return

            result['path'] = str(server_path)

        self.show_installation_progress(result, server_path, is_reinstall, is_update)

    def show_installation_progress(self, server_info, server_path, is_reinstall, is_update=False):
        """Muestra el progreso de instalación moderno."""
        self.clear_content()

        # Resetear columnas
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=0)

        progress_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        progress_container.grid(row=0, column=0, sticky="nsew")
        progress_container.grid_rowconfigure(0, weight=1)
        progress_container.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(progress_container, fg_color="transparent")
        content.grid(row=0, column=0)

        icon_label = ctk.CTkLabel(content, text="⚙️", font=ctk.CTkFont(size=72))
        icon_label.pack(pady=(0, 20))

        if is_update:
            title_text = "Actualizando Servidor"
        elif is_reinstall:
            title_text = "Reinstalando Servidor"
        else:
            title_text = "Creando Servidor"
        ctk.CTkLabel(
            content,
            text=title_text,
            font=ctk.CTkFont(size=32, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(pady=(0, 10))

        self.progress_label = ctk.CTkLabel(
            content,
            text="Iniciando...",
            font=ctk.CTkFont(size=16, family="Segoe UI"),
            text_color=TEXT_MUTED
        )
        self.progress_label.pack(pady=(0, 30))

        progress_frame = ctk.CTkFrame(
            content, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=INPUT_BORDER, height=80
        )
        progress_frame.pack(fill="x", padx=80)
        progress_frame.pack_propagate(False)

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame, mode="determinate", height=20, progress_color=ACCENT, corner_radius=10, border_width=0
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(padx=20, pady=30, fill="x")

        try:
            reinstall_mode = server_info.get('reinstall_mode', 'partial')
            installer = get_installer(
                server_info, str(server_path), self, self.on_installation_progress,
                is_reinstall or is_update, reinstall_mode, is_update
            )
            threading.Thread(target=installer.run_installation, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error de Creación", f"No se pudo iniciar la instalación:\n{e}", parent=self)
            self.show_main_menu()

    def on_installation_progress(self, status):
        """Maneja las actualizaciones de progreso de instalación."""
        if status.get("progress"):
            self.update_progress(progress_val=status["progress"])
        if status.get("text"):
            self.update_progress(text=status["text"])
        if status.get("error"):
            messagebox.showerror("Error en la Operación", f"Ocurrió un error:\n{status['error']}", parent=self)

            path_to_clean = Path(status['path'])
            if "reinstall_mode=total" in status.get("reinstall_details", ""):
                if path_to_clean.exists():
                    shutil.rmtree(path_to_clean, ignore_errors=True)

            self.show_main_menu()

        if status.get("success"):
            new_server_data = status["server_data"]
            if status.get("was_update"):
                action = "actualizado"
            elif status.get("was_reinstall"):
                action = "reinstalado"
            else:
                action = "creado"
            self.show_notification(f"¡Servidor '{new_server_data['name']}' {action}!")
            self.show_server_dashboard(new_server_data)

    def update_progress(self, text=None, progress_val=None):
        """Actualiza el texto y barra de progreso."""
        if text and hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
            self.progress_label.configure(text=text)
        if progress_val is not None and hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
            self.progress_bar.set(progress_val)

    def show_server_dashboard(self, server_info):
        """Muestra el dashboard del servidor."""
        if not server_info or 'path' not in server_info:
            messagebox.showerror(
                "Error",
                "Información del servidor inválida (falta 'path').",
                parent=self
            )
            self.show_main_menu()
            return

        save_setting('last_server_path', server_info['path'])

        self.clear_content()
        self.focus()
        self.active_server_info = server_info

        # Configurar columnas para vista de servidor
        self.main_container.grid_columnconfigure(0, weight=0)  # Sidebar fija
        self.main_container.grid_columnconfigure(1, weight=1)  # Content expandible

        if not self.server_manager or self.server_manager.server_info['path'] != server_info['path']:
            self.server_manager = server_process.ServerManager(
                server_info,
                lambda text: self.on_console_update(text),
                lambda running: self.on_status_change(running),
                lambda: self.on_graceful_stop_failed()
            )

        self.active_server_manager = self.server_manager

        self.sidebar = Sidebar(
            self.main_container,
            server_info,
            on_view_change=self.change_view,
            on_main_menu=self.show_main_menu
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", pady=0, padx=0)

        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self.change_view('console')

    def change_view(self, view_name):
        """Cambia la vista central."""
        for widget in self.content_area.winfo_children():
            widget.destroy()

        if view_name == 'console':
            self.current_view = ConsoleView(
                self.content_area,
                self.active_server_info,
                app_instance=self
            )
            if hasattr(self.current_view, 'update_status') and self.server_manager:
                self.current_view.update_status(self.server_manager.is_running)

        elif view_name == 'players':
            self.current_view = PlayersView(
                self.content_area,
                self.active_server_info,
                app_instance=self
            )

        elif view_name == 'properties':
            self.current_view = PropertiesEditorView(
                self.content_area,
                self.active_server_info
            )

        elif view_name == 'options':
            self.current_view = ServerOptionsView(
                self.content_area,
                self.active_server_info
            )

        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_console_view(self, view_name):
        self.change_view('console')

    def on_console_update(self, text):
        """Maneja actualizaciones de la consola con alta prioridad."""
        if self.current_view and hasattr(self.current_view, 'console_widget'):
            try:
                if hasattr(self.current_view.console_widget, 'append_text'):
                    self.current_view.console_widget.append_text(text)
                elif hasattr(self.current_view.console_widget, 'write'):
                    self.current_view.console_widget.write(text)
            except Exception:
                pass

    def on_status_change(self, is_running):
        """Llamado desde el thread _read_output — despacha al hilo principal."""
        self.after(0, self._apply_status_change, is_running)

    def _apply_status_change(self, is_running):
        """Aplica cambios de estado en el hilo principal de Tkinter."""
        if self.current_view and hasattr(self.current_view, 'update_status'):
            self.current_view.update_status(is_running)

        if self.sidebar:
            self.sidebar.set_main_menu_state("disabled" if is_running else "normal")

        if hasattr(self, '_restart_pending') and self._restart_pending and not is_running:
            self._restart_pending = False
            self.start_server()

    def on_graceful_stop_failed(self):
        """Llamado desde threading.Timer — despacha al hilo principal."""
        self.after(0, self._apply_graceful_stop_failed)

    def _apply_graceful_stop_failed(self):
        """Habilita el botón de forzar apagado en el hilo principal."""
        if self.current_view and hasattr(self.current_view, 'enable_force_kill'):
            self.current_view.enable_force_kill()

    def start_server(self):
        """Inicia el servidor."""
        if self.server_manager and not self.server_manager.is_running:
            try:
                if self.current_view and hasattr(self.current_view, 'clear_console'):
                    self.current_view.clear_console()
                self.server_manager.start()
            except Exception as e:
                messagebox.showerror("Error al Iniciar Servidor", str(e), parent=self)
                if self.server_manager:
                    self.server_manager._cleanup_and_reset_status()
        elif self.server_manager and self.server_manager.is_running:
            self.show_notification("El servidor ya está encendido.")

    def stop_server(self):
        """Detiene el servidor."""
        if self.server_manager and self.server_manager.is_running:
            btn_stop = getattr(self.current_view, 'btn_stop', None)

            if btn_stop and hasattr(btn_stop, 'cget') and "Forzar" in btn_stop.cget("text"):
                btn_stop.configure(text="Forzando...", state="disabled")
                self.server_manager.kill()
            else:
                if btn_stop:
                    btn_stop.configure(text="Apagando...", state="disabled")
                self.server_manager.stop()
            if load_setting("notifications_enabled", True):
                send_notification(
                    "Servidor Apagado",
                    f"El servidor '{self.active_server_info['name']}' se está apagando."
                )
        else:
            self.show_notification("El servidor no está encendido.")

    def restart_server(self):
        """Reinicia el servidor."""
        if self.server_manager and self.server_manager.is_running:
            self.stop_server()
            self._restart_pending = True
        else:
            self.start_server()

    def enable_force_kill(self):
        """Habilita el forzado de apagado."""
        if self.current_view and hasattr(self.current_view, 'enable_force_kill'):
            self.current_view.enable_force_kill()

    def show_notification(self, message):
        """Muestra una notificación en la sidebar."""
        if self.sidebar:
            toast_label = self.sidebar.get_toast_label()
            if toast_label and toast_label.winfo_exists():
                toast_label.configure(
                    text=message,
                    pady=12,
                    fg_color=CARD_BG,
                    text_color=TEXT_LIGHT
                )
                toast_label.pack(fill="x", padx=5)
                self.after(3000, lambda: self.clear_notification())

    def clear_notification(self):
        """Limpia la notificación."""
        if self.sidebar:
            toast_label = self.sidebar.get_toast_label()
            if toast_label and toast_label.winfo_exists():
                toast_label.pack_forget()
                toast_label.configure(text="", fg_color="transparent", pady=0)

    def on_close(self):
        """Maneja el cierre de la aplicación."""
        if self.server_manager and self.server_manager.is_running:
            if messagebox.askyesno(
                    "Servidor Activo",
                    "El servidor está encendido. ¿Forzar el cierre de todo?",
                    parent=self
            ):
                self.server_manager.kill()
                self.destroy()
            return
        self.destroy()
