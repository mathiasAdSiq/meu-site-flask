from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date, timedelta

app = Flask(__name__)

def conectar():
    return sqlite3.connect("estoque.db")

def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            minimo INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            tipo TEXT,
            quantidade INTEGER,
            data TEXT,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)

    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    previsoes = []

    for produto in produtos:
        produto_id, nome, quantidade_atual, minimo = produto

        sete_dias_atras = date.today() - timedelta(days=7)

        cursor.execute("""
            SELECT SUM(quantidade) 
            FROM movimentacoes 
            WHERE produto_id = ? 
            AND tipo = 'saida'
            AND data >= ?
        """, (produto_id, str(sete_dias_atras)))

        consumo_7_dias = cursor.fetchone()[0] or 0
        media_diaria = consumo_7_dias / 7
        previsao_fim_semana = round(media_diaria * 2)

        quantidade_recomendada = max(0, previsao_fim_semana + minimo - quantidade_atual)

        previsoes.append({
            "id": produto_id,
            "nome": nome,
            "quantidade": quantidade_atual,
            "minimo": minimo,
            "media_diaria": round(media_diaria, 2),
            "previsao_fim_semana": previsao_fim_semana,
            "comprar": quantidade_recomendada
        })

    conn.close()

    return render_template("index.html", produtos=previsoes)

@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    nome = request.form["nome"]
    quantidade = int(request.form["quantidade"])
    minimo = int(request.form["minimo"])

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO produtos (nome, quantidade, minimo)
        VALUES (?, ?, ?)
    """, (nome, quantidade, minimo))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/movimentar", methods=["POST"])
def movimentar():
    produto_id = int(request.form["produto_id"])
    tipo = request.form["tipo"]
    quantidade = int(request.form["quantidade"])

    conn = conectar()
    cursor = conn.cursor()

    if tipo == "entrada":
        cursor.execute("""
            UPDATE produtos 
            SET quantidade = quantidade + ?
            WHERE id = ?
        """, (quantidade, produto_id))
    else:
        cursor.execute("""
            UPDATE produtos 
            SET quantidade = quantidade - ?
            WHERE id = ?
        """, (quantidade, produto_id))

    cursor.execute("""
        INSERT INTO movimentacoes (produto_id, tipo, quantidade, data)
        VALUES (?, ?, ?, ?)
    """, (produto_id, tipo, quantidade, str(date.today())))

    conn.commit()
    conn.close()

    return redirect("/")

if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)
