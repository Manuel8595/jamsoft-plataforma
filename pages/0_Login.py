"""
Ecra de login da plataforma.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.auth import autenticar
from auth_helper import iniciar_sessao


def main():
    st.set_page_config(
        page_title="Login - JAM Soft",
        page_icon="🔐",
        layout="centered",
    )

    if st.session_state.get("logado", False):
        st.success("Ja estas logado!")
        if st.button("Ir para o Dashboard"):
            st.switch_page("app.py")
        return

    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1>💊 JAM Soft</h1>
            <p style='color: #94a3b8;'>Plataforma de Monitorizacao</p>
            <hr style='border-color: #334155;'>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("🔐 Entrar")

        with st.form("form_login"):
            email = st.text_input(
                "📧 Email",
                placeholder="o-teu-email@exemplo.com",
            )
            senha = st.text_input(
                "🔑 Senha",
                type="password",
                placeholder="A tua senha",
            )

            submitted = st.form_submit_button(
                "Entrar",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not email or not senha:
                st.error("Preenche o email e a senha.")
            else:
                ok = False
                dados = None

                try:
                    ok, dados = autenticar(email.strip().lower(), senha)
                except Exception as e:
                    st.error("ERRO: " + str(e))
                    import traceback
                    st.code(traceback.format_exc())

    
                if ok:
                    iniciar_sessao(dados)
                    st.success("Bem-vindo, " + dados["nome"] + "!")
                    st.rerun()
                else:
                    if dados and dados.get("erro") == "inativo":
                        st.error("Conta inactiva. Contacta o administrador.")
                    else:
                        st.error("Email ou senha incorrectos.")

        st.markdown("---")
        st.caption("🔒 Acesso restrito. Cada CEO tem a sua conta própria.")


main()