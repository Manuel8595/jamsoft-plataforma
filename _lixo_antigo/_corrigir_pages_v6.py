# Substitui mostrar_diagnostico() e mostrar_definicoes()

import re

path = "pages_secundarias.py"

with open(path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# --- Nova funcao mostrar_diagnostico ---
nova_diagnostico = '''def mostrar_diagnostico():
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
                    f"**{p['area']}**\\n\\n"
                    f"{p['problema']}\\n\\n"
                    f"💡 **Solucao:** {p['solucao']}"
                )
        st.markdown("")

    # Avisos
    if avisos:
        st.subheader("🟡 Avisos")
        for a in avisos:
            with st.container():
                st.warning(
                    f"**{a['area']}**\\n\\n"
                    f"{a['problema']}\\n\\n"
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
    st.caption(f"Ultima analise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")'''

# --- Nova funcao mostrar_definicoes ---
nova_definicoes = '''def mostrar_definicoes():
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
        "**JAM Soft - Plataforma de Monitorizacao**\\n\\n"
        "Para suporte tecnico, contactar:\\n"
        "- Email: suporte@jamsoft.ao\\n"
        "- Tel: +244 XXX XXX XXX"
    )

    st.markdown("---")
    st.caption("JAM Soft 2026 - Todos os direitos reservados")'''

# Substituir mostrar_diagnostico
padrao_diag = re.compile(r"def mostrar_diagnostico\(\):.*?(?=\ndef |\Z)", re.DOTALL)
if "def mostrar_diagnostico" in conteudo:
    if "diagnostico_sistema" in conteudo:
        print("diagnostico: JA SUBSTITUIDO")
    else:
        conteudo = padrao_diag.sub(nova_diagnostico + "\n\n", conteudo, count=1)
        print("diagnostico: OK substituido")

# Substituir mostrar_definicoes
padrao_def = re.compile(r"def mostrar_definicoes\(\):.*?(?=\ndef |\Z)", re.DOTALL)
if "def mostrar_definicoes" in conteudo:
    if "info_plataforma" in conteudo:
        print("definicoes: JA SUBSTITUIDO")
    else:
        conteudo = padrao_def.sub(nova_definicoes + "\n", conteudo, count=1)
        print("definicoes: OK substituido")

with open(path, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("Ficheiro guardado.")