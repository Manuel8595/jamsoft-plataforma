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
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**{u.get('nome', '?')}** — {u.get('email', '?')}")
                        st.caption(f"Ultimo login: {ultimo}")
                    with col_b:
                        st.markdown(status)