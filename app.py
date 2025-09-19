import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog, Canvas, Frame, Scrollbar
import sqlite3
from datetime import datetime
import csv
import hashlib

# ============================
# CONFIGURAÇÕES
# ============================
USUARIOS = [
    
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
    ("comunicacao", "Comunicação"),
    ("trabalho_equipe", "Trabalho em equipe e humildade"),
    ("produtividade", "Produtividade, agilidade e eficiência"),
    ("resolucao", "Resolução de problemas (proatividade)"),
    ("comprometimento", "Comprometimento e postura profissional"),
]

PONTOS_MIN = 300
PONTOS_MAX = 600
ADMIN_SENHA = "admin123"
ANON_SALT = "um_salt_bem_grande_e_aleatorio_2025"

MESES_NOMES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# ============================
# FUNÇÕES DE DATA / CICLO
# ============================
def ciclo_atual(dt=None):
    if dt is None:
        dt = datetime.now()
    ano = dt.year
    mes = dt.month
    if mes >= 9:
        return ano
    else:
        return ano - 1

# ============================
# BANCO DE DADOS
# ============================
conn = sqlite3.connect("votacao.db")
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS votos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ciclo_ano INTEGER NOT NULL,
        ano INTEGER NOT NULL,
        mes INTEGER NOT NULL,
        votado TEXT NOT NULL,
        comunicacao INTEGER NOT NULL,
        trabalho_equipe INTEGER NOT NULL,
        produtividade INTEGER NOT NULL,
        resolucao INTEGER NOT NULL,
        comprometimento INTEGER NOT NULL,
        total INTEGER NOT NULL
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS submissao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ciclo_ano INTEGER NOT NULL,
        ano INTEGER NOT NULL,
        mes INTEGER NOT NULL,
        voter_hash TEXT NOT NULL,
        UNIQUE(ciclo_ano, mes, voter_hash)
    )
    """
)
conn.commit()

# ============================
# ESTADO GLOBAL
# ============================
usuario_logado = None
entradas = {}

# ============================
# AUXILIARES
# ============================
def mes_atual(): return datetime.now().month
def ano_atual(): return datetime.now().year
def mes_nome(m): return MESES_NOMES.get(m, str(m))

def voter_hash(nome, c_ano, m, a):
    base = f"{nome}|{c_ano}|{m}|{a}|{ANON_SALT}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()

# ============================
# LOGIN
# ============================
def login_usuario():
    global usuario_logado
    nome = entrada_usuario.get().strip()
    if nome in USUARIOS:
        usuario_logado = nome
        abrir_tela_votacao()
    else:
        messagebox.showerror("Erro", "Usuário não encontrado.")

def login_admin():
    senha = entrada_admin.get()
    if senha == ADMIN_SENHA:
        abrir_tela_admin()
    else:
        messagebox.showerror("Erro", "Senha incorreta.")

# ============================
# SALVAR VOTOS
# ============================
def salvar_votos():
    global usuario_logado
    c_ano = ciclo_atual()
    m = mes_atual()
    a = ano_atual()

    vhash = voter_hash(usuario_logado, c_ano, m, a)
    try:
        cursor.execute(
            "INSERT INTO submissao (ciclo_ano, ano, mes, voter_hash) VALUES (?,?,?,?)",
            (c_ano, a, m, vhash)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Você já enviou sua votação neste mês.")
        return

    total_geral = 0
    registros = []

    for nome, campos in entradas.items():
        valores = {}
        subtotal = 0
        for key, _rotulo in CRITERIOS:
            try:
                v = int(campos[key].get())
            except ValueError:
                v = 0
            if v < 0 or v > 10:
                messagebox.showerror("Erro", f"Nota inválida (0-10) para {nome} em {_rotulo}.")
                return
            valores[key] = v
            subtotal += v
        total_geral += subtotal
        registros.append((c_ano, a, m, nome,
                          valores["comunicacao"], valores["trabalho_equipe"], valores["produtividade"],
                          valores["resolucao"], valores["comprometimento"], subtotal))

    if total_geral < PONTOS_MIN or total_geral > PONTOS_MAX:
        cursor.execute("DELETE FROM submissao WHERE ciclo_ano=? AND ano=? AND mes=? AND voter_hash=?",
                       (c_ano, a, m, vhash))
        conn.commit()
        messagebox.showerror("Erro", f"A soma total deve ficar entre {PONTOS_MIN} e {PONTOS_MAX}. (Atual: {total_geral})")
        return

    cursor.executemany(
        """
        INSERT INTO votos(
            ciclo_ano, ano, mes, votado, comunicacao, trabalho_equipe, produtividade, resolucao, comprometimento, total
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        registros
    )
    conn.commit()

    messagebox.showinfo("Sucesso", "Votos registrados com sucesso!")
    voltar_para_login()

