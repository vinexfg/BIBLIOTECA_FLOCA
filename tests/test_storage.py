import os
import pytest

import config
import storage

SAMPLE = [
    {
        "nome": "João Silva",
        "cpf": "529.982.247-25",
        "telefone": "(11) 99999-0000",
        "livro": "Dom Casmurro",
        "data_emprestimo": "01/01/2026",
        "devolvido": False,
        "data_devolucao": "",
    }
]


@pytest.fixture
def data_file(tmp_path, monkeypatch):
    path = str(tmp_path / "test.csv")
    monkeypatch.setattr(config, "DATA_FILE", path)
    monkeypatch.setattr(storage, "DATA_FILE", path)
    return path


def test_escreve_e_le(data_file):
    storage.write_records(SAMPLE)
    result = storage.read_records()
    assert len(result) == 1
    assert result[0]["nome"] == "João Silva"
    assert result[0]["devolvido"] is False


def test_devolvido_salvo_como_1(data_file):
    rec = {**SAMPLE[0], "devolvido": True, "data_devolucao": "15/01/2026"}
    storage.write_records([rec])
    result = storage.read_records()
    assert result[0]["devolvido"] is True
    assert result[0]["data_devolucao"] == "15/01/2026"


def test_sem_arquivo_retorna_lista_vazia(data_file):
    assert storage.read_records() == []


def test_backup_criado_na_segunda_escrita(data_file):
    storage.write_records(SAMPLE)
    assert not os.path.exists(data_file + ".bak")
    storage.write_records(SAMPLE)
    assert os.path.exists(data_file + ".bak")


def test_multiplos_registros(data_file):
    records = [
        {**SAMPLE[0], "nome": f"Pessoa {i}"} for i in range(5)
    ]
    storage.write_records(records)
    result = storage.read_records()
    assert len(result) == 5
    assert result[2]["nome"] == "Pessoa 2"
