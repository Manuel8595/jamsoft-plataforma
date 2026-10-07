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

    vendas_ultimos_dias,

    top_produtos_mes,

    top_clientes_mes,

    listar_produtos_stock,

    lotes_a_vencer,

    resumo_stock,

    listar_perdas,

    resumo_perdas,

    listar_turnos_período,

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





def _placeholder(titulo, icone, descrição, fase):

    st.title(f"{icone} {titulo}")

    st.markdown("---")

    st.info(f"Em construcao - Fase {fase}")





def mostrar_ranking():

    st.title("Ranking de Farmacias")

    st.caption("Desempenho comparado — vendas, metas e crescimento")

    st.markdown("---")



    col1, col2, col3, col4 = st.columns([2, 2, 1, 2])

    hoje = datetime.now()



    with col1:

        mes_escolhido = st.selectbox("Mes", MESES, index=hoje.month - 1, key="rank_mes")

    with col2:

        anos = anos_disponiveis()

        ano_escolhido = st.selectbox("Ano", anos, index=0, key="rank_ano")

    with col3:

        st.write("")

        st.write("")

        if st.button("🔄", use_container_width=True, key="rank_refresh"):

            st.cache_data.clear()

            st.rerun()

    with col4:

        st.write("")

        comparar = st.checkbox("Comparar com mes anterior", key="rank_comparar")



    mes_num = MESES.index(mes_escolhido) + 1



    # Mês anterior

    mes_ant = mes_num - 1

    ano_ant = ano_escolhido

    if mes_ant < 1:

        mes_ant = 12

        ano_ant -= 1



    st.markdown("---")



    with st.spinner("A carregar..."):

        resumo_atual = resumo_por_farmacia_mes(mes_num, ano_escolhido)

        metas = metas_activas(mes_num, ano_escolhido)

        resumo_ant = resumo_por_farmacia_mes(mes_ant, ano_ant) if comparar else {}



    metas_por_farm = {}

    for m in metas:

        fid = m.get("farmacia_id")

        if fid is not None:

            metas_por_farm[fid] = m



    total_geral = sum(r["total"] for r in resumo_atual.values())

    num_geral = sum(r["num_vendas"] for r in resumo_atual.values())

    ticket_geral = (total_geral / num_geral) if num_geral > 0 else 0

    num_farmacias = len(resumo_atual)



    st.subheader(f"{mes_escolhido} {ano_escolhido}")

    c1, c2, c3, c4 = st.columns(4)

    with c1: st.metric("Lojas", f"{num_farmacias}")

    with c2: st.metric("Total Vendas", _fmt_kz(total_geral))

    with c3: st.metric("Num. Vendas", f"{num_geral}")

    with c4: st.metric("Ticket Médio", _fmt_kz(ticket_geral))



    st.markdown("---")

    st.subheader("🏆 Ranking")



    ranking = sorted(resumo_atual.values(), key=lambda x: x["total"], reverse=True)

    if not ranking:

        st.warning("Sem dados.")

        return



    for i, r in enumerate(ranking, start=1):

        f = r["farmacia"]

        fid = f["id"]

        total = r["total"]

        num = r["num_vendas"]

        ticket = r["ticket_medio"]



        if i == 1: medalha = "🥇"

        elif i == 2: medalha = "🥈"

        elif i == 3: medalha = "🥉"

        else: medalha = f"{i}º"



        meta = metas_por_farm.get(fid)

        orcamento = meta.get("orcamento_mes", 0) if meta else 0

        perc_meta = (total / orcamento * 100) if orcamento > 0 else 0



        cresc = None

        if comparar:

            total_ant = resumo_ant.get(fid, {}).get("total", 0)

            if total_ant > 0:

                cresc = ((total - total_ant) / total_ant) * 100



        if orcamento > 0:

            if perc_meta >= 100:

                estado_txt = f"✅ {perc_meta:.0f}%"

            elif perc_meta >= 70:

                estado_txt = f"🟢 {perc_meta:.0f}%"

            elif perc_meta >= 30:

                estado_txt = f"🟡 {perc_meta:.0f}%"

            else:

                estado_txt = f"🔴 {perc_meta:.0f}%"

        else:

            estado_txt = "—"



        with st.container(border=True):

            row = st.columns([0.5, 2.5, 1.3, 1, 1.2, 1.2, 1.2])

            with row[0]:

                st.markdown(f"## {medalha}")

            with row[1]:

                st.markdown(f"### {f['nome']}")

                st.caption(f"{f.get('endereco', '-')}")

            with row[2]:

                st.metric("Vendido", _fmt_kz(total))

            with row[3]:

                st.metric("Vendas", f"{num}")

            with row[4]:

                st.metric("Ticket", _fmt_kz(ticket))

            with row[5]:

                if orcamento > 0:

                    st.metric("Meta", _fmt_kz(orcamento))

                else:

                    st.markdown("**Meta**")

                    st.caption("_nao definida_")

            with row[6]:

                st.markdown("**Estado**")

                st.markdown(f"**{estado_txt}**")



            if comparar and cresc is not None:

                st.markdown("")

                if cresc > 5:

                    st.success(f"📈 Cresceu {cresc:+.1f}% vs mês anterior")

                elif cresc < -5:

                    st.error(f"📉 Caiu {cresc:+.1f}% vs mês anterior")

                else:

                    st.info(f"➡️ Estável {cresc:+.1f}% vs mês anterior")



    st.markdown("---")

    st.subheader("Grafico de Vendas")

    dados_grafico = {r["farmacia"]["nome"][:20]: r["total"] for r in ranking}

    st.bar_chart(dados_grafico, height=320, use_container_width=True)



    # ============================================================

    # RENTABILIDADE POR FARMACIA

    # ============================================================

    st.markdown("---")

    st.subheader("📊 Rentabilidade e Sugestões (IA)")

    st.caption(

        "A IA analisa margem, ticket médio, tendencia e stock. "

        "Sugestões são actualizadas automáticamente."

    )



    with st.spinner("A carregar farmacias..."):

        farmacias = listar_farmacias()



    if st.button("🤖 Analisar rentabilidade", use_container_width=True, key="btn_rent"):

        with st.spinner("A analisar..."):

            from services.supabase_client import calcular_rentabilidade_farmacia

            rentabilidades = {}

            for f in farmacias:

                rent = calcular_rentabilidade_farmacia(f["id"], ano_escolhido)

                rentabilidades[f["id"]] = rent

        st.session_state["rentabilidades"] = rentabilidades

        st.session_state["rent_ano"] = ano_escolhido



    if "rentabilidades" in st.session_state:

        rent_data = st.session_state["rentabilidades"]

        rent_ano = st.session_state.get("rent_ano")



        if rent_ano == ano_escolhido:

            for f in farmacias:

                rent = rent_data.get(f["id"])

                if not rent:

                    continue



                st.markdown("")

                with st.container(border=True):

                    st.markdown(f"### {f['nome']}")



                    ano_tot = rent.get("ano_total", {})

                    c1, c2, c3, c4 = st.columns(4)

                    with c1:

                        st.metric("Vendas (ano)", _fmt_kz(ano_tot.get("vendas", 0)))

                    with c2:

                        st.metric("Custo (ano)", _fmt_kz(ano_tot.get("custo", 0)))

                    with c3:

                        st.metric("Lucro (ano)", _fmt_kz(ano_tot.get("lucro", 0)))

                    with c4:

                        margem = ano_tot.get("margem_pct", 0)

                        if margem >= 30:

                            st.metric("Margem", f"🟢 {margem:.1f}%")

                        elif margem >= 20:

                            st.metric("Margem", f"🟡 {margem:.1f}%")

                        else:

                            st.metric("Margem", f"🔴 {margem:.1f}%")



                    st.markdown("**Por ciclo (3 meses):**")

                    ciclos = rent.get("ciclos", {})

                    if ciclos:

                        cols_cic = st.columns(len(ciclos))

                        for idx, (nome_ciclo, dados_cic) in enumerate(ciclos.items()):

                            with cols_cic[idx]:

                                st.markdown(f"_{nome_ciclo}_")

                                st.markdown(f"**{_fmt_kz(dados_cic.get('vendas', 0))}**")

                                st.caption(

                                    f"Lucro: {_fmt_kz(dados_cic.get('lucro', 0))} | "

                                    f"Margem: {dados_cic.get('margem_pct', 0):.0f}%"

                                )



                    sugestões = rent.get("sugestões", [])

                    if sugestões:

                        st.markdown("**🤖 Sugestões da IA:**")

                        for s in sugestões:

                            nivel = s.get("nivel", "INFO")

                            msg = f"**{s.get('titulo', '?')}** — {s.get('detalhe', '')} 💡 {s.get('acção', '')}"

                            if nivel == "CRITICO":

                                st.error(msg)

                            elif nivel == "AVISO":

                                st.warning(msg)

                            else:

                                st.info(msg)

                    else:

                        st.success("✅ Sem sugestões — desempenho saudável.")





