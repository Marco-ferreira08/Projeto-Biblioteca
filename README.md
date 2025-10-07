# Sistema de Biblioteca Escolar

Um sistema completo para gerenciamento de bibliotecas escolares, desenvolvido em **Python** utilizando **Tkinter** para a interface gráfica e **SQLite** como banco de dados.

O sistema permite cadastrar livros, alunos, registrar empréstimos e devoluções, além de gerar estatísticas rápidas sobre a biblioteca.

---

## Funcionalidades

### Livros
- Cadastro de livros com título, autor, ISBN, categoria e quantidade.
- Edição e atualização de informações.
- Visualização de todos os livros cadastrados com lista detalhada.
- Controle de disponibilidade de cada livro.

### Alunos
- Cadastro de alunos com nome, matrícula, série, turma, telefone e e-mail.
- Visualização da lista de alunos cadastrados.

### Empréstimos
- Registro de empréstimos de livros para alunos.
- Controle de data de devolução prevista.
- Registro de devoluções e atualização automática da disponibilidade do livro.
- Indicação de status do empréstimo (Emprestado, Devolvido ou Atrasado).

### Relatórios e Estatísticas
- Total de livros cadastrados.
- Total de alunos cadastrados.
- Número de empréstimos ativos.
- Quantidade de livros disponíveis.

---

## Tecnologias Utilizadas

- **Python 3.x**
- **Tkinter**: Biblioteca para criação da interface gráfica.
- **SQLite**: Banco de dados leve, integrado ao Python.
- **datetime**: Para gerenciamento de datas de empréstimo e devolução.

---

## Estrutura do Projeto

- `biblioteca_escolar.py` — Código principal do sistema.
- `biblioteca_escolar.db` — Banco de dados SQLite (será criado automaticamente ao executar o sistema).

---

## Instalação e Execução

### Pré-requisitos

- Python 3.x instalado.
- Biblioteca Tkinter (normalmente já vem instalada com Python).

### Passo a passo

1. Clone o repositório ou faça download do arquivo `biblioteca_escolar.py`.
2. Abra o terminal na pasta do projeto.
3. Execute o sistema:

```bash
python biblioteca_escolar.py
