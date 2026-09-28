import streamlit as st
from datetime import datetime
from services.supabase_client import (
    listar_farmacias, resumo_por_farmacia, vendas_por_dia
)
from services.auth import autenticar


# ============================================================
# CONFIGURACAO (primeira instrucao Streamlit)
# ============================================================

st.set_page_config(
    page_title="JAM Soft - Monitorizacao",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ESTADO DA SESSAO
# ============================================================

if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "utilizador" not in st.session_state:
    st.session_state["utilizador"] = None


# ============================================================
# FUNCAO DE LOGIN
# ============================================================

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
                try:
                    ok, dados = autenticar(email.strip().lower(), senha)
                except Exception as e:
                    st.error(f"Erro: {e}")
                    ok, dados = False, None
                
                if ok:
                    st.session_state["logado"] = True
                    st.session_state["utilizador"] = dados
                    st.rerun()
                else:
                    if dados and dados.get("erro") == "inativo":
                        st.error("Conta inactiva. Contacta o administrador.")
                    else:
                        st.error("Email ou senha incorrectos.")
        
        st.markdown("---")
        st.caption("🔒 Acesso restrito. Cada CEO tem a sua conta própria.")


# ============================================================
# FUNCAO DO DASHBOARD
# ============================================================

@st.cache_data(ttl=300)
def carregar_farmacias():
    return listar_farmacias()


@st.cache_data(ttl=300)
def carregar_resumo(dias):
    return resumo_por_farmacia(dias=dias)


@st.cache_data(ttl=300)
def carregar_vendas_dia(dias):
    return vendas_por_dia(dias=dias)


def mostrar_dashboard():
    user = st.session_state["utilizador"]
    
    # ===== MENU LATERAL =====
    with st.sidebar:
        st.markdown(f"### 👤 {user['nome']}")
        st.caption(f"📧 {user['email']}")
        st.markdown("---")
        
        if st.button("🚪 Terminar Sessao", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["utilizador"] = None
            st.rerun()
        
        st.markdown("---")
        st.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # ===== CONTEUDO =====
    st.title("💊 JAM Soft — Monitorizacao")
    st.caption(f"Dados em tempo real • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.markdown("---")
    
    # Filtros
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    
    with col_f1:
        periodo = st.selectbox(
            "📅 Periodo",
            ["Hoje", "Ultimos 7 dias", "Este mes", "Ultimos 30 dias"],
            index=0,
        )
    
    if periodo == "Hoje":
        dias = 1
    elif periodo == "Ultimos 7 dias":
        dias = 7
    elif periodo == "Este mes":
        dias = 31
    else:
        dias = 30
    
    with col_f2:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col_f3:
        st.caption(f"Periodo: **{periodo}**")
    
    st.markdown("---")
    
    with st.spinner("A carregar..."):
        farmacias = carregar_farmacias()
        resumo = carregar_resumo(dias)
    
    total_vendas = sum(r["total"] for r in resumo.values())
    num_vendas = sum(r["num_vendas"] for r in resumo.values())
    ticket_medio_global = (total_vendas / num_vendas) if num_vendas > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏥 Farmacias", f"{len(farmacias)}")
    with col2:
        st.metric("💰 Vendas", f"Kz {total_vendas:,.0f}".replace(",", "."))
    with col3:
        st.metric("🛒 Num. Vendas", f"{num_vendas}")
    with col4:
        st.metric("📊 Ticket Medio", f"Kz {ticket_medio_global:,.0f}".replace(",", "."))
    
    st.markdown("---")
    st.subheader(f"📊 Vendas por Farmacia ({periodo})")
    
    if not farmacias:
        st.info("Nenhuma farmacia registada.")
    else:
        for fid, dados in resumo.items():
            f = dados["farmacia"]
            total = dados["total"]
            num_v = dados["num_vendas"]
            ticket = dados["ticket_medio"]
            
            with st.container(border=True):
                col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
                
                with col_a:
                    st.markdown(f"### {f['nome']}")
                    st.caption(f"📍 {f.get('endereco', '-')}")
                
                with col_b:
                    st.metric("Total", f"Kz {total:,.0f}".replace(",", "."))
                with col_c:
                    st.metric("Vendas", f"{num_v}")
                with col_d:
                    st.metric("Ticket Medio", f"Kz {ticket:,.0f}".replace(",", "."))
                
                if dados["formas"]:
                    st.caption("**Formas:** " + " • ".join(
                        [f"{k}: **{v}**" for k, v in dados["formas"].items()]
                    ))
    
    st.markdown("---")
    st.subheader(f"📈 Evolucao ({periodo})")
    
    vendas_periodo = carregar_vendas_dia(dias)
    if vendas_periodo:
        st.bar_chart(
            {k: v["total"] for k, v in vendas_periodo.items()},
            height=300,
            use_container_width=True,
        )
    else:
        st.info("Sem dados suficientes.")


# ============================================================
# ROUTER
# ============================================================

if st.session_state["logado"]:
    mostrar_dashboard()
else:
    mostrar_login()