import customtkinter as ctk
from tkinter import ttk
import tkinter as tk

from config.general import CARD_BG, ACCENT, TEXT_LIGHT, TEXT_MUTED, INPUT_BG, INPUT_BORDER


class ScrollableDropdown(ctk.CTkFrame):
    """
    Dropdown con scroll compatible con Linux, Windows y macOS.
    Reemplaza CTkOptionMenu cuando la lista es larga.
    """

    def __init__(self, parent, values=None, command=None, variable=None,
                 height=48, max_items=10, state="normal", **kwargs):
        super().__init__(parent, fg_color="transparent", height=height)
        self.pack_propagate(False)

        self._values = values or []
        self._command = command
        self._variable = variable
        self._state = state
        self._max_items = max_items
        self._item_height = 34
        self._popup = None

        # Entry de solo lectura que muestra el valor
        self._entry = ctk.CTkEntry(
            self,
            height=height,
            fg_color=INPUT_BG,
            border_color=INPUT_BORDER,
            border_width=2,
            corner_radius=12,
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color=TEXT_LIGHT,
            state="readonly",
        )
        self._entry.pack(fill="both", expand=True)

        self._arrow = ctk.CTkLabel(
            self._entry,
            text="▾",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
            fg_color="transparent",
            width=30,
        )
        self._arrow.place(relx=1.0, rely=0.5, anchor="e", x=-10)

        for w in (self._entry, self._arrow):
            w.bind("<Button-1>", self._toggle_popup)

        if self._variable:
            self._set_display(self._variable.get())
            self._variable.trace_add("write", self._on_var_write)

    # ── API pública ──────────────────────────────────────────────────────────

    def configure(self, **kwargs):
        if "values" in kwargs:
            self._values = kwargs.pop("values")
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._arrow.configure(
                text_color=TEXT_MUTED if self._state == "normal" else "#555566"
            )
        if "variable" in kwargs:
            self._variable = kwargs.pop("variable")
        if kwargs:
            super().configure(**kwargs)

    def get(self):
        raw = self._entry.cget("textvariable")
        val = self._entry.get() if not raw else raw
        return val

    def set(self, value):
        self._set_display(value)

    # ── Internos ─────────────────────────────────────────────────────────────

    def _set_display(self, value):
        self._entry.configure(state="normal")
        self._entry.delete(0, "end")
        self._entry.insert(0, value)
        self._entry.configure(state="readonly")

    def _on_var_write(self, *_):
        if self._variable:
            self._set_display(self._variable.get())

    def _toggle_popup(self, event=None):
        if self._state != "normal":
            return
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        if not self._values:
            return

        self.update_idletasks()
        x = self._entry.winfo_rootx()
        y = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
        width = self._entry.winfo_width()

        visible = min(len(self._values), self._max_items)
        popup_h = visible * self._item_height + 6

        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.configure(bg="#2d2d3f")  # color del borde
        self._popup.geometry(f"{width}x{popup_h}+{x}+{y}")
        self._popup.lift()
        self._popup.focus_set()
        self._popup.bind("<FocusOut>", self._on_focus_out)
        self._popup.bind("<Escape>", lambda e: self._close_popup())

        # Inner frame con padding de 1px = borde visual
        inner = tk.Frame(self._popup, bg=CARD_BG, bd=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Canvas + Scrollbar manual (funciona igual en todos los SO)
        canvas = tk.Canvas(inner, bg=CARD_BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(inner, orient="vertical", command=canvas.yview)

        # Solo mostrar scrollbar si hay más ítems que los visibles
        if len(self._values) > self._max_items:
            scrollbar.pack(side="right", fill="y")

        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)

        items_frame = tk.Frame(canvas, bg=CARD_BG)
        canvas_window = canvas.create_window((0, 0), window=items_frame, anchor="nw")

        current = self._variable.get() if self._variable else ""

        for value in self._values:
            is_selected = value == current
            bg = ACCENT if is_selected else CARD_BG
            fg = "#ffffff" if is_selected else TEXT_LIGHT

            btn = tk.Label(
                items_frame,
                text=f"  {value}",
                anchor="w",
                bg=bg,
                fg=fg,
                font=("Segoe UI", 11, "bold" if is_selected else "normal"),
                height=1,
                cursor="hand2",
            )
            btn.pack(fill="x", padx=3, pady=1, ipady=4)

            # Hover
            btn.bind("<Enter>", lambda e, b=btn, s=is_selected: b.configure(
                bg=ACCENT if s else "#23233a"
            ))
            btn.bind("<Leave>", lambda e, b=btn, orig_bg=bg: b.configure(bg=orig_bg))
            btn.bind("<Button-1>", lambda e, v=value: self._select(v))

        # Actualizar scroll region cuando el frame cambie de tamaño
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(canvas_window, width=event.width if event.width > 0
                                  else canvas.winfo_width())

        items_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(
            canvas_window, width=e.width
        ))

        # Scroll con rueda del ratón — compatible Linux/Win/Mac
        def _on_mousewheel(event):
            # Linux: Button-4 = arriba, Button-5 = abajo
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                # Windows / macOS: event.delta
                canvas.yview_scroll(-1 * (event.delta // 120), "units")

        for widget in (canvas, items_frame, self._popup):
            widget.bind("<MouseWheel>", _on_mousewheel)   # Win/Mac
            widget.bind("<Button-4>", _on_mousewheel)      # Linux scroll up
            widget.bind("<Button-5>", _on_mousewheel)      # Linux scroll down

        # Scroll en los labels individuales también
        def _bind_scroll(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_scroll(child)

        items_frame.after(10, lambda: _bind_scroll(items_frame))

    def _on_focus_out(self, event):
        # Pequeño delay para no cerrar cuando se hace click en un ítem
        self._popup.after(100, self._close_if_no_focus)

    def _close_if_no_focus(self):
        if not self._popup or not self._popup.winfo_exists():
            return
        try:
            focused = self._popup.focus_get()
            if focused is None or str(focused) == str(self._popup) or "." not in str(focused):
                self._close_popup()
        except Exception:
            self._close_popup()

    def _select(self, value):
        self._close_popup()
        if self._variable:
            self._variable.set(value)
        self._set_display(value)
        if self._command:
            self._command(value)

    def _close_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None
