from flask import Flask, render_template, request
import urllib.parse
import segno
import io
import base64
import os

app = Flask(__name__)
WHATSAPP_NUMERO = "5568999900690"
CHAVE_PIX = "d881c964-ee6b-45a6-8e51-2e069fb597b2"
ARQUIVO_AGENDAMENTOS = "agendamentos.txt"

SERVICOS = {
    "Brow Lamination com Tintura": 90.00,
    "Brow Lamination sem Tintura": 55.00,
    "Design com Henna": 40.00,
    "Design + Spa das Sobrancelhas": 40.00,
    "Design Personalizado": 25.00,
    "Limpeza da Micropigmentação": 20.00,
    "Cílios Tufos (P)": 55.00,
    "Cílios Tufos (M)": 65.00,
    "Cílios Tufos (G)": 75.00,
    "Cílios Tufos (GG)": 90.00,
    "Lash Lifting com Coloração": 100.00,
    "Lash Lifting sem Coloração": 80.00,
    "Look Francês": 35.00,
    "Depilação Rosto Inteiro": 35.00,
    "Depilação Axilas": 25.00,
    "Depilação de Buço + Queixo": 10.00,
    "Limpeza de Pele": 100.00,
    "Dermaplaning": 55.00,
    "Spa dos Lábios": 20.00,
    "Maquiagem (Noiva/Eventos/Artística)": 120.00,
    "Maquiagem Luxo Elaborada": 80.00,
    "Maquiagem Express Básica": 65.00,
    "Micropigmentação (1ª Sessão)": 370.00,
    "Micropigmentação (1ª Sessão + Retoque)": 450.00
}

@app.route('/')
def home():
    return render_template('index.html', servicos=SERVICOS)

@app.route('/pagamento', methods=['POST'])
def pagamento():
    nome = request.form.get('nome')
    procedimento = request.form.get('procedimento')
    data = request.form.get('data')
    hora = request.form.get('hora')
    horario_solicitado = f"{data} {hora}"
    
    if os.path.exists(ARQUIVO_AGENDAMENTOS):
        with open(ARQUIVO_AGENDAMENTOS, "r") as f:
            if horario_solicitado in f.read().splitlines():
                return "❌ Horário já reservado! Por favor, volte e escolha outro."
                
    with open(ARQUIVO_AGENDAMENTOS, "a") as f:
        f.write(horario_solicitado + "\n")

    valor_total = SERVICOS.get(procedimento, 0.00)
    return "Agendamento confirmado!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
