from flask import Flask, render_template, request, jsonify
import os
import mercadopago
import re

app = Flask(__name__, template_folder='templates')

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
    nome = request.form.get('nome', 'Cliente')
    data = request.form.get('data')
    hora = request.form.get('hora')
    procedimentos = request.form.getlist('procedimentos') 
    
    # Prevenção: Se não escolher nada, avisa logo
    if not procedimentos:
        return "<h3 style='color: white; font-family: sans-serif; text-align: center; margin-top: 50px;'>❌ Precisas de selecionar pelo menos um procedimento! Volte atrás.</h3>"

    horario_solicitado = f"{data} {hora}"
    
    if os.path.exists(ARQUIVO_AGENDAMENTOS):
        with open(ARQUIVO_AGENDAMENTOS, "r") as f:
            if horario_solicitado in f.read().splitlines():
                return render_template('erro.html')
                
    with open(ARQUIVO_AGENDAMENTOS, "a") as f:
        f.write(horario_solicitado + "\n")

    valor_total = sum(SERVICOS.get(p, 0.00) for p in procedimentos)
    procedimentos_str = ", ".join(procedimentos) 

    # Gera um e-mail fictício com o nome real do cliente para não ser bloqueado
    email_limpo = re.sub(r'[^a-zA-Z0-9]', '', nome.lower()) + "@email.com"

    payment_data = {
        "transaction_amount": float(valor_total),
        "description": f"Estúdio Karine - {procedimentos_str}",
        "payment_method_id": "pix",
        "payer": {
            "email": email_limpo,
            "first_name": nome
        }
    }
    
    payment_response = sdk.payment().create(payment_data)
    payment = payment_response.get("response", {})
    
    # SE O MERCADO PAGO RECUSAR: Mostra o erro no ecrã
    if "id" not in payment or payment_response.get("status") in [400, 401]:
        erro_motivo = payment.get("message", "Erro desconhecido")
        causas = payment.get("cause", [])
        if causas:
            erro_motivo += " | Detalhe: " + str(causas[0].get("description", ""))
        
        return f"""
        <div style="font-family: sans-serif; text-align: center; color: white; background: #121212; height: 100vh; padding: 20px;">
            <h2 style="color: #ff4c4c;">❌ O Mercado Pago recusou a geração do Pix</h2>
            <p><strong>Motivo do bloqueio:</strong> {erro_motivo}</p>
            <p>Tira um print deste erro para podermos corrigir!</p>
            <a href="javascript:history.back()" style="color: #d4af37;">Voltar</a>
        </div>
        """

    payment_id = payment.get("id")
    transaction_data = payment.get("point_of_interaction", {}).get("transaction_data", {})
    
    pix_copia_cola = transaction_data.get("qr_code")
    img_base64 = transaction_data.get("qr_code_base64")
    
    msg = f"✨ *AGENDAMENTO CONFIRMADO* ✨%0A%0A👤 *Cliente:* {nome}%0A📅 *Data:* {data}%0A⏰ *Hora:* {hora}%0A💅 *Serviços:* {procedimentos_str}%0A💰 *Valor Total:* R$ {valor_total:.2f}"
    
    return render_template('pix.html', nome=nome, valor_total=f"{valor_total:.2f}", qr_code_img=img_base64, mensagem_wpp=msg, pix_copia_cola=pix_copia_cola, payment_id=payment_id)

@app.route('/status/<payment_id>')
def status_pagamento(payment_id):
    payment_info = sdk.payment().get(payment_id)
    status = payment_info.get("response", {}).get("status", "pending")
    return jsonify({"status": status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
