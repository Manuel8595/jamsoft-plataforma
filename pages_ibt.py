"""
Página de Transferências entre Farmácias (IBT) — Streamlit.
"""
import streamlit as st
from datetime import datetime

from services.supabase_client import listar_farmacias, _get
from services.transferencias_client import (
    ESTADO_RASCUNHO,
    ESTADO_EM_TRANSITO,
    ESTADO_RECEBIDA_PARCIAL,
    ESTADO_CONCLUIDA,
    ESTADO_CANCELADA,
    ESTADO_DIVERGENCIA,
    CORES_ESTADO,
    listar_transferencias,
    listar_todas_transferencias,
    obter_transferencia,
    listar_itens,
    listar_historico,
    estatisticas_ibt,
    criar_transferencia,
    adicionar_item,
    atualizar_totais,
    enviar_transferencia,
    receber_transferencia,
    cancelar_transferencia,
    eliminar_transferencia,
    registar_historico,
)


def _fmt_kz(valor):
    try:
        return f"Kz {float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "Kz 0"


def _badge(estado):
    """Devolve emoji + texto do estado."""
    mapa = {
        ESTADO_RASCUNHO: "📝 Rascunho",
        ESTADO_EM_TRANSITO: "🚚 Em trânsito",
        ESTADO_RECEBIDA_PARCIAL: "⚠️ Recebida parcial",
        ESTADO_CONCLUIDA: "✅ Concluída",
        ESTADO_CANCELADA: "❌ Cancelada",
        ESTADO_DIVERGENCIA: "🔴 Divergência",
    }
    return mapa.get(estado, estado)


def mostrar_ibt():
    """Página principal de Transferências entre Farmácias."""
    st.title("🔄 Transferências entre Farmácias")
    st.caption("Inter-Branch Transfer (IBT) — movimentos de stock entre lojas")
    st.markdown("---")

    # ─── ESTATÍSTICAS ───
    with st.spinner("A carregar estatísticas..."):
        stats = estatisticas_ibt()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("📝 Rascunho", stats.get(ESTADO_RASCUNHO, 0))
    with c2:
        st.metric("🚚 Em trânsito", stats.get(ESTADO_EM_TRANSITO, 0))
    with c3:
        st.metric("⚠️ Parcial", stats.get(ESTADO_RECEBIDA_PARCIAL, 0))
    with c4:
        st.metric("✅ Concluída", stats.get(ESTADO_CONCLUIDA, 0))
    with c5:
        st.metric("🔴 Divergência", stats.get(ESTADO_DIVERGENCIA, 0))
    with c6:
        st.metric("❌ Cancelada", stats.get(ESTADO_CANCELADA, 0))

    st.markdown("---")

    # ─── TABS ───
    tab_lista, tab_nova, tab_dashboard = st.tabs([
        "📋 Lista",
        "➕ Nova Transferência",
        "📊 Dashboard",
    ])

    with tab_lista:
        _tab_lista()

    with tab_nova:
        _tab_nova()

    with tab_dashboard:
        _tab_dashboard()


# ============================================================
# TAB 1 — LISTA
# ============================================================

def _tab_lista():
    """Lista de transferências."""
    st.subheader("📋 Transferências")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        filtro_estado = st.selectbox(
            "Estado",
            [
                "TODAS (activas)",
                "TODAS (com arquivadas)",
                ESTADO_RASCUNHO,
                ESTADO_EM_TRANSITO,
                ESTADO_RECEBIDA_PARCIAL,
                ESTADO_CONCLUIDA,
                ESTADO_DIVERGENCIA,
                ESTADO_CANCELADA,
            ],
            key="ibt_filtro_estado",
        )

    with col2:
        farmacias = listar_farmacias()
        opcoes_farm = [{"id": None, "nome": "Todas as farmácias"}] + farmacias
        farm_filtro = st.selectbox(
            "Farmácia",
            opcoes_farm,
            format_func=lambda f: f["nome"],
            key="ibt_filtro_farm",
        )

    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Atualizar", use_container_width=True, key="ibt_refresh"):
            st.cache_data.clear()
            st.rerun()

    # Buscar dados
    farm_id = farm_filtro.get("id") if isinstance(farm_filtro, dict) else None

    with st.spinner("A carregar..."):
        if filtro_estado == "TODAS (activas)":
            trans = listar_transferencias(estado=None, farmacia_id=farm_id)
        elif filtro_estado == "TODAS (com arquivadas)":
            trans = listar_todas_transferencias(farmacia_id=farm_id)
        else:
            trans = listar_transferencias(estado=filtro_estado, farmacia_id=farm_id)

    if not trans:
        st.info("Nenhuma transferência encontrada.")
        return

    st.caption(f"Total: **{len(trans)}** transferência(s)")

    # ─── Cada transferência num card ───
    for t in trans:
        _card_transferencia(t)


