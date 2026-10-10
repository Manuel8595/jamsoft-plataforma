import streamlit as st
from pwa_utils import inject_pwa, mobile_css
from config_cloud import CLOUD_ACCESS_ENABLED
from services.auth import autenticar
from services.supabase_client import definir_jwt, limpar_jwt
from pages_admin import mostrar_admin, mostrar_diagnostico_remoto, mostrar_backup
from pages_ibt import mostrar_ibt
from pages_secundarias import mostrar_chat_ia
from pages_config import mostrar_configuração
from pages_registo import mostrar_registo
try:
    from plataforma_web.dashboard import mostrar_dashboard
except ImportError:
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
    page_title="JAM Soft - Monitorização",
    page_icon="logos/JamLogo_transparente.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# ─── ACTIVAR PWA + CSS MOBILE ───
inject_pwa()
mobile_css()
if not CLOUD_ACCESS_ENABLED:
    st.info("A plataforma online está temporariamente desligada.")
    st.stop()
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "utilizador" not in st.session_state:
    st.session_state["utilizador"] = None
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "📊 Resumo do País"

st.markdown("""
<style>
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    .logo-animado {
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba(124, 58, 237, 0.4));
        width: 180px !important;
        max-width: 180px !important;
        height: auto !important;
    }
    
    /* Mobile: logo mais pequeno */
    @media (max-width: 768px) {
        .logo-animado {
            width: 120px !important;
            max-width: 120px !important;
        }
    }
    
    /* Tablet */
    @media (min-width: 769px) and (max-width: 1024px) {
        .logo-animado {
            max-width: 180px;
        }
    }
    .logo-container {
        text-align: center;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

def mostrar_login():
    # ─── Cabeçalho com logo ───
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            from pathlib import Path
            caminho_logo = Path(__file__).parent / "logos" / "JamLogo_transparente.png"
            if caminho_logo.exists():
                import base64
                with open(caminho_logo, "rb") as f_logo:
                    logo_b64 = base64.b64encode(f_logo.read()).decode()
                st.markdown(
                    f'''<div class="logo-container">
                        <img src="data:image/png;base64,{logo_b64}" class="logo-animado" />
                    </div>''',
                    unsafe_allow_html=True
                )
            else:
                st.markdown("""
                    <div style='text-align: center;'>
                        <h1>💊 JAM Soft</h1>
                    </div>
                """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
                <div style='text-align: center;'>
                    <h1>💊 JAM Soft</h1>
                </div>
            """, unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; padding: 5px 0 15px 0;'>
            <p style='color: #94a3b8; margin: 0;'>Plataforma de Monitorização</p>
            <hr style='border-color: #334155;'>
        </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Entrar")
        with st.form("form_login"):
            email = st.text_input("📧 Email")
            senha = st.text_input("🔑 Senha", type="password")
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
                    st.error("Email ou senha incorrectos.")
# ============================================================
# ENDPOINT PARA CRON-JOB.ORG (backup diario)
# ============================================================
if st.query_params.get("cron") == "backup":
    token = st.query_params.get("token", "")
    TOKEN_ESPERADO = "jamsoft-cron-2026-secreto"
    if token != TOKEN_ESPERADO:
        st.error("Token inválido")
        st.stop()
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        from datetime import datetime as _dt
        from backup_service import criar_backup, ultimo_backup_path, ler_backup_bytes
        # ─── 1. Criar o backup ───
        ok, msg = criar_backup()
        if not ok:
            st.error(f"Erro ao criar backup: {msg}")
            st.stop()
        # ─── 2. Config email ───
        EMAIL_REMETENTE = st.secrets.get("EMAIL_REMETENTE", "")
        EMAIL_SENHA_APP = st.secrets.get("EMAIL_SENHA_APP", "")
        EMAIL_SMTP = st.secrets.get("EMAIL_SMTP", "smtp.gmail.com")
        EMAIL_PORTA = int(st.secrets.get("EMAIL_PORTA", "587"))
        EMAIL_DESTINO = "simaom510@gmail.com"
        if not EMAIL_REMETENTE or not EMAIL_SENHA_APP:
            st.error("Config email em falta nos Secrets.")
            st.stop()
        # ─── 3. Preparar mensagem ───
        hoje = _dt.now()
        assunto = f"JAM Soft — Backup diário ({hoje.strftime('%d/%m/%Y')})"
        # Corpo do email (versão simples)
        corpo_texto = f"""
Backup diário JAM Soft — {hoje.strftime('%d/%m/%Y às %H:%M')}
{msg}
Este email contém o ficheiro de backup em anexo (encriptado AES-256).
Guarda-o num sítio seguro.
Para abrir o ficheiro, precisas da BACKUP_KEY configurada no secrets.toml.
JAM Soft © {hoje.year}
"""
        # ─── 4. Construir email com anexo ───
        msg_email = MIMEMultipart()
        msg_email["Subject"] = assunto
        msg_email["From"] = f"JAM Soft <{EMAIL_REMETENTE}>"
        msg_email["To"] = EMAIL_DESTINO
        msg_email.attach(MIMEText(corpo_texto, "plain", "utf-8"))
        # Anexo do ficheiro .enc
        ultimo = ultimo_backup_path()
        if ultimo and ultimo.exists():
            conteudo = ler_backup_bytes(ultimo)
            if conteudo:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(conteudo)
                encoders.encode_base64(parte)
                parte.add_header(
                    "Content-Disposition",
                    f"attachment; filename={ultimo.name}",
                )
                msg_email.attach(parte)
        # ─── 5. Enviar ───
        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORTA, timeout=30) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
            server.sendmail(EMAIL_REMETENTE, [EMAIL_DESTINO], msg_email.as_string())
        st.success(f"✅ Backup diário enviado para {EMAIL_DESTINO}")
        st.stop()
    except Exception as e:
        st.error(f"Erro no backup automático: {e}")
        st.stop()
