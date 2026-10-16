# -*- coding: utf-8 -*-
"""
Serviço de Backup Criptografado — JAM Soft
Puxa dados do Supabase, encripta com AES-256 e guarda em:
- /tmp/ (local, para download imediato)
- Supabase Storage (persistente, bucket 'backups')
"""
import os
import json
import tempfile
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from services.supabase_client import _get_paginado, SUPABASE_URL, SUPABASE_KEY

try:
    import requests
except ImportError:
    requests = None


# ============================================================
# CONFIGURAÇÃO
# ============================================================
PASTA_BACKUP = Path(tempfile.gettempdir()) / "jamsoft_backups"
PASTA_BACKUP.mkdir(parents=True, exist_ok=True)

BUCKET_STORAGE = "backups"
MAX_BACKUPS = 30


# ============================================================
# TABELAS A BACKUPAR
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
    try:
        import streamlit as st
        chave = st.secrets.get("BACKUP_KEY", "")
        if chave:
            return chave.encode()
    except Exception:
        pass

    chave = os.environ.get("BACKUP_KEY", "")
    if chave:
        return chave.encode()

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

    raise ValueError("BACKUP_KEY nao encontrada no secrets.toml")


def _puxar_tabela(nome_tabela):
    """Puxa TODOS os registos de uma tabela (com paginação)."""
    try:
        dados = _get_paginado(nome_tabela, {"select": "*"}) or []
        return dados
    except Exception as e:
        print(f"[Backup] Erro em '{nome_tabela}': {e}")
        return []


def _criar_backup_dict():
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
        print(f"  -> {tabela}: {len(registos)} registos")
    return backup


def _encriptar(dados_dict, chave):
    """Encripta o dicionário com Fernet (AES-256)."""
    fernet = Fernet(chave)
    texto = json.dumps(dados_dict, ensure_ascii=False, default=str)
    return fernet.encrypt(texto.encode("utf-8"))


def _desencriptar(bytes_enc, chave):
    """Desencripta o backup."""
    fernet = Fernet(chave)
    texto = fernet.decrypt(bytes_enc).decode("utf-8")
    return json.loads(texto)


def _upload_storage(nome_ficheiro, bytes_dados):
    """Faz upload para o Supabase Storage (bucket 'backups')."""
    if not requests:
        return False, "requests nao instalado"
    
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_STORAGE}/{nome_ficheiro}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/octet-stream",
        "x-upsert": "true",
    }
    try:
        r = requests.post(url, headers=headers, data=bytes_dados, timeout=30)
        if r.status_code in (200, 201):
            return True, "OK"
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


def _listar_storage():
    """Lista ficheiros no bucket."""
    if not requests:
        return []
    
    url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_STORAGE}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(url, headers=headers, json={
            "prefix": "",
            "limit": 100,
            "sortBy": {"column": "created_at", "order": "desc"},
        }, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def _download_storage(nome_ficheiro):
    """Faz download de um ficheiro do bucket."""
    if not requests:
        return None
    
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_STORAGE}/{nome_ficheiro}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return None


def _apagar_storage(nome_ficheiro):
    """Apaga ficheiro do bucket."""
    if not requests:
        return False
    
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_STORAGE}/{nome_ficheiro}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    try:
        r = requests.delete(url, headers=headers, timeout=15)
        return r.status_code in (200, 204)
    except Exception:
        return False


