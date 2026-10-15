from __future__ import annotations
from dataclasses import dataclass
from src.algoritmo_distancia import ordenar_distancias
from enum import Enum

QTD_MINIMA_PRODUTO = 25

class Estado(Enum):
    AC = "Acre"
    AL = "Alagoas"
    AP = "Amapá"
    AM = "Amazonas"
    BA = "Bahia"
    CE = "Ceará"
    DF = "Distrito Federal"
    ES = "Espírito Santo"
    GO = "Goiás"
    MA = "Maranhão"
    MT = "Mato Grosso"
    MS = "Mato Grosso do Sul"
    MG = "Minas Gerais"
    PA = "Pará"
    PB = "Paraíba"
    PR = "Paraná"
    PE = "Pernambuco"
    PI = "Piauí"
    RJ = "Rio de Janeiro"
    RN = "Rio Grande do Norte"
    RS = "Rio Grande do Sul"
    RO = "Rondônia"
    RR = "Roraima"
    SC = "Santa Catarina"
    SP = "São Paulo"
    SE = "Sergipe"
    TO = "Tocantins"

    def __str__(self):
        return self.name

@dataclass(frozen=True)
class Localizacao:
    endereco: str
    cidade: str
    estado: Estado

    def __str__(self):
        return f"{self.endereco}, {self.cidade}, {self.estado}"

class CategoriaProduto(Enum):
    FRESCO = "fresco"
    CONGELADO = "congelado"

class StatusPedido(Enum):
    RASCUNHO = "rascunho"
    PENDENTE = "pendente"
    ACEITO = "aceito"
    REJEITADO = "rejeitado"
    AJUSTE_SOLICITADO = "ajuste solicitado"
    EM_PREPARO = "em preparo"
    EM_ROTA = "em rota"
    ENTREGUE = "entregue"

PROXIMO_STATUS = {
    StatusPedido.ACEITO: StatusPedido.EM_PREPARO,
    StatusPedido.EM_PREPARO: StatusPedido.EM_ROTA,
    StatusPedido.EM_ROTA: StatusPedido.ENTREGUE
}

class OrdenarPor(Enum):
    MENOR_PRECO = 1
    MELHOR_AVALIACAO = 2
    PROXIMIDADE = 3

class RegraNegocioError(Exception):
    pass



class Produto:
    def __init__(self, descricao, categoria:CategoriaProduto, preco_kg, qtd_disponivel, empresa:EmpresaMarisqueira, foto=None):
        self.descricao = descricao
        self.categoria = categoria
        self.preco_kg = preco_kg
        self.empresa = empresa
        self.foto = foto
        self.qtd_disponivel = 0

        self.atualizar_quantidade(qtd_disponivel)

    def __str__(self):
        return f"{self.descricao.upper()} - R$ {self.preco_kg}/kg | Marisco {self.categoria.name} | {self.empresa.nome}"

    def atualizar_quantidade(self, nova_qtd, via_venda=False):
        if nova_qtd < 0 or (not via_venda and nova_qtd < QTD_MINIMA_PRODUTO):
            raise RegraNegocioError(f"A quantidade registrada deve ser no mínimo {QTD_MINIMA_PRODUTO} kg")
        
        self.qtd_disponivel = nova_qtd

    def verificar_disponibilidade(self, qtd_solicitada):
        return 0 < qtd_solicitada <= self.qtd_disponivel

class ItemPedido:
    def __init__(self, produto: Produto, quantidade):
        self.produto = produto
        self.quantidade = quantidade
        self.preco_unitario = produto.preco_kg

    def validar_quantidade(self):
        if self.quantidade < QTD_MINIMA_PRODUTO:
            raise RegraNegocioError(f"Mínimo de {QTD_MINIMA_PRODUTO} kg por produto.")

    def verificar_disponibilidade(self):
        if not self.produto.verificar_disponibilidade(self.quantidade):
            raise RegraNegocioError("Estoque insuficiente para concluir o pedido.")

