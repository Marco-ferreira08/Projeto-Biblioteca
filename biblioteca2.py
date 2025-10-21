# biblioteca_escolar.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import os
import sys

# --- Utilitário: caminho do banco confiável mesmo quando empacotado ---
def get_db_path():
    # Se empacotado com PyInstaller, sys._MEIPASS existe; guardamos o DB ao lado do exe.
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, "biblioteca_escolar.db")

DB_PATH = get_db_path()

class SistemaBiblioteca:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Biblioteca Escolar")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Criar banco de dados (usa DB_PATH)
        self.criar_banco()
        
        # criar variáveis
        self.ultimo_aviso_data = None  # para não notificar repetidamente a mesma data
        
        # Criar interface principal
        self.criar_interface()

        # Checar devoluções do dia imediatamente e periodicamente (a cada 60s)
        self.check_due_today()  # chama e agenda próximas verificações

    def criar_banco(self):
        """Cria o banco de dados SQLite com as tabelas necessárias"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Tabela de livros
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                isbn TEXT UNIQUE,
                categoria TEXT,
                quantidade INTEGER DEFAULT 1,
                disponivel INTEGER DEFAULT 1,
                data_cadastro DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Tabela de alunos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                matricula TEXT UNIQUE NOT NULL,
                serie TEXT,
                turma TEXT,
                telefone TEXT,
                email TEXT,
                data_cadastro DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Tabela de empréstimos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emprestimos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                livro_id INTEGER,
                aluno_id INTEGER,
                data_emprestimo DATE DEFAULT CURRENT_DATE,
                data_devolucao_prevista DATE,
                data_devolucao_real DATE,
                status TEXT DEFAULT 'Emprestado',
                observacoes TEXT,
                FOREIGN KEY (livro_id) REFERENCES livros (id),
                FOREIGN KEY (aluno_id) REFERENCES alunos (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def criar_interface(self):
        """Cria a interface principal com abas"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        title_label = tk.Label(main_frame, text="SISTEMA DE BIBLIOTECA ESCOLAR", 
                              font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Notebook para abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Criar abas
        self.criar_aba_livros()
        self.criar_aba_alunos()
        self.criar_aba_emprestimos()
        self.criar_aba_relatorios()
        self.criar_aba_estudante()

    # ---------------------- ABA ESTUDANTE ----------------------
    def criar_aba_estudante(self):
        """Aba para visualizar estudantes por turma e seus empréstimos"""
        frame_estudante = ttk.Frame(self.notebook)
        self.notebook.add(frame_estudante, text="🧑‍🎓 Estudante")

        # Frame para blocos de turmas
        bloco_frame = tk.LabelFrame(frame_estudante, text="Blocos de Turmas", font=('Arial', 12, 'bold'), padx=10, pady=10)
        bloco_frame.pack(fill='x', padx=10, pady=10)

        # Blocos de turmas
        blocos = {
            "6º Ano": ["601", "602", "603", "604"],
            "7º Ano": ["701", "702", "703", "704"],
            "8º Ano": ["801", "802", "803", "804"],
            "9º Ano": ["901", "902", "903", "904"],
            "1º Médio": ["1001", "1002", "1003", "1004", "1005"],
            "2º Médio": ["2001", "2002", "2003", "2004", "2005"],
            "3º Médio": ["3001", "3002", "3003", "3005"]
        }

        self.selected_turma = tk.StringVar()
        col = 0
        for bloco, turmas in blocos.items():
            bloco_label = tk.Label(bloco_frame, text=bloco, font=('Arial', 10, 'bold'))
            bloco_label.grid(row=0, column=col, padx=10, pady=5)
            for i, turma in enumerate(turmas):
                btn = tk.Radiobutton(
                    bloco_frame, text=turma, variable=self.selected_turma, value=turma,
                    indicatoron=0, width=6, font=('Arial', 10),
                    command=self.carregar_estudantes_turma
                )
                btn.grid(row=i+1, column=col, padx=5, pady=2)
            col += 1

        # Frame para lista de estudantes
        lista_frame = tk.LabelFrame(frame_estudante, text="Estudantes da Turma", font=('Arial', 12, 'bold'), padx=10, pady=10)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree_estudantes = ttk.Treeview(lista_frame, columns=('ID', 'Nome', 'Matrícula', 'Série', 'Telefone', 'E-mail', 'Livro Emprestado'), show='headings')
        colunas = ['ID', 'Nome', 'Matrícula', 'Série', 'Telefone', 'E-mail', 'Livro Emprestado']
        for col in colunas:
            self.tree_estudantes.heading(col, text=col)
            self.tree_estudantes.column(col, width=120 if col != 'Nome' else 180)
        scroll_y = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_estudantes.yview)
        self.tree_estudantes.configure(yscrollcommand=scroll_y.set)
        self.tree_estudantes.pack(side='left', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')

    def carregar_estudantes_turma(self):
        """Carrega estudantes da turma selecionada e mostra empréstimos ativos"""
        turma = self.selected_turma.get()
        for item in self.tree_estudantes.get_children():
            self.tree_estudantes.delete(item)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, matricula, serie, telefone, email
                FROM alunos WHERE turma = ? ORDER BY nome
            ''', (turma,))
            alunos = cursor.fetchall()
            for aluno in alunos:
                cursor.execute('''
                    SELECT l.titulo FROM emprestimos e
                    JOIN livros l ON e.livro_id = l.id
                    WHERE e.aluno_id = ? AND e.status = 'Emprestado'
                ''', (aluno[0],))
                livros = cursor.fetchall()
                livros_str = ', '.join([l[0] for l in livros]) if livros else 'Nenhum'
                valores = aluno + (livros_str,)
                self.tree_estudantes.insert('', 'end', values=valores)
            conn.close()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar estudantes: {e}")

    # ---------------------- ABA LIVROS ----------------------
    def criar_aba_livros(self):
        """Aba para cadastro e gerenciamento de livros"""
        frame_livros = ttk.Frame(self.notebook)
        self.notebook.add(frame_livros, text="📚 Livros")
        
        # Frame para formulário
        form_frame = tk.LabelFrame(frame_livros, text="Cadastrar/Editar Livro", 
                                  font=('Arial', 12, 'bold'), padx=10, pady=10)
        form_frame.pack(fill='x', padx=10, pady=10)
        
        # Campos do formulário
        tk.Label(form_frame, text="Título:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.entry_titulo = tk.Entry(form_frame, width=40, font=('Arial', 10))
        self.entry_titulo.grid(row=0, column=1, padx=(10, 0), pady=5)
        
        tk.Label(form_frame, text="Autor:", font=('Arial', 10)).grid(row=0, column=2, sticky='w', padx=(20, 0), pady=5)
        self.entry_autor = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.entry_autor.grid(row=0, column=3, padx=(10, 0), pady=5)
        
        tk.Label(form_frame, text="ISBN:", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.entry_isbn = tk.Entry(form_frame, width=20, font=('Arial', 10))
        self.entry_isbn.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        tk.Label(form_frame, text="Categoria:", font=('Arial', 10)).grid(row=1, column=2, sticky='w', padx=(20, 0), pady=5)
        self.combo_categoria = ttk.Combobox(form_frame, width=25, font=('Arial', 10))
        self.combo_categoria['values'] = (
            'Romance', 'Conto', 'Poesia', 'Drama', 'Aventura', 'Fantasia', 'Ficção Científica',
            'Mistério', 'Suspense', 'Terror', 'Biografia', 'Autobiografia', 'Infantil',
            'Juvenil', 'Didático', 'Literatura Brasileira', 'Literatura Estrangeira',
            'Clássicos', 'História', 'Ciências', 'Geografia', 'Matemática', 'Religião', 'Outros'
        )
        self.combo_categoria.grid(row=1, column=3, padx=(10, 0), pady=5)
        
        tk.Label(form_frame, text="Quantidade:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.entry_quantidade = tk.Entry(form_frame, width=10, font=('Arial', 10))
        self.entry_quantidade.grid(row=2, column=1, padx=(10, 0), pady=5)
        
        # Botões
        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)
        
        tk.Button(btn_frame, text="Cadastrar Livro", command=self.cadastrar_livro,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Limpar Campos", command=self.limpar_campos_livro,
                 bg='#95a5a6', fg='white', font=('Arial', 10), width=15).pack(side='left', padx=5)

        # Busca por autor (live e Enter)
        search_frame = tk.Frame(form_frame)
        search_frame.grid(row=4, column=0, columnspan=4, pady=(10,0), sticky='w')
        tk.Label(search_frame, text="Buscar por autor disponível:", font=('Arial', 10)).pack(side='left')
        self.entry_busca_autor = tk.Entry(search_frame, width=40, font=('Arial', 10))
        self.entry_busca_autor.pack(side='left', padx=8)
        # Atualiza ao pressionar Enter
        self.entry_busca_autor.bind("<Return>", lambda e: self.buscar_por_autor())
        # Opcional: também atualiza ao digitar
        self.entry_busca_autor.bind("<KeyRelease>", lambda e: self.buscar_por_autor())

        # Frame para lista de livros
        lista_frame = tk.LabelFrame(frame_livros, text="Lista de Livros", 
                                   font=('Arial', 12, 'bold'), padx=10, pady=10)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview para livros
        self.tree_livros = ttk.Treeview(lista_frame, columns=('ID', 'Título', 'Autor', 'ISBN', 'Categoria', 'Quantidade', 'Disponível'), show='headings')
        
        # Configurar colunas
        colunas_livros = ['ID', 'Título', 'Autor', 'ISBN', 'Categoria', 'Quantidade', 'Disponível']
        for col in colunas_livros:
            self.tree_livros.heading(col, text=col)
            self.tree_livros.column(col, width=120 if col != 'Título' else 250)
        
        # Scrollbars
        scroll_y_livros = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_livros.yview)
        scroll_x_livros = ttk.Scrollbar(lista_frame, orient='horizontal', command=self.tree_livros.xview)
        self.tree_livros.configure(yscrollcommand=scroll_y_livros.set, xscrollcommand=scroll_x_livros.set)
        
        # Pack da treeview e scrollbars
        self.tree_livros.pack(side='left', fill='both', expand=True)
        scroll_y_livros.pack(side='right', fill='y')
        scroll_x_livros.pack(side='bottom', fill='x')
        
        # Carregar dados
        self.carregar_livros()

    def buscar_por_autor(self):
        q = self.entry_busca_autor.get().strip()
        # Limpar tree
        for item in self.tree_livros.get_children():
            self.tree_livros.delete(item)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if q == "":
                cursor.execute('SELECT * FROM livros ORDER BY titulo')
            else:
                cursor.execute('SELECT * FROM livros WHERE autor LIKE ? AND disponivel > 0 ORDER BY titulo', ('%'+q+'%',))
            livros = cursor.fetchall()
            conn.close()
            for livro in livros:
                self.tree_livros.insert('', 'end', values=livro)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na busca por autor: {e}")

    # ---------------------- ABA ALUNOS ----------------------
    def criar_aba_alunos(self):
        """Aba para cadastro, edição e gerenciamento de alunos filtrados por turma"""
        frame_alunos = ttk.Frame(self.notebook)
        self.notebook.add(frame_alunos, text="👨‍🎓 Alunos")

        # Frame para seleção de turma
        filtro_frame = tk.LabelFrame(frame_alunos, text="Filtrar por Turma", font=('Arial', 12, 'bold'), padx=10, pady=10)
        filtro_frame.pack(fill='x', padx=10, pady=(10, 0))

        tk.Label(filtro_frame, text="Turma:", font=('Arial', 10)).pack(side='left')
        self.combo_turma_filtro = ttk.Combobox(filtro_frame, width=15, font=('Arial', 10))
        self.combo_turma_filtro.pack(side='left', padx=8)
        # Ao selecionar turma, filtra alunos
        self.combo_turma_filtro.bind("<<ComboboxSelected>>", lambda e: self.carregar_alunos())
        tk.Button(filtro_frame, text="Atualizar Turmas", command=self.atualizar_lista_turmas, bg='#f39c12', fg='white', font=('Arial', 9)).pack(side='left', padx=8)
        tk.Button(filtro_frame, text="Limpar Filtro", command=self.limpar_filtro_turma, bg='#95a5a6', fg='white', font=('Arial', 9)).pack(side='left', padx=8)

        # Frame para formulário
        form_frame = tk.LabelFrame(frame_alunos, text="Cadastrar/Editar Aluno", font=('Arial', 12, 'bold'), padx=10, pady=10)
        form_frame.pack(fill='x', padx=10, pady=10)

        # Campos do formulário
        tk.Label(form_frame, text="Nome:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.entry_nome_aluno = tk.Entry(form_frame, width=40, font=('Arial', 10))
        self.entry_nome_aluno.grid(row=0, column=1, padx=(10, 0), pady=5)

        tk.Label(form_frame, text="Matrícula:", font=('Arial', 10)).grid(row=0, column=2, sticky='w', padx=(20, 0), pady=5)
        self.entry_matricula = tk.Entry(form_frame, width=20, font=('Arial', 10))
        self.entry_matricula.grid(row=0, column=3, padx=(10, 0), pady=5)

        tk.Label(form_frame, text="Série:", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.combo_serie = ttk.Combobox(form_frame, width=15, font=('Arial', 10))
        self.combo_serie['values'] = (
            '6º Fundamental', '7º Fundamental', '8º Fundamental', '9º Fundamental',
            '1º Médio', '2º Médio', '3º Médio'
        )
        self.combo_serie.grid(row=1, column=1, padx=(10, 0), pady=5)

        tk.Label(form_frame, text="Turma:", font=('Arial', 10)).grid(row=1, column=2, sticky='w', padx=(20, 0), pady=5)
        self.combo_turma_aluno = ttk.Combobox(form_frame, width=15, font=('Arial', 10))
        self.combo_turma_aluno.grid(row=1, column=3, padx=(10, 0), pady=5)
        self.atualizar_lista_turmas()

        tk.Label(form_frame, text="Telefone:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.entry_telefone = tk.Entry(form_frame, width=20, font=('Arial', 10))
        self.entry_telefone.grid(row=2, column=1, padx=(10, 0), pady=5)

        tk.Label(form_frame, text="E-mail:", font=('Arial', 10)).grid(row=2, column=2, sticky='w', padx=(20, 0), pady=5)
        self.entry_email = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.entry_email.grid(row=2, column=3, padx=(10, 0), pady=5)

        # Botões
        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=20)

        tk.Button(btn_frame, text="Cadastrar Aluno", command=self.cadastrar_aluno,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Limpar Campos", command=self.limpar_campos_aluno,
                 bg='#95a5a6', fg='white', font=('Arial', 10), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Salvar Edição", command=self.salvar_edicao_aluno,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), width=15).pack(side='left', padx=5)

        # Frame para lista de alunos
        lista_frame = tk.LabelFrame(frame_alunos, text="Lista de Alunos", font=('Arial', 12, 'bold'), padx=10, pady=10)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Treeview para alunos
        self.tree_alunos = ttk.Treeview(lista_frame, columns=('ID', 'Nome', 'Matrícula', 'Série', 'Turma', 'Telefone', 'E-mail'), show='headings')
        colunas_alunos = ['ID', 'Nome', 'Matrícula', 'Série', 'Turma', 'Telefone', 'E-mail']
        for col in colunas_alunos:
            self.tree_alunos.heading(col, text=col)
            self.tree_alunos.column(col, width=140 if col == 'Nome' else 100)

        scroll_y_alunos = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_alunos.yview)
        self.tree_alunos.configure(yscrollcommand=scroll_y_alunos.set)
        self.tree_alunos.pack(side='left', fill='both', expand=True)
        scroll_y_alunos.pack(side='right', fill='y')

        # Seleção para edição
        self.tree_alunos.bind("<<TreeviewSelect>>", self.preencher_campos_edicao_aluno)

        # Carregar dados
        self.carregar_alunos()

    def atualizar_lista_turmas(self):
        """Povoar combobox de turmas a partir do banco"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT turma FROM alunos WHERE turma IS NOT NULL AND turma <> ""')
            turmas_db = [t[0] for t in cursor.fetchall()]
            conn.close()
            # Turmas padrão corrigidas
            turmas_padrao = [
                "601", "602", "603", "604",
                "701", "702", "703", "704",
                "801", "802", "803", "804",
                "901", "902", "903", "904",
                "1001", "1002", "1003", "1004", "1005",
                "2001", "2002", "2003", "2004", "2005",
                "3001", "3002", "3003", "3005"
            ]
            turmas = sorted(set(turmas_db + turmas_padrao), key=lambda x: (len(x), x))
            self.combo_turma_aluno['values'] = turmas
            self.combo_turma_filtro['values'] = turmas
        except Exception:
            pass

    def limpar_filtro_turma(self):
        """Limpa filtro de turma e mostra todos os alunos"""
        self.combo_turma_filtro.set('')
        self.carregar_alunos()

    def carregar_alunos(self):
        """Carrega a lista de alunos na treeview, filtrando por turma se selecionada"""
        for item in self.tree_alunos.get_children():
            self.tree_alunos.delete(item)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            turma = self.combo_turma_filtro.get().strip()
            if turma:
                cursor.execute('SELECT * FROM alunos WHERE turma = ? ORDER BY nome', (turma,))
            else:
                cursor.execute('SELECT * FROM alunos ORDER BY nome')
            alunos = cursor.fetchall()
            conn.close()
            for aluno in alunos:
                self.tree_alunos.insert('', 'end', values=aluno)
            self.atualizar_lista_turmas()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar alunos: {e}")

    def preencher_campos_edicao_aluno(self, event):
        """Preenche os campos do formulário com os dados do aluno selecionado para edição"""
        selected = self.tree_alunos.selection()
        if not selected:
            return
        item = self.tree_alunos.item(selected)
        valores = item['values']
        self.entry_nome_aluno.delete(0, tk.END)
        self.entry_nome_aluno.insert(0, valores[1])
        self.entry_matricula.delete(0, tk.END)
        self.entry_matricula.insert(0, valores[2])
        self.combo_serie.set(valores[3])
        self.combo_turma_aluno.set(valores[4])
        self.entry_telefone.delete(0, tk.END)
        self.entry_telefone.insert(0, valores[5])
        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, valores[6])
        self.aluno_editando_id = valores[0]

    def salvar_edicao_aluno(self):
        """Salva as alterações do aluno editado"""
        if not hasattr(self, 'aluno_editando_id') or not self.aluno_editando_id:
            messagebox.showerror("Erro", "Selecione um aluno para editar!")
            return
        if not self.entry_nome_aluno.get() or not self.entry_matricula.get():
            messagebox.showerror("Erro", "Nome e Matrícula são obrigatórios!")
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alunos SET nome=?, matricula=?, serie=?, turma=?, telefone=?, email=?
                WHERE id=?
            ''', (
                self.entry_nome_aluno.get(), self.entry_matricula.get(),
                self.combo_serie.get(), self.combo_turma_aluno.get(),
                self.entry_telefone.get(), self.entry_email.get(),
                self.aluno_editando_id
            ))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Dados do aluno atualizados!")
            self.limpar_campos_aluno()
            self.carregar_alunos()
            self.atualizar_combos_emprestimo()
            self.aluno_editando_id = None
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Matrícula já existe no sistema!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao editar aluno: {e}")

    def limpar_campos_aluno(self):
        """Limpa os campos do formulário de alunos"""
        self.entry_nome_aluno.delete(0, tk.END)
        self.entry_matricula.delete(0, tk.END)
        self.combo_serie.set('')
        self.combo_turma_aluno.set('')
        self.entry_telefone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.aluno_editando_id = None

    # ---------------------- ABA EMPRÉSTIMOS ----------------------
    def criar_aba_emprestimos(self):
        """Aba para gerenciamento de empréstimos"""
        frame_emprestimos = ttk.Frame(self.notebook)
        self.notebook.add(frame_emprestimos, text="📋 Empréstimos")
        
        # Frame para novo empréstimo
        form_frame = tk.LabelFrame(frame_emprestimos, text="Novo Empréstimo", 
                                  font=('Arial', 12, 'bold'), padx=10, pady=10)
        form_frame.pack(fill='x', padx=10, pady=10)
        
        # Seleção de turma (novo)
        tk.Label(form_frame, text="Turma:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.combo_turma_emp = ttk.Combobox(form_frame, width=30, font=('Arial', 10))
        self.combo_turma_emp.grid(row=0, column=1, padx=(10, 0), pady=5)
        self.combo_turma_emp.bind("<<ComboboxSelected>>", lambda e: self.atualizar_alunos_por_turma())
        tk.Button(form_frame, text="Atualizar Turmas", command=self.atualizar_lista_turmas_emp, 
                  bg='#f39c12', fg='white', font=('Arial', 9)).grid(row=0, column=2, padx=10)

        # Seleção de livro com autocomplete
        tk.Label(form_frame, text="Livro:", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.entry_livro_emp = tk.Entry(form_frame, width=60, font=('Arial', 10))
        self.entry_livro_emp.grid(row=1, column=1, padx=(10, 0), pady=5, columnspan=2)
        self.listbox_livro_sugestoes = tk.Listbox(form_frame, width=60, font=('Arial', 10), height=5)
        self.listbox_livro_sugestoes.grid(row=2, column=1, padx=(10, 0), pady=(0,5), columnspan=2)
        self.listbox_livro_sugestoes.grid_remove()  # Esconde inicialmente

        self.entry_livro_emp.bind("<KeyRelease>", self.autocomplete_livro)
        self.listbox_livro_sugestoes.bind("<<ListboxSelect>>", self.selecionar_livro_sugestao)

        # Seleção de aluno
        tk.Label(form_frame, text="Aluno:", font=('Arial', 10)).grid(row=3, column=0, sticky='w', pady=5)
        self.combo_aluno_emp = ttk.Combobox(form_frame, width=60, font=('Arial', 10))
        self.combo_aluno_emp.grid(row=3, column=1, padx=(10, 0), pady=5, columnspan=2)
        
        # Data de devolução
        tk.Label(form_frame, text="Dias para devolução:", font=('Arial', 10)).grid(row=4, column=0, sticky='w', pady=5)
        self.entry_dias_devolucao = tk.Entry(form_frame, width=10, font=('Arial', 10))
        self.entry_dias_devolucao.insert(0, "15")  # Padrão 15 dias
        self.entry_dias_devolucao.grid(row=4, column=1, padx=(10, 0), pady=5)
        
        # Observações
        tk.Label(form_frame, text="Observações:", font=('Arial', 10)).grid(row=5, column=0, sticky='nw', pady=5)
        self.text_observacoes = tk.Text(form_frame, width=50, height=3, font=('Arial', 10))
        self.text_observacoes.grid(row=5, column=1, padx=(10, 0), pady=5, columnspan=2)
        
        # Botões
        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        tk.Button(btn_frame, text="Registrar Empréstimo", command=self.registrar_emprestimo,
                 bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'), width=18).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Atualizar Listas", command=self.atualizar_combos_emprestimo,
                 bg='#f39c12', fg='white', font=('Arial', 10), width=15).pack(side='left', padx=5)
        
        # Frame para lista de empréstimos
        lista_frame = tk.LabelFrame(frame_emprestimos, text="Empréstimos Ativos", 
                                   font=('Arial', 12, 'bold'), padx=10, pady=10)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview para empréstimos
        self.tree_emprestimos = ttk.Treeview(lista_frame, columns=('ID', 'Livro', 'Aluno', 'Data Emp.', 'Prev. Dev.', 'Status'), show='headings')
        colunas_emp = ['ID', 'Livro', 'Aluno', 'Data Emp.', 'Prev. Dev.', 'Status']
        for col in colunas_emp:
            self.tree_emprestimos.heading(col, text=col)
            self.tree_emprestimos.column(col, width=120)
        scroll_y_emp = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_emprestimos.yview)
        self.tree_emprestimos.configure(yscrollcommand=scroll_y_emp.set)
        self.tree_emprestimos.pack(side='left', fill='both', expand=True)
        scroll_y_emp.pack(side='right', fill='y')
        
        tk.Button(lista_frame, text="Registrar Devolução", command=self.registrar_devolucao,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), width=20).pack(pady=10)
        
        self.carregar_emprestimos()
        self.atualizar_combos_emprestimo()

    def autocomplete_livro(self, event=None):
        """Mostra sugestões de livros conforme o texto digitado"""
        texto = self.entry_livro_emp.get().strip().lower()
        if not texto:
            self.listbox_livro_sugestoes.grid_remove()
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT id, titulo, autor FROM livros WHERE disponivel > 0 AND LOWER(titulo) LIKE ?', ('%' + texto + '%',))
            livros = cursor.fetchall()
            conn.close()
            self.listbox_livro_sugestoes.delete(0, tk.END)
            for livro in livros:
                self.listbox_livro_sugestoes.insert(tk.END, f"{livro[0]} - {livro[1]} ({livro[2]})")
            if livros:
                self.listbox_livro_sugestoes.grid()
            else:
                self.listbox_livro_sugestoes.grid_remove()
        except Exception:
            self.listbox_livro_sugestoes.grid_remove()

    def selecionar_livro_sugestao(self, event=None):
        """Seleciona livro da sugestão e preenche o campo"""
        selection = self.listbox_livro_sugestoes.curselection()
        if selection:
            valor = self.listbox_livro_sugestoes.get(selection[0])
            self.entry_livro_emp.delete(0, tk.END)
            self.entry_livro_emp.insert(0, valor)
            self.listbox_livro_sugestoes.grid_remove()

    def atualizar_lista_turmas_emp(self):
        """Atualiza combobox de turmas na aba de empréstimos"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT turma FROM alunos WHERE turma IS NOT NULL AND turma <> ""')
            turmas = [t[0] for t in cursor.fetchall()]
            conn.close()
            self.combo_turma_emp['values'] = turmas
        except Exception:
            pass

    def atualizar_alunos_por_turma(self):
        """Popula combo de alunos com os alunos da turma selecionada"""
        turma = self.combo_turma_emp.get().strip()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if turma == "":
                cursor.execute('SELECT id, nome, matricula FROM alunos ORDER BY nome')
            else:
                cursor.execute('SELECT id, nome, matricula FROM alunos WHERE turma = ? ORDER BY nome', (turma,))
            alunos = cursor.fetchall()
            conn.close()
            alunos_values = [f"{al[0]} - {al[1]} ({al[2]})" for al in alunos]
            self.combo_aluno_emp['values'] = alunos_values
            if alunos_values:
                self.combo_aluno_emp.set(alunos_values[0])
            else:
                self.combo_aluno_emp.set('')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar alunos por turma: {e}")

    def atualizar_combos_emprestimo(self):
        """Atualiza os comboboxes de alunos disponíveis"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Alunos (todos por padrão)
            cursor.execute('SELECT id, nome, matricula FROM alunos ORDER BY nome')
            alunos = cursor.fetchall()
            alunos_values = [f"{aluno[0]} - {aluno[1]} ({aluno[2]})" for aluno in alunos]
            self.combo_aluno_emp['values'] = alunos_values
            conn.close()
            self.atualizar_lista_turmas_emp()
            self.atualizar_lista_turmas()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar listas: {e}")

    def registrar_emprestimo(self):
        """Registra um novo empréstimo"""
        livro_valor = self.entry_livro_emp.get()
        aluno_valor = self.combo_aluno_emp.get()
        if not livro_valor or not aluno_valor:
            messagebox.showerror("Erro", "Selecione um livro e um aluno!")
            return
        try:
            # Extrair ID do livro
            livro_id = int(livro_valor.split(' - ')[0])
            aluno_id = int(aluno_valor.split(' - ')[0])
            dias = int(self.entry_dias_devolucao.get()) if self.entry_dias_devolucao.get() else 15
            data_devolucao = datetime.now() + timedelta(days=dias)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT disponivel FROM livros WHERE id = ?', (livro_id,))
            disponivel = cursor.fetchone()[0]
            if disponivel <= 0:
                messagebox.showerror("Erro", "Livro não está disponível!")
                conn.close()
                return
            cursor.execute('''
                INSERT INTO emprestimos (livro_id, aluno_id, data_devolucao_prevista, observacoes)
                VALUES (?, ?, ?, ?)
            ''', (livro_id, aluno_id, data_devolucao.strftime('%Y-%m-%d'), 
                  self.text_observacoes.get(1.0, tk.END).strip()))
            cursor.execute('UPDATE livros SET disponivel = disponivel - 1 WHERE id = ?', (livro_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Empréstimo registrado com sucesso!")
            self.entry_livro_emp.delete(0, tk.END)
            self.combo_aluno_emp.set('')
            self.text_observacoes.delete(1.0, tk.END)
            self.carregar_emprestimos()
            self.atualizar_combos_emprestimo()
        except ValueError:
            messagebox.showerror("Erro", "Dias para devolução deve ser um número!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar empréstimo: {e}")

    # ---------------------- CARREGAR E LISTAR ----------------------
    def carregar_livros(self):
        """Carrega a lista de livros na treeview"""
        for item in self.tree_livros.get_children():
            self.tree_livros.delete(item)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM livros ORDER BY titulo')
            livros = cursor.fetchall()
            conn.close()
            for livro in livros:
                self.tree_livros.insert('', 'end', values=livro)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar livros: {e}")

    def carregar_alunos(self):
        """Carrega a lista de alunos na treeview"""
        for item in self.tree_alunos.get_children():
            self.tree_alunos.delete(item)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM alunos ORDER BY nome')
            alunos = cursor.fetchall()
            conn.close()
            for aluno in alunos:
                self.tree_alunos.insert('', 'end', values=aluno)
            self.atualizar_lista_turmas()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar alunos: {e}")

    def carregar_emprestimos(self):
        """Carrega a lista de empréstimos ativos na treeview"""
        for item in self.tree_emprestimos.get_children():
            self.tree_emprestimos.delete(item)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.id, l.titulo, a.nome, e.data_emprestimo, 
                       e.data_devolucao_prevista, e.status
                FROM emprestimos e
                JOIN livros l ON e.livro_id = l.id
                JOIN alunos a ON e.aluno_id = a.id
                WHERE e.status = 'Emprestado'
                ORDER BY e.data_emprestimo DESC
            ''')
            emprestimos = cursor.fetchall()
            conn.close()
            for emp in emprestimos:
                data_prev = datetime.strptime(emp[4], '%Y-%m-%d')
                if data_prev.date() < datetime.now().date():
                    status = "ATRASADO"
                else:
                    status = emp[5]
                valores = (emp[0], emp[1][:30], emp[2][:20], emp[3], emp[4], status)
                self.tree_emprestimos.insert('', 'end', values=valores)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar empréstimos: {e}")

    # ---------------------- CADASTROS E UTILIDADES ----------------------
    def cadastrar_livro(self):
        """Cadastra um novo livro no banco de dados"""
        if not self.entry_titulo.get() or not self.entry_autor.get():
            messagebox.showerror("Erro", "Título e Autor são obrigatórios!")
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            quantidade = int(self.entry_quantidade.get()) if self.entry_quantidade.get() else 1
            cursor.execute('''
                INSERT INTO livros (titulo, autor, isbn, categoria, quantidade, disponivel)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.entry_titulo.get(), self.entry_autor.get(), self.entry_isbn.get(),
                  self.combo_categoria.get(), quantidade, quantidade))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Livro cadastrado com sucesso!")
            self.limpar_campos_livro()
            self.carregar_livros()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "ISBN já existe no sistema!")
        except ValueError:
            messagebox.showerror("Erro", "Quantidade deve ser um número!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar livro: {e}")

    def limpar_campos_livro(self):
        """Limpa os campos do formulário de livros"""
        self.entry_titulo.delete(0, tk.END)
        self.entry_autor.delete(0, tk.END)
        self.entry_isbn.delete(0, tk.END)
        self.combo_categoria.set('')
        self.entry_quantidade.delete(0, tk.END)

    def cadastrar_aluno(self):
        """Cadastra um novo aluno no banco de dados"""
        if not self.entry_nome_aluno.get() or not self.entry_matricula.get():
            messagebox.showerror("Erro", "Nome e Matrícula são obrigatórios!")
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alunos (nome, matricula, serie, turma, telefone, email)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.entry_nome_aluno.get(), self.entry_matricula.get(), 
                  self.combo_serie.get(), self.combo_turma_aluno.get(),
                  self.entry_telefone.get(), self.entry_email.get()))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Aluno cadastrado com sucesso!")
            self.limpar_campos_aluno()
            self.carregar_alunos()
            self.atualizar_combos_emprestimo()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Matrícula já existe no sistema!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar aluno: {e}")

    def limpar_campos_aluno(self):
        """Limpa os campos do formulário de alunos"""
        self.entry_nome_aluno.delete(0, tk.END)
        self.entry_matricula.delete(0, tk.END)
        self.combo_serie.set('')
        self.combo_turma_aluno.set('')
        self.entry_turma = None
        self.entry_telefone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)

    def registrar_devolucao(self):
        """Registra a devolução de um livro"""
        selected_item = self.tree_emprestimos.selection()
        if not selected_item:
            messagebox.showerror("Erro", "Selecione um empréstimo para devolver!")
            return
        try:
            item = self.tree_emprestimos.item(selected_item)
            emprestimo_id = item['values'][0]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT livro_id FROM emprestimos WHERE id = ?', (emprestimo_id,))
            livro_id = cursor.fetchone()[0]
            cursor.execute('''
                UPDATE emprestimos 
                SET data_devolucao_real = CURRENT_DATE, status = 'Devolvido'
                WHERE id = ?
            ''', (emprestimo_id,))
            cursor.execute('UPDATE livros SET disponivel = disponivel + 1 WHERE id = ?', (livro_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Devolução registrada com sucesso!")
            self.carregar_emprestimos()
            self.atualizar_combos_emprestimo()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar devolução: {e}")

    def renovar_emprestimo(self, event=None):
        """Renova o empréstimo do livro para mais 7 dias"""
        selected_item = self.tree_emprestimos.selection()
        if not selected_item:
            messagebox.showerror("Erro", "Selecione um empréstimo para renovar!")
            return
        try:
            item = self.tree_emprestimos.item(selected_item)
            emprestimo_id = item['values'][0]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Buscar data atual prevista
            cursor.execute('SELECT data_devolucao_prevista FROM emprestimos WHERE id = ?', (emprestimo_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                messagebox.showerror("Erro", "Empréstimo não encontrado!")
                return
            data_prevista = datetime.strptime(row[0], '%Y-%m-%d')
            nova_data = data_prevista + timedelta(days=7)
            cursor.execute('''
                UPDATE emprestimos
                SET data_devolucao_prevista = ?
                WHERE id = ? AND status = 'Emprestado'
            ''', (nova_data.strftime('%Y-%m-%d'), emprestimo_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", f"Empréstimo renovado para {nova_data.strftime('%d/%m/%Y')}!")
            self.carregar_emprestimos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao renovar empréstimo: {e}")

    # Adiciona o duplo clique no nome do aluno para renovar
    def bind_renovar_emprestimo(self):
        """Associa duplo clique na coluna 'Aluno' para renovar empréstimo"""
        def on_double_click(event):
            region = self.tree_emprestimos.identify("region", event.x, event.y)
            col = self.tree_emprestimos.identify_column(event.x)
            # Coluna 3 é 'Aluno'
            if region == "cell" and col == "#3":
                self.renovar_emprestimo()
        self.tree_emprestimos.bind("<Double-1>", on_double_click)

    # Chame bind_renovar_emprestimo após criar a treeview de empréstimos

    # ---------------------- RELATÓRIOS ----------------------
    def criar_aba_relatorios(self):
        """Aba para relatórios e estatísticas"""
        frame_relatorios = ttk.Frame(self.notebook)
        self.notebook.add(frame_relatorios, text="📊 Relatórios")
        
        # Frame para estatísticas rápidas
        stats_frame = tk.LabelFrame(frame_relatorios, text="Estatísticas Rápidas", 
                                   font=('Arial', 12, 'bold'), padx=10, pady=10)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        # Labels para estatísticas
        self.label_total_livros = tk.Label(stats_frame, text="Total de Livros: 0", font=('Arial', 11))
        self.label_total_livros.grid(row=0, column=0, sticky='w', padx=20, pady=5)
        
        self.label_total_alunos = tk.Label(stats_frame, text="Total de Alunos: 0", font=('Arial', 11))
        self.label_total_alunos.grid(row=0, column=1, sticky='w', padx=20, pady=5)
        
        self.label_emprestimos_ativos = tk.Label(stats_frame, text="Empréstimos Ativos: 0", font=('Arial', 11))
        self.label_emprestimos_ativos.grid(row=1, column=0, sticky='w', padx=20, pady=5)
        
        self.label_livros_disponiveis = tk.Label(stats_frame, text="Livros Disponíveis: 0", font=('Arial', 11))
        self.label_livros_disponiveis.grid(row=1, column=1, sticky='w', padx=20, pady=5)
        
        # Botão para atualizar estatísticas
        tk.Button(stats_frame, text="Atualizar Estatísticas", command=self.atualizar_estatisticas,
                 bg='#9b59b6', fg='white', font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Atualizar estatísticas iniciais
        self.atualizar_estatisticas()

    def atualizar_estatisticas(self):
        """Atualiza as estatísticas na aba de relatórios"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Total de livros
            cursor.execute('SELECT COUNT(*) FROM livros')
            total_livros = cursor.fetchone()[0]
            
            # Total de alunos
            cursor.execute('SELECT COUNT(*) FROM alunos')
            total_alunos = cursor.fetchone()[0]
            
            # Empréstimos ativos
            cursor.execute("SELECT COUNT(*) FROM emprestimos WHERE status = 'Emprestado'")
            emprestimos_ativos = cursor.fetchone()[0]
            
            # Livros disponíveis
            cursor.execute('SELECT SUM(disponivel) FROM livros')
            livros_disponiveis = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Atualizar labels
            self.label_total_livros.config(text=f"Total de Livros: {total_livros}")
            self.label_total_alunos.config(text=f"Total de Alunos: {total_alunos}")
            self.label_emprestimos_ativos.config(text=f"Empréstimos Ativos: {emprestimos_ativos}")
            self.label_livros_disponiveis.config(text=f"Livros Disponíveis: {livros_disponiveis}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar estatísticas: {e}")

    # ---------------------- NOTIFICAÇÕES ----------------------
    def check_due_today(self):
        """Verifica empréstimos com devolução prevista para hoje e mostra notificação."""
        try:
            hoje = datetime.now().date()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.id, a.nome, a.matricula, l.titulo, e.data_devolucao_prevista
                FROM emprestimos e
                JOIN alunos a ON e.aluno_id = a.id
                JOIN livros l ON e.livro_id = l.id
                WHERE e.status = 'Emprestado' AND e.data_devolucao_prevista = ?
            ''', (hoje.strftime('%Y-%m-%d'),))
            rows = cursor.fetchall()
            conn.close()

            if rows:
                # evitar notificar repetidamente no mesmo dia
                if self.ultimo_aviso_data != hoje:
                    self.ultimo_aviso_data = hoje
                    self.mostrar_notificacao_devolucoes(rows)
            # Reagendar verificação em 60 segundos (60000 ms)
        except Exception:
            pass
        finally:
            # agenda próxima verificação
            self.root.after(60000, self.check_due_today)

    def mostrar_notificacao_devolucoes(self, rows):
        """Mostra uma janela topmost listando devoluções previstas para hoje."""
        texto = "Devoluções previstas para hoje:\n\n"
        for r in rows:
            texto += f"- {r[1]} (Matrícula: {r[2]}) — {r[3]}\n"
        
        # janela pequena, topmost, não modal
        win = tk.Toplevel(self.root)
        win.title("Lembrete de Devoluções")
        win.attributes('-topmost', True)
        win.geometry("420x220")
        tk.Label(win, text="Lembrete de Devoluções (Hoje)", font=('Arial', 12, 'bold')).pack(pady=8)
        txt = tk.Text(win, width=60, height=8, wrap='word')
        txt.pack(padx=10)
        txt.insert('1.0', texto)
        txt.config(state='disabled')
        btn = tk.Button(win, text="OK", command=win.destroy, bg='#27ae60', fg='white')
        btn.pack(pady=8)

    # ---------------------- EXECUTAR ----------------------
    def executar(self):
        """Inicia a aplicação"""
        self.root.mainloop()

# Executar o sistema
if __name__ == "__main__":
    sistema = SistemaBiblioteca()
    sistema.executar()