def _card_transferencia(t):
    """Mostra uma transferência num card com botões de acção."""
    trans_id = t.get("id")
    referencia = t.get("referencia", "?")
    estado = t.get("estado", "?")
    origem = t.get("farmacia_origem_nome", "?")
    destino = t.get("farmacia_destino_nome", "?")
    data_criacao = (t.get("data_criacao") or "")[:16]
    valor = t.get("valor_estimado", 0)
    n_itens = t.get("total_itens", 0)
    qtd = t.get("total_quantidade", 0)

    cor = CORES_ESTADO.get(estado, "#94a3b8")

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.markdown(f"### {referencia}")
            st.caption(f"Criada em: {data_criacao}")
            st.markdown(f"**{origem}** → **{destino}**")

        with col2:
            st.markdown(f"**{_badge(estado)}**")
            st.caption(f"{n_itens} item(s) | {qtd} unidade(s)")
            st.markdown(f"💰 **{_fmt_kz(valor)}**")

        with col3:
            if estado == ESTADO_RASCUNHO:
                if st.button("✏️ Continuar", key=f"cont_{trans_id}", use_container_width=True):
                    st.session_state["ibt_continuar_id"] = trans_id
                    st.rerun()
                if st.button("🗑️ Eliminar", key=f"del_{trans_id}", use_container_width=True):
                    st.session_state["ibt_eliminar_id"] = trans_id
                    st.rerun()

            elif estado == ESTADO_EM_TRANSITO:
                if st.button("📥 Receber", key=f"rec_{trans_id}", use_container_width=True, type="primary"):
                    st.session_state["ibt_receber_id"] = trans_id
                    st.rerun()
                if st.button("🔍 Ver detalhes", key=f"det_{trans_id}", use_container_width=True):
                    st.session_state["ibt_detalhes_id"] = trans_id
                    st.rerun()

            else:
                if st.button("🔍 Ver detalhes", key=f"det_{trans_id}", use_container_width=True):
                    st.session_state["ibt_detalhes_id"] = trans_id
                    st.rerun()

    # ─── Modais de acção ───
    if st.session_state.get("ibt_receber_id") == trans_id:
        _modal_receber(trans_id)

    if st.session_state.get("ibt_detalhes_id") == trans_id:
        _modal_detalhes(trans_id)

    if st.session_state.get("ibt_eliminar_id") == trans_id:
        _modal_eliminar(trans_id)

    if st.session_state.get("ibt_continuar_id") == trans_id:
        st.warning("⚠️ Edição de rascunho não implementada nesta versão.")
        if st.button("OK", key=f"ok_cont_{trans_id}"):
            st.session_state.pop("ibt_continuar_id", None)
            st.rerun()


# ============================================================
# MODAIS
# ============================================================

