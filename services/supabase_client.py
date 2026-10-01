import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config_cloud import SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, CLOUD_ACCESS_ENABLED

SUPABASE_KEY = SUPABASE_PUBLISHABLE_KEY
try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get("SUPABASE_URL") or SUPABASE_URL
    SUPABASE_KEY = (
        st.secrets.get("SUPABASE_PUBLISHABLE_KEY")
        or st.secrets.get("SUPABASE_KEY")
        or SUPABASE_KEY
    )
except Exception:
    pass

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _get(tabela, params=None):
    if not CLOUD_ACCESS_ENABLED:
        return []
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception as e:
        print(f"[Supabase] Erro em {tabela}: {e}")
        return []


def listar_farmacias():
    return _get("farmacias", {"select": "*", "order": "id"}) or []


def obter_farmacia(fid):
    r = _get("farmacias", {"select": "*", "id": f"eq.{fid}"})
    return r[0] if r else None


def vendas_hoje(farmacia_id=None):
    hoje = datetime.now().strftime("%Y-%m-%d")
    params = {"select": "*", "data": f"gte.{hoje}T00:00:00", "order": "data.desc"}
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get("vendas", params) or []


def vendas_ultimos_dias(dias=7, farmacia_id=None):
    inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    params = {"select": "*", "data": f"gte.{inicio}T00:00:00", "order": "data.desc"}
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get("vendas", params) or []


def resumo_por_farmacia(dias=1):
    farmacias = listar_farmacias()
    vendas = vendas_ultimos_dias(dias)
    resumo = {}
    for f in farmacias:
        fid = f["id"]
        v_f = [v for v in vendas if v.get("farmacia_id") == fid]
        resumo[fid] = {
            "farmacia": f,
            "num_vendas": len(v_f),
            "total": sum(v.get("total", 0) for v in v_f),
            "ticket_medio": (sum(v.get("total", 0) for v in v_f) / len(v_f)) if v_f else 0,
            "formas": _contar_formas(v_f),
            "vendedores": _contar_vendedores(v_f),
        }
    return resumo


def _contar_formas(vendas):
    c = {}
    for v in vendas:
        f = v.get("forma_pagamento") or "Nao especificado"
        c[f] = c.get(f, 0) + 1
    return c


def _contar_vendedores(vendas):
    c = {}
    for v in vendas:
        u = v.get("utilizador_nome") or "Desconhecido"
        c[u] = c.get(u, 0) + 1
    return c


def vendas_por_dia(dias=30, farmacia_id=None):
    vendas = vendas_ultimos_dias(dias, farmacia_id)
    por_dia = {}
    for v in vendas:
        d = v.get("data", "")[:10]
        if not d:
            continue
        if d not in por_dia:
            por_dia[d] = {"total": 0, "num": 0}
        por_dia[d]["total"] += v.get("total", 0)
        por_dia[d]["num"] += 1
    return dict(sorted(por_dia.items()))


def vendas_por_hora(dias=1, farmacia_id=None):
    vendas = vendas_ultimos_dias(dias, farmacia_id)
    por_hora = {h: {"total": 0, "num": 0} for h in range(24)}
    for v in vendas:
        d = v.get("data", "")
        if "T" not in d:
            continue
        try:
            h = int(d[11:13])
            por_hora[h]["total"] += v.get("total", 0)
            por_hora[h]["num"] += 1
        except Exception:
            continue
    return por_hora


def _get_paginado(tabela, params=None, pagina=1000):
    todos = []
    offset = 0
    while True:
        p = dict(params or {})
        p["limit"] = pagina
        p["offset"] = offset
        lote = _get(tabela, p) or []
        todos.extend(lote)
        if len(lote) < pagina:
            break
        offset += pagina
        if offset > 50000:
            break
    return todos


def _intervalo_mes(mes, ano):
    inicio = f"{ano}-{mes:02d}-01T00:00:00"
    if mes == 12:
        prox = f"{ano + 1}-01-01T00:00:00"
    else:
        prox = f"{ano}-{mes + 1:02d}-01T00:00:00"
    return inicio, prox


