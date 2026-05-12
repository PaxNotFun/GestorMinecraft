import customtkinter as ctk
from collections import deque

from config.general import TEXT_LIGHT, TEXT_MUTED, ACCENT, INPUT_BG, INPUT_BORDER, CARD_BG
from utils.ansi_parser import setup_console_tags, parse_ansi_and_insert


class ConsoleWidget(ctk.CTkFrame):
    """Widget de consola interactiva moderna para servidores con salida optimizada."""

    def __init__(self, parent, on_command_send):
        super().__init__(parent, fg_color="transparent")

        self.on_command_send = on_command_send
        self.command_history = []
        self.history_index = -1
        self.common_commands = [
            "help", "kick", "ban", "pardon", "op", "deop", "whitelist", "gamemode",
            "difficulty", "say", "tell", "time", "weather", "tps", "list", "stop",
            "save-all", "save-on", "save-off", "tp", "give", "effect", "enchant",
            "xp", "kill", "gamerule"
        ]
        
        # Buffer para procesamiento por lotes
        self._pending_text = deque()
        self._batch_job = None
        self._batch_delay = 10

        self.build_console()

    def build_console(self):
        """Construye la interfaz moderna de la consola."""
        # Configurar grid
        self.grid_rowconfigure(0, weight=1)   # Console text - expandible
        self.grid_rowconfigure(1, weight=0)   # Input area - tamaño fijo
        self.grid_columnconfigure(0, weight=1)

        # Container de consola
        console_container = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=15,
            border_width=1,
            border_color=INPUT_BORDER
        )
        console_container.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        console_container.grid_rowconfigure(0, weight=1)
        console_container.grid_columnconfigure(0, weight=1)

        # Área de texto
        self.text_widget = ctk.CTkTextbox(
            console_container,
            state="disabled",
            font=("JetBrains Mono", 13),
            activate_scrollbars=True,
            border_width=0,
            corner_radius=0,
            fg_color=CARD_BG,
            text_color=TEXT_LIGHT,
            scrollbar_button_color="#2d2d3f",
            scrollbar_button_hover_color="#3d3d4f",
            wrap="none"
        )
        self.text_widget.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        setup_console_tags(self.text_widget)

        # Frame de input moderno
        input_container = ctk.CTkFrame(
            self,
            fg_color=INPUT_BG,
            corner_radius=15,
            border_width=1,
            border_color=INPUT_BORDER,
            height=70
        )
        input_container.grid(row=1, column=0, sticky="ew")
        input_container.grid_propagate(False)
        input_container.grid_columnconfigure(0, weight=1)
        input_container.grid_columnconfigure(1, weight=0)

        # Entry
        self.command_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="Escribe un comando...",
            height=45,
            corner_radius=10,
            fg_color=INPUT_BG,
            border_color=INPUT_BORDER,
            border_width=2,
            text_color=TEXT_LIGHT,
            placeholder_text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="JetBrains Mono", size=14)
        )
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(15, 10), pady=12)
        self.command_entry.bind("<Return>", self._on_command_send)
        self.command_entry.bind("<Up>", self._navigate_history)
        self.command_entry.bind("<Down>", self._navigate_history)
        self.command_entry.bind("<Tab>", self._handle_autocomplete)
        self.command_entry.bind("<FocusIn>", lambda e: self.command_entry.configure(border_color=ACCENT))
        self.command_entry.bind("<FocusOut>", lambda e: self.command_entry.configure(border_color=INPUT_BORDER))

        # Botón enviar
        self.send_button = ctk.CTkButton(
            input_container,
            text="Enviar",
            command=self._on_command_send,
            height=45,
            width=100,
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            corner_radius=10,
            fg_color=ACCENT,
            hover_color="#a78bfa"
        )
        self.send_button.grid(row=0, column=1, padx=(0, 15), pady=12)

    def _on_command_send(self, event=None):
        """Maneja el envío de comandos."""
        cmd = self.command_entry.get().strip()
        if cmd:
            self.on_command_send(cmd)
            if not self.command_history or self.command_history[-1] != cmd:
                self.command_history.append(cmd)
            self.history_index = len(self.command_history)
            self.command_entry.delete(0, 'end')

    def _navigate_history(self, event):
        """Navega por el historial de comandos."""
        if event.keysym == 'Up':
            if self.history_index > 0:
                self.history_index -= 1
                self.command_entry.delete(0, 'end')
                self.command_entry.insert(0, self.command_history[self.history_index])
        elif event.keysym == 'Down':
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_entry.delete(0, 'end')
                self.command_entry.insert(0, self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.command_entry.delete(0, 'end')
        return "break"

    def _handle_autocomplete(self, event):
        """Maneja el autocompletado de comandos."""
        current_text = self.command_entry.get()
        matches = [cmd for cmd in self.common_commands if cmd.startswith(current_text)]
        if matches:
            self.command_entry.delete(0, 'end')
            self.command_entry.insert(0, matches[0])
        return "break"

    def append_text(self, text):
        """Añade texto a la consola con procesamiento por lotes.
        Puede ser llamado desde cualquier hilo — solo toca estructuras thread-safe.
        """
        if not text:
            return

        self._pending_text.append(text)

        # after() es thread-safe en Tkinter. No tocamos _batch_job desde aquí
        # porque también lo escribe el hilo principal en _process_batch,
        # lo que provocaría una race condition. _process_batch se re-agenda
        # solo si queda texto pendiente al terminar.
        self.after(self._batch_delay, self._process_batch)

    def _process_batch(self):
        """Procesa todo el texto pendiente. Siempre corre en el hilo principal."""
        self._batch_job = None

        if not self._pending_text:
            return

        if not self.text_widget or not self.text_widget.winfo_exists():
            self._pending_text.clear()
            return

        combined_text = ''.join(self._pending_text)
        self._pending_text.clear()

        try:
            parse_ansi_and_insert(self.text_widget, combined_text)
        except Exception:
            pass

    def clear_console(self):
        """Limpia la consola."""
        if self._batch_job:
            try:
                self.after_cancel(self._batch_job)
            except Exception:
                pass
            self._batch_job = None

        self._pending_text.clear()

        if self.text_widget and self.text_widget.winfo_exists():
            self.text_widget.configure(state="normal")
            self.text_widget.delete("1.0", "end")
            self.text_widget.configure(state="disabled")

    def set_input_state(self, state):
        """Habilita/deshabilita la entrada de comandos."""
        self.command_entry.configure(state=state)
        self.send_button.configure(state=state)
