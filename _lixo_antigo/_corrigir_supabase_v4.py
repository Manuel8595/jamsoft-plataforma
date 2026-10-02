conteudo_novo = '''

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
'''

path = "services/supabase_client.py"
with open(path, "r", encoding="utf-8") as f:
    conteudo_atual = f.read()

if "def listar_turnos_periodo" in conteudo_atual:
    print("JA EXISTE - nao adicionado novamente")
else:
    with open(path, "a", encoding="utf-8") as f:
        f.write(conteudo_novo)
    print(f"OK - adicionadas funcoes financeiro+utilizadores ({len(conteudo_novo)} caracteres)")