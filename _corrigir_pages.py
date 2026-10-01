conteudo = '''"""
Paginas secundarias da plataforma.
"""

import streamlit as st
from datetime import datetime, timedelta
from services.supabase_client import (
    listar_farmacias,
    resumo_por_farmacia_mes,
    anos_disponiveis,
    ultima_venda_por_farmacia,
    metas_activas,
    produtos_validade_proxima,
    produtos_estoque_baixo,
    turnos_com_diferenca,
    total_vendas_por_mes,
)

MESES = ["Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def _fmt_kz(valor):
    try:
        return f"Kz {float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "Kz 0"


def _placeholder(titulo, icone, descricao, fase):
    st.title(f"{icone} {titulo}")
    st.markdown("---")
    st.info(f"Em construcao - Fase {fase}")


def mostrar_ranking():
    st.title("Ranking de Farmacias")
    st.caption("Compare o desempenho de todas as farmacias do pais")
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 2, 3])
    hoje = datetime.now()

    with col1:
        mes_escolhido = st.selectbox("Mes", MESES, index=hoje.month - 1, key="rank_mes")
    with col2:
        anos = anos_disponiveis()
        ano_escolhido = st.selectbox("Ano", anos, index=0, key="rank_ano")
    with col3:
        st.write("")
        st.write("")
        comparar = st.checkbox("Comparar com outro ano", key="rank_comparar")

    mes_num = MESES.index(mes_escolhido) + 1

    mes_comp = None
    ano_comp = None
    if comparar:
        col_a, col_b = st.columns([2, 2])
        with col_a:
            mes_comp = st.selectbox("Mes (comparar)", MESES, index=hoje.month - 1, key="rank_mes_comp")
        with col_b:
            anos_comp = [a for a in anos if a != ano_escolhido]
            if anos_comp:
                ano_comp = st.selectbox("Ano (comparar)", anos_comp, index=0, key="rank_ano_comp")

    st.markdown("---")

    with st.spinner("A carregar..."):
        resumo_atual = resumo_por_farmacia_mes(mes_num, ano_escolhido)
        resumo_comp = None
        if comparar and mes_comp and ano_comp:
            mes_comp_num = MESES.index(mes_comp) + 1
            resumo_comp = resumo_por_farmacia_mes(mes_comp_num, ano_comp)

    total_geral = sum(r["total"] for r in resumo_atual.values())
    num_geral = sum(r["num_vendas"] for r in resumo_atual.values())
    ticket_geral = (total_geral / num_geral) if num_geral > 0 else 0
    num_farmacias = len(resumo_atual)

    st.subheader(f"{mes_escolhido} {ano_escolhido}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Lojas", f"{num_farmacias}")
    with c2: st.metric("Total Vendas", _fmt_kz(total_geral))
    with c3: st.metric("Num. Vendas", f"{num_geral}")
    with c4: st.metric("Ticket Medio", _fmt_kz(ticket_geral))

    st.markdown("---")
    st.subheader("Ranking")

    ranking = sorted(resumo_atual.values(), key=lambda x: x["total"], reverse=True)
    if not ranking:
        st.warning("Sem dados.")
        return

    for i, r in enumerate(ranking, start=1):
        f = r["farmacia"]
        total = r["total"]
        num = r["num_vendas"]
        ticket = r["ticket_medio"]

        if i == 1: medalha = "1º"
        elif i == 2: medalha = "2º"
        elif i == 3: medalha = "3º"
        else: medalha = f"{i}º"

        if total > 0: status = "Activa"
        else: status = "Sem vendas"

        row = st.columns([0.5, 2.5, 1.2, 1, 1, 1.2])
        with row[0]: st.markdown(f"**{medalha}**")
        with row[1]:
            st.markdown(f"**{f['nome']}**")
            st.caption(f"{f.get('endereco', '-')}")
        with row[2]: st.markdown(f"**{_fmt_kz(total)}**")
        with row[3]: st.markdown(f"{num}")
        with row[4]: st.markdown(f"{_fmt_kz(ticket)}")
        with row[5]: st.markdown(status)
        st.markdown("")

    st.markdown("---")
    st.subheader("Grafico")
    dados_grafico = {r["farmacia"]["nome"][:20]: r["total"] for r in ranking}
    st.bar_chart(dados_grafico, height=320, use_container_width=True)


def mostrar_alertas():
    st.title("Alertas")
    st.caption("Monitorizacao automatica")
    st.markdown("---")

    col_a, col_b = st.columns([6, 1])
    with col_b:
        if st.button("Atualizar", use_container_width=True, key="alertas_refresh"):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("A analisar..."):
        farmacias = listar_farmacias()
        ultimas = ultima_venda_por_farmacia()
        validades = produtos_validade_proxima(dias=90)
        estoque_baixo = produtos_estoque_baixo()
        turnos_dif = turnos_com_diferenca(dias=7)
        metas = metas_activas()

    criticos = []
    avisos = []
    informacoes = []

    for f in farmacias:
        fid = f["id"]
        info = ultimas.get(fid, {})
        dias = info.get("dias_atras")

        if dias is None:
            criticos.append({
                "titulo": f"{f['nome']} - Nunca comunicou",
                "detalhe": "Ainda nao enviou nenhuma venda.",
                "accao": "Verificar JAM Soft e internet.",
            })
        elif dias == 0:
            pass
        elif dias == 1:
            avisos.append({
                "titulo": f"{f['nome']} - Sem vendas ontem",
                "detalhe": f"Ultima: {info.get('data', '?')}",
                "accao": "Confirmar fecho.",
            })
        elif dias <= 3:
            avisos.append({
                "titulo": f"{f['nome']} - Sem comunicar ha {dias} dias",
                "detalhe": f"Ultima: {info.get('data', '?')}",
                "accao": "Ligar para a farmacia.",
            })
        else:
            criticos.append({
                "titulo": f"{f['nome']} - Sem comunicar ha {dias} dias",
                "detalhe": f"Ultima: {info.get('data', '?')}",
                "accao": "Contactar gerente URGENTE.",
            })

    for t in turnos_dif:
        dif = t.get("diferenca", 0)
        tipo = "SOBRA" if dif > 0 else "FALTA"
        avisos.append({
            "titulo": f"{t.get('utilizador_nome', '?')} - {tipo} de {_fmt_kz(abs(dif))}",
            "detalhe": f"Turno em {t.get('data_abertura', '?')[:10]}",
            "accao": "Verificar contagem.",
        })

    if validades:
        hoje = datetime.now().date()
        vencidos = []
        urgentes = []
        for v in validades:
            try:
                dv = datetime.strptime(v["data_validade"], "%Y-%m-%d").date()
                dias = (dv - hoje).days
                if dias < 0:
                    vencidos.append(v)
                elif dias <= 30:
                    urgentes.append(v)
            except Exception:
                continue

        if vencidos:
            criticos.append({
                "titulo": f"{len(vencidos)} produto(s) VENCIDO(S)",
                "detalhe": f"Ex: {vencidos[0].get('produto_nome', '?')}",
                "accao": "Retirar do stock.",
            })
        if urgentes:
            avisos.append({
                "titulo": f"{len(urgentes)} produto(s) a vencer em 30 dias",
                "detalhe": f"Ex: {urgentes[0].get('produto_nome', '?')}",
                "accao": "Promover vendas.",
            })

    if estoque_baixo:
        informacoes.append({
            "titulo": f"{len(estoque_baixo)} produto(s) com estoque baixo",
            "detalhe": f"Ex: {estoque_baixo[0].get('nome', '?')}",
            "accao": "Encomendar.",
        })

    st.subheader("Resumo")
    c1, c2, c3 = st.columns(3)
    with c1:
        if criticos: st.error(f"{len(criticos)} critico(s)")
        else: st.success("Sem criticos")
    with c2:
        if avisos: st.warning(f"{len(avisos)} aviso(s)")
        else: st.success("Sem avisos")
    with c3:
        if informacoes: st.info(f"{len(informacoes)} info")
        else: st.success("Sem info")

    st.markdown("---")

    if criticos:
        st.subheader("Criticos")
        for a in criticos:
            st.error(f"{a['titulo']} - {a['detalhe']} - {a['accao']}")

    if avisos:
        st.subheader("Avisos")
        for a in avisos:
            st.warning(f"{a['titulo']} - {a['detalhe']} - {a['accao']}")

    if informacoes:
        st.subheader("Informacoes")
        for a in informacoes:
            st.info(f"{a['titulo']} - {a['detalhe']} - {a['accao']}")


def mostrar_orcamentos():
    st.title("Orcamentos")
    st.caption("Metas mensais por farmacia e global do pais")
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 2, 1])
    hoje = datetime.now()

    with col1:
        mes_escolhido = st.selectbox("Mes", MESES, index=hoje.month - 1, key="orc_mes")
    with col2:
        anos = anos_disponiveis()
        ano_escolhido = st.selectbox("Ano", anos, index=0, key="orc_ano")
    with col3:
        st.write("")
        st.write("")
        if st.button("Atualizar", use_container_width=True, key="orc_refresh"):
            st.cache_data.clear()
            st.rerun()

    mes_num = MESES.index(mes_escolhido) + 1
    st.markdown("---")

    with st.spinner("A carregar..."):
        farmacias = listar_farmacias()
        metas = metas_activas(mes_num, ano_escolhido)
        resumo_vendas = resumo_por_farmacia_mes(mes_num, ano_escolhido)

    metas_por_farm = {}
    for m in metas:
        fid = m.get("farmacia_id")
        if fid is not None:
            metas_por_farm[fid] = m

    orcamento_total = sum(m.get("orcamento_mes", 0) or 0 for m in metas)
    vendido_total = sum(r["total"] for r in resumo_vendas.values())
    perc_total = (vendido_total / orcamento_total * 100) if orcamento_total > 0 else 0

    st.subheader(f"Orcamento do Pais - {mes_escolhido} {ano_escolhido}")

    if orcamento_total > 0:
        col_a, col_b, col_c = st.columns(3)
        with col_a: st.metric("Orcamento", _fmt_kz(orcamento_total))
        with col_b: st.metric("Vendido", _fmt_kz(vendido_total))
        with col_c: st.metric("Atingido", f"{perc_total:.1f}%")

        progresso = min(perc_total / 100, 1.0)
        st.progress(progresso)

        if perc_total >= 100:
            st.success(f"Meta batida! Superou em {_fmt_kz(vendido_total - orcamento_total)}")
        else:
            st.warning(f"Falta {_fmt_kz(orcamento_total - vendido_total)}")
    else:
        st.info("Sem orcamento definido para este mes.")

    st.markdown("---")
    st.subheader("Por Farmacia")

    cols = st.columns([2.5, 1.5, 1.5, 1, 1.5])
    with cols[0]: st.markdown("**Farmacia**")
    with cols[1]: st.markdown("**Orcamento**")
    with cols[2]: st.markdown("**Vendido**")
    with cols[3]: st.markdown("**%**")
    with cols[4]: st.markdown("**Estado**")

    st.markdown("")

    for f in farmacias:
        fid = f["id"]
        meta = metas_por_farm.get(fid)
        orcamento = meta.get("orcamento_mes", 0) if meta else 0
        vendido = resumo_vendas.get(fid, {}).get("total", 0)

        if orcamento > 0:
            perc = (vendido / orcamento) * 100
            if perc >= 100: estado = "Batida"
            elif perc >= 70: estado = "Bom"
            elif perc >= 30: estado = "Baixo"
            else: estado = "Critico"
            perc_txt = f"{perc:.0f}%"
        else:
            estado = "Sem meta"
            perc_txt = "-"

        row = st.columns([2.5, 1.5, 1.5, 1, 1.5])
        with row[0]: st.markdown(f"**{f['nome']}**")
        with row[1]:
            if orcamento > 0: st.markdown(_fmt_kz(orcamento))
            else: st.markdown("_nao definido_")
        with row[2]: st.markdown(f"**{_fmt_kz(vendido)}**")
        with row[3]: st.markdown(perc_txt)
        with row[4]: st.markdown(estado)
        st.markdown("")

    st.markdown("---")
    st.subheader("Definir / Editar Orcamento")

    with st.form("form_orcamento"):
        c1, c2 = st.columns(2)
        with c1:
            farm_escolhida = st.selectbox(
                "Farmacia", farmacias,
                format_func=lambda f: f["nome"],
                key="orc_farm_edit",
            )
        with c2:
            valor_actual = metas_por_farm.get(farm_escolhida["id"], {}).get("orcamento_mes", 0) or 0
            valor_orc = st.number_input(
                "Orcamento (Kz)",
                min_value=0.0, value=float(valor_actual),
                step=100000.0, key="orc_valor_edit",
            )

        obs = st.text_input(
            "Observacoes",
            value=metas_por_farm.get(farm_escolhida["id"], {}).get("observacoes", "") or "",
            key="orc_obs_edit",
        )

        submitted = st.form_submit_button("Guardar Orcamento", use_container_width=True, type="primary")

    if submitted:
        if valor_orc <= 0:
            st.error("Orcamento deve ser > 0.")
        else:
            with st.spinner("A guardar..."):
                from services.supabase_client import criar_meta
                ok = criar_meta(
                    mes=mes_num, ano=ano_escolhido,
                    farmacia_id=farm_escolhida["id"],
                    orcamento=valor_orc, observacoes=obs,
                    definido_por="CEO",
                )
            if ok:
                st.success(f"Guardado: {farm_escolhida['nome']} -> {_fmt_kz(valor_orc)}")
                st.balloons()
                st.cache_data.clear()
                import time as _t
                _t.sleep(1)
                st.rerun()
            else:
                st.error("Erro ao guardar.")


def mostrar_vendas():
    _placeholder("Vendas", "", "Aqui vais ver as vendas detalhadas.", "9.6")


def mostrar_stock():
    _placeholder("Stock", "", "Stock das farmacias.", "9.7")


def mostrar_perdas():
    _placeholder("Perdas", "", "Perdas por tipo.", "9.7")


def mostrar_financeiro():
    _placeholder("Financeiro", "", "Depositos e saldos.", "9.8")


def mostrar_utilizadores():
    _placeholder("Utilizadores", "", "Utilizadores.", "9.8")


def mostrar_diagnostico():
    _placeholder("Diagnostico", "", "Diagnostico.", "9.9")


def mostrar_definicoes():
    _placeholder("Definicoes", "", "Preferencias.", "9.9")
'''

path = "pages_secundarias.py"
with open(path, "w", encoding="utf-8") as f:
    f.write(conteudo)

print(f"OK - {path} escrito ({len(conteudo)} caracteres)")
