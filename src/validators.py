def validate_cpf(cpf: str) -> bool:
    cpf = "".join(c for c in cpf if c.isdigit())
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    total = sum(int(cpf[i]) * (10 - i) for i in range(9))
    remainder = (total * 10) % 11
    if remainder == 10:
        remainder = 0
    if remainder != int(cpf[9]):
        return False

    total = sum(int(cpf[i]) * (11 - i) for i in range(10))
    remainder = (total * 10) % 11
    if remainder == 10:
        remainder = 0
    return remainder == int(cpf[10])
