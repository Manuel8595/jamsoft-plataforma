"""


Dashboard — Resumo do País (vista inicial).


"""





import streamlit as st


from datetime import datetime


from services.supabase_client import (


    listar_farmacias,


    resumo_por_farmacia,


    resumo_por_farmacia_mes,


    vendas_por_dia,


    metas_activas,


)








# ============================================================


# HELPERS


# ============================================================





def _fmt_kz(valor):


    try:


        return f"Kz {float(valor):,.0f}".replace(",", ".")


    except Exception:


        return "Kz 0"








    # ============================================================


    # IA — ALERTAS AUTOMATICOS


    # ============================================================


    st.markdown("---")


    st.subheader("🤖 Alertas Automáticos (IA)")





    try:


        from services.supabase_client import analisar_alertas_geral


        alertas = analisar_alertas_geral()





        if not alertas:


            st.success("✅ Nenhum alerta. Sistema saudável.")


        else:


            criticos = [a for a in alertas if a.get("nivel") == "CRITICO"]


            avisos = [a for a in alertas if a.get("nivel") == "AVISO"]





            col1, col2 = st.columns(2)


            with col1:


                if criticos:


                    st.error(f"🔴 **{len(criticos)}** critico(s)")


                else:


                    st.success("✅ Sem criticos")


            with col2:


                if avisos:


                    st.warning(f"🟡 **{len(avisos)}** aviso(s)")


                else:


                    st.success("✅ Sem avisos")





            st.markdown("")





            if criticos:


                st.markdown("#### 🔴 Críticos")


                for a in criticos[:10]:


                    with st.container(border=True):


                        st.markdown(f"**{a['titulo']}**")


                        st.caption(a.get("detalhe", ""))


                        st.caption(f"💡 **Acção:** {a.get('accao', '')}")





            if avisos:


                st.markdown("#### 🟡 Avisos")


                for a in avisos[:10]:


                    with st.container(border=True):


                        st.markdown(f"**{a['titulo']}**")


                        st.caption(a.get("detalhe", ""))


                        st.caption(f"💡 **Acção:** {a.get('accao', '')}")


    except Exception as e:


        st.warning(f"Erro ao analisar alertas: {e}")








# ============================================================


# DASHBOARD


# ============================================================





def mostrar_dashboard():


    # ─── Cabeçalho com logo ───


    col_logo, col_info = st.columns([1, 2])


    with col_logo:


        try:


            from pathlib import Path


            caminho_logo = Path(__file__).parent / "logos" / "JamLogo_transparente.png"


            if caminho_logo.exists():


                st.image(str(caminho_logo), width=200)


            else:


                st.title("💊 JAM Soft")


        except Exception:


            st.title("💊 JAM Soft")





    with col_info:


        st.markdown(f"### Resumo do País")


        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")





    st.markdown("---")





    col_a, col_b = st.columns([6, 1])


    with col_b:


        if st.button("🔄 Atualizar", use_container_width=True):


            st.cache_data.clear()


            st.rerun()





    with st.spinner("A carregar..."):


        farmacias = listar_farmacias()


        resumo_hoje = resumo_por_farmacia(dias=1)


        resumo_mes = resumo_por_farmacia(dias=31)


        vendas_30d = vendas_por_dia(dias=30)





    num_farmacias = len(farmacias)





    total_hoje = sum(r["total"] for r in resumo_hoje.values())


    num_vendas_hoje = sum(r["num_vendas"] for r in resumo_hoje.values())


    ticket_hoje = (total_hoje / num_vendas_hoje) if num_vendas_hoje > 0 else 0





    total_mes = sum(r["total"] for r in resumo_mes.values())





    st.subheader("📊 Hoje")


    col1, col2, col3, col4 = st.columns(4)


    with col1:


        st.metric("🏥 Lojas", f"{num_farmacias}")


    with col2:


        st.metric("💰 Vendas", _fmt_kz(total_hoje))


    with col3:


        st.metric("🛒 Nº Vendas", f"{num_vendas_hoje}")


    with col4:


        st.metric("📊 Ticket Médio", _fmt_kz(ticket_hoje))





    st.markdown("---")





    # ─── Orçamento do País ───


    st.subheader("🎯 Orcamento do Pais (este mes)")





    # Buscar metas do mês actual


    hoje = datetime.now()


    metas_mes = metas_activas(hoje.month, hoje.year) or []





    if metas_mes:


        orcamento_total = sum(m.get("orcamento_mes", 0) or 0 for m in metas_mes)


        perc = (total_mes / orcamento_total * 100) if orcamento_total > 0 else 0





        col_a, col_b, col_c = st.columns(3)


        with col_a:


            st.metric("Meta do Pais", _fmt_kz(orcamento_total))


        with col_b:


            st.metric("Vendido", _fmt_kz(total_mes))


        with col_c:


            st.metric("Atingido", f"{perc:.1f}%")





        # Barra de progresso


        st.progress(min(perc / 100, 1.0))





        if perc >= 100:


            st.success(f"🎉 Meta batida! Superou em {_fmt_kz(total_mes - orcamento_total)}")


        elif perc >= 70:


            st.info(f"🟢 Bom progresso! Falta {_fmt_kz(orcamento_total - total_mes)}")


        elif perc >= 30:


            st.warning(f"🟡 Falta {_fmt_kz(orcamento_total - total_mes)} para a meta")


        else:


            st.error(f"🔴 Falta {_fmt_kz(orcamento_total - total_mes)} para a meta")


    else:


        st.info(


            f"Vendido este mes: **{_fmt_kz(total_mes)}**\n\n"


            f"_(as metas ainda nao estao configuradas — vai a **Orcamentos** para definir)_"


        )





    st.markdown("---")





    st.subheader("🔔 Alertas Rapidos")





    sem_vendas = []


    for f in farmacias:


        fid = f["id"]


        r = resumo_hoje.get(fid, {})


        if r.get("num_vendas", 0) == 0:


            sem_vendas.append(f["nome"])





    if not sem_vendas:


        st.success("✅ Todas as farmacias a comunicar hoje.")


    else:


        st.warning(


            f"⚠️ **{len(sem_vendas)}** farmacia(s) sem vendas hoje: "


            + ", ".join(sem_vendas)


        )





    st.markdown("---")





    st.subheader("📈 Evolucao (ultimos 30 dias)")





    if vendas_30d:


        dados = {k: v["total"] for k, v in vendas_30d.items()}


        st.bar_chart(dados, height=280, use_container_width=True)


    else:


        st.info("Sem dados suficientes.")





    st.markdown("---")


    st.caption(


        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} • "


        f"Fonte: Supabase • Actualiza a cada 5 min"


    )