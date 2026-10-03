"""
Cliente Supabase para Transferências entre Farmácias (IBT).
"""
from datetime import datetime
import uuid as _uuid

from services.supabase_client import _get, _post, _patch, _delete, _get_paginado


# ============================================================
# ESTADOS
# ============================================================
ESTADO_RASCUNHO = "RASCUNHO"
ESTADO_EM_TRANSITO = "EM_TRANSITO"
ESTADO_RECEBIDA_PARCIAL = "RECEBIDA_PARCIAL"
ESTADO_CONCLUIDA = "CONCLUIDA"
ESTADO_CANCELADA = "CANCELADA"
ESTADO_DIVERGENCIA = "DIVERGENCIA"

TODOS_ESTADOS = [
    ESTADO_RASCUNHO,
    ESTADO_EM_TRANSITO,
    ESTADO_RECEBIDA_PARCIAL,
    ESTADO_CONCLUIDA,
    ESTADO_CANCELADA,
    ESTADO_DIVERGENCIA,
]

CORES_ESTADO = {
    ESTADO_RASCUNHO: "#94a3b8",
    ESTADO_EM_TRANSITO: "#fbbf24",
    ESTADO_RECEBIDA_PARCIAL: "#f97316",
    ESTADO_CONCLUIDA: "#10b981",
    ESTADO_CANCELADA: "#ef4444",
    ESTADO_DIVERGENCIA: "#ef4444",
}


# ============================================================
# LISTAR
# ============================================================

def listar_transferencias(estado=None, farmacia_id=None, limite=200):
    """Lista transferências. Se estado=None, mostra activas (não concluídas/canceladas)."""
    params = {
        "select": "*",
        "order": "id.desc",
        "limit": str(limite),
    }

    if estado:
        params["estado"] = f"eq.{estado}"
    elif estado is None and limite == 200:
        # Por defeito: excluir concluídas e canceladas
        params["estado"] = "not.in.(CONCLUIDA,CANCELADA)"

    if farmacia_id:
        params["or"] = f"(farmacia_origem_id.eq.{farmacia_id},farmacia_destino_id.eq.{farmacia_id})"

    return _get("transferencias_filiais", params) or []


def listar_todas_transferencias(farmacia_id=None, limite=500):
    """Lista TODAS (inclui concluídas e canceladas)."""
    params = {
        "select": "*",
        "order": "id.desc",
        "limit": str(limite),
    }
    if farmacia_id:
        params["or"] = f"(farmacia_origem_id.eq.{farmacia_id},farmacia_destino_id.eq.{farmacia_id})"
    return _get("transferencias_filiais", params) or []


def obter_transferencia(trans_id):
    """Devolve uma transferência pelo ID."""
    r = _get("transferencias_filiais", {
        "select": "*",
        "id": f"eq.{trans_id}",
        "limit": "1",
    })
    return r[0] if r else None


def listar_itens(trans_id):
    """Lista os itens de uma transferência."""
    return _get("itens_transferencia", {
        "select": "*",
        "transferencia_id": f"eq.{trans_id}",
        "order": "id.asc",
    }) or []


def listar_historico(trans_id):
    """Lista o histórico de uma transferência."""
    return _get("historico_ibt", {
        "select": "*",
        "transferencia_id": f"eq.{trans_id}",
        "order": "id.asc",
    }) or []


def estatisticas_ibt():
    """Conta transferências por estado."""
    stats = {}
    for estado in TODOS_ESTADOS:
        r = _get("transferencias_filiais", {
            "select": "id",
            "estado": f"eq.{estado}",
        })
        stats[estado] = len(r) if r else 0
    return stats


# ============================================================
# CRIAR
# ============================================================

def _gerar_referencia():
    """Gera referência tipo IBT-2026-0006."""
    ano = datetime.now().strftime("%Y")
    r = _get("transferencias_filiais", {
        "select": "referencia",
        "referencia": f"like.IBT-{ano}-%",
        "order": "id.desc",
        "limit": "1",
    })

    if r and r[0].get("referencia"):
        try:
            novo = int(r[0]["referencia"].split("-")[-1]) + 1
        except Exception:
            novo = 1
    else:
        novo = 1

    return f"IBT-{ano}-{novo:04d}"


