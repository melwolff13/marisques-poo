# Marisqueiras da Ilha - Plataforma Marisquês

Modelagem em Programação Orientada a Objetos de um sistema de **comercialização direta de mariscos** entre empresas das marisqueiras e empresas compradoras (modelo B2B). O caso inicial de estudo é a Vila Maresia, em Raposa (MA). Trabalho da disciplina de POO (UNDB).

O fluxo básico do negócio é:

```
consulta → seleção → pedido → análise (aceitar / rejeitar / solicitar ajuste) → preparo → entrega → avaliação
```

## Arquivos

| Arquivo | O que é |
|---|---|
| `src/models.py` | As classes e as regras de negócio (o núcleo do trabalho). |
| `src/algoritmo_distancia.py` | Calcula a distância entre endereços (geopy + Nominatim), usada na ordenação por proximidade. |
| `testar.py` | Sistema simples de terminal para testar o modelo. Os dados ficam só em memória. |
| `requirements.txt` | Bibliotecas externas necessárias. |

## Modelagem

**Classes principais**

- `EmpresaMarisqueira`: cadastra produtos, altera estoque, recebe, aceita, rejeita e pede ajuste em pedidos, atualiza o status da entrega. Guarda também suas avaliações e a média.
- `EmpresaCompradora`: consulta e compara produtos, realiza pedidos e avalia a empresa depois da entrega.
- `Produto`: descrição, categoria (fresco ou congelado), preço por kg e quantidade disponível.
- `Pedido` e `ItemPedido`: um pedido tem vários itens, todos da mesma empresa.
- `Avaliacao`: nota de 1 a 5 dada pela compradora à marisqueira.

**Apoio:** `Localizacao` (dataclass), `Estado`, `CategoriaProduto`, `StatusPedido`, `OrdenarPor` e `RegraNegocioError`.

**Principais regras implementadas**

- Venda por quilograma, com mínimo de **25 kg por produto** do pedido.
- Produto fresco e produto congelado são cadastros diferentes.
- Um pedido pode ter vários produtos, mas **de uma única empresa**.
- Se a quantidade pedida for maior que a disponível, o pedido é impedido.
- O estoque só é baixado quando a marisqueira **aceita** o pedido. O preço do item fica fixado no momento do pedido.
- A entrega segue a ordem: aceito → em preparo → em rota → entregue.
- A avaliação (1 a 5) só é liberada com o pedido entregue, e cada pedido pode ser avaliado uma vez.
- A busca filtra por nome, categoria, localização, empresa e estrelas, e ordena por menor preço, melhor avaliação ou proximidade.
- Pagamento está fora do escopo.

## Como rodar

Requisitos: **Python 3.9 ou superior**.

1. Clone esse repositório
    ```
    git clone https://github.com/melwolff13/marisques-poo.git
    ```

2. (Recomendado) Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Linux/macOS
   .venv\Scripts\activate         # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Execute:

   ```bash
   python testar.py
   ```

## Como usar o sistema de teste

Ao iniciar, o sistema já carrega 3 marisqueiras (Maria Mariscos, Mariscos da Rita e Mariscos da Lurdes) e 1 compradora (Restaurante Maré). Tudo é feito por menus numerados: digite o número da opção e tecle Enter; `0` volta ou sai.

Roteiro sugerido:

1. **Menu principal → Entrar como empresa** e escolha o *Restaurante Maré*.
2. **Consultar produtos** (aperte Enter para pular os filtros) e depois **Realizar pedido**: escolha o produto, informe a quantidade (mínimo 25 kg), Enter para usar o endereço da empresa e informe o tempo de entrega em dias.
3. Volte (`0`), entre como *Maria Mariscos* e use **Aceitar pedido** e depois **Atualizar status da entrega** três vezes, até "entregue".
4. Entre de novo como *Restaurante Maré* e use **Avaliar empresa de um pedido**.

Para ver as regras funcionando, tente também: pedir menos de 25 kg, pedir mais do que o estoque, juntar produtos de empresas diferentes no mesmo pedido, avaliar antes da entrega e avaliar com nota fora de 1 a 5. O sistema recusa e explica o motivo.

## Observações

- Os dados ficam em memória: ao fechar o programa, tudo é perdido. Não há login; a empresa é escolhida em uma lista.
- A ordenação dos produtos por proximidade precisa de internet, porque o `algoritmo_distancia.py` consulta o serviço Nominatim (OpenStreetMap). Sem internet, a distância não será calculada, mas os produtos ainda serão exibidos (sem ordenação).
