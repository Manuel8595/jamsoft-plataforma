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


# ============================================================
# JWT DO UTILIZADOR LOGADO
# ============================================================

_JWT_UTILIZADOR = None


def definir_jwt(jwt):
    global _JWT_UTILIZADOR
    _JWT_UTILIZADOR = jwt


def limpar_jwt():
    global _JWT_UTILIZADOR
    _JWT_UTILIZADOR = None


def _headers():
    if _JWT_UTILIZADOR:
        return {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {_JWT_UTILIZADOR}",
            "Content-Type": "application/json",
        }
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _get(tabela, params=None):
    if not CLOUD_ACCESS_ENABLED:
        return []
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception as e:
        print(f"[Supabase] Erro em {tabela}: {e}")
        return []


def _post(tabela, dados):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"
    try:
        headers = _headers()
        headers["Prefer"] = "return=representation"
        r = requests.post(url, headers=headers, json=dados, timeout=10)
        return r.status_code in (200, 201, 204)
    except Exception as e:
        print(f"[Supabase] Erro POST {tabela}: {e}")
        return False


def _patch(tabela, filtro, dados):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}?{filtro}"
    try:
        r = requests.patch(url, headers=_headers(), json=dados, timeout=10)
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"[Supabase] Erro PATCH {tabela}: {e}")
        return False


def _delete(tabela, filtro):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}?{filtro}"
    try:
        r = requests.delete(url, headers=_headers(), timeout=10)
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"[Supabase] Erro DELETE {tabela}: {e}")
        return False


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


# ============================================================
# FARMACIAS
# ============================================================

def listar_farmacias():
    return _get("farmacias", {"select": "*", "order": "id"}) or []


def obter_farmacia(fid):
    r = _get("farmacias", {"select": "*", "id": f"eq.{fid}"})
    return r[0] if r else None


# ============================================================
# VENDAS
# ============================================================

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


def resumo_por_farmacia(dias=1):
    farmacias = listar_farmacias()
    vendas = vendas_ultimos_dias(dias)
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
            "formas": _contar_formas(v_f),
            "vendedores": _contar_vendedores(v_f),
        }
    return resumo


def vendas_por_dia(dias=30, farmacia_id=None):
    vendas = vendas_ultimos_dias(dias, farmacia_id)
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


def vendas_por_hora(dias=1, farmacia_id=None):
    vendas = vendas_ultimos_dias(dias, farmacia_id)
    por_hora = {h: {"total": 0, "num": 0} for h in range(24)}
    for v in vendas:
        d = v.get("data", "")
        if "T" not in d:
            continue
        try:
            h = int(d[11:13])
            por_hora[h]["total"] += v.get("total", 0) or 0
            por_hora[h]["num"] += 1
        except Exception:
            continue
    return por_hora


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
    ano_atual = datetime.now().year
    return list(range(ano_atual, 2022, -1))


def criar_meta(mes, ano, farmacia_id, orcamento, observacoes="", definido_por=""):
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
    if r:
        meta_id = r[0]["id"]
        return _patch("metas_farmacia", f"id=eq.{meta_id}", dados)
    else:
        dados["criado_em"] = datetime.now().isoformat()
        return _post("metas_farmacia", dados)


def apagar_meta(meta_id):
    return _delete("metas_farmacia", f"id=eq.{meta_id}")


def ultima_venda_por_farmacia():
    farmacias = listar_farmacias()
    resultado = {}
    hoje = datetime.now().date()
    for f in farmacias:
        fid = f["id"]
        params = {"select": "data,total", "farmacia_id": f"eq.{fid}", "order": "data.desc", "limit": 5}
        vendas = _get("vendas", params) or []
        if not vendas:
            resultado[fid] = {"data": None, "dias_atras": None, "num": 0}
            continue
        ultima_data = vendas[0]["data"][:10]
        try:
            dt = datetime.strptime(ultima_data, "%Y-%m-%d").date()
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
    if not mes:
        mes = datetime.now().month
    if not ano:
        ano = datetime.now().year
    mes_str = f"{ano}-{mes:02d}"
    params = {"select": "*", "mes": f"eq.{mes_str}", "order": "id"}
    return _get("metas_farmacia", params) or []


def produtos_validade_proxima(dias=90):
    hoje = datetime.now().date()
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
    inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
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
# VENDAS DETALHADAS
# ============================================================

