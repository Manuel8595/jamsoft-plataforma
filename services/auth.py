"""
Autenticacao e gestao de utilizadores da plataforma.
"""

import requests
import bcrypt
import secrets
from datetime import datetime, timedelta

from services.supabase_client import SUPABASE_URL, SUPABASE_KEY

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


# ============================================================
# HASH DE SENHAS
# ============================================================

def gerar_hash(senha):
    salt = bcrypt.gensalt(rounds=12)
    hash_bytes = bcrypt.hashpw(senha.encode("utf-8"), salt)
    return hash_bytes.decode("utf-8")


def verificar_senha(senha, hash_guardado):
    try:
        return bcrypt.checkpw(
            senha.encode("utf-8"),
            hash_guardado.encode("utf-8"),
        )
    except Exception:
        return False


# ============================================================
# UTILIZADORES
# ============================================================

def obter_utilizador_por_email(email):
    url = f"{SUPABASE_URL}/rest/v1/plataforma_utilizadores"
    params = {"email": f"eq.{email}", "select": "*", "limit": "1"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    if r.status_code == 200 and r.json():
        return r.json()[0]
    return None


def listar_utilizadores():
    url = f"{SUPABASE_URL}/rest/v1/plataforma_utilizadores"
    params = {"select": "*", "order": "id"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []


def registar_utilizador(email, senha, nome):
    senha_hash = gerar_hash(senha)
    url = f"{SUPABASE_URL}/rest/v1/plataforma_utilizadores"
    dados = {
        "email": email,
        "senha_hash": senha_hash,
        "nome": nome,
        "perfil": "ceo",
        "ativo": True,
        "email_verificado": True,
    }
    r = requests.post(url, headers=HEADERS, json=dados, timeout=10)
    return r.status_code in (200, 201)


def autenticar(email, senha):
    user = obter_utilizador_por_email(email)
    if not user:
        return False, None
    
    if not user.get("ativo"):
        return False, {"erro": "inativo"}
    
    if not verificar_senha(senha, user.get("senha_hash", "")):
        return False, None
    
    url = f"{SUPABASE_URL}/rest/v1/plataforma_utilizadores?id=eq.{user['id']}"
    dados = {"ultimo_login": datetime.now().isoformat()}
    requests.patch(url, headers=HEADERS, json=dados, timeout=10)
    
    return True, {
        "id": user["id"],
        "email": user["email"],
        "nome": user["nome"],
        "perfil": user.get("perfil", "ceo"),
    }


def alterar_senha(user_id, senha_antiga, senha_nova):
    user = None
    for u in listar_utilizadores():
        if u["id"] == user_id:
            user = u
            break
    
    if not user:
        return False, "Utilizador nao encontrado"
    
    if not verificar_senha(senha_antiga, user.get("senha_hash", "")):
        return False, "Senha actual incorrecta"
    
    novo_hash = gerar_hash(senha_nova)
    url = f"{SUPABASE_URL}/rest/v1/plataforma_utilizadores?id=eq.{user_id}"
    requests.patch(url, headers=HEADERS, json={"senha_hash": novo_hash}, timeout=10)
    
    return True, "Senha alterada com sucesso"


# ============================================================
# CONVITES
# ============================================================

def gerar_token():
    return secrets.token_urlsafe(24)


def criar_convite(email, nome_sugerido=""):
    token = gerar_token()
    expira = (datetime.now() + timedelta(days=7)).isoformat()
    
    url = f"{SUPABASE_URL}/rest/v1/plataforma_convites"
    dados = {
        "email": email,
        "token": token,
        "nome_sugerido": nome_sugerido,
        "expira_em": expira,
    }
    
    r = requests.post(url, headers=HEADERS, json=dados, timeout=10)
    if r.status_code in (200, 201):
        return token
    return None


def listar_convites():
    url = f"{SUPABASE_URL}/rest/v1/plataforma_convites"
    params = {"select": "*", "order": "id.desc"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []


def obter_convite_por_token(token):
    url = f"{SUPABASE_URL}/rest/v1/plataforma_convites"
    params = {"token": f"eq.{token}", "select": "*", "limit": "1"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    if r.status_code == 200 and r.json():
        return r.json()[0]
    return None


def marcar_convite_usado(convite_id):
    url = f"{SUPABASE_URL}/rest/v1/plataforma_convites?id=eq.{convite_id}"
    requests.patch(url, headers=HEADERS, json={"usado": True}, timeout=10)


def convite_valido(token):
    conv = obter_convite_por_token(token)
    if not conv:
        return False, "Convite nao encontrado"
    
    if conv.get("usado"):
        return False, "Este convite ja foi utilizado"
    
    try:
        expira = datetime.fromisoformat(conv["expira_em"].replace("Z", "+00:00"))
        if datetime.now(expira.tzinfo) > expira:
            return False, "Este convite expirou"
    except Exception:
        pass
    
    return True, conv