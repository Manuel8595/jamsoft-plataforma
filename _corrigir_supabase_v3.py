conteudo_novo = '''

# ============================================================
# ============ FUNCOES PARA STOCK E PERDAS (FASE 9.7) ========
# ============================================================

def listar_produtos_stock(farmacia_id=None):
    """Lista todos os produtos com stock."""
    params = {
        "select": "id,nome,codigo_barras,principio_ativo,laboratorio,preco_custo,preco_venda,estoque_atual,estoque_minimo,categoria_nome,fornecedor_nome,farmacia_id",
        "order": "nome.asc",
        "limit": 5000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("produtos", params) or []


def listar_lotes(farmacia_id=None):
    """Lista todos os lotes."""
    params = {
        "select": "produto_nome,codigo_barras,numero_lote,data_validade,quantidade,farmacia_id",
        "order": "data_validade.asc",
        "limit": 5000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("lotes", params) or []


def produtos_estoque_baixo_filtrado(farmacia_id=None):
    """Produtos com estoque_atual <= estoque_minimo."""
    produtos = listar_produtos_stock(farmacia_id)
    return [
        p for p in produtos
        if (p.get("estoque_atual") or 0) <= (p.get("estoque_minimo") or 0)
    ]


def lotes_a_vencer(dias=90, farmacia_id=None):
    """Lotes a vencer nos próximos N dias."""
    from datetime import datetime as _dt, timedelta
    lotes = listar_lotes(farmacia_id)
    hoje = _dt.now().date()
    limite = hoje + timedelta(days=dias)

    resultado = []
    for l in lotes:
        dv_str = l.get("data_validade")
        if not dv_str:
            continue
        try:
            dv = _dt.strptime(dv_str[:10], "%Y-%m-%d").date()
            if dv <= limite:
                dias = (dv - hoje).days
                resultado.append({
                    **l,
                    "dias_restantes": dias,
                })
        except Exception:
            continue

    resultado.sort(key=lambda x: x.get("dias_restantes", 9999))
    return resultado


def resumo_stock(farmacia_id=None):
    """Resumo agregado do stock."""
    produtos = listar_produtos_stock(farmacia_id)
    total_produtos = len(produtos)
    total_unidades = sum(p.get("estoque_atual") or 0 for p in produtos)
    valor_custo = sum((p.get("estoque_atual") or 0) * (p.get("preco_custo") or 0) for p in produtos)
    valor_venda = sum((p.get("estoque_atual") or 0) * (p.get("preco_venda") or 0) for p in produtos)
    estoque_baixo = len([p for p in produtos if (p.get("estoque_atual") or 0) <= (p.get("estoque_minimo") or 0)])

    return {
        "total_produtos": total_produtos,
        "total_unidades": total_unidades,
        "valor_custo": valor_custo,
        "valor_venda": valor_venda,
        "margem_potencial": valor_venda - valor_custo,
        "estoque_baixo": estoque_baixo,
    }


def listar_perdas(mes=None, ano=None, farmacia_id=None):
    """Lista perdas do mês."""
    from datetime import datetime as _dt
    if not mes:
        mes = _dt.now().month
    if not ano:
        ano = _dt.now().year

    inicio = f"{ano}-{mes:02d}-01T00:00:00"
    if mes == 12:
        prox = f"{ano + 1}-01-01T00:00:00"
    else:
        prox = f"{ano}-{mes + 1:02d}-01T00:00:00"

    params = {
        "select": "id,data,tipo,produto_nome,quantidade,valor_perdido,motivo,utilizador_nome,farmacia_id",
        "data": [f"gte.{inicio}", f"lt.{prox}"],
        "order": "data.desc",
        "limit": 2000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("perdas", params) or []


def resumo_perdas(mes=None, ano=None, farmacia_id=None):
    """Resumo das perdas por tipo."""
    perdas = listar_perdas(mes, ano, farmacia_id)

    por_tipo = {}
    total_valor = 0
    for p in perdas:
        tipo = p.get("tipo") or "Outro"
        valor = p.get("valor_perdido") or 0
        if tipo not in por_tipo:
            por_tipo[tipo] = {"total": 0, "num": 0}
        por_tipo[tipo]["total"] += valor
        por_tipo[tipo]["num"] += 1
        total_valor += valor

    return {
        "total_valor": total_valor,
        "total_num": len(perdas),
        "por_tipo": por_tipo,
    }
'''

path = "services/supabase_client.py"
with open(path, "r", encoding="utf-8") as f:
    conteudo_atual = f.read()

if "def listar_produtos_stock" in conteudo_atual:
    print("JA EXISTE - nao adicionado novamente")
else:
    with open(path, "a", encoding="utf-8") as f:
        f.write(conteudo_novo)
    print(f"OK - adicionadas novas funcoes de stock/perdas ({len(conteudo_novo)} caracteres)")