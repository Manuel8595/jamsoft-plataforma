"""
Serviço de Backup Criptografado — JAM Soft
Puxa dados do Supabase, encripta com AES-256 e guarda localmente.
"""
import os
import json
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet
from services.supabase_client import _get_paginado


# ============================================================
# CONFIGURAÇÃO
# ============================================================
PASTA_BACKUP = Path(r"C:\Users\manue\farmacia-app\backups")
MAX_BACKUPS = 30  # mantém os últimos N


# ============================================================
# TABELAS A BACKUPAR (nomes reais do Supabase)
# ============================================================
TABELAS = [
    "farmacias",
    "plataforma_utilizadores",
    "utilizadores",
    "vendas",
    "itens_venda",
    "facturas",
    "produtos",
    "lotes",
    "turnos_caixa",
    "depositos",
    "saldo_farmacia",
    "perdas",
    "metas_farmacia",
    "ajustes_ceo",
    "config_farmacia",
]


def _obter_chave():
    """Lê a chave do secrets.toml (Streamlit ou ficheiro local)."""
    # 1. Tentar Streamlit
    try:
        import streamlit as st
        chave = st.secrets.get("BACKUP_KEY", "")
        if chave:
            return chave.encode()
    except Exception:
        pass

    # 2. Tentar variável de ambiente
    chave = os.environ.get("BACKUP_KEY", "")
    if chave:
        return chave.encode()

    # 3. Ler directamente do secrets.toml
    caminhos = [
        Path(__file__).parent / ".streamlit" / "secrets.toml",
        Path(__file__).parent.parent / ".streamlit" / "secrets.toml",
    ]
    for caminho in caminhos:
        if caminho.exists():
            with open(caminho, "r", encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if linha.startswith("BACKUP_KEY"):
                        partes = linha.split("=", 1)
                        if len(partes) == 2:
                            valor = partes[1].strip().strip('"').strip("'")
                            if valor:
                                return valor.encode()

    raise ValueError(
        "BACKUP_KEY não encontrada. "
        "Verifica se está no .streamlit/secrets.toml"
    )


def _puxar_tabela(nome_tabela):
    """Puxa TODOS os registos de uma tabela (com paginação)."""
    try:
        # _get_paginado já faz paginação automática (1000 por página)
        dados = _get_paginado(nome_tabela, {"select": "*"}) or []
        return dados
    except Exception as e:
        print(f"[Backup] Erro em '{nome_tabela}': {e}")
        return []


def _criar_backup():
    """Cria o JSON completo com todas as tabelas."""
    backup = {
        "meta": {
            "data": datetime.now().isoformat(),
            "versao": "1.0",
            "tabelas": TABELAS,
        },
        "dados": {},
    }

    for tabela in TABELAS:
        registos = _puxar_tabela(tabela)
        backup["dados"][tabela] = registos
        print(f"  → {tabela}: {len(registos)} registos")

    return backup


def _encriptar(dados_dict, chave):
    """Encripta o dicionário com Fernet (AES-256)."""
    fernet = Fernet(chave)
    texto = json.dumps(dados_dict, ensure_ascii=False, default=str)
    bytes_encriptados = fernet.encrypt(texto.encode("utf-8"))
    return bytes_encriptados


def _limpar_antigos():
    """Remove backups mais antigos que MAX_BACKUPS."""
    if not PASTA_BACKUP.exists():
        return 0

    ficheiros = sorted(
        PASTA_BACKUP.glob("backup_*.enc"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    removidos = 0
    for ficheiro in ficheiros[MAX_BACKUPS:]:
        try:
            ficheiro.unlink()
            removidos += 1
        except Exception:
            pass

    return removidos


def criar_backup():
    """
    Função principal. Cria, encripta e guarda o backup.
    Devolve (sucesso, mensagem).
    """
    try:
        # 1. Chave
        chave = _obter_chave()

        # 2. Pasta
        PASTA_BACKUP.mkdir(parents=True, exist_ok=True)

        # 3. Recolher dados
        print("[Backup] A recolher dados...")
        backup = _criar_backup()

        # 4. Encriptar
        bytes_enc = _encriptar(backup, chave)

        # 5. Nome do ficheiro
        agora = datetime.now().strftime("%Y-%m-%d_%Hh%M")
        ficheiro = PASTA_BACKUP / f"backup_{agora}.enc"

        # 6. Guardar
        with open(ficheiro, "wb") as f:
            f.write(bytes_enc)

        # 7. Limpar antigos
        removidos = _limpar_antigos()

        # 8. Estatísticas
        tamanho_kb = len(bytes_enc) / 1024
        total_registos = sum(
            len(v) if isinstance(v, list) else 0
            for v in backup["dados"].values()
        )

        detalhe_tabelas = "\n".join(
            f"  - {t}: **{len(v) if isinstance(v, list) else 0}** registos"
            for t, v in backup["dados"].items()
        )

        msg = (
            f"✅ Backup criado: **{ficheiro.name}**\n\n"
            f"- Tamanho: **{tamanho_kb:.1f} KB**\n"
            f"- Total: **{total_registos}** registos em **{len(TABELAS)} tabelas**\n"
            f"- Local: `{PASTA_BACKUP}`\n"
            f"- Antigos removidos: **{removidos}**\n"
            f"- Backups guardados: **{len(list(PASTA_BACKUP.glob('backup_*.enc')))}/{MAX_BACKUPS}**\n\n"
            f"**Por tabela:**\n{detalhe_tabelas}"
        )
        return True, msg

    except Exception as e:
        return False, f"❌ Erro no backup: {e}"


def restaurar_backup(caminho_ficheiro):
    """
    Lê e desencripta um backup. Devolve o dicionário.
    Só para uso manual/auditoria.
    """
    try:
        chave = _obter_chave()
        fernet = Fernet(chave)

        with open(caminho_ficheiro, "rb") as f:
            bytes_enc = f.read()

        bytes_dec = fernet.decrypt(bytes_enc)
        dados = json.loads(bytes_dec.decode("utf-8"))
        return True, dados

    except Exception as e:
        return False, f"❌ Erro ao restaurar: {e}"


def listar_backups():
    """Lista backups existentes com data e tamanho."""
    if not PASTA_BACKUP.exists():
        return []

    ficheiros = sorted(
        PASTA_BACKUP.glob("backup_*.enc"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    return [
        {
            "nome": f.name,
            "tamanho_kb": f.stat().st_size / 1024,
            "data": datetime.fromtimestamp(f.stat().st_mtime).strftime(
                "%d/%m/%Y %H:%M"
            ),
        }
        for f in ficheiros
    ]

    

def ler_backup_bytes(caminho_ficheiro):
    """
    Lê os bytes de um ficheiro de backup (.enc).
    Usado para o download pelo browser.
    """
    try:
        with open(caminho_ficheiro, "rb") as f:
            return f.read()
    except Exception as e:
        print(f"[Backup] Erro ao ler {caminho_ficheiro}: {e}")
        return None


def ultimo_backup_path():
    """Devolve o Path do backup mais recente, ou None."""
    if not PASTA_BACKUP.exists():
        return None

    ficheiros = sorted(
        PASTA_BACKUP.glob("backup_*.enc"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return ficheiros[0] if ficheiros else None