def _limpar_antigos():
    """Remove backups mais antigos que MAX_BACKUPS (local + Storage)."""
    removidos = 0
    
    # Local
    if PASTA_BACKUP.exists():
        ficheiros = sorted(
            PASTA_BACKUP.glob("backup_*.enc"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for ficheiro in ficheiros[MAX_BACKUPS:]:
            try:
                ficheiro.unlink()
                removidos += 1
            except Exception:
                pass
    
    # Storage
    ficheiros_storage = _listar_storage()
    if len(ficheiros_storage) > MAX_BACKUPS:
        for f in ficheiros_storage[MAX_BACKUPS:]:
            nome = f.get("name", "")
            if nome:
                _apagar_storage(nome)
                removidos += 1
    
    return removidos


def criar_backup():
    """
    Função principal. Cria, encripta e guarda backup local + Storage.
    Devolve (sucesso, mensagem).
    """
    try:
        # 1. Chave
        chave = _obter_chave()

        # 2. Recolher dados
        print("[Backup] A recolher dados...")
        backup_dict = _criar_backup_dict()

        # 3. Encriptar
        bytes_enc = _encriptar(backup_dict, chave)

        # 4. Nome do ficheiro
        agora = datetime.now().strftime("%Y-%m-%d_%Hh%M")
        nome_ficheiro = f"backup_{agora}.enc"

        # 5. Guardar local
        ficheiro_local = PASTA_BACKUP / nome_ficheiro
        with open(ficheiro_local, "wb") as f:
            f.write(bytes_enc)

        # 6. Upload Storage
        storage_ok, storage_msg = _upload_storage(nome_ficheiro, bytes_enc)

        # 7. Limpar antigos
        removidos = _limpar_antigos()

        # 8. Estatísticas
        tamanho_kb = len(bytes_enc) / 1024
        total_registos = sum(
            len(v) if isinstance(v, list) else 0
            for v in backup_dict["dados"].values()
        )
        detalhe_tabelas = "\n".join(
            f"  - {t}: **{len(v) if isinstance(v, list) else 0}** registos"
            for t, v in backup_dict["dados"].items()
        )

        status_storage = "OK" if storage_ok else f"AVISO: {storage_msg}"

        msg = (
            f"Backup criado: **{nome_ficheiro}**\n\n"
            f"- Tamanho: **{tamanho_kb:.1f} KB**\n"
            f"- Total: **{total_registros}** registos em **{len(TABELAS)} tabelas**\n"
            f"- Local: `{PASTA_BACKUP}`\n"
            f"- Storage: **{status_storage}**\n"
            f"- Antigos removidos: **{removidos}**\n\n"
            f"**Por tabela:**\n{detalhe_tabelas}"
        )
        return True, msg

    except Exception as e:
        return False, f"Erro: {e}"


def listar_backups():
    """Lista backups (Storage + local). Devolve lista de dicts."""
    backups = []
    
    # Storage
    for f in _listar_storage():
        nome = f.get("name", "")
        if nome.endswith(".enc"):
            backups.append({
                "nome": nome,
                "origem": "Storage",
                "tamanho": f.get("metadata", {}).get("size", 0),
                "data": f.get("created_at", ""),
            })
    
    # Local (adicionar os que não estão no Storage)
    nomes_storage = {b["nome"] for b in backups}
    if PASTA_BACKUP.exists():
        for f in PASTA_BACKUP.glob("backup_*.enc"):
            if f.name not in nomes_storage:
                backups.append({
                    "nome": f.name,
                    "origem": "Local",
                    "tamanho": f.stat().st_size,
                    "data": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
    
    return sorted(backups, key=lambda b: b.get("data", ""), reverse=True)


def descarregar_backup(nome_ficheiro):
    """Devolve bytes de um backup (tenta Storage, depois local)."""
    # Tentar Storage
    dados = _download_storage(nome_ficheiro)
    if dados:
        return dados
    
    # Tentar local
    ficheiro = PASTA_BACKUP / nome_ficheiro
    if ficheiro.exists():
        with open(ficheiro, "rb") as f:
            return f.read()
    
    return None


def restaurar_backup(nome_ficheiro):
    """Desencripta e devolve o dict do backup (não aplica)."""
    chave = _obter_chave()
    dados = descarregar_backup(nome_ficheiro)
    if not dados:
        return None, "Backup nao encontrado"
    try:
        return _desencriptar(dados, chave), "OK"
    except Exception as e:
        return None, f"Erro a desencriptar: {e}"