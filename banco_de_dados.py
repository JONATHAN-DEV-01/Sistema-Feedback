# banco_de_dados.py
import sqlite3
import os

def get_caminho_banco_dados():
    """
    Verifica se existe uma pasta para a aplicação em AppData, a cria se necessário,
    e retorna o caminho completo para o arquivo do banco de dados.
    """
    # Nome da pasta que será criada em AppData\Roaming (seja específico)
    NOME_DA_PASTA_APP = "SistemaVotacaoInterna"
    NOME_DO_BANCO = "votacao.db"
    
    # Pega o caminho para a pasta AppData\Roaming do usuário atual
    caminho_appdata = os.getenv('APPDATA')
    
    # Se o caminho não for encontrado (caso de S.O. não-Windows), usa a pasta home
    if not caminho_appdata:
        caminho_appdata = os.path.expanduser("~")

    # Monta o caminho completo para a pasta da sua aplicação
    caminho_da_app = os.path.join(caminho_appdata, NOME_DA_PASTA_APP)
    
    # Cria a pasta se ela ainda não existir.
    os.makedirs(caminho_da_app, exist_ok=True)
    
    # Retorna o caminho completo onde o banco de dados deve estar
    return os.path.join(caminho_da_app, NOME_DO_BANCO)

def conectar():
    """
    Conecta ao banco de dados no caminho correto e retorna a conexão e o cursor.
    Cria o arquivo de banco de dados se ele não existir.
    """
    caminho_banco = get_caminho_banco_dados()
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        print(f"Banco de dados conectado em: {caminho_banco}")
        return conn, cursor
    except sqlite3.Error as e:
        print(f"Erro fatal ao conectar ao banco de dados: {e}")
        # Em uma aplicação real, você poderia mostrar um messagebox de erro aqui e fechar o app
        return None, None

def criar_tabelas(cursor):
    """Cria as tabelas do banco de dados se elas não existirem."""
    if not cursor: return
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

# ... (o resto do arquivo banco_de_dados.py continua exatamente igual) ...

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