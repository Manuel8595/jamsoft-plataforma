import streamlit as st
from datetime import datetime, timedelta
from services.supabase_client import (
    listar_farmacias, resumo_por_farmacia, vendas_por_dia, vendas_ultimos_dias
)

st.set_page_config(
    page_title="JAM Soft - Monitorizacao",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CACHE (evita pedir ao Supabase em cada refresh)
# ============================================================

@st.cache_data(ttl=300)  # 5 min
def carregar_farmacias():
    return listar_farmacias()


@st.cache_data(ttl=300)
def carregar_resumo(dias):
    return resumo_por_farmacia(dias=dias)


@st.cache_data(ttl=300)
def carregar_vendas_dia(dias):
    return vendas_por_dia(dias=dias)


# ============================================================
# INTERFACE
# ============================================================

st.title("💊 JAM Soft — Monitorizacao")
st.caption(f"Dados em tempo real • {datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.markdown("---")

# ===== FILTRO DE PERIODO =====
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
    st.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")

st.markdown("---")

# ===== CARREGAR DADOS =====
with st.spinner("A carregar..."):
    farmacias = carregar_farmacias()
    resumo = carregar_resumo(dias)

# ===== METRICAS GLOBAIS =====
total_vendas = sum(r["total"] for r in resumo.values())
num_vendas = sum(r["num_vendas"] for r in resumo.values())
ticket_medio_global = (total_vendas / num_vendas) if num_vendas > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏥 Farmacias Activas", f"{len(farmacias)}")
with col2:
    st.metric("💰 Vendas", f"Kz {total_vendas:,.0f}".replace(",", "."))
with col3:
    st.metric("🛒 Numero de Vendas", f"{num_vendas}")
with col4:
    st.metric("📊 Ticket Medio", f"Kz {ticket_medio_global:,.0f}".replace(",", "."))

st.markdown("---")

# ===== POR FARMACIA =====
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
                st.caption("**Formas de pagamento:** " + " • ".join(
                    [f"{forma}: **{qtd}**" for forma, qtd in dados["formas"].items()]
                ))
            
            if dados["vendedores"]:
                st.caption("**Vendedores:** " + " • ".join(
                    [f"{v}: **{q}**" for v, q in dados["vendedores"].items()]
                ))

st.markdown("---")

# ===== EVOLUCAO =====
st.subheader(f"📈 Evolucao ({periodo})")

vendas_periodo = carregar_vendas_dia(dias)

if vendas_periodo:
    st.bar_chart(
        {k: v["total"] for k, v in vendas_periodo.items()},
        height=300,
        use_container_width=True,
    )
else:
    st.info("Sem dados suficientes para o grafico.")