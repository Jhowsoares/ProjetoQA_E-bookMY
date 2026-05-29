# EduStark — Plataforma de Cursos com E-books

MVP acadêmico em Flask + HTML/CSS/JS para testes de QA.

## Como rodar

```bash
pip install flask
python app.py
# Abrir: http://localhost:5000
```

## Estrutura

```
edustark/
├── app.py                  ← Backend Flask (API + rotas de página)
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html           ← Layout compartilhado (navbar)
│   ├── index.html          ← Home + listagem pública de cursos
│   ├── cadastro.html       ← Formulário de cadastro de usuário
│   ├── login.html          ← Formulário de login
│   ├── dashboard.html      ← Área logada do instrutor
│   └── novo_curso.html     ← Formulário de publicação de curso
└── static/
    ├── css/style.css       ← Estilos completos
    └── js/main.js          ← Scripts utilitários
```

## Endpoints da API

| Método | Rota          | Descrição                       | Auth |
|--------|---------------|---------------------------------|------|
| POST   | /api/cadastro | Cadastrar usuário               | —    |
| POST   | /api/login    | Login                           | —    |
| POST   | /api/logout   | Logout                          | —    |
| GET    | /api/cursos   | Listar todos os cursos          | —    |
| POST   | /api/cursos   | Publicar novo curso             | ✓    |

## Mapeamento Testes de QA → Regras do Sistema

| Teste | Endpoint         | Validação implementada                        | HTTP |
|-------|------------------|-----------------------------------------------|------|
| T1    | POST /api/cadastro | Campos obrigatórios, formato e-mail, senha ≥ 6 | 201 / 400 / 409 |
| T2    | POST /api/login  | Senha incorreta → rejeição                    | 401  |
| T3    | POST /api/login  | E-mail inexistente → rejeição                 | 404  |
| T4a   | POST /api/cursos | Preço negativo → rejeição                     | 400  |
| T4b   | POST /api/cursos | Preço nulo → rejeição                         | 400  |
| T4c   | POST /api/cursos | Dados completos válidos → criação             | 201  |
| T5    | POST /api/cursos | Título vazio → rejeição                       | 400  |
| T6    | POST /api/cursos | E-book vazio → rejeição                       | 400  |
| T7    | POST /api/cursos | E-book > 5000 chars → rejeição com contagem   | 400  |