def mostrar_alertas():

    st.title("Alertas")

    st.caption("Monitorização automática")

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

        # Depositos pendentes (mes actual)

        depositos_pendentes = listar_depositos()



    críticos = []

    avisos = []

    informacoes = []



    for f in farmacias:

        fid = f["id"]

        info = ultimas.get(fid, {})

        dias = info.get("dias_atras")



        if dias is None:

            críticos.append({

                "titulo": f"{f['nome']} - Nunca comunicou",

                "detalhe": "Ainda nao enviou nenhuma venda.",

                "acção": "Verificar JAM Soft e internet.",

            })

        elif dias == 0:

            pass

        elif dias == 1:

            avisos.append({

                "titulo": f"{f['nome']} - Sem vendas ontem",

                "detalhe": f"Ultima: {info.get('data', '?')}",

                "acção": "Confirmar fecho.",

            })

        elif dias <= 3:

            avisos.append({

                "titulo": f"{f['nome']} - Sem comunicar ha {dias} dias",

                "detalhe": f"Ultima: {info.get('data', '?')}",

                "acção": "Ligar para a farmacia.",

            })

        else:

            críticos.append({

                "titulo": f"{f['nome']} - Sem comunicar ha {dias} dias",

                "detalhe": f"Ultima: {info.get('data', '?')}",

                "acção": "Contactar gerente URGENTE.",

            })



    for t in turnos_dif:

        dif = t.get("diferenca", 0)

        tipo = "SOBRA" if dif > 0 else "FALTA"

        avisos.append({

            "titulo": f"{t.get('utilizador_nome', '?')} - {tipo} de {_fmt_kz(abs(dif))}",

            "detalhe": f"Turno em {t.get('data_abertura', '?')[:10]}",

            "acção": "Verificar contagem.",

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

            críticos.append({

                "titulo": f"{len(vencidos)} produto(s) VENCIDO(S)",

                "detalhe": f"Ex: {vencidos[0].get('produto_nome', '?')}",

                "acção": "Retirar do stock.",

            })

        if urgentes:

            avisos.append({

                "titulo": f"{len(urgentes)} produto(s) a vencer em 30 dias",

                "detalhe": f"Ex: {urgentes[0].get('produto_nome', '?')}",

                "acção": "Promover vendas.",

            })



    if estoque_baixo:

        informacoes.append({

            "titulo": f"{len(estoque_baixo)} produto(s) com estoque baixo",

            "detalhe": f"Ex: {estoque_baixo[0].get('nome', '?')}",

            "acção": "Encomendar.",

        })





    # ─── Depósitos pendentes ───

    if depositos_pendentes:

        from datetime import datetime as _dt_alert



        registados_antigos = []

        aguarda_antigos = []



        for d in depositos_pendentes:

            estado = d.get("estado") or ""

            data_str = d.get("data") or ""



            if not data_str:

                continue



            try:

                data_dep = _dt_alert.strptime(data_str[:10], "%Y-%m-%d")

                dias_atras = (_dt_alert.now() - data_dep).days

            except Exception:

                continue



            ref = d.get("referencia") or "?"

            valor = d.get("valor") or 0

            banco = d.get("banco") or "?"



            if estado == "REGISTADO" and dias_atras >= 1:

                registados_antigos.append({

                    "ref": ref,

                    "valor": valor,

                    "banco": banco,

                    "dias": dias_atras,

                })

            elif estado == "AGUARDA_CONFIRMACAO" and dias_atras >= 3:

                aguarda_antigos.append({

                    "ref": ref,

                    "valor": valor,

                    "banco": banco,

                    "dias": dias_atras,

                })



        if registados_antigos:

            for r in registados_antigos[:3]:

                avisos.append({

                    "titulo": f"Deposito {r['ref']} nao foi registado no banco",

                    "detalhe": f"Kz {r['valor']:,.0f} | {r['banco']} | {r['dias']} dia(s) atras",

                    "acção": "Gerente deve registar comprovante.",

                })



        if aguarda_antigos:

            for r in aguarda_antigos[:3]:

                críticos.append({

                    "titulo": f"Deposito {r['ref']} aguarda confirmacao ha {r['dias']} dias",

                    "detalhe": f"Kz {r['valor']:,.0f} | {r['banco']}",

                    "acção": "CEO deve confirmar no extrato bancario.",

                })

                

    st.subheader("Resumo")

    c1, c2, c3 = st.columns(3)

    with c1:

        if críticos: st.error(f"{len(críticos)} crítico(s)")

        else: st.success("Sem críticos")

    with c2:

        if avisos: st.warning(f"{len(avisos)} aviso(s)")

        else: st.success("Sem avisos")

    with c3:

        if informacoes: st.info(f"{len(informacoes)} info")

        else: st.success("Sem info")



    st.markdown("---")



    if críticos:

        st.subheader("Críticos")

        for a in críticos:

            st.error(f"{a['titulo']} - {a['detalhe']} - {a['acção']}")



    if avisos:

        st.subheader("Avisos")

        for a in avisos:

            st.warning(f"{a['titulo']} - {a['detalhe']} - {a['acção']}")



    if informacoes:

        st.subheader("Informações")

        for a in informacoes:

            st.info(f"{a['titulo']} - {a['detalhe']} - {a['acção']}")





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



    from calendar import monthrange

    dias_no_mes = monthrange(ano_escolhido, mes_num)[1]

    semanas_no_mes = dias_no_mes / 7

    meta_anual = orcamento_total * 12

    meta_diaria = orcamento_total / dias_no_mes if dias_no_mes > 0 else 0

    meta_semanal = orcamento_total / semanas_no_mes if semanas_no_mes > 0 else 0



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

        st.markdown("**Distribuição automática por período:**")



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



    from services.supabase_client import listar_todas_configs

    todas_configs = listar_todas_configs()



    mostrar_dia_pais = any(c.get("mostrar_dia", True) for c in todas_configs.values()) if todas_configs else True

    mostrar_semana_pais = any(c.get("mostrar_semana", True) for c in todas_configs.values()) if todas_configs else True

    mostrar_mes_pais = any(c.get("mostrar_mes", True) for c in todas_configs.values()) if todas_configs else True

    mostrar_ano_pais = any(c.get("mostrar_ano", True) for c in todas_configs.values()) if todas_configs else True



    if orcamento_total > 0:

        st.markdown("---")

        st.subheader("Progresso por período")



        hoje_data = datetime.now()



        vendas_hoje = 0

        if hoje_data.month == mes_num and hoje_data.year == ano_escolhido:

            try:

                from services.supabase_client import vendas_ultimos_dias

                v_hoje = vendas_ultimos_dias(dias=1)

                vendas_hoje = sum(v.get("total", 0) or 0 for v in v_hoje)

            except Exception:

                vendas_hoje = 0



        try:

            from services.supabase_client import vendas_ultimos_dias

            v_semana = vendas_ultimos_dias(dias=7)

            vendas_semana = sum(v.get("total", 0) or 0 for v in v_semana)

        except Exception:

            vendas_semana = 0



        vendas_mes = vendido_total



        try:

            from services.supabase_client import vendas_por_mes

            vendas_ano = 0

            for m in range(1, 13):

                vs = vendas_por_mes(m, ano_escolhido)

                vendas_ano += sum(v.get("total", 0) or 0 for v in vs)

        except Exception:

            vendas_ano = 0



        if mostrar_dia_pais:

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



        if mostrar_semana_pais:

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



        if mostrar_mes_pais:

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



        if mostrar_ano_pais:

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

    # IA SUGERE ORÇAMENTOS

    # ============================================================

    st.markdown("---")

    st.subheader("🤖 IA Sugere Orcamentos")



    st.caption(

        "A IA analisa o histórico do ano passado, os ultimos 3 meses "

        "e a tendencia de crescimento/queda para sugerir um orcamento."

    )



    if st.button("🤖 Gerar Sugestões da IA", use_container_width=True, key="btn_ia_sugerir"):

        with st.spinner("A analisar histórico..."):

            from services.supabase_client import sugerir_orcamento_farmacia

            sugestões = {}

            for f in farmacias:

                sug = sugerir_orcamento_farmacia(f["id"], mes_num, ano_escolhido)

                sugestões[f["id"]] = sug



        st.session_state["sugestões_ia"] = sugestões

        st.session_state["sugestões_mes"] = mes_num

        st.session_state["sugestões_ano"] = ano_escolhido



    if "sugestões_ia" in st.session_state:

        sugestões = st.session_state["sugestões_ia"]

        sug_mes = st.session_state.get("sugestões_mes")

        sug_ano = st.session_state.get("sugestões_ano")



        if sug_mes == mes_num and sug_ano == ano_escolhido:

            st.markdown("")

            st.markdown("**Sugestões geradas:**")

            st.markdown("")



            for f in farmacias:

                fid = f["id"]

                sug = sugestões.get(fid, {})

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

                            st.caption("Sem histórico — usando media das outras farmacias")

                        else:

                            st.caption("Sem dados suficientes")



                    with col_b:

                        st.metric("Sugestao IA", _fmt_kz(valor))



                # Botões de acção

                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])



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



                with col_btn2:

                    if st.button("✏️ Ajustar", key=f"ajustar_ia_{fid}"):

                        st.session_state[f"ajustar_aberto_{fid}"] = True



                with col_btn3:

                    if st.button("📝 Modo Treino", key=f"treino_ia_{fid}"):

                        st.session_state[f"treino_aberto_{fid}"] = True



                if st.session_state.get(f"ajustar_aberto_{fid}", False):

                    with st.expander("✏️ Ajustar valor", expanded=True):

                        novo_valor = st.number_input(

                            "Valor ajustado (Kz)",

                            min_value=0.0,

                            value=float(valor),

                            step=50000.0,

                            key=f"ajuste_val_{fid}",

                        )

                        notas = st.text_input(

                            "Motivo do ajuste (opcional)",

                            key=f"ajuste_notas_{fid}",

                        )

                        col_a, col_b = st.columns(2)

                        with col_a:

                            if st.button("💾 Guardar ajuste", key=f"save_ajuste_{fid}"):

                                from services.supabase_client import (criar_meta,

                                                                       guardar_ajuste_ceo)

                                ok = criar_meta(

                                    mes=mes_num, ano=ano_escolhido,

                                    farmacia_id=fid,

                                    orcamento=novo_valor,

                                    observacoes=f"Ajustado pelo CEO. {notas}",

                                    definido_por="CEO",

                                )

                                guardar_ajuste_ceo(

                                    farmacia_id=fid,

                                    mes=mes_num,

                                    ano=ano_escolhido,

                                    sugestao_ia=valor,

                                    valor_aceito=novo_valor,

                                    notas=notas,

                                )

                                if ok:

                                    st.success(f"Ajustado: {_fmt_kz(novo_valor)}")

                                    st.session_state[f"ajustar_aberto_{fid}"] = False

                                    st.cache_data.clear()

                                    import time as _t2

                                    _t2.sleep(1)

                                    st.rerun()

                        with col_b:

                            if st.button("❌ Fechar", key=f"close_ajuste_{fid}"):

                                st.session_state[f"ajustar_aberto_{fid}"] = False

                                st.rerun()



                if st.session_state.get(f"treino_aberto_{fid}", False):

                    with st.expander("📝 Modo Treino — Ensina a IA", expanded=True):

                        st.caption(

                            "Ajusta o valor. A IA vai aprender o teu padrão "

                            "e usar nas próximas sugestões (por farmácia + por mês)."

                        )

                        valor_treino = st.number_input(

                            "Valor a ensinar (Kz)",

                            min_value=0.0,

                            value=float(valor),

                            step=50000.0,

                            key=f"treino_val_{fid}",

                        )

                        motivo = st.text_input(

                            "Motivo (ex: Dezembro vende mais)",

                            key=f"treino_notas_{fid}",

                        )

                        if st.button("🧠 Ensinar IA", key=f"ensinar_ia_{fid}"):

                            from services.supabase_client import guardar_ajuste_ceo

                            ok = guardar_ajuste_ceo(

                                farmacia_id=fid,

                                mes=mes_num,

                                ano=ano_escolhido,

                                sugestao_ia=valor,

                                valor_aceito=valor_treino,

                                notas=motivo,

                            )

                            if ok:

                                st.success(f"IA aprendeu: {_fmt_kz(valor_treino)}")

                                st.session_state[f"treino_aberto_{fid}"] = False

                                import time as _t3

                                _t3.sleep(1)

                                st.rerun()

                            else:

                                st.error("Erro ao ensinar")



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

    with c3: st.metric("Ticket Médio", _fmt_kz(ticket_medio))

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

        st.info("Sem perdas registadas neste período.")



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

        turnos = listar_turnos_período(mes_num, ano_escolhido, farm_id)

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



    dc1, dc2, dc3, dc4 = st.columns(4)

    with dc1:

        st.metric("Total depositado", _fmt_kz(resumo_d['total_valor']))

    with dc2:

        st.metric("Num. depositos", f"{resumo_d['num_total']}")

    with dc3:

        pend = resumo_d.get('num_pendentes', 0)

        if pend > 0:

            st.metric("Aguarda confirmacao", f"{pend}", delta="⚠️")

        else:

            st.metric("Aguarda confirmacao", "0", delta="OK")

    with dc4:

        regist = resumo_d.get('num_registados', 0)

        if regist > 0:

            st.metric("So registados", f"{regist}", delta="⚠️")

        else:

            st.metric("So registados", "0", delta="OK")



    if depositos:

        st.markdown("---")



        # Filtro por estado

        filtro_estado = st.selectbox(

            "Filtrar por estado",

            ["TODOS", "REGISTADO", "AGUARDA_CONFIRMACAO", "CONFIRMADO", "REJEITADO"],

            key="fin_filtro_dep",

        )



        if filtro_estado == "TODOS":

            depositos_filtrados = depositos

        else:

            depositos_filtrados = [d for d in depositos if d.get("estado") == filtro_estado]



        st.caption(f"A mostrar **{len(depositos_filtrados)}** de **{len(depositos)}** depositos")



        for d in depositos_filtrados:

            estado = d.get("estado") or "-"

            dep_id = d.get("id")

            referencia = d.get("referencia") or "-"

            valor = d.get("valor") or 0

            banco = d.get("banco") or "-"

            data_dep = d.get("data") or "-"

            gerente = d.get("gerente_nome") or "-"

            comprovante = d.get("numero_comprovante") or "-"

            observacoes = d.get("observacoes") or ""



            # Cores por estado

            if estado == "CONFIRMADO":

                st.success(

                    f"✅ **{referencia}** — {_fmt_kz(valor)} — "

                    f"{data_dep} — {banco} — Gerente: {gerente}"

                )

            elif estado == "AGUARDA_CONFIRMACAO":

                st.warning(

                    f"🟡 **{referencia}** — {_fmt_kz(valor)} — "

                    f"{data_dep} — {banco} — Gerente: {gerente} — "

                    f"Comprovante: {comprovante}"

                )

            elif estado == "REJEITADO":

                st.error(

                    f"❌ **{referencia}** — {_fmt_kz(valor)} — "

                    f"{data_dep} — {banco} — {observacoes}"

                )

            else:  # REGISTADO

                st.info(

                    f"🔵 **{referencia}** — {_fmt_kz(valor)} — "

                    f"{data_dep} — {banco} — Gerente: {gerente} — "

                    f"Comprovante: {comprovante}"

                )



            # Mostrar botões só para AGUARDA_CONFIRMACAO

            if estado == "AGUARDA_CONFIRMACAO":

                col_b1, col_b2, col_b3 = st.columns([1, 1, 3])



                with col_b1:

                    if st.button("✅ Confirmar", key=f"conf_dep_{dep_id}", type="primary"):

                        from services.supabase_client import confirmar_deposito

                        aprovador = "CEO"

                        if confirmar_deposito(dep_id, aprovador):

                            st.success(f"Deposito {referencia} confirmado!")

                            st.cache_data.clear()

                            import time

                            time.sleep(1)

                            st.rerun()

                        else:

                            st.error("Erro ao confirmar.")



                with col_b2:

                    if st.button("❌ Rejeitar", key=f"rej_dep_{dep_id}"):

                        st.session_state[f"rejeitar_dep_{dep_id}"] = True



                # Formulário de rejeição

                if st.session_state.get(f"rejeitar_dep_{dep_id}", False):

                    with st.expander("❌ Motivo da rejeição", expanded=True):

                        motivo = st.text_area(

                            "Motivo",

                            key=f"motivo_{dep_id}",

                            placeholder="Ex: Nao encontrei este deposito no extrato",

                        )

                        col_r1, col_r2 = st.columns(2)

                        with col_r1:

                            if st.button("💾 Confirmar rejeicao", key=f"save_rej_{dep_id}"):

                                if not motivo or len(motivo.strip()) < 3:

                                    st.warning("Escreve um motivo (min 3 caracteres).")

                                else:

                                    from services.supabase_client import rejeitar_deposito

                                    if rejeitar_deposito(dep_id, motivo.strip(), "CEO"):

                                        st.error(f"Deposito {referencia} rejeitado.")

                                        st.session_state[f"rejeitar_dep_{dep_id}"] = False

                                        st.cache_data.clear()

                                        import time

                                        time.sleep(1)

                                        st.rerun()

                                    else:

                                        st.error("Erro ao rejeitar.")

                        with col_r2:

                            if st.button("❌ Cancelar", key=f"cancel_rej_{dep_id}"):

                                st.session_state[f"rejeitar_dep_{dep_id}"] = False

                                st.rerun()



            st.markdown("")

    else:

        st.info("Sem depositos registados neste período.")



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

        st.info("Sem turnos registados neste período.")



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

    st.caption("Saude do sistema e detecao automática de problemas")

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



    if problemas:

        st.subheader("🔴 Problemas Críticos")

        for p in problemas:

            with st.container():

                st.error(

                    f"**{p['area']}**\n\n"

                    f"{p['problema']}\n\n"

                    f"💡 **Solucao:** {p['solucao']}"

                )

                st.markdown("")



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



    if info:

        st.subheader("🔵 Informações")

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

        st.success("✅ **Sistema saudável!** Nenhum problema detectado.")

        st.balloons()



    st.markdown("---")

    st.caption(f"Ultima analise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")





