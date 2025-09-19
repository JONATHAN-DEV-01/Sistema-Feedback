# banco_de_dados.py
import sqlite3

def conectar():
    """Conecta ao banco de dados e retorna a conexão e o cursor."""
    conn = sqlite3.connect("votacao.db")
    cursor = conn.cursor()
    return conn, cursor

def criar_tabelas(cursor):
    """Cria as tabelas do banco de dados se elas não existirem."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS votos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ciclo_ano INTEGER NOT NULL, ano INTEGER NOT NULL,
            mes INTEGER NOT NULL, votado TEXT NOT NULL, comunicacao INTEGER NOT NULL,
            trabalho_equipe INTEGER NOT NULL, produtividade INTEGER NOT NULL, resolucao INTEGER NOT NULL,
            comprometimento INTEGER NOT NULL, total INTEGER NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS submissao (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ciclo_ano INTEGER NOT NULL, ano INTEGER NOT NULL,
            mes INTEGER NOT NULL, voter_hash TEXT NOT NULL, UNIQUE(ciclo_ano, mes, voter_hash)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE
        )
        """
    )

def contar_colaboradores(cursor):
    """Conta o número de colaboradores no banco."""
    cursor.execute("SELECT COUNT(*) FROM colaboradores")
    return cursor.fetchone()[0]

def inserir_colaboradores_padrao(cursor, conn, usuarios_padrao):
    """Insere la lista de usuários padrão no banco."""
    cursor.executemany("INSERT INTO colaboradores (nome) VALUES (?)", [(nome,) for nome in usuarios_padrao])
    conn.commit()

def carregar_colaboradores(cursor):
    """Retorna uma lista de todos os colaboradores do banco."""
    cursor.execute("SELECT nome FROM colaboradores ORDER BY nome")
    return [row[0] for row in cursor.fetchall()]

def adicionar_colaborador(cursor, conn, nome):
    """Adiciona um novo colaborador. Retorna True se bem-sucedido, False caso contrário."""
    try:
        cursor.execute("INSERT INTO colaboradores (nome) VALUES (?)", (nome.strip(),))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def excluir_colaborador(cursor, conn, nome):
    """Exclui um colaborador do banco."""
    cursor.execute("DELETE FROM colaboradores WHERE nome=?", (nome,))
    conn.commit()

def inserir_submissao(cursor, conn, dados):
    """Insere um registro de submissão de voto."""
    try:
        cursor.execute("INSERT INTO submissao (ciclo_ano, ano, mes, voter_hash) VALUES (?,?,?,?)", dados)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def reverter_submissao(cursor, conn, dados):
    """Remove um registro de submissão de voto."""
    cursor.execute("DELETE FROM submissao WHERE ciclo_ano=? AND ano=? AND mes=? AND voter_hash=?", dados)
    conn.commit()

def inserir_votos(cursor, conn, registros):
    """Insere uma lista de registros de votos."""
    cursor.executemany(
        """
        INSERT INTO votos(ciclo_ano, ano, mes, votado, comunicacao, trabalho_equipe, 
                         produtividade, resolucao, comprometimento, total) 
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        registros
    )
    conn.commit()

def buscar_ranking_mensal(cursor, ciclo, mes):
    """Busca os dados para o ranking mensal."""
    cursor.execute("SELECT votado, SUM(total) as pontos FROM votos WHERE ciclo_ano=? AND mes=? GROUP BY votado ORDER BY pontos DESC", (ciclo, mes))
    return cursor.fetchall()

def buscar_ranking_acumulado(cursor, ciclo):
    """Busca os dados para o ranking acumulado."""
    cursor.execute("SELECT votado, SUM(total) as pontos FROM votos WHERE ciclo_ano=? GROUP BY votado ORDER BY pontos DESC", (ciclo,))
    return cursor.fetchall()