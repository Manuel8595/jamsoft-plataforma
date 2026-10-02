"""
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
    vendas_detalhadas_mes,
    vendas_por_forma_pagamento,
    vendas_por_dia_mes,
    vendas_por_hora_mes,
    top_produtos_mes,
    top_clientes_mes,
    listar_produtos_stock,
    lotes_a_vencer,
    resumo_stock,
    listar_perdas,
    resumo_perdas,
    listar_turnos_periodo,
    resumo_turnos,
    listar_depositos,
    resumo_depositos,
    listar_todos_utilizadores,
    resumo_utilizadores,
    top_vendedores_mes,
    diagnostico_sistema,
    info_plataforma,
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
    st.caption("Metas por período: dia / semana / mes / ano")
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

    # ============================================================
    # CÁLCULO DAS METAS POR PERÍODO
    # ============================================================
    from calendar import monthrange

    # Número de dias do mês
    dias_no_mes = monthrange(ano_escolhido, mes_num)[1]

    # Dias úteis (aproximação: 30 dias como padrão)
    # Número de semanas no mês
    semanas_no_mes = dias_no_mes / 7

    # Ano = mês × 12
    meta_anual = orcamento_total * 12

    # Divisões do mês
    meta_diaria = orcamento_total / dias_no_mes if dias_no_mes > 0 else 0
    meta_semanal = orcamento_total / semanas_no_mes if semanas_no_mes > 0 else 0

    # ============================================================
    # ORÇAMENTO DO PAÍS — VISTA GERAL
    # ============================================================
    st.subheader(f"Orcamento do Pais - {mes_escolhido} {ano_escolhido}")

    if orcamento_total > 0:
        col_a, col_b, col_c = st.columns(3)
        with col_a: st.metric("Orcamento Total", _fmt_kz(orcamento_total))
        with col_b: st.metric("Vendido", _fmt_kz(vendido_total))
        with col_c:
            perc_total = (vendido_total / orcamento_total * 100) if orcamento_total > 0 else 0
            st.metric("Atingido", f"{perc_total:.1f}%")

        progresso = min(perc_total / 100, 1.0)
        st.progress(progresso)

        if perc_total >= 100:
            st.success(f"Meta batida! Superou em {_fmt_kz(vendido_total - orcamento_total)}")
        else:
            st.warning(f"Falta {_fmt_kz(orcamento_total - vendido_total)}")

        st.markdown("")
        st.markdown("**Distribuicao automatica por periodo:**")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Meta Diaria", _fmt_kz(meta_diaria), f"x {dias_no_mes} dias")
        with c2:
            st.metric("Meta Semanal", _fmt_kz(meta_semanal), f"~{semanas_no_mes:.1f} semanas")
        with c3:
            st.metric("Meta Mensal", _fmt_kz(orcamento_total))
        with c4:
            st.metric("Meta Anual", _fmt_kz(meta_anual), f"x 12 meses")
    else:
        st.info("Sem orcamento definido para este mes.")

    # ============================================================
    # METAS DETALHADAS POR PERÍODO (progresso real)
    # ============================================================
    if orcamento_total > 0:
        st.markdown("---")
        st.subheader("Progresso por periodo")

        # Calcular vendas por período (do mês escolhido)
        # Dia de hoje
        hoje_data = datetime.now()
        if hoje_data.month == mes_num and hoje_data.year == ano_escolhido:
            dia_actual = hoje_data.day
        else:
            dia_actual = 1

        # Vendas do dia (só se for o mês actual)
        vendas_hoje = 0
        if hoje_data.month == mes_num and hoje_data.year == ano_escolhido:
            try:
                from services.supabase_client import vendas_ultimos_dias
                v_hoje = vendas_ultimos_dias(dias=1)
                vendas_hoje = sum(v.get("total", 0) or 0 for v in v_hoje)
            except Exception:
                vendas_hoje = 0

        # Vendas da semana (últimos 7 dias)
        try:
            from services.supabase_client import vendas_ultimos_dias
            v_semana = vendas_ultimos_dias(dias=7)
            vendas_semana = sum(v.get("total", 0) or 0 for v in v_semana)
        except Exception:
            vendas_semana = 0

        # Vendas do mês
        vendas_mes = vendido_total

        # Vendas do ano
        try:
            from services.supabase_client import vendas_por_mes
            vendas_ano = 0
            for m in range(1, 13):
                vs = vendas_por_mes(m, ano_escolhido)
                vendas_ano += sum(v.get("total", 0) or 0 for v in vs)
        except Exception:
            vendas_ano = 0

        # ===== Meta Diária =====
        col1, col2, col3 = st.columns(3)
        with col1:
            perc_dia = (vendas_hoje / meta_diaria * 100) if meta_diaria > 0 else 0
            st.metric("Meta Diaria (hoje)", _fmt_kz(meta_diaria))
        with col2:
            st.metric("Vendido hoje", _fmt_kz(vendas_hoje))
        with col3:
            st.metric("Atingido hoje", f"{perc_dia:.1f}%")
        st.progress(min(perc_dia / 100, 1.0))

        st.markdown("")

        # ===== Meta Semanal =====
        col1, col2, col3 = st.columns(3)
        with col1:
            perc_sem = (vendas_semana / meta_semanal * 100) if meta_semanal > 0 else 0
            st.metric("Meta Semanal", _fmt_kz(meta_semanal))
        with col2:
            st.metric("Vendido (7 dias)", _fmt_kz(vendas_semana))
        with col3:
            st.metric("Atingido semana", f"{perc_sem:.1f}%")
        st.progress(min(perc_sem / 100, 1.0))

        st.markdown("")

        # ===== Meta Mensal =====
        col1, col2, col3 = st.columns(3)
        with col1:
            perc_mes = (vendas_mes / orcamento_total * 100) if orcamento_total > 0 else 0
            st.metric("Meta Mensal", _fmt_kz(orcamento_total))
        with col2:
            st.metric("Vendido no mes", _fmt_kz(vendas_mes))
        with col3:
            st.metric("Atingido mes", f"{perc_mes:.1f}%")
        st.progress(min(perc_mes / 100, 1.0))

        st.markdown("")

        # ===== Meta Anual =====
        col1, col2, col3 = st.columns(3)
        with col1:
            perc_ano = (vendas_ano / meta_anual * 100) if meta_anual > 0 else 0
            st.metric("Meta Anual", _fmt_kz(meta_anual))
        with col2:
            st.metric("Vendido no ano", _fmt_kz(vendas_ano))
        with col3:
            st.metric("Atingido ano", f"{perc_ano:.1f}%")
        st.progress(min(perc_ano / 100, 1.0))

    # ============================================================
    # POR FARMÁCIA
    # ============================================================
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


    # ============================================================
    # IA SUGERE ORÇAMENTOS
    # ============================================================
    st.markdown("---")
    st.subheader("🤖 IA Sugere Orcamentos")

    st.caption(
        "A IA analisa o historico do ano passado, os ultimos 3 meses "
        "e a tendencia de crescimento/queda para sugerir um orcamento."
    )

    if st.button("🤖 Gerar Sugestoes da IA", use_container_width=True, key="btn_ia_sugerir"):
        with st.spinner("A analisar historico..."):
            from services.supabase_client import sugerir_orcamento_farmacia
            sugestoes = {}
            for f in farmacias:
                sug = sugerir_orcamento_farmacia(f["id"], mes_num, ano_escolhido)
                sugestoes[f["id"]] = sug

        st.session_state["sugestoes_ia"] = sugestoes
        st.session_state["sugestoes_mes"] = mes_num
        st.session_state["sugestoes_ano"] = ano_escolhido

    # Mostrar sugestões se existirem
    if "sugestoes_ia" in st.session_state:
        sugestoes = st.session_state["sugestoes_ia"]
        sug_mes = st.session_state.get("sugestoes_mes")
        sug_ano = st.session_state.get("sugestoes_ano")

        # Só mostrar se for o mesmo mês/ano escolhido
        if sug_mes == mes_num and sug_ano == ano_escolhido:
            st.markdown("")
            st.markdown("**Sugestoes geradas:**")
            st.markdown("")

            for f in farmacias:
                fid = f["id"]
                sug = sugestoes.get(fid, {})
                valor = sug.get("sugestao", 0)
                base_ap = sug.get("base_ano_passado", 0)
                base_3m = sug.get("base_3meses", 0)
                tend = sug.get("tendencia", 0)
                metodo = sug.get("metodo", "")

                with st.container(border=True):
                    col_a, col_b = st.columns([3, 2])

                    with col_a:
                        st.markdown(f"**{f['nome']}**")

                        if metodo == "completo":
                            st.caption(
                                f"Ano passado: {_fmt_kz(base_ap)} | "
                                f"Media 3 meses: {_fmt_kz(base_3m)} | "
                                f"Tendencia: {tend:+.1f}%/mes"
                            )
                        elif metodo == "ano_passado":
                            st.caption(f"Baseado no ano passado: {_fmt_kz(base_ap)}")
                        elif metodo == "ultimos_3meses":
                            st.caption(f"Baseado nos ultimos 3 meses: {_fmt_kz(base_3m)}")
                        elif metodo == "media_geral":
                            st.caption("Sem historico — usando media das outras farmacias")
                        else:
                            st.caption("Sem dados suficientes")

                    with col_b:
                        st.metric("Sugestao IA", _fmt_kz(valor))

                # Botão para aceitar
                col_btn1, col_btn2 = st.columns([1, 5])
                with col_btn1:
                    if st.button("✅ Aceitar", key=f"aceitar_ia_{fid}"):
                        if valor > 0:
                            from services.supabase_client import criar_meta
                            ok = criar_meta(
                                mes=mes_num, ano=ano_escolhido,
                                farmacia_id=fid,
                                orcamento=valor,
                                observacoes=f"Sugerido pela IA ({metodo})",
                                definido_por="IA",
                            )
                            if ok:
                                st.success(f"Guardado: {f['nome']} → {_fmt_kz(valor)}")
                                st.cache_data.clear()
                                import time as _t
                                _t.sleep(1)
                                st.rerun()
                            else:
                                st.error("Erro ao guardar")
                        else:
                            st.warning("Valor sugerido e 0")

            st.markdown("---")

    # ============================================================
    # DEFINIR / EDITAR
    # ============================================================
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
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def mostrar_stock():
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
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def mostrar_perdas():
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
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def mostrar_financeiro():
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
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def mostrar_utilizadores():
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
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def mostrar_diagnostico():
    st.title("Diagnostico")
    st.caption("Saude do sistema e detecao automatica de problemas")
    st.markdown("---")

    col_a, col_b = st.columns([6, 1])
    with col_b:
        if st.button("🔄 Re-analisar", use_container_width=True, key="diag_refresh"):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("A analisar sistema..."):
        resultado = diagnostico_sistema()

    problemas = resultado.get("problemas", [])
    avisos = resultado.get("avisos", [])
    info = resultado.get("info", [])
    tabelas = resultado.get("tabelas", {})

    # Resumo
    st.subheader("📊 Resumo do Sistema")
    c1, c2, c3 = st.columns(3)
    with c1:
        if problemas:
            st.error(f"🔴 **{len(problemas)}** problema(s)")
        else:
            st.success("✅ Sem problemas")
    with c2:
        if avisos:
            st.warning(f"🟡 **{len(avisos)}** aviso(s)")
        else:
            st.success("✅ Sem avisos")
    with c3:
        if info:
            st.info(f"🔵 **{len(info)}** info")

    st.markdown("---")

    # Problemas
    if problemas:
        st.subheader("🔴 Problemas Criticos")
        for p in problemas:
            with st.container():
                st.error(
                    f"**{p['area']}**\n\n"
                    f"{p['problema']}\n\n"
                    f"💡 **Solucao:** {p['solucao']}"
                )  
                      
                st.markdown("")

    # Avisos
    if avisos:
        st.subheader("🟡 Avisos")
        for a in avisos:
            with st.container():
                st.warning(
                    f"**{a['area']}**\n\n"
                    f"{a['problema']}\n\n"
                    f"💡 **Solucao:** {a['solucao']}"
                )
        st.markdown("")

    # Informacoes
    if info:
        st.subheader("🔵 Informacoes")
        for i in info:
            st.info(i)
        st.markdown("")

    st.markdown("---")
    st.subheader("📋 Estado das Tabelas no Supabase")

    if tabelas:
        cols = st.columns(2)
        items = list(tabelas.items())
        for idx, (nome, estado) in enumerate(items):
            with cols[idx % 2]:
                if estado == "OK":
                    st.markdown(f"✅ **{nome}** — com dados")
                elif estado == "vazio":
                    st.markdown(f"⚪ **{nome}** — vazio")
                else:
                    st.markdown(f"❌ **{nome}** — erro")

    st.markdown("---")

    if not problemas and not avisos:
        st.success("✅ **Sistema saudavel!** Nenhum problema detectado.")
        st.balloons()

    st.markdown("---")
    st.caption(f"Ultima analise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def mostrar_definicoes():
    st.title("Definicoes")
    st.caption("Informacao da plataforma e preferencias")
    st.markdown("---")

    info = info_plataforma()

    st.subheader("ℹ️ Informacao da Plataforma")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Versao:** {info['versao']}")
        st.markdown(f"**Servidor:** {info['data_servidor']}")
    with c2:
        st.markdown(f"**Supabase URL:**")
        st.code(info['supabase_url'], language="text")

    st.markdown("---")
    st.subheader("✅ Fases Concluidas")

    for fase in info['fases_concluidas']:
        st.markdown(f"✅ {fase}")

    st.markdown("---")
    st.subheader("📊 Estatisticas da Plataforma")

    with st.spinner("A carregar estatisticas..."):
        try:
            farmacias = listar_farmacias()
            num_farmacias = len(farmacias)
        except Exception:
            num_farmacias = 0

        try:
            utilizadores = listar_todos_utilizadores()
            num_users = len(utilizadores)
        except Exception:
            num_users = 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Farmacias", f"{num_farmacias}")
    with c2:
        st.metric("Utilizadores", f"{num_users}")
    with c3:
        st.metric("Fases activas", f"{len(info['fases_concluidas'])}")

    st.markdown("---")
    st.subheader("🔧 Acoes Rapidas")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Limpar Cache", use_container_width=True, key="def_limpar"):
            st.cache_data.clear()
            st.success("Cache limpa com sucesso!")
            st.rerun()

    with c2:
        if st.button("📊 Actualizar Tudo", use_container_width=True, key="def_actualizar"):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    st.subheader("📞 Suporte")

    st.info(
        "**JAM Soft - Plataforma de Monitorizacao**\n\n"
        "Para suporte tecnico, contactar:\n"
        "- Email: suporte@jamsoft.ao\n"
        "- Tel: +244 XXX XXX XXX"
    )

    st.markdown("---")
    st.caption("JAM Soft 2026 - Todos os direitos reservados")
