from abc import ABC, abstractmethod
from datetime import datetime
import textwrap


# ============================================================
# CAMADA DE TRANSAÇÕES (Polimorfismo + Abstração)
# ============================================================

class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self):
        pass

    @abstractmethod
    def registrar(self, conta):
        pass


class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        if conta.depositar(self._valor):
            conta.historico.adicionar_transacao(self)


class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        if conta.sacar(self._valor):
            conta.historico.adicionar_transacao(self)


# ============================================================
# HISTÓRICO
# ============================================================

class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )

    def gerar_relatorio(self, tipo_transacao=None):
        for t in self._transacoes:
            if tipo_transacao is None or t["tipo"].lower() == tipo_transacao.lower():
                yield t

    def transacoes_do_dia(self):
        hoje = datetime.now().date()
        return [
            t for t in self._transacoes
            if datetime.strptime(t["data"], "%d-%m-%Y %H:%M:%S").date() == hoje
        ]


# ============================================================
# CONTAS (Herança + Encapsulamento)
# ============================================================

class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    def sacar(self, valor):
        if valor <= 0:
            print("\n@@@ Operação falhou! Valor inválido. @@@")
            return False
        if valor > self._saldo:
            print("\n@@@ Operação falhou! Saldo insuficiente. @@@")
            return False
        self._saldo -= valor
        print("\n=== Saque realizado com sucesso! ===")
        return True

    def depositar(self, valor):
        if valor <= 0:
            print("\n@@@ Operação falhou! Valor inválido. @@@")
            return False
        self._saldo += valor
        print("\n=== Depósito realizado com sucesso! ===")
        return True


class ContaCorrente(Conta):
    """Herda de Conta e adiciona limite e controle de saques."""

    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    @classmethod
    def nova_conta(cls, cliente, numero, limite=500, limite_saques=3):
        return cls(numero, cliente, limite, limite_saques)

    def sacar(self, valor):
        saques_hoje = sum(
            1 for t in self.historico.transacoes_do_dia()
            if t["tipo"] == "Saque"
        )

        if valor > self._limite:
            print(f"\n@@@ Operação falhou! Valor excede o limite de R$ {self._limite:.2f}. @@@")
            return False
        if saques_hoje >= self._limite_saques:
            print(f"\n@@@ Operação falhou! Limite de {self._limite_saques} saques diários atingido. @@@")
            return False

        return super().sacar(valor)

    def __str__(self):
        return (
            f"Agência:\t{self.agencia}\n"
            f"C/C:\t\t{self.numero}\n"
            f"Titular:\t{self.cliente.nome}"
        )


# ============================================================
# CLIENTES (Herança)
# ============================================================

class Cliente:
    def __init__(self, endereco):
        self._endereco = endereco
        self._contas = []

    @property
    def contas(self):
        return self._contas

    def realizar_transacao(self, conta, transacao):
        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self._contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self._nome = nome
        self._data_nascimento = data_nascimento
        self._cpf = cpf

    @property
    def nome(self):
        return self._nome

    @property
    def cpf(self):
        return self._cpf

    def __str__(self):
        return f"{self._nome} (CPF: {self._cpf})"


# ============================================================
# ITERADORES / DECORADORES UTILITÁRIOS
# ============================================================

def log_transacao(func):
    """Decorator que registra no console cada operação realizada."""
    def wrapper(*args, **kwargs):
        print(f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Iniciando: {func.__name__}")
        resultado = func(*args, **kwargs)
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Finalizado: {func.__name__}")
        return resultado
    return wrapper


# ============================================================
# INTERFACE / MENU
# ============================================================

def menu():
    opcoes = """\n
    ================ MENU ================
    [d]   Depositar
    [s]   Sacar
    [e]   Extrato
    [nc]  Nova conta
    [lc]  Listar contas
    [nu]  Novo usuário
    [q]   Sair
    => """
    return input(textwrap.dedent(opcoes))


def filtrar_cliente(cpf, clientes):
    return next((c for c in clientes if c.cpf == cpf), None)


def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print("\n@@@ Cliente não possui conta! @@@")
        return None
    # Retorna a primeira conta (poderia ser expandido para múltiplas)
    return cliente.contas[0]


@log_transacao
def depositar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)
    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do depósito: "))
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, Deposito(valor))


@log_transacao
def sacar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)
    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do saque: "))
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, Saque(valor))


def exibir_extrato(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)
    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    print("\n================ EXTRATO ================")
    transacoes = list(conta.historico.gerar_relatorio())
    if not transacoes:
        print("Não foram realizadas movimentações.")
    else:
        for t in transacoes:
            print(f"{t['tipo']:<12} R$ {t['valor']:.2f}  ({t['data']})")
    print(f"\nSaldo atual:\tR$ {conta.saldo:.2f}")
    print("==========================================")


@log_transacao
def criar_cliente(clientes):
    cpf = input("Informe o CPF (somente números): ")
    if filtrar_cliente(cpf, clientes):
        print("\n@@@ Já existe cliente com esse CPF! @@@")
        return

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/UF): ")

    cliente = PessoaFisica(nome, data_nascimento, cpf, endereco)
    clientes.append(cliente)
    print("\n=== Cliente criado com sucesso! ===")


@log_transacao
def criar_conta(numero_conta, clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)
    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
    contas.append(conta)
    cliente.adicionar_conta(conta)
    print("\n=== Conta criada com sucesso! ===")


def listar_contas(contas):
    if not contas:
        print("\nNenhuma conta cadastrada.")
        return
    for conta in contas:
        print("=" * 50)
        print(textwrap.dedent(str(conta)))


# ============================================================
# PONTO DE ENTRADA
# ============================================================

def main():
    clientes = []
    contas = []

    while True:
        opcao = menu()

        if opcao == "d":
            depositar(clientes)
        elif opcao == "s":
            sacar(clientes)
        elif opcao == "e":
            exibir_extrato(clientes)
        elif opcao == "nu":
            criar_cliente(clientes)
        elif opcao == "nc":
            criar_conta(len(contas) + 1, clientes, contas)
        elif opcao == "lc":
            listar_contas(contas)
        elif opcao == "q":
            print("\nAté logo!")
            break
        else:
            print("\nOpção inválida. Tente novamente.")


main()
