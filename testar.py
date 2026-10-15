import traceback
from itertools import count

from src.models import (QTD_MINIMA_PRODUTO, CategoriaProduto, EmpresaCompradora, EmpresaMarisqueira,
                    Estado, Localizacao, OrdenarPor, RegraNegocioError, StatusPedido)

CATEGORIAS = {"1": CategoriaProduto.FRESCO, "2": CategoriaProduto.CONGELADO}
ORDENACOES = {"1": OrdenarPor.MENOR_PRECO, "2": OrdenarPor.MELHOR_AVALIACAO, "3": OrdenarPor.PROXIMIDADE}



def ler_int(rotulo):
    try:
        return int(input(f"{rotulo}: ").strip())
    except ValueError:
        raise ValueError("digite um número inteiro")


def ler_preco(rotulo):
    try:
        return float(input(f"{rotulo}: ").strip().replace(",", "."))
    except ValueError:
        raise ValueError("digite um valor numérico")


def ler_localizacao(padrao=None):
    dica = f" (enter = {padrao})" if padrao else ""
    endereco = input(f"Endereço{dica}: ").strip()
    if not endereco and padrao:
        return padrao
    cidade = input("Cidade: ").strip()
    sigla = input("Estado (sigla, ex.: MA): ").strip().upper()
    if not endereco or not cidade:
        raise ValueError("endereço e cidade são obrigatórios")
    if sigla not in Estado.__members__:
        raise ValueError("sigla de estado inválida")
    return Localizacao(endereco, cidade, Estado[sigla])


def escolher(itens, descrever, titulo):
    if not itens:
        print("  (nada para escolher)")
        return None
    print(titulo)
    for n, item in enumerate(itens, 1):
        print(f"  {n}) {descrever(item)}")
    n = ler_int("Número (0 para voltar)")
    return itens[n - 1] if 1 <= n <= len(itens) else None


def estrelas(empresa):
    return f"{empresa.media_avaliacoes():.1f}★" if empresa.avaliacoes else "sem avaliações"


def descrever_empresa(e):
    tipo = "marisqueira" if isinstance(e, EmpresaMarisqueira) else "compradora"
    return f"[id {e.id}] {e.nome} ({tipo}) - {e.localizacao.cidade}/{e.localizacao.estado}"


def descrever_produto(p):
    estoque = f"{p.qtd_disponivel} kg" if p.qtd_disponivel >= QTD_MINIMA_PRODUTO else \
        f"INDISPONÍVEL ({p.qtd_disponivel} kg)"
    return f"{p} | {estoque} | {p.empresa.localizacao.cidade}/{p.empresa.localizacao.estado} | {estrelas(p.empresa)}"


def descrever_pedido(p):
    itens = ", ".join(f"{i.produto.descricao} {i.quantidade} kg" for i in p.itens)
    texto = (f"[{p.status.value}] {p.empresa_compradora.nome} -> {p.empresa_marisqueira.nome} | "
             f"{itens} | R$ {p.total:.2f} | entrega em {p.tempo_entrega_dias} dia(s) para {p.endereco_entrega}")
    if p.mensagem_ajuste:
        texto += f" | ajuste pedido: {p.mensagem_ajuste}"
    return texto