def mostrar_definicoes():

    st.title("Definicoes")

    st.caption("Informação da plataforma e preferencias")

    st.markdown("---")



    info = info_plataforma()



    st.subheader("ℹ️ Informação da Plataforma")



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

        "**JAM Soft - Plataforma de Monitorização**\n\n"

        "Para suporte tecnico, contactar:\n"

        "- Email: suporte@jamsoft.ao\n"

        "- Tel: +244 XXX XXX XXX"

    )



    st.markdown("---")

    st.caption("JAM Soft 2026 - Todos os direitos reservados")





# ============================================================

# ============ CHAT IA =======================================

# ============================================================



def mostrar_chat_ia():

    """Chat IA — perguntar sobre vendas e dados em linguagem natural."""

    import requests as _req



    st.title("💬 Chat IA")

    st.caption("Pergunta sobre as tuas farmácias em linguagem natural")

    st.markdown("---")



    # Configuração Groq

    try:

        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

    except Exception:

        GROQ_API_KEY = ""



    if not GROQ_API_KEY:

        st.error(

            "⚠️ A chave da IA não está configurada.\n\n"

            "Vai a **Settings → Secrets** no Streamlit Cloud e adiciona:\n\n"

            "```\nGROQ_API_KEY = \"gsk_...\"\n```"

        )

        return



    st.markdown("### Perguntas sugeridas:")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        if st.button("📊 Vendas de hoje", use_container_width=True):

            st.session_state["chat_pergunta"] = "Quanto vendi hoje em todas as farmácias?"

    with c2:

        if st.button("🏆 Melhor farmácia", use_container_width=True):

            st.session_state["chat_pergunta"] = "Qual foi a farmácia que mais vendeu este mês?"

    with c3:

        if st.button("📦 Stock baixo", use_container_width=True):

            st.session_state["chat_pergunta"] = "Que produtos estão com stock baixo?"

    with c4:

        if st.button("📅 Resumo do mês", use_container_width=True):

            st.session_state["chat_pergunta"] = "Como está o mês actual? Estou a bater a meta?"



    st.markdown("---")



    # Histórico

    if "chat_histórico" not in st.session_state:

        st.session_state["chat_histórico"] = []



    # Mostrar histórico

    for msg in st.session_state["chat_histórico"]:

        if msg["role"] == "user":

            with st.chat_message("user"):

                st.markdown(msg["content"])

        else:

            with st.chat_message("assistant"):

                st.markdown(msg["content"])



    # Input

    pergunta = st.chat_input("Escreve a tua pergunta...")



    # Se veio de botão sugerido

    if "chat_pergunta" in st.session_state and st.session_state["chat_pergunta"]:

        pergunta = st.session_state.pop("chat_pergunta")



    if pergunta:

        # Mostrar pergunta

        with st.chat_message("user"):

            st.markdown(pergunta)



        st.session_state["chat_histórico"].append({

            "role": "user",

            "content": pergunta,

        })



        # Gerar resposta

        with st.chat_message("assistant"):

            with st.spinner("A pensar..."):

                resposta = _chat_ia_responder(pergunta, GROQ_API_KEY, st)

            st.markdown(resposta)



        st.session_state["chat_histórico"].append({

            "role": "assistant",

            "content": resposta,

        })



    # Botão limpar

    if st.session_state["chat_histórico"]:

        if st.button("🗑️ Limpar conversa"):

            st.session_state["chat_histórico"] = []

            st.rerun()





