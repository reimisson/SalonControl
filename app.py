from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date, timedelta

app = Flask(__name__)


# =========================
# BANCO DE DADOS
# =========================

def conectar_banco():

    conexao = sqlite3.connect("saloncontrol.db")

    conexao.row_factory = sqlite3.Row

    return conexao


def criar_banco():

    conexao = conectar_banco()

    # =========================
    # CLIENTES
    # =========================

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            observacoes TEXT
        )
    """)

    # =========================
    # SERVIÇOS
    # =========================

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            duracao INTEGER NOT NULL
        )
    """)

    # =========================
    # PROFISSIONAIS
    # =========================

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS profissionais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            especialidade TEXT,
            comissao REAL DEFAULT 0
        )
    """)

    # =========================
    # AGENDAMENTOS
    # =========================

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            servico TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            valor REAL NOT NULL,
            observacoes TEXT,
            status TEXT DEFAULT 'Agendado',
            profissional_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (profissional_id) REFERENCES profissionais(id)
        )
    """)

    # =========================
    # CORREÇÕES EM BANCOS ANTIGOS
    # =========================

    colunas = conexao.execute(
        "PRAGMA table_info(agendamentos)"
    ).fetchall()

    nomes_colunas = [
        coluna["name"]
        for coluna in colunas
    ]

    if "status" not in nomes_colunas:

        conexao.execute("""
            ALTER TABLE agendamentos
            ADD COLUMN status TEXT DEFAULT 'Agendado'
        """)

    if "profissional_id" not in nomes_colunas:

        conexao.execute("""
            ALTER TABLE agendamentos
            ADD COLUMN profissional_id INTEGER
        """)

    conexao.commit()

    conexao.close()


# =========================
# DASHBOARD
# =========================

