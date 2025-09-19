# app.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Canvas, Frame, Scrollbar
from datetime import datetime

# Importa os outros módulos
import banco_de_dados as bd
import regras_de_negocio as rn

# ============================
# ESTADO GLOBAL DA INTERFACE
# ============================
usuario_logado = None
entradas = {}
LISTA_USUARIOS_DINAMICA = []

# Referências de widgets para atualização
area_votacao = None
admin_novo_usuario_entry = None
admin_usuario_para_excluir_combo = None

# Conexão com o banco de dados
conn, cursor = bd.conectar()

# ============================
# FUNÇÕES DE ATUALIZAÇÃO DA UI
# ============================
def recarregar_tela_admin():
    """Recarrega a lista de usuários e redesenha a tela de Admin por completo."""
    global LISTA_USUARIOS_DINAMICA
    LISTA_USUARIOS_DINAMICA = bd.carregar_colaboradores(cursor)
    abrir_tela_admin()

# ============================
# HANDLERS DE EVENTOS (lógica de clique)
# ============================
def handle_adicionar_usuario(nome, refresh_callback):
    if bd.adicionar_colaborador(cursor, conn, nome):
        messagebox.showinfo("Sucesso", f"'{nome}' foi adicionado com sucesso!")
        refresh_callback()
    else:
        messagebox.showerror("Erro", f"O colaborador '{nome}' já existe.")

def handle_excluir_usuario(nome, refresh_callback):
    if not nome:
        messagebox.showerror("Erro", "Selecione um usuário para excluir.")
        return
    if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{nome}'? Esta ação não pode ser desfeita."):
        bd.excluir_colaborador(cursor, conn, nome)
        messagebox.showinfo("Sucesso", f"'{nome}' foi excluído.")
        refresh_callback()

def login_usuario():
    global usuario_logado
    nome = entrada_usuario.get().strip()
    if nome in LISTA_USUARIOS_DINAMICA:
        usuario_logado = nome
        abrir_tela_votacao()
    else:
        messagebox.showerror("Erro", "Usuário não encontrado.")

def login_admin():
    senha = entrada_admin.get()
    if senha == rn.ADMIN_SENHA:
        abrir_tela_admin()
    else:
        messagebox.showerror("Erro", "Senha incorreta.")

def salvar_votos():
    resultado = rn.processar_envio_votos(conn, cursor, usuario_logado, entradas)
    if resultado["sucesso"]:
        messagebox.showinfo("Sucesso", resultado["mensagem"])
        voltar_para_login()
    else:
        messagebox.showerror("Erro", resultado["mensagem"])

# ============================
# TELAS (código de construção da UI)
# ============================
def abrir_tela_votacao():
    # CORREÇÃO: Limpa o conteúdo do frame de votação antes de redesenhar
    for widget in votacao_frame.winfo_children():
        widget.destroy()
        
    global entradas, area_votacao
    limpar_frames()
    entradas = {}
    votacao_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    ttk.Label(votacao_frame, text=f"Votação de {rn.MESES_NOMES.get(datetime.now().month)}/{datetime.now().year}", font=("Arial", 18, "bold")).pack(pady=(0, 5))
    ttk.Label(votacao_frame, text=f"Logado como: {usuario_logado}  |  Distribua entre {rn.PONTOS_MIN} e {rn.PONTOS_MAX} pontos", bootstyle="secondary").pack(pady=(0, 10))
    
    canvas = Canvas(votacao_frame, borderwidth=0, highlightthickness=0)
    scroll = ttk.Scrollbar(votacao_frame, orient="vertical", command=canvas.yview)
    container_frame = ttk.Frame(canvas)
    container_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=container_frame, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    
    area_votacao = ttk.Frame(container_frame)
    area_votacao.pack(expand=True, padx=80, pady=10, fill='x')
    area_votacao.columnconfigure(0, weight=3)
    for i in range(1, 6): area_votacao.columnconfigure(i, weight=2)
    
    headers = [("COLEGA", 200)] + [(c[1].upper(), 180) for c in rn.CRITERIOS]
    for col, (text, wrap_len) in enumerate(headers):
        anchor = "w" if col == 0 else "center"
        header_label = ttk.Label(area_votacao, text=text, font=("Arial", 10, "bold"), anchor=anchor, wraplength=wrap_len, justify="center")
        header_label.grid(row=0, column=col, padx=10, pady=5, sticky="ew")
    
    ttk.Separator(area_votacao, orient="horizontal").grid(row=1, columnspan=len(headers), pady=10, sticky="ew")
    
    usuarios_para_votar = [n for n in LISTA_USUARIOS_DINAMICA if n != usuario_logado]
    for i, nome in enumerate(usuarios_para_votar, start=2):
        entradas[nome] = {}
        ttk.Label(area_votacao, text=nome).grid(row=i, column=0, padx=10, sticky="w")
        for j, (key, rot) in enumerate(rn.CRITERIOS, start=1):
            sp = ttk.Spinbox(area_votacao, from_=0, to=10, width=8, justify="center")
            sp.delete(0, "end"); sp.insert(0, "0")
            sp.grid(row=i, column=j, padx=10, pady=10)
            entradas[nome][key] = sp
            
    botoes = ttk.Frame(votacao_frame)
    botoes.pack(pady=20)
    ttk.Button(botoes, text="Enviar Votos", command=salvar_votos, bootstyle=SUCCESS, padding=(20, 10)).pack()
    
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