def _obter_contexto_ia():

    """Recolhe dados para dar à IA como contexto."""

    from datetime import datetime as _dt, timedelta



    ctx = {}



    try:

        ctx["farmacias"] = listar_farmacias()

    except Exception:

        ctx["farmacias"] = []



    try:

        # Vendas do mês actual por farmácia

        hoje = _dt.now()

        resumo_mes = resumo_por_farmacia_mes(hoje.month, hoje.year)

        ctx["resumo_mes"] = resumo_mes

    except Exception:

        ctx["resumo_mes"] = {}



    try:

        # Vendas dos últimos 7 dias

        v7 = vendas_ultimos_dias(dias=7)

        ctx["vendas_7d"] = {

            "total": sum(v.get("total", 0) or 0 for v in v7),

            "numero": len(v7),

        }

    except Exception:

        ctx["vendas_7d"] = {"total": 0, "numero": 0}



    try:

        # Vendas de hoje

        v1 = vendas_ultimos_dias(dias=1)

        ctx["vendas_hoje"] = {

            "total": sum(v.get("total", 0) or 0 for v in v1),

            "numero": len(v1),

        }

    except Exception:

        ctx["vendas_hoje"] = {"total": 0, "numero": 0}



    try:

        # Stock baixo

        ctx["stock_baixo"] = produtos_estoque_baixo()

    except Exception:

        ctx["stock_baixo"] = []



    try:

        # Orçamentos do mês

        hoje = _dt.now()

        ctx["metas"] = metas_activas(hoje.month, hoje.year)

    except Exception:

        ctx["metas"] = []



    try:

        # Top produtos do mês

        hoje = _dt.now()

        ctx["top_produtos"] = top_produtos_mes(hoje.month, hoje.year, 5)

    except Exception:

        ctx["top_produtos"] = []



    return ctx





