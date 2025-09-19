# regras_de_negocio.py
import banco_de_dados as bd
from datetime import datetime
import hashlib

# ============================
# CONSTANTES E CONFIGURAÇÕES
# ============================
USUARIOS_PADRAO = [
    
    "Thiago Henrique",
    "Bruno Cassini",
    "Giovani Galindo",
    "Rafael Grecco",
    "Ricardo Toledo",
    "Lucas Lima",
    "Julio Cesar",
    "André Miranda",
    "Rafael Jesuíno",
    "Alexandre Silva",
    "Eliezer Domingos",
    "José Fernando",
    "Claudia Silvia"
]
CRITERIOS = [
    ("comunicacao", "Comunicação"), ("trabalho_equipe", "Trabalho em equipe e humildade"),
    ("produtividade", "Produtividade, agilidade e eficiência"), ("resolucao", "Resolução de problemas (proatividade)"),
    ("comprometimento", "Comprometimento e postura profissional"),
]
PONTOS_MIN = 275
PONTOS_MAX = 550
ADMIN_SENHA = "admin123"
ANON_SALT = "um_salt_bem_grande_e_aleatorio_2025"
MESES_NOMES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# ============================
# LÓGICA PRINCIPAL
# ============================
def ciclo_atual(dt=None):
    if dt is None: dt = datetime.now()
    return dt.year if dt.month >= 9 else dt.year - 1

def voter_hash(nome, c_ano, m, a):
    base = f"{nome}|{c_ano}|{m}|{a}|{ANON_SALT}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()

def processar_envio_votos(conn, cursor, usuario_logado, entradas):
    """Valida e salva os votos, retornando um dicionário com status e mensagem."""
    c_ano = ciclo_atual()
    m = datetime.now().month
    a = datetime.now().year
    vhash = voter_hash(usuario_logado, c_ano, m, a)
    
    if not bd.inserir_submissao(cursor, conn, (c_ano, a, m, vhash)):
        return {"sucesso": False, "mensagem": "Você já enviou sua votação neste mês."}

    total_geral = 0
    registros = []
    
    if not entradas:
        bd.reverter_submissao(cursor, conn, (c_ano, a, m, vhash))
        return {"sucesso": False, "mensagem": "Não há colaboradores para votar."}

    for nome, campos in entradas.items():
        valores, subtotal = {}, 0
        for key, _rotulo in CRITERIOS:
            try: v = int(campos[key].get())
            except (ValueError, TypeError): v = 0
            if not (0 <= v <= 10):
                bd.reverter_submissao(cursor, conn, (c_ano, a, m, vhash))
                return {"sucesso": False, "mensagem": f"Nota inválida (0-10) para {nome} em {_rotulo}."}
            valores[key] = v
            subtotal += v
        total_geral += subtotal
        registros.append((c_ano, a, m, nome, valores["comunicacao"], valores["trabalho_equipe"], valores["produtividade"], valores["resolucao"], valores["comprometimento"], subtotal))

    if not (PONTOS_MIN <= total_geral <= PONTOS_MAX):
        bd.reverter_submissao(cursor, conn, (c_ano, a, m, vhash))
        return {"sucesso": False, "mensagem": f"A soma total deve ficar entre {PONTOS_MIN} e {PONTOS_MAX}. (Atual: {total_geral})"}
        
    bd.inserir_votos(cursor, conn, registros)
    return {"sucesso": True, "mensagem": "Votos registrados com sucesso!"}