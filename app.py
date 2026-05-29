from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import re
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'WebEdu-secret-key-2024'

DB_PATH = Path("database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Usuários com campo 'tipo': 'aluno' ou 'criador'
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        email TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL DEFAULT 'aluno'
    )
    """)

    # Cursos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        ebook TEXT NOT NULL,
        criador TEXT NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (criador) REFERENCES usuarios(email)
    )
    """)

    # Comentários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comentarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso_id INTEGER NOT NULL,
        usuario_email TEXT NOT NULL,
        texto TEXT NOT NULL,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (curso_id) REFERENCES cursos(id),
        FOREIGN KEY (usuario_email) REFERENCES usuarios(email)
    )
    """)

    # Avaliações (nota de 1 a 5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso_id INTEGER NOT NULL,
        usuario_email TEXT NOT NULL,
        nota INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(curso_id, usuario_email),
        FOREIGN KEY (curso_id) REFERENCES cursos(id),
        FOREIGN KEY (usuario_email) REFERENCES usuarios(email)
    )
    """)

    # Compras simuladas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_email TEXT NOT NULL,
        curso_id INTEGER NOT NULL,
        data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_email) REFERENCES usuarios(email),
        FOREIGN KEY (curso_id) REFERENCES cursos(id),
        UNIQUE(usuario_email, curso_id)
    )
    """)

    conn.commit()
    conn.close()

# ─── PÁGINAS ──────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro')
def pagina_cadastro():
    return render_template('cadastro.html')

@app.route('/login')
def pagina_login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect('/login')
    return render_template('dashboard.html', usuario=session['usuario'], tipo=session.get('tipo'))

@app.route('/novo-curso')
def pagina_novo_curso():
    if 'usuario' not in session or session.get('tipo') != 'criador':
        return redirect('/dashboard')
    return render_template('novo_curso.html')

@app.route('/curso/<int:curso_id>')
def pagina_curso(curso_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cursos WHERE id = ?", (curso_id,))
    curso = cursor.fetchone()
    if not curso:
        conn.close()
        return "Curso não encontrado", 404
    conn.close()
    return render_template('curso.html', curso=curso)

@app.route('/meus-cursos')
def meus_cursos():
    if 'usuario' not in session:
        return redirect('/login')
    return render_template('meus_cursos.html')

@app.route('/admin')
def admin_view():
    # Rota simples para visualizar dados (apenas para debug)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios_db = cursor.fetchall()
    cursor.execute("SELECT * FROM cursos")
    cursos_db = cursor.fetchall()
    cursor.execute("SELECT * FROM compras")
    compras_db = cursor.fetchall()
    conn.close()
    return render_template('admin.html', usuarios=usuarios_db, cursos=cursos_db, compras=compras_db)

# ─── API: USUÁRIOS ────────────────────────────────────────────

@app.route('/api/cadastro', methods=['POST'])
def cadastrar_usuario():
    dados = request.get_json()
    nome  = (dados.get('nome') or '').strip()
    email = (dados.get('email') or '').strip()
    senha = (dados.get('senha') or '').strip()
    tipo  = (dados.get('tipo') or 'aluno').strip()

    # Validações
    if not nome:
        return jsonify({'erro': 'O nome é obrigatório.'}), 400
    if not email:
        return jsonify({'erro': 'O e-mail é obrigatório.'}), 400
    if not senha:
        return jsonify({'erro': 'A senha é obrigatória.'}), 400
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({'erro': 'Formato de e-mail inválido.'}), 400
    if len(senha) < 6:
        return jsonify({'erro': 'A senha deve ter pelo menos 6 caracteres.'}), 400
    if tipo not in ('aluno', 'criador'):
        return jsonify({'erro': 'Tipo inválido. Escolha "aluno" ou "criador".'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM usuarios WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'erro': 'E-mail já cadastrado.'}), 409

    cursor.execute(
        "INSERT INTO usuarios (email, nome, senha, tipo) VALUES (?, ?, ?, ?)",
        (email, nome, senha, tipo)
    )
    conn.commit()
    conn.close()

    return jsonify({'mensagem': f'Conta {tipo} criada para {nome}!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json()
    email = (dados.get('email') or '').strip()
    senha = (dados.get('senha') or '').strip()

    if not email or not senha:
        return jsonify({'erro': 'E-mail e senha são obrigatórios.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'erro': 'E-mail não encontrado.'}), 404

    if user['senha'] != senha:
        return jsonify({'erro': 'Senha incorreta.'}), 401

    session['usuario'] = email
    session['tipo'] = user['tipo']
    session['nome'] = user['nome']

    return jsonify({'mensagem': 'Login realizado!', 'redirect': '/dashboard'}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensagem': 'Logout realizado.'}), 200

@app.route('/api/usuario', methods=['GET'])
def info_usuario():
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401
    return jsonify({
        'email': session['usuario'],
        'tipo': session.get('tipo'),
        'nome': session.get('nome')
    })

# ─── API: CURSOS ──────────────────────────────────────────────

@app.route('/api/cursos', methods=['GET'])
def listar_cursos():
    # Suporte a pesquisa por título ou descrição
    termo = request.args.get('q', '').strip()
    conn = get_db()
    cursor = conn.cursor()
    if termo:
        cursor.execute("""
            SELECT * FROM cursos
            WHERE titulo LIKE ? OR descricao LIKE ?
            ORDER BY data_criacao DESC
        """, (f'%{termo}%', f'%{termo}%'))
    else:
        cursor.execute("SELECT * FROM cursos ORDER BY data_criacao DESC")
    cursos_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(cursos_list), 200

@app.route('/api/cursos/<int:curso_id>', methods=['GET'])
def obter_curso(curso_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cursos WHERE id = ?", (curso_id,))
    curso = cursor.fetchone()
    if not curso:
        conn.close()
        return jsonify({'erro': 'Curso não encontrado'}), 404
    conn.close()
    return jsonify(dict(curso))

@app.route('/api/cursos', methods=['POST'])
def cadastrar_curso():
    if 'usuario' not in session or session.get('tipo') != 'criador':
        return jsonify({'erro': 'Apenas criadores podem publicar cursos.'}), 403

    dados     = request.get_json()
    titulo    = (dados.get('titulo') or '').strip()
    descricao = (dados.get('descricao') or '').strip()
    preco     = dados.get('preco')
    ebook     = (dados.get('ebook') or '').strip()

    if not titulo:
        return jsonify({'erro': 'O título do curso é obrigatório.'}), 400
    if not ebook:
        return jsonify({'erro': 'O conteúdo do e-book é obrigatório.'}), 400
    if len(ebook) > 5000:
        return jsonify({'erro': f'O e-book excede o limite de 5000 caracteres ({len(ebook)} enviados).'}), 400
    if preco is None or preco == '':
        return jsonify({'erro': 'O preço é obrigatório.'}), 400
    try:
        preco = float(preco)
    except (ValueError, TypeError):
        return jsonify({'erro': 'Preço inválido.'}), 400
    if preco < 0:
        return jsonify({'erro': 'O preço não pode ser negativo.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cursos (titulo, descricao, preco, ebook, criador)
        VALUES (?, ?, ?, ?, ?)
    """, (titulo, descricao, preco, ebook, session['usuario']))
    conn.commit()
    curso_id = cursor.lastrowid
    conn.close()

    return jsonify({'mensagem': f'Curso "{titulo}" publicado!', 'curso_id': curso_id}), 201