def criar_transferencia(origem, destino, utilizador_nome, observacoes=""):
    """
    Cria uma transferência em RASCUNHO.
    origem/destino: dict com keys id, codigo, nome
    Devolve (ok, trans_id ou msg_erro)
    """
    try:
        referencia = _gerar_referencia()
        agora = datetime.now().isoformat()
        uid = str(_uuid.uuid4())

        dados = {
            "uuid": uid,
            "referencia": referencia,
            "data_criacao": agora,
            "farmacia_origem_id": origem["id"],
            "farmacia_origem_codigo": origem.get("codigo", ""),
            "farmacia_origem_nome": origem["nome"],
            "farmacia_destino_id": destino["id"],
            "farmacia_destino_codigo": destino.get("codigo", ""),
            "farmacia_destino_nome": destino["nome"],
            "utilizador_criou_nome": utilizador_nome,
            "estado": ESTADO_RASCUNHO,
            "total_itens": 0,
            "total_quantidade": 0,
            "valor_estimado": 0,
            "observacoes": observacoes or "",
            "terminal_id": "WEB",
            "sincronizado": False,
        }

        ok = _post("transferencias_filiais", dados)
        if not ok:
            return False, "Erro ao criar transferência"

        # Buscar o ID criado
        r = _get("transferencias_filiais", {
            "select": "id",
            "uuid": f"eq.{uid}",
            "limit": "1",
        })
        if not r:
            return False, "Transferência criada mas não encontrada"

        trans_id = r[0]["id"]

        registar_historico(
            trans_id, uid, "CRIOU", utilizador_nome,
            None, ESTADO_RASCUNHO,
            f"Transferência {referencia} criada"
        )

        return True, trans_id

    except Exception as e:
        return False, f"Erro: {e}"


def adicionar_item(trans_id, trans_uuid, produto, quantidade, preco_custo):
    """
    Adiciona um produto à transferência.
    produto: dict com id, nome, codigo_barras
    """
    try:
        subtotal = quantidade * (preco_custo or 0)

        dados = {
            "transferencia_id": trans_id,
            "transferencia_uuid": trans_uuid,
            "produto_id": produto["id"],
            "produto_nome": produto.get("nome", ""),
            "codigo_barras": produto.get("codigo_barras", ""),
            "quantidade_enviada": quantidade,
            "quantidade_recebida": 0,
            "diferenca": 0,
            "lote": "",
            "validade": "",
            "preco_custo": float(preco_custo or 0),
            "subtotal": float(subtotal),
            "justificacao": "",
        }

        return _post("itens_transferencia", dados)
    except Exception as e:
        print(f"[IBT] Erro ao adicionar item: {e}")
        return False


def atualizar_totais(trans_id):
    """Recalcula total_itens, total_quantidade e valor_estimado."""
    itens = listar_itens(trans_id)

    n_itens = len(itens)
    total_qtd = sum(i.get("quantidade_enviada", 0) or 0 for i in itens)
    total_valor = sum(i.get("subtotal", 0) or 0 for i in itens)

    return _patch("transferencias_filiais", f"id=eq.{trans_id}", {
        "total_itens": n_itens,
        "total_quantidade": total_qtd,
        "valor_estimado": total_valor,
    })


def registar_historico(trans_id, trans_uuid, acao, utilizador_nome,
                       estado_anterior=None, estado_novo=None, detalhes=""):
    """Regista uma acção no histórico."""
    try:
        dados = {
            "transferencia_id": trans_id,
            "transferencia_uuid": trans_uuid or "",
            "data": datetime.now().isoformat(),
            "acao": acao,
            "utilizador_nome": utilizador_nome,
            "estado_anterior": estado_anterior or "",
            "estado_novo": estado_novo or "",
            "detalhes": detalhes or "",
        }
        return _post("historico_ibt", dados)
    except Exception as e:
        print(f"[IBT] Erro histórico: {e}")
        return False


# ============================================================
# ACÇÕES
# ============================================================

def enviar_transferencia(trans_id, autorizado_por):
    """
    Envia: RASCUNHO → EM_TRANSITO
    Baixa stock na origem.
    """
    trans = obter_transferencia(trans_id)
    if not trans:
        return False, "Transferência não encontrada"

    if trans["estado"] != ESTADO_RASCUNHO:
        return False, f"Estado actual ({trans['estado']}) não permite envio"

    itens = listar_itens(trans_id)
    if not itens:
        return False, "Sem produtos na transferência"

    # Verificar stock (opcional — depende se tens produtos com estoque_atual)
    # Baixar stock na origem
    for item in itens:
        produto_id = item.get("produto_id")
        qtd = item.get("quantidade_enviada", 0)

        if not produto_id or qtd <= 0:
            continue

        # Buscar stock actual
        prod = _get("produtos", {
            "select": "estoque_atual",
            "id": f"eq.{produto_id}",
            "limit": "1",
        })

        if prod:
            estoque_actual = prod[0].get("estoque_atual", 0) or 0
            novo_estoque = estoque_actual - qtd

            _patch("produtos", f"id=eq.{produto_id}", {
                "estoque_atual": novo_estoque,
            })

    # Actualizar estado
    agora = datetime.now().isoformat()
    ok = _patch("transferencias_filiais", f"id=eq.{trans_id}", {
        "estado": ESTADO_EM_TRANSITO,
        "data_envio": agora,
        "autorizado_por": autorizado_por,
        "sincronizado": False,
    })

    if ok:
        registar_historico(
            trans_id, trans.get("uuid"), "ENVIOU", autorizado_por,
            ESTADO_RASCUNHO, ESTADO_EM_TRANSITO,
            f"Autorizado por: {autorizado_por}"
        )

    return ok, "Transferência enviada" if ok else "Erro ao enviar"