class Pedido:
    def __init__(self, empresa_compradora: EmpresaCompradora, endereco_entrega:Localizacao, tempo_entrega_dias):
        self.empresa_compradora = empresa_compradora
        self.empresa_marisqueira = None
        self.endereco_entrega = endereco_entrega
        self.tempo_entrega_dias = tempo_entrega_dias
        self.itens: list[ItemPedido] = []
        self.status = StatusPedido.RASCUNHO
        self.mensagem_ajuste = None

    @property
    def total(self):
        return sum(item.quantidade * item.preco_unitario for item in self.itens)

    def adicionar_item(self, produto:Produto, quantidade):
        if self.status is not StatusPedido.RASCUNHO:
            raise RegraNegocioError("Um pedido já enviado não pode receber novos itens.")

        if self.empresa_marisqueira and produto.empresa is not self.empresa_marisqueira:
            raise RegraNegocioError("Todos os itens de um pedido devem ser da mesma loja.")

        if any(item.produto == produto for item in self.itens):
            raise RegraNegocioError("Este produto já foi adicionado ao pedido.")
        
        novo_item = ItemPedido(produto, quantidade)

        novo_item.validar_quantidade()
        novo_item.verificar_disponibilidade()
        self.itens.append(novo_item)
        self.empresa_marisqueira = produto.empresa

class Avaliacao:
    def __init__(self, empresa_compradora:EmpresaCompradora, empresa_marisqueira:EmpresaMarisqueira, pedido:Pedido):
        self.empresa_compradora = empresa_compradora
        self.empresa_marisqueira = empresa_marisqueira
        self.pedido = pedido
        self.nota = None

    def registrar_nota(self, nota):
        if not isinstance(nota, int) or isinstance(nota, bool) or not 1 <= nota <= 5:
            raise RegraNegocioError("A nota deve ser um número inteiro de 1 a 5.")
        self.nota = nota
        self.empresa_marisqueira.avaliacoes.append(self)

class EmpresaMarisqueira:
    def __init__(self, id, nome, responsavel, localizacao:Localizacao):
        self.id = id
        self.nome = nome
        self.responsavel = responsavel
        self.localizacao = localizacao

        self.produtos:list[Produto] = []
        self.pedidos_recebidos = []
        self.avaliacoes = []

    def media_avaliacoes(self):
        notas = [a.nota for a in self.avaliacoes]
        return sum(notas) / len(notas) if notas else 0.0

    def _validar_pedido(self, pedido:Pedido, *status_validos):
        if pedido.empresa_marisqueira is not self:
            raise RegraNegocioError("Este pedido não pertence a esta empresa.")
        if pedido.status not in status_validos:
            raise RegraNegocioError(f"Operação inválida para um pedido '{pedido.status.value}'.")

    def cadastrar_produto(self, descricao, categoria:CategoriaProduto, preco_kg, qtd_disponivel, foto=None):
        
        if any(p.descricao.lower() == descricao.lower() and p.categoria == categoria for p in self.produtos):
            raise RegraNegocioError(f"{descricao} já está cadastrado nesta categoria.")

        novo_produto = Produto(descricao, categoria, preco_kg, qtd_disponivel, self, foto)
        self.produtos.append(novo_produto)
        return novo_produto

    def alterar_quantidade(self, produto:Produto, quantidade):
        if produto not in self.produtos:
            raise RegraNegocioError("Só é possível alterar produtos da própria empresa.")
        produto.atualizar_quantidade(quantidade)

    def receber_pedido(self, pedido:Pedido):
        self._validar_pedido(pedido, StatusPedido.RASCUNHO)

        if not pedido.itens:
            raise RegraNegocioError("O pedido não tem itens.")
        
        pedido.status = StatusPedido.PENDENTE
        self.pedidos_recebidos.append(pedido)

    def aceitar_pedido(self, pedido:Pedido):
        self._validar_pedido(pedido, StatusPedido.PENDENTE)

        for item in pedido.itens:
            item.validar_quantidade()
            item.verificar_disponibilidade()
        for item in pedido.itens:
            item.produto.atualizar_quantidade(item.produto.qtd_disponivel - item.quantidade, via_venda=True)

        pedido.status = StatusPedido.ACEITO

    def rejeitar_pedido(self, pedido:Pedido):
        self._validar_pedido(pedido, StatusPedido.PENDENTE)
        pedido.status = StatusPedido.REJEITADO

    def solicitar_ajuste(self, pedido:Pedido, mensagem):
        self._validar_pedido(pedido, StatusPedido.PENDENTE)
        if not mensagem:
            raise RegraNegocioError("Informe o que precisa ser ajustado")
        
        pedido.mensagem_ajuste = mensagem
        pedido.status = StatusPedido.AJUSTE_SOLICITADO 

    def atualizar_status_entrega(self, pedido:Pedido):
        self._validar_pedido(pedido, *PROXIMO_STATUS)
        pedido.status = PROXIMO_STATUS[pedido.status]