def vendas_detalhadas_mes(mes, ano, farmacia_id=None):
    inicio, fim = _intervalo_mes(mes, ano)
    params = {
        "select": "id,total,data,forma_pagamento,farmacia_id,utilizador_nome",
        "data": [f"gte.{inicio}", f"lt.{fim}"],
        "order": "data.asc",
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("vendas", params) or []


def vendas_por_forma_pagamento(mes, ano, farmacia_id=None):
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
    vendas = vendas_detalhadas_mes(mes, ano, farmacia_id)
    por_hora = {h: {"total": 0, "num": 0} for h in range(24)}
    for v in vendas:
        d = v.get("data", "")
        if "T" not in d and " " not in d:
            continue
        try:
            h = int(d[11:13])
            por_hora[h]["total"] += v.get("total", 0) or 0
            por_hora[h]["num"] += 1
        except Exception:
            continue
    return por_hora


def top_produtos_mes(mes, ano, limite=10, farmacia_id=None):
    vendas = vendas_detalhadas_mes(mes, ano, farmacia_id)
    venda_ids = [v["id"] for v in vendas]
    if not venda_ids:
        return []
    params = {
        "select": "produto_nome,quantidade,preco_unitario,subtotal,venda_id_origem,farmacia_id",
        "order": "id.asc",
        "limit": 5000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    itens = _get_paginado("itens_venda", params) or []
    itens_mes = [i for i in itens if i.get("venda_id_origem") in venda_ids]
    produtos = {}
    for it in itens_mes:
        nome = it.get("produto_nome") or "Desconhecido"
        qtd = it.get("quantidade") or 0
        sub = it.get("subtotal") or 0
        if nome not in produtos:
            produtos[nome] = {"quantidade": 0, "total": 0}
        produtos[nome]["quantidade"] += qtd
        produtos[nome]["total"] += sub
    lista = [{"nome": k, **v} for k, v in produtos.items()]
    lista.sort(key=lambda x: x["quantidade"], reverse=True)
    return lista[:limite]


def top_clientes_mes(mes, ano, limite=10):
    inicio, fim = _intervalo_mes(mes, ano)
    params = {
        "select": "cliente_nome,total,data",
        "data": [f"gte.{inicio}", f"lt.{fim}"],
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
    lista = [{"nome": k, **v} for k, v in clientes.items()]
    lista.sort(key=lambda x: x["total"], reverse=True)
    return lista[:limite]


# ============================================================
# STOCK E PERDAS
# ============================================================

def listar_produtos_stock(farmacia_id=None):
    params = {
        "select": "id,nome,codigo_barras,principio_ativo,laboratorio,preco_custo,preco_venda,estoque_atual,estoque_minimo,categoria_nome,fornecedor_nome,farmacia_id",
        "order": "nome.asc",
        "limit": 5000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("produtos", params) or []


def listar_lotes(farmacia_id=None):
    params = {
        "select": "produto_nome,codigo_barras,numero_lote,data_validade,quantidade,farmacia_id",
        "order": "data_validade.asc",
        "limit": 5000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("lotes", params) or []


def produtos_estoque_baixo_filtrado(farmacia_id=None):
    produtos = listar_produtos_stock(farmacia_id)
    return [p for p in produtos if (p.get("estoque_atual") or 0) <= (p.get("estoque_minimo") or 0)]


def lotes_a_vencer(dias=90, farmacia_id=None):
    lotes = listar_lotes(farmacia_id)
    hoje = datetime.now().date()
    limite = hoje + timedelta(days=dias)
    resultado = []
    for l in lotes:
        dv_str = l.get("data_validade")
        if not dv_str:
            continue
        try:
            dv = datetime.strptime(dv_str[:10], "%Y-%m-%d").date()
            if dv <= limite:
                resultado.append({**l, "dias_restantes": (dv - hoje).days})
        except Exception:
            continue
    resultado.sort(key=lambda x: x.get("dias_restantes", 9999))
    return resultado


def resumo_stock(farmacia_id=None):
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
    if not mes:
        mes = datetime.now().month
    if not ano:
        ano = datetime.now().year
    inicio, fim = _intervalo_mes(mes, ano)
    params = {
        "select": "id,data,tipo,produto_nome,quantidade,valor_perdido,motivo,utilizador_nome,farmacia_id",
        "data": [f"gte.{inicio}", f"lt.{fim}"],
        "order": "data.desc",
        "limit": 2000,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("perdas", params) or []


def resumo_perdas(mes=None, ano=None, farmacia_id=None):
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
    return {"total_valor": total_valor, "total_num": len(perdas), "por_tipo": por_tipo}


# ============================================================
# FINANCEIRO E UTILIZADORES
# ============================================================

def listar_turnos_periodo(mes=None, ano=None, farmacia_id=None):
    if not mes:
        mes = datetime.now().month
    if not ano:
        ano = datetime.now().year
    inicio, fim = _intervalo_mes(mes, ano)
    params = {
        "select": "id,caixa_id,data_abertura,data_fecho,utilizador_nome,valor_inicial,total_vendas,total_dinheiro,total_tpa,total_contado,total_sistema,diferenca,estado,farmacia_id",
        "data_abertura": [f"gte.{inicio}", f"lt.{fim}"],
        "order": "data_abertura.desc",
        "limit": 500,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("turnos_caixa", params) or []


def resumo_turnos(mes=None, ano=None, farmacia_id=None):
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
    if not mes:
        mes = datetime.now().month
    if not ano:
        ano = datetime.now().year
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
    if not mes:
        mes = datetime.now().month
    if not ano:
        ano = datetime.now().year
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


def listar_todos_utilizadores(farmacia_id=None):
    params = {
        "select": "id,nome,username,perfil,ativo,criado_em,ultimo_login,farmacia_id",
        "order": "nome.asc",
        "limit": 500,
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("utilizadores", params) or []


def resumo_utilizadores(farmacia_id=None):
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
    if not mes:
        mes = datetime.now().month
    if not ano:
        ano = datetime.now().year
    inicio, fim = _intervalo_mes(mes, ano)
    params = {
        "select": "utilizador_nome,total,data",
        "data": [f"gte.{inicio}", f"lt.{fim}"],
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


def diagnostico_sistema():
    problemas = []
    avisos = []
    info = []
    try:
        farmacias = listar_farmacias()
        if not farmacias:
            problemas.append({
                "area": "Base de dados",
                "problema": "Nenhuma farmacia encontrada no Supabase",
                "solucao": "Verificar se as farmacias foram criadas.",
            })
        else:
            info.append(f"Supabase OK - {len(farmacias)} farmacias encontradas")
    except Exception as e:
        problemas.append({
            "area": "Ligacao",
            "problema": f"Erro ao ligar: {str(e)[:100]}",
            "solucao": "Verificar internet e credenciais.",
        })
        return {"problemas": problemas, "avisos": avisos, "info": info, "tabelas": {}}
    tabelas = {}
    tabelas_check = [
        ("farmacias", "Farmacias"),
        ("vendas", "Vendas"),
        ("produtos", "Produtos"),
        ("lotes", "Lotes"),
        ("turnos_caixa", "Turnos de Caixa"),
        ("utilizadores", "Utilizadores"),
        ("facturas", "Facturas"),
    ]
    for nome, label in tabelas_check:
        try:
            r = _get(nome, {"select": "id", "limit": 1})
            tabelas[label] = "OK" if r else "vazio"
        except Exception:
            tabelas[label] = "ERRO"
    return {"problemas": problemas, "avisos": avisos, "info": info, "tabelas": tabelas}


def info_plataforma():
    return {
        "versao": "1.0 - Segura",
        "fases_concluidas": [
            "Autenticacao Supabase Auth",
            "RLS activo",
            "Dados por farmacia",
        ],
        "supabase_url": SUPABASE_URL,
        "data_servidor": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }



# ============================================================
# ============ IA: SUGESTAO DE ORCAMENTOS ====================
# ============================================================

def sugerir_orcamento_farmacia(farmacia_id, mes, ano):
    """
    Sugere orçamento para uma farmácia num mês/ano com base em:
    - Mesmo mês do ano passado
    - Últimos 3 meses deste ano
    - Tendência (crescimento/queda)
    
    Retorna dict:
    {
        "sugestao": float,
        "base_ano_passado": float,
        "base_3meses": float,
        "tendencia": float,        # % por mês
        "meses_analisados": int,
        "metodo": str,             # "completo" ou "media_geral"
    }
    """
    from datetime import datetime as _dt, timedelta

    resultado = {
        "sugestao": 0.0,
        "base_ano_passado": 0.0,
        "base_3meses": 0.0,
        "tendencia": 0.0,
        "meses_analisados": 0,
        "metodo": "sem_dados",
    }

    # ── 1. Mês do ano passado ──
    vendas_ano_passado = vendas_por_mes(mes, ano - 1, farmacia_id)
    total_ano_passado = sum(v.get("total", 0) or 0 for v in vendas_ano_passado)

    # ── 2. Últimos 3 meses (antes do mês escolhido) ──
    meses_3 = []
    m_temp = mes
    a_temp = ano
    for i in range(3):
        m_temp -= 1
        if m_temp < 1:
            m_temp = 12
            a_temp -= 1
        vendas_m = vendas_por_mes(m_temp, a_temp, farmacia_id)
        total_m = sum(v.get("total", 0) or 0 for v in vendas_m)
        if total_m > 0:
            meses_3.append(total_m)

    media_3meses = sum(meses_3) / len(meses_3) if meses_3 else 0

    # ── 3. Tendência (crescimento ou queda) ──
    tendencia = 0.0
    if len(meses_3) >= 2:
        # Ordem cronológica (mais antigo primeiro)
        meses_ord = list(reversed(meses_3))
        if meses_ord[0] > 0:
            variacao_total = (meses_ord[-1] - meses_ord[0]) / meses_ord[0]
            tendencia = variacao_total / (len(meses_ord) - 1) * 100  # % por mês
            # Limitar entre -50% e +50% por mês
            tendencia = max(-50, min(50, tendencia))

    # ── 4. Sugestão ──
    sugestao = 0.0
    metodo = "sem_dados"

    if total_ano_passado > 0 and media_3meses > 0:
        # Média ponderada: 40% ano passado + 60% últimos meses
        base = (total_ano_passado * 0.4) + (media_3meses * 0.6)
        # Aplicar tendência
        sugestao = base * (1 + tendencia / 100)
        metodo = "completo"
    elif total_ano_passado > 0:
        sugestao = total_ano_passado
        metodo = "ano_passado"
    elif media_3meses > 0:
        sugestao = media_3meses * (1 + tendencia / 100)
        metodo = "ultimos_3meses"
    else:
        # ── 5. Fallback: média geral das outras farmácias ──
        todas = listar_farmacias()
        vendas_todas = []
        for f in todas:
            if f["id"] == farmacia_id:
                continue
            vm = vendas_por_mes(mes, ano, f["id"])
            tm = sum(v.get("total", 0) or 0 for v in vm)
            if tm > 0:
                vendas_todas.append(tm)
        if vendas_todas:
            sugestao = sum(vendas_todas) / len(vendas_todas)
            metodo = "media_geral"

    resultado["sugestao"] = round(sugestao, 2)
    resultado["base_ano_passado"] = round(total_ano_passado, 2)
    resultado["base_3meses"] = round(media_3meses, 2)
    resultado["tendencia"] = round(tendencia, 2)
    resultado["meses_analisados"] = len(meses_3)
    resultado["metodo"] = metodo

    return resultado



# ============================================================
# ============ CONFIGURACAO POR FARMACIA =====================
# ============================================================

def obter_config_farmacia(farmacia_id):
    """Obtém a configuração de uma farmácia."""
    r = _get("config_farmacia", {
        "select": "*",
        "farmacia_id": f"eq.{farmacia_id}",
        "limit": "1",
    })
    if r:
        return r[0]
    return {
        "farmacia_id": farmacia_id,
        "mostrar_dia": True,
        "mostrar_semana": True,
        "mostrar_mes": True,
        "mostrar_ano": True,
    }


def guardar_config_farmacia(farmacia_id, dia, semana, mes, ano):
    """Cria ou actualiza a configuração de uma farmácia."""
    dados = {
        "farmacia_id": farmacia_id,
        "mostrar_dia": bool(dia),
        "mostrar_semana": bool(semana),
        "mostrar_mes": bool(mes),
        "mostrar_ano": bool(ano),
        "updated_at": datetime.now().isoformat(),
    }

    # Verificar se já existe
    r = _get("config_farmacia", {
        "select": "id",
        "farmacia_id": f"eq.{farmacia_id}",
        "limit": "1",
    })

    if r:
        # Actualizar
        return _patch("config_farmacia", f"farmacia_id=eq.{farmacia_id}", dados)
    else:
        # Criar
        dados["created_at"] = datetime.now().isoformat()
        return _post("config_farmacia", dados)


def listar_todas_configs():
    """Retorna todas as configurações (dict: farmacia_id -> config)."""
    r = _get("config_farmacia", {"select": "*"}) or []
    return {c["farmacia_id"]: c for c in r}



# ============================================================
# ============ IA: ALERTAS AUTOMATICOS =======================
# ============================================================

def analisar_alertas_farmacia(farmacia_id, farmacia_nome):
    """
    Analisa uma farmácia e devolve lista de alertas.
    Tipos: CRITICO, AVISO, INFO
    """
    from datetime import datetime as _dt, timedelta

    alertas = []
    hoje = _dt.now().date()

    # ─── 1. Vendas dos últimos 7 dias ───
    try:
        vendas_7d = vendas_ultimos_dias(dias=7, farmacia_id=farmacia_id)
        total_7d = sum(v.get("total", 0) or 0 for v in vendas_7d)
        num_vendas_7d = len(vendas_7d)
    except Exception:
        total_7d = 0
        num_vendas_7d = 0

    # ─── 2. Média das últimas 4 semanas (28 dias) ───
    try:
        vendas_28d = vendas_ultimos_dias(dias=28, farmacia_id=farmacia_id)
        total_28d = sum(v.get("total", 0) or 0 for v in vendas_28d)
        media_semanal = total_28d / 4 if total_28d > 0 else 0
    except Exception:
        media_semanal = 0

    # Comparar semana actual com média
    if media_semanal > 0:
        variacao = ((total_7d - media_semanal) / media_semanal) * 100

        if variacao <= -50:
            alertas.append({
                "nivel": "CRITICO",
                "area": "Vendas",
                "titulo": f"{farmacia_nome} vendeu {abs(variacao):.0f}% abaixo da média",
                "detalhe": f"Média: {_fmt_kz_local(media_semanal)}/sem | Esta semana: {_fmt_kz_local(total_7d)}",
                "accao": "Verificar stock, preços ou ligar ao gerente.",
            })
        elif variacao <= -30:
            alertas.append({
                "nivel": "AVISO",
                "area": "Vendas",
                "titulo": f"{farmacia_nome} vendeu {abs(variacao):.0f}% abaixo da média",
                "detalhe": f"Média: {_fmt_kz_local(media_semanal)}/sem | Esta semana: {_fmt_kz_local(total_7d)}",
                "accao": "Acompanhar de perto.",
            })

    # ─── 3. Última venda ───
    try:
        ultima = ultima_venda_por_farmacia().get(farmacia_id, {})
        dias_atras = ultima.get("dias_atras")
        if dias_atras is not None:
            if dias_atras >= 2:
                alertas.append({
                    "nivel": "CRITICO",
                    "area": "Comunicação",
                    "titulo": f"{farmacia_nome} sem vender há {dias_atras} dias",
                    "detalhe": f"Última venda: {ultima.get('data', '?')}",
                    "accao": "Verificar PC, internet ou ligar ao gerente.",
                })
            elif dias_atras == 1:
                alertas.append({
                    "nivel": "AVISO",
                    "area": "Comunicação",
                    "titulo": f"{farmacia_nome} sem vender ontem",
                    "detalhe": f"Última venda: {ultima.get('data', '?')}",
                    "accao": "Confirmar se fechou o dia.",
                })
    except Exception:
        pass

    # ─── 4. Lotes a vencer (30 dias) ───
    try:
        validade = produtos_validade_proxima(dias=30)
        venc_loja = [v for v in validade if v.get("farmacia_id") == farmacia_id]
        if venc_loja:
            alertas.append({
                "nivel": "AVISO",
                "area": "Stock",
                "titulo": f"{farmacia_nome} tem {len(venc_loja)} lote(s) a vencer em 30 dias",
                "detalhe": f"Ex: {venc_loja[0].get('produto_nome', '?')}",
                "accao": "Promover ou devolver ao fornecedor.",
            })
    except Exception:
        pass

    # ─── 5. Lotes vencidos ───
    try:
        todos_lotes = listar_lotes(farmacia_id=farmacia_id)
        vencidos = []
        for l in todos_lotes:
            dv_str = l.get("data_validade")
            if not dv_str:
                continue
            try:
                dv = _dt.strptime(dv_str[:10], "%Y-%m-%d").date()
                if dv < hoje and (l.get("quantidade") or 0) > 0:
                    vencidos.append(l)
            except Exception:
                continue

        if vencidos:
            alertas.append({
                "nivel": "CRITICO",
                "area": "Stock",
                "titulo": f"{farmacia_nome} tem {len(vencidos)} lote(s) VENCIDO(S)",
                "detalhe": f"Ex: {vencidos[0].get('produto_nome', '?')}",
                "accao": "Retirar do stock imediatamente.",
            })
    except Exception:
        pass

    # ─── 6. Stock crítico ───
    try:
        produtos = listar_produtos_stock(farmacia_id=farmacia_id)
        criticos = [p for p in produtos if (p.get("estoque_atual") or 0) == 0]
        if criticos:
            alertas.append({
                "nivel": "AVISO",
                "area": "Stock",
                "titulo": f"{farmacia_nome} tem {len(criticos)} produto(s) em falta",
                "detalhe": f"Ex: {criticos[0].get('nome', '?')}",
                "accao": "Encomendar ao fornecedor.",
            })
    except Exception:
        pass

    # ─── 7. Diferenças de caixa (7 dias) ───
    try:
        turnos = listar_turnos_periodo(farmacia_id=farmacia_id)
        for t in turnos[:10]:
            dif = t.get("diferenca") or 0
            if abs(dif) >= 50000:
                tipo = "SOBRA" if dif > 0 else "FALTA"
                alertas.append({
                    "nivel": "AVISO",
                    "area": "Caixa",
                    "titulo": f"{farmacia_nome} tem {tipo} de {_fmt_kz_local(abs(dif))}",
                    "detalhe": f"Turno de {t.get('data_abertura', '?')[:10]}",
                    "accao": "Verificar contagem de notas.",
                })
    except Exception:
        pass

    return alertas


def analisar_alertas_geral():
    """Analisa todas as farmácias e devolve lista agregada."""
    farmacias = listar_farmacias()
    todos = []

    for f in farmacias:
        try:
            alertas_f = analisar_alertas_farmacia(f["id"], f["nome"])
            for a in alertas_f:
                a["farmacia_id"] = f["id"]
                a["farmacia_nome"] = f["nome"]
                todos.append(a)
        except Exception as e:
            print(f"[Alertas] Erro em {f.get('nome')}: {e}")

    # Ordenar: CRITICO primeiro, depois AVISO
    ordem = {"CRITICO": 0, "AVISO": 1, "INFO": 2}
    todos.sort(key=lambda x: ordem.get(x.get("nivel", "INFO"), 99))

    return todos


def _fmt_kz_local(valor):
    """Formatar Kz (cópia local, sem importar de moeda)."""
    try:
        return f"Kz {float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "Kz 0"

    

# ============================================================
# ============ RENTABILIDADE E SUGESTOES IA ==================
# ============================================================

def calcular_rentabilidade_farmacia(farmacia_id, ano):
    """
    Calcula rentabilidade de uma farmácia no ano + ciclos de 3 meses.
    Retorna dict com: margem, lucro, custo, ticket, sugestões.
    """
    from datetime import datetime as _dt

    resultado = {
        "ano": ano,
        "ciclos": {},          # {Q1: {...}, Q2: {...}, Q3: {...}, Q4: {...}}
        "ano_total": {
            "vendas": 0.0,
            "custo": 0.0,
            "lucro": 0.0,
            "margem_pct": 0.0,
            "num_vendas": 0,
            "ticket_medio": 0.0,
        },
        "sugestoes": [],
    }

    # ─── 1. Vendas por mês ───
    vendas_por_mes_cache = {}
    for m in range(1, 13):
        vendas_por_mes_cache[m] = vendas_por_mes(m, ano, farmacia_id)

    # ─── 2. Calcular totais por ciclo (3 meses) ───
    # Q1: Jan-Mar | Q2: Abr-Jun | Q3: Jul-Set | Q4: Out-Dez
    ciclos = {
        "Q1 (Jan-Mar)": [1, 2, 3],
        "Q2 (Abr-Jun)": [4, 5, 6],
        "Q3 (Jul-Set)": [7, 8, 9],
        "Q4 (Out-Dez)": [10, 11, 12],
    }

    total_ano_vendas = 0
    total_ano_custo = 0
    total_ano_num = 0

    for nome_ciclo, meses in ciclos.items():
        total_ciclo_vendas = 0
        total_ciclo_num = 0
        total_ciclo_custo = 0

        for m in meses:
            vendas_m = vendas_por_mes_cache[m]
            vendas_m_total = sum(v.get("total", 0) or 0 for v in vendas_m)
            total_ciclo_vendas += vendas_m_total
            total_ciclo_num += len(vendas_m)

            # Calcular custo dos produtos vendidos no mês
            for v in vendas_m:
                custo_venda = _calcular_custo_venda(v.get("id"))
                total_ciclo_custo += custo_venda

        lucro_ciclo = total_ciclo_vendas - total_ciclo_custo
        margem_ciclo = (lucro_ciclo / total_ciclo_vendas * 100) if total_ciclo_vendas > 0 else 0
        ticket_ciclo = (total_ciclo_vendas / total_ciclo_num) if total_ciclo_num > 0 else 0

        resultado["ciclos"][nome_ciclo] = {
            "vendas": round(total_ciclo_vendas, 2),
            "custo": round(total_ciclo_custo, 2),
            "lucro": round(lucro_ciclo, 2),
            "margem_pct": round(margem_ciclo, 2),
            "num_vendas": total_ciclo_num,
            "ticket_medio": round(ticket_ciclo, 2),
        }

        total_ano_vendas += total_ciclo_vendas
        total_ano_custo += total_ciclo_custo
        total_ano_num += total_ciclo_num

    lucro_ano = total_ano_vendas - total_ano_custo
    margem_ano = (lucro_ano / total_ano_vendas * 100) if total_ano_vendas > 0 else 0
    ticket_ano = (total_ano_vendas / total_ano_num) if total_ano_num > 0 else 0

    resultado["ano_total"] = {
        "vendas": round(total_ano_vendas, 2),
        "custo": round(total_ano_custo, 2),
        "lucro": round(lucro_ano, 2),
        "margem_pct": round(margem_ano, 2),
        "num_vendas": total_ano_num,
        "ticket_medio": round(ticket_ano, 2),
    }

    # ─── 3. Sugestões IA ───
    sugestoes = []

    # Margem baixa
    if margem_ano < 20 and total_ano_vendas > 0:
        sugestoes.append({
            "nivel": "CRITICO",
            "titulo": f"Margem muito baixa ({margem_ano:.1f}%)",
            "detalhe": "Preços de venda podem estar demasiado baixos.",
            "accao": "Rever preços ou negociar melhores condições com fornecedores.",
        })
    elif margem_ano < 30 and total_ano_vendas > 0:
        sugestoes.append({
            "nivel": "AVISO",
            "titulo": f"Margem modesta ({margem_ano:.1f}%)",
            "detalhe": "Margem abaixo do ideal (30%+).",
            "accao": "Promover produtos com margem alta.",
        })

    # Ticket médio baixo
    if 0 < ticket_ano < 300:
        sugestoes.append({
            "nivel": "AVISO",
            "titulo": f"Ticket médio baixo ({_fmt_kz_local(ticket_ano)})",
            "detalhe": "Clientes compram poucos produtos por venda.",
            "accao": "Sugerir produtos complementares no PDV.",
        })

    # Ciclo em queda
    ciclos_ord = ["Q1 (Jan-Mar)", "Q2 (Abr-Jun)", "Q3 (Jul-Set)", "Q4 (Out-Dez)"]
    valores_ciclos = [resultado["ciclos"][c]["vendas"] for c in ciclos_ord]
    valores_nao_zero = [v for v in valores_ciclos if v > 0]

    if len(valores_nao_zero) >= 2:
        if valores_nao_zero[-1] < valores_nao_zero[-2] * 0.8:
            sugestoes.append({
                "nivel": "CRITICO",
                "titulo": "Vendas em queda no último ciclo",
                "detalhe": f"Caiu de {_fmt_kz_local(valores_nao_zero[-2])} para {_fmt_kz_local(valores_nao_zero[-1])}",
                "accao": "Investigar motivo — stock, preços, concorrência.",
            })

    # Stock crítico
    try:
        produtos = listar_produtos_stock(farmacia_id=farmacia_id)
        sem_stock = [p for p in produtos if (p.get("estoque_atual") or 0) == 0]
        if sem_stock:
            sugestoes.append({
                "nivel": "AVISO",
                "titulo": f"{len(sem_stock)} produto(s) em falta",
                "detalhe": f"Ex: {sem_stock[0].get('nome', '?')}",
                "accao": "Encomendar ao fornecedor.",
            })
    except Exception:
        pass

    # Sem vendas
    if total_ano_vendas == 0:
        sugestoes.append({
            "nivel": "INFO",
            "titulo": "Sem vendas registadas este ano",
            "detalhe": "Farmácia ainda não operou ou é de teste.",
            "accao": "Verificar sincronização do PC.",
        })

    resultado["sugestoes"] = sugestoes

    return resultado


def _calcular_custo_venda(venda_id):
    """Calcula o custo dos produtos vendidos numa venda."""
    if not venda_id:
        return 0.0

    # Buscar itens da venda
    itens = _get("itens_venda", {
        "select": "produto_id,quantidade",
        "venda_id": f"eq.{venda_id}",
    }) or []

    custo_total = 0.0
    for it in itens:
        pid = it.get("produto_id")
        qtd = it.get("quantidade") or 0
        if not pid:
            continue

        # Buscar preço de custo
        prod = _get("produtos", {
            "select": "preco_custo",
            "id": f"eq.{pid}",
            "limit": "1",
        })
        if prod:
            preco_custo = prod[0].get("preco_custo") or 0
            custo_total += preco_custo * qtd

    return custo_total


def calcular_rentabilidade_geral(ano):
    """Calcula rentabilidade de todas as farmácias agregada."""
    farmacias = listar_farmacias()
    resultado = {}

    for f in farmacias:
        try:
            resultado[f["id"]] = calcular_rentabilidade_farmacia(f["id"], ano)
        except Exception as e:
            print(f"[Rentabilidade] Erro em {f.get('nome')}: {e}")
            resultado[f["id"]] = None

    return resultado

    

# ============================================================
# ============ IA: APRENDIZAGEM COM AJUSTES DO CEO ===========
# ============================================================

def guardar_ajuste_ceo(farmacia_id, mes, ano, sugestao_ia, valor_aceito, notas=""):
    """
    Guarda um ajuste do CEO.
    A IA usa isto para aprender padrões.
    """
    try:
        # Calcular % de diferença
        diferenca = 0.0
        if sugestao_ia > 0:
            diferenca = ((valor_aceito - sugestao_ia) / sugestao_ia) * 100

        dados = {
            "farmacia_id": farmacia_id,
            "mes": mes,
            "ano": ano,
            "sugestao_ia": float(sugestao_ia),
            "valor_aceito": float(valor_aceito),
            "diferenca_pct": round(diferenca, 2),
            "notas": notas,
        }

        return _post("ajustes_ceo", dados)
    except Exception as e:
        print(f"[Ajustes] Erro ao guardar: {e}")
        return False


def obter_padrao_ajuste(farmacia_id, mes):
    """
    Calcula o padrão de ajuste para uma farmácia e mês.
    Retorna % média de ajuste com base em ajustes anteriores.
    """
    try:
        r = _get("ajustes_ceo", {
            "select": "diferenca_pct",
            "farmacia_id": f"eq.{farmacia_id}",
            "mes": f"eq.{mes}",
        })

        if not r:
            return None

        valores = [a.get("diferenca_pct", 0) for a in r if a.get("diferenca_pct") is not None]
        if not valores:
            return None

        # Média
        media = sum(valores) / len(valores)
        return {
            "media_pct": round(media, 2),
            "num_ajustes": len(valores),
        }
    except Exception as e:
        print(f"[Ajustes] Erro ao calcular padrao: {e}")
        return None


def sugerir_com_aprendizagem(farmacia_id, mes, ano):
    """
    Combina a sugestão base com o padrão aprendido.
    Retorna dict com sugestão ajustada.
    """
    # Sugestão base
    base = sugerir_orcamento_farmacia(farmacia_id, mes, ano)

    # Padrão aprendido
    padrao = obter_padrao_ajuste(farmacia_id, mes)

    resultado = {
        "sugestao_base": base.get("sugestao", 0),
        "sugestao_final": base.get("sugestao", 0),
        "ajuste_pct": 0.0,
        "tem_historico": bool(padrao),
        "num_ajustes": 0,
        "metodo": base.get("metodo", ""),
        "base_ano_passado": base.get("base_ano_passado", 0),
        "base_3meses": base.get("base_3meses", 0),
        "tendencia": base.get("tendencia", 0),
    }

    if padrao:
        sugestao_ajustada = base.get("sugestao", 0) * (1 + padrao["media_pct"] / 100)
        resultado["sugestao_final"] = round(sugestao_ajustada, 2)
        resultado["ajuste_pct"] = padrao["media_pct"]
        resultado["num_ajustes"] = padrao["num_ajustes"]

    return resultado