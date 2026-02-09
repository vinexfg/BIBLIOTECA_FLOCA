from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

from dates import (
    parse_date,
    format_date,
    calc_days,
    is_expired,
    calc_duration,
)
from storage import read_records, write_records


class BibliotecaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Emprestimos")
        self.records = read_records()

        self._setup_style()
        self._build_ui()
        self._set_initial_focus()
        self._load_tree()
        self._notify_expired()

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
        style.map(
            "Treeview.Heading",
            background=[("active", header_active)],
        )

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frm.rowconfigure(2, weight=1)

        input_frame = ttk.LabelFrame(frm, text="Cadastro")
        input_frame.grid(row=0, column=0, sticky="ew")
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)

        ttk.Label(input_frame, text="Nome:").grid(row=0, column=0, sticky="w")
        self.nome_var = tk.StringVar()
        self.nome_entry = ttk.Entry(input_frame, textvariable=self.nome_var)
        self.nome_entry.grid(
            row=0, column=1, sticky="ew", padx=6, pady=4
        )

        ttk.Label(input_frame, text="CPF:").grid(row=0, column=2, sticky="w")
        self.cpf_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.cpf_var).grid(
            row=0, column=3, sticky="ew", padx=6, pady=4
        )

        ttk.Label(input_frame, text="Telefone:").grid(row=1, column=0, sticky="w")
        self.telefone_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.telefone_var).grid(
            row=1, column=1, sticky="ew", padx=6, pady=4
        )

        ttk.Label(input_frame, text="Livro:").grid(row=1, column=2, sticky="w")
        self.livro_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.livro_var).grid(
            row=1, column=3, sticky="ew", padx=6, pady=4
        )

        ttk.Label(input_frame, text="Data emprestimo (DD/MM/AAAA):").grid(
            row=2, column=0, sticky="w"
        )
        self.data_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.data_var).grid(
            row=2, column=1, sticky="ew", padx=6, pady=4
        )

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=6)
        btn_frame.columnconfigure(0, weight=1)

        ttk.Button(btn_frame, text="Adicionar", command=self.add_record).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(btn_frame, text="Marcar devolvido", command=self.mark_returned).grid(
            row=0, column=1, sticky="w", padx=6
        )
        ttk.Button(btn_frame, text="Deletar selecionado", command=self.delete_record).grid(
            row=0, column=2, sticky="w"
        )
        ttk.Button(btn_frame, text="Recarregar", command=self.reload_records).grid(
            row=0, column=3, sticky="w", padx=6
        )

        search_frame = ttk.LabelFrame(frm, text="Busca")
        search_frame.grid(row=1, column=0, sticky="ew")
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Buscar (nome, CPF, telefone, livro):").grid(
            row=0, column=0, sticky="w"
        )
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        search_entry.bind("<KeyRelease>", self._on_search)

        ttk.Button(search_frame, text="Limpar", command=self.clear_search).grid(
            row=0, column=2, sticky="w"
        )

        list_frame = ttk.LabelFrame(frm, text="Emprestimos")
        list_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        columns = ("nome", "cpf", "telefone", "livro", "data", "devolucao", "dias", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        self.tree.heading("nome", text="Nome")
        self.tree.heading("cpf", text="CPF")
        self.tree.heading("telefone", text="Telefone")
        self.tree.heading("livro", text="Livro")
        self.tree.heading("data", text="Data emprestimo")
        self.tree.heading("devolucao", text="Devolucao")
        self.tree.heading("dias", text="Dias")
        self.tree.heading("status", text="Status")

        self.tree.column("nome", width=160)
        self.tree.column("cpf", width=100)
        self.tree.column("telefone", width=120)
        self.tree.column("livro", width=160)
        self.tree.column("data", width=120)
        self.tree.column("devolucao", width=120)
        self.tree.column("dias", width=60, anchor="center")
        self.tree.column("status", width=100, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("expirado", foreground="#b23a1d")
        self.tree.tag_configure("devolvido", foreground="#1f6f43")
        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background=self.row_alt)

    def _set_initial_focus(self):
        def _focus():
            try:
                self.root.focus_force()
            except tk.TclError:
                pass
            self.nome_entry.focus_set()

        self.root.after(150, _focus)

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

    def _notify_expired(self):
        expired = []
        for rec in self.records:
            if rec.get("devolvido"):
                continue
            try:
                loan_date = parse_date(rec["data_emprestimo"])
            except ValueError:
                continue
            if is_expired(loan_date):
                expired.append(rec)

        if not expired:
            return

        preview = []
        for rec in expired[:5]:
            try:
                data_str = format_date(parse_date(rec["data_emprestimo"]))
            except ValueError:
                data_str = rec["data_emprestimo"]
            preview.append(f"{rec['nome']} - {rec['livro']} ({data_str})")
        extra = ""
        if len(expired) > 5:
            extra = f"\n... e mais {len(expired) - 5}"

        message = "Emprestimos expirados: {0}\n\n{1}{2}".format(
            len(expired), "\n".join(preview), extra
        )
        messagebox.showwarning("Aviso", message)

    def add_record(self):
        nome = self.nome_var.get().strip()
        cpf = self.cpf_var.get().strip()
        telefone = self.telefone_var.get().strip()
        livro = self.livro_var.get().strip()
        data_emp = self.data_var.get().strip()

        if not nome or not cpf or not telefone or not livro or not data_emp:
            messagebox.showerror("Erro", "Preencha todos os campos.")
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

        if not messagebox.askyesno("Confirmar", "Devolucao confirmada? Deletar?"):
            return

        idx = int(selected[0])
        if idx < 0 or idx >= len(self.records):
            return
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

    def _filtered_records(self):
        query = (self.search_var.get() if hasattr(self, "search_var") else "").strip()
        if not query:
            return list(enumerate(self.records))

        query_lower = query.lower()
        filtered = []
        for idx, rec in enumerate(self.records):
            haystack = " ".join(
                [
                    rec.get("nome", ""),
                    rec.get("cpf", ""),
                    rec.get("telefone", ""),
                    rec.get("livro", ""),
                ]
            ).lower()
            if query_lower in haystack:
                filtered.append((idx, rec))
        return filtered

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