def abrir_tela_admin():
    for widget in admin_view_frame.winfo_children():
        widget.destroy()

    global admin_novo_usuario_entry, admin_usuario_para_excluir_combo
    limpar_frames()
    admin_view_frame.pack(fill="both", expand=True, padx=16, pady=16)
    
    agora = datetime.now()
    ttk.Label(admin_view_frame, text="Admin - Painel de Controle", font=("Arial", 16, "bold")).pack(pady=6)
    
    c_ano = rn.ciclo_atual(agora)
    c_ano_display = agora.year - 1 if agora.month < 9 else agora.year
    c_ano_proximo = c_ano_display + 1
    
    ttk.Label(admin_view_frame, text=f"Ciclo Atual: Set/{c_ano_display} → Jan/{c_ano_proximo}", font=("Arial", 10)).pack()

    tabs = ttk.Notebook(admin_view_frame, bootstyle=PRIMARY)
    aba_mensal = ttk.Frame(tabs)
    aba_cumul = ttk.Frame(tabs)
    aba_colaboradores = ttk.Frame(tabs)
    tabs.add(aba_mensal, text="Ranking Mensal")
    tabs.add(aba_cumul, text="Acumulado + Pódio")
    tabs.add(aba_colaboradores, text="Colaboradores")
    tabs.pack(fill="both", expand=True, pady=10, padx=10)

    montar_ranking_mensal(aba_mensal, c_ano)
    montar_ranking_cumulativo(aba_cumul, c_ano)
    montar_aba_colaboradores(aba_colaboradores)
    
    ttk.Button(admin_view_frame, text="Voltar para Login", command=voltar_para_login, style='Hover.TButton').pack(pady=10)

