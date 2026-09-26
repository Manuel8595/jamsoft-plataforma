import requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://bkbeedknuunjpuvbpgxr.supabase.co"
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