import os
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont

import config as cfg
from dates import parse_date, format_date, calc_days, is_expired, calc_duration
from storage import read_records, write_records
from validators import validate_cpf

# ── Paleta ──────────────────────────────────────────────────────────────────
BG         = "#f0ebe2"
SURFACE    = "#ffffff"
BORDER     = "#e0dbd1"
HDR_BG     = "#162820"
HDR_FG     = "#e8f4f0"
HDR_BTN    = "#1e3a2e"
ACCENT     = "#2a6049"
ACCENT_H   = "#3d7a5e"
ACCENT_L   = "#e8f5ee"
BTN_BLUE   = "#1a6b9a"
BTN_BLUE_H = "#155a82"
BTN_RED    = "#c0392b"
BTN_RED_H  = "#a93226"
BTN_GRAY   = "#64748b"
BTN_GRAY_H = "#4a5568"
SUCCESS_FG = "#166534"
DANGER_FG  = "#991b1b"
TEXT       = "#1a1a2e"
TEXT2      = "#64748b"
ROW_ALT    = "#f8f5f0"
TH_BG      = ACCENT
TH_FG      = "#ffffff"
SHADOW     = "#bfb9b1"
FLASH_OK   = "#bbf7d0"

CHIP_TOTAL_BG = SURFACE;  CHIP_TOTAL_FG = TEXT;      CHIP_TOTAL_BD = BORDER
CHIP_OPEN_BG  = "#eff6ff"; CHIP_OPEN_FG  = "#1d4ed8"; CHIP_OPEN_BD  = "#bfdbfe"
CHIP_EXP_BG   = "#fef2f2"; CHIP_EXP_FG   = "#dc2626"; CHIP_EXP_BD   = "#fecaca"

_COL_LABELS = {
    "nome":      "Nome",
    "cpf":       "CPF",
    "telefone":  "Telefone",
    "livro":     "Livro",
    "data":      "Data empréstimo",
    "devolucao": "Devolução",
    "dias":      "Dias",
    "status":    "Status",
}


def _darken(hex_color, factor=0.85):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"


def _round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
           x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
           x1,y2,   x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


# ── Widgets ──────────────────────────────────────────────────────────────────

class Tooltip:
    """Tooltip simples que aparece ao passar o mouse."""
    def __init__(self, widget, text):
        self._w    = widget
        self._text = text
        self._tip  = None
        widget.bind("<Enter>",       self._show, add=True)
        widget.bind("<Leave>",       self._hide, add=True)
        widget.bind("<ButtonPress>", self._hide, add=True)

    def _show(self, _=None):
        self._hide()
        x = self._w.winfo_rootx() + 8
        y = self._w.winfo_rooty() + self._w.winfo_height() + 6
        tw = tk.Toplevel(self._w)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self._text, bg="#1a1a2e", fg="white",
                 font=("Segoe UI", 8), padx=9, pady=5,
                 relief="flat").pack()
        self._tip = tw

    def _hide(self, _=None):
        if self._tip:
            try: self._tip.destroy()
            except Exception: pass
            self._tip = None


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None,
                 bg=ACCENT, fg="white", hover_bg=None, active_bg=None,
                 radius=8, font_spec=("Segoe UI", 10),
                 pad_x=14, pad_y=7, **kw):
        self._bg     = bg
        self._hover  = hover_bg  or _darken(bg, 0.88)
        self._active = active_bg or _darken(bg, 0.72)
        self._fg     = fg
        self._r      = radius
        self._cmd    = command
        self._text   = text
        self._cur    = bg

        fnt = tkfont.Font(family=font_spec[0], size=font_spec[1],
                          weight=font_spec[2] if len(font_spec) > 2 else "normal")
        w = fnt.measure(text) + pad_x * 2
        h = fnt.metrics("linespace") + pad_y * 2
        kw.setdefault("width",  w)
        kw.setdefault("height", h)

        super().__init__(parent, highlightthickness=0, bd=0, cursor="hand2", **kw)
        self._fnt = fnt
        self._draw(bg)

        self.bind("<Configure>",       lambda e: self._draw(self._cur))
        self.bind("<Enter>",           lambda e: self._draw(self._hover))
        self.bind("<Leave>",           lambda e: self._draw(self._bg))
        self.bind("<Button-1>",        lambda e: self._draw(self._active))
        self.bind("<ButtonRelease-1>", lambda e: self._release())

    def _draw(self, color):
        self._cur = color
        self.delete("all")
        w = max(self.winfo_width(),  1)
        h = max(self.winfo_height(), 1)
        _round_rect(self, 1, 2, w + 1, h + 1, self._r,
                    fill=_darken(color, 0.65), outline="")
        _round_rect(self, 0, 0, w, h, self._r, fill=color, outline="")
        self.create_text(w // 2, h // 2, text=self._text,
                         fill=self._fg, font=self._fnt, anchor="center")

    def _release(self):
        self._draw(self._hover)
        if self._cmd:
            self._cmd()

    def configure(self, **kw):
        changed = False
        if "text"    in kw: self._text = kw.pop("text");    changed = True
        if "command" in kw: self._cmd  = kw.pop("command")
        if "bg"      in kw:
            self._bg  = kw.pop("bg")
            self._cur = self._bg
            changed   = True
        super().configure(**kw)
        if changed:
            self._draw(self._cur)

    config = configure


