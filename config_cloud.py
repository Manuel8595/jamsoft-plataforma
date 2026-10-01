"""Configuração local e privada da sincronização Supabase."""

import os
from pathlib import Path


def _carregar_env_local():
    caminho = Path(__file__).with_name(".env")
    if not caminho.is_file():
        return
    try:
        linhas = caminho.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        nome, valor = linha.split("=", 1)
        nome = nome.strip()
        valor = valor.strip().strip("\"'")
        if nome and nome not in os.environ:
            os.environ[nome] = valor


_carregar_env_local()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()

_VALORES_VERDADEIROS = {"1", "true", "yes", "sim"}

CLOUD_ACCESS_ENABLED = (
    os.environ.get("CLOUD_ACCESS_ENABLED", "false").strip().lower()
    in _VALORES_VERDADEIROS
)

SYNC_ENABLED = (
    CLOUD_ACCESS_ENABLED
    and os.environ.get("SYNC_ENABLED", "false").strip().lower() in _VALORES_VERDADEIROS
    and bool(SUPABASE_URL)
    and bool(SUPABASE_PUBLISHABLE_KEY)
)

try:
    SYNC_TIMEOUT = max(1, int(os.environ.get("SYNC_TIMEOUT", "30")))
except (TypeError, ValueError):
    SYNC_TIMEOUT = 30

try:
    SYNC_MAX_LOTES = max(1, int(os.environ.get("SYNC_MAX_LOTES", "500")))
except (TypeError, ValueError):
    SYNC_MAX_LOTES = 500