@app.route("/")
def inicio():

    conexao = conectar_banco()

    clientes = conexao.execute("""
        SELECT *
        FROM clientes
        ORDER BY id DESC
    """).fetchall()

    total_agendamentos = conexao.execute("""
        SELECT COUNT(*) AS total
        FROM agendamentos
        WHERE status = 'Agendado'
    """).fetchone()["total"]

    faturamento = conexao.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM agendamentos
        WHERE status = 'Concluído'
    """).fetchone()["total"]

    total_profissionais = conexao.execute("""
        SELECT COUNT(*) AS total
        FROM profissionais
    """).fetchone()["total"]

    conexao.close()

    return render_template(
        "index.html",
        clientes=clientes,
        total_agendamentos=total_agendamentos,
        faturamento=faturamento,
        total_profissionais=total_profissionais
    )


# =========================
# CLIENTES
# =========================

@app.route("/clientes")
def clientes():

    conexao = conectar_banco()

    lista_clientes = conexao.execute("""
        SELECT *
        FROM clientes
        ORDER BY nome
    """).fetchall()

    conexao.close()

    return render_template(
        "clientes.html",
        clientes=lista_clientes
    )


@app.route("/clientes/novo", methods=["POST"])
def novo_cliente():

    nome = request.form["nome"]
    telefone = request.form["telefone"]
    email = request.form["email"]
    observacoes = request.form["observacoes"]

    conexao = conectar_banco()

    conexao.execute("""
        INSERT INTO clientes
        (nome, telefone, email, observacoes)
        VALUES (?, ?, ?, ?)
    """, (
        nome,
        telefone,
        email,
        observacoes
    ))

    conexao.commit()

    conexao.close()

    return redirect("/clientes")


# =========================
# SERVIÇOS
# =========================

@app.route("/servicos")
def servicos():

    conexao = conectar_banco()

    lista_servicos = conexao.execute("""
        SELECT *
        FROM servicos
        ORDER BY nome
    """).fetchall()

    conexao.close()

    return render_template(
        "servicos.html",
        servicos=lista_servicos
    )


@app.route("/servicos/novo", methods=["POST"])
def novo_servico():

    nome = request.form["nome"]
    preco = request.form["preco"]
    duracao = request.form["duracao"]

    conexao = conectar_banco()

    conexao.execute("""
        INSERT INTO servicos
        (nome, preco, duracao)
        VALUES (?, ?, ?)
    """, (
        nome,
        preco,
        duracao
    ))

    conexao.commit()

    conexao.close()

    return redirect("/servicos")


# =========================
# PROFISSIONAIS
# =========================

@app.route("/profissionais")
def profissionais():

    conexao = conectar_banco()

    lista_profissionais = conexao.execute("""
        SELECT *
        FROM profissionais
        ORDER BY nome
    """).fetchall()

    conexao.close()

    return render_template(
        "profissionais.html",
        profissionais=lista_profissionais
    )


@app.route("/profissionais/novo", methods=["POST"])
def novo_profissional():

    nome = request.form["nome"]
    telefone = request.form["telefone"]
    especialidade = request.form["especialidade"]
    comissao = request.form["comissao"]

    conexao = conectar_banco()

    conexao.execute("""
        INSERT INTO profissionais
        (nome, telefone, especialidade, comissao)
        VALUES (?, ?, ?, ?)
    """, (
        nome,
        telefone,
        especialidade,
        comissao
    ))

    conexao.commit()

    conexao.close()

    return redirect("/profissionais")


# =========================
# AGENDA
# =========================

@app.route("/agenda")
def agenda():

    conexao = conectar_banco()

    lista_clientes = conexao.execute("""
        SELECT *
        FROM clientes
        ORDER BY nome
    """).fetchall()

    lista_servicos = conexao.execute("""
        SELECT *
        FROM servicos
        ORDER BY nome
    """).fetchall()

    lista_profissionais = conexao.execute("""
        SELECT *
        FROM profissionais
        ORDER BY nome
    """).fetchall()

    agendamentos = conexao.execute("""
        SELECT
            agendamentos.*,
            clientes.nome AS cliente_nome,
            profissionais.nome AS profissional_nome,
            profissionais.comissao AS profissional_comissao

        FROM agendamentos

        INNER JOIN clientes
        ON agendamentos.cliente_id = clientes.id

        LEFT JOIN profissionais
        ON agendamentos.profissional_id = profissionais.id

        ORDER BY data, horario
    """).fetchall()

    conexao.close()

    return render_template(
        "agenda.html",
        clientes=lista_clientes,
        servicos=lista_servicos,
        profissionais=lista_profissionais,
        agendamentos=agendamentos
    )


# =========================
# NOVO AGENDAMENTO
# =========================

@app.route("/agendamentos/novo", methods=["POST"])
def novo_agendamento():

    cliente_id = request.form["cliente_id"]
    servico_id = request.form["servico_id"]
    profissional_id = request.form["profissional_id"]
    data = request.form["data"]
    horario = request.form["horario"]
    observacoes = request.form["observacoes"]

    conexao = conectar_banco()

    servico = conexao.execute("""
        SELECT *
        FROM servicos
        WHERE id = ?
    """, (servico_id,)).fetchone()

    if not servico:

        conexao.close()

        return "Serviço não encontrado", 404

    profissional = conexao.execute("""
        SELECT *
        FROM profissionais
        WHERE id = ?
    """, (profissional_id,)).fetchone()

    if not profissional:

        conexao.close()

        return "Profissional não encontrado", 404

    nome_servico = servico["nome"]

    valor = servico["preco"]

    conexao.execute("""
        INSERT INTO agendamentos
        (
            cliente_id,
            servico,
            data,
            horario,
            valor,
            observacoes,
            status,
            profissional_id
        )

        VALUES (?, ?, ?, ?, ?, ?, 'Agendado', ?)
    """, (
        cliente_id,
        nome_servico,
        data,
        horario,
        valor,
        observacoes,
        profissional_id
    ))

    conexao.commit()

    conexao.close()

    return redirect("/agenda")


# =========================
# CANCELAR AGENDAMENTO
# =========================

@app.route(
    "/agendamentos/<int:id>/cancelar",
    methods=["POST"]
)
def cancelar_agendamento(id):

    conexao = conectar_banco()

    conexao.execute("""
        UPDATE agendamentos

        SET status = 'Cancelado'

        WHERE id = ?

        AND status = 'Agendado'
    """, (id,))

    conexao.commit()

    conexao.close()

    return redirect("/agenda")


# =========================
# CONCLUIR AGENDAMENTO
# =========================

@app.route(
    "/agendamentos/<int:id>/concluir",
    methods=["POST"]
)
def concluir_agendamento(id):

    conexao = conectar_banco()

    conexao.execute("""
        UPDATE agendamentos

        SET status = 'Concluído'

        WHERE id = ?

        AND status = 'Agendado'
    """, (id,))

    conexao.commit()

    conexao.close()

    return redirect("/agenda")


# =========================
# VINCULAR PROFISSIONAL
# =========================

@app.route(
    "/agendamentos/<int:id>/profissional",
    methods=["POST"]
)
def vincular_profissional(id):

    profissional_id = request.form["profissional_id"]

    conexao = conectar_banco()

    profissional = conexao.execute("""
        SELECT *
        FROM profissionais
        WHERE id = ?
    """, (profissional_id,)).fetchone()

    if not profissional:

        conexao.close()

        return "Profissional não encontrado", 404

    conexao.execute("""
        UPDATE agendamentos

        SET profissional_id = ?

        WHERE id = ?
    """, (
        profissional_id,
        id
    ))

    conexao.commit()

    conexao.close()

    return redirect("/agenda")


# =========================
# FINANCEIRO
# =========================

@app.route("/financeiro")
def financeiro():

    periodo = request.args.get(
        "periodo",
        "mes"
    )

    hoje = date.today()


    # =========================
    # HOJE
    # =========================

    if periodo == "hoje":

        data_inicio = hoje

        data_fim = hoje

        titulo_periodo = "Hoje"


    # =========================
    # ESTA SEMANA
    # =========================

    elif periodo == "semana":

        # Segunda-feira
        data_inicio = (
            hoje -
            timedelta(
                days=hoje.weekday()
            )
        )

        # Domingo
        data_fim = (
            data_inicio +
            timedelta(days=6)
        )

        titulo_periodo = "Esta semana"


    # =========================
    # ESTE MÊS
    # =========================

    elif periodo == "mes":

        # Primeiro dia do mês
        data_inicio = hoje.replace(
            day=1
        )

        # Descobre o primeiro dia
        # do próximo mês
        if hoje.month == 12:

            proximo_mes = hoje.replace(
                year=hoje.year + 1,
                month=1,
                day=1
            )

        else:

            proximo_mes = hoje.replace(
                month=hoje.month + 1,
                day=1
            )

        # Último dia do mês atual
        data_fim = (
            proximo_mes -
            timedelta(days=1)
        )

        titulo_periodo = "Este mês"


    # =========================
    # PERSONALIZADO
    # =========================

    elif periodo == "personalizado":

        inicio_recebido = request.args.get(
            "data_inicio"
        )

        fim_recebido = request.args.get(
            "data_fim"
        )

        try:

            data_inicio = date.fromisoformat(
                inicio_recebido
            )

            data_fim = date.fromisoformat(
                fim_recebido
            )

            # Se o usuário colocar
            # o final antes do início
            if data_fim < data_inicio:

                data_inicio, data_fim = (
                    data_fim,
                    data_inicio
                )

            titulo_periodo = (
                f"{data_inicio.strftime('%d/%m/%Y')}"
                f" até "
                f"{data_fim.strftime('%d/%m/%Y')}"
            )

        except (
            ValueError,
            TypeError
        ):

            # Se houver erro,
            # volta para o mês atual

            data_inicio = hoje.replace(
                day=1
            )

            if hoje.month == 12:

                proximo_mes = hoje.replace(
                    year=hoje.year + 1,
                    month=1,
                    day=1
                )

            else:

                proximo_mes = hoje.replace(
                    month=hoje.month + 1,
                    day=1
                )

            data_fim = (
                proximo_mes -
                timedelta(days=1)
            )

            titulo_periodo = "Este mês"

            periodo = "mes"


    # =========================
    # CASO PADRÃO
    # =========================

    else:

        data_inicio = hoje.replace(
            day=1
        )

        if hoje.month == 12:

            proximo_mes = hoje.replace(
                year=hoje.year + 1,
                month=1,
                day=1
            )

        else:

            proximo_mes = hoje.replace(
                month=hoje.month + 1,
                day=1
            )

        data_fim = (
            proximo_mes -
            timedelta(days=1)
        )

        titulo_periodo = "Este mês"

        periodo = "mes"


    # =========================
    # CONVERTER DATAS
    # =========================

    data_inicio_str = (
        data_inicio.isoformat()
    )

    data_fim_str = (
        data_fim.isoformat()
    )


    conexao = conectar_banco()


    # =========================
    # FATURAMENTO
    # =========================

    faturamento = conexao.execute("""
        SELECT COALESCE(
            SUM(valor),
            0
        ) AS total

        FROM agendamentos

        WHERE status = 'Concluído'

        AND data >= ?

        AND data <= ?
    """, (
        data_inicio_str,
        data_fim_str
    )).fetchone()["total"]


    # =========================
    # ATENDIMENTOS
    # =========================

    total_atendimentos = conexao.execute("""
        SELECT COUNT(*) AS total

        FROM agendamentos

        WHERE status = 'Concluído'

        AND data >= ?

        AND data <= ?
    """, (
        data_inicio_str,
        data_fim_str
    )).fetchone()["total"]


    # =========================
    # COMISSÕES
    # =========================

    comissao_total = conexao.execute("""
        SELECT COALESCE(
            SUM(
                agendamentos.valor *
                COALESCE(
                    profissionais.comissao,
                    0
                ) / 100
            ),
            0
        ) AS total

        FROM agendamentos

        LEFT JOIN profissionais

        ON agendamentos.profissional_id =
           profissionais.id

        WHERE agendamentos.status =
              'Concluído'

        AND agendamentos.data >= ?

        AND agendamentos.data <= ?
    """, (
        data_inicio_str,
        data_fim_str
    )).fetchone()["total"]


    # =========================
    # LÍQUIDO
    # =========================

    valor_liquido = (
        faturamento -
        comissao_total
    )


    # =========================
    # DESEMPENHO DOS PROFISSIONAIS
    # =========================

    profissionais_financeiro = conexao.execute("""
        SELECT

            profissionais.nome AS nome,

            COUNT(
                agendamentos.id
            ) AS atendimentos,

            COALESCE(
                SUM(
                    agendamentos.valor
                ),
                0
            ) AS faturamento,

            COALESCE(
                SUM(
                    agendamentos.valor *
                    COALESCE(
                        profissionais.comissao,
                        0
                    ) / 100
                ),
                0
            ) AS comissao

        FROM profissionais

        LEFT JOIN agendamentos

        ON profissionais.id =
           agendamentos.profissional_id

        AND agendamentos.status =
            'Concluído'

        AND agendamentos.data >= ?

        AND agendamentos.data <= ?

        GROUP BY profissionais.id

        ORDER BY faturamento DESC
    """, (
        data_inicio_str,
        data_fim_str
    )).fetchall()


       # =========================
    # HISTÓRICO FINANCEIRO
    # =========================

    historico_financeiro = conexao.execute("""
        SELECT
            data,
            COUNT(*) AS atendimentos,
            COALESCE(SUM(valor), 0) AS faturamento

        FROM agendamentos

        WHERE status = 'Concluído'

        AND data >= ?
        AND data <= ?

        GROUP BY data

        ORDER BY data
    """, (
        data_inicio_str,
        data_fim_str
    )).fetchall()


    # =========================
    # PREPARAR DADOS DOS GRÁFICOS
    # =========================

    grafico_datas = []
    grafico_faturamento = []
    grafico_atendimentos = []


    # Transformar os registros do banco
    # em um dicionário para facilitar
    historico_por_data = {

        registro["data"]: {

            "faturamento":
                float(registro["faturamento"]),

            "atendimentos":
                registro["atendimentos"]

        }

        for registro in historico_financeiro
    }


    # =========================
    # CRIAR TODOS OS DIAS DO PERÍODO
    # =========================

    data_atual = data_inicio


    while data_atual <= data_fim:

        data_chave = data_atual.isoformat()


        grafico_datas.append(
            data_atual.strftime("%d/%m")
        )


        if data_chave in historico_por_data:

            grafico_faturamento.append(
                historico_por_data[data_chave]["faturamento"]
            )

            grafico_atendimentos.append(
                historico_por_data[data_chave]["atendimentos"]
            )

        else:

            grafico_faturamento.append(0)

            grafico_atendimentos.append(0)


        data_atual += timedelta(days=1)


    conexao.close()


    # =========================
    # MOSTRAR FINANCEIRO
    # =========================

    return render_template(

"financeiro.html",

    faturamento=faturamento,

    total_atendimentos=
        total_atendimentos,

    comissao_total=
        comissao_total,

    valor_liquido=
        valor_liquido,

    profissionais_financeiro=
        profissionais_financeiro,

    historico_financeiro=
        historico_financeiro,

    grafico_datas=
        grafico_datas,

    grafico_faturamento=
        grafico_faturamento,

    grafico_atendimentos=
        grafico_atendimentos,

    periodo=periodo,

    titulo_periodo=
        titulo_periodo,

    data_inicio=
        data_inicio_str,

    data_fim=
        data_fim_str
)


# =========================
# CRIAR BANCO AO INICIAR
# =========================

criar_banco()


# =========================
# INICIAR SISTEMA
# =========================

if __name__ == "__main__":

    app.run(
        debug=True)
    