# ============================
# TELAS
# ============================
def abrir_tela_votacao():
    global entradas
    limpar_frames()

    # ALTERAÇÃO: Limpa o frame de votação antes de recriar os widgets para evitar duplicação.
    for widget in votacao_frame.winfo_children():
        widget.destroy()

    entradas = {}
    
    votacao_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # --- Títulos ---
    ttk.Label(votacao_frame, text=f"Votação de {mes_nome(mes_atual())}/{ano_atual()}",
              font=("Arial", 18, "bold")).pack(pady=(0, 5))
    ttk.Label(votacao_frame, text=f"Logado como: {usuario_logado}  |  Distribua entre {PONTOS_MIN} e {PONTOS_MAX} pontos",
              bootstyle="secondary").pack(pady=(0, 20))

    # --- Container com Scroll ---
    canvas = Canvas(votacao_frame, borderwidth=0, highlightthickness=0)
    scroll = ttk.Scrollbar(votacao_frame, orient="vertical", command=canvas.yview)
    
    container_frame = ttk.Frame(canvas)

    container_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=container_frame, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)

    area = ttk.Frame(container_frame)
    area.pack(expand=True, padx=80, pady=20, fill='x')

    # --- Configuração do Grid na 'area' ---
    area.columnconfigure(0, weight=3)
    for i in range(1, 6):
        area.columnconfigure(i, weight=2)

    # --- Cabeçalho ---
    headers = [("COLEGA", 200)] + [(c[1].upper(), 180) for c in CRITERIOS]
    for col, (text, wrap_len) in enumerate(headers):
        anchor = "w" if col == 0 else "center"
        header_label = ttk.Label(area, text=text, font=("Arial", 10, "bold"), anchor=anchor, wraplength=wrap_len, justify="center")
        header_label.grid(row=0, column=col, padx=10, pady=5, sticky="ew")
    
    ttk.Separator(area, orient="horizontal").grid(row=1, columnspan=len(headers), pady=10, sticky="ew")

    # --- Linhas de Votação ---
    usuarios_para_votar = [n for n in USUARIOS if n != usuario_logado]
    for i, nome in enumerate(usuarios_para_votar, start=2):
        entradas[nome] = {}
        
        ttk.Label(area, text=nome).grid(row=i, column=0, padx=10, sticky="w")
        
        for j, (key, rot) in enumerate(CRITERIOS, start=1):
            sp = ttk.Spinbox(area, from_=0, to=10, width=8, justify="center")
            sp.delete(0, "end")
            sp.insert(0, "0")
            sp.grid(row=i, column=j, padx=10, pady=10)
            entradas[nome][key] = sp
            
    # --- Botão de Envio ---
    botoes_frame = ttk.Frame(votacao_frame)
    botoes_frame.pack(pady=20)
    ttk.Button(botoes_frame, text="Enviar Votos", command=salvar_votos, bootstyle=SUCCESS, padding=(20, 10)).pack(side='left', padx=5)
    ttk.Button(botoes_frame, text="Voltar para Login", command=voltar_para_login, style='Hover.TButton', padding=(20, 10)).pack(side='left', padx=5)

    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    

# ============================
# ADMIN
# ============================
def abrir_tela_admin():
    limpar_frames()

    # ALTERAÇÃO: Limpa o frame de admin antes de recriar os widgets para evitar duplicação.
    for widget in admin_view_frame.winfo_children():
        widget.destroy()

    admin_view_frame.pack(fill="both", expand=True, padx=16, pady=16)

    agora = datetime.now()
    if agora.month < 2:
        ttk.Label(admin_view_frame, text="Ranking bloqueado até Fevereiro.", font=("Arial", 14, "bold"), bootstyle=DANGER).pack(pady=10)
        ttk.Button(admin_view_frame, text="Voltar para Login", command=voltar_para_login, style='Hover.TButton').pack(pady=6)
        return

    ttk.Label(admin_view_frame, text="Admin - Rankings", font=("Arial", 16, "bold")).pack(pady=6)

    c_ano = ciclo_atual()
    if agora.month < 9:
        c_ano_display = agora.year - 1
        c_ano_proximo = agora.year
    else:
        c_ano_display = agora.year
        c_ano_proximo = agora.year + 1

    seletor = ttk.Frame(admin_view_frame)
    seletor.pack(pady=6)
    ttk.Label(seletor, text=f"Ciclo: Set/{c_ano_display} → Jan/{c_ano_proximo}", font=("Arial", 10)).pack()

    tabs = ttk.Notebook(admin_view_frame, bootstyle=PRIMARY)
    aba_mensal = ttk.Frame(tabs)
    aba_cumul = ttk.Frame(tabs)
    tabs.add(aba_mensal, text="Ranking Mensal")
    tabs.add(aba_cumul, text="Acumulado + Pódio")
    tabs.pack(fill="both", expand=True)

    montar_ranking_mensal(aba_mensal, c_ano)
    montar_ranking_cumulativo(aba_cumul, c_ano)

    ttk.Button(admin_view_frame, text="Voltar para Login", command=voltar_para_login, style='Hover.TButton').pack(pady=8)

