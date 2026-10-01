# Substitui mostrar_stock() e mostrar_perdas() no pages_secundarias.py

import re

path = "pages_secundarias.py"

with open(path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# --- Nova funcao mostrar_stock ---
nova_stock = '''def mostrar_stock():
    st.title("Stock")
    st.caption("Inventario de produtos por farmacia")
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 3, 1])
    hoje = datetime.now()

    with col1:
        farmacias = listar_farmacias()
        opcoes_farm = [{"id": None, "nome": "Todas as farmacias"}] + farmacias
        farm_escolhida = st.selectbox(
            "Farmacia",
            opcoes_farm,
            format_func=lambda f: f["nome"],
            key="stock_farm",
        )

    with col2:
        st.write("")
        filtro = st.radio(
            "Mostrar",
            ["Todos", "Estoque Baixo", "A Vencer"],
            horizontal=True,
            key="stock_filtro",
        )

    with col3:
        st.write("")
        st.write("")
        if st.button("Atualizar", use_container_width=True, key="stock_refresh"):
            st.cache_data.clear()
            st.rerun()

    farm_id = farm_escolhida.get("id") if isinstance(farm_escolhida, dict) else None

    st.markdown("---")

    with st.spinner("A carregar stock..."):
        resumo = resumo_stock(farm_id)
        produtos = listar_produtos_stock(farm_id)
        lotes_vencer = lotes_a_vencer(90, farm_id)

    # Resumo
    st.subheader("Resumo")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Produtos", f"{resumo['total_produtos']}")
    with c2:
        st.metric("Unidades em stock", f"{resumo['total_unidades']}")
    with c3:
        st.metric("Valor de venda", _fmt_kz(resumo['valor_venda']))
    with c4:
        if resumo['estoque_baixo'] > 0:
            st.metric("Estoque baixo", f"{resumo['estoque_baixo']}", delta="⚠️")
        else:
            st.metric("Estoque baixo", "0", delta="OK")

    st.markdown("---")

    # Lista de produtos
    if filtro == "Estoque Baixo":
        produtos_filtrados = [
            p for p in produtos
            if (p.get("estoque_atual") or 0) <= (p.get("estoque_minimo") or 0)
        ]
        st.subheader(f"Produtos com Estoque Baixo ({len(produtos_filtrados)})")
    elif filtro == "A Vencer":
        st.subheader(f"Lotes a Vencer em 90 dias ({len(lotes_vencer)})")
        if not lotes_vencer:
            st.success("Nenhum lote a vencer nos proximos 90 dias.")
        else:
            cols = st.columns([3, 2, 1.5, 1.5, 1.5, 1.5])
            with cols[0]: st.markdown("**Produto**")
            with cols[1]: st.markdown("**Lote**")
            with cols[2]: st.markdown("**Validade**")
            with cols[3]: st.markdown("**Qtd**")
            with cols[4]: st.markdown("**Dias**")
            with cols[5]: st.markdown("**Estado**")
            st.markdown("---")
            for l in lotes_vencer:
                dias = l.get("dias_restantes", 0)
                if dias < 0:
                    estado = "VENCIDO"
                elif dias <= 30:
                    estado = "URGENTE"
                elif dias <= 60:
                    estado = "ATENCAO"
                else:
                    estado = "OK"
                r = st.columns([3, 2, 1.5, 1.5, 1.5, 1.5])
                with r[0]: st.markdown(l.get("produto_nome") or "?")
                with r[1]: st.markdown(l.get("numero_lote") or "-")
                with r[2]: st.markdown(l.get("data_validade") or "-")
                with r[3]: st.markdown(f"{l.get('quantidade', 0)}")
                with r[4]: st.markdown(f"{dias}")
                with r[5]: st.markdown(estado)
        produtos_filtrados = None
    else:
        produtos_filtrados = produtos
        st.subheader(f"Todos os Produtos ({len(produtos)})")

    # Lista de produtos (excepto no modo "A Vencer")
    if produtos_filtrados is not None:
        if not produtos_filtrados:
            st.info("Sem produtos.")
        else:
            cols = st.columns([3, 2, 1.2, 1, 1.2, 1.5])
            with cols[0]: st.markdown("**Produto**")
            with cols[1]: st.markdown("**Codigo**")
            with cols[2]: st.markdown("**Atual**")
            with cols[3]: st.markdown("**Min.**")
            with cols[4]: st.markdown("**Estado**")
            with cols[5]: st.markdown("**Preco**")
            st.markdown("---")

            for p in produtos_filtrados:
                est = p.get("estoque_atual") or 0
                mn = p.get("estoque_minimo") or 0
                if est <= mn:
                    estado = "⚠️ Baixo"
                elif est == 0:
                    estado = "🔴 Esgotado"
                else:
                    estado = "🟢 OK"

                r = st.columns([3, 2, 1.2, 1, 1.2, 1.5])
                with r[0]:
                    st.markdown(f"**{p.get('nome', '?')}**")
                    if p.get('categoria_nome'):
                        st.caption(p.get('categoria_nome'))
                with r[1]: st.markdown(p.get("codigo_barras") or "-")
                with r[2]: st.markdown(f"**{est}**")
                with r[3]: st.markdown(f"{mn}")
                with r[4]: st.markdown(estado)
                with r[5]: st.markdown(_fmt_kz(p.get("preco_venda") or 0))

    st.markdown("---")
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")'''

# --- Nova funcao mostrar_perdas ---
nova_perdas = '''def mostrar_perdas():
    st.title("Perdas")
    st.caption("Quebras, validades e outros prejuizos")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    hoje = datetime.now()

    with col1:
        mes_escolhido = st.selectbox("Mes", MESES, index=hoje.month - 1, key="perd_mes")
    with col2:
        anos = anos_disponiveis()
        ano_escolhido = st.selectbox("Ano", anos, index=0, key="perd_ano")
    with col3:
        farmacias = listar_farmacias()
        opcoes_farm = [{"id": None, "nome": "Todas as farmacias"}] + farmacias
        farm_escolhida = st.selectbox(
            "Farmacia",
            opcoes_farm,
            format_func=lambda f: f["nome"],
            key="perd_farm",
        )
    with col4:
        st.write("")
        st.write("")
        if st.button("Atualizar", use_container_width=True, key="perd_refresh"):
            st.cache_data.clear()
            st.rerun()

    mes_num = MESES.index(mes_escolhido) + 1
    farm_id = farm_escolhida.get("id") if isinstance(farm_escolhida, dict) else None

    st.markdown("---")

    with st.spinner("A carregar perdas..."):
        resumo = resumo_perdas(mes_num, ano_escolhido, farm_id)
        perdas = listar_perdas(mes_num, ano_escolhido, farm_id)

    st.subheader(f"Totais - {mes_escolhido} {ano_escolhido}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Perdido", _fmt_kz(resumo['total_valor']))
    with c2:
        st.metric("Num. Registos", f"{resumo['total_num']}")
    with c3:
        st.metric("Tipos", f"{len(resumo['por_tipo'])}")

    st.markdown("---")

    if resumo['por_tipo']:
        st.subheader("Por Tipo")
        for tipo, dados in sorted(resumo['por_tipo'].items(), key=lambda x: -x[1]["total"]):
            perc = (dados["total"] / resumo['total_valor'] * 100) if resumo['total_valor'] > 0 else 0
            st.markdown(f"**{tipo}** - {_fmt_kz(dados['total'])} ({perc:.1f}%) - {dados['num']} registos")
            st.progress(min(perc / 100, 1.0))
    else:
        st.info("Sem perdas registadas neste periodo.")

    st.markdown("---")
    st.subheader("Detalhes")

    if perdas:
        cols = st.columns([1.5, 1.5, 3, 1, 1.5, 3, 2])
        with cols[0]: st.markdown("**Data**")
        with cols[1]: st.markdown("**Tipo**")
        with cols[2]: st.markdown("**Produto**")
        with cols[3]: st.markdown("**Qtd**")
        with cols[4]: st.markdown("**Valor**")
        with cols[5]: st.markdown("**Motivo**")
        with cols[6]: st.markdown("**Utilizador**")
        st.markdown("---")

        for p in perdas[:100]:
            r = st.columns([1.5, 1.5, 3, 1, 1.5, 3, 2])
            with r[0]: st.markdown((p.get("data") or "-")[:10])
            with r[1]: st.markdown(p.get("tipo") or "-")
            with r[2]: st.markdown(p.get("produto_nome") or "-")
            with r[3]: st.markdown(f"{p.get('quantidade', 0)}")
            with r[4]: st.markdown(f"**{_fmt_kz(p.get('valor_perdido') or 0)}**")
            with r[5]: st.markdown((p.get("motivo") or "-")[:40])
            with r[6]: st.markdown(p.get("utilizador_nome") or "-")
    else:
        st.info("Sem perdas registadas.")

    st.markdown("---")
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")'''

# Substituir mostrar_stock
padrao_stock = re.compile(r"def mostrar_stock\(\):.*?(?=\ndef |\Z)", re.DOTALL)
if "def mostrar_stock" in conteudo:
    if "resumo_stock" in conteudo:
        print("stock: JA SUBSTITUIDO")
    else:
        conteudo = padrao_stock.sub(nova_stock + "\n\n", conteudo, count=1)
        print("stock: OK substituido")

# Substituir mostrar_perdas
padrao_perdas = re.compile(r"def mostrar_perdas\(\):.*?(?=\ndef |\Z)", re.DOTALL)
if "def mostrar_perdas" in conteudo:
    if "resumo_perdas" in conteudo:
        print("perdas: JA SUBSTITUIDO")
    else:
        conteudo = padrao_perdas.sub(nova_perdas + "\n\n", conteudo, count=1)
        print("perdas: OK substituido")

with open(path, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("Ficheiro guardado.")