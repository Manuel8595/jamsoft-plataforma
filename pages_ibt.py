"""
Página de Transferências entre Farmácias (IBT) — Streamlit.
"""
import streamlit as st
import time
from datetime import datetime

from services.supabase_client import listar_farmacias, _get
from services.ibt_pdf import gerar_pdf_ibt
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
    _delete,
)


def _fmt_kz(valor):
    try:
        return f"Kz {float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "Kz 0"


def _badge(estado):
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
    """Página principal."""
    st.title("🔄 Transferências entre Farmácias")
    st.caption("Inter-Branch Transfer (IBT) — movimentos de stock entre lojas")
    st.markdown("---")

    stats = estatisticas_ibt()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.metric("📝 Rascunho", stats.get(ESTADO_RASCUNHO, 0))
    with c2: st.metric("🚚 Em trânsito", stats.get(ESTADO_EM_TRANSITO, 0))
    with c3: st.metric("⚠️ Parcial", stats.get(ESTADO_RECEBIDA_PARCIAL, 0))
    with c4: st.metric("✅ Concluída", stats.get(ESTADO_CONCLUIDA, 0))
    with c5: st.metric("🔴 Divergência", stats.get(ESTADO_DIVERGENCIA, 0))
    with c6: st.metric("❌ Cancelada", stats.get(ESTADO_CANCELADA, 0))

    st.markdown("---")

    # Estado global da página
    if "ibt_modo" not in st.session_state:
        st.session_state["ibt_modo"] = "lista"

    if st.session_state["ibt_modo"] == "editar":
        _ecra_editar_rascunho()
    elif st.session_state["ibt_modo"] == "receber":
        _ecra_receber()
    elif st.session_state["ibt_modo"] == "detalhes":
        _ecra_detalhes()
    elif st.session_state["ibt_modo"] == "cancelar":
        _ecra_cancelar()
    else:
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
# LISTA
# ============================================================

def _tab_lista():
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

    for t in trans:
        _card_transferencia(t)


def _card_transferencia(t):
    trans_id = t.get("id")
    referencia = t.get("referencia", "?")
    estado = t.get("estado", "?")
    origem = t.get("farmacia_origem_nome", "?")
    destino = t.get("farmacia_destino_nome", "?")
    data_criacao = (t.get("data_criacao") or "")[:16]
    valor = t.get("valor_estimado", 0)
    n_itens = t.get("total_itens", 0)
    qtd = t.get("total_quantidade", 0)

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
                if st.button("✏️ Editar", key=f"edit_{trans_id}", use_container_width=True, type="primary"):
                    st.session_state["ibt_editar_id"] = trans_id
                    st.session_state["ibt_modo"] = "editar"
                    st.rerun()
                if st.button("🗑️ Eliminar", key=f"del_{trans_id}", use_container_width=True):
                    _eliminar_rascunho(trans_id, referencia)
                if st.button("🔍 Detalhes", key=f"det_{trans_id}", use_container_width=True):
                    st.session_state["ibt_detalhes_id"] = trans_id
                    st.session_state["ibt_modo"] = "detalhes"
                    st.rerun()

            elif estado == ESTADO_EM_TRANSITO:
                if st.button("📥 Receber", key=f"rec_{trans_id}", use_container_width=True, type="primary"):
                    st.session_state["ibt_receber_id"] = trans_id
                    st.session_state["ibt_modo"] = "receber"
                    st.rerun()
                if st.button("🔍 Detalhes", key=f"det_{trans_id}", use_container_width=True):
                    st.session_state["ibt_detalhes_id"] = trans_id
                    st.session_state["ibt_modo"] = "detalhes"
                    st.rerun()
                if st.button("❌ Cancelar", key=f"cancel_{trans_id}", use_container_width=True):
                    st.session_state["ibt_cancelar_id"] = trans_id
                    st.session_state["ibt_modo"] = "cancelar"
                    st.rerun()

            else:
                if st.button("🔍 Detalhes", key=f"det_{trans_id}", use_container_width=True):
                    st.session_state["ibt_detalhes_id"] = trans_id
                    st.session_state["ibt_modo"] = "detalhes"
                    st.rerun()


# ============================================================
# ELIMINAR RASCUNHO (directo, com confirmação inline)
# ============================================================

def _eliminar_rascunho(trans_id, referencia):
    ok, msg = eliminar_transferencia(trans_id, "Sistema Web")
    if ok:
        st.success(f"✅ {referencia} eliminada")
        time.sleep(1.2)
        st.rerun()
    else:
        st.error(f"❌ {msg}")


# ============================================================
# ECRí: EDITAR RASCUNHO
# ============================================================