def _construir_system_prompt(ctx):

    """Constroi o prompt de sistema com os dados da farmácia."""

    from datetime import datetime as _dt



    # Farmacias

    farm_txt = ""

    for f in ctx.get("farmacias", []):

        farm_txt += f"- {f.get('nome', '?')} (NIF: {f.get('nif', '-')})\n"



    # Resumo do mês

    resumo_txt = ""

    total_mes = 0

    for fid, dados in ctx.get("resumo_mes", {}).items():

        nome = dados.get("farmacia", {}).get("nome", "?")

        total = dados.get("total", 0)

        num = dados.get("num_vendas", 0)

        total_mes += total

        resumo_txt += f"- {nome}: Kz {total:,.0f} ({num} vendas)\n"



    # Stock baixo

    stock_txt = ""

    for p in ctx.get("stock_baixo", [])[:10]:

        stock_txt += f"- {p.get('nome', '?')}: {p.get('estoque_atual', 0)} unidades\n"



    # Metas

    metas_txt = ""

    for m in ctx.get("metas", []):

        metas_txt += f"- {m.get('mes', '?')}: Kz {m.get('orcamento_mes', 0):,.0f}\n"



    # Top produtos

    top_txt = ""

    for p in ctx.get("top_produtos", [])[:5]:

        top_txt += f"- {p.get('nome', '?')}: {p.get('quantidade', 0)} unidades\n"



    hoje = _dt.now().strftime("%d/%m/%Y %H:%M")



    return f"""És o assistente IA do JAM Soft, sistema de gestão de farmácias em Angola.



Data e hora actual: {hoje}



=== DADOS DA REDE ===



FARMÁCIAS ({len(ctx.get('farmacias', []))}):

{farm_txt or '  (nenhuma)'}



VENDAS HOJE:

  Total: Kz {ctx.get('vendas_hoje', {}).get('total', 0):,.0f}

  Número: {ctx.get('vendas_hoje', {}).get('numero', 0)}



VENDAS ÚLTIMOS 7 DIAS:

  Total: Kz {ctx.get('vendas_7d', {}).get('total', 0):,.0f}

  Número: {ctx.get('vendas_7d', {}).get('numero', 0)}



VENDAS DO MÊS (por farmácia):

{resumo_txt or '  (sem dados)'}



TOTAL DO MÊS: Kz {total_mes:,.0f}



METAS/ORÇAMENTOS:

{metas_txt or '  (sem metas definidas)'}



STOCK BAIXO:

{stock_txt or '  (tudo OK)'}



TOP PRODUTOS DO MÊS:

{top_txt or '  (sem dados)'}



=== INSTRUÇÕES ===



- Responde sempre em PORTUGUÊS (Angola)

- Sê conciso e directo

- Usa os dados acima

- Se não souberes algo, diz "não tenho essa informação"

- Nunca inventes números

- Formata valores em Kwanza (Kz)

- Quando fizer sentido, dá sugestões úteis"""





def _chat_ia_responder(pergunta, api_key, st_module):

    """Envia pergunta ao Groq e devolve resposta."""

    import requests as _req



    ctx = _obter_contexto_ia()

    system_prompt = _construir_system_prompt(ctx)



    # Histórico recente (últimas 8 mensagens)

    histórico = st_module.session_state.get("chat_histórico", [])

    mensagens = [{"role": "system", "content": system_prompt}]

    for msg in histórico[-8:]:

        mensagens.append({

            "role": msg["role"],

            "content": msg["content"],

        })

    mensagens.append({"role": "user", "content": pergunta})



    try:

        r = _req.post(

            "https://api.groq.com/openai/v1/chat/completions",

            headers={

                "Authorization": f"Bearer {api_key}",

                "Content-Type": "application/json",

            },

            json={

                "model": "openai/gpt-oss-120b",

                "messages": mensagens,

                "temperature": 0.5,

                "max_tokens": 800,

            },

            timeout=30,

        )



        if r.status_code != 200:

            return f"❌ Erro da IA ({r.status_code}). Tenta novamente."



        dados = r.json()

        return dados["choices"][0]["message"]["content"]



    except Exception as e:

        return f"❌ Erro ao contactar a IA: {e}"