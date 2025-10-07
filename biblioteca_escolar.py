import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import os

class SistemaBiblioteca:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Biblioteca Escolar")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Criar banco de dados
        self.criar_banco()
        
        # Criar interface principal
        self.criar_interface()
        
    def criar_banco(self):
        """Cria o banco de dados SQLite com as tabelas necessárias"""
        conn = sqlite3.connect('biblioteca_escolar.db')
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
        self.combo_categoria['values'] = ('Ficção', 'Não-ficção', 'Didático', 'Literatura', 'Ciências', 'História', 'Geografia', 'Matemática', 'Outros')
        self.combo_categoria.grid(row=1, column=3, padx=(10, 0), pady=5)
        
        tk.Label(form_frame, text="Quantidade:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.entry_quantidade = tk.Entry(form_frame, width=10, font=('Arial', 10))
        self.entry_quantidade.grid(row=2, column=1, padx=(10, 0), pady=5)
        
        # Botões
        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=20)
        
        tk.Button(btn_frame, text="Cadastrar Livro", command=self.cadastrar_livro,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Limpar Campos", command=self.limpar_campos_livro,
                 bg='#95a5a6', fg='white', font=('Arial', 10), width=15).pack(side='left', padx=5)
        
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
            self.tree_livros.column(col, width=100)
        
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
    
    def criar_aba_alunos(self):
        """Aba para cadastro e gerenciamento de alunos"""
        frame_alunos = ttk.Frame(self.notebook)
        self.notebook.add(frame_alunos, text="👨‍🎓 Alunos")
        
        # Frame para formulário
        form_frame = tk.LabelFrame(frame_alunos, text="Cadastrar/Editar Aluno", 
                                  font=('Arial', 12, 'bold'), padx=10, pady=10)
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
        self.combo_serie['values'] = ('1º Fundamental', '2º Fundamental', '3º Fundamental', '4º Fundamental', '5º Fundamental', 
                                     '6º Fundamental', '7º Fundamental', '8º Fundamental', '9º Fundamental', 
                                     '1º Médio', '2º Médio', '3º Médio')
        self.combo_serie.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        tk.Label(form_frame, text="Turma:", font=('Arial', 10)).grid(row=1, column=2, sticky='w', padx=(20, 0), pady=5)
        self.entry_turma = tk.Entry(form_frame, width=10, font=('Arial', 10))
        self.entry_turma.grid(row=1, column=3, padx=(10, 0), pady=5)
        
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
        
        # Frame para lista de alunos
        lista_frame = tk.LabelFrame(frame_alunos, text="Lista de Alunos", 
                                   font=('Arial', 12, 'bold'), padx=10, pady=10)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview para alunos
        self.tree_alunos = ttk.Treeview(lista_frame, columns=('ID', 'Nome', 'Matrícula', 'Série', 'Turma', 'Telefone', 'E-mail'), show='headings')
        
        # Configurar colunas
        colunas_alunos = ['ID', 'Nome', 'Matrícula', 'Série', 'Turma', 'Telefone', 'E-mail']
        for col in colunas_alunos:
            self.tree_alunos.heading(col, text=col)
            self.tree_alunos.column(col, width=120)
        
        # Scrollbars
        scroll_y_alunos = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_alunos.yview)
        self.tree_alunos.configure(yscrollcommand=scroll_y_alunos.set)
        
        # Pack da treeview e scrollbar
        self.tree_alunos.pack(side='left', fill='both', expand=True)
        scroll_y_alunos.pack(side='right', fill='y')
        
        # Carregar dados
        self.carregar_alunos()
    
    def criar_aba_emprestimos(self):
        """Aba para gerenciamento de empréstimos"""
        frame_emprestimos = ttk.Frame(self.notebook)
        self.notebook.add(frame_emprestimos, text="📋 Empréstimos")
        
        # Frame para novo empréstimo
        form_frame = tk.LabelFrame(frame_emprestimos, text="Novo Empréstimo", 
                                  font=('Arial', 12, 'bold'), padx=10, pady=10)
        form_frame.pack(fill='x', padx=10, pady=10)
        
        # Seleção de livro
        tk.Label(form_frame, text="Livro:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.combo_livro_emp = ttk.Combobox(form_frame, width=50, font=('Arial', 10))
        self.combo_livro_emp.grid(row=0, column=1, padx=(10, 0), pady=5, columnspan=2)
        
        # Seleção de aluno
        tk.Label(form_frame, text="Aluno:", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.combo_aluno_emp = ttk.Combobox(form_frame, width=50, font=('Arial', 10))
        self.combo_aluno_emp.grid(row=1, column=1, padx=(10, 0), pady=5, columnspan=2)
        
        # Data de devolução
        tk.Label(form_frame, text="Dias para devolução:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.entry_dias_devolucao = tk.Entry(form_frame, width=10, font=('Arial', 10))
        self.entry_dias_devolucao.insert(0, "15")  # Padrão 15 dias
        self.entry_dias_devolucao.grid(row=2, column=1, padx=(10, 0), pady=5)
        
        # Observações
        tk.Label(form_frame, text="Observações:", font=('Arial', 10)).grid(row=3, column=0, sticky='nw', pady=5)
        self.text_observacoes = tk.Text(form_frame, width=50, height=3, font=('Arial', 10))
        self.text_observacoes.grid(row=3, column=1, padx=(10, 0), pady=5, columnspan=2)
        
        # Botões
        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
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
        
        # Configurar colunas
        colunas_emp = ['ID', 'Livro', 'Aluno', 'Data Emp.', 'Prev. Dev.', 'Status']
        for col in colunas_emp:
            self.tree_emprestimos.heading(col, text=col)
            self.tree_emprestimos.column(col, width=120)
        
        # Scrollbars
        scroll_y_emp = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_emprestimos.yview)
        self.tree_emprestimos.configure(yscrollcommand=scroll_y_emp.set)
        
        # Pack da treeview e scrollbar
        self.tree_emprestimos.pack(side='left', fill='both', expand=True)
        scroll_y_emp.pack(side='right', fill='y')
        
        # Botão de devolução
        tk.Button(lista_frame, text="Registrar Devolução", command=self.registrar_devolucao,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), width=20).pack(pady=10)
        
        # Carregar dados
        self.carregar_emprestimos()
        self.atualizar_combos_emprestimo()
    
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
    
    # Métodos para gerenciar livros
    def cadastrar_livro(self):
        """Cadastra um novo livro no banco de dados"""
        if not self.entry_titulo.get() or not self.entry_autor.get():
            messagebox.showerror("Erro", "Título e Autor são obrigatórios!")
            return
        
        try:
            conn = sqlite3.connect('biblioteca_escolar.db')
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
    
    def carregar_livros(self):
        """Carrega a lista de livros na treeview"""
        # Limpar treeview
        for item in self.tree_livros.get_children():
            self.tree_livros.delete(item)
        
        try:
            conn = sqlite3.connect('biblioteca_escolar.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM livros ORDER BY titulo')
            livros = cursor.fetchall()
            conn.close()
            
            for livro in livros:
                self.tree_livros.insert('', 'end', values=livro)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar livros: {e}")
    
    # Métodos para gerenciar alunos
    def cadastrar_aluno(self):
        """Cadastra um novo aluno no banco de dados"""
        if not self.entry_nome_aluno.get() or not self.entry_matricula.get():
            messagebox.showerror("Erro", "Nome e Matrícula são obrigatórios!")
            return
        
        try:
            conn = sqlite3.connect('biblioteca_escolar.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alunos (nome, matricula, serie, turma, telefone, email)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.entry_nome_aluno.get(), self.entry_matricula.get(), 
                  self.combo_serie.get(), self.entry_turma.get(),
                  self.entry_telefone.get(), self.entry_email.get()))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Sucesso", "Aluno cadastrado com sucesso!")
            self.limpar_campos_aluno()
            self.carregar_alunos()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Matrícula já existe no sistema!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar aluno: {e}")
    
    def limpar_campos_aluno(self):
        """Limpa os campos do formulário de alunos"""
        self.entry_nome_aluno.delete(0, tk.END)
        self.entry_matricula.delete(0, tk.END)
        self.combo_serie.set('')
        self.entry_turma.delete(0, tk.END)
        self.entry_telefone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
    
    def carregar_alunos(self):
        """Carrega a lista de alunos na treeview"""
        # Limpar treeview
        for item in self.tree_alunos.get_children():
            self.tree_alunos.delete(item)
        
        try:
            conn = sqlite3.connect('biblioteca_escolar.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM alunos ORDER BY nome')
            alunos = cursor.fetchall()
            conn.close()
            
            for aluno in alunos:
                self.tree_alunos.insert('', 'end', values=aluno)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar alunos: {e}")
    
    # Métodos para gerenciar empréstimos
    def atualizar_combos_emprestimo(self):
        """Atualiza os comboboxes de livros e alunos disponíveis"""
        try:
            conn = sqlite3.connect('biblioteca_escolar.db')
            cursor = conn.cursor()
            
            # Livros disponíveis
            cursor.execute('SELECT id, titulo, autor FROM livros WHERE disponivel > 0')
            livros = cursor.fetchall()
            livros_values = [f"{livro[0]} - {livro[1]} ({livro[2]})" for livro in livros]
            self.combo_livro_emp['values'] = livros_values
            
            # Alunos
            cursor.execute('SELECT id, nome, matricula FROM alunos ORDER BY nome')
            alunos = cursor.fetchall()
            alunos_values = [f"{aluno[0]} - {aluno[1]} ({aluno[2]})" for aluno in alunos]
            self.combo_aluno_emp['values'] = alunos_values
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar listas: {e}")
    
    def registrar_emprestimo(self):
        """Registra um novo empréstimo"""
        if not self.combo_livro_emp.get() or not self.combo_aluno_emp.get():
            messagebox.showerror("Erro", "Selecione um livro e um aluno!")
            return
        
        try:
            # Extrair IDs dos comboboxes
            livro_id = int(self.combo_livro_emp.get().split(' - ')[0])
            aluno_id = int(self.combo_aluno_emp.get().split(' - ')[0])
            dias = int(self.entry_dias_devolucao.get()) if self.entry_dias_devolucao.get() else 15
            
            # Calcular data de devolução
            data_devolucao = datetime.now() + timedelta(days=dias)
            
            conn = sqlite3.connect('biblioteca_escolar.db')
            cursor = conn.cursor()
            
            # Verificar disponibilidade
            cursor.execute('SELECT disponivel FROM livros WHERE id = ?', (livro_id,))
            disponivel = cursor.fetchone()[0]
            
            if disponivel <= 0:
                messagebox.showerror("Erro", "Livro não está disponível!")
                return
            
            # Registrar empréstimo
            cursor.execute('''
                INSERT INTO emprestimos (livro_id, aluno_id, data_devolucao_prevista, observacoes)
                VALUES (?, ?, ?, ?)
            ''', (livro_id, aluno_id, data_devolucao.strftime('%Y-%m-%d'), 
                  self.text_observacoes.get(1.0, tk.END).strip()))
            
            # Atualizar disponibilidade do livro
            cursor.execute('UPDATE livros SET disponivel = disponivel - 1 WHERE id = ?', (livro_id,))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Sucesso", "Empréstimo registrado com sucesso!")
            self.combo_livro_emp.set('')
            self.combo_aluno_emp.set('')
            self.text_observacoes.delete(1.0, tk.END)
            self.carregar_emprestimos()
            self.atualizar_combos_emprestimo()
            
        except ValueError:
            messagebox.showerror("Erro", "Dias para devolução deve ser um número!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar empréstimo: {e}")
    
    def carregar_emprestimos(self):
        """Carrega a lista de empréstimos ativos na treeview"""
        # Limpar treeview
        for item in self.tree_emprestimos.get_children():
            self.tree_emprestimos.delete(item)
        
        try:
            conn = sqlite3.connect('biblioteca_escolar.db')
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
                # Verificar se está atrasado
                data_prev = datetime.strptime(emp[4], '%Y-%m-%d')
                if data_prev < datetime.now():
                    status = "ATRASADO"
                else:
                    status = emp[5]
                
                valores = (emp[0], emp[1][:30], emp[2][:20], emp[3], emp[4], status)
                self.tree_emprestimos.insert('', 'end', values=valores)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar empréstimos: {e}")
    
    def registrar_devolucao(self):
        """Registra a devolução de um livro"""
        selected_item = self.tree_emprestimos.selection()
        if not selected_item:
            messagebox.showerror("Erro", "Selecione um empréstimo para devolver!")
            return
        
        try:
            # Obter ID do empréstimo
            item = self.tree_emprestimos.item(selected_item)
            emprestimo_id = item['values'][0]
            
            conn = sqlite3.connect('biblioteca_escolar.db')
            cursor = conn.cursor()
            
            # Obter dados do empréstimo
            cursor.execute('SELECT livro_id FROM emprestimos WHERE id = ?', (emprestimo_id,))
            livro_id = cursor.fetchone()[0]
            
            # Atualizar empréstimo
            cursor.execute('''
                UPDATE emprestimos 
                SET data_devolucao_real = CURRENT_DATE, status = 'Devolvido'
                WHERE id = ?
            ''', (emprestimo_id,))
            
            # Atualizar disponibilidade do livro
            cursor.execute('UPDATE livros SET disponivel = disponivel + 1 WHERE id = ?', (livro_id,))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Sucesso", "Devolução registrada com sucesso!")
            self.carregar_emprestimos()
            self.atualizar_combos_emprestimo()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar devolução: {e}")
    
    def atualizar_estatisticas(self):
        """Atualiza as estatísticas na aba de relatórios"""
        try:
            conn = sqlite3.connect('biblioteca_escolar.db')
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
    
    def executar(self):
        """Inicia a aplicação"""
        self.root.mainloop()

# Executar o sistema
if __name__ == "__main__":
    sistema = SistemaBiblioteca()
    sistema.executar()