def _ecra_editar_rascunho():
    trans_id = st.session_state.get("ibt_editar_id")
    if not trans_id:
        st.session_state["ibt_modo"] = "lista"
        st.rerun()
        return

    trans = obter_transferencia(trans_id)
    if not trans:
        st.error("Transferência não encontrada")
        _voltar_lista()
        return

    if trans.get("estado") != ESTADO_RASCUNHO:
        st.error(f"Só rascunhos podem ser editados. Estado actual: {trans.get('estado')}")
        _voltar_lista()
        return

    st.markdown(f"## ✏️ Editar {trans.get('referencia')}")

    if st.button("⬅️ Voltar à lista", key="voltar_editar"):
        _voltar_lista()

    st.markdown("---")

    # Carregar itens existentes para o carrinho
    if st.session_state.get("ibt_carrinho_id") != trans_id:
        itens = listar_itens(trans_id)
        carrinho = []
        for it in itens:
            carrinho.append({
                "id": it.get("produto_id"),
                "nome": it.get("produto_nome", "?"),
                "codigo": it.get("codigo_barras", ""),
                "qtd": it.get("quantidade_enviada", 0),
                "preco_custo": it.get("preco_custo", 0) or 0,
                "estoque": 0,
            })
        st.session_state["ibt_carrinho"] = carrinho
        st.session_state["ibt_carrinho_id"] = trans_id

    # Mostrar cabeçalho (origem/destino/observações)
    farmacias = listar_farmacias()

    col1, col2 = st.columns(2)

    with col1:
        # Origem fixa
        origem = {
            "id": trans.get("farmacia_origem_id"),
            "codigo": trans.get("farmacia_origem_codigo"),
            "nome": trans.get("farmacia_origem_nome"),
        }
        st.markdown(f"**🏢 Origem:** {origem['nome']}")

    with col2:
        # Destino editável
        destinos_possiveis = [f for f in farmacias if f["id"] != origem["id"]]
        idx_dest = 0
        for i, f in enumerate(destinos_possiveis):
            if f["id"] == trans.get("farmacia_destino_id"):
                idx_dest = i
                break

        destino = st.selectbox(
            "🎯 Destino",
            destinos_possiveis,
            index=idx_dest,
            format_func=lambda f: f["nome"],
            key="edit_destino",
        )

    observacoes = st.text_input(
        "📝 Observações",
        value=trans.get("observacoes", "") or "",
        key="edit_obs",
    )

    st.markdown("---")
    st.markdown("### 📦 Produtos")

    # Adicionar produtos
    col_a, col_b, col_c = st.columns([3, 1, 1])

    with col_a:
        busca = st.text_input("🔎 Código ou nome", key="edit_busca")

    with col_b:
        qtd_add = st.number_input("Qtd", min_value=1, value=1, key="edit_qtd")

    with col_c:
        st.write("")
        if st.button("➕ Adicionar", use_container_width=True, key="edit_add"):
            _adicionar_ao_carrinho(busca, qtd_add)

    # Carrinho
    carrinho = st.session_state.get("ibt_carrinho", [])

    if carrinho:
        st.markdown("#### 🛒 Itens")
        for i, item in enumerate(carrinho):
            c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1])
            with c1:
                st.markdown(f"**{item['nome']}**")
            with c2:
                st.caption(f"Qtd: {item['qtd']}")
            with c3:
                sub = item["qtd"] * item["preco_custo"]
                st.caption(f"{_fmt_kz(sub)}")
            with c4:
                st.caption(f"{_fmt_kz(item['preco_custo'])}")
            with c5:
                if st.button("🗑️", key=f"edit_rm_{i}"):
                    carrinho.pop(i)
                    st.rerun()

        total = sum(i["qtd"] * i["preco_custo"] for i in carrinho)
        st.markdown(f"**Total: {_fmt_kz(total)}** ({len(carrinho)} itens)")

        st.markdown("---")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("💾 Guardar Rascunho", use_container_width=True, key="edit_guardar"):
                _guardar_edicao(trans_id, trans, destino, observacoes, carrinho, enviar=False)

        with col_b:
            if st.button("🚀 Enviar", type="primary", use_container_width=True, key="edit_enviar"):
                _guardar_edicao(trans_id, trans, destino, observacoes, carrinho, enviar=True)
    else:
        st.info("Sem itens. Adiciona produtos acima.")


