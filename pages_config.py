"""
Pagina de Configuração - escolher o que mostrar a cada farmacia.
"""
import streamlit as st
from datetime import datetime
from services.supabase_client import (
    listar_farmacias,
    obter_config_farmacia,
    guardar_config_farmacia,
)
def mostrar_configuração():
    st.title("⚙️ Configuração")
    st.caption("Escolhe o que mostrar a cada farmacia no painel de Orcamentos")
    st.markdown("---")
    with st.spinner("A carregar farmacias..."):
        farmacias = listar_farmacias()
    if not farmacias:
        st.warning("Nenhuma farmacia encontrada.")
        return
    st.info(
        "💡 **Como funciona:** escolhe para cada farmacia quais os períodos "
        "que queres ver no painel de Orcamentos (Dia, Semana, Mes, Ano)."
    )
    st.markdown("---")
    st.subheader(f"Farmacias ({len(farmacias)})")
    for f in farmacias:
        fid = f["id"]
        cfg = obter_config_farmacia(fid)
        with st.container(border=True):
            st.markdown(f"### {f['nome']}")
            st.caption(f"{f.get('endereco', '-')} | NIF: {f.get('nif', '-')}")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                mostrar_dia = st.checkbox(
                    "📅 Dia",
                    value=cfg.get("mostrar_dia", True),
                    key=f"cfg_dia_{fid}",
                )
            with col2:
                mostrar_semana = st.checkbox(
                    "📆 Semana",
                    value=cfg.get("mostrar_semana", True),
                    key=f"cfg_sem_{fid}",
                )
            with col3:
                mostrar_mes = st.checkbox(
                    "🗓️ Mes",
                    value=cfg.get("mostrar_mes", True),
                    key=f"cfg_mes_{fid}",
                )
            with col4:
                mostrar_ano = st.checkbox(
                    "📊 Ano",
                    value=cfg.get("mostrar_ano", True),
                    key=f"cfg_ano_{fid}",
                )
            # Botão guardar
            if st.button(f"💾 Guardar", key=f"cfg_save_{fid}"):
                ok = guardar_config_farmacia(
                    fid,
                    mostrar_dia,
                    mostrar_semana,
                    mostrar_mes,
                    mostrar_ano,
                )
                if ok:
                    st.success(f"Configuração guardada: {f['nome']}")
                    st.cache_data.clear()
                else:
                    st.error("Erro ao guardar")
    st.markdown("---")
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
