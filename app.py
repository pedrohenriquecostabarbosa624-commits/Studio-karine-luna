from flask import Flask, render_template, request, jsonify
import os
import mercadopago

app = Flask(__name__, template_folder='templates')

# Inicializa o Mercado Pago com o Token que vamos colocar na Render
sdk = mercadopago.SDK(os.environ.get("MERCADO_PAGO_TOKEN"))

WHATSAPP_NUMERO = "5568999900690"
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
    "Maquiagem (Noiva)": 120.00,
    "Maquiagem Luxo": 80.00,
    "Micropigmentação": 370.00
}

@app.route('/')
def home():
    return render_template('index.html', servicos=SERVICOS)

@app.route('/pagamento', methods=['POST'])
def pagamento():
    nome = request.form.get('nome')
    data = request.form.get('data')
    hora = request.form.get('hora')
    procedimentos = request.form.getlist('procedimentos') 
    
    horario_solicitado = f"{data} {hora}"
    
    if os.path.exists(ARQUIVO_AGENDAMENTOS):
        with open(ARQUIVO_AGENDAMENTOS, "r") as f:
            if horario_solicitado in f.read().splitlines():
                return render_template('erro.html')
                
    with open(ARQUIVO_AGENDAMENTOS, "a") as f:
        f.write(horario_solicitado + "\n")

    valor_total = sum(SERVICOS.get(p, 0.00) for p in procedimentos)
    procedimentos_str = ", ".join(procedimentos) 

    # Criando o pagamento Pix real no Mercado Pago
    payment_data = {
        "transaction_amount": float(valor_total),
        "description": f"Estúdio Karine - {procedimentos_str}",
        "payment_method_id": "pix",
        "payer": {
            "email": "cliente_estudio@sua_escolha.com", # Email fictício obrigatório pela API
            "first_name": nome
        }
    }
    
    payment_response = sdk.payment().create(payment_data)
    payment = payment_response.get("response", {})
    
    # Puxa os dados gerados pelo Mercado Pago
    payment_id = payment.get("id")
    transaction_data = payment.get("point_of_interaction", {}).get("transaction_data", {})
    pix_copia_cola = transaction_data.get("qr_code")
    img_base64 = transaction_data.get("qr_code_base64")
    
    msg = f"✨ *AGENDAMENTO CONFIRMADO* ✨%0A%0A👤 *Cliente:* {nome}%0A📅 *Data:* {data}%0A⏰ *Hora:* {hora}%0A💅 *Serviços:* {procedimentos_str}%0A💰 *Valor Total:* R$ {valor_total:.2f}"
    
    return render_template('pix.html', nome=nome, valor_total=f"{valor_total:.2f}", qr_code_img=img_base64, mensagem_wpp=msg, pix_copia_cola=pix_copia_cola, payment_id=payment_id)

# Nova rota que o ecrã vai consultar para saber se já foi pago
@app.route('/status/<payment_id>')
def status_pagamento(payment_id):
    payment_info = sdk.payment().get(payment_id)
    status = payment_info.get("response", {}).get("status", "pending")
    return jsonify({"status": status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
