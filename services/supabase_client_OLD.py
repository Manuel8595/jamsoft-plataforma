"""
Paginas secundarias da plataforma.
FASE 9.3: Ranking de Farmacias.
FASE 9.4: Alertas.
FASE 9.5: Orcamentos.
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


MESES = [
    "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def _fmt_kz(valor):
    try:
        return f"Kz {float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "Kz 0"


def _placeholder(titulo, icone, descricao, fase):
    st.title(f"{icone} {titulo}")
    st.markdown("---")
    st.info(
        f"🚧 **Em construcao** — Fase {fase}\n\n"
        f"{descricao}"
    )


def mostrar_ranking():
    st.title("🏆 Ranking de Farmacias")
    st.caption("Compare o desempenho de todas as farmacias do pais")
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 2, 3])
    hoje = datetime.now()

    with col1:
        mes_escolhido = st.selectbox("📅 Mes", MESES, index=hoje.month - 1, key="rank_mes")
    with col2:
        anos = anos_disponiveis()
        ano_escolhido = st.selectbox("📆 Ano", anos, index=0, key="rank_ano")
    with col3:
        st.write("")
        st.write("")
        comparar = st.checkbox("🔀 Comparar com outro ano", key="rank_comparar")

    mes_num = MESES.index(mes_escolhido) + 1

    mes_comp = None
    ano_comp = None
    if comparar:
        col_a, col_b = st.columns([2, 2])
        with col_a:
            mes_comp = st.selectbox("📅 Mes (comparar)", MESES, index=hoje.month - 1, key="rank_mes_comp")
        with col_b:
            anos_comp = [a for a in anos if a != ano_escolhido]
            if anos_comp:
                ano_comp = st.selectbox("📆 Ano (comparar)", anos_comp, index=0, key="rank_ano_comp")

    st.markdown("---")

    with st.spinner("A carregar dados do Supabase..."):
        resumo_atual = resumo_por_farmacia_mes(mes_num, ano_escolhido)
        resumo_comp = None
        if comparar and mes_comp and ano_comp:
            mes_comp_num = MESES.index(mes_comp) + 1
            resumo_comp = resumo_por_farmacia_mes(mes_comp_num, ano_comp)

    total_geral = sum(r["total"] for r in resumo_atual.values())
    num_geral = sum(r["num_vendas"] for r in resumo_atual.values())
    ticket_geral = (total_geral / num_geral) if num_geral > 0 else 0
    num_farmacias = len(resumo_atual)

    st.subheader(f"📊 {mes_escolhido} {ano_escolhido}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("🏥 Lojas", f"{num_farmacias}")
    with c2: st.metric("💰 Total Vendas", _fmt_kz(total_geral))
    with c3: st.metric("🛒 Num. Vendas", f"{num_geral}")
    with c4: st.metric("📊 Ticket Medio", _fmt_kz(ticket_geral))

    st.markdown("---")
    st.subheader("🏆 Ranking")

    ranking = sorted(resumo_atual.values(), key=lambda x: x["total"], reverse=True)
    if not ranking:
        st.warning("Sem dados para este periodo.")
        return

    if comparar and resumo_comp:
        cols = st.columns([0.4, 2.5, 1, 1, 1, 1, 1.2])
        with cols[0]: st.markdown("**#**")
        with cols[1]: st.markdown("**Farmacia**")
        with cols[2]: st.markdown(f"**{ano_escolhido}**")
        with cols[3]: st.markdown(f"**{ano_comp}**")
        with cols[4]: st.markdown("**Dif.**")
        with cols[5]: st.markdown("**Num.**")
        with cols[6]: st.markdown("**Status**")
    else:
        cols = st.columns([0.4, 2.5, 1.2, 1, 1, 1.2])
        with cols[0]: st.markdown("**#**")
        with cols[1]: st.markdown("**Farmacia**")
        with cols[2]: st.markdown("**Total**")
        with cols[3]: st.markdown("**Num. Vendas**")
        with cols[4]: st.markdown("**Ticket**")
        with cols[5]: st.markdown("**Status**")

    st.markdown("---")

    for i, r in enumerate(ranking, start=1):
        f = r["farmacia"]
        total = r["total"]
        num = r["num_vendas"]
        ticket = r["ticket_medio"]

        if i == 1: medalha = "🥇"
        elif i == 2: medalha = "🥈"
        elif i == 3: medalha = "🥉"
        else: medalha = f"**{i}**"

        if total > 0: status = "🟢 Activa"
        else: status = "⚪ Sem vendas"

        if comparar and resumo_comp:
            comp = resumo_comp.get(f["id"], {})
            total_comp = comp.get("total", 0)
            if total_comp > 0:
                diff_pct = ((total - total_comp) / total_comp) * 100
                if diff_pct > 0: dif_txt = f"📈 +{diff_pct:.0f}%"
                elif diff_pct < 0: dif_txt = f"📉 {diff_pct:.0f}%"
                else: dif_txt = "➖ 0%"
            else:
                dif_txt = "—" if total == 0 else "🆕"

            row = st.columns([0.4, 2.5, 1, 1, 1, 1, 1.2])
            with row[0]: st.markdown(medalha)
            with row[1]:
                st.markdown(f"**{f['nome']}**")
                st.caption(f"📍 {f.get('endereco', '-')}")
            with row[2]: st.markdown(f"**{_fmt_kz(total)}**")
            with row[3]: st.markdown(f"{_fmt_kz(total_comp)}")
            with row[4]: st.markdown(dif_txt)
            with row[5]: st.markdown(f"{num}")
            with row[6]: st.markdown(status)
        else:
            row = st.columns([0.4, 2.5, 1.2, 1, 1, 1.2])
            with row[0]: st.markdown(medalha)
            with row[1]:
                st.markdown(f"**{f['nome']}**")
                st.caption(f"📍 {f.get('endereco', '-')}")
            with row[2]: st.markdown(f"**{_fmt_kz(total)}**")
            with row[3]: st.markdown(f"{num}")
            with row[4]: st.markdown(f"{_fmt_kz(ticket)}")
            with row[5]: st.markdown(status)

        st.markdown("")

    st.markdown("---")
    st.subheader("📈 Grafico Comparativo")

    if comparar and resumo_comp:
        dados_grafico = {}
        for r in ranking:
            nome = r["farmacia"]["nome"][:18]
            ano_a = r["total"]
            ano_c = resumo_comp.get(r["farmacia"]["id"], {}).get("total", 0)
            dados_grafico[f"{nome} ({ano_escolhido})"] = ano_a
            dados_grafico[f"{nome} ({ano_comp})"] = ano_c
        st.bar_chart(dados_grafico, height=320, use_container_width=True)
    else:
        dados_grafico = {r["farmacia"]["nome"][:20]: r["total"] for r in ranking}
        st.bar_chart(dados_grafico, height=320, use_container_width=True)


def mostrar_alertas():
    st.title("🔔 Alertas")
    st.caption("Monitorizacao automatica do estado das farmacias")
    st.markdown("---")

    col_a, col_b = st.columns([6, 1])
    with col_b:
        if st.button("🔄 Atualizar", use_container_width=True, key="alertas_refresh"):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("A analisar dados..."):
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
                "titulo": f"⚠️ **{f['nome']}** — Nunca comunicou",
                "detalhe": "Esta farmacia ainda nao enviou nenhuma venda para a nuvem.",
                "accao": "Verificar se o JAM Soft esta instalado e ligado a internet.",
            })
        elif dias == 0:
            pass
        elif dias == 1:
            avisos.append({
                "titulo": f"🕒 **{f['nome']}** — Sem vendas ontem",
                "detalhe": f"Ultima venda: {info.get('data', '?')} (1 dia atras)",
                "accao": "Confirmar se houve fecho ou feriado.",
            })
        elif dias <= 3:
            avisos.append({
                "titulo": f"🕒 **{f['nome']}** — Sem comunicar ha {dias} dias",
                "detalhe": f"Ultima venda: {info.get('data', '?')}",
                "accao": "Ligar para a farmacia e verificar ligacao.",
            })
        else:
            criticos.append({
                "titulo": f"🔴 **{f['nome']}** — Sem comunicar ha {dias} dias",
                "detalhe": f"Ultima venda: {info.get('data', '?')}",
                "accao": "URGENTE: contactar gerente e verificar sistema.",
            })

    for t in turnos_dif:
        dif = t.get("diferenca", 0)
        tipo = "SOBRA" if dif > 0 else "FALTA"
        avisos.append({
            "titulo": f"💰 **{t.get('utilizador_nome', '?')}** — {tipo} de {_fmt_kz(abs(dif))}",
            "detalhe": f"Turno aberto em {t.get('data_abertura', '?')[:10]}",
            "accao": "Verificar contagem de notas e justificacao.",
        })

    if metas:
        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year
        total_mes = total_vendas_por_mes(mes_atual, ano_atual)
        dias_passados = hoje.day
        dias_no_mes = 30

        for meta in metas:
            orcamento = meta.get("orcamento_mes", 0)
            if orcamento <= 0:
                continue
            esperado_ate_hoje = orcamento * (dias_passados / dias_no_mes)
            percentagem = (total_mes / orcamento) * 100 if orcamento > 0 else 0
            if total_mes < esperado_ate_hoje * 0.5:
                avisos.append({
                    "titulo": f"📉 **Orcamento do pais** — Apenas {percentagem:.0f}%",
                    "detalhe": f"Vendido: {_fmt_kz(total_mes)} de {_fmt_kz(orcamento)}",
                    "accao": "Rever estrategia ou ajustar meta.",
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
                "titulo": f"🚨 **{len(vencidos)} produto(s) VENCIDO(S)**",
                "detalhe": f"Ex: {vencidos[0].get('produto_nome', '?')} — lote {vencidos[0].get('numero_lote', '?')}",
                "accao": "Retirar imediatamente do stock e registar perda.",
            })
        if urgentes:
            avisos.append({
                "titulo": f"⏰ **{len(urgentes)} produto(s) a vencer em 30 dias**",
                "detalhe": f"Ex: {urgentes[0].get('produto_nome', '?')} — vence a {urgentes[0].get('data_validade', '?')}",
                "accao": "Promover vendas ou devolver ao fornecedor.",
            })
        if len(validades) > len(vencidos) + len(urgentes):
            informacoes.append({
                "titulo": f"📅 **{len(validades) - len(vencidos) - len(urgentes)} produto(s) a vencer em 31-90 dias**",
                "detalhe": "Monitorizar nos proximos meses.",
                "accao": "Verificar semanalmente.",
            })

    if estoque_baixo:
        informacoes.append({
            "titulo": f"📦 **{len(estoque_baixo)} produto(s) com estoque baixo**",
            "detalhe": f"Ex: {estoque_baixo[0].get('nome', '?')} — {estoque_baixo[0].get('estoque_atual', 0)} un. (min: {estoque_baixo[0].get('estoque_minimo', 0)})",
            "accao": "Fazer encomenda ao fornecedor.",
        })

    st.subheader("📊 Resumo")
    c1, c2, c3 = st.columns(3)
    with c1:
        if criticos: st.error(f"🔴 **{len(criticos)}** critico(s)")
        else: st.success("✅ Sem criticos")
    with c2:
        if avisos: st.warning(f"🟡 **{len(avisos)}** aviso(s)")
        else: st.success("✅ Sem avisos")
    with c3:
        if informacoes: st.info(f"🔵 **{len(informacoes)}** informacao(oes)")
        else: st.success("✅ Sem informacoes")

    st.markdown("---")

    if criticos:
        st.subheader("🔴 Criticos")
        for a in criticos:
            with st.container():
                st.error(f"{a['titulo']}\n\n{a['detalhe']}\n\n💡 _{a['accao']}_")
        st.markdown("")

    if avisos:
        st.subheader("🟡 Avisos")
        for a in avisos:
            with st.container():
                st.warning(f"{a['titulo']}\n\n{a['detalhe']}\n\n💡 _{a['accao']}_")
        st.markdown("")

    if informacoes:
        st.subheader("🔵 Informacoes")
        for a in informacoes:
            with st.container():
                st.info(f"{a['titulo']}\n\n{a['detalhe']}\n\n💡 _{a['accao']}_")
        st.markdown("")

    if not criticos and not avisos and not informacoes:
        st.success("✅ Tudo em ordem! Nenhum alerta no momento.")
        st.balloons()

    st.markdown("---")
    st.caption(f"🕐 Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def mostrar_orcamentos():
    st.title("💰 Orcamentos")
    st.caption("Metas mensais por farmacia e global do pais")
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 2, 1])
    hoje = datetime.now()

    with col1:
        mes_escolhido = st.selectbox("📅 Mes", MESES, index=hoje.month - 1, key="orc_mes")
    with col2:
        anos = anos_disponiveis()
        ano_escolhido = st.selectbox("📆 Ano", anos, index=0, key="orc_ano")
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Atualizar", use_container_width=True, key="orc_refresh"):
            st.cache_data.clear()
            st.rerun()

    mes_num = MESES.index(mes_escolhido) + 1
    st.markdown("---")

    with st.spinner("A carregar dados..."):
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

    st.subheader(f"🎯 Orcamento do Pais — {mes_escolhido} {ano_escolhido}")

    if orcamento_total > 0:
        col_a, col_b, col_c = st.columns(3)
        with col_a: st.metric("🎯 Orcamento", _fmt_kz(orcamento_total))
        with col_b: st.metric("💰 Vendido", _fmt_kz(vendido_total))
        with col_c:
            delta = "✅ Batida!" if perc_total >= 100 else "⚠️ Abaixo"
            st.metric("📊 Atingido", f"{perc_total:.1f}%", delta=delta)

        progresso = min(perc_total / 100, 1.0)
        st.progress(progresso)

        if perc_total >= 100:
            st.success(f"🎉 Meta batida! Superou em {_fmt_kz(vendido_total - orcamento_total)}")
        elif perc_total >= 70:
            st.info(f"📈 Bom progresso! Falta {_fmt_kz(orcamento_total - vendido_total)}")
        else:
            st.warning(f"⚠️ Abaixo do esperado. Falta {_fmt_kz(orcamento_total - vendido_total)}")
    else:
        st.info("📌 Ainda nao ha orcamento definido para este mes.")
        st.markdown("**Define o primeiro orcamento em baixo.** 👇")

    st.markdown("---")
    st.subheader("📊 Por Farmacia")

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
            if perc >= 100: estado = "🟢 Batida"
            elif perc >= 70: estado = "🟡 Bom"
            elif perc >= 30: estado = "🟠 Baixo"
            else: estado = "🔴 Critico"
            perc_txt = f"{perc:.0f}%"
        else:
            estado = "⚪ Sem meta"
            perc_txt = "—"

        row = st.columns([2.5, 1.5, 1.5, 1, 1.5])
        with row[0]:
            st.markdown(f"**{f['nome']}**")
            st.caption(f"📍 {f.get('endereco', '-')}")
        with row[1]:
            if orcamento > 0:
                st.markdown(_fmt_kz(orcamento))
            else:
                st.markdown("_nao definido_")
        with row[2]: st.markdown(f"**{_fmt_kz(vendido)}**")
        with row[3]: st.markdown(perc_txt)
        with row[4]: st.markdown(estado)

        st.markdown("")

    st.markdown("---")
    st.subheader("✏️ Definir / Editar Orcamento")

    with st.form("form_orcamento"):
        c1, c2 = st.columns(2)
        with c1:
            farm_escolhida = st.selectbox(
                "🏥 Farmacia",
                farmacias,
                format_func=lambda f: f["nome"],
                key="orc_farm_edit",
            )
        with c2:
            valor_actual = metas_por_farm.get(farm_escolhida["id"], {}).get("orcamento_mes", 0) or 0
            valor_orc = st.number_input(
                "💰 Orcamento (Kz)",
                min_value=0.0,
                value=float(valor_actual),
                step=100000.0,
                key="orc_valor_edit",
            )

        obs = st.text_input(
            "📝 Observacoes (opcional)",
            value=metas_por_farm.get(farm_escolhida["id"], {}).get("observacoes", "") or "",
            key="orc_obs_edit",
        )

        submitted = st.form_submit_button(
            "💾 Guardar Orcamento",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if valor_orc <= 0:
            st.error("O orcamento deve ser superior a 0.")
        else:
            with st.spinner("A guardar no Supabase..."):
                from services.supabase_client import criar_meta
                ok = criar_meta(
                    mes=mes_num,
                    ano=ano_escolhido,
                    farmacia_id=farm_escolhida["id"],
                    orcamento=valor_orc,
                    observacoes=obs,
                    definido_por="CEO",
                )

            if ok:
                st.success(f"✅ Orcamento guardado: {farm_escolhida['nome']} → {_fmt_kz(valor_orc)}")
                st.balloons()
                st.cache_data.clear()
                import time as _t
                _t.sleep(1)
                st.rerun()
            else:
                st.error("❌ Erro ao guardar. Verifica a ligacao.")

    st.markdown("---")

    if metas:
        st.subheader("📋 Metas Definidas")
        for m in metas:
            fid = m.get("farmacia_id")
            f_nome = "?"
            for f in farmacias:
                if f["id"] == fid:
                    f_nome = f["nome"]
                    break

            c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 0.8])
            with c1: st.markdown(f"**{f_nome}**")
            with c2: st.markdown(_fmt_kz(m.get("orcamento_mes", 0)))
            with c3: st.caption(f"Definido por: {m.get('definido_por', '-')}")
            with c4:
                if st.button("🗑️", key=f"del_meta_{m['id']}", help="Apagar meta"):
                    from services.supabase_client import apagar_meta
                    if apagar_meta(m["id"]):
                        st.success("Meta apagada.")
                        st.cache_data.clear()
                        import time as _t
                        _t.sleep(1)
                        st.rerun()

    st.markdown("---")
    st.caption(f"🕐 Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def mostrar_vendas():
    _placeholder("Vendas", "📈", "Aqui vais ver as vendas detalhadas.", "9.6")


def mostrar_stock():
    _placeholder("Stock", "📦", "Aqui vais ver o stock de todas as farmacias.", "9.7")


def mostrar_perdas():
    _placeholder("Perdas", "💸", "Aqui vais ver as perdas por tipo.", "9.7")


def mostrar_financeiro():
    _placeholder("Financeiro", "🏦", "Aqui vais ver depositos e saldos.", "9.8")


def mostrar_utilizadores():
    _placeholder("Utilizadores", "👥", "Aqui vais ver os utilizadores.", "9.8")


def mostrar_diagnostico():
    _placeholder("Diagnostico", "🩺", "Aqui vais ver o diagnostico inteligente.", "9.9")


def mostrar_definicoes():
    _placeholder("Definicoes", "⚙️", "Aqui vais configurar preferencias.", "9.9")