# ─── API: COMENTÁRIOS ────────────────────────────────────────

@app.route('/api/cursos/<int:curso_id>/comentarios', methods=['GET'])
def listar_comentarios(curso_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, u.nome FROM comentarios c
        JOIN usuarios u ON c.usuario_email = u.email
        WHERE curso_id = ?
        ORDER BY c.data DESC
    """, (curso_id,))
    comentarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(comentarios)

@app.route('/api/cursos/<int:curso_id>/comentarios', methods=['POST'])
def adicionar_comentario(curso_id):
    if 'usuario' not in session:
        return jsonify({'erro': 'Faça login para comentar.'}), 401

    dados = request.get_json()
    texto = (dados.get('texto') or '').strip()
    if not texto:
        return jsonify({'erro': 'O comentário não pode ser vazio.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cursos WHERE id = ?", (curso_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'erro': 'Curso não encontrado.'}), 404

    cursor.execute("""
        INSERT INTO comentarios (curso_id, usuario_email, texto)
        VALUES (?, ?, ?)
    """, (curso_id, session['usuario'], texto))
    conn.commit()
    comentario_id = cursor.lastrowid
    conn.close()
    return jsonify({'mensagem': 'Comentário adicionado.', 'id': comentario_id}), 201

# ─── API: AVALIAÇÕES ─────────────────────────────────────────

@app.route('/api/cursos/<int:curso_id>/avaliacao', methods=['GET'])
def obter_avaliacao_media(curso_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT AVG(nota) as media, COUNT(*) as total
        FROM avaliacoes WHERE curso_id = ?
    """, (curso_id,))
    row = cursor.fetchone()
    conn.close()
    media = round(row['media'], 1) if row['media'] is not None else 0
    total = row['total'] or 0
    return jsonify({'media': media, 'total': total})