def vendas_por_mes(mes, ano, farmacia_id=None):
    inicio, fim = _intervalo_mes(mes, ano)
    params = {
        "select": "id,total,farmacia_id,data,forma_pagamento",
        "data": [f"gte.{inicio}", f"lt.{fim}"],
        "order": "data.asc",
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("vendas", params) or []


def resumo_por_farmacia_mes(mes, ano):
    farmacias = listar_farmacias()
    vendas = vendas_por_mes(mes, ano)
    resumo = {}
    for f in farmacias:
        fid = f["id"]
        v_f = [v for v in vendas if v.get("farmacia_id") == fid]
        total = sum(v.get("total", 0) or 0 for v in v_f)
        num = len(v_f)
        resumo[fid] = {
            "farmacia": f,
            "num_vendas": num,
            "total": total,
            "ticket_medio": (total / num) if num > 0 else 0,
        }
    return resumo


def anos_disponiveis():
    from datetime import datetime as _dt
    ano_atual = _dt.now().year
    return list(range(ano_atual, 2022, -1))


def criar_meta(mes, ano, farmacia_id, orcamento, observacoes="", definido_por=""):
    if not CLOUD_ACCESS_ENABLED:
        return False
    import requests as _req
    mes_str = f"{ano}-{mes:02d}"
    params = {"select": "id", "mes": f"eq.{mes_str}", "farmacia_id": f"eq.{farmacia_id}"}
    r = _get("metas_farmacia", params)
    dados = {
        "mes": mes_str,
        "farmacia_id": farmacia_id,
        "orcamento_mes": float(orcamento),
        "observacoes": observacoes,
        "definido_por": definido_por,
        "atualizado_em": datetime.now().isoformat(),
    }
    url = f"{SUPABASE_URL}/rest/v1/metas_farmacia"
    try:
        if r:
            meta_id = r[0]["id"]
            resp = _req.patch(f"{url}?id=eq.{meta_id}", headers=HEADERS, json=dados, timeout=10)
        else:
            dados["criado_em"] = datetime.now().isoformat()
            resp = _req.post(url, headers=HEADERS, json=dados, timeout=10)
        return resp.status_code in (200, 201, 204)
    except Exception as e:
        print(f"[Supabase] Erro ao criar meta: {e}")
        return False


def apagar_meta(meta_id):
    if not CLOUD_ACCESS_ENABLED:
        return False
    import requests as _req
    url = f"{SUPABASE_URL}/rest/v1/metas_farmacia?id=eq.{meta_id}"
    try:
        resp = _req.delete(url, headers=HEADERS, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"[Supabase] Erro ao apagar meta: {e}")
        return False


def ultima_venda_por_farmacia():
    from datetime import datetime as _dt
    farmacias = listar_farmacias()
    resultado = {}
    hoje = _dt.now().date()
    for f in farmacias:
        fid = f["id"]
        params = {"select": "data,total", "farmacia_id": f"eq.{fid}", "order": "data.desc", "limit": 5}
        vendas = _get("vendas", params) or []
        if not vendas:
            resultado[fid] = {"data": None, "dias_atras": None, "num": 0}
            continue
        ultima_data = vendas[0]["data"][:10]
        try:
            dt = _dt.strptime(ultima_data, "%Y-%m-%d").date()
            dias_atras = (hoje - dt).days
        except Exception:
            dias_atras = None
        resultado[fid] = {"data": ultima_data, "dias_atras": dias_atras, "num": len(vendas)}
    return resultado


def ultima_venda_global():
    params = {"select": "data", "order": "data.desc", "limit": 1}
    r = _get("vendas", params)
    if r:
        return r[0]["data"][:10]
    return None


def metas_activas(mes=None, ano=None):
    from datetime import datetime as _dt
    if not mes:
        mes = _dt.now().month
    if not ano:
        ano = _dt.now().year
    mes_str = f"{ano}-{mes:02d}"
    params = {"select": "*", "mes": f"eq.{mes_str}", "order": "id"}
    return _get("metas_farmacia", params) or []


def produtos_validade_proxima(dias=90):
    from datetime import datetime as _dt, timedelta
    hoje = _dt.now().date()
    limite = (hoje + timedelta(days=dias)).isoformat()
    params = {
        "select": "produto_nome,codigo_barras,numero_lote,data_validade,quantidade,farmacia_id",
        "data_validade": [f"gte.{hoje.isoformat()}", f"lte.{limite}"],
        "order": "data_validade.asc",
    }
    return _get("lotes", params) or []


def produtos_estoque_baixo():
    params = {"select": "nome,codigo_barras,estoque_atual,estoque_minimo,farmacia_id", "order": "estoque_atual.asc"}
    todos = _get("produtos", params) or []
    return [p for p in todos if (p.get("estoque_atual") or 0) <= (p.get("estoque_minimo") or 0)]


def turnos_com_diferenca(dias=7):
    from datetime import datetime as _dt, timedelta
    inicio = (_dt.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    params = {"select": "*", "data_abertura": f"gte.{inicio}T00:00:00", "order": "data_abertura.desc", "limit": 50}
    turnos = _get("turnos_caixa", params) or []
    return [t for t in turnos if abs(t.get("diferenca") or 0) >= 50000]


def tem_meta_definida(mes, ano):
    metas = metas_activas(mes, ano)
    return len(metas) > 0


def total_vendas_por_mes(mes, ano):
    vendas = vendas_por_mes(mes, ano)
    return sum(v.get("total", 0) or 0 for v in vendas)


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


# ============================================================
# ============ FUNCOES PARA FINANCEIRO (FASE 9.8) ============
# ============================================================

def listar_turnos_periodo(mes=None, ano=None, farmacia_id=None):
    """Lista turnos de caixa de um mes."""
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
        "select": "id,caixa_id,data_abertura,data_fecho,utilizador_nome,valor_inicial,total_vendas,total_dinheiro,total_tpa,total_contado,total_sistema,diferenca,estado,farmacia_id",
        "data_abertura": [f"gte.{inicio}", f"lt.{prox}"],
        "order": "data_abertura.desc",
        "limit": 500,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("turnos_caixa", params) or []


def resumo_turnos(mes=None, ano=None, farmacia_id=None):
    """Resumo financeiro dos turnos do mes."""
    turnos = listar_turnos_periodo(mes, ano, farmacia_id)
    fechados = [t for t in turnos if t.get("estado") == "FECHADO"]

    total_vendas = sum(t.get("total_vendas") or 0 for t in fechados)
    total_dinheiro = sum(t.get("total_dinheiro") or 0 for t in fechados)
    total_tpa = sum(t.get("total_tpa") or 0 for t in fechados)
    total_diferenca = sum(t.get("diferenca") or 0 for t in fechados)
    total_faltas = sum(abs(t.get("diferenca") or 0) for t in fechados if (t.get("diferenca") or 0) < 0)
    total_sobras = sum(t.get("diferenca") or 0 for t in fechados if (t.get("diferenca") or 0) > 0)

    return {
        "num_turnos": len(turnos),
        "num_fechados": len(fechados),
        "total_vendas": total_vendas,
        "total_dinheiro": total_dinheiro,
        "total_tpa": total_tpa,
        "total_diferenca": total_diferenca,
        "total_faltas": total_faltas,
        "total_sobras": total_sobras,
    }


def listar_depositos(mes=None, ano=None, farmacia_id=None):
    """Lista depositos bancarios de um mes."""
    from datetime import datetime as _dt
    if not mes:
        mes = _dt.now().month
    if not ano:
        ano = _dt.now().year

    inicio = f"{ano}-{mes:02d}-01"
    if mes == 12:
        prox = f"{ano + 1}-01-01"
    else:
        prox = f"{ano}-{mes + 1:02d}-01"

    params = {
        "select": "*",
        "data": [f"gte.{inicio}", f"lt.{prox}"],
        "order": "data.desc",
        "limit": 500,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("depositos", params) or []


def resumo_depositos(mes=None, ano=None, farmacia_id=None):
    """Resumo de depositos."""
    depos = listar_depositos(mes, ano, farmacia_id)
    total = sum(d.get("valor") or 0 for d in depos)
    pendentes = [d for d in depos if d.get("estado") == "PENDENTE_APROVACAO"]
    aprovados = [d for d in depos if d.get("estado") == "APROVADO"]
    registados = [d for d in depos if d.get("estado") == "REGISTADO"]

    return {
        "num_total": len(depos),
        "total_valor": total,
        "num_pendentes": len(pendentes),
        "num_aprovados": len(aprovados),
        "num_registados": len(registados),
    }


def listar_movimentos_saldo(mes=None, ano=None, farmacia_id=None):
    """Lista movimentos de saldo da farmacia."""
    from datetime import datetime as _dt
    if not mes:
        mes = _dt.now().month
    if not ano:
        ano = _dt.now().year

    inicio = f"{ano}-{mes:02d}-01"
    if mes == 12:
        prox = f"{ano + 1}-01-01"
    else:
        prox = f"{ano}-{mes + 1:02d}-01"

    params = {
        "select": "*",
        "data": [f"gte.{inicio}", f"lt.{prox}"],
        "order": "data.desc",
        "limit": 500,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("saldo_farmacia", params) or []


# ============================================================
# ============ FUNCOES PARA UTILIZADORES (FASE 9.8) ==========
# ============================================================

def listar_todos_utilizadores(farmacia_id=None):
    """Lista todos os utilizadores."""
    params = {
        "select": "id,nome,username,perfil,ativo,criado_em,ultimo_login,farmacia_id",
        "order": "nome.asc",
        "limit": 500,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("utilizadores", params) or []


def resumo_utilizadores(farmacia_id=None):
    """Resumo de utilizadores."""
    users = listar_todos_utilizadores(farmacia_id)
    activos = [u for u in users if u.get("ativo")]
    perfis = {}
    for u in users:
        p = u.get("perfil") or "desconhecido"
        perfis[p] = perfis.get(p, 0) + 1

    return {
        "total": len(users),
        "activos": len(activos),
        "inactivos": len(users) - len(activos),
        "perfis": perfis,
    }


def top_vendedores_mes(mes=None, ano=None, farmacia_id=None, limite=10):
    """Top N vendedores do mes (via vendas)."""
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
        "select": "utilizador_nome,total,data",
        "data": [f"gte.{inicio}", f"lt.{prox}"],
        "order": "data.asc",
        "limit": 5000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"

    vendas = _get_paginado("vendas", params) or []

    vendedores = {}
    for v in vendas:
        nome = v.get("utilizador_nome") or "Desconhecido"
        total = v.get("total") or 0
        if nome not in vendedores:
            vendedores[nome] = {"num_vendas": 0, "total": 0}
        vendedores[nome]["num_vendas"] += 1
        vendedores[nome]["total"] += total

    lista = [{"nome": k, **v} for k, v in vendedores.items()]
    lista.sort(key=lambda x: x["total"], reverse=True)
    return lista[:limite]


# ============================================================
# ============ FUNCOES PARA DIAGNOSTICO (FASE 9.9) ===========
# ============================================================

def diagnostico_sistema():
    """
    Verifica a saude do sistema:
    - Tabelas com dados
    - Farmacias a comunicar
    - Alertas criticos
    - Erros recentes
    """
    from datetime import datetime as _dt, timedelta

    problemas = []
    avisos = []
    info = []

    # 1. Verificar ligacao ao Supabase
    try:
        farmacias = listar_farmacias()
        if not farmacias:
            problemas.append({
                "area": "Base de dados",
                "problema": "Nenhuma farmacia encontrada no Supabase",
                "solucao": "Verificar se as farmacias foram criadas. Correr o SQL de setup.",
            })
        else:
            info.append(f"Supabase OK - {len(farmacias)} farmacias encontradas")
    except Exception as e:
        problemas.append({
            "area": "Ligacao",
            "problema": f"Erro ao ligar ao Supabase: {str(e)[:100]}",
            "solucao": "Verificar internet e credenciais em config_cloud.py / secrets",
        })
        return {
            "problemas": problemas,
            "avisos": avisos,
            "info": info,
            "tabelas": {},
        }

    # 2. Verificar tabelas principais
    tabelas = {}
    tabelas_check = [
        ("farmacias", "Farmacias"),
        ("vendas", "Vendas"),
        ("produtos", "Produtos"),
        ("lotes", "Lotes"),
        ("turnos_caixa", "Turnos de Caixa"),
        ("utilizadores", "Utilizadores"),
        ("facturas", "Facturas"),
        ("clientes", "Clientes"),
        ("metas_farmacia", "Metas/Orcamentos"),
        ("auditoria", "Log de Auditoria"),
    ]

    for nome, label in tabelas_check:
        try:
            r = _get(nome, {"select": "id", "limit": 1})
            tabelas[label] = "OK" if r else "vazio"
        except Exception:
            tabelas[label] = "ERRO"

    # 3. Farmacias a comunicar
    ultimas = ultima_venda_por_farmacia()
    sem_dados = 0
    for f in farmacias:
        fid = f["id"]
        info_f = ultimas.get(fid, {})
        dias = info_f.get("dias_atras")
        if dias is None:
            sem_dados += 1
        elif dias > 3:
            avisos.append({
                "area": "Comunicacao",
                "problema": f"{f['nome']} sem comunicar ha {dias} dias",
                "solucao": "Verificar ligacao de internet no PC dessa farmacia.",
            })

    if sem_dados == len(farmacias):
        avisos.append({
            "area": "Comunicacao",
            "problema": "Nenhuma farmacia enviou dados ainda",
            "solucao": "Instalar JAM Soft no PC de cada farmacia e clicar F9.",
        })

    # 4. Verificar produtos a vencer
    try:
        vencidos = produtos_validade_proxima(dias=0)
        urgentes = produtos_validade_proxima(dias=30)
        if vencidos:
            problemas.append({
                "area": "Stock",
                "problema": f"{len(vencidos)} produto(s) ja VENCIDO(S)",
                "solucao": "Retirar do stock imediatamente.",
            })
        if urgentes:
            avisos.append({
                "area": "Stock",
                "problema": f"{len(urgentes)} produto(s) a vencer em 30 dias",
                "solucao": "Promover vendas ou devolver ao fornecedor.",
            })
    except Exception:
        pass

    # 5. Verificar estoque baixo
    try:
        baixo = produtos_estoque_baixo()
        if baixo:
            avisos.append({
                "area": "Stock",
                "problema": f"{len(baixo)} produto(s) com estoque baixo",
                "solucao": "Fazer encomenda ao fornecedor.",
            })
    except Exception:
        pass

    # 6. Turnos com diferenca
    try:
        difs = turnos_com_diferenca(dias=7)
        for t in difs[:5]:
            dif = t.get("diferenca", 0)
            tipo = "SOBRA" if dif > 0 else "FALTA"
            avisos.append({
                "area": "Caixa",
                "problema": f"{t.get('utilizador_nome', '?')} - {tipo} de {abs(dif):,.0f} Kz",
                "solucao": "Verificar contagem de notas.",
            })
    except Exception:
        pass

    return {
        "problemas": problemas,
        "avisos": avisos,
        "info": info,
        "tabelas": tabelas,
    }


def info_plataforma():
    """Informacao geral da plataforma."""
    from datetime import datetime as _dt

    return {
        "versao": "1.0 - Fase 9",
        "fases_concluidas": [
            "9.1 - Dashboard",
            "9.2 - Sincronizacao",
            "9.3 - Ranking",
            "9.4 - Alertas",
            "9.5 - Orcamentos",
            "9.6 - Vendas",
            "9.7 - Stock + Perdas",
            "9.8 - Financeiro + Utilizadores",
            "9.9 - Diagnostico + Definicoes",
        ],
        "supabase_url": SUPABASE_URL,
        "data_servidor": _dt.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
