"""
Painel de admin — criar convites para novos CEOs.
"""

import streamlit as st
from datetime import datetime
from services.auth import criar_convite, listar_convites, listar_utilizadores


def mostrar_admin(user):
    st.title("⚙️ Administracao")
    st.caption(f"Logado como: {user['nome']} ({user['email']})")

    st.markdown("---")

    tab1, tab2 = st.tabs(["📨 Convites", "👥 Utilizadores"])

    with tab1:
        st.subheader("Criar Novo Convite")
        st.caption("Cada CEO recebe um link proprio. So ele pode criar a sua senha.")

        col1, col2 = st.columns(2)

        with col1:
            email_novo = st.text_input(
                "Email do novo CEO",
                placeholder="ceo2@empresa.com",
                key="email_novo",
            )

        with col2:
            nome_novo = st.text_input(
                "Nome (opcional)",
                placeholder="Joao Silva",
                key="nome_novo",
            )

        if st.button("📨 Gerar Link de Convite", type="primary"):
            if not email_novo:
                st.error("Preenche o email.")
            elif not "@" in email_novo:
                st.error("Email invalido.")
            else:
                users = listar_utilizadores()
                if any(u["email"].lower() == email_novo.lower() for u in users):
                    st.error(f"Ja existe utilizador com email {email_novo}")
                else:
                    token = criar_convite(email_novo, nome_novo)
                    if token:
                        st.success("Convite criado!")
                        st.markdown("**Link a enviar por WhatsApp/Email:**")

                        link = f"https://jamsoft-plataforma-nthcjcruax7wmg9rqxr4qz.streamlit.app/?convite={token}"
                        st.code(link, language=None)

                        st.info("Copia este link e envia ao novo CEO. Ele tem 7 dias para se registar.")
                    else:
                        st.error("Erro ao criar convite.")

        st.markdown("---")
        st.subheader("Convites Existentes")

        try:
            convites = listar_convites()
        except Exception as e:
            st.error(f"Erro ao listar: {e}")
            convites = []

        if not convites:
            st.info("Nenhum convite criado.")
        else:
            for c in convites:
                status = "✅ Usado" if c.get("usado") else "🟡 Pendente"
                with st.container(border=True):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**{c.get('email', '?')}** — {c.get('nome_sugerido', '—') or '—'}")
                        st.caption(f"Criado em: {c.get('criado_em', '?')[:16]} | Expira: {c.get('expira_em', '?')[:16]}")
                    with col_b:
                        st.markdown(status)

    with tab2:
        st.subheader("Utilizadores da Plataforma")

        try:
            users = listar_utilizadores()
        except Exception as e:
            st.error(f"Erro: {e}")
            users = []

        if not users:
            st.info("Nenhum utilizador registado.")
        else:
            for u in users:
                status = "✅ Activo" if u.get("ativo") else "🚫 Inactivo"
                ultimo = u.get("ultimo_login", "—")
                if ultimo and ultimo != "—":
                    ultimo = ultimo[:16]

                with st.container(border=True):
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        st.markdown(f"**{u.get('nome', '?')}** — {u.get('email', '?')}")
                        st.caption(f"Ultimo login: {ultimo}")
                    with col_b:
                        st.markdown(status)
                    with col_c:
                        if st.button("🗑️ Eliminar", key=f"del_user_{u.get('id')}"):
                            st.session_state[f"confirmar_del_{u.get('id')}"] = True

                    # Confirmação de eliminação
                    if st.session_state.get(f"confirmar_del_{u.get('id')}", False):
                        st.warning(
                            f"⚠️ Tem a certeza que quer eliminar "
                            f"**{u.get('nome', '?')}** ({u.get('email', '?')})?\n\n"
                            "Esta ação não pode ser revertida."
                        )
                        col_conf1, col_conf2 = st.columns(2)
                        with col_conf1:
                            if st.button("✅ Sim, eliminar", key=f"confirma_del_{u.get('id')}"):
                                from services.supabase_client import eliminar_ceo
                                ok1, ok2 = eliminar_ceo(u.get("id"), u.get("email"))

                                if ok1:
                                    st.success(f"Eliminado: {u.get('nome', '?')}")
                                    if not ok2:
                                        st.warning(
                                            "⚠️ Aviso: o registo foi eliminado da base de dados, "
                                            "mas **não foi possível eliminar do Supabase Auth**. "
                                            "Para remover completamente, vais ao painel Supabase → "
                                            "Authentication → Users."
                                        )
                                    st.session_state[f"confirmar_del_{u.get('id')}"] = False
                                    st.cache_data.clear()
                                    import time as _t
                                    _t.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("Erro ao eliminar. Tenta novamente.")
                        with col_conf2:
                            if st.button("❌ Cancelar", key=f"cancela_del_{u.get('id')}"):
                                st.session_state[f"confirmar_del_{u.get('id')}"] = False
                                st.rerun()

                                

# ============================================================
# ============ DIAGNOSTICO REMOTO (estado dos PCs) ===========
# ============================================================