@app.route('/api/cursos/<int:curso_id>/avaliacao', methods=['POST'])
def avaliar_curso(curso_id):
    if 'usuario' not in session:
        return jsonify({'erro': 'Faça login para avaliar.'}), 401

    dados = request.get_json()
    try:
        nota = int(dados.get('nota'))
    except (TypeError, ValueError):
        return jsonify({'erro': 'Nota inválida.'}), 400
    if nota < 1 or nota > 5:
        return jsonify({'erro': 'A nota deve ser entre 1 e 5.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    # Verificar se o usuário já comprou o curso? (opcional) Vou permitir avaliar mesmo sem compra, mas poderia restringir.
    cursor.execute("""
        INSERT INTO avaliacoes (curso_id, usuario_email, nota)
        VALUES (?, ?, ?)
        ON CONFLICT(curso_id, usuario_email) DO UPDATE SET nota = excluded.nota, data = CURRENT_TIMESTAMP
    """, (curso_id, session['usuario'], nota))
    conn.commit()
    conn.close()
    return jsonify({'mensagem': 'Avaliação registrada!'})

# ─── API: COMPRAS (SIMULADAS) ────────────────────────────────

@app.route('/api/cursos/<int:curso_id>/comprar', methods=['POST'])
def comprar_curso(curso_id):
    if 'usuario' not in session:
        return jsonify({'erro': 'Faça login para comprar.'}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, preco FROM cursos WHERE id = ?", (curso_id,))
    curso = cursor.fetchone()
    if not curso:
        conn.close()
        return jsonify({'erro': 'Curso não encontrado.'}), 404

    try:
        cursor.execute("""
            INSERT INTO compras (usuario_email, curso_id)
            VALUES (?, ?)
        """, (session['usuario'], curso_id))
        conn.commit()
    except sqlite3.IntegrityError:
        # Já comprou
        conn.close()
        return jsonify({'erro': 'Você já comprou este curso.'}), 409

    conn.close()
    return jsonify({'mensagem': f'Compra do curso "{curso["id"]}" simulada com sucesso! Agora você tem acesso ao e-book.'})

@app.route('/api/compras', methods=['GET'])
def listar_compras_usuario():
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado.'}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.* FROM compras cp
        JOIN cursos c ON cp.curso_id = c.id
        WHERE cp.usuario_email = ?
        ORDER BY cp.data_compra DESC
    """, (session['usuario'],))
    compras = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(compras)

@app.route('/api/cursos/<int:curso_id>/acesso', methods=['GET'])
def verificar_acesso_ebook(curso_id):
    if 'usuario' not in session:
        return jsonify({'acesso': False})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM compras WHERE usuario_email = ? AND curso_id = ?
    """, (session['usuario'], curso_id))
    tem_acesso = cursor.fetchone() is not None
    conn.close()
    # Criador também tem acesso
    cursor = conn.cursor()
    cursor.execute("SELECT criador FROM cursos WHERE id = ?", (curso_id,))
    curso = cursor.fetchone()
    if curso and curso['criador'] == session['usuario']:
        tem_acesso = True
    return jsonify({'acesso': tem_acesso, 'ebook': curso['ebook'] if tem_acesso else None})

# ─── INICIALIZAÇÃO ───────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)