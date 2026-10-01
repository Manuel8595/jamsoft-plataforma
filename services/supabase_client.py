import os
import requests
from datetime import datetime, timedelta

try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
except Exception:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""

if not SUPABASE_URL:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
if not SUPABASE_KEY:
    SUPABASE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")


def _headers():
    """Headers base (chave pública)."""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _headers_autenticado(jwt=None):
    """Headers com JWT do utilizador logado (se existir)."""
    if jwt:
        return {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        }
    return _headers()


def _get(tabela, params=None, jwt=None):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"
    try:
        r = requests.get(
            url,
            headers=_headers_autenticado(jwt),
            params=params,
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
        return []
    except Exception as e:
        print(f"[Supabase] Erro em {tabela}: {e}")
        return []


def _get_paginado(tabela, params=None, pagina=1000, jwt=None):
    todos = []
    offset = 0
    while True:
        p = dict(params or {})
        p["limit"] = pagina
        p["offset"] = offset
        lote = _get(tabela, p, jwt=jwt) or []
        todos.extend(lote)
        if len(lote) < pagina:
            break
        offset += pagina
        if offset > 50000:
            break
    return todos


# ============================================================
# FARMACIAS
# ============================================================

def listar_farmacias(jwt=None):
    return _get("farmacias", {"select": "*", "order": "id"}, jwt=jwt) or []


def obter_farmacia(fid, jwt=None):
    r = _get("farmacias", {"select": "*", "id": f"eq.{fid}"}, jwt=jwt)
    return r[0] if r else None


# ============================================================
# VENDAS
# ============================================================

def vendas_hoje(farmacia_id=None, jwt=None):
    hoje = datetime.now().strftime("%Y-%m-%d")
    params = {"select": "*", "data": f"gte.{hoje}T00:00:00", "order": "data.desc"}
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get("vendas", params, jwt=jwt) or []


def vendas_ultimos_dias(dias=7, farmacia_id=None, jwt=None):
    inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    params = {"select": "*", "data": f"gte.{inicio}T00:00:00", "order": "data.desc"}
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get("vendas", params, jwt=jwt) or []


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


def resumo_por_farmacia(dias=1, jwt=None):
    farmacias = listar_farmacias(jwt=jwt)
    vendas = vendas_ultimos_dias(dias, jwt=jwt)
    resumo = {}
    for f in farmacias:
        fid = f["id"]
        v_f = [v for v in vendas if v.get("farmacia_id") == fid]
        total = sum(v.get("total", 0) for v in v_f)
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


def vendas_por_dia(dias=30, farmacia_id=None, jwt=None):
    vendas = vendas_ultimos_dias(dias, farmacia_id, jwt=jwt)
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


def vendas_por_hora(dias=1, farmacia_id=None, jwt=None):
    vendas = vendas_ultimos_dias(dias, farmacia_id, jwt=jwt)
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


def _intervalo_mes(mes, ano):
    inicio = f"{ano}-{mes:02d}-01T00:00:00"
    if mes == 12:
        prox = f"{ano + 1}-01-01T00:00:00"
    else:
        prox = f"{ano}-{mes + 1:02d}-01T00:00:00"
    return inicio, prox


def vendas_por_mes(mes, ano, farmacia_id=None, jwt=None):
    inicio, fim = _intervalo_mes(mes, ano)
    params = {
        "select": "id,total,farmacia_id,data,forma_pagamento",
        "data": [f"gte.{inicio}", f"lt.{fim}"],
        "order": "data.asc",
    }
    if farmacia_id:
        params["farmacia_id"] = f"eq.{farmacia_id}"
    return _get_paginado("vendas", params, jwt=jwt) or []


def resumo_por_farmacia_mes(mes, ano, jwt=None):
    farmacias = listar_farmacias(jwt=jwt)
    vendas = vendas_por_mes(mes, ano, jwt=jwt)
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


def criar_meta(mes, ano, farmacia_id, orcamento, observacoes="", definido_por="", jwt=None):
    mes_str = f"{ano}-{mes:02d}"
    params = {"select": "id", "mes": f"eq.{mes_str}", "farmacia_id": f"eq.{farmacia_id}"}
    r = _get("metas_farmacia", params, jwt=jwt)
    dados = {
        "mes": mes_str,
        "farmacia_id": farmacia_id,
        "orcamento_mes": float(orcamento),
        "observacoes": observacoes,
        "definido_por": definido_por,
        "atualizado_em": datetime.now().isoformat(),
    }
    url = f"{SUPABASE_URL}/rest/v1/metas_farmacia"
    headers = _headers_autenticado(jwt)
    headers["Prefer"] = "return=representation"
    try:
        if r:
            meta_id = r[0]["id"]
            resp = requests.patch(f"{url}?id=eq.{meta_id}", headers=headers, json=dados, timeout=10)
        else:
            dados["criado_em"] = datetime.now().isoformat()
            resp = requests.post(url, headers=headers, json=dados, timeout=10)
        return resp.status_code in (200, 201, 204)
    except Exception as e:
        print(f"[Supabase] Erro ao criar meta: {e}")
        return False


def apagar_meta(meta_id, jwt=None):
    url = f"{SUPABASE_URL}/rest/v1/metas_farmacia?id=eq.{meta_id}"
    try:
        resp = requests.delete(url, headers=_headers_autenticado(jwt), timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"[Supabase] Erro ao apagar meta: {e}")
        return False


def ultima_venda_por_farmacia(jwt=None):
    farmacias = listar_farmacias(jwt=jwt)
    resultado = {}
    hoje = datetime.now().date()
    for f in farmacias:
        fid = f["id"]
        params = {"select": "data,total", "farmacia_id": f"eq.{fid}", "order": "data.desc", "limit": 5}
        vendas = _get("vendas", params, jwt=jwt) or []
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


def ultima_venda_global(jwt=None):
    params = {"select": "data", "order": "data.desc", "limit": 1}
    r = _get("vendas", params, jwt=jwt)
    if r:
        return r[0]["data"][:10]
    return None


def metas_activas(mes=None, ano=None, jwt=None):
    if not mes:
        mes = datetime.now().month
    if not ano:
        ano = datetime.now().year
    mes_str = f"{ano}-{mes:02d}"
    params = {"select": "*", "mes": f"eq.{mes_str}", "order": "id"}
    return _get("metas_farmacia", params, jwt=jwt) or []


def produtos_validade_proxima(dias=90, jwt=None):
    hoje = datetime.now().date()
    limite = (hoje + timedelta(days=dias)).isoformat()
    params = {
        "select": "produto_nome,codigo_barras,numero_lote,data_validade,quantidade,farmacia_id",
        "data_validade": [f"gte.{hoje.isoformat()}", f"lte.{limite}"],
        "order": "data_validade.asc",
    }
    return _get("lotes", params, jwt=jwt) or []


def produtos_estoque_baixo(jwt=None):
    params = {"select": "nome,codigo_barras,estoque_atual,estoque_minimo,farmacia_id", "order": "estoque_atual.asc"}
    todos = _get("produtos", params, jwt=jwt) or []
    return [p for p in todos if (p.get("estoque_atual") or 0) <= (p.get("estoque_minimo") or 0)]


def turnos_com_diferenca(dias=7, jwt=None):
    inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    params = {"select": "*", "data_abertura": f"gte.{inicio}T00:00:00", "order": "data_abertura.desc", "limit": 50}
    turnos = _get("turnos_caixa", params, jwt=jwt) or []
    return [t for t in turnos if abs(t.get("diferenca") or 0) >= 50000]


def tem_meta_definida(mes, ano, jwt=None):
    metas = metas_activas(mes, ano, jwt=jwt)
    return len(metas) > 0


def total_vendas_por_mes(mes, ano, jwt=None):
    vendas = vendas_por_mes(mes, ano, jwt=jwt)
    return sum(v.get("total", 0) or 0 for v in vendas)
