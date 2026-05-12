import re
import threading
from pathlib import Path

import customtkinter as ctk

from config.general import TEXT_LIGHT, TEXT_MUTED, CARD_BG, CARD_BG_HOVER, INPUT_BORDER, DANGER, WARNING, SUCCESS
from utils.helpers import fix_scroll_linux


class PlayersView(ctk.CTkFrame):
    """Vista de jugadores conectados en tiempo real."""
    
    def __init__(self, parent, server_info, app_instance):
        super().__init__(parent, fg_color="transparent")
        self.server_info = server_info
        self.app = app_instance
        self.server_path = Path(server_info['path'])
        self.players_data = []
        self.update_job = None
        self.is_monitoring = False
        self.build_view()
        self.start_monitoring()
    
    def build_view(self):
        """Construye la interfaz de la vista de jugadores."""
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=15, height=90)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_propagate(False)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(
            header_content,
            text="Jugadores Online",
            font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(side="left", fill="x", expand=True)
        
        self.player_count_label = ctk.CTkLabel(
            header_content,
            text="0 jugadores",
            font=ctk.CTkFont(size=18, family="Segoe UI"),
            text_color=TEXT_MUTED
        )
        self.player_count_label.pack(side="right", padx=(15, 0))
        
        refresh_btn = ctk.CTkButton(
            header_content,
            text="🔄 Actualizar",
            width=130,
            height=55,
            command=self.force_refresh,
            fg_color=CARD_BG_HOVER,
            hover_color="#3f3f46",
            font=ctk.CTkFont(size=14, weight="bold", family="Segoe UI"),
            corner_radius=12
        )
        refresh_btn.pack(side="right")
        
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)
        
        self.players_scroll = None
        self.empty_state_frame = None
        self.show_empty_state()
    
    def show_empty_state(self):
        if self.players_scroll:
            self.players_scroll.grid_forget()
            self.players_scroll.destroy()
            self.players_scroll = None
        
        if self.empty_state_frame:
            self.empty_state_frame.grid_forget()
            self.empty_state_frame.destroy()
        
        self.empty_state_frame = ctk.CTkFrame(
            self.content_container,
            fg_color=CARD_BG,
            corner_radius=15,
            border_width=1,
            border_color=INPUT_BORDER
        )
        self.empty_state_frame.grid(row=0, column=0, sticky="nsew", padx=10)
        self.empty_state_frame.grid_rowconfigure(0, weight=1)
        self.empty_state_frame.grid_columnconfigure(0, weight=1)
        
        content = ctk.CTkFrame(self.empty_state_frame, fg_color="transparent")
        content.grid(row=0, column=0)
        
        ctk.CTkLabel(content, text="👥", font=ctk.CTkFont(size=80), text_color=TEXT_MUTED).pack(pady=(0, 20))
        ctk.CTkLabel(content, text="No hay jugadores conectados",
                     font=ctk.CTkFont(size=22, weight="bold", family="Segoe UI"), text_color=TEXT_LIGHT).pack(pady=(0, 10))
        ctk.CTkLabel(content, text="Cuando alguien se conecte, aparecerá aquí",
                     font=ctk.CTkFont(size=15, family="Segoe UI"), text_color=TEXT_MUTED).pack()
    
    def show_players_list(self):
        if self.empty_state_frame:
            self.empty_state_frame.grid_forget()
            self.empty_state_frame.destroy()
            self.empty_state_frame = None
        
        if not self.players_scroll:
            self.players_scroll = ctk.CTkScrollableFrame(
                self.content_container,
                fg_color="transparent",
                scrollbar_button_color="#2d2d3f",
                scrollbar_button_hover_color="#3d3d4f"
            )
            self.players_scroll.grid(row=0, column=0, sticky="nsew")
            fix_scroll_linux(self.players_scroll)
    
    def start_monitoring(self):
        self.is_monitoring = True
        self.monitor_players()
    
    def stop_monitoring(self):
        self.is_monitoring = False
        if self.update_job:
            try:
                self.after_cancel(self.update_job)
            except:
                pass
    
    def monitor_players(self):
        if not self.is_monitoring:
            return
        manager = getattr(self.app, 'server_manager', None)
        if manager and manager.is_running:
            threading.Thread(target=self.fetch_players, daemon=True).start()
        self.update_job = self.after(5000, self.monitor_players)
    
    def fetch_players(self):
        try:
            manager = getattr(self.app, 'server_manager', None)
            if not manager or not manager.is_running:
                self.after(0, self.update_players_ui, [])
                return
            players = self.parse_players_from_logs()
            self.after(0, self.update_players_ui, players)
        except Exception:
            self.after(0, self.update_players_ui, [])

    @staticmethod
    def strip_minecraft_colors(text):
        """Elimina códigos §X de Minecraft y secuencias ANSI."""
        text = re.sub(r'§[0-9a-fk-or]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        return text.strip()

    def parse_players_from_logs(self):
        """Parsea jugadores desde los logs del servidor."""
        players = []
        try:
            manager = getattr(self.app, 'server_manager', None)
            if not manager:
                return players

            history = manager.get_history()
            if not history:
                return players

            clean_history = self.strip_minecraft_colors(history)
            lines = clean_history.split('\n')

            seen = {}  # nombre → estado ('online' | 'offline')

            for line in reversed(lines[-500:]):
                join_match = re.search(r'([A-Za-z0-9_]{1,16})\s+joined the game', line, re.IGNORECASE)
                leave_match = re.search(r'([A-Za-z0-9_]{1,16})\s+left the game', line, re.IGNORECASE)

                if join_match:
                    name = join_match.group(1)
                    if name not in seen:
                        seen[name] = 'online'
                elif leave_match:
                    name = leave_match.group(1)
                    if name not in seen:
                        seen[name] = 'offline'

            for player_name, status in seen.items():
                if status == 'online':
                    players.append({
                        'name': player_name,
                        'ping': self.find_ping(player_name, lines),
                        'gamemode': self.find_gamemode(player_name, lines),
                    })

        except Exception:
            pass

        return players

    def find_ping(self, player_name, log_lines):
        """
        Busca el ping real del jugador en los logs.
        Minecraft Paper/Spigot imprime líneas como:
          'PaxNotFun has a latency of 3ms'
        o al hacer login:
          'PaxNotFun[/127.0.0.1:PORT] logged in ...'  → localhost = <5ms
        """
        # Buscar latencia explícita (Paper/Spigot)
        for line in reversed(log_lines[-300:]):
            if player_name not in line:
                continue
            lat = re.search(
                r'latency\s+of\s+(\d+)\s*ms', line, re.IGNORECASE
            )
            if lat:
                return f"~{lat.group(1)}ms"
            # Formato alternativo: "ping: 4ms" o "4ms ping"
            ping = re.search(
                r'\bping[:\s]+(\d+)\s*ms|\b(\d+)\s*ms\s+ping', line, re.IGNORECASE
            )
            if ping:
                val = ping.group(1) or ping.group(2)
                return f"~{val}ms"

        # Si el jugador se conectó desde localhost, el ping es mínimo
        for line in reversed(log_lines[-300:]):
            if player_name not in line:
                continue
            if re.search(r'logged in', line, re.IGNORECASE):
                if re.search(r'/127\.0\.0\.1|/0:0:0:0:0:0:0:1|localhost', line, re.IGNORECASE):
                    return "~1ms"
                # Intentar extraer IP y marcar como remoto desconocido
                return "N/D"

        return "N/D"

    def find_gamemode(self, player_name, log_lines):
        """Busca el modo de juego del jugador en los logs."""
        gamemode_names = {
            '0': 'Survival', 'survival': 'Survival',
            '1': 'Creative', 'creative': 'Creative',
            '2': 'Adventure', 'adventure': 'Adventure',
            '3': 'Spectator', 'spectator': 'Spectator',
        }
        for line in reversed(log_lines[-300:]):
            gm = re.search(
                r"(?:set\s+)?" + re.escape(player_name) + r"'?s?\s+game\s*mode\s+(?:to\s+)?(\w+)",
                line, re.IGNORECASE
            )
            if gm:
                mode = gm.group(1).lower()
                return gamemode_names.get(mode, mode.capitalize())
        return "Survival"

    def update_players_ui(self, players):
        self.players_data = players
        count = len(players)
        self.player_count_label.configure(
            text=f"{count} jugador{'es' if count != 1 else ''}"
        )
        if not players:
            self.show_empty_state()
            return
        self.show_players_list()
        for widget in self.players_scroll.winfo_children():
            widget.destroy()
        for player in players:
            self.create_player_card(self.players_scroll, player)
    
    def create_player_card(self, parent, player):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color=INPUT_BORDER)
        card.pack(fill="x", pady=(0, 12), padx=10)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=25)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=0)
        
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=(0, 20))
        
        name_container = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_container.pack(anchor="w", pady=(0, 12))
        
        ctk.CTkLabel(
            name_container,
            text=f"👤 {player['name']}",
            font=ctk.CTkFont(size=20, weight="bold", family="Segoe UI"),
            text_color=TEXT_LIGHT,
            anchor="w"
        ).pack(side="left", padx=(0, 15))
        
        status_badge = ctk.CTkFrame(name_container, fg_color=SUCCESS, corner_radius=8, height=26)
        status_badge.pack(side="left")
        ctk.CTkLabel(status_badge, text="● Conectado",
                     font=ctk.CTkFont(size=12, weight="bold", family="Segoe UI"),
                     text_color="#ffffff").pack(padx=12, pady=3)
        
        details_grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        details_grid.pack(fill="x")
        details_grid.grid_columnconfigure(0, weight=0)
        details_grid.grid_columnconfigure(1, weight=0)
        
        details = [
            ("📶 Ping:", player.get('ping', 'N/D')),
            ("🎮 Modo:", player.get('gamemode', 'Survival')),
        ]
        
        for i, (label, value) in enumerate(details):
            detail_container = ctk.CTkFrame(details_grid, fg_color="transparent")
            detail_container.grid(row=0, column=i, sticky="w", padx=(0, 25))
            ctk.CTkLabel(detail_container, text=label,
                         font=ctk.CTkFont(size=12, family="Segoe UI"), text_color=TEXT_MUTED).pack(side="left", padx=(0, 5))
            ctk.CTkLabel(detail_container, text=value,
                         font=ctk.CTkFont(size=12, weight="bold", family="Segoe UI"), text_color=TEXT_LIGHT).pack(side="left")
        
        actions_frame = ctk.CTkFrame(content, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e")
        
        ctk.CTkButton(actions_frame, text="💬", width=55, height=55,
                      command=lambda p=player: self.send_message_to_player(p['name']),
                      fg_color=CARD_BG_HOVER, hover_color="#3f3f46",
                      text_color=TEXT_LIGHT, font=ctk.CTkFont(size=20), corner_radius=12
                      ).grid(row=0, column=0, padx=(0, 8))
        
        ctk.CTkButton(actions_frame, text="⚠️", width=55, height=55,
                      command=lambda p=player: self.kick_player(p['name']),
                      fg_color=WARNING, hover_color="#fbbf24",
                      text_color=TEXT_LIGHT, font=ctk.CTkFont(size=20), corner_radius=12
                      ).grid(row=0, column=1, padx=(0, 8))
        
        ctk.CTkButton(actions_frame, text="🚫", width=55, height=55,
                      command=lambda p=player: self.ban_player(p['name']),
                      fg_color=DANGER, hover_color="#f87171",
                      text_color=TEXT_LIGHT, font=ctk.CTkFont(size=20), corner_radius=12
                      ).grid(row=0, column=2)
    
    def send_message_to_player(self, player_name):
        dialog = ctk.CTkInputDialog(text=f"Mensaje para {player_name}:", title="Enviar Mensaje")
        message = dialog.get_input()
        if message:
            manager = getattr(self.app, 'server_manager', None)
            if manager and manager.is_running:
                manager.send_command(f"tell {player_name} {message}")
                self.show_notification(f"Mensaje enviado a {player_name}")
    
    def kick_player(self, player_name):
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Kick", f"¿Expulsar a {player_name} del servidor?", parent=self):
            manager = getattr(self.app, 'server_manager', None)
            if manager and manager.is_running:
                manager.send_command(f"kick {player_name}")
                self.show_notification(f"{player_name} ha sido expulsado")
                self.force_refresh()
    
    def ban_player(self, player_name):
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Ban",
                               f"¿Banear permanentemente a {player_name}?\n\n"
                               "Esta acción impedirá que el jugador vuelva a conectarse.", parent=self):
            manager = getattr(self.app, 'server_manager', None)
            if manager and manager.is_running:
                manager.send_command(f"ban {player_name}")
                self.show_notification(f"{player_name} ha sido baneado")
                self.force_refresh()
    
    def force_refresh(self):
        threading.Thread(target=self.fetch_players, daemon=True).start()
    
    def show_notification(self, message):
        app = self._get_app_instance()
        if app and hasattr(app, 'show_notification'):
            app.show_notification(message)
    
    def _get_app_instance(self):
        widget = self.master
        while widget:
            if hasattr(widget, 'server_manager'):
                return widget
            widget = widget.master if hasattr(widget, 'master') else None
        return None
    
    def destroy(self):
        self.stop_monitoring()
        super().destroy()
