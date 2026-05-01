import os
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import config as cfg
from dates import parse_date, format_date, calc_days, is_expired, calc_duration
from storage import read_records, write_records
from validators import validate_cpf

# ── Paleta ──────────────────────────────────────────────────────────────────
BG         = "#f2ede5"   # fundo geral (creme quente)
SURFACE    = "#ffffff"   # fundo de cards/tabela
BORDER     = "#ddd8cf"   # borda suave
HDR_BG     = "#1a3028"   # cabeçalho (verde escuro)
HDR_FG     = "#e8f4f0"   # texto do cabeçalho
HDR_BTN    = "#274d3a"   # botões do cabeçalho (hover)
ACCENT     = "#2a6049"   # verde principal
ACCENT_H   = "#3d7a5e"   # hover do verde
BTN_BLUE   = "#1a6b9a"   # azul (marcar devolvido)
BTN_BLUE_H = "#155a82"
BTN_RED    = "#c0392b"   # vermelho (deletar)
BTN_RED_H  = "#a93226"
BTN_GRAY   = "#64748b"   # cinza (ações secundárias)
BTN_GRAY_H = "#4a5568"
SUCCESS_FG = "#1a7a4a"   # texto devolvido
DANGER_FG  = "#b52020"   # texto expirado
TEXT       = "#1a1a2e"   # texto principal
TEXT2      = "#6b7280"   # texto secundário
ROW_ALT    = "#f8f4ee"   # linhas alternadas
TH_BG      = "#e2ddd5"   # fundo dos títulos da tabela
TH_FG      = "#1a3028"   # texto dos títulos


class BibliotecaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Biblioteca Floca")
        self.root.minsize(960, 580)
        self.records = read_records()
        self._sort_col = None
        self._sort_reverse = False

        self._setup_style()
        self._build_ui()
        self._set_icon()
        self._set_initial_focus()
        self._load_tree()
        self._notify_expired()

    def _set_icon(self):
        icon_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logo_floca.ico")
        )
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError:
                pass

    # ── Estilos ─────────────────────────────────────────────────────────────

    def _setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.root.configure(bg=BG)

        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, font=("Segoe UI", 10), foreground=TEXT)
        style.configure("TEntry", font=("Segoe UI", 10), padding=(4, 3),
                        fieldbackground=SURFACE, foreground=TEXT)

        style.configure("TLabelframe", background=SURFACE, relief="flat",
                        borderwidth=1, bordercolor=BORDER)
        style.configure("TLabelframe.Label", background=BG, foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"), padding=(2, 0))

        # Botões coloridos
        _btn = {"font": ("Segoe UI", 10), "padding": (12, 6),
                "relief": "flat", "borderwidth": 0, "focusthickness": 0}

        style.configure("Primary.TButton", background=ACCENT, foreground="white", **_btn)
        style.map("Primary.TButton",
                  background=[("active", ACCENT_H), ("pressed", "#1b4332")])

        style.configure("Return.TButton", background=BTN_BLUE, foreground="white", **_btn)
        style.map("Return.TButton",
                  background=[("active", BTN_BLUE_H), ("pressed", "#104060")])

        style.configure("Danger.TButton", background=BTN_RED, foreground="white", **_btn)
        style.map("Danger.TButton",
                  background=[("active", BTN_RED_H), ("pressed", "#7b1515")])

        style.configure("Muted.TButton", background=BTN_GRAY, foreground="white",
                        **{**_btn, "font": ("Segoe UI", 9), "padding": (8, 4)})
        style.map("Muted.TButton",
                  background=[("active", BTN_GRAY_H)])

        style.configure("Header.TButton", background=HDR_BG, foreground=HDR_FG,
                        font=("Segoe UI", 9), padding=(10, 5),
                        relief="flat", borderwidth=0, focusthickness=0)
        style.map("Header.TButton",
                  background=[("active", HDR_BTN)])

        # Treeview
        style.configure("Treeview",
                        font=("Segoe UI", 10), rowheight=28,
                        background=SURFACE, fieldbackground=SURFACE,
                        foreground=TEXT, borderwidth=0, relief="flat")
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background=TH_BG, foreground=TH_FG,
                        relief="flat", padding=(6, 6))
        style.map("Treeview",
                  background=[("selected", "#cce3d8")],
                  foreground=[("selected", TEXT)])
        style.map("Treeview.Heading",
                  background=[("active", "#d4cfc7")])

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        self._build_header()

        body = ttk.Frame(self.root, padding=(14, 10))
        body.grid(row=1, column=0, sticky="nsew")
        body.rowconfigure(2, weight=1)
        body.columnconfigure(0, weight=1)

        self._build_form(body)
        self._build_search(body)
        self._build_tree(body)
        self._build_statsbar(body)

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=HDR_BG)
        hdr.grid(row=0, column=0, sticky="ew")

        tk.Label(
            hdr, text="BIBLIOTECA FLOCA",
            bg=HDR_BG, fg=HDR_FG,
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left", padx=18, pady=12)

        for label, cmd in [
            ("Configuracoes", self._open_config),
            ("Exportar",      self._export),
            ("Recarregar",    self.reload_records),
        ]:
            ttk.Button(hdr, text=label, style="Header.TButton", command=cmd).pack(
                side="right", padx=(0, 10), pady=10
            )

    def _build_form(self, parent):
        card = self._card(parent, "Novo Emprestimo")
        card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        card.columnconfigure(1, weight=1)
        card.columnconfigure(3, weight=1)

        self._lbl(card, "Nome:").grid(row=0, column=0, sticky="w", padx=(8, 4), pady=6)
        self.nome_var = tk.StringVar()
        self.nome_entry = ttk.Entry(card, textvariable=self.nome_var)
        self.nome_entry.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=6)

        self._lbl(card, "CPF:").grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.cpf_var = tk.StringVar()
        self.cpf_var.trace_add("write", self._mask_cpf)
        ttk.Entry(card, textvariable=self.cpf_var).grid(row=0, column=3, sticky="ew", padx=(0, 8), pady=6)

        self._lbl(card, "Telefone:").grid(row=1, column=0, sticky="w", padx=(8, 4), pady=6)
        self.telefone_var = tk.StringVar()
        self.telefone_var.trace_add("write", self._mask_telefone)
        ttk.Entry(card, textvariable=self.telefone_var).grid(row=1, column=1, sticky="ew", padx=(0, 14), pady=6)

        self._lbl(card, "Livro:").grid(row=1, column=2, sticky="w", padx=(0, 4))
        self.livro_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.livro_var).grid(row=1, column=3, sticky="ew", padx=(0, 8), pady=6)

        self._lbl(card, "Data (DD/MM/AAAA):").grid(row=2, column=0, sticky="w", padx=(8, 4), pady=6)
        self.data_var = tk.StringVar()
        self.data_var.trace_add("write", self._mask_data)
        data_entry = ttk.Entry(card, textvariable=self.data_var, width=16)
        data_entry.grid(row=2, column=1, sticky="w", padx=(0, 14), pady=6)
        data_entry.bind("<Return>", lambda _: self.add_record())

        sep = tk.Frame(card, bg=BORDER, height=1)
        sep.grid(row=3, column=0, columnspan=4, sticky="ew", padx=8, pady=(4, 0))

        btns = tk.Frame(card, bg=SURFACE)
        btns.grid(row=4, column=0, columnspan=4, sticky="w", padx=8, pady=10)

        ttk.Button(btns, text="Adicionar",          style="Primary.TButton", command=self.add_record).pack(side="left")
        ttk.Button(btns, text="Marcar devolvido",   style="Return.TButton",  command=self.mark_returned).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Deletar selecionado",style="Danger.TButton",  command=self.delete_record).pack(side="left", padx=(8, 0))

    def _build_search(self, parent):
        frm = tk.Frame(parent, bg=BG)
        frm.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        frm.columnconfigure(1, weight=1)

        self._lbl(frm, "Buscar:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(frm, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        search_entry.bind("<KeyRelease>", self._on_search)
        ttk.Button(frm, text="Limpar", style="Muted.TButton", command=self.clear_search).grid(row=0, column=2)

    def _build_tree(self, parent):
        card = self._card(parent, "Emprestimos")
        card.grid(row=2, column=0, sticky="nsew")
        card.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)

        columns = ("nome", "cpf", "telefone", "livro", "data", "devolucao", "dias", "status")
        self.tree = ttk.Treeview(card, columns=columns, show="headings", selectmode="browse")

        col_cfg = {
            "nome":      ("Nome",            170, "w"),
            "cpf":       ("CPF",             115, "w"),
            "telefone":  ("Telefone",        135, "w"),
            "livro":     ("Livro",           170, "w"),
            "data":      ("Data emprestimo", 120, "center"),
            "devolucao": ("Devolucao",       120, "center"),
            "dias":      ("Dias",             56, "center"),
            "status":    ("Status",          100, "center"),
        }
        for col, (label, width, anchor) in col_cfg.items():
            self.tree.heading(col, text=label, command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=width, anchor=anchor, minwidth=40)

        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("expirado", foreground=DANGER_FG)
        self.tree.tag_configure("devolvido", foreground=SUCCESS_FG)
        self.tree.tag_configure("odd",  background=SURFACE)
        self.tree.tag_configure("even", background=ROW_ALT)

    def _build_statsbar(self, parent):
        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=3, column=0, sticky="ew", pady=(6, 0))

        self.stats_total  = self._stat_label(bar, "Total",      TEXT2)
        self.stats_aberto = self._stat_label(bar, "Em aberto",  TEXT2)
        self.stats_expir  = self._stat_label(bar, "Expirados",  DANGER_FG)

        for w in (self.stats_total, self.stats_aberto, self.stats_expir):
            w.pack(side="left", padx=(0, 24))

    def _stat_label(self, parent, prefix, color):
        frm = tk.Frame(parent, bg=BG)
        tk.Label(frm, text=prefix + ":", bg=BG, fg=TEXT2,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 3))
        lbl = tk.Label(frm, text="—", bg=BG, fg=color, font=("Segoe UI", 9, "bold"))
        lbl.pack(side="left")
        frm._value_label = lbl
        return frm

    # ── Helpers de layout ────────────────────────────────────────────────────

    def _card(self, parent, title):
        outer = tk.Frame(parent, bg=BORDER, bd=0)
        inner = ttk.LabelFrame(outer, text=title, padding=(8, 6),
                                style="TLabelframe")
        inner.configure(style="TLabelframe")
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        inner._outer = outer
        return inner

    def _lbl(self, parent, text):
        return tk.Label(parent, text=text, bg=SURFACE,
                        fg=TEXT2, font=("Segoe UI", 9))

    def _set_initial_focus(self):
        def _focus():
            try:
                self.root.focus_force()
            except tk.TclError:
                pass
            self.nome_entry.focus_set()
        self.root.after(150, _focus)

    # ── Máscaras ─────────────────────────────────────────────────────────────

    def _mask_cpf(self, *_):
        raw = "".join(c for c in self.cpf_var.get() if c.isdigit())[:11]
        if len(raw) <= 3:
            m = raw
        elif len(raw) <= 6:
            m = f"{raw[:3]}.{raw[3:]}"
        elif len(raw) <= 9:
            m = f"{raw[:3]}.{raw[3:6]}.{raw[6:]}"
        else:
            m = f"{raw[:3]}.{raw[3:6]}.{raw[6:9]}-{raw[9:]}"
        if m != self.cpf_var.get():
            self.cpf_var.set(m)

    def _mask_telefone(self, *_):
        raw = "".join(c for c in self.telefone_var.get() if c.isdigit())[:11]
        if len(raw) <= 2:
            m = raw
        elif len(raw) <= 7:
            m = f"({raw[:2]}) {raw[2:]}"
        elif len(raw) <= 10:
            m = f"({raw[:2]}) {raw[2:6]}-{raw[6:]}"
        else:
            m = f"({raw[:2]}) {raw[2:7]}-{raw[7:]}"
        if m != self.telefone_var.get():
            self.telefone_var.set(m)

    def _mask_data(self, *_):
        raw = "".join(c for c in self.data_var.get() if c.isdigit())[:8]
        if len(raw) <= 2:
            m = raw
        elif len(raw) <= 4:
            m = f"{raw[:2]}/{raw[2:]}"
        else:
            m = f"{raw[:2]}/{raw[2:4]}/{raw[4:]}"
        if m != self.data_var.get():
            self.data_var.set(m)

    # ── Ordenação ─────────────────────────────────────────────────────────────

    def _sort_by_column(self, col):
        self._sort_reverse = (not self._sort_reverse) if self._sort_col == col else False
        self._sort_col = col
        key_map = {
            "nome":      lambda r: r.get("nome", "").lower(),
            "cpf":       lambda r: r.get("cpf", ""),
            "telefone":  lambda r: r.get("telefone", ""),
            "livro":     lambda r: r.get("livro", "").lower(),
            "data":      lambda r: self._date_key(r.get("data_emprestimo", "")),
            "devolucao": lambda r: self._date_key(r.get("data_devolucao", "")),
            "dias":      self._days_key,
            "status":    self._status_key,
        }
        self.records.sort(key=key_map.get(col, lambda r: ""), reverse=self._sort_reverse)
        self._load_tree()

    def _date_key(self, s):
        try:
            return parse_date(s).isoformat()
        except (ValueError, AttributeError):
            return ""

    def _days_key(self, rec):
        try:
            ld = parse_date(rec["data_emprestimo"])
            if rec.get("devolvido") and rec.get("data_devolucao"):
                return calc_duration(ld, parse_date(rec["data_devolucao"]))
            return calc_days(ld)
        except (ValueError, KeyError):
            return -1

    def _status_key(self, rec):
        if rec.get("devolvido"):
            return "2"
        try:
            return "0" if is_expired(parse_date(rec["data_emprestimo"])) else "1"
        except ValueError:
            return "3"

    # ── Tabela ───────────────────────────────────────────────────────────────

    def _load_tree(self):
        self.tree.delete(*self.tree.get_children())
        for idx, rec in self._filtered_records():
            try:
                ld = parse_date(rec["data_emprestimo"])
                dev = rec.get("devolvido")
                if dev and rec.get("data_devolucao"):
                    days = calc_duration(ld, parse_date(rec["data_devolucao"]))
                else:
                    days = calc_days(ld)
                status = "Devolvido" if dev else ("Expirado" if is_expired(ld) else "OK")
                date_str = format_date(ld)
            except ValueError:
                days, status, date_str = "-", "Data invalida", rec["data_emprestimo"]

            if rec.get("data_devolucao") and status != "Data invalida":
                try:
                    dev_str = format_date(parse_date(rec["data_devolucao"]))
                except ValueError:
                    dev_str = rec.get("data_devolucao") or "-"
            else:
                dev_str = rec.get("data_devolucao") or "-"

            tags = ("even" if idx % 2 == 0 else "odd",)
            if status == "Expirado":
                tags += ("expirado",)
            elif status == "Devolvido":
                tags += ("devolvido",)

            self.tree.insert("", "end", iid=str(idx),
                             values=(rec["nome"], rec["cpf"], rec.get("telefone", ""),
                                     rec["livro"], date_str, dev_str, days, status),
                             tags=tags)
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
        self.stats_total._value_label.config(text=str(total))
        self.stats_aberto._value_label.config(text=str(aberto))
        self.stats_expir._value_label.config(text=str(expirados))

    # ── Notificação ───────────────────────────────────────────────────────────

    def _notify_expired(self):
        expired = [r for r in self.records if not r.get("devolvido") and self._is_expired_safe(r)]
        if not expired:
            return
        preview = []
        for rec in expired[:5]:
            try:
                ds = format_date(parse_date(rec["data_emprestimo"]))
            except ValueError:
                ds = rec["data_emprestimo"]
            preview.append(f"  {rec['nome']} — {rec['livro']} ({ds})")
        extra = f"\n  ... e mais {len(expired) - 5}" if len(expired) > 5 else ""
        messagebox.showwarning("Emprestimos expirados",
                               f"{len(expired)} emprestimo(s) em atraso:\n\n" +
                               "\n".join(preview) + extra)

    def _is_expired_safe(self, rec):
        try:
            return is_expired(parse_date(rec["data_emprestimo"]))
        except ValueError:
            return False

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
            messagebox.showerror("Erro", "CPF invalido.")
            return
        try:
            data_emp = format_date(parse_date(data_emp))
        except ValueError:
            messagebox.showerror("Erro", "Data invalida. Use DD/MM/AAAA.")
            return

        self.records.append({"nome": nome, "cpf": cpf, "telefone": telefone,
                             "livro": livro, "data_emprestimo": data_emp,
                             "devolvido": False, "data_devolucao": ""})
        write_records(self.records)
        self._load_tree()
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
            messagebox.showinfo("Info", "Este registro ja esta como devolvido.")
            return
        if not messagebox.askyesno("Confirmar", "Marcar como devolvido?"):
            return
        rec["devolvido"] = True
        rec["data_devolucao"] = format_date(date.today())
        write_records(self.records)
        self._load_tree()

    # ── Busca ─────────────────────────────────────────────────────────────────

    def _filtered_records(self):
        q = self.search_var.get().strip().lower()
        if not q:
            return list(enumerate(self.records))
        return [
            (i, r) for i, r in enumerate(self.records)
            if q in " ".join([r.get("nome",""), r.get("cpf",""),
                               r.get("telefone",""), r.get("livro","")]).lower()
        ]

    def _on_search(self, _event):
        self._load_tree()

    def clear_search(self):
        self.search_var.set("")
        self._load_tree()

    def _clear_inputs(self):
        for v in (self.nome_var, self.cpf_var, self.telefone_var,
                  self.livro_var, self.data_var):
            v.set("")

    # ── Configurações ─────────────────────────────────────────────────────────

    def _open_config(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Configuracoes")
        dlg.resizable(False, False)
        dlg.configure(bg=BG)
        dlg.grab_set()

        frm = ttk.Frame(dlg, padding=20)
        frm.pack()

        tk.Label(frm, text="Dias para expirar emprestimo:", bg=BG,
                 font=("Segoe UI", 10), fg=TEXT).grid(row=0, column=0, sticky="w", padx=(0, 10))
        exp_var = tk.StringVar(value=str(cfg.EXP_DAYS))
        ttk.Entry(frm, textvariable=exp_var, width=6).grid(row=0, column=1)

        def _save():
            try:
                d = int(exp_var.get())
                if d < 1:
                    raise ValueError
            except (ValueError, tk.TclError):
                messagebox.showerror("Erro", "Informe um numero inteiro maior que zero.", parent=dlg)
                return
            cfg.save_settings(d)
            dlg.destroy()
            self._load_tree()

        ttk.Button(frm, text="Salvar", style="Primary.TButton", command=_save).grid(
            row=1, column=0, columnspan=2, pady=(14, 0), sticky="ew")
        dlg.wait_window()

    # ── Exportar ──────────────────────────────────────────────────────────────

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("CSV", "*.csv")],
            initialfile="emprestimos_relatorio",
            parent=self.root,
        )
        if not path:
            return
        records = self._filtered_records()
        if path.lower().endswith(".csv"):
            import csv as _csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = _csv.writer(f)
                w.writerow(["Nome", "CPF", "Telefone", "Livro",
                             "Data Emprestimo", "Devolucao", "Dias", "Status"])
                for _, rec in records:
                    st, dy = self._compute_status_days(rec)
                    w.writerow([rec.get("nome",""), rec.get("cpf",""),
                                 rec.get("telefone",""), rec.get("livro",""),
                                 rec.get("data_emprestimo",""),
                                 rec.get("data_devolucao","") or "-", dy, st])
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write("RELATORIO DE EMPRESTIMOS\n")
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
            return "Data invalida", "-"
