import streamlit as st
from config_cloud import CLOUD_ACCESS_ENABLED
from services.auth import autenticar
from services.supabase_client import definir_jwt, limpar_jwt
from pages_registo import mostrar_registo
from dashboard import mostrar_dashboard
from pages_secundarias import (
    mostrar_ranking,
    mostrar_alertas,
    mostrar_orcamentos,
    mostrar_vendas,
    mostrar_stock,
    mostrar_perdas,
    mostrar_financeiro,
    mostrar_utilizadores,
    mostrar_diagnostico,
    mostrar_definicoes,
)


st.set_page_config(
    page_title="JAM Soft - Monitorizacao",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not CLOUD_ACCESS_ENABLED:
    st.info(
        "A plataforma online está temporariamente desligada. "
        "A aplicação local da farmácia continua disponível."
    )
    st.stop()


if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "utilizador" not in st.session_state:
    st.session_state["utilizador"] = None
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "📊 Resumo do Pais"


def mostrar_login():
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
            email = st.text_input("📧 Email", placeholder="o-teu-email@exemplo.com")
            senha = st.text_input("🔑 Senha", type="password", placeholder="A tua senha")
            submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            if not email or not senha:
                st.error("Preenche o email e a senha.")
            else:
                try:
                    ok, dados = autenticar(email.strip().lower(), senha)
                except Exception as e:
                    st.error(f"Erro: {e}")
                    ok, dados = False, None

                if ok:
                    st.session_state["logado"] = True
                    st.session_state["utilizador"] = dados
                    definir_jwt(dados.get("jwt", ""))
                    st.rerun()
                else:
                    if dados and dados.get("erro") == "inativo":
                        st.error("Conta inactiva. Contacta o administrador.")
                    else:
                        st.error("Email ou senha incorrectos.")

        st.markdown("---")
        st.caption("🔒 Acesso restrito.")


query_params = st.query_params
token_convite = query_params.get("convite", None)

if token_convite:
    mostrar_registo(token_convite)
    st.stop()


if st.session_state["logado"]:
    user = st.session_state["utilizador"]

    with st.sidebar:
        st.markdown(f"### 👤 {user['nome']}")
        st.caption(f"📧 {user['email']}")
        st.markdown("---")

        menu = [
            "📊 Resumo do Pais",
            "🏆 Ranking de Farmacias",
            "🔔 Alertas",
            "💰 Orcamentos",
            "📈 Vendas",
            "📦 Stock",
            "💸 Perdas",
            "🏦 Financeiro",
            "👥 Utilizadores",
            "🩺 Diagnostico",
            "⚙️ Definicoes",
            "🔐 Administracao",
        ]

        pagina = st.radio(
            "Navegacao",
            menu,
            index=menu.index(st.session_state["pagina"]),
            label_visibility="collapsed",
        )
        st.session_state["pagina"] = pagina

        st.markdown("---")
        if st.button("🚪 Terminar Sessao", use_container_width=True):
            limpar_jwt()
            st.session_state["logado"] = False
            st.session_state["utilizador"] = None
            st.session_state["pagina"] = "📊 Resumo do Pais"
            st.rerun()

    if pagina == "📊 Resumo do Pais":
        mostrar_dashboard()
    elif pagina == "🏆 Ranking de Farmacias":
        mostrar_ranking()
    elif pagina == "🔔 Alertas":
        mostrar_alertas()
    elif pagina == "💰 Orcamentos":
        mostrar_orcamentos()
    elif pagina == "📈 Vendas":
        mostrar_vendas()
    elif pagina == "📦 Stock":
        mostrar_stock()
    elif pagina == "💸 Perdas":
        mostrar_perdas()
    elif pagina == "🏦 Financeiro":
        mostrar_financeiro()
    elif pagina == "👥 Utilizadores":
        mostrar_utilizadores()
    elif pagina == "🩺 Diagnostico":
        mostrar_diagnostico()
    elif pagina == "⚙️ Definicoes":
        mostrar_definicoes()
    elif pagina == "🔐 Administracao":
        mostrar_admin(user)

else:
    mostrar_login()