class FilterTab(tk.Canvas):
    """Botão de filtro em estilo pill — ativo ou inativo."""
    def __init__(self, parent, text, command, **kw):
        fnt = tkfont.Font(family="Segoe UI", size=9)
        w   = fnt.measure(text) + 26
        kw.setdefault("width", w)
        kw.setdefault("height", 28)
        super().__init__(parent, highlightthickness=0, bd=0,
                         cursor="hand2", **kw)
        self._text     = text
        self._fnt      = fnt
        self._cmd      = command
        self._active   = False
        self._hovering = False
        self._draw()
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>",  lambda e: self._cmd())
        self.bind("<Enter>",     lambda e: self._hover(True))
        self.bind("<Leave>",     lambda e: self._hover(False))

    def _hover(self, v):
        self._hovering = v
        self._draw()

    def _draw(self):
        self.delete("all")
        w = max(self.winfo_width(),  1)
        h = max(self.winfo_height(), 1)
        if self._active:
            _round_rect(self, 0, 0, w, h, 6, fill=ACCENT, outline="")
            fg = "white"
        else:
            bg = BG if self._hovering else SURFACE
            _round_rect(self, 0, 0, w, h, 6, fill=bg, outline=BORDER, width=1)
            fg = TEXT if self._hovering else TEXT2
        self.create_text(w // 2, h // 2, text=self._text,
                         fill=fg, font=self._fnt)

    def set_active(self, v):
        self._active = v
        self._draw()


class FocusEntry(tk.Frame):
    def __init__(self, parent, textvariable=None, width=None, **kw):
        super().__init__(parent, bg=BORDER)
        ekw = dict(font=("Segoe UI", 10), bd=0, relief="flat",
                   bg=SURFACE, fg=TEXT, insertbackground=ACCENT,
                   highlightthickness=0,
                   selectbackground=ACCENT, selectforeground="white")
        if textvariable: ekw["textvariable"] = textvariable
        if width:        ekw["width"] = width
        self._e = tk.Entry(self, **ekw)
        self._e.pack(fill="both", expand=True, padx=1, pady=5)
        self._e.bind("<FocusIn>",  lambda _: self.config(bg=ACCENT))
        self._e.bind("<FocusOut>", lambda _: self.config(bg=BORDER))

    def bind(self, seq=None, func=None, add=None):
        if seq and seq.startswith("<"):
            return self._e.bind(seq, func, add)
        return super().bind(seq, func, add)

    def focus_set(self): self._e.focus_set()
    def get(self):       return self._e.get()


class RoundedCard(tk.Frame):
    _PAD = 12

    def __init__(self, parent, title="", radius=14, auto_height=False, **kw):
        super().__init__(parent, bg=BG)
        self._r          = radius
        self._auto       = auto_height
        self._th         = 40 if title else 0
        self._title_text = title
        p                = self._PAD

        self._cv = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self._cv.pack(fill="both", expand=True)

        self.inner = tk.Frame(self._cv, bg=SURFACE)
        self._iid  = self._cv.create_window(p, self._th + p, anchor="nw",
                                            window=self.inner)
        self._cv.bind("<Configure>", self._on_resize)
        if auto_height:
            self.after(120, self._fit_to_content)

    def _on_resize(self, _=None):
        w = self._cv.winfo_width()
        h = self._cv.winfo_height()
        if w < 4:
            return
        self._draw(w, h)

    def _draw(self, w, h):
        self._cv.delete("bg")
        r = self._r
        p = self._PAD
        _round_rect(self._cv, 4, 5, w, h, r, fill=SHADOW, outline="", tags="bg")
        _round_rect(self._cv, 0, 0, w - 4, h - 4, r,
                    fill=SURFACE, outline=BORDER, width=1, tags="bg")
        if self._th:
            th = self._th
            _round_rect(self._cv, 0, 0, w - 4, th + r, r,
                        fill=ACCENT_L, outline="", tags="bg")
            self._cv.create_rectangle(0, th - 1, w - 4, th + r + 1,
                                      fill=ACCENT_L, outline="", tags="bg")
            self._cv.create_line(1, th, w - 5, th, fill=BORDER, tags="bg")
            dot_x = p
            dot_y = th // 2
            self._cv.create_oval(dot_x, dot_y - 5, dot_x + 10, dot_y + 5,
                                 fill=ACCENT, outline="", tags="bg")
            self._cv.create_text(dot_x + 16, dot_y, text=self._title_text,
                                 fill=ACCENT, font=("Segoe UI", 10, "bold"),
                                 anchor="w", tags="bg")
        self._cv.tag_raise(self._iid)
        self._cv.itemconfig(self._iid,
                            width=max(1, w - 4 - p * 2),
                            height=max(1, h - 4 - self._th - p * 2))

    def _fit_to_content(self):
        self.inner.update_idletasks()
        rh = self.inner.winfo_reqheight()
        p  = self._PAD
        self._cv.configure(height=self._th + rh + p * 2 + 5)

    def rowconfigure(self, idx, **kw):    self.inner.rowconfigure(idx, **kw)
    def columnconfigure(self, idx, **kw): self.inner.columnconfigure(idx, **kw)


