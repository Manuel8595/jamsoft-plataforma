conteudo_novo = '''

# ============================================================
# ============ FUNCOES PARA VENDAS DETALHADAS (FASE 9.6) =====
# ============================================================

def vendas_detalhadas_mes(mes, ano, farmacia_id=None):
    """Vendas completas de um mes (com hora, forma pagamento, etc.)."""
    from datetime import datetime as _dt
    inicio = f"{ano}-{mes:02d}-01T00:00:00"
    if mes == 12:
        prox = f"{ano + 1}-01-01T00:00:00"
    else:
        prox = f"{ano}-{mes + 1:02d}-01T00:00:00"

    params = {
        "select": "id,total,data,forma_pagamento,farmacia_id,utilizador_nome",
        "data": [f"gte.{inicio}", f"lt.{prox}"],
        "order": "data.asc",
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("vendas", params) or []


def vendas_por_forma_pagamento(mes, ano, farmacia_id=None):
    """Totais agrupados por forma de pagamento."""
    vendas = vendas_detalhadas_mes(mes, ano, farmacia_id)
    formas = {}
    for v in vendas:
        f = v.get("forma_pagamento") or "Nao especificado"
        if f not in formas:
            formas[f] = {"total": 0, "num": 0}
        formas[f]["total"] += v.get("total", 0) or 0
        formas[f]["num"] += 1
    return formas


def vendas_por_dia_mes(mes, ano, farmacia_id=None):
    """Totais agrupados por dia do mes."""
    vendas = vendas_detalhadas_mes(mes, ano, farmacia_id)
    por_dia = {}
    for v in vendas:
        d = v.get("data", "")[:10]
        if not d:
            continue
        if d not in por_dia:
            por_dia[d] = {"total": 0, "num": 0}
        por_dia[d]["total"] += v.get("total", 0) or 0
        por_dia[d]["num"] += 1
    return dict(sorted(por_dia.items()))


def vendas_por_hora_mes(mes, ano, farmacia_id=None):
    """Totais agrupados por hora (0-23)."""
    vendas = vendas_detalhadas_mes(mes, ano, farmacia_id)
    por_hora = {h: {"total": 0, "num": 0} for h in range(24)}
    for v in vendas:
        d = v.get("data", "")
        if "T" not in d and " " not in d:
            continue
        try:
            if "T" in d:
                h = int(d[11:13])
            else:
                h = int(d[11:13])
            por_hora[h]["total"] += v.get("total", 0) or 0
            por_hora[h]["num"] += 1
        except Exception:
            continue
    return por_hora


def top_produtos_mes(mes, ano, limite=10, farmacia_id=None):
    """Top N produtos mais vendidos no mes."""
    # Buscar vendas do mes para pegar UUIDS
    vendas = vendas_detalhadas_mes(mes, ano, farmacia_id)
    venda_ids = [v["id"] for v in vendas]

    if not venda_ids:
        return []

    # Buscar itens de venda correspondentes
    params = {
        "select": "produto_nome,quantidade,preco_unitario,subtotal,venda_id_origem,farmacia_id",
        "order": "id.asc",
        "limit": 5000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"

    itens = _get_paginado("itens_venda", params) or []

    # Filtrar pelos que pertencem a vendas do mes
    itens_mes = [i for i in itens if i.get("venda_id_origem") in venda_ids]

    # Agrupar por produto
    produtos = {}
    for it in itens_mes:
        nome = it.get("produto_nome") or "Desconhecido"
        qtd = it.get("quantidade") or 0
        sub = it.get("subtotal") or 0
        if nome not in produtos:
            produtos[nome] = {"quantidade": 0, "total": 0}
        produtos[nome]["quantidade"] += qtd
        produtos[nome]["total"] += sub

    # Ordenar por quantidade
    lista = [
        {"nome": k, **v} for k, v in produtos.items()
    ]
    lista.sort(key=lambda x: x["quantidade"], reverse=True)
    return lista[:limite]


def top_clientes_mes(mes, ano, limite=10):
    """Top N clientes do mes (via facturas)."""
    inicio = f"{ano}-{mes:02d}-01T00:00:00"
    if mes == 12:
        prox = f"{ano + 1}-01-01T00:00:00"
    else:
        prox = f"{ano}-{mes + 1:02d}-01T00:00:00"

    params = {
        "select": "cliente_nome,total,data",
        "data": [f"gte.{inicio}", f"lt.{prox}"],
        "order": "data.asc",
    }
    facturas = _get_paginado("facturas", params) or []

    clientes = {}
    for f in facturas:
        nome = f.get("cliente_nome") or "Sem nome"
        total = f.get("total") or 0
        if nome not in clientes:
            clientes[nome] = {"compras": 0, "total": 0}
        clientes[nome]["compras"] += 1
        clientes[nome]["total"] += total

    lista = [
        {"nome": k, **v} for k, v in clientes.items()
    ]
    lista.sort(key=lambda x: x["total"], reverse=True)
    return lista[:limite]
'''

# Adicionar ao fim do ficheiro existente
path = "services/supabase_client.py"
with open(path, "r", encoding="utf-8") as f:
    conteudo_atual = f.read()

# Verificar se ja foi adicionado
if "def vendas_detalhadas_mes" in conteudo_atual:
    print("JA EXISTE - nao adicionado novamente")
else:
    with open(path, "a", encoding="utf-8") as f:
        f.write(conteudo_novo)
    print(f"OK - adicionadas novas funcoes ({len(conteudo_novo)} caracteres)")