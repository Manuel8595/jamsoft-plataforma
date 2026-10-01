# Este script SUBSTITUI a funcao mostrar_vendas() no pages_secundarias.py
# por uma versao completa.

import re

path = "pages_secundarias.py"

with open(path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# Nova funcao mostrar_vendas
nova_funcao = '''def mostrar_vendas():
    st.title("Vendas")
    st.caption("Analise detalhada das vendas")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    hoje = datetime.now()

    with col1:
        mes_escolhido = st.selectbox("Mes", MESES, index=hoje.month - 1, key="vend_mes")
    with col2:
        anos = anos_disponiveis()
        ano_escolhido = st.selectbox("Ano", anos, index=0, key="vend_ano")
    with col3:
        farmacias = listar_farmacias()
        opcoes_farm = [{"id": None, "nome": "Todas as farmacias"}] + farmacias
        farm_escolhida = st.selectbox(
            "Farmacia",
            opcoes_farm,
            format_func=lambda f: f["nome"],
            key="vend_farm",
        )
    with col4:
        st.write("")
        st.write("")
        if st.button("Atualizar", use_container_width=True, key="vend_refresh"):
            st.cache_data.clear()
            st.rerun()

    mes_num = MESES.index(mes_escolhido) + 1
    farm_id = farm_escolhida.get("id") if isinstance(farm_escolhida, dict) else None

    st.markdown("---")

    with st.spinner("A carregar dados..."):
        vendas = vendas_detalhadas_mes(mes_num, ano_escolhido, farm_id)
        por_forma = vendas_por_forma_pagamento(mes_num, ano_escolhido, farm_id)
        por_dia = vendas_por_dia_mes(mes_num, ano_escolhido, farm_id)
        por_hora = vendas_por_hora_mes(mes_num, ano_escolhido, farm_id)
        top_prods = top_produtos_mes(mes_num, ano_escolhido, 10, farm_id)
        top_clis = top_clientes_mes(mes_num, ano_escolhido, 10)

    total_geral = sum(v.get("total", 0) or 0 for v in vendas)
    num_geral = len(vendas)
    ticket_medio = (total_geral / num_geral) if num_geral > 0 else 0

    dias_ativos = len(por_dia) if por_dia else 1
    media_diaria = total_geral / dias_ativos

    st.subheader(f"Totais - {mes_escolhido} {ano_escolhido}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Vendas", _fmt_kz(total_geral))
    with c2: st.metric("Num. Vendas", f"{num_geral}")
    with c3: st.metric("Ticket Medio", _fmt_kz(ticket_medio))
    with c4: st.metric("Media Diaria", _fmt_kz(media_diaria))

    st.markdown("---")
    st.subheader("Por Forma de Pagamento")

    if por_forma:
        for forma, dados in sorted(por_forma.items(), key=lambda x: -x[1]["total"]):
            perc = (dados["total"] / total_geral * 100) if total_geral > 0 else 0
            st.markdown(f"**{forma}** - {_fmt_kz(dados['total'])} ({perc:.1f}%) - {dados['num']} vendas")
            st.progress(min(perc / 100, 1.0))
    else:
        st.info("Sem dados.")

    st.markdown("---")
    st.subheader("Vendas por Dia")

    if por_dia:
        dados = {d: v["total"] for d, v in por_dia.items()}
        st.bar_chart(dados, height=280, use_container_width=True)
    else:
        st.info("Sem dados.")

    st.markdown("---")
    st.subheader("Vendas por Hora")

    if por_hora:
        dados_h = {f"{h:02d}h": por_hora[h]["total"] for h in range(24) if por_hora[h]["num"] > 0}
        if dados_h:
            st.bar_chart(dados_h, height=280, use_container_width=True)
        else:
            st.info("Sem dados.")
    else:
        st.info("Sem dados.")

    st.markdown("---")
    st.subheader("Top 10 Produtos")

    if top_prods:
        cols = st.columns([0.5, 3, 1.2, 1.5])
        with cols[0]: st.markdown("**#**")
        with cols[1]: st.markdown("**Produto**")
        with cols[2]: st.markdown("**Qtd**")
        with cols[3]: st.markdown("**Total**")
        st.markdown("---")
        for i, p in enumerate(top_prods, start=1):
            r = st.columns([0.5, 3, 1.2, 1.5])
            with r[0]: st.markdown(f"**{i}**")
            with r[1]: st.markdown(p.get("nome", "?"))
            with r[2]: st.markdown(f"{p.get('quantidade', 0)}")
            with r[3]: st.markdown(f"**{_fmt_kz(p.get('total', 0))}**")
    else:
        st.info("Sem itens de venda registados neste mes.")

    st.markdown("---")
    st.subheader("Top 10 Clientes")

    if top_clis:
        cols = st.columns([0.5, 3, 1.2, 1.5])
        with cols[0]: st.markdown("**#**")
        with cols[1]: st.markdown("**Cliente**")
        with cols[2]: st.markdown("**Compras**")
        with cols[3]: st.markdown("**Total**")
        st.markdown("---")
        for i, c in enumerate(top_clis, start=1):
            r = st.columns([0.5, 3, 1.2, 1.5])
            with r[0]: st.markdown(f"**{i}**")
            with r[1]: st.markdown(c.get("nome", "?"))
            with r[2]: st.markdown(f"{c.get('compras', 0)}")
            with r[3]: st.markdown(f"**{_fmt_kz(c.get('total', 0))}**")
    else:
        st.info("Sem clientes registados em facturas neste mes.")

    st.markdown("---")
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")'''

# Substituir a funcao mostrar_vendas() antiga
padrao = re.compile(
    r"def mostrar_vendas\(\):.*?(?=\ndef |\Z)",
    re.DOTALL
)

if "def mostrar_vendas" in conteudo:
    # Verificar se ja foi substituida
    if "vendas_detalhadas_mes" in conteudo:
        print("JA SUBSTITUIDA - nao mexer")
    else:
        conteudo = padrao.sub(nova_funcao + "\n\n", conteudo, count=1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print("OK - funcao mostrar_vendas substituida")
else:
    print("ERRO - funcao mostrar_vendas nao encontrada")