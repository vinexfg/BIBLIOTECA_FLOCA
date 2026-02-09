# Registro Bibliotecario

App simples em Tkinter para controlar emprestimos de livros.

## Estrutura

- src/ - codigo do app
- data/ - dados (CSV)
- dist/ - build do executavel (nao subir)
- build/ - arquivos temporarios (nao subir)

## Como rodar

1. Crie o arquivo de dados (opcional):

```
copy data/emprestimos.sample.csv data/emprestimos.csv
```

2. Execute:

```
python src/biblioteca_tk.py
```

Ou use o atalho:

```
run.bat
```

## Gerar executavel (Windows)

```
pip install -r requirements.txt
python -m PyInstaller -F -w -n registro_bibliotecario src/biblioteca_tk.py
```

O executavel fica em `dist/registro_bibliotecario.exe`.