def montar_ranking_mensal(container, c_ano):
    for w in container.winfo_children():
        w.destroy()
    meses_ciclo = [9, 10, 11, 12, 1]

    canvas = Canvas(container, borderwidth=0, highlightthickness=0)
    vscroll = Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas_frame = ttk.Frame(canvas)

    canvas_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=canvas_frame, anchor="nw")
    canvas.configure(yscrollcommand=vscroll.set)

    for m in meses_ciclo:
        bloco = ttk.LabelFrame(canvas_frame, text=f"{mes_nome(m)}", bootstyle="info", padding=10)
        bloco.pack(fill="x", padx=10, pady=5)

        cursor.execute(
            """
            SELECT votado, SUM(total) as pontos
            FROM votos
            WHERE ciclo_ano=? AND mes=?
            GROUP BY votado
            ORDER BY pontos DESC
            """,
            (c_ano, m)
        )
        dados = cursor.fetchall()

        if not dados:
            ttk.Label(bloco, text="Sem votos registrados neste mês.", bootstyle="secondary").pack(anchor="w", padx=5, pady=4)
            continue

        tree = ttk.Treeview(bloco, columns=("rank", "nome", "pontos"), show="headings", bootstyle="info")
        tree.heading("rank", text="#", anchor="center")
        tree.heading("nome", text="Colega", anchor="w")
        tree.heading("pontos", text="Pontos", anchor="center")

        tree.column("rank", width=30, anchor="center")
        tree.column("nome", width=500, anchor="w")
        tree.column("pontos", width=80, anchor="center")

        for i, (nome, pts) in enumerate(dados, start=1):
            tree.insert("", "end", values=(i, nome, pts))

        tree.pack(fill="both", expand=True, padx=5, pady=5)

    canvas.pack(side="left", fill="both", expand=True)
    vscroll.pack(side="right", fill="y")


def montar_ranking_cumulativo(container, c_ano):
    for w in container.winfo_children():
        w.destroy()

    ttk.Label(container, text="Acumulado do Ciclo (Set→Jan)", font=("Arial", 12, "bold")).pack(pady=10)

    cursor.execute(
        """
        SELECT votado, SUM(total) as pontos
        FROM votos
        WHERE ciclo_ano=?
        GROUP BY votado
        ORDER BY pontos DESC
        """,
        (c_ano,)
    )
    dados = cursor.fetchall()

    if not dados:
        ttk.Label(container, text="Sem votos registrados neste ciclo.", bootstyle="secondary").pack(pady=6)
        return

    quadro_completo = ttk.LabelFrame(container, text="Ranking Completo", bootstyle="info", padding=10)
    quadro_completo.pack(fill="both", expand=True, padx=10, pady=5)

    tree_completo = ttk.Treeview(quadro_completo, columns=("rank", "nome", "pontos"), show="headings", bootstyle="info")
    tree_completo.heading("rank", text="#", anchor="center")
    tree_completo.heading("nome", text="Colega", anchor="w")
    tree_completo.heading("pontos", text="Pontos", anchor="center")

    tree_completo.column("rank", width=40, anchor="center")
    tree_completo.column("nome", width=500, anchor="w")
    tree_completo.column("pontos", width=100, anchor="center")

    for i, (nome, pts) in enumerate(dados, start=1):
        tree_completo.insert("", "end", values=(i, nome, pts))

    tree_completo.pack(fill="both", expand=True, padx=5, pady=5)

    top3 = dados[:3]
    if top3:
        podium = ttk.LabelFrame(container, text="Pódio (Top 3)", bootstyle="success", padding=10)
        podium.pack(fill="x", padx=10, pady=15)

        tree_podium = ttk.Treeview(podium, columns=("rank", "nome", "pontos"), show="headings", bootstyle="success")
        tree_podium.heading("rank", text="Pos.", anchor="center")
        tree_podium.heading("nome", text="Vencedor", anchor="w")
        tree_podium.heading("pontos", text="Total Pontos", anchor="center")

        tree_podium.column("rank", width=50, anchor="center")
        tree_podium.column("nome", width=500, anchor="w")
        tree_podium.column("pontos", width=120, anchor="center")

        for i, (nome, pts) in enumerate(top3, start=1):
            tag_style = ""
            if i == 1:
                tag_style = "gold"
            elif i == 2:
                tag_style = "silver"
            elif i == 3:
                tag_style = "bronze"
            
            tree_podium.insert("", "end", values=(f"#{i}", nome, pts), tags=(tag_style,))

        tree_podium.tag_configure("gold", background="#FFD700", foreground="black", font=("Arial", 11, "bold"))
        tree_podium.tag_configure("silver", background="#C0C0C0", foreground="black", font=("Arial", 11, "bold"))
        tree_podium.tag_configure("bronze", background="#CD7F32", foreground="black", font=("Arial", 11, "bold"))

        tree_podium.pack(fill="x", padx=5, pady=5)


