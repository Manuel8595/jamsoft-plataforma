import streamlit as st
from datetime import datetime
from services.supabase_client import (
    listar_farmacias, resumo_por_farmacia, vendas_por_dia
)

st.set_page_config(
    page_title="JAM Soft - Monitorizacao",
    page_icon="💊",
    layout="wide",
)

st.title("💊 JAM Soft — Plataforma de Monitorizacao")
st.caption(f"Dados em tempo real • {datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.markdown("---")

with st.spinner("A carregar dados..."):
    farmacias = listar_farmacias()
    resumo = resumo_por_farmacia(dias=1)

total_vendas_hoje = sum(r["total"] for r in resumo.values())
num_vendas_hoje = sum(r["num_vendas"] for r in resumo.values())

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🏥 Farmacias Activas", f"{len(farmacias)}")
with col2:
    st.metric("💰 Vendas Hoje", f"Kz {total_vendas_hoje:,.0f}".replace(",", "."))
with col3:
    st.metric("🛒 Numero de Vendas", f"{num_vendas_hoje}")

st.markdown("---")
st.subheader("📊 Vendas por Farmacia (Hoje)")

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
                st.caption(f"📍 {f.get('endereco', '-')} • NIF: {f.get('nif', '-')}")
            
            with col_b:
                st.metric("Total", f"Kz {total:,.0f}".replace(",", "."))
            
            with col_c:
                st.metric("Vendas", f"{num_v}")
            
            with col_d:
                st.metric("Ticket Medio", f"Kz {ticket:,.0f}".replace(",", "."))
            
            if dados["formas"]:
                st.caption("**Formas de pagamento:**")
                cols_formas = st.columns(len(dados["formas"]))
                for i, (forma, qtd) in enumerate(dados["formas"].items()):
                    with cols_formas[i]:
                        st.caption(f"• {forma}: **{qtd}**")

st.markdown("---")
st.subheader("📈 Evolucao (Ultimos 7 dias)")

vendas_7d = vendas_por_dia(dias=7)

if vendas_7d:
    st.bar_chart({k: v["total"] for k, v in vendas_7d.items()}, height=300)
else:
    st.info("Sem dados suficientes para o grafico.")