def _adicionar_ao_carrinho(busca, qtd):
    if not busca:
        st.warning("Escreve o código ou nome")
        return

    produtos = _get("produtos", {
        "select": "id,nome,codigo_barras,preco_custo,estoque_atual",
        "or": f"(codigo_barras.eq.{busca},nome.ilike.%{busca}%)",
        "limit": "5",
    }) or []

    if not produtos:
        st.error(f"Produto '{busca}' não encontrado.")
        return

    p = produtos[0]
    existente = next((i for i in st.session_state["ibt_carrinho"] if i["id"] == p["id"]), None)

    if existente:
        existente["qtd"] += qtd
    else:
        st.session_state["ibt_carrinho"].append({
            "id": p["id"],
            "nome": p.get("nome", "?"),
            "codigo": p.get("codigo_barras", ""),
            "qtd": qtd,
            "preco_custo": p.get("preco_custo", 0) or 0,
            "estoque": p.get("estoque_atual", 0) or 0,
        })
    st.success(f"Adicionado: {p.get('nome')}")
    st.rerun()


def _guardar_edicao(trans_id, trans, destino, observacoes, carrinho, enviar=False):
    """Guarda alterações ao rascunho."""
    with st.spinner("A guardar..."):
        # 1. Apagar itens antigos
        _delete("itens_transferencia", f"transferencia_id=eq.{trans_id}")

        # 2. Actualizar cabeçalho
        from services.supabase_client import _patch
        _patch("transferencias_filiais", f"id=eq.{trans_id}", {
            "farmacia_destino_id": destino["id"],
            "farmacia_destino_codigo": destino.get("codigo", ""),
            "farmacia_destino_nome": destino["nome"],
            "observacoes": observacoes or "",
        })

        # 3. Adicionar itens novos
        trans_uuid = trans.get("uuid", "")
        for item in carrinho:
            adicionar_item(
                trans_id,
                trans_uuid,
                {"id": item["id"], "nome": item["nome"], "codigo_barras": item["codigo"]},
                item["qtd"],
                item["preco_custo"],
            )

        # 4. Actualizar totais
        atualizar_totais(trans_id)

        # 5. Enviar se pedido
        if enviar:
            ok_env, msg_env = enviar_transferencia(trans_id, "Sistema Web")
            if not ok_env:
                st.warning(f"Guardado mas não enviado: {msg_env}")

        # Limpar carrinho
        st.session_state["ibt_carrinho"] = []
        st.session_state.pop("ibt_carrinho_id", None)
        st.session_state.pop("ibt_editar_id", None)

        st.success("✅ Guardado com sucesso!")
        time.sleep(1)
        _voltar_lista()


# ============================================================
# ECRí: RECEBER
# ============================================================

def _ecra_receber():
    trans_id = st.session_state.get("ibt_receber_id")
    if not trans_id:
        st.session_state["ibt_modo"] = "lista"
        st.rerun()
        return

    trans = obter_transferencia(trans_id)
    if not trans:
        st.error("Não encontrada")
        _voltar_lista()
        return

    st.markdown(f"## 📥 Receber {trans.get('referencia')}")
    st.markdown(f"**{trans.get('farmacia_origem_nome')}** → **{trans.get('farmacia_destino_nome')}**")

    if st.button("⬅️ Voltar", key="voltar_receber"):
        _voltar_lista()

    st.markdown("---")

    itens = listar_itens(trans_id)
    if not itens:
        st.warning("Sem itens.")
        return

    st.markdown("### Confirma o que chegou:")

    itens_recebidos = {}

    for it in itens:
        item_id = it.get("id")
        qtd_env = it.get("quantidade_enviada", 0) or 0

        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{it.get('produto_nome', '?')}**")
                st.caption(f"Enviado: **{qtd_env}** unidades")
            with c2:
                qtd_rec = st.number_input(
                    "Recebido",
                    min_value=0,
                    max_value=int(qtd_env),
                    value=int(qtd_env),
                    key=f"rec_qtd_{item_id}",
                )
                itens_recebidos[item_id] = qtd_rec

    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirmar", type="primary", use_container_width=True, key="conf_rec"):
            ok, msg = receber_transferencia(trans_id, "Sistema Web", itens_recebidos)
            if ok:
                st.success(f"✅ {msg}")
                st.session_state.pop("ibt_receber_id", None)
                time.sleep(1.5)
                _voltar_lista()
            else:
                st.error(f"❌ {msg}")

    with col2:
        if st.button("❌ Cancelar", use_container_width=True, key="cancel_rec"):
            st.session_state.pop("ibt_receber_id", None)
            _voltar_lista()


# ============================================================
# ECRí: CANCELAR
# ============================================================

