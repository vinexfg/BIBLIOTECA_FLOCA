import csv
import os

from config import DATA_FILE


def read_records():
    if not os.path.exists(DATA_FILE):
        return []
    records = []
    with open(DATA_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            devolvido_raw = (row.get("devolvido") or "").strip().lower()
            devolvido = devolvido_raw in {"1", "true", "sim", "yes"}
            records.append(
                {
                    "nome": (row.get("nome") or "").strip(),
                    "cpf": (row.get("cpf") or "").strip(),
                    "telefone": (row.get("telefone") or "").strip(),
                    "livro": (row.get("livro") or "").strip(),
                    "data_emprestimo": (row.get("data_emprestimo") or "").strip(),
                    "devolvido": devolvido,
                    "data_devolucao": (row.get("data_devolucao") or "").strip(),
                }
            )
    return records


def write_records(records):
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "nome",
                "cpf",
                "telefone",
                "livro",
                "data_emprestimo",
                "devolvido",
                "data_devolucao",
            ],
        )
        writer.writeheader()
        for rec in records:
            writer.writerow(
                {
                    "nome": rec.get("nome", ""),
                    "cpf": rec.get("cpf", ""),
                    "telefone": rec.get("telefone", ""),
                    "livro": rec.get("livro", ""),
                    "data_emprestimo": rec.get("data_emprestimo", ""),
                    "devolvido": "1" if rec.get("devolvido") else "0",
                    "data_devolucao": rec.get("data_devolucao", ""),
                }
            )
