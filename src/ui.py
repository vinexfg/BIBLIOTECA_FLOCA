import os
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import config as cfg
from dates import parse_date, format_date, calc_days, is_expired, calc_duration
from storage import read_records, write_records
from validators import validate_cpf


class BibliotecaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Emprestimos")
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

    def _setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        bg = "#f6f3ee"
        accent = "#2d6a6a"
        header_bg = "#e0e7e5"
        header_active = "#d3dddb"
        self.row_alt = "#fbf8f4"

        self.root.configure(bg=bg)
        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=bg)
        style.configure("TLabelframe.Label", background=bg, foreground=accent, font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=bg, font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=24,
            background="#ffffff",
            fieldbackground="#ffffff",
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background=header_bg,
            foreground=accent,
        )
        style.map("Treeview.Heading", background=[("active", header_active)])

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frm.rowconfigure(2, weight=1)

        # --- Cadastro ---
        input_frame = ttk.LabelFrame(frm, text="Cadastro")
        input_frame.grid(row=0, column=0, sticky="ew")
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)

        ttk.Label(input_frame, text="Nome:").grid(row=0, column=0, sticky="w")
        self.nome_var = tk.StringVar()
        self.nome_entry = ttk.Entry(input_frame, textvariable=self.nome_var)
        self.nome_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(input_frame, text="CPF:").grid(row=0, column=2, sticky="w")
        self.cpf_var = tk.StringVar()
        self.cpf_var.trace_add("write", self._mask_cpf)
        ttk.Entry(input_frame, textvariable=self.cpf_var).grid(row=0, column=3, sticky="ew", padx=6, pady=4)

        ttk.Label(input_frame, text="Telefone:").grid(row=1, column=0, sticky="w")
        self.telefone_var = tk.StringVar()
        self.telefone_var.trace_add("write", self._mask_telefone)
        ttk.Entry(input_frame, textvariable=self.telefone_var).grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(input_frame, text="Livro:").grid(row=1, column=2, sticky="w")
        self.livro_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.livro_var).grid(row=1, column=3, sticky="ew", padx=6, pady=4)

        ttk.Label(input_frame, text="Data emprestimo (DD/MM/AAAA):").grid(row=2, column=0, sticky="w")
        self.data_var = tk.StringVar()
        self.data_var.trace_add("write", self._mask_data)
        data_entry = ttk.Entry(input_frame, textvariable=self.data_var)
        data_entry.grid(row=2, column=1, sticky="ew", padx=6, pady=4)
        data_entry.bind("<Return>", lambda _: self.add_record())

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=6)

        ttk.Button(btn_frame, text="Adicionar", command=self.add_record).grid(row=0, column=0, sticky="w")
        ttk.Button(btn_frame, text="Marcar devolvido", command=self.mark_returned).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Button(btn_frame, text="Deletar selecionado", command=self.delete_record).grid(row=0, column=2, sticky="w")
        ttk.Button(btn_frame, text="Recarregar", command=self.reload_records).grid(row=0, column=3, sticky="w", padx=6)
        ttk.Button(btn_frame, text="Configurações", command=self._open_config).grid(row=0, column=4, sticky="w")
        ttk.Button(btn_frame, text="Exportar", command=self._export).grid(row=0, column=5, sticky="w", padx=6)

        # --- Busca ---
        search_frame = ttk.LabelFrame(frm, text="Busca")
        search_frame.grid(row=1, column=0, sticky="ew")
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Buscar (nome, CPF, telefone, livro):").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        search_entry.bind("<KeyRelease>", self._on_search)
        ttk.Button(search_frame, text="Limpar", command=self.clear_search).grid(row=0, column=2, sticky="w")

        # --- Tabela ---
        list_frame = ttk.LabelFrame(frm, text="Emprestimos")
        list_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        columns = ("nome", "cpf", "telefone", "livro", "data", "devolucao", "dias", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        col_config = {
            "nome":      ("Nome",            160),
            "cpf":       ("CPF",             110),
            "telefone":  ("Telefone",        130),
            "livro":     ("Livro",           160),
            "data":      ("Data emprestimo", 120),
            "devolucao": ("Devolucao",       120),
            "dias":      ("Dias",             60),
            "status":    ("Status",          100),
        }
        for col, (label, width) in col_config.items():
            anchor = "center" if col in ("dias", "status") else "w"
            self.tree.heading(col, text=label, command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("expirado", foreground="#b23a1d")
        self.tree.tag_configure("devolvido", foreground="#1f6f43")
        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background=self.row_alt)

        # --- Barra de estatísticas ---
        self.stats_var = tk.StringVar(value="")
        ttk.Label(frm, textvariable=self.stats_var, font=("Segoe UI", 9), foreground="#555555").grid(
            row=3, column=0, sticky="w", pady=(0, 2)
        )

    def _set_initial_focus(self):
        def _focus():
            try:
                self.root.focus_force()
            except tk.TclError:
                pass
            self.nome_entry.focus_set()

        self.root.after(150, _focus)

    # --- Máscaras de entrada ---

    def _mask_cpf(self, *_):
        raw = "".join(c for c in self.cpf_var.get() if c.isdigit())[:11]
        if len(raw) <= 3:
            masked = raw
        elif len(raw) <= 6:
            masked = f"{raw[:3]}.{raw[3:]}"
        elif len(raw) <= 9:
            masked = f"{raw[:3]}.{raw[3:6]}.{raw[6:]}"
        else:
            masked = f"{raw[:3]}.{raw[3:6]}.{raw[6:9]}-{raw[9:]}"
        if masked != self.cpf_var.get():
            self.cpf_var.set(masked)

    def _mask_telefone(self, *_):
        raw = "".join(c for c in self.telefone_var.get() if c.isdigit())[:11]
        if len(raw) <= 2:
            masked = raw
        elif len(raw) <= 7:
            masked = f"({raw[:2]}) {raw[2:]}"
        elif len(raw) <= 10:
            masked = f"({raw[:2]}) {raw[2:6]}-{raw[6:]}"
        else:
            masked = f"({raw[:2]}) {raw[2:7]}-{raw[7:]}"
        if masked != self.telefone_var.get():
            self.telefone_var.set(masked)

    def _mask_data(self, *_):
        raw = "".join(c for c in self.data_var.get() if c.isdigit())[:8]
        if len(raw) <= 2:
            masked = raw
        elif len(raw) <= 4:
            masked = f"{raw[:2]}/{raw[2:]}"
        else:
            masked = f"{raw[:2]}/{raw[2:4]}/{raw[4:]}"
        if masked != self.data_var.get():
            self.data_var.set(masked)

    # --- Ordenação por coluna ---

    def _sort_by_column(self, col):
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False

        key_map = {
            "nome":      lambda r: r.get("nome", "").lower(),
            "cpf":       lambda r: r.get("cpf", ""),
            "telefone":  lambda r: r.get("telefone", ""),
            "livro":     lambda r: r.get("livro", "").lower(),
            "data":      lambda r: self._date_sort_key(r.get("data_emprestimo", "")),
            "devolucao": lambda r: self._date_sort_key(r.get("data_devolucao", "")),
            "dias":      self._days_sort_key,
            "status":    self._status_sort_key,
        }
        self.records.sort(key=key_map.get(col, lambda r: ""), reverse=self._sort_reverse)
        self._load_tree()

    def _date_sort_key(self, date_str):
        try:
            return parse_date(date_str).isoformat()
        except (ValueError, AttributeError):
            return ""

    def _days_sort_key(self, rec):
        try:
            loan_date = parse_date(rec["data_emprestimo"])
            if rec.get("devolvido") and rec.get("data_devolucao"):
                return calc_duration(loan_date, parse_date(rec["data_devolucao"]))
            return calc_days(loan_date)
        except (ValueError, KeyError):
            return -1

    def _status_sort_key(self, rec):
        if rec.get("devolvido"):
            return "2"
        try:
            return "0" if is_expired(parse_date(rec["data_emprestimo"])) else "1"
        except ValueError:
            return "3"

    # --- Carregar tabela ---

    def _load_tree(self):
        self.tree.delete(*self.tree.get_children())
        for idx, rec in self._filtered_records():
            try:
                loan_date = parse_date(rec["data_emprestimo"])
                devolvido = rec.get("devolvido")
                if devolvido and rec.get("data_devolucao"):
                    end_date = parse_date(rec["data_devolucao"])
                    days = calc_duration(loan_date, end_date)
                else:
                    days = calc_days(loan_date)

                if devolvido:
                    status = "Devolvido"
                else:
                    status = "Expirado" if is_expired(loan_date) else "OK"
            except ValueError:
                days = "-"
                status = "Data invalida"

            tags = ("even",) if idx % 2 == 0 else ("odd",)
            if status == "Expirado":
                tags = tags + ("expirado",)
            elif status == "Devolvido":
                tags = tags + ("devolvido",)

            data_emp_str = format_date(loan_date) if status != "Data invalida" else rec["data_emprestimo"]
            if rec.get("data_devolucao") and status != "Data invalida":
                try:
                    devolucao_str = format_date(parse_date(rec.get("data_devolucao") or ""))
                except ValueError:
                    devolucao_str = rec.get("data_devolucao") or "-"
            else:
                devolucao_str = rec.get("data_devolucao") or "-"

            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    rec["nome"],
                    rec["cpf"],
                    rec.get("telefone", ""),
                    rec["livro"],
                    data_emp_str,
                    devolucao_str,
                    days,
                    status,
                ),
                tags=tags,
            )
        self._update_stats()

    def _update_stats(self):
        total = len(self.records)
        em_aberto = expirados = 0
        for rec in self.records:
            if rec.get("devolvido"):
                continue
            em_aberto += 1
            try:
                if is_expired(parse_date(rec["data_emprestimo"])):
                    expirados += 1
            except ValueError:
                pass
        self.stats_var.set(f"Total: {total}  |  Em aberto: {em_aberto}  |  Expirados: {expirados}")

    # --- Notificação de expirados ---

    def _notify_expired(self):
        expired = [rec for rec in self.records if not rec.get("devolvido") and self._is_expired_safe(rec)]
        if not expired:
            return

        preview = []
        for rec in expired[:5]:
            try:
                data_str = format_date(parse_date(rec["data_emprestimo"]))
            except ValueError:
                data_str = rec["data_emprestimo"]
            preview.append(f"{rec['nome']} - {rec['livro']} ({data_str})")
        extra = f"\n... e mais {len(expired) - 5}" if len(expired) > 5 else ""
        messagebox.showwarning(
            "Aviso",
            f"Emprestimos expirados: {len(expired)}\n\n" + "\n".join(preview) + extra,
        )

    def _is_expired_safe(self, rec):
        try:
            return is_expired(parse_date(rec["data_emprestimo"]))
        except ValueError:
            return False

    # --- CRUD ---

    def add_record(self):
        nome = self.nome_var.get().strip()
        cpf = self.cpf_var.get().strip()
        telefone = self.telefone_var.get().strip()
        livro = self.livro_var.get().strip()
        data_emp = self.data_var.get().strip()

        if not nome or not cpf or not telefone or not livro or not data_emp:
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return

        if not validate_cpf(cpf):
            messagebox.showerror("Erro", "CPF inválido.")
            return

        try:
            data_emp = format_date(parse_date(data_emp))
        except ValueError:
            messagebox.showerror("Erro", "Data invalida. Use DD/MM/AAAA.")
            return

        self.records.append(
            {
                "nome": nome,
                "cpf": cpf,
                "telefone": telefone,
                "livro": livro,
                "data_emprestimo": data_emp,
                "devolvido": False,
                "data_devolucao": "",
            }
        )
        write_records(self.records)
        self._load_tree()
        self._clear_inputs()

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Selecione um registro.")
            return

        if not messagebox.askyesno("Confirmar", "Deletar este registro permanentemente?"):
            return

        idx = int(selected[0])
        if 0 <= idx < len(self.records):
            self.records.pop(idx)
            write_records(self.records)
            self._load_tree()

    def reload_records(self):
        self.records = read_records()
        self._load_tree()

    def mark_returned(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Selecione um registro.")
            return

        idx = int(selected[0])
        if idx < 0 or idx >= len(self.records):
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

    # --- Busca ---

    def _filtered_records(self):
        query = self.search_var.get().strip().lower()
        if not query:
            return list(enumerate(self.records))
        return [
            (idx, rec)
            for idx, rec in enumerate(self.records)
            if query in " ".join([
                rec.get("nome", ""),
                rec.get("cpf", ""),
                rec.get("telefone", ""),
                rec.get("livro", ""),
            ]).lower()
        ]

    def _on_search(self, event):
        self._load_tree()

    def clear_search(self):
        self.search_var.set("")
        self._load_tree()

    def _clear_inputs(self):
        self.nome_var.set("")
        self.cpf_var.set("")
        self.telefone_var.set("")
        self.livro_var.set("")
        self.data_var.set("")

    # --- Diálogo de configurações ---

    def _open_config(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Configurações")
        dlg.resizable(False, False)
        dlg.grab_set()

        frm = ttk.Frame(dlg, padding=16)
        frm.pack()

        ttk.Label(frm, text="Dias para expirar empréstimo:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        exp_var = tk.StringVar(value=str(cfg.EXP_DAYS))
        ttk.Entry(frm, textvariable=exp_var, width=6).grid(row=0, column=1, sticky="ew")

        def _save():
            try:
                days = int(exp_var.get())
                if days < 1:
                    raise ValueError
            except (ValueError, tk.TclError):
                messagebox.showerror("Erro", "Informe um número inteiro maior que zero.", parent=dlg)
                return
            cfg.save_settings(days)
            dlg.destroy()
            self._load_tree()

        ttk.Button(frm, text="Salvar", command=_save).grid(row=1, column=0, columnspan=2, pady=(12, 0))
        dlg.wait_window()

    # --- Exportar relatório ---

    def _export(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("CSV", "*.csv")],
            initialfile="emprestimos_relatorio",
            parent=self.root,
        )
        if not filepath:
            return

        records = self._filtered_records()

        if filepath.lower().endswith(".csv"):
            import csv as csv_mod
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv_mod.writer(f)
                writer.writerow(["Nome", "CPF", "Telefone", "Livro", "Data Emprestimo", "Devolucao", "Dias", "Status"])
                for _, rec in records:
                    status, days = self._compute_status_days(rec)
                    writer.writerow([
                        rec.get("nome", ""),
                        rec.get("cpf", ""),
                        rec.get("telefone", ""),
                        rec.get("livro", ""),
                        rec.get("data_emprestimo", ""),
                        rec.get("data_devolucao", "") or "-",
                        days,
                        status,
                    ])
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("RELATÓRIO DE EMPRÉSTIMOS\n")
                f.write(f"Gerado em: {format_date(date.today())}\n")
                f.write("=" * 60 + "\n\n")
                for _, rec in records:
                    status, days = self._compute_status_days(rec)
                    f.write(f"Nome:    {rec.get('nome', '')}\n")
                    f.write(f"CPF:     {rec.get('cpf', '')}\n")
                    f.write(f"Tel:     {rec.get('telefone', '')}\n")
                    f.write(f"Livro:   {rec.get('livro', '')}\n")
                    f.write(f"Emprest: {rec.get('data_emprestimo', '')}\n")
                    f.write(f"Devol:   {rec.get('data_devolucao', '') or '-'}\n")
                    f.write(f"Dias:    {days}  |  Status: {status}\n")
                    f.write("-" * 40 + "\n")

        messagebox.showinfo("Exportado", f"Arquivo salvo:\n{filepath}")

    def _compute_status_days(self, rec):
        try:
            loan_date = parse_date(rec["data_emprestimo"])
            if rec.get("devolvido") and rec.get("data_devolucao"):
                days = calc_duration(loan_date, parse_date(rec["data_devolucao"]))
                return "Devolvido", days
            days = calc_days(loan_date)
            status = "Expirado" if is_expired(loan_date) else "OK"
            return status, days
        except ValueError:
            return "Data invalida", "-"