def montar_aba_colaboradores(container):
    global admin_novo_usuario_entry, admin_usuario_para_excluir_combo
    lista_frame = ttk.LabelFrame(container, text="Colaboradores Atuais", padding=10)
    lista_frame.pack(fill="both", expand=True, padx=10, pady=10)
    tree = ttk.Treeview(lista_frame, columns=("nome"), show="headings")
    tree.heading("nome", text="Nome do Colaborador")
    for nome in LISTA_USUARIOS_DINAMICA:
        tree.insert("", "end", values=(nome,))
    tree.pack(fill="both", expand=True)
    gerenciamento_frame = ttk.LabelFrame(container, text="Ações", padding=15)
    gerenciamento_frame.pack(pady=10, padx=10, fill="x")
    ttk.Label(gerenciamento_frame, text="Novo Colaborador:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    admin_novo_usuario_entry = ttk.Entry(gerenciamento_frame, width=30)
    admin_novo_usuario_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
    ttk.Button(gerenciamento_frame, text="Adicionar", bootstyle="success-outline", command=lambda: handle_adicionar_usuario(admin_novo_usuario_entry.get(), recarregar_tela_admin)).grid(row=0, column=2, padx=10, pady=5)
    ttk.Label(gerenciamento_frame, text="Excluir Colaborador:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    admin_usuario_para_excluir_combo = ttk.Combobox(gerenciamento_frame, values=LISTA_USUARIOS_DINAMICA, state="readonly")
    admin_usuario_para_excluir_combo.grid(row=1, column=1, padx=5, pady=5, sticky="we")
    ttk.Button(gerenciamento_frame, text="Excluir", bootstyle="danger-outline", command=lambda: handle_excluir_usuario(admin_usuario_para_excluir_combo.get(), recarregar_tela_admin)).grid(row=1, column=2, padx=10, pady=5)
    gerenciamento_frame.columnconfigure(1, weight=1)

def montar_ranking_mensal(container, c_ano):
    for w in container.winfo_children(): w.destroy()
    meses_ciclo = [9, 10, 11, 12, 1]
    canvas = Canvas(container, borderwidth=0, highlightthickness=0)
    vscroll = Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas_frame = ttk.Frame(canvas)
    canvas_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=canvas_frame, anchor="nw")
    canvas.configure(yscrollcommand=vscroll.set)
    for m in meses_ciclo:
        bloco = ttk.LabelFrame(canvas_frame, text=f"{rn.MESES_NOMES.get(m)}", bootstyle="info", padding=10)
        bloco.pack(fill="x", padx=10, pady=5)
        dados = bd.buscar_ranking_mensal(cursor, c_ano, m)
        if not dados:
            ttk.Label(bloco, text="Sem votos registrados neste mês.", bootstyle="secondary").pack(anchor="w", padx=5, pady=4)
            continue
        tree = ttk.Treeview(bloco, columns=("rank", "nome", "pontos"), show="headings", bootstyle="info")
        tree.heading("rank", text="#", anchor="center"); tree.heading("nome", text="Colega", anchor="w"); tree.heading("pontos", text="Pontos", anchor="center")
        tree.column("rank", width=30, anchor="center"); tree.column("nome", width=500, anchor="w"); tree.column("pontos", width=80, anchor="center")
        for i, (nome, pts) in enumerate(dados, start=1): tree.insert("", "end", values=(i, nome, pts))
        tree.pack(fill="both", expand=True, padx=5, pady=5)
    canvas.pack(side="left", fill="both", expand=True); vscroll.pack(side="right", fill="y")

def montar_ranking_cumulativo(container, c_ano):
    for w in container.winfo_children(): w.destroy()
    ttk.Label(container, text="Acumulado do Ciclo (Set→Jan)", font=("Arial", 12, "bold")).pack(pady=10)
    dados = bd.buscar_ranking_acumulado(cursor, c_ano)
    if not dados:
        ttk.Label(container, text="Sem votos registrados neste ciclo.", bootstyle="secondary").pack(pady=6)
        return
    quadro_completo = ttk.LabelFrame(container, text="Ranking Completo", bootstyle="info", padding=10)
    quadro_completo.pack(fill="both", expand=True, padx=10, pady=5)
    tree_completo = ttk.Treeview(quadro_completo, columns=("rank", "nome", "pontos"), show="headings", bootstyle="info")
    tree_completo.heading("rank", text="#", anchor="center"); tree_completo.heading("nome", text="Colega", anchor="w"); tree_completo.heading("pontos", text="Pontos", anchor="center")
    tree_completo.column("rank", width=40, anchor="center"); tree_completo.column("nome", width=500, anchor="w"); tree_completo.column("pontos", width=100, anchor="center")
    for i, (nome, pts) in enumerate(dados, start=1): tree_completo.insert("", "end", values=(i, nome, pts))
    tree_completo.pack(fill="both", expand=True, padx=5, pady=5)
    top3 = dados[:3]
    if top3:
        podium = ttk.LabelFrame(container, text="Pódio (Top 3)", bootstyle="success", padding=10)
        podium.pack(fill="x", padx=10, pady=15)
        tree_podium = ttk.Treeview(podium, columns=("rank", "nome", "pontos"), show="headings", bootstyle="success")
        tree_podium.heading("rank", text="Pos.", anchor="center"); tree_podium.heading("nome", text="Vencedor", anchor="w"); tree_podium.heading("pontos", text="Total Pontos", anchor="center")
        tree_podium.column("rank", width=50, anchor="center"); tree_podium.column("nome", width=500, anchor="w"); tree_podium.column("pontos", width=120, anchor="center")
        for i, (nome, pts) in enumerate(top3, start=1):
            tag_style = "gold" if i == 1 else "silver" if i == 2 else "bronze"
            tree_podium.insert("", "end", values=(f"#{i}", nome, pts), tags=(tag_style,))
        tree_podium.tag_configure("gold", background="#FFD700", foreground="black", font=("Arial", 11, "bold"))
        tree_podium.tag_configure("silver", background="#C0C0C0", foreground="black", font=("Arial", 11, "bold"))
        tree_podium.tag_configure("bronze", background="#CD7F32", foreground="black", font=("Arial", 11, "bold"))
        tree_podium.pack(fill="x", padx=5, pady=5)

def limpar_frames():
    for f in (login_frame, admin_login_frame, votacao_frame, admin_view_frame):
        f.pack_forget()

def voltar_para_login():
    global usuario_logado
    usuario_logado = None
    limpar_frames()
    entrada_usuario.delete(0, 'end'); entrada_admin.delete(0, 'end')
    login_frame.pack(pady=40); admin_login_frame.pack(pady=30)

# ============================
# JANELA PRINCIPAL E INICIALIZAÇÃO
# ============================
if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    root.title("Sistema de Votação Interna")
    root.geometry("1100x650")

    bd.criar_tabelas(cursor)
    if bd.contar_colaboradores(cursor) == 0:
        bd.inserir_colaboradores_padrao(cursor, conn, rn.USUARIOS_PADRAO)
    LISTA_USUARIOS_DINAMICA = bd.carregar_colaboradores(cursor)

    style = ttk.Style()
    style.configure('Hover.TButton', background='#212121', foreground='white', font=('Arial', 10), borderwidth=1, relief="raised")
    style.map('Hover.TButton', background=[('active', '#424242'), ('pressed', '#616161')], relief=[('pressed', 'sunken')])
    style.configure('LoginUser.TButton', background='#007bff', foreground='black', font=('Arial', 11, 'bold'), borderwidth=0, relief="flat")
    style.map('LoginUser.TButton', background=[('active', '#0056b3'), ('pressed', '#004085')], foreground=[('active', 'black'), ('pressed', 'black')], focuscolor=[('!active', '#66afe9')]) 
    style.configure('LoginAdmin.TButton', background='#ffc107', foreground='black', font=('Arial', 11, 'bold'), borderwidth=0, relief="flat")
    style.map('LoginAdmin.TButton', background=[('active', '#e0a800'), ('pressed', '#c69500')], foreground=[('active', 'black'), ('pressed', 'black')], focuscolor=[('!active', '#fd7e14')])

    login_frame = ttk.Frame(root); admin_login_frame = ttk.Frame(root); votacao_frame = ttk.Frame(root); admin_view_frame = ttk.Frame(root)
    
    login_frame.pack(pady=40) 
    linha1 = ttk.Frame(login_frame); linha1.pack(pady=8)
    ttk.Label(linha1, text="Login - Digite seu nome (exato)", font=("Arial", 14)).pack()
    entrada_usuario = ttk.Entry(login_frame, width=40, bootstyle="info")
    entrada_usuario.pack(pady=8)
    ttk.Button(login_frame, text="Entrar como Usuário", command=login_usuario, style='LoginUser.TButton', padding=(15, 8)).pack(pady=10)

    admin_login_frame.pack(pady=30) 
    ttk.Label(admin_login_frame, text="Admin - Digite a senha", font=("Arial", 12)).pack()
    entrada_admin = ttk.Entry(admin_login_frame, show="*", width=30, bootstyle="warning")
    entrada_admin.pack(pady=8)
    ttk.Button(admin_login_frame, text="Entrar como Admin", command=login_admin, style='LoginAdmin.TButton', padding=(15, 8)).pack(pady=10)

    root.mainloop()