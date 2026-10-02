import os

# ============================================================
# FICHEIRO 1 — services/supabase_client.py
# ============================================================

conteudo_supabase = '''import os
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
    SUPABASE_URL = "https://bkbeedknuunjpuvbpgxr.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "sb_publishable_KXK6NeMtIy1m4jFk7jDprw_9rHnD-WT"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _get(tabela, params=None):
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
'''

path = "services/supabase_client.py"
with open(path, "w", encoding="utf-8") as f:
    f.write(conteudo_supabase)

print(f"OK - {path} escrito ({len(conteudo_supabase)} caracteres)")