def _modal_detalhes(trans_id):
    """Modal de detalhes — itens + histórico."""
    trans = obter_transferencia(trans_id)
    if not trans:
        st.error("Não encontrada")
        st.session_state.pop("ibt_detalhes_id", None)
        return

    st.markdown("---")
    st.markdown(f"## 🔍 Detalhes — {trans.get('referencia', '?')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Estado:** {_badge(trans.get('estado'))}")
        st.markdown(f"**Origem:** {trans.get('farmacia_origem_nome', '?')}")
        st.markdown(f"**Destino:** {trans.get('farmacia_destino_nome', '?')}")
        st.markdown(f"**Criada por:** {trans.get('utilizador_criou_nome', '?')}")

    with col2:
        st.markdown(f"**Data criação:** {(trans.get('data_criacao') or '')[:16]}")
        st.markdown(f"**Data envio:** {(trans.get('data_envio') or '-')[:16]}")
        st.markdown(f"**Data recepção:** {(trans.get('data_recepcao') or '-')[:16]}")
        st.markdown(f"**Autorizado por:** {trans.get('autorizado_por') or '-'}")

    if trans.get("observacoes"):
        st.info(f"**Observações:** {trans['observacoes']}")

    # Itens
    st.markdown("### 📦 Itens")
    itens = listar_itens(trans_id)

    if itens:
        for it in itens:
            c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
            with c1:
                st.markdown(f"**{it.get('produto_nome', '?')}**")
            with c2:
                st.caption(f"Env: {it.get('quantidade_enviada', 0)}")
            with c3:
                st.caption(f"Rec: {it.get('quantidade_recebida', 0)}")
            with c4:
                dif = it.get("diferenca", 0) or 0
                if dif != 0:
                    st.markdown(f"🔴 {dif:+d}")
                else:
                    st.markdown("✅")
    else:
        st.info("Sem itens.")

    # Histórico
    st.markdown("### 📜 Histórico")
    historico = listar_historico(trans_id)

    if historico:
        for h in historico:
            st.markdown(
                f"- **{(h.get('data') or '')[:16]}** — {h.get('acao', '?')} "
                f"por **{h.get('utilizador_nome', '?')}** — {h.get('detalhes', '')}"
            )
    else:
        st.info("Sem histórico.")

    if st.button("❌ Fechar detalhes", key=f"close_det_{trans_id}", use_container_width=True):
        st.session_state.pop("ibt_detalhes_id", None)
        st.rerun()


def _modal_receber(trans_id):
    """Modal para receber uma transferência em trânsito."""
    trans = obter_transferencia(trans_id)
    if not trans:
        st.error("Não encontrada")
        st.session_state.pop("ibt_receber_id", None)
        return

    st.markdown("---")
    st.markdown(f"## 📥 Receber — {trans.get('referencia', '?')}")
    st.markdown(f"**{trans.get('farmacia_origem_nome')}** → **{trans.get('farmacia_destino_nome')}**")

    itens = listar_itens(trans_id)
    if not itens:
        st.warning("Sem itens.")
        return

    st.markdown("### Confirma o que chegou:")
    st.caption("Altera a quantidade se for diferente do enviado.")

    itens_recebidos = {}

    for it in itens:
        item_id = it.get("id")
        qtd_env = it.get("quantidade_enviada", 0)

        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{it.get('produto_nome', '?')}**")
                st.caption(f"Enviado: **{qtd_env}** unidades")
            with c2:
                qtd_rec = st.number_input(
                    "Recebido",
                    min_value=0,
                    max_value=int(qtd_env) if qtd_env else 0,
                    value=int(qtd_env) if qtd_env else 0,
                    key=f"rec_qtd_{item_id}",
                )
                itens_recebidos[item_id] = qtd_rec

    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirmar recepção", type="primary", use_container_width=True, key=f"conf_rec_{trans_id}"):
            utilizador_nome = "Sistema Web"  # ou o nome do utilizador logado
            ok, msg = receber_transferencia(trans_id, utilizador_nome, itens_recebidos)
            if ok:
                st.success(f"✅ {msg}")
                st.session_state.pop("ibt_receber_id", None)
                import time
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(f"❌ {msg}")

    with col2:
        if st.button("❌ Cancelar", use_container_width=True, key=f"cancel_rec_{trans_id}"):
            st.session_state.pop("ibt_receber_id", None)
            st.rerun()