class EmpresaCompradora:
    def __init__(self, id, nome, localizacao:Localizacao):
        self.id = id
        self.nome = nome
        self.localizacao = localizacao

        self.pedidos_realizados = []

    def consultar_produtos(self, empresas:list[EmpresaMarisqueira], nome=None, categoria=None, localizacao=None, empresa=None, estrelas_min=None, ordenar_por=None):
        resultado:list[Produto] = []

        for emp in empresas:
            
            if localizacao and localizacao.lower() not in str(emp.localizacao).lower():
                continue
            if empresa and empresa.lower() not in emp.nome.lower():
                continue
            if estrelas_min and emp.media_avaliacoes() < estrelas_min:
                continue
            for p in emp.produtos:
                if nome and nome.lower() not in p.descricao.lower():
                    continue
                if categoria and p.categoria != categoria:
                    continue
                resultado.append(p)

        if ordenar_por == OrdenarPor.MENOR_PRECO:
            resultado.sort(key=lambda p: p.preco_kg)
        elif ordenar_por == OrdenarPor.MELHOR_AVALIACAO:
            resultado.sort(key=lambda p: p.empresa.media_avaliacoes(), reverse=True)
        elif ordenar_por == OrdenarPor.PROXIMIDADE:
            resultado = list(ordenar_distancias(self, resultado).keys())

        return resultado

    def comparar_produtos(self, produtos):
        if len(produtos) < 2:
            raise RegraNegocioError("Selecione pelo menos dois produtos para comparar.")
        return [
            {
                "produto": p.descricao,
                "categoria": p.categoria.value,
                "empresa": p.empresa.nome,
                "preco_kg": p.preco_kg,
                "disponivel_kg": p.qtd_disponivel,
                "avaliacao": p.empresa.media_avaliacoes()
            } 
            for p in produtos]

    def realizar_pedido(self, itens:list[ItemPedido], endereco_entrega, tempo_entrega_dias):
        pedido = Pedido(self, endereco_entrega, tempo_entrega_dias)
        for produto, quantidade in itens:
            pedido.adicionar_item(produto, quantidade)
        if not pedido.itens:
            raise RegraNegocioError("Seu carrinho está vazio.")
        pedido.empresa_marisqueira.receber_pedido(pedido)
        self.pedidos_realizados.append(pedido)

        return pedido

    def avaliar_empresa(self, pedido, nota):
        if pedido not in self.pedidos_realizados:
            raise RegraNegocioError("Só é possível avaliar a empresa de um pedido seu.")
        if pedido.status != StatusPedido.ENTREGUE:
            raise RegraNegocioError("A avaliação só é liberada depois da entrega.")
        if any(a.pedido == pedido for a in pedido.empresa_marisqueira.avaliacoes):
            raise RegraNegocioError("Esse pedido já foi avaliado.")

        avaliacao = Avaliacao(self, pedido.empresa_marisqueira, pedido)
        avaliacao.registrar_nota(nota)

        return avaliacao