class StatChip(tk.Canvas):
    def __init__(self, parent, label, bg=SURFACE, fg=TEXT,
                 border=BORDER, radius=10, **kw):
        kw.setdefault("width",  110)
        kw.setdefault("height", 70)
        super().__init__(parent, highlightthickness=0, bd=0, **kw)
        self._bg     = bg
        self._fg     = fg
        self._border = border
        self._r      = radius
        self._label  = label
        self._value  = "—"
        self._draw()
        self.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.delete("all")
        w = max(self.winfo_width(),  110)
        h = max(self.winfo_height(), 70)
        _round_rect(self, 2, 3, w, h + 1, self._r, fill=SHADOW, outline="")
        _round_rect(self, 0, 0, w - 2, h - 2, self._r,
                    fill=self._bg, outline=self._border, width=1)
        self.create_text(w // 2 - 1, h // 2 - 9, text=self._value,
                         fill=self._fg, font=("Segoe UI", 20, "bold"),
                         anchor="center")
        self.create_text(w // 2 - 1, h // 2 + 14, text=self._label,
                         fill=TEXT2, font=("Segoe UI", 8), anchor="center")

    def set_value(self, val):
        self._value = str(val)
        self._draw()


# ── Aplicação ────────────────────────────────────────────────────────────────

class BibliotecaApp:
    def __init__(self, root):
        self.root          = root
        self.root.title("Biblioteca Floca")
        self.root.minsize(960, 600)
        self.records       = read_records()
        self._sort_col     = None
        self._sort_reverse = False
        self._status_filter = "todos"

        self._setup_style()
        self._build_ui()
        self._bind_shortcuts()
        self._center_window()
        self._set_icon()
        self._set_initial_focus()
        self._load_tree()
        self._notify_expired()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 1080, 680
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _set_icon(self):
        icon_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "assets", "logo_floca.ico"))
        if os.path.exists(icon_path):
            try: self.root.iconbitmap(icon_path)
            except tk.TclError: pass

    # ── Estilos ─────────────────────────────────────────────────────────────

    def _setup_style(self):
        style = ttk.Style(self.root)
        try: style.theme_use("clam")
        except tk.TclError: pass

        self.root.configure(bg=BG)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, font=("Segoe UI", 10), foreground=TEXT)
        style.configure("Treeview",
                        font=("Segoe UI", 10), rowheight=32,
                        background=SURFACE, fieldbackground=SURFACE,
                        foreground=TEXT, borderwidth=0, relief="flat")
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background=TH_BG, foreground=TH_FG,
                        relief="flat", padding=(6, 8))
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])
        style.map("Treeview.Heading",
                  background=[("active", ACCENT_H)])
        style.configure("Vertical.TScrollbar",
                        background=BORDER, troughcolor=SURFACE,
                        borderwidth=0, relief="flat", arrowsize=14)

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self._build_header()

        body = tk.Frame(self.root, bg=BG)
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        body.rowconfigure(2, weight=1)
        body.columnconfigure(0, weight=1)

        self._build_form(body)
        self._build_search(body)
        self._build_tree(body)
        self._build_statsbar(body)

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=HDR_BG)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        left = tk.Frame(hdr, bg=HDR_BG)
        left.grid(row=0, column=0, sticky="w", padx=18, pady=10)
        tk.Label(left, text="BIBLIOTECA FLOCA", bg=HDR_BG, fg=HDR_FG,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(left, text=" — Gestão de empréstimos", bg=HDR_BG, fg="#7aada0",
                 font=("Segoe UI", 9)).pack(side="left", pady=(2, 0))

        self._hdr_exp_lbl = tk.Label(hdr, text="", bg=HDR_BG, fg="#f87171",
                                     font=("Segoe UI", 9, "bold"))
        self._hdr_exp_lbl.grid(row=0, column=1, sticky="w", padx=8)

        right = tk.Frame(hdr, bg=HDR_BG)
        right.grid(row=0, column=2, sticky="e", padx=(0, 14), pady=10)

        btn_cfg = [
            ("Recarregar",    self.reload_records, "F5"),
            ("Exportar",      self._export,        None),
            ("Configurações", self._open_config,   None),
        ]
        for label, cmd, shortcut in btn_cfg:
            b = RoundedButton(right, text=label, command=cmd,
                              bg=HDR_BTN, fg=HDR_FG, hover_bg=ACCENT_H,
                              radius=6, font_spec=("Segoe UI", 9),
                              pad_x=10, pad_y=5)
            b.pack(side="left", padx=(8, 0))
            tip = f"{label} ({shortcut})" if shortcut else label
            Tooltip(b, tip)

        tk.Frame(hdr, bg=ACCENT_H, height=3).grid(
            row=1, column=0, columnspan=3, sticky="ew")

    def _build_form(self, parent):
        card = RoundedCard(parent, title="Novo Empréstimo", auto_height=True)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for col in range(4):
            card.columnconfigure(col, weight=1)
        inn = card.inner

        # Row 0: labels; Row 1: entries
        self._lbl(inn, "Nome").grid(row=0, column=0, sticky="w", padx=(0,6), pady=(0,2))
        self.nome_var   = tk.StringVar()
        self.nome_entry = FocusEntry(inn, textvariable=self.nome_var)
        self.nome_entry.grid(row=1, column=0, sticky="ew", padx=(0,12), pady=(0,10))

        self._lbl(inn, "CPF").grid(row=0, column=1, sticky="w", padx=(0,6), pady=(0,2))
        self.cpf_var = tk.StringVar()
        self.cpf_var.trace_add("write", self._mask_cpf)
        self._cpf_entry = FocusEntry(inn, textvariable=self.cpf_var)
        self._cpf_entry.grid(row=1, column=1, sticky="ew", padx=(0,12), pady=(0,10))

        self._lbl(inn, "Telefone").grid(row=0, column=2, sticky="w", padx=(0,6), pady=(0,2))
        self.telefone_var = tk.StringVar()
        self.telefone_var.trace_add("write", self._mask_telefone)
        self._tel_entry = FocusEntry(inn, textvariable=self.telefone_var)
        self._tel_entry.grid(row=1, column=2, sticky="ew", padx=(0,12), pady=(0,10))

        self._lbl(inn, "Livro").grid(row=0, column=3, sticky="w", padx=(0,6), pady=(0,2))
        self.livro_var = tk.StringVar()
        FocusEntry(inn, textvariable=self.livro_var).grid(
            row=1, column=3, sticky="ew", pady=(0,10))

        self._lbl(inn, "Data (DD/MM/AAAA)").grid(row=2, column=0, sticky="w",
                                                  padx=(0,6), pady=(0,2))
        self.data_var = tk.StringVar(value=format_date(date.today()))
        self.data_var.trace_add("write", self._mask_data)
        self._data_entry = FocusEntry(inn, textvariable=self.data_var, width=16)
        self._data_entry.grid(row=3, column=0, sticky="w", pady=(0,4))
        self._data_entry.bind("<Return>", lambda _: self.add_record())

        tk.Frame(inn, bg=BORDER, height=1).grid(
            row=4, column=0, columnspan=4, sticky="ew", pady=(4, 10))

        btns = tk.Frame(inn, bg=SURFACE)
        btns.grid(row=5, column=0, columnspan=4, sticky="w", pady=(0, 2))

        b_add = RoundedButton(btns, text="Adicionar", command=self.add_record,
                              bg=ACCENT, fg="white", hover_bg=ACCENT_H)
        b_add.pack(side="left")
        Tooltip(b_add, "Adicionar empréstimo (Enter no campo Data)")

        b_ret = RoundedButton(btns, text="Marcar devolvido",
                              command=self.mark_returned,
                              bg=BTN_BLUE, fg="white", hover_bg=BTN_BLUE_H)
        b_ret.pack(side="left", padx=(10, 0))
        Tooltip(b_ret, "Marcar registro selecionado como devolvido")

        b_del = RoundedButton(btns, text="Deletar selecionado",
                              command=self.delete_record,
                              bg=BTN_RED, fg="white", hover_bg=BTN_RED_H)
        b_del.pack(side="left", padx=(10, 0))
        Tooltip(b_del, "Deletar registro selecionado (Delete)")

    def _build_search(self, parent):
        card = RoundedCard(parent, radius=10, auto_height=True)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        card.columnconfigure(1, weight=1)
        inn = card.inner

        tk.Label(inn, text="Buscar:", bg=SURFACE, fg=TEXT2,
                 font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self.search_var    = tk.StringVar()
        self._search_entry = FocusEntry(inn, textvariable=self.search_var)
        self._search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=6)
        self._search_entry.bind("<KeyRelease>", self._on_search)

        b_clr = RoundedButton(inn, text="Limpar", command=self.clear_search,
                               bg=BTN_GRAY, fg="white", hover_bg=BTN_GRAY_H,
                               font_spec=("Segoe UI", 9), pad_x=12, pad_y=5,
                               radius=7)
        b_clr.grid(row=0, column=2, pady=6)
        Tooltip(b_clr, "Limpar busca (Esc)")

    def _build_tree(self, parent):
        card = RoundedCard(parent, title="Empréstimos")
        card.grid(row=2, column=0, sticky="nsew")
        card.rowconfigure(1, weight=1)
        card.columnconfigure(0, weight=1)
        inn = card.inner

        # ── Filtros de status ────────────────────────────────────────────
        filter_frm = tk.Frame(inn, bg=SURFACE)
        filter_frm.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self._filter_tabs: dict[str, FilterTab] = {}
        for label, key in [("Todos", "todos"), ("Em aberto", "aberto"),
                            ("Expirados", "expirado"), ("Devolvidos", "devolvido")]:
            tab = FilterTab(filter_frm, text=label,
                            command=lambda k=key: self._set_filter(k),
                            bg=SURFACE)
            tab.pack(side="left", padx=(0, 6))
            self._filter_tabs[key] = tab
        self._filter_tabs["todos"].set_active(True)

        # ── Treeview ─────────────────────────────────────────────────────
        columns = ("nome", "cpf", "telefone", "livro", "data", "devolucao", "dias", "status")
        self.tree = ttk.Treeview(inn, columns=columns, show="headings",
                                 selectmode="browse")

        col_cfg = {
            "nome":      (170, "w"),
            "cpf":       (115, "w"),
            "telefone":  (135, "w"),
            "livro":     (170, "w"),
            "data":      (120, "center"),
            "devolucao": (120, "center"),
            "dias":      ( 56, "center"),
            "status":    (110, "center"),
        }
        for col, (width, anchor) in col_cfg.items():
            self.tree.heading(col, text=_COL_LABELS[col],
                              command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=width, anchor=anchor, minwidth=40)

        vsb = ttk.Scrollbar(inn, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")

        self.tree.tag_configure("expirado",  foreground=DANGER_FG,  background="#fff5f5")
        self.tree.tag_configure("devolvido", foreground=SUCCESS_FG, background="#f0fdf4")
        self.tree.tag_configure("odd",       background=SURFACE)
        self.tree.tag_configure("even",      background=ROW_ALT)
        self.tree.tag_configure("flash",     background=FLASH_OK)

        # ── Bindings na tabela ───────────────────────────────────────────
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Delete>",   lambda e: self.delete_record())
        self.tree.bind("<Return>",   lambda e: self._edit_selected())

        # ── Estado vazio ─────────────────────────────────────────────────
        self._empty_lbl = tk.Label(
            inn, text="Nenhum empréstimo encontrado.",
            bg=SURFACE, fg=TEXT2, font=("Segoe UI", 12))

    def _build_statsbar(self, parent):
        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.chip_total  = StatChip(bar, "Total",
                                    bg=CHIP_TOTAL_BG, fg=CHIP_TOTAL_FG,
                                    border=CHIP_TOTAL_BD)
        self.chip_aberto = StatChip(bar, "Em aberto",
                                    bg=CHIP_OPEN_BG, fg=CHIP_OPEN_FG,
                                    border=CHIP_OPEN_BD)
        self.chip_expir  = StatChip(bar, "Expirados",
                                    bg=CHIP_EXP_BG, fg=CHIP_EXP_FG,
                                    border=CHIP_EXP_BD)
        for chip in (self.chip_total, self.chip_aberto, self.chip_expir):
            chip.pack(side="left", padx=(0, 12))

    # ── Atalhos de teclado ───────────────────────────────────────────────────

    def _bind_shortcuts(self):
        self.root.bind("<Control-f>", lambda e: self._focus_search())
        self.root.bind("<F5>",        lambda e: self.reload_records())
        self.root.bind("<Escape>",    lambda e: self.clear_search())

    def _focus_search(self):
        self._search_entry.focus_set()
        return "break"

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _lbl(self, parent, text):
        return tk.Label(parent, text=text, bg=SURFACE,
                        fg=TEXT2, font=("Segoe UI", 9, "bold"))

    def _set_initial_focus(self):
        def _focus():
            try: self.root.focus_force()
            except tk.TclError: pass
            self.nome_entry.focus_set()
        self.root.after(150, _focus)

    def _flash_row(self, iid):
        if not self.tree.exists(iid):
            return
        original = self.tree.item(iid, "tags")
        self.tree.item(iid, tags=("flash",))
        self.root.after(700, lambda: self._restore_tags(iid, original))

    def _restore_tags(self, iid, tags):
        if self.tree.exists(iid):
            self.tree.item(iid, tags=tags)

    # ── Filtro de status ─────────────────────────────────────────────────────

    def _set_filter(self, key):
        self._status_filter = key
        for k, tab in self._filter_tabs.items():
            tab.set_active(k == key)
        self._load_tree()

    # ── Menu de contexto ─────────────────────────────────────────────────────

    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9))
        menu.add_command(label="Editar",            command=self._edit_selected)
        menu.add_command(label="Marcar devolvido",  command=self.mark_returned)
        menu.add_separator()
        menu.add_command(label="Deletar",           command=self.delete_record)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ── Edição de registro ───────────────────────────────────────────────────

    def _edit_selected(self):
        sel = self.tree.selection()
        if sel:
            self._edit_record(int(sel[0]))

    def _edit_record(self, idx):
        if not (0 <= idx < len(self.records)):
            return
        rec = self.records[idx]

        dlg = tk.Toplevel(self.root)
        dlg.title("Editar Empréstimo")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.update_idletasks()
        pw = self.root.winfo_x() + (self.root.winfo_width()  - 460) // 2
        ph = self.root.winfo_y() + (self.root.winfo_height() - 360) // 2
        dlg.geometry(f"460x360+{pw}+{ph}")

        frm = tk.Frame(dlg, bg=BG, padx=24, pady=20)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)

        def lbl(text):
            return tk.Label(frm, text=text, bg=BG, fg=TEXT2,
                            font=("Segoe UI", 9, "bold"))

        nome_var  = tk.StringVar(value=rec["nome"])
        cpf_var   = tk.StringVar(value=rec["cpf"])
        tel_var   = tk.StringVar(value=rec.get("telefone", ""))
        livro_var = tk.StringVar(value=rec["livro"])
        data_var  = tk.StringVar(value=rec.get("data_emprestimo", ""))

        lbl("Nome").grid(row=0, column=0, sticky="w", pady=(0, 2))
        FocusEntry(frm, textvariable=nome_var).grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        lbl("CPF").grid(row=0, column=1, sticky="w", pady=(0, 2))
        FocusEntry(frm, textvariable=cpf_var).grid(
            row=1, column=1, sticky="ew", pady=(0, 10))

        lbl("Telefone").grid(row=2, column=0, sticky="w", pady=(0, 2))
        FocusEntry(frm, textvariable=tel_var).grid(
            row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        lbl("Livro").grid(row=2, column=1, sticky="w", pady=(0, 2))
        FocusEntry(frm, textvariable=livro_var).grid(
            row=3, column=1, sticky="ew", pady=(0, 10))

        lbl("Data (DD/MM/AAAA)").grid(row=4, column=0, sticky="w", pady=(0, 2))
        FocusEntry(frm, textvariable=data_var, width=14).grid(
            row=5, column=0, sticky="w", pady=(0, 10))

        def _save():
            nome     = nome_var.get().strip()
            cpf      = cpf_var.get().strip()
            telefone = tel_var.get().strip()
            livro    = livro_var.get().strip()
            data_emp = data_var.get().strip()
            if not all([nome, cpf, telefone, livro, data_emp]):
                messagebox.showerror("Erro", "Preencha todos os campos.", parent=dlg)
                return
            if not validate_cpf(cpf):
                messagebox.showerror("Erro", "CPF inválido.", parent=dlg)
                return
            try:
                data_emp = format_date(parse_date(data_emp))
            except ValueError:
                messagebox.showerror("Erro", "Data inválida. Use DD/MM/AAAA.", parent=dlg)
                return
            rec["nome"]            = nome
            rec["cpf"]             = cpf
            rec["telefone"]        = telefone
            rec["livro"]           = livro
            rec["data_emprestimo"] = data_emp
            write_records(self.records)
            dlg.destroy()
            self._load_tree()

        tk.Frame(frm, bg=BORDER, height=1).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(4, 12))
        RoundedButton(frm, text="Salvar alterações", command=_save,
                      bg=ACCENT, fg="white", hover_bg=ACCENT_H).grid(
            row=7, column=0, columnspan=2, sticky="ew")
        dlg.wait_window()

    # ── Máscaras ─────────────────────────────────────────────────────────────

    @staticmethod
    def _cursor_after_set(entry_widget, var, new_val, old_val):
        """Aplica var.set(new_val) preservando a posição lógica do cursor."""
        if new_val == old_val:
            return
        e = entry_widget._e
        try:
            pos = e.index(tk.INSERT)
            # Conta dígitos antes do cursor no valor atual
            n = sum(1 for c in old_val[:pos] if c.isdigit())
        except Exception:
            n = len(new_val)
        var.set(new_val)
        # Encontra posição em new_val com o mesmo número de dígitos antes
        count, new_pos = 0, len(new_val)
        for i, c in enumerate(new_val):
            if count == n:
                new_pos = i
                break
            if c.isdigit():
                count += 1
        try:
            e.icursor(new_pos)
        except Exception:
            pass

    def _mask_cpf(self, *_):
        old = self.cpf_var.get()
        raw = "".join(c for c in old if c.isdigit())[:11]
        if len(raw) <= 3:   m = raw
        elif len(raw) <= 6: m = f"{raw[:3]}.{raw[3:]}"
        elif len(raw) <= 9: m = f"{raw[:3]}.{raw[3:6]}.{raw[6:]}"
        else:               m = f"{raw[:3]}.{raw[3:6]}.{raw[6:9]}-{raw[9:]}"
        self._cursor_after_set(self._cpf_entry, self.cpf_var, m, old)

    def _mask_telefone(self, *_):
        old = self.telefone_var.get()
        raw = "".join(c for c in old if c.isdigit())[:11]
        if len(raw) <= 2:    m = raw
        elif len(raw) <= 7:  m = f"({raw[:2]}) {raw[2:]}"
        elif len(raw) <= 10: m = f"({raw[:2]}) {raw[2:6]}-{raw[6:]}"
        else:                m = f"({raw[:2]}) {raw[2:7]}-{raw[7:]}"
        self._cursor_after_set(self._tel_entry, self.telefone_var, m, old)

    def _mask_data(self, *_):
        old = self.data_var.get()
        raw = "".join(c for c in old if c.isdigit())[:8]
        if len(raw) <= 2:   m = raw
        elif len(raw) <= 4: m = f"{raw[:2]}/{raw[2:]}"
        else:               m = f"{raw[:2]}/{raw[2:4]}/{raw[4:]}"
        self._cursor_after_set(self._data_entry, self.data_var, m, old)

    # ── Ordenação com seta ────────────────────────────────────────────────────

    def _sort_by_column(self, col):
        for c, lbl in _COL_LABELS.items():
            self.tree.heading(c, text=lbl)

        self._sort_reverse = (not self._sort_reverse) if self._sort_col == col else False
        self._sort_col = col

        key_map = {
            "nome":      lambda r: r.get("nome",  "").lower(),
            "cpf":       lambda r: r.get("cpf",   ""),
            "telefone":  lambda r: r.get("telefone", ""),
            "livro":     lambda r: r.get("livro", "").lower(),
            "data":      lambda r: self._date_key(r.get("data_emprestimo", "")),
            "devolucao": lambda r: self._date_key(r.get("data_devolucao",  "")),
            "dias":      self._days_key,
            "status":    self._status_key,
        }
        self.records.sort(key=key_map.get(col, lambda r: ""), reverse=self._sort_reverse)

        arrow = " ↑" if not self._sort_reverse else " ↓"
        self.tree.heading(col, text=_COL_LABELS[col] + arrow)
        self._load_tree()

    def _date_key(self, s):
        try:    return parse_date(s).isoformat()
        except: return ""

    def _days_key(self, rec):
        try:
            ld = parse_date(rec["data_emprestimo"])
            if rec.get("devolvido") and rec.get("data_devolucao"):
                return calc_duration(ld, parse_date(rec["data_devolucao"]))
            return calc_days(ld)
        except: return -1

    def _status_key(self, rec):
        if rec.get("devolvido"): return "2"
        try: return "0" if is_expired(parse_date(rec["data_emprestimo"])) else "1"
        except: return "3"

    # ── Tabela ───────────────────────────────────────────────────────────────

    def _load_tree(self):
        self.tree.delete(*self.tree.get_children())
        for idx, rec in self._filtered_records():
            try:
                ld  = parse_date(rec["data_emprestimo"])
                dev = rec.get("devolvido")
                days = (calc_duration(ld, parse_date(rec["data_devolucao"]))
                        if dev and rec.get("data_devolucao") else calc_days(ld))
                status   = "Devolvido" if dev else ("Expirado" if is_expired(ld) else "OK")
                date_str = format_date(ld)
            except ValueError:
                days, status, date_str = "-", "Data inválida", rec["data_emprestimo"]

            dev_str = "-"
            if rec.get("data_devolucao") and status != "Data inválida":
                try:    dev_str = format_date(parse_date(rec["data_devolucao"]))
                except: dev_str = rec.get("data_devolucao") or "-"

            tags = ("even" if idx % 2 == 0 else "odd",)
            if status == "Expirado":   tags = ("expirado",)
            elif status == "Devolvido": tags = ("devolvido",)

            self.tree.insert("", "end", iid=str(idx),
                             values=(rec["nome"], rec["cpf"],
                                     rec.get("telefone", ""), rec["livro"],
                                     date_str, dev_str, days, status),
                             tags=tags)

        # Estado vazio
        if self.tree.get_children():
            self._empty_lbl.place_forget()
        else:
            self._empty_lbl.place(relx=0.5, rely=0.5, anchor="center")

        self._update_stats()

    def _update_stats(self):
        total = len(self.records)
        aberto = expirados = 0
        for rec in self.records:
            if rec.get("devolvido"):
                continue
            aberto += 1
            try:
                if is_expired(parse_date(rec["data_emprestimo"])):
                    expirados += 1
            except ValueError:
                pass
        self.chip_total.set_value(total)
        self.chip_aberto.set_value(aberto)
        self.chip_expir.set_value(expirados)
        if expirados > 0:
            s = "s" if expirados != 1 else ""
            self._hdr_exp_lbl.config(text=f"  [{expirados} expirado{s}]")
        else:
            self._hdr_exp_lbl.config(text="")

    # ── Notificação de expirados ──────────────────────────────────────────────

    def _notify_expired(self):
        expired = [r for r in self.records
                   if not r.get("devolvido") and self._is_expired_safe(r)]
        if not expired:
            return
        preview = []
        for rec in expired[:5]:
            try:    ds = format_date(parse_date(rec["data_emprestimo"]))
            except: ds = rec["data_emprestimo"]
            preview.append(f"  {rec['nome']} — {rec['livro']} ({ds})")
        extra = f"\n  ... e mais {len(expired) - 5}" if len(expired) > 5 else ""
        messagebox.showwarning(
            "Empréstimos expirados",
            f"{len(expired)} empréstimo(s) em atraso:\n\n" +
            "\n".join(preview) + extra)

    def _is_expired_safe(self, rec):
        try:    return is_expired(parse_date(rec["data_emprestimo"]))
        except: return False

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def add_record(self):
        nome     = self.nome_var.get().strip()
        cpf      = self.cpf_var.get().strip()
        telefone = self.telefone_var.get().strip()
        livro    = self.livro_var.get().strip()
        data_emp = self.data_var.get().strip()

        if not all([nome, cpf, telefone, livro, data_emp]):
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return
        if not validate_cpf(cpf):
            messagebox.showerror("Erro", "CPF inválido.")
            return
        try:
            data_emp = format_date(parse_date(data_emp))
        except ValueError:
            messagebox.showerror("Erro", "Data inválida. Use DD/MM/AAAA.")
            return

        # Verifica CPF duplicado com empréstimo em aberto
        digits = lambda s: "".join(c for c in s if c.isdigit())
        for r in self.records:
            if digits(r["cpf"]) == digits(cpf) and not r.get("devolvido"):
                if not messagebox.askyesno(
                    "CPF já cadastrado",
                    f"O CPF {cpf} já tem um empréstimo em aberto.\n"
                    f"Livro: {r['livro']}\n\nAdicionar mesmo assim?"):
                    return
                break

        self.records.append({"nome": nome, "cpf": cpf, "telefone": telefone,
                             "livro": livro, "data_emprestimo": data_emp,
                             "devolvido": False, "data_devolucao": ""})
        write_records(self.records)
        self._load_tree()
        new_iid = str(len(self.records) - 1)
        self.tree.see(new_iid)
        self._flash_row(new_iid)
        self._clear_inputs()

    def delete_record(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecione um registro.")
            return
        if not messagebox.askyesno("Confirmar", "Deletar este registro permanentemente?"):
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.records):
            self.records.pop(idx)
            write_records(self.records)
            self._load_tree()

    def reload_records(self):
        self.records = read_records()
        self._load_tree()

    def mark_returned(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecione um registro.")
            return
        idx = int(sel[0])
        if not (0 <= idx < len(self.records)):
            return
        rec = self.records[idx]
        if rec.get("devolvido"):
            messagebox.showinfo("Info", "Este registro já está como devolvido.")
            return
        if not messagebox.askyesno("Confirmar", "Marcar como devolvido?"):
            return
        rec["devolvido"]     = True
        rec["data_devolucao"] = format_date(date.today())
        write_records(self.records)
        self._load_tree()

    # ── Busca e filtros ───────────────────────────────────────────────────────

    def _filtered_records(self):
        q  = self.search_var.get().strip().lower()
        sf = self._status_filter
        result = list(enumerate(self.records))

        if q:
            result = [(i, r) for i, r in result
                      if q in " ".join([r.get("nome",""), r.get("cpf",""),
                                        r.get("telefone",""), r.get("livro","")]).lower()]
        if sf == "aberto":
            result = [(i, r) for i, r in result
                      if not r.get("devolvido") and not self._is_expired_safe(r)]
        elif sf == "expirado":
            result = [(i, r) for i, r in result
                      if not r.get("devolvido") and self._is_expired_safe(r)]
        elif sf == "devolvido":
            result = [(i, r) for i, r in result if r.get("devolvido")]

        return result

    def _on_search(self, _event): self._load_tree()

    def clear_search(self):
        self.search_var.set("")
        self._load_tree()

    def _clear_inputs(self):
        for v in (self.nome_var, self.cpf_var, self.telefone_var, self.livro_var):
            v.set("")
        self.data_var.set(format_date(date.today()))

    # ── Configurações ─────────────────────────────────────────────────────────

    def _open_config(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Configurações")
        dlg.resizable(False, False)
        dlg.configure(bg=BG)
        dlg.grab_set()
        frm = tk.Frame(dlg, bg=BG, padx=24, pady=24)
        frm.pack()
        tk.Label(frm, text="Dias para expirar empréstimo:", bg=BG,
                 font=("Segoe UI", 10), fg=TEXT).grid(
            row=0, column=0, sticky="w", padx=(0, 12))
        exp_var = tk.StringVar(value=str(cfg.EXP_DAYS))
        FocusEntry(frm, textvariable=exp_var, width=6).grid(row=0, column=1)

        def _save():
            try:
                d = int(exp_var.get())
                if d < 1: raise ValueError
            except (ValueError, tk.TclError):
                messagebox.showerror("Erro", "Informe um número inteiro maior que zero.",
                                     parent=dlg)
                return
            cfg.save_settings(d)
            dlg.destroy()
            self._load_tree()

        RoundedButton(frm, text="Salvar", command=_save,
                      bg=ACCENT, fg="white", hover_bg=ACCENT_H).grid(
            row=1, column=0, columnspan=2, pady=(16, 0), sticky="ew")
        dlg.wait_window()

    # ── Exportar ──────────────────────────────────────────────────────────────

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("CSV", "*.csv")],
            initialfile="emprestimos_relatorio", parent=self.root)
        if not path:
            return
        records = self._filtered_records()
        if path.lower().endswith(".csv"):
            import csv as _csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = _csv.writer(f)
                w.writerow(["Nome","CPF","Telefone","Livro",
                             "Data Empréstimo","Devolução","Dias","Status"])
                for _, rec in records:
                    st, dy = self._compute_status_days(rec)
                    w.writerow([rec.get("nome",""), rec.get("cpf",""),
                                 rec.get("telefone",""), rec.get("livro",""),
                                 rec.get("data_emprestimo",""),
                                 rec.get("data_devolucao","") or "-", dy, st])
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write("RELATÓRIO DE EMPRÉSTIMOS\n")
                f.write(f"Gerado em: {format_date(date.today())}\n")
                f.write("=" * 58 + "\n\n")
                for _, rec in records:
                    st, dy = self._compute_status_days(rec)
                    f.write(f"Nome:    {rec.get('nome','')}\n")
                    f.write(f"CPF:     {rec.get('cpf','')}\n")
                    f.write(f"Tel:     {rec.get('telefone','')}\n")
                    f.write(f"Livro:   {rec.get('livro','')}\n")
                    f.write(f"Emprest: {rec.get('data_emprestimo','')}\n")
                    f.write(f"Devol:   {rec.get('data_devolucao','') or '-'}\n")
                    f.write(f"Dias:    {dy}  |  Status: {st}\n")
                    f.write("-" * 40 + "\n")
        messagebox.showinfo("Exportado", f"Arquivo salvo:\n{path}")

    def _compute_status_days(self, rec):
        try:
            ld = parse_date(rec["data_emprestimo"])
            if rec.get("devolvido") and rec.get("data_devolucao"):
                return "Devolvido", calc_duration(ld, parse_date(rec["data_devolucao"]))
            return ("Expirado" if is_expired(ld) else "OK"), calc_days(ld)
        except ValueError:
            return "Data inválida", "-"
