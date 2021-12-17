from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import random


def criatabela():
    conn = sqlite3.connect('card.s3db')  # conectando
    cursor = conn.cursor()  # definindo um cursor
    # cria a tabela
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS card(
    id INTEGER,
    number TEXT,
    pin TEXT,
    balance INTEGER DEFAULT 0
    );
    """)


criatabela()
app = Flask(__name__)
app.secret_key = 'felipeiras'


@app.route('/')
def pagina_inicial():
    return render_template('login.html')


@app.route('/criarconta', methods=['POST', ])
def criarconta():
    class Account:  # conta, número de pin e balanço do usuário são armazenados nesta classe
        def __init__(self, an=0, pin=0, balance=0, idd=1):
            self.an = an
            self.pin = pin
            self.balance = balance
            self.idd = idd

        def generatean(self):  # Gera um número de cartão aleatório para o usuário seguindo o algoritmo de LUHN
            random.seed()
            self.an = str(400000) + \
                      str(random.randrange(100, 999)) + \
                      str(random.randrange(100, 999)) + \
                      str(random.randrange(100, 999))  # O número gerado consiste de 12 números aleatórios
            lista = list(self.an)
            # Control number -- LUHN algoritmo
            # ---------------------------
            lista = [int(a) for a in lista]
            for i in range(len(lista)):
                if i % 2 == 0:
                    lista[i] *= 2
            lista = [a - 9 if a > 9 else a for a in lista]
            control_number = sum(lista)
            # Checkdigit number
            # -------------------------------
            for checkdigit in range(10):
                control_number += checkdigit
                if control_number % 10 == 0:
                    lista.append(checkdigit)
                    break
                control_number -= checkdigit

            self.an = self.an + str(lista[-1])
            self.an = int(self.an)

        def generatepin(self):  # Gera um número de pin aleatório para o usuário entre 1000 e 9999
            random.seed()
            self.pin = random.randrange(1000, 9999)

        def inserir(self):
            conn = sqlite3.connect('card.s3db')  # conectando
            cursor = conn.cursor()  # definindo um cursor
            cursor.execute("""
                    INSERT INTO card (id, number, pin, balance)
                    VALUES (?, ?, ?, ?)""", (self.idd, self.an, self.pin, self.balance))

            conn.commit()
            conn.close()

    conta = Account()
    conta.generatean()
    conta.generatepin()
    conta.idd += 1
    conta.inserir()
    return redirect('/contacriada')


@app.route('/contacriada')
def contacriada():
    conn = sqlite3.connect('card.s3db')  # conectando
    cursor = conn.cursor()  # definindo um cursor
    cursor.execute("SELECT * FROM card")
    records = cursor.fetchall()
    numero_conta = None
    numero_pin = None
    for linha in records:
        numero_conta = linha[1]
        numero_pin = linha[2]
    conn.close()
    conn.close()
    return render_template('display2.html', variavel1=numero_conta, variavel2=numero_pin)


@app.route('/autenticacao', methods=['POST', ])
def autenticacao():
    conn = sqlite3.connect('card.s3db')  # conectando
    cursor = conn.cursor()  # definindo um cursor
    cursor.execute("SELECT * FROM card WHERE number = (?) AND pin = (?)", (request.form['numerodaconta'],
                                                                           request.form['senha']))
    records = cursor.fetchall()
    conn.close()
    if records:
        session['usuario_logado'] = request.form['numerodaconta']
        flash('Conta número ' + request.form['numerodaconta'] + ' logou com sucesso!')
        return redirect('/interno')
    else:
        flash('Não logado, tente novamente!')
        return redirect('/')


@app.route('/interno')
def interno():
    if 'usuario_logado' not in session or session['usuario_logado'] is None:
        return redirect('/')
    return render_template('display.html')


@app.route('/saldo', methods=['POST', ])
def saldo():
    if 'usuario_logado' not in session or session['usuario_logado'] is None:
        return redirect('/')
    conn = sqlite3.connect('card.s3db')  # conectando
    cursor = conn.cursor()  # definindo um cursor
    cursor.execute("SELECT * FROM card WHERE number = (?)", (session['usuario_logado'],))
    records = cursor.fetchall()
    balanco = None
    for linha in records:
        balanco = linha[3]
    conn.close()
    return render_template('display_saldo.html', variavel=balanco)


@app.route('/deposito', methods=['POST', ])
def deposito():
    if 'usuario_logado' not in session or session['usuario_logado'] is None:
        return redirect('/')
    return render_template('display_deposito.html')


@app.route('/depositofunf', methods=['POST', ])
def depositofunf():
    conn = sqlite3.connect('card.s3db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM card WHERE number = (?)", (session['usuario_logado'],))
    records = cursor.fetchall()
    for linha in records:
        balanco = linha[3]

    cursor.execute("UPDATE card SET balance = ? WHERE number = ?",
                   (int(balanco) + int(request.form['valordepositado']), session['usuario_logado']))
    conn.commit()
    conn.close()
    flash(f'Depósito no valor de {request.form["valordepositado"]} reais realizado com sucesso.')
    return redirect('/interno')


@app.route('/transferencia', methods=['POST', ])
def transferencia():
    if 'usuario_logado' not in session or session['usuario_logado'] is None:
        return redirect('/')
    return render_template('display_transferencia.html')


@app.route('/transferenciafunf', methods=['POST', ])
def transferenciafunf():
    conn = sqlite3.connect('card.s3db')
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM card WHERE number = ?", (session['usuario_logado'],))
    records = cursor.fetchall()
    for linha in records:
        balanco1 = linha[0]

    cursor.execute("UPDATE card SET balance = ? WHERE number = ?",
                   (int(balanco1) - int(request.form['valor_transferido']), session['usuario_logado']))
    if balanco1 < request.form['valor_transferido']:
        flash('Saldo insuficiente')
    else:
        cursor.execute("SELECT balance FROM card WHERE number = ?", (request.form['numero_conta_transferida'],))
        records = cursor.fetchall()
        for linha in records:
            balanco2 = linha[0]

        cursor.execute("UPDATE card SET balance = ? WHERE number = ?",
                       (int(balanco2) + int(request.form['valor_transferido']), request.form['numero_conta_transferida']))
        conn.commit()
        conn.close()
        flash(f"Valor de {request.form['valor_transferido']} transferido com sucesso.")
        return redirect('/interno')


@app.route('/delete', methods=['POST', ])
def delete():
    if 'usuario_logado' not in session or session['usuario_logado'] is None:
        return redirect('/')
    conn = sqlite3.connect('card.s3db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM card WHERE number = ?', (session['usuario_logado'],))
    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/logout', methods=['POST', ])
def logout():
    session['usuario_logado'] = None
    flash('Log Out efetuado com sucesso!')
    return redirect('/')


app.run(debug=True)