# ============================================================
# ENDPOINT PARA CRON-JOB.ORG (envio semanal de emails)
# ============================================================
query_params_cron = st.query_params
if query_params_cron.get("cron") == "email_semanal":
    token = query_params_cron.get("token", "")
    TOKEN_ESPERADO = "jamsoft-cron-2026-secreto"
    if token != TOKEN_ESPERADO:
        st.error("Token inválido")
        st.stop()
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from datetime import datetime as _dt, timedelta
        # ─── Config email ───
        try:
            EMAIL_REMETENTE = st.secrets.get("EMAIL_REMETENTE", "")
            EMAIL_SENHA_APP = st.secrets.get("EMAIL_SENHA_APP", "")
            EMAIL_SMTP = st.secrets.get("EMAIL_SMTP", "smtp.gmail.com")
            EMAIL_PORTA = int(st.secrets.get("EMAIL_PORTA", "587"))
        except Exception as e_cfg:
            st.error(f"Config email em falta nos Secrets: {e_cfg}")
            st.stop()
        if not EMAIL_REMETENTE or not EMAIL_SENHA_APP:
            st.error("EMAIL_REMETENTE ou EMAIL_SENHA_APP nao configurados nos Secrets do Streamlit.")
            st.stop()
        # ─── Obter destinatarios ───
        from services.supabase_client import _get, listar_farmacias
        users = _get("plataforma_utilizadores", {
            "select": "email",
            "ativo": "eq.true",
        }) or []
        destinatarios = [u.get("email") for u in users if u.get("email")]
        if not destinatarios:
            st.warning("Sem destinatarios registados.")
            st.stop()
        # ─── Dados da semana ───
        from services.supabase_client import vendas_ultimos_dias, resumo_por_farmacia
        vendas_sem = vendas_ultimos_dias(dias=7)
        total_sem = sum(v.get("total", 0) or 0 for v in vendas_sem)
        num_vendas = len(vendas_sem)
        resumo = resumo_por_farmacia(dias=7)
        # ─── HTML ───
        hoje = _dt.now()
        semana_ini = hoje - timedelta(days=7)
        # Linhas por farmácia
        linhas_farm = ""
        for fid, dados in resumo.items():
            nome = dados.get("farmacia", {}).get("nome", "?")
            total = dados.get("total", 0)
            num = dados.get("num_vendas", 0)
            linhas_farm += f"""
            <tr>
                <td style="padding: 8px 0;">{nome}</td>
                <td style="text-align: right; padding: 8px 0;">
                    Kz {total:,.0f}
                </td>
                <td style="text-align: right; padding: 8px 0;">{num}</td>
            </tr>
            """
                # ─── Logo em base64 ───
        LOGO_B64 = ""
        try:
            from pathlib import Path
            caminho_logo_b64 = Path(__file__).parent / "logo_email_base64.txt"
            if caminho_logo_b64.exists():
                LOGO_B64 = caminho_logo_b64.read_text().strip()
        except Exception as e_logo:
            print(f"[Email] Aviso logo: {e_logo}")
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px;">
            <div style="max-width: 700px; margin: 0 auto; background: #1e293b; border-radius: 10px; padding: 30px;">
                <div style="text-align: center; margin-bottom: 15px;">
                    <img src="data:image/png;base64,{LOGO_B64}" 
                         alt="JAM Soft" 
                         style="max-width: 280px; height: auto;">
                </div>
                <p style="color: #94a3b8;">
                    Período: {semana_ini.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}
                </p>
                <hr style="border: 1px solid #334155; margin: 20px 0;">
                <h2 style="color: #10b981;">Total da Semana</h2>
                <table style="width: 100%; color: #f8fafc;">
                    <tr>
                        <td style="padding: 8px 0;">Total vendido:</td>
                        <td style="text-align: right; font-weight: bold; color: #10b981;">
                            Kz {total_sem:,.0f}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0;">Num. vendas:</td>
                        <td style="text-align: right; font-weight: bold;">
                            {num_vendas}
                        </td>
                    </tr>
                </table>
                <hr style="border: 1px solid #334155; margin: 20px 0;">
                <h2 style="color: #fbbf24;">Por Farmácia</h2>
                <table style="width: 100%; color: #f8fafc;">
                    <tr style="border-bottom: 1px solid #334155;">
                        <th style="text-align: left; padding: 8px 0;">Farmácia</th>
                        <th style="text-align: right; padding: 8px 0;">Total</th>
                        <th style="text-align: right; padding: 8px 0;">Vendas</th>
                    </tr>
                    {linhas_farm}
                </table>
                <hr style="border: 1px solid #334155; margin: 20px 0;">
                <p>
                    <a href="https://jamsoft-plataforma-nthcjcruax7wmg9rqxr4qz.streamlit.app"
                       style="background: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
                        Abrir Plataforma
                    </a>
                </p>
                <p style="font-size: 12px; color: #64748b; text-align: center; margin-top: 30px;">
                    JAM Soft © {hoje.year} — Email automático
                </p>
            </div>
        </body>
        </html>
        """
        # ─── Enviar ───
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"JAM Soft — Resumo Semanal ({hoje.strftime('%d/%m/%Y')})"
        msg["From"] = f"JAM Soft <{EMAIL_REMETENTE}>"
        msg["To"] = ", ".join(destinatarios)
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORTA, timeout=20) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
            server.sendmail(EMAIL_REMETENTE, destinatarios, msg.as_string())
        st.success(f"✅ Relatório semanal enviado para {len(destinatarios)} destinatários")
        st.stop()
    except Exception as e:
        st.error(f"Erro: {e}")
        st.stop()
# ============================================================
# CONVITES (registo via link)
# ============================================================
query_params = st.query_params
token_convite = query_params.get("convite", None)
if token_convite:
    mostrar_registo(token_convite)
    st.stop()
# ============================================================
# APLICAÇíO PRINCIPAL (após login)
# ============================================================
if st.session_state["logado"]:
    user = st.session_state["utilizador"]
    with st.sidebar:
        st.markdown(f"### 👤 {user['nome']}")
        st.caption(f"📧 {user['email']}")
        st.markdown("---")
        menu = [
            "📊 Resumo do País",
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
            "🖥️ Diagnostico Remoto",
            "💬 Chat IA",
            "⚙️ Configuração",
            "💾 Backup",
            "🔄 Transferências IBT",
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
            st.session_state["pagina"] = "📊 Resumo do País"
            st.rerun()
    # ─── Rotas ───
    if pagina == "📊 Resumo do País":
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
    elif pagina == "🖥️ Diagnostico Remoto":
        mostrar_diagnostico_remoto(user)
    elif pagina == "💬 Chat IA":
        mostrar_chat_ia()
    elif pagina == "⚙️ Configuração":
        mostrar_configuração()
    elif pagina == "💾 Backup":
        mostrar_backup()
    elif pagina == "🔄 Transferências IBT":
        mostrar_ibt()
else:
    mostrar_login()