class App:
    def __init__(self):
        self.marisqueiras = []
        self.compradoras = []
        self.ids = count(1)  
        self.dados_exemplo()


    def menu(self, titulo, opcoes, saida="Voltar"):
        while True:
            print(f"\n=== {titulo} ===")
            for n, (rotulo, _) in enumerate(opcoes, 1):
                print(f"{n}) {rotulo}")
            print(f"0) {saida}")
            op = input("Opção: ").strip()
            if op == "0":
                return
            if not (op.isdigit() and 1 <= int(op) <= len(opcoes)):
                print("Opção inválida.")
                continue
            try:
                opcoes[int(op) - 1][1]()
            except (RegraNegocioError, ValueError) as erro:
                print(f">> Não foi possível: {erro}")
            except Exception:
                print(">> ERRO INESPERADO (provável bug no modelo):")
                traceback.print_exc()

    def principal(self):
        self.menu("MARISQUEIRAS DA ILHA", [
            ("Entrar como empresa", self.entrar),
            ("Cadastrar empresa", self.cadastrar_empresa),
        ], saida="Sair")

    def dados_exemplo(self):
        maria = EmpresaMarisqueira(next(self.ids), "Maria Mariscos", "Maria",
                                   Localizacao("Rua 1, Vila Maresia", "Raposa", Estado.MA))
        rita = EmpresaMarisqueira(next(self.ids), "Mariscos da Rita", "Rita",
                                  Localizacao("Rua 5, Vila Maresia", "Raposa", Estado.MA))
        lurdes = EmpresaMarisqueira(next(self.ids), "Mariscos da Lurdes", "Lurdes",
                                    Localizacao("Rua Santa Helena, João Paulo", "São Luís", Estado.MA))
        maria.cadastrar_produto("Sururu", CategoriaProduto.FRESCO, 40, 100)
        maria.cadastrar_produto("Sururu", CategoriaProduto.CONGELADO, 35, 80)
        rita.cadastrar_produto("Camarão", CategoriaProduto.FRESCO, 60, 30)
        mare = EmpresaCompradora(next(self.ids), "Restaurante Maré",
                                 Localizacao("Av. Litorânea, 100", "São Luís", Estado.MA))
        self.marisqueiras += [maria, rita, lurdes]
        self.compradoras.append(mare)
        print("Dados de exemplo carregados: 3 marisqueiras, 1 compradora.")

    def cadastrar_empresa(self):
        tipo = input("Tipo (1 = marisqueira, 2 = compradora): ").strip()
        if tipo not in ("1", "2"):
            raise ValueError("tipo inválido")
        nome = input("Nome da empresa: ").strip()
        localizacao = ler_localizacao()
        if not nome:
            raise ValueError("o nome da empresa é obrigatório")
        if tipo == "1":
            responsavel = input("Nome do responsável: ").strip()
            if not responsavel:
                raise ValueError("o nome do responsável é obrigatório")
            self.marisqueiras.append(EmpresaMarisqueira(next(self.ids), nome, responsavel, localizacao))
        else:
            self.compradoras.append(EmpresaCompradora(next(self.ids), nome, localizacao))
        print("Empresa cadastrada.")

    def entrar(self):
        empresa = escolher(self.marisqueiras + self.compradoras, descrever_empresa, "Empresas cadastradas:")
        if empresa is None:
            return
        if isinstance(empresa, EmpresaMarisqueira):
            self.menu_marisqueira(empresa)
        else:
            self.menu_compradora(empresa)


    def menu_marisqueira(self, m):
        em_andamento = (StatusPedido.ACEITO, StatusPedido.EM_PREPARO, StatusPedido.EM_ROTA)
        self.menu(f"Marisqueira: {m.nome}", [
            ("Cadastrar produto", lambda: self.cadastrar_produto(m)),
            ("Meus produtos", lambda: self.listar(m.produtos, descrever_produto)),
            ("Alterar quantidade de um produto", lambda: self.alterar_quantidade(m)),
            ("Pedidos recebidos", lambda: self.listar(m.pedidos_recebidos, descrever_pedido)),
            ("Aceitar pedido", lambda: self.tratar_pedido(
                m, (StatusPedido.PENDENTE,), "Pedidos para aceitar:", m.aceitar_pedido)),
            ("Rejeitar pedido", lambda: self.tratar_pedido(
                m, (StatusPedido.PENDENTE,), "Pedidos para rejeitar:", m.rejeitar_pedido)),
            ("Solicitar ajuste", lambda: self.tratar_pedido(
                m, (StatusPedido.PENDENTE,), "Pedidos para ajustar:",
                lambda p: m.solicitar_ajuste(p, input("O que precisa ser ajustado? ").strip()))),
            ("Atualizar status da entrega", lambda: self.tratar_pedido(
                m, em_andamento, "Pedidos em andamento:", m.atualizar_status_entrega)),
            ("Minha avaliação", lambda: print(f"  {estrelas(m)} ({len(m.avaliacoes)} avaliação(ões))")),
        ])

    def listar(self, itens, descrever):
        if not itens:
            print("  (vazio)")
        for item in itens:
            print(" ", descrever(item))

    def cadastrar_produto(self, m):
        descricao = input("Descrição do produto: ").strip()
        categoria = CATEGORIAS.get(input("Categoria (1 = fresco, 2 = congelado): ").strip())
        preco = ler_preco("Preço por kg (R$)")
        quantidade = ler_int(f"Quantidade disponível (kg, mínimo {QTD_MINIMA_PRODUTO})")
        m.cadastrar_produto(descricao, categoria, preco, quantidade)
        print("Produto cadastrado.")

    def alterar_quantidade(self, m):
        produto = escolher(m.produtos, descrever_produto, "Qual produto?")
        if produto:
            m.alterar_quantidade(produto, ler_int(f"Nova quantidade (kg, mínimo {QTD_MINIMA_PRODUTO})"))
            print("Quantidade atualizada.")

    def tratar_pedido(self, m, status_validos, titulo, acao):
        pedido = escolher([p for p in m.pedidos_recebidos if p.status in status_validos],
                          descrever_pedido, titulo)
        if pedido:
            acao(pedido)
            print(f"Feito. Status do pedido agora: {pedido.status.value}.")


    def menu_compradora(self, c):
        self.menu(f"Compradora: {c.nome}", [
            ("Consultar produtos", lambda: self.consultar(c)),
            ("Comparar produtos", lambda: self.comparar(c)),
            ("Realizar pedido", lambda: self.realizar_pedido(c)),
            ("Meus pedidos", lambda: self.listar(c.pedidos_realizados, descrever_pedido)),
            ("Avaliar empresa de um pedido", lambda: self.avaliar(c)),
        ])

    def _mostrar_catalogo(self, c):
        produtos = c.consultar_produtos(self.marisqueiras)
        for n, p in enumerate(produtos, 1):
            print(f"  {n}) {descrever_produto(p)}")
        return produtos

    def _produto_numero(self, catalogo, texto):
        n = int(texto)
        if not 1 <= n <= len(catalogo):
            raise ValueError(f"não existe produto número {n}")
        return catalogo[n - 1]

    def consultar(self, c):
        nome = input("Nome do produto (enter = qualquer): ").strip() or None
        categoria = CATEGORIAS.get(input("Categoria (1 = fresco, 2 = congelado, enter = todas): ").strip())
        localizacao = input("Localização, texto contido no endereço/cidade/UF (enter = qualquer): ").strip() or None
        empresa = input("Empresa/marisqueira (enter = qualquer): ").strip() or None
        minimo = input("Mínimo de estrelas 1-5 (enter = qualquer): ").strip()
        ordem = ORDENACOES.get(input("Ordenar por (1 menor preço, 2 melhor avaliação, 3 proximidade, "
                                     "enter = nenhuma): ").strip())
        produtos = c.consultar_produtos(self.marisqueiras, nome, categoria, localizacao, empresa,
                                        int(minimo) if minimo else None, ordem)
        if not produtos:
            print("Nenhum produto encontrado.")
        for n, p in enumerate(produtos, 1):
            print(f"  {n}) {descrever_produto(p)}")

    def comparar(self, c):
        catalogo = self._mostrar_catalogo(c)
        numeros = input("Números dos produtos para comparar (separados por vírgula): ")
        produtos = [self._produto_numero(catalogo, n) for n in numeros.split(",") if n.strip()]
        for linha in c.comparar_produtos(produtos):
            print(f"  - {linha['produto']} ({linha['categoria']}) | {linha['empresa']} | "
                  f"R$ {linha['preco_kg']:.2f}/kg | {linha['disponivel_kg']} kg | {linha['avaliacao']:.1f}★")

    def realizar_pedido(self, c):
        catalogo = self._mostrar_catalogo(c)
        itens = []
        while True:
            texto = input("Número do produto (enter para finalizar os itens): ").strip()
            if not texto:
                break
            produto = self._produto_numero(catalogo, texto)
            itens.append((produto, ler_int(f"Quantidade de {produto.descricao} (kg)")))
        endereco = ler_localizacao(padrao=c.localizacao)
        dias = ler_int("Tempo de entrega (dias)")
        pedido = c.realizar_pedido(itens, endereco, dias)
        print(f"Pedido enviado para {pedido.empresa_marisqueira.nome}. Total: R$ {pedido.total:.2f}")

    def avaliar(self, c):
        pedido = escolher(c.pedidos_realizados, descrever_pedido, "Qual pedido?")
        if pedido:
            c.avaliar_empresa(pedido, ler_int("Nota (1 a 5)"))
            print("Avaliação registrada.")


if __name__ == "__main__":
    App().principal()