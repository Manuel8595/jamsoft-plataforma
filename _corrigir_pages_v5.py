# Substitui mostrar_financeiro() e mostrar_utilizadores()

import re

path = "pages_secundarias.py"

with open(path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# --- Nova funcao mostrar_financeiro ---
nova_financeiro = '''def mostrar_financeiro():
    st.title("Financeiro")
    st.caption("Depositos, turnos de caixa e saldos")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    hoje = datetime.now()

    with col1:
        mes_escolhido = st.selectbox("Mes", MESES, index=hoje.month - 1, key="fin_mes")
    with col2:
        anos = anos_disponiveis()
        ano_escolhido = st.selectbox("Ano", anos, index=0, key="fin_ano")
    with col3:
        farmacias = listar_farmacias()
        opcoes_farm = [{"id": None, "nome": "Todas as farmacias"}] + farmacias
        farm_escolhida = st.selectbox(
            "Farmacia",
            opcoes_farm,
            format_func=lambda f: f["nome"],
            key="fin_farm",
        )
    with col4:
        st.write("")
        st.write("")
        if st.button("Atualizar", use_container_width=True, key="fin_refresh"):
            st.cache_data.clear()
            st.rerun()

    mes_num = MESES.index(mes_escolhido) + 1
    farm_id = farm_escolhida.get("id") if isinstance(farm_escolhida, dict) else None

    st.markdown("---")

    with st.spinner("A carregar dados financeiros..."):
        resumo_t = resumo_turnos(mes_num, ano_escolhido, farm_id)
        turnos = listar_turnos_periodo(mes_num, ano_escolhido, farm_id)
        resumo_d = resumo_depositos(mes_num, ano_escolhido, farm_id)
        depositos = listar_depositos(mes_num, ano_escolhido, farm_id)

    st.subheader(f"Resumo - {mes_escolhido} {ano_escolhido}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Vendas (turnos)", _fmt_kz(resumo_t['total_vendas']))
    with c2: st.metric("Em dinheiro", _fmt_kz(resumo_t['total_dinheiro']))
    with c3: st.metric("Em TPA", _fmt_kz(resumo_t['total_tpa']))
    with c4:
        dif = resumo_t['total_diferenca']
        if abs(dif) < 1:
            st.metric("Diferenca", "OK", delta="0")
        else:
            sinal = "+" if dif > 0 else ""
            st.metric("Diferenca", _fmt_kz(dif), delta=f"{sinal}{dif:.0f}")

    st.markdown("---")
    st.subheader("Depositos Bancarios")

    dc1, dc2, dc3 = st.columns(3)
    with dc1: st.metric("Total depositado", _fmt_kz(resumo_d['total_valor']))
    with dc2: st.metric("Num. depositos", f"{resumo_d['num_total']}")
    with dc3:
        if resumo_d['num_pendentes'] > 0:
            st.metric("Pendentes aprovacao", f"{resumo_d['num_pendentes']}", delta="Aviso")
        else:
            st.metric("Pendentes aprovacao", "0", delta="OK")

    if depositos:
        st.markdown("---")
        cols = st.columns([1.2, 2, 2, 1.5, 2, 2])
        with cols[0]: st.markdown("**Data**")
        with cols[1]: st.markdown("**Referencia**")
        with cols[2]: st.markdown("**Banco**")
        with cols[3]: st.markdown("**Valor**")
        with cols[4]: st.markdown("**Gerente**")
        with cols[5]: st.markdown("**Estado**")
        st.markdown("---")
        for d in depositos:
            r = st.columns([1.2, 2, 2, 1.5, 2, 2])
            with r[0]: st.markdown(d.get("data") or "-")
            with r[1]: st.markdown(d.get("referencia") or "-")
            with r[2]: st.markdown(d.get("banco") or "-")
            with r[3]: st.markdown(f"**{_fmt_kz(d.get('valor') or 0)}**")
            with r[4]: st.markdown(d.get("gerente_nome") or "-")
            with r[5]: st.markdown(d.get("estado") or "-")
    else:
        st.info("Sem depositos registados neste periodo.")

    st.markdown("---")
    st.subheader("Turnos de Caixa")

    if turnos:
        cols = st.columns([1.5, 2.5, 1.5, 1.5, 1.5, 1.5, 1.5])
        with cols[0]: st.markdown("**Data**")
        with cols[1]: st.markdown("**Utilizador**")
        with cols[2]: st.markdown("**Vendas**")
        with cols[3]: st.markdown("**Dinheiro**")
        with cols[4]: st.markdown("**TPA**")
        with cols[5]: st.markdown("**Diferenca**")
        with cols[6]: st.markdown("**Estado**")
        st.markdown("---")
        for t in turnos[:100]:
            dif = t.get("diferenca") or 0
            if abs(dif) < 1: dif_txt = "OK"
            elif dif > 0: dif_txt = f"+{_fmt_kz(dif)}"
            else: dif_txt = f"-{_fmt_kz(abs(dif))}"

            r = st.columns([1.5, 2.5, 1.5, 1.5, 1.5, 1.5, 1.5])
            with r[0]: st.markdown((t.get("data_abertura") or "-")[:10])
            with r[1]: st.markdown(t.get("utilizador_nome") or "-")
            with r[2]: st.markdown(_fmt_kz(t.get("total_vendas") or 0))
            with r[3]: st.markdown(_fmt_kz(t.get("total_dinheiro") or 0))
            with r[4]: st.markdown(_fmt_kz(t.get("total_tpa") or 0))
            with r[5]: st.markdown(dif_txt)
            with r[6]: st.markdown(t.get("estado") or "-")
    else:
        st.info("Sem turnos registados neste periodo.")

    st.markdown("---")
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")'''

# --- Nova funcao mostrar_utilizadores ---
nova_utilizadores = '''def mostrar_utilizadores():
    st.title("Utilizadores")
    st.caption("Equipa de todas as farmacias")
    st.markdown("---")

    col1, col2, col3 = st.columns([3, 3, 1])
    hoje = datetime.now()

    with col1:
        farmacias = listar_farmacias()
        opcoes_farm = [{"id": None, "nome": "Todas as farmacias"}] + farmacias
        farm_escolhida = st.selectbox(
            "Farmacia",
            opcoes_farm,
            format_func=lambda f: f["nome"],
            key="user_farm",
        )
    with col2:
        anos = anos_disponiveis()
        ano_escolhido = st.selectbox("Ano (actividade)", anos, index=0, key="user_ano")
    with col3:
        st.write("")
        st.write("")
        if st.button("Atualizar", use_container_width=True, key="user_refresh"):
            st.cache_data.clear()
            st.rerun()

    farm_id = farm_escolhida.get("id") if isinstance(farm_escolhida, dict) else None

    st.markdown("---")

    with st.spinner("A carregar utilizadores..."):
        resumo = resumo_utilizadores(farm_id)
        utilizadores = listar_todos_utilizadores(farm_id)
        top_vend = top_vendedores_mes(hoje.month, ano_escolhido, farm_id)

    st.subheader("Resumo")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total", f"{resumo['total']}")
    with c2: st.metric("Activos", f"{resumo['activos']}")
    with c3: st.metric("Inactivos", f"{resumo['inactivos']}")
    with c4: st.metric("Perfis", f"{len(resumo['perfis'])}")

    if resumo['perfis']:
        st.markdown("**Por perfil:** " + " | ".join([f"{k}: {v}" for k, v in resumo['perfis'].items()]))

    st.markdown("---")
    st.subheader(f"Lista de Utilizadores ({resumo['total']})")

    if utilizadores:
        cols = st.columns([3, 2, 1.5, 1, 2])
        with cols[0]: st.markdown("**Nome**")
        with cols[1]: st.markdown("**Username**")
        with cols[2]: st.markdown("**Perfil**")
        with cols[3]: st.markdown("**Activo**")
        with cols[4]: st.markdown("**Ultimo Login**")
        st.markdown("---")
        for u in utilizadores:
            r = st.columns([3, 2, 1.5, 1, 2])
            with r[0]: st.markdown(f"**{u.get('nome') or '?'}**")
            with r[1]: st.markdown(u.get("username") or "-")
            with r[2]: st.markdown(u.get("perfil") or "-")
            with r[3]:
                if u.get("ativo"): st.markdown("🟢 Sim")
                else: st.markdown("🔴 Nao")
            with r[4]: st.markdown((u.get("ultimo_login") or "-")[:16])
    else:
        st.info("Sem utilizadores.")

    st.markdown("---")
    st.subheader(f"Top Vendedores do Mes ({hoje.month}/{ano_escolhido})")

    if top_vend:
        cols = st.columns([0.5, 3, 1.5, 2])
        with cols[0]: st.markdown("**#**")
        with cols[1]: st.markdown("**Utilizador**")
        with cols[2]: st.markdown("**Vendas**")
        with cols[3]: st.markdown("**Total**")
        st.markdown("---")
        for i, v in enumerate(top_vend, start=1):
            r = st.columns([0.5, 3, 1.5, 2])
            with r[0]: st.markdown(f"**{i}**")
            with r[1]: st.markdown(v.get("nome") or "-")
            with r[2]: st.markdown(f"{v.get('num_vendas', 0)}")
            with r[3]: st.markdown(f"**{_fmt_kz(v.get('total', 0))}**")
    else:
        st.info("Sem vendas registadas neste mes.")

    st.markdown("---")
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")'''

# Substituir mostrar_financeiro
padrao_fin = re.compile(r"def mostrar_financeiro\(\):.*?(?=\ndef |\Z)", re.DOTALL)
if "def mostrar_financeiro" in conteudo:
    if "resumo_turnos" in conteudo:
        print("financeiro: JA SUBSTITUIDO")
    else:
        conteudo = padrao_fin.sub(nova_financeiro + "\n\n", conteudo, count=1)
        print("financeiro: OK substituido")

# Substituir mostrar_utilizadores
padrao_user = re.compile(r"def mostrar_utilizadores\(\):.*?(?=\ndef |\Z)", re.DOTALL)
if "def mostrar_utilizadores" in conteudo:
    if "resumo_utilizadores" in conteudo:
        print("utilizadores: JA SUBSTITUIDO")
    else:
        conteudo = padrao_user.sub(nova_utilizadores + "\n\n", conteudo, count=1)
        print("utilizadores: OK substituido")

with open(path, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("Ficheiro guardado.")