def _modal_eliminar(trans_id):
    """Modal de confirmação de eliminação."""
    trans = obter_transferencia(trans_id)
    if not trans:
        st.session_state.pop("ibt_eliminar_id", None)
        return

    st.markdown("---")
    st.warning(
        f"⚠️ Eliminar **{trans.get('referencia', '?')}**?\n\n"
        "Esta acção não pode ser revertida."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Sim, eliminar", type="primary", use_container_width=True, key=f"yes_del_{trans_id}"):
            ok, msg = eliminar_transferencia(trans_id, "Sistema Web")
            if ok:
                st.success(f"✅ {msg}")
                st.session_state.pop("ibt_eliminar_id", None)
                import time
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(f"❌ {msg}")

    with col2:
        if st.button("❌ Não", use_container_width=True, key=f"no_del_{trans_id}"):
            st.session_state.pop("ibt_eliminar_id", None)
            st.rerun()


# ============================================================
# TAB 2 — NOVA TRANSFERÊNCIA
# ============================================================

def _tab_nova():
    """Criar nova transferência."""
    st.subheader("➕ Nova Transferência")

    farmacias = listar_farmacias()

    if len(farmacias) < 2:
        st.warning("Precisas de **pelo menos 2 farmácias** para fazer transferências.")
        return

    # ─── Escolher origem e destino ───
    col1, col2 = st.columns(2)

    with col1:
        origem = st.selectbox(
            "🏢 Farmácia Origem",
            farmacias,
            format_func=lambda f: f["nome"],
            key="nova_origem",
        )

    with col2:
        destinos_possiveis = [f for f in farmacias if f["id"] != origem["id"]]
        destino = st.selectbox(
            "🎯 Farmácia Destino",
            destinos_possiveis,
            format_func=lambda f: f["nome"],
            key="nova_destino",
        )

    observacoes = st.text_input("📝 Observações (opcional)", key="nova_obs")

    st.markdown("---")
    st.markdown("### 📦 Adicionar Produtos")

    # ─── Carrinho na sessão ───
    if "ibt_carrinho" not in st.session_state:
        st.session_state["ibt_carrinho"] = []

    # ─── Adicionar produto ───
    col_a, col_b, col_c = st.columns([3, 1, 1])

    with col_a:
        busca = st.text_input("🔎 Código de barras ou nome", key="nova_busca")

    with col_b:
        qtd_add = st.number_input("Qtd", min_value=1, value=1, key="nova_qtd")

    with col_c:
        st.write("")
        if st.button("➕ Adicionar", use_container_width=True, key="nova_add"):
            if not busca:
                st.warning("Escreve o código ou nome do produto.")
            else:
                # Buscar produto
                produtos = _get("produtos", {
                    "select": "id,nome,codigo_barras,preco_custo,estoque_atual",
                    "or": f"(codigo_barras.eq.{busca},nome.ilike.%{busca}%)",
                    "limit": "5",
                }) or []

                if not produtos:
                    st.error(f"Produto '{busca}' não encontrado.")
                else:
                    p = produtos[0]
                    # Verificar se já está no carrinho
                    existente = next(
                        (i for i in st.session_state["ibt_carrinho"] if i["id"] == p["id"]),
                        None
                    )
                    if existente:
                        existente["qtd"] += qtd_add
                    else:
                        st.session_state["ibt_carrinho"].append({
                            "id": p["id"],
                            "nome": p.get("nome", "?"),
                            "codigo": p.get("codigo_barras", ""),
                            "qtd": qtd_add,
                            "preco_custo": p.get("preco_custo", 0) or 0,
                            "estoque": p.get("estoque_atual", 0) or 0,
                        })
                    st.success(f"Adicionado: {p.get('nome')}")
                    st.rerun()

    # ─── Carrinho ───
    carrinho = st.session_state["ibt_carrinho"]

    if carrinho:
        st.markdown("#### 🛒 Carrinho")
        for i, item in enumerate(carrinho):
            c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1])
            with c1:
                st.markdown(f"**{item['nome']}**")
                st.caption(f"Código: {item['codigo']} | Estoque origem: {item['estoque']}")
            with c2:
                st.caption(f"Qtd: {item['qtd']}")
            with c3:
                sub = item["qtd"] * item["preco_custo"]
                st.caption(f"Sub: {_fmt_kz(sub)}")
            with c4:
                st.caption(f"Custo: {_fmt_kz(item['preco_custo'])}")
            with c5:
                if st.button("🗑️", key=f"ibt_rm_{i}"):
                    carrinho.pop(i)
                    st.rerun()

        total = sum(i["qtd"] * i["preco_custo"] for i in carrinho)
        st.markdown(f"**Total: {_fmt_kz(total)}** ({len(carrinho)} itens)")

        st.markdown("---")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("💾 Criar como Rascunho", use_container_width=True, key="ibt_criar_rasc"):
                _criar_ibt(origem, destino, observacoes, carrinho, enviar=False)

        with col_b:
            if st.button("🚀 Criar e Enviar", type="primary", use_container_width=True, key="ibt_criar_env"):
                _criar_ibt(origem, destino, observacoes, carrinho, enviar=True)

        if st.button("🧹 Limpar carrinho", use_container_width=True, key="ibt_limpar"):
            st.session_state["ibt_carrinho"] = []
            st.rerun()
    else:
        st.info("Carrinho vazio. Adiciona produtos acima.")


def _criar_ibt(origem, destino, observacoes, carrinho, enviar=False):
    """Cria uma transferência (rascunho ou já enviada)."""
    with st.spinner("A criar transferência..."):
        utilizador_nome = "Sistema Web"

        # Criar transferência
        ok, resultado = criar_transferencia(
            origem,
            destino,
            utilizador_nome,
            observacoes,
        )

        if not ok:
            st.error(f"❌ {resultado}")
            return

        trans_id = resultado

        # Buscar UUID
        trans = obter_transferencia(trans_id)
        trans_uuid = trans.get("uuid") if trans else ""

        # Adicionar itens
        for item in carrinho:
            adicionar_item(
                trans_id,
                trans_uuid,
                {"id": item["id"], "nome": item["nome"], "codigo_barras": item["codigo"]},
                item["qtd"],
                item["preco_custo"],
            )

        # Actualizar totais
        atualizar_totais(trans_id)

        # Enviar se pedido
        if enviar:
            ok_env, msg_env = enviar_transferencia(trans_id, utilizador_nome)
            if not ok_env:
                st.warning(f"Transferência criada mas não enviada: {msg_env}")

        # Limpar carrinho
        st.session_state["ibt_carrinho"] = []

        st.success(f"✅ Transferência criada com sucesso! (ID: {trans_id})")
        st.balloons()
        import time
        time.sleep(2)
        st.rerun()


# ============================================================
# TAB 3 — DASHBOARD
# ============================================================

def _tab_dashboard():
    """Dashboard de IBTs."""
    st.subheader("📊 Dashboard")

    stats = estatisticas_ibt()
    total = sum(stats.values())

    st.markdown(f"### Total: {total} transferências")
    st.markdown("---")

    # Cards por estado
    for estado, qtd in stats.items():
        cor = CORES_ESTADO.get(estado, "#94a3b8")
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{_badge(estado)}**")
            with c2:
                st.markdown(f"### {qtd}")

    st.markdown("---")

    # IBTs em trânsito
    st.markdown("### 🚚 Em trânsito (a aguardar recepção)")
    em_transito = listar_transferencias(estado=ESTADO_EM_TRANSITO)

    if em_transito:
        for t in em_transito[:20]:
            st.markdown(
                f"- **{t.get('referencia')}** — "
                f"{t.get('farmacia_origem_nome')} → {t.get('farmacia_destino_nome')} "
                f"({t.get('total_itens', 0)} itens)"
            )
    else:
        st.info("Nenhuma em trânsito.")

    # Divergências
    st.markdown("### 🔴 Divergências (a resolver)")
    divergencias = listar_transferencias(estado=ESTADO_DIVERGENCIA)

    if divergencias:
        for t in divergencias[:20]:
            st.error(
                f"**{t.get('referencia')}** — "
                f"{t.get('farmacia_origem_nome')} → {t.get('farmacia_destino_nome')}"
            )
    else:
        st.success("✅ Sem divergências.")