def receber_transferencia(trans_id, utilizador_nome, itens_recebidos):
    """
    Recebe: EM_TRANSITO → CONCLUIDA ou DIVERGENCIA
    itens_recebidos: dict {item_id: quantidade_recebida}
    Adiciona stock no destino.
    """
    trans = obter_transferencia(trans_id)
    if not trans:
        return False, "Transferência não encontrada"

    if trans["estado"] != ESTADO_EM_TRANSITO:
        return False, f"Estado actual ({trans['estado']}) não permite recepção"

    tem_divergencia = False

    for item_id, qtd_rec in itens_recebidos.items():
        item = _get("itens_transferencia", {
            "select": "*",
            "id": f"eq.{item_id}",
            "limit": "1",
        })

        if not item:
            continue

        item = item[0]
        qtd_env = item.get("quantidade_enviada", 0) or 0
        produto_id = item.get("produto_id")
        diferenca = qtd_rec - qtd_env

        # Actualizar item
        _patch("itens_transferencia", f"id=eq.{item_id}", {
            "quantidade_recebida": qtd_rec,
            "diferenca": diferenca,
        })

        # Adicionar stock no destino
        if produto_id and qtd_rec > 0:
            prod = _get("produtos", {
                "select": "estoque_atual",
                "id": f"eq.{produto_id}",
                "limit": "1",
            })

            if prod:
                estoque_actual = prod[0].get("estoque_atual", 0) or 0
                novo_estoque = estoque_actual + qtd_rec

                _patch("produtos", f"id=eq.{produto_id}", {
                    "estoque_atual": novo_estoque,
                })

        if diferenca != 0:
            tem_divergencia = True

    novo_estado = ESTADO_DIVERGENCIA if tem_divergencia else ESTADO_CONCLUIDA
    agora = datetime.now().isoformat()

    ok = _patch("transferencias_filiais", f"id=eq.{trans_id}", {
        "estado": novo_estado,
        "data_recepcao": agora,
        "sincronizado": False,
    })

    if ok:
        detalhe = "Recebido com divergência" if tem_divergencia else "Recebido OK"
        registar_historico(
            trans_id, trans.get("uuid"), "RECEBEU", utilizador_nome,
            ESTADO_EM_TRANSITO, novo_estado, detalhe
        )

    return ok, f"Recepção registada ({novo_estado})"


def cancelar_transferencia(trans_id, motivo, utilizador_nome):
    """Cancela (só se não estiver concluída/cancelada)."""
    trans = obter_transferencia(trans_id)
    if not trans:
        return False, "Transferência não encontrada"

    estado = trans["estado"]

    if estado in (ESTADO_CONCLUIDA, ESTADO_CANCELADA):
        return False, f"Estado {estado} não permite cancelamento"

    # Se estava em trânsito, devolver stock à origem
    if estado == ESTADO_EM_TRANSITO:
        for item in listar_itens(trans_id):
            produto_id = item.get("produto_id")
            qtd = item.get("quantidade_enviada", 0)

            if not produto_id or qtd <= 0:
                continue

            prod = _get("produtos", {
                "select": "estoque_atual",
                "id": f"eq.{produto_id}",
                "limit": "1",
            })

            if prod:
                estoque_actual = prod[0].get("estoque_atual", 0) or 0
                _patch("produtos", f"id=eq.{produto_id}", {
                    "estoque_atual": estoque_actual + qtd,
                })

    ok = _patch("transferencias_filiais", f"id=eq.{trans_id}", {
        "estado": ESTADO_CANCELADA,
        "sincronizado": False,
    })

    if ok:
        registar_historico(
            trans_id, trans.get("uuid"), "CANCELOU", utilizador_nome,
            estado, ESTADO_CANCELADA, f"Motivo: {motivo}"
        )

    return ok, "Cancelada" if ok else "Erro ao cancelar"


def eliminar_transferencia(trans_id, utilizador_nome):
    """Elimina um RASCUNHO (junto com itens e histórico)."""
    trans = obter_transferencia(trans_id)
    if not trans:
        return False, "Não encontrada"

    if trans["estado"] != ESTADO_RASCUNHO:
        return False, f"Apenas RASCUNHOS podem ser eliminados (estado: {trans['estado']})"

    # Eliminar itens e histórico
    _delete("itens_transferencia", f"transferencia_id=eq.{trans_id}")
    _delete("historico_ibt", f"transferencia_id=eq.{trans_id}")
    _delete("transferencias_filiais", f"id=eq.{trans_id}")

    return True, f"Transferência {trans['referencia']} eliminada"