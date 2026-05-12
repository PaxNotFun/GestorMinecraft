import os
import platform
import subprocess
import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from config.general import TEXT_LIGHT, TEXT_MUTED, CARD_BG, CARD_BG_HOVER, DANGER, DANGER_HOVER, WARNING, WARNING_HOVER, ACCENT, INPUT_BORDER
from services.server.server_data import load_server_config, save_server_config, delete_server
from services import version_cache_service as vcs
from ui.components.scrollable_dropdown import ScrollableDropdown
from utils.helpers import fix_scroll_linux

class ServerOptionsView(ctk.CTkFrame):
    def __init__(self, parent, server_info):
        super().__init__(parent, fg_color="transparent")
        self.server_info = server_info
        self.server_path = server_info['path']
        self.local_config = load_server_config(self.server_path)

        # Variables
        self.reinstall_mode_var = ctk.StringVar(value="partial")
        self.delete_mode_var = ctk.StringVar(value="keep_files")
        self.aikar_flags_var = ctk.IntVar(value=1 if self.local_config.get('use_aikar_flags', False) else 0)

        self.build_view()

    def build_view(self):
        # Configurar grid principal
        self.grid_rowconfigure(0, weight=0)  # Header fijo
        self.grid_rowconfigure(1, weight=1)  # Scroll expandible
        self.grid_columnconfigure(0, weight=1)

        # Header (FUERA del scroll)
        header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=15, height=90)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            header_content,
            text=f"Opciones: {self.server_info.get('name')}",
            font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        # Scrollable frame (DEBAJO del header)
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#2d2d3f",
            scrollbar_button_hover_color="#3d3d4f"
        )
        scroll.grid(row=1, column=0, sticky="nsew")
        fix_scroll_linux(scroll)

        # Container principal dentro del scroll
        main_container = ctk.CTkFrame(scroll, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Sección de gestión de archivos
        self.build_files_section(main_container)

        # Sección de rendimiento
        self.build_performance_section(main_container)

        # Sección de actualización
        self.build_update_section(main_container)

        # Zona peligrosa
        self.build_danger_zone(main_container)

    def build_performance_section(self, parent):
        """Sección de rendimiento."""
        perf_frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=15)
        perf_frame.pack(fill="x", pady=(0, 15))

        # Header
        ctk.CTkLabel(
            perf_frame,
            text="⚡ Rendimiento y Argumentos Java",
            font=ctk.CTkFont(size=18, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(anchor="w", padx=25, pady=(25, 18))

        # RAM Grid
        ram_container = ctk.CTkFrame(perf_frame, fg_color="transparent")
        ram_container.pack(fill="x", padx=25, pady=(0, 18))
        ram_container.grid_columnconfigure(0, weight=0)
        ram_container.grid_columnconfigure(1, weight=1)
        ram_container.grid_columnconfigure(2, weight=0)
        ram_container.grid_columnconfigure(3, weight=1)

        # RAM Mínima
        ctk.CTkLabel(
            ram_container,
            text="RAM Mínima:",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=14, family="Segoe UI")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.entry_min_ram = ctk.CTkEntry(
            ram_container,
            placeholder_text="Ej: 2G",
            height=44,
            border_color=INPUT_BORDER,
            font=ctk.CTkFont(size=14, family="Segoe UI")
        )
        self.entry_min_ram.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        self.entry_min_ram.insert(0, self.local_config.get("min_ram", "2G"))

        # RAM Máxima
        ctk.CTkLabel(
            ram_container,
            text="RAM Máxima:",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=14, family="Segoe UI")
        ).grid(row=0, column=2, sticky="w", padx=(0, 10))

        self.entry_max_ram = ctk.CTkEntry(
            ram_container,
            placeholder_text="Ej: 4G",
            height=44,
            border_color=INPUT_BORDER,
            font=ctk.CTkFont(size=14, family="Segoe UI")
        )
        self.entry_max_ram.grid(row=0, column=3, sticky="ew")
        self.entry_max_ram.insert(0, self.local_config.get("max_ram", "4G"))

        # JVM Args
        ctk.CTkLabel(
            perf_frame,
            text="Argumentos JVM Adicionales:",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=14, family="Segoe UI")
        ).pack(anchor="w", padx=25, pady=(18, 8))

        self.entry_args = ctk.CTkEntry(
            perf_frame,
            placeholder_text="-XX:+UseG1GC -XX:MaxGCPauseMillis=200",
            height=44,
            border_color=INPUT_BORDER,
            font=ctk.CTkFont(size=14, family="Segoe UI")
        )
        self.entry_args.pack(fill="x", padx=25, pady=(0, 18))

        if self.local_config.get("jvm_args", ""):
            self.entry_args.insert(0, self.local_config.get("jvm_args", ""))

        # Toggle Aikar's Flags
        aikar_frame = ctk.CTkFrame(perf_frame, fg_color=CARD_BG_HOVER, corner_radius=10)
        aikar_frame.pack(fill="x", padx=25, pady=(0, 18))

        aikar_text_frame = ctk.CTkFrame(aikar_frame, fg_color="transparent")
        aikar_text_frame.pack(side="left", fill="x", expand=True, padx=15, pady=12)

        ctk.CTkLabel(
            aikar_text_frame,
            text="⚡ Aikar's Flags (Optimización G1GC)",
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            aikar_text_frame,
            text="Flags de garbage collector recomendadas para servidores Minecraft",
            font=ctk.CTkFont(size=12, family="Segoe UI"),
            text_color=TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkSwitch(
            aikar_frame,
            text="",
            variable=self.aikar_flags_var,
            width=46,
            button_color=ACCENT,
            button_hover_color="#a78bfa",
            progress_color=ACCENT,
        ).pack(side="right", padx=15)

        # Botón guardar
        self.btn_save = ctk.CTkButton(
            perf_frame,
            text="💾 Guardar Configuración",
            command=self.save_changes,
            height=50,
            fg_color=ACCENT,
            hover_color="#a78bfa",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            corner_radius=10
        )
        self.btn_save.pack(fill="x", padx=25, pady=(0, 25))

    def build_files_section(self, parent):
        """Sección de gestión de archivos."""
        files_frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=15)
        files_frame.pack(fill="x", pady=(0, 15))

        # Header
        ctk.CTkLabel(
            files_frame,
            text="📂 Gestión de Archivos",
            font=ctk.CTkFont(size=18, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(anchor="w", padx=25, pady=(25, 18))

        # Botón abrir carpeta
        btn_folder = ctk.CTkButton(
            files_frame,
            text="📁 Abrir Carpeta del Servidor",
            command=self.open_server_folder,
            height=50,
            fg_color=CARD_BG_HOVER,
            hover_color="#3f3f46",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            corner_radius=10
        )
        btn_folder.pack(fill="x", padx=25, pady=(0, 25))

    def build_update_section(self, parent):
        """Sección para actualizar el servidor a una versión superior."""
        update_frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=15)
        update_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            update_frame,
            text="⬆️ Actualizar Servidor",
            font=ctk.CTkFont(size=18, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(anchor="w", padx=25, pady=(25, 5))

        ctk.CTkLabel(
            update_frame,
            text="Solo se muestran versiones superiores a la actual. No se puede bajar de versión.",
            font=ctk.CTkFont(size=12, family="Segoe UI"),
            text_color=TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", padx=25, pady=(0, 18))

        # Fila: dropdown + botón
        row = ctk.CTkFrame(update_frame, fg_color="transparent")
        row.pack(fill="x", padx=25, pady=(0, 25))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)

        self.update_version_var = ctk.StringVar(value="Cargando versiones...")
        self.update_dropdown = ScrollableDropdown(
            row,
            values=["Cargando versiones..."],
            variable=self.update_version_var,
            height=44,
            max_items=10,
            state="disabled",
        )
        self.update_dropdown.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        self.btn_update = ctk.CTkButton(
            row,
            text="Actualizar",
            command=self._confirm_update,
            height=44,
            width=130,
            fg_color=ACCENT,
            hover_color="#a78bfa",
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            corner_radius=10,
            state="disabled"
        )
        self.btn_update.grid(row=0, column=1)

        # Cargar versiones en background para no bloquear la UI
        threading.Thread(target=self._load_available_versions, daemon=True).start()

    def _load_available_versions(self):
        """Obtiene versiones disponibles superiores a la actual usando el cache."""
        server_type = self.server_info.get("type", "")
        current_version = self.server_info.get("version", "")

        try:
            versions = vcs.get_versions(server_type)
            newer = self._filter_newer_versions(versions, current_version)
        except Exception:
            newer = []

        def update_ui():
            if not self.winfo_exists():
                return
            if newer:
                self.update_dropdown.configure(values=newer, state="normal")
                self.update_version_var.set(newer[0])
                self.btn_update.configure(state="normal")
            else:
                self.update_dropdown.configure(values=["No hay versiones superiores"], state="disabled")
                self.update_version_var.set("No hay versiones superiores")
                self.btn_update.configure(state="disabled")

        self.after(0, update_ui)

    def _filter_newer_versions(self, versions, current_version):
        """Filtra solo versiones estrictamente superiores a la actual usando tuple comparison."""
        def parse_ver(v):
            try:
                return tuple(int(x) for x in v.split('.'))
            except ValueError:
                return (0,)

        current_tuple = parse_ver(current_version)
        newer = [v for v in versions if parse_ver(v) > current_tuple]
        # Ordenar de más reciente a más antigua
        newer.sort(key=parse_ver, reverse=True)
        return newer

    def _confirm_update(self):
        """Pide confirmación antes de actualizar."""
        target_version = self.update_version_var.get()
        if not target_version or target_version.startswith("No hay"):
            return

        app = self._get_app_instance()
        if app and hasattr(app, 'server_manager') and app.server_manager and app.server_manager.is_running:
            messagebox.showerror(
                "Servidor en Ejecución",
                "Detén el servidor antes de actualizarlo.",
                parent=self
            )
            return

        current = self.server_info.get('version', '?')
        server_type = self.server_info.get('type', '')

        # Advertencia especial para Forge cruzando el límite 1.16 → 1.17
        if server_type == "Forge":
            def parse_ver(v):
                try:
                    return tuple(int(x) for x in v.split('.'))
                except ValueError:
                    return (0,)

            current_tuple = parse_ver(current)
            target_tuple = parse_ver(target_version)
            boundary = (1, 17)

            if current_tuple < boundary <= target_tuple:
                proceed = messagebox.askyesno(
                    "⚠️ Cambio de Arquitectura en Forge",
                    f"Estás actualizando Forge de {current} a {target_version}.\n\n"
                    "Esta actualización cruza el límite 1.16 → 1.17, donde Forge\n"
                    "cambió completamente su arquitectura de lanzamiento.\n\n"
                    "• Antes de 1.17: un único JAR (legacy)\n"
                    "• Desde 1.17: sistema de argumentos @libraries (modern)\n\n"
                    "El proceso intentará actualizarse automáticamente, pero algunos\n"
                    "mods de 1.16 serán incompatibles con 1.17+.\n\n"
                    "Si algo falla, tus archivos serán restaurados automáticamente.\n\n"
                    "¿Deseas continuar de todas formas?",
                    parent=self
                )
                if not proceed:
                    return

        if not messagebox.askyesno(
            "Confirmar Actualización",
            f"¿Actualizar de MC {current} a MC {target_version}?\n\n"
            "Se conservarán mundos, plugins y configuraciones.\n"
            "Si algo falla, tus archivos serán restaurados automáticamente.",
            parent=self
        ):
            return

        app = self._get_app_instance()
        if app:
            update_data = {
                'name': self.server_info['name'],
                'type': self.server_info['type'],
                'version': target_version,
                'reinstall_mode': 'partial',
                'original_path': self.server_path,
                'path': self.server_path
            }
            app.process_new_server_result(update_data, is_reinstall=False, is_update=True)

    def build_danger_zone(self, parent):
        """Zona peligrosa."""
        danger_frame = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=15,
            border_width=2,
            border_color=DANGER
        )
        danger_frame.pack(fill="x", pady=(0, 15))

        # Header
        header = ctk.CTkFrame(danger_frame, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(25, 18))

        ctk.CTkLabel(
            header,
            text="⚠️ Zona Peligrosa",
            font=ctk.CTkFont(size=18, weight="bold", family="Segoe UI"),
            text_color=DANGER
        ).pack(anchor="w")

        # === REINSTALACIÓN ===
        reinstall_section = ctk.CTkFrame(danger_frame, fg_color="transparent")
        reinstall_section.pack(fill="x", padx=25, pady=(0, 18))

        ctk.CTkLabel(
            reinstall_section,
            text="Reinstalación del Servidor",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(anchor="w", pady=(0, 10))

        # Radio buttons frame
        radio_frame = ctk.CTkFrame(
            reinstall_section,
            fg_color=INPUT_BORDER,
            corner_radius=10
        )
        radio_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkRadioButton(
            radio_frame,
            text="Parcial - Conservar mundos, plugins y configuraciones",
            variable=self.reinstall_mode_var,
            value="partial",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_LIGHT,
            fg_color=WARNING,
            hover_color=WARNING_HOVER
        ).pack(anchor="w", padx=15, pady=(15, 8))

        ctk.CTkRadioButton(
            radio_frame,
            text="Completa - Eliminar TODO excepto configuración de RAM/JVM",
            variable=self.reinstall_mode_var,
            value="total",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_LIGHT,
            fg_color=DANGER,
            hover_color=DANGER_HOVER
        ).pack(anchor="w", padx=15, pady=(8, 15))

        # Botón reinstalar
        ctk.CTkButton(
            reinstall_section,
            text="🔄 Reinstalar Servidor",
            command=self.reinstall_server,
            height=50,
            fg_color=WARNING,
            hover_color=WARNING_HOVER,
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            corner_radius=10
        ).pack(fill="x")

        # Separador
        ctk.CTkFrame(
            danger_frame,
            height=2,
            fg_color=INPUT_BORDER
        ).pack(fill="x", padx=25, pady=20)

        # === ELIMINACIÓN ===
        delete_section = ctk.CTkFrame(danger_frame, fg_color="transparent")
        delete_section.pack(fill="x", padx=25, pady=(0, 25))

        ctk.CTkLabel(
            delete_section,
            text="Eliminación del Servidor",
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT
        ).pack(anchor="w", pady=(0, 10))

        # Radio buttons frame
        delete_radio_frame = ctk.CTkFrame(
            delete_section,
            fg_color=INPUT_BORDER,
            corner_radius=10
        )
        delete_radio_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkRadioButton(
            delete_radio_frame,
            text="Solo quitar de la lista - Mantener archivos en el disco",
            variable=self.delete_mode_var,
            value="keep_files",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_LIGHT,
            fg_color=WARNING,
            hover_color=WARNING_HOVER
        ).pack(anchor="w", padx=15, pady=(15, 8))

        ctk.CTkRadioButton(
            delete_radio_frame,
            text="Eliminar completamente - Borrar TODOS los archivos",
            variable=self.delete_mode_var,
            value="delete_all",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_LIGHT,
            fg_color=DANGER,
            hover_color=DANGER_HOVER
        ).pack(anchor="w", padx=15, pady=(8, 15))

        # Botón eliminar
        ctk.CTkButton(
            delete_section,
            text="🗑️ Eliminar Servidor",
            command=self.delete_server,
            height=50,
            fg_color=DANGER,
            hover_color=DANGER_HOVER,
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=15, weight="bold", family="Segoe UI"),
            corner_radius=10
        ).pack(fill="x")

    def save_changes(self):
        new_config = {
            "min_ram": self.entry_min_ram.get().strip(),
            "max_ram": self.entry_max_ram.get().strip(),
            "jvm_args": self.entry_args.get().strip(),
            "use_aikar_flags": bool(self.aikar_flags_var.get())
        }

        success = save_server_config(self.server_path, new_config)

        if success:
            original_text = self.btn_save.cget("text")
            original_color = self.btn_save.cget("fg_color")
            self.btn_save.configure(text="✅ ¡Guardado!", fg_color="#22c55e")
            self.after(2000, lambda: self.btn_save.configure(text=original_text, fg_color=original_color))
        else:
            self.btn_save.configure(text="❌ Error", fg_color="#ef4444")

    def open_server_folder(self):
        path = self.server_info['path']
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def reinstall_server(self):
        """Reinstalación del servidor."""
        app = self._get_app_instance()
        if app and hasattr(app, 'server_manager') and app.server_manager and app.server_manager.is_running:
            messagebox.showerror(
                "Servidor en Ejecución",
                "Debes detener el servidor antes de reinstalarlo.",
                parent=self
            )
            return

        mode = self.reinstall_mode_var.get()

        if mode == 'partial':
            msg = (
                "¿Reinstalar conservando datos importantes?\n\n"
                "Se conservará:\n"
                "  • Mundos detectados\n"
                "  • Plugins y mods\n"
                "  • Configuraciones\n\n"
                "Se eliminará:\n"
                "  • JAR del servidor\n"
                "  • Librerías"
            )
        else:
            msg = (
                "¿REINSTALACIÓN COMPLETA?\n\n"
                "Se conservará únicamente:\n"
                "  • Configuración de RAM y JVM\n\n"
                "SE ELIMINARÁ TODO LO DEMÁS\n\n"
                "ESTA ACCIÓN NO SE PUEDE DESHACER"
            )

        if not messagebox.askyesno("Confirmar Reinstalación", msg, parent=self):
            return

        reinstall_data = {
            'name': self.server_info['name'],
            'type': self.server_info['type'],
            'version': self.server_info['version'],
            'reinstall_mode': mode,
            'original_path': self.server_path,
            'path': self.server_path
        }

        if app:
            app.process_new_server_result(reinstall_data, is_reinstall=True)

    def delete_server(self):
        """Eliminación del servidor."""
        app = self._get_app_instance()
        if app and hasattr(app, 'server_manager') and app.server_manager and app.server_manager.is_running:
            messagebox.showerror(
                "Servidor en Ejecución",
                "Debes detener el servidor antes de eliminarlo.",
                parent=self
            )
            return

        mode = self.delete_mode_var.get()
        delete_files = (mode == "delete_all")

        if delete_files:
            msg = (
                f"¿ELIMINAR COMPLETAMENTE '{self.server_info['name']}'?\n\n"
                "Borrará PERMANENTEMENTE todos los archivos\n\n"
                "ESTA ACCIÓN NO SE PUEDE DESHACER"
            )
        else:
            msg = (
                f"¿Quitar '{self.server_info['name']}' de GetMineHub?\n\n"
                "Mantendrá TODOS los archivos intactos"
            )

        if not messagebox.askyesno("Confirmar Eliminación", msg, parent=self):
            return

        success, message = delete_server(self.server_info, delete_files=delete_files)

        if success:
            messagebox.showinfo("Eliminación Exitosa", message, parent=self)
            if app:
                app.show_main_menu()
        else:
            messagebox.showerror("Error", message, parent=self)

    def _get_app_instance(self):
        """Obtiene la instancia de la app."""
        widget = self.master
        while widget:
            if hasattr(widget, 'server_manager'):
                return widget
            widget = widget.master if hasattr(widget, 'master') else None
        return None
