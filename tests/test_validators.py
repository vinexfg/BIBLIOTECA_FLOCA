from validators import validate_cpf


def test_valid_cpf_com_mascara():
    assert validate_cpf("529.982.247-25") is True


def test_valid_cpf_somente_digitos():
    assert validate_cpf("52998224725") is True


def test_digito_verificador_errado():
    assert validate_cpf("529.982.247-26") is False


def test_todos_digitos_iguais():
    assert validate_cpf("111.111.111-11") is False


def test_cpf_muito_curto():
    assert validate_cpf("123") is False


def test_cpf_vazio():
    assert validate_cpf("") is False


def test_cpf_com_letras():
    assert validate_cpf("abc.def.ghi-jk") is False
