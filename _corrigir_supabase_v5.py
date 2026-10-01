conteudo_novo = '''

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
'''

path = "services/supabase_client.py"
with open(path, "r", encoding="utf-8") as f:
    conteudo_atual = f.read()

if "def diagnostico_sistema" in conteudo_atual:
    print("JA EXISTE")
else:
    with open(path, "a", encoding="utf-8") as f:
        f.write(conteudo_novo)
    print(f"OK - adicionadas funcoes de diagnostico ({len(conteudo_novo)} caracteres)")