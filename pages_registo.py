"""
Ecrã de registo via convite.
O novo CEO abre um link ?convite=TOKEN, escolhe nome + senha, e fica registado.
"""

import streamlit as st
from services.auth import (
    convite_valido, obter_convite_por_token, registar_utilizador,
    marcar_convite_usado, obter_utilizador_por_email,
)


def mostrar_registo(token):
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1>💊 JAM Soft</h1>
            <p style='color: #94a3b8;'>Criar Conta de CEO</p>
            <hr style='border-color: #334155;'>
        </div>
    """, unsafe_allow_html=True)
    
    ok, dados = convite_valido(token)
    
    if not ok:
        st.error(f"❌ {dados}")
        st.markdown("---")
        st.caption("Pede um novo convite ao administrador.")
        return
    
    convite = dados
    email = convite.get("email", "")
    nome_sug = convite.get("nome_sugerido", "")
    
    st.info(f"Convite valido para: **{email}**")
    
    if st.session_state.get("logado"):
        st.warning("Ja estas logado. Termina sessao primeiro.")
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Criar a tua conta")
        
        with st.form("form_registo"):
            nome = st.text_input(
                "Nome completo",
                value=nome_sug,
                placeholder="O teu nome",
            )
            senha = st.text_input(
                "Escolhe uma senha",
                type="password",
                placeholder="Minimo 6 caracteres",
            )
            confirma = st.text_input(
                "Confirma a senha",
                type="password",
                placeholder="Repete a senha",
            )
            
            submitted = st.form_submit_button(
                "Criar Conta",
                use_container_width=True,
                type="primary",
            )
        
        if submitted:
            if not nome:
                st.error("Preenche o nome.")
            elif len(senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            elif senha != confirma:
                st.error("As senhas nao coincidem.")
            else:
                # Verificar se ja existe
                if obter_utilizador_por_email(email):
                    st.error("Este email ja esta registado.")
                else:
                    sucesso = registar_utilizador(email, senha, nome)
                    if sucesso:
                        marcar_convite_usado(convite["id"])
                        st.success("✅ Conta criada com sucesso!")
                        st.balloons()
                        st.markdown("---")
                        st.markdown("**Ja podes fazer login com:**")
                        st.code(f"Email: {email}\nSenha: (a que escolheste)", language=None)
                        st.info("Volta ao inicio e faz login.")
                    else:
                        st.error("Erro ao criar conta. Tenta novamente.")