def mostrar_diagnostico_remoto(user):
    """Mostra o estado de todos os PCs das farmácias."""
    import streamlit as st
    from datetime import datetime, timedelta
    from services.supabase_client import listar_farmacias, _get

    st.title("🖥️ Diagnostico Remoto")
    st.caption("Estado dos PCs das farmácias em tempo real")
    st.markdown("---")

    if st.button("🔄 Actualizar", key="diag_remoto_refresh"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("A carregar..."):
        farmacias = listar_farmacias()

        # Buscar todos os estados
        estados = _get("estado_pcs", {"select": "*"}) or []

    # Indexar por farmacia_id
    estados_por_farm = {}
    for e in estados:
        fid = e.get("farmacia_id")
        if fid:
            if fid not in estados_por_farm:
                estados_por_farm[fid] = []
            estados_por_farm[fid].append(e)

    agora = datetime.now()

    # Contadores
    online = 0
    offline = 0
    nunca = 0

    for f in farmacias:
        fid = f["id"]
        estados_f = estados_por_farm.get(fid, [])

        with st.container(border=True):
            st.markdown(f"### {f['nome']}")
            st.caption(f"{f.get('endereco', '-')} | NIF: {f.get('nif', '-')}")

            if not estados_f:
                nunca += 1
                st.error("🔴 **Nunca comunicou** — PC ainda não enviou dados")
                continue

            for e in estados_f:
                ultima_sync_str = e.get("ultima_sync", "")
                try:
                    ultima = datetime.fromisoformat(ultima_sync_str.replace("Z", "+00:00"))
                    segundos_atras = (agora - ultima.replace(tzinfo=None)).total_seconds()
                    minutos_atras = int(segundos_atras / 60)
                except Exception:
                    minutos_atras = 9999

                # Estado
                if minutos_atras < 5:
                    estado_emoji = "🟢"
                    estado_txt = "Online"
                    online += 1
                elif minutos_atras < 60:
                    estado_emoji = "🟡"
                    estado_txt = f"Sync há {minutos_atras} min"
                    online += 1
                else:
                    horas = minutos_atras // 60
                    estado_emoji = "🔴"
                    estado_txt = f"Offline há {horas}h"
                    offline += 1

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Estado", f"{estado_emoji} {estado_txt}")
                with col2:
                    st.metric("Terminal", e.get("terminal_id", "?"))
                with col3:
                    st.metric("Versão", e.get("versao", "?"))
                with col4:
                    vendas = e.get("vendas_hoje", 0) or 0
                    st.metric("Vendas hoje", f"Kz {vendas:,.0f}".replace(",", "."))

                col5, col6 = st.columns(2)
                with col5:
                    pendentes = e.get("total_pendentes", 0) or 0
                    if pendentes > 0:
                        st.warning(f"⚠️ {pendentes} operações pendentes de envio")
                    else:
                        st.success("✅ Sem pendentes")
                with col6:
                    erro = e.get("ultimo_erro")
                    if erro:
                        st.error(f"❌ Último erro: {erro[:60]}")
                    else:
                        st.success("✅ Sem erros recentes")

    st.markdown("---")
    st.subheader("Resumo Geral")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🟢 Online", f"{online}")
    with c2:
        st.metric("🔴 Offline", f"{offline}")
    with c3:
        st.metric("⚪ Nunca comunicou", f"{nunca}")

    st.markdown("---")
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")    
    
# ============================================================
# ============ BACKUP DE DADOS ===============================
# ============================================================

def mostrar_backup():
    """Página de Backup — CEO."""
    from backup_service import criar_backup, listar_backups
    from datetime import datetime

    st.title("💾 Backup de Dados")
    st.caption("Cópia encriptada de todos os dados do Supabase")
    st.markdown("---")

    # ─── Botão principal ───
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Criar backup agora")
        st.caption("Puxa todos os dados, encripta com AES-256 e guarda localmente")
    with col2:
        st.write("")
        if st.button("💾 Criar Backup", type="primary", use_container_width=True):
            with st.spinner("A recolher dados do Supabase..."):
                ok, msg = criar_backup()
            if ok:
                st.success(msg)
                st.balloons()
            else:
                st.error(msg)

    st.markdown("---")

    # ─── Lista de backups ───
    st.markdown("### 📁 Backups existentes")
    backups = listar_backups()

    if not backups:
        st.info("Ainda não há backups. Clica em **Criar Backup** acima.")
    else:
        st.caption(f"Total: **{len(backups)}** backups | Máximo: **30**")
        st.markdown("")
        for b in backups:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(f"**{b['nome']}**")
                with c2:
                    st.markdown(f"📅 {b['data']}")
                with c3:
                    st.markdown(f"📦 {b['tamanho_kb']:.1f} KB")

    st.markdown("---")
    st.info(
        "**ℹ️ Sobre o backup**\n\n"
        "- Local: `C:\\Users\\manue\\farmacia-app\\backups\\`\n"
        "- Encriptação: **AES-256** (Fernet)\n"
        "- Retenção: **30 backups** (rotação automática)\n"
        "- Ficheiros `.enc` só abrem com a `BACKUP_KEY` do `secrets.toml`"
    )