# ============================
# UTILITÁRIOS
# ============================
def limpar_frames():
    for f in (login_frame, admin_login_frame, votacao_frame, admin_view_frame):
        f.pack_forget()

def voltar_para_login():
    """Limpa os frames e exibe a tela de login novamente."""
    global usuario_logado
    usuario_logado = None
    limpar_frames()
    entrada_usuario.delete(0, 'end')
    entrada_admin.delete(0, 'end')
    login_frame.pack(pady=40)
    admin_login_frame.pack(pady=30)

# ============================
# JANELA PRINCIPAL
# ============================
root = ttk.Window(themename="darkly")
root.title("Sistema de Votação Interna")
root.geometry("1100x700") # Aumentei um pouco a altura para melhor acomodação

# Criando um estilo para o botão de admin na tela de admin
style = ttk.Style()
style.configure('Hover.TButton',
                  background='#212121',
                  foreground='white',
                  font=('Arial', 10),
                  borderwidth=1,
                  relief="raised")
style.map('Hover.TButton',
          background=[('active', '#424242'),
                      ('pressed', '#616161')],
          relief=[('pressed', 'sunken')])

# Estilo para o botão de Usuário
style.configure('LoginUser.TButton',
                  background='#007bff',
                  foreground='black', 
                  font=('Arial', 11, 'bold'),
                  borderwidth=0,
                  relief="flat")
style.map('LoginUser.TButton',
          background=[('active', '#0056b3'),
                      ('pressed', '#004085')],
          foreground=[('active', 'black'),
                      ('pressed', 'black')],
          # CORREÇÃO APLICADA AQUI
          focuscolor=[('!active', '#66afe9')]) 

# Estilo para o botão de Admin
style.configure('LoginAdmin.TButton',
                  background='#ffc107',
                  foreground='black',
                  font=('Arial', 11, 'bold'),
                  borderwidth=0,
                  relief="flat")
style.map('LoginAdmin.TButton',
          background=[('active', '#e0a800'),
                      ('pressed', '#c69500')],
          foreground=[('active', 'black'),
                      ('pressed', 'black')],
          # CORREÇÃO APLICADA AQUI
          focuscolor=[('!active', '#fd7e14')])


# --- Login Usuário ---
login_frame = ttk.Frame(root)
login_frame.pack(pady=40) 

linha1 = ttk.Frame(login_frame); linha1.pack(pady=8)
ttk.Label(linha1, text="Login - Digite seu nome (exato)", font=("Arial", 14)).pack()
entrada_usuario = ttk.Entry(login_frame, width=40, bootstyle="info")
entrada_usuario.pack(pady=8)

ttk.Button(login_frame, text="Entrar como Usuário", command=login_usuario, style='LoginUser.TButton', padding=(15, 8)).pack(pady=10)

# --- Login Admin ---
admin_login_frame = ttk.Frame(root)
admin_login_frame.pack(pady=30) 

ttk.Label(admin_login_frame, text="Admin - Digite a senha", font=("Arial", 12)).pack()
entrada_admin = ttk.Entry(admin_login_frame, show="*", width=30, bootstyle="warning")
entrada_admin.pack(pady=8)

ttk.Button(admin_login_frame, text="Entrar como Admin", command=login_admin, style='LoginAdmin.TButton', padding=(15, 8)).pack(pady=10)

# --- Votação ---
votacao_frame = ttk.Frame(root)

# --- Admin View ---
admin_view_frame = ttk.Frame(root)

root.mainloop()