def _ecra_cancelar():
    trans_id = st.session_state.get("ibt_cancelar_id")
    if not trans_id:
        st.session_state["ibt_modo"] = "lista"
        st.rerun()
        return

    trans = obter_transferencia(trans_id)
    if not trans:
        st.error("Não encontrada")
        _voltar_lista()
        return

    st.markdown(f"## ❌ Cancelar {trans.get('referencia')}")
    st.markdown(f"**{trans.get('farmacia_origem_nome')}** → **{trans.get('farmacia_destino_nome')}**")

    if st.button("⬅️ Voltar", key="voltar_cancelar"):
        _voltar_lista()

    st.markdown("---")

    st.warning(
        "⚠️ Se esta IBT estiver **em trânsito**, o stock será **devolvido à origem**."
    )

    motivo = st.text_area("📝 Motivo do cancelamento (obrigatório)", key="motivo_cancelar")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirmar cancelamento", type="primary", use_container_width=True, key="confirmar_cancelar"):
            if not motivo or len(motivo.strip()) < 3:
                st.error("Escreve um motivo (mínimo 3 caracteres)")
            else:
                ok, msg = cancelar_transferencia(trans_id, motivo.strip(), "Sistema Web")
                if ok:
                    st.success(f"✅ {msg}")
                    st.session_state.pop("ibt_cancelar_id", None)
                    time.sleep(1.5)
                    _voltar_lista()
                else:
                    st.error(f"❌ {msg}")

    with col2:
        if st.button("❌ Fechar", use_container_width=True, key="fechar_cancelar"):
            st.session_state.pop("ibt_cancelar_id", None)
            _voltar_lista()


# ============================================================
# ECRí: DETALHES
# ============================================================

def _ecra_detalhes():
    trans_id = st.session_state.get("ibt_detalhes_id")
    if not trans_id:
        st.session_state["ibt_modo"] = "lista"
        st.rerun()
        return

    trans = obter_transferencia(trans_id)
    if not trans:
        st.error("Não encontrada")
        _voltar_lista()
        return

    st.markdown(f"## 🔍 {trans.get('referencia')}")

    if st.button("⬅️ Voltar", key="voltar_detalhes"):
        _voltar_lista()

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Estado:** {_badge(trans.get('estado'))}")
        st.markdown(f"**Origem:** {trans.get('farmacia_origem_nome', '?')}")
        st.markdown(f"**Destino:** {trans.get('farmacia_destino_nome', '?')}")
        st.markdown(f"**Criada por:** {trans.get('utilizador_criou_nome', '?')}")

    with col2:
        st.markdown(f"**Criação:** {(trans.get('data_criacao') or '')[:16]}")
        st.markdown(f"**Envio:** {(trans.get('data_envio') or '-')[:16]}")
        st.markdown(f"**Recepção:** {(trans.get('data_recepcao') or '-')[:16]}")
        st.markdown(f"**Autorizado:** {trans.get('autorizado_por') or '-'}")

    if trans.get("observacoes"):
        st.info(f"**Observações:** {trans['observacoes']}")

    # Itens
    st.markdown("### 📦 Itens")
    itens = listar_itens(trans_id)

    if itens:
        for it in itens:
            c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
            with c1: st.markdown(f"**{it.get('produto_nome', '?')}**")
            with c2: st.caption(f"Env: {it.get('quantidade_enviada', 0)}")
            with c3: st.caption(f"Rec: {it.get('quantidade_recebida', 0)}")
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

    # ─── Botão de PDF ───
    st.markdown("---")
    st.markdown("### 📄 Exportar")

    if st.button("📄 Gerar PDF do Comprovativo", type="primary", use_container_width=True, key="gerar_pdf_btn"):
        try:
            with st.spinner("A gerar PDF..."):
                pdf_bytes = gerar_pdf_ibt(trans, itens, historico)

            st.download_button(
                label=f"📥 Descarregar {trans.get('referencia', 'IBT')}.pdf",
                data=pdf_bytes,
                file_name=f"{trans.get('referencia', 'IBT')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="baixar_pdf_btn",
            )
        except Exception as e:
            st.error(f"❌ Erro ao gerar PDF: {e}")

# ============================================================
# TAB NOVA
# ============================================================

def _tab_nova():
    st.subheader("➕ Nova Transferência")

    farmacias = listar_farmacias()
    if len(farmacias) < 2:
        st.warning("Precisas de pelo menos 2 farmácias.")
        return

    col1, col2 = st.columns(2)
    with col1:
        origem = st.selectbox("🏢 Origem", farmacias,
                                format_func=lambda f: f["nome"], key="nova_origem")
    with col2:
        destinos = [f for f in farmacias if f["id"] != origem["id"]]
        destino = st.selectbox("🎯 Destino", destinos,
                                 format_func=lambda f: f["nome"], key="nova_destino")

    observacoes = st.text_input("📝 Observações", key="nova_obs")

    st.markdown("---")
    st.markdown("### 📦 Produtos")

    if "ibt_carrinho" not in st.session_state:
        st.session_state["ibt_carrinho"] = []

    col_a, col_b, col_c = st.columns([3, 1, 1])
    with col_a:
        busca = st.text_input("🔎 Código ou nome", key="nova_busca")
    with col_b:
        qtd_add = st.number_input("Qtd", min_value=1, value=1, key="nova_qtd")
    with col_c:
        st.write("")
        if st.button("➕ Adicionar", use_container_width=True, key="nova_add"):
            _adicionar_ao_carrinho(busca, qtd_add)

    carrinho = st.session_state["ibt_carrinho"]

    if carrinho:
        st.markdown("#### 🛒 Carrinho")
        for i, item in enumerate(carrinho):
            c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1])
            with c1: st.markdown(f"**{item['nome']}**")
            with c2: st.caption(f"Qtd: {item['qtd']}")
            with c3:
                sub = item["qtd"] * item["preco_custo"]
                st.caption(f"{_fmt_kz(sub)}")
            with c4: st.caption(f"{_fmt_kz(item['preco_custo'])}")
            with c5:
                if st.button("🗑️", key=f"nova_rm_{i}"):
                    carrinho.pop(i)
                    st.rerun()

        total = sum(i["qtd"] * i["preco_custo"] for i in carrinho)
        st.markdown(f"**Total: {_fmt_kz(total)}** ({len(carrinho)} itens)")

        st.markdown("---")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("💾 Criar Rascunho", use_container_width=True, key="criar_rasc"):
                _criar_nova(origem, destino, observacoes, carrinho, enviar=False)
        with col_b:
            if st.button("🚀 Criar e Enviar", type="primary", use_container_width=True, key="criar_env"):
                _criar_nova(origem, destino, observacoes, carrinho, enviar=True)

        if st.button("🧹 Limpar", use_container_width=True, key="limpar_carrinho"):
            st.session_state["ibt_carrinho"] = []
            st.rerun()
    else:
        st.info("Carrinho vazio.")


def _criar_nova(origem, destino, observacoes, carrinho, enviar=False):
    with st.spinner("A criar..."):
        ok, resultado = criar_transferencia(origem, destino, "Sistema Web", observacoes)

        if not ok:
            st.error(f"❌ {resultado}")
            return

        trans_id = resultado
        trans = obter_transferencia(trans_id)
        trans_uuid = trans.get("uuid") if trans else ""

        for item in carrinho:
            adicionar_item(
                trans_id, trans_uuid,
                {"id": item["id"], "nome": item["nome"], "codigo_barras": item["codigo"]},
                item["qtd"], item["preco_custo"],
            )

        atualizar_totais(trans_id)

        if enviar:
            ok_env, msg_env = enviar_transferencia(trans_id, "Sistema Web")
            if not ok_env:
                st.warning(f"Criada mas não enviada: {msg_env}")

        st.session_state["ibt_carrinho"] = []
        st.success(f"✅ Criada com sucesso! (ID: {trans_id})")
        st.balloons()
        time.sleep(1.5)
        st.rerun()


# ============================================================
# TAB DASHBOARD
# ============================================================

def _tab_dashboard():
    st.subheader("📊 Dashboard")
    stats = estatisticas_ibt()
    total = sum(stats.values())
    st.markdown(f"### Total: {total} transferências")

    for estado, qtd in stats.items():
        cor = CORES_ESTADO.get(estado, "#94a3b8")
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1: st.markdown(f"**{_badge(estado)}**")
            with c2: st.markdown(f"### {qtd}")

    st.markdown("---")
    st.markdown("### 🚚 Em trânsito")
    em_transito = listar_transferencias(estado=ESTADO_EM_TRANSITO)
    if em_transito:
        for t in em_transito[:20]:
            st.markdown(f"- **{t.get('referencia')}** — {t.get('farmacia_origem_nome')} → {t.get('farmacia_destino_nome')}")
    else:
        st.info("Nenhuma em trânsito.")


# ============================================================
# UTIL
# ============================================================

def _voltar_lista():
    """Limpa estado e volta à lista."""
    for k in ["ibt_modo", "ibt_editar_id", "ibt_receber_id",
              "ibt_detalhes_id", "ibt_cancelar_id", "ibt_carrinho_id"]:
        st.session_state.pop(k, None)
    st.session_state["ibt_carrinho"] = []
    st.session_state["ibt_modo"] = "lista"
    st.rerun()