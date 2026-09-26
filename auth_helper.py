"""
Helpers de sessao para a plataforma.
"""

import streamlit as st


def iniciar_sessao(utilizador):
    """Grava o utilizador na sessao."""
    st.session_state["logado"] = True
    st.session_state["utilizador"] = utilizador


def terminar_sessao():
    """Limpa a sessao."""
    st.session_state["logado"] = False
    st.session_state["utilizador"] = None


def esta_logado():
    """Verifica se ha um utilizador logado."""
    return st.session_state.get("logado", False)


def utilizador_actual():
    """Devolve o utilizador logado."""
    return st.session_state.get("utilizador", None)


def exigir_login():
    """Bloqueia se nao estiver logado. Devolve o utilizador."""
    if not esta_logado():
        st.warning("Sessao expirada. Faz login.")
        st.stop()
    return utilizador_actual()