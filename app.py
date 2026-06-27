from flask import Flask, render_template, request
import urllib.parse
import segno
import io
import base64
import os

app = Flask(__name__, template_folder='templates')
WHATSAPP_NUMERO = "5568999900690"
CHAVE_PIX = "d881c964-ee6b-45a6-8e51-2e069fb597b2"
ARQUIVO_AGENDAMENTOS = "agendamentos.txt"

def calcular_crc16(payload):
    crc = 0xFFFF
    for byte in payload.encode('utf-8'):
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def gerar_payload_pix(valor):
    valor_formatado = f"{valor:.2f}"
    payload = f"00020126360014BR.GOV.BCB.PIX0114{CHAVE_PIX}5204000053039865405{valor_formatado}5802BR5916Estudio Karine6008BRASILIA62070503***6304"
    crc = calcular_crc16(payload)
    return payload + crc

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
    # request.form.getlist pega TODOS os itens que o cliente marcou
    procedimentos = request.form.getlist('procedimentos') 
    
    horario_solicitado = f"{data} {hora}"
    
    # Trava de agendamento duplicado
    if os.path.exists(ARQUIVO_AGENDAMENTOS):
        with open(ARQUIVO_AGENDAMENTOS, "r") as f:
            if horario_solicitado in f.read().splitlines():
                return render_template('erro.html')
                
    with open(ARQUIVO_AGENDAMENTOS, "a") as f:
        f.write(horario_solicitado + "\n")

    # Calcula o total somando os procedimentos escolhidos
    valor_total = sum(SERVICOS.get(p, 0.00) for p in procedimentos)
    
    # Transforma a lista de procedimentos num texto separado por vírgula
    procedimentos_str = ", ".join(procedimentos) 

    pix_payload = gerar_payload_pix(valor_total)
    
    qr = segno.make(pix_payload)
    out = io.BytesIO()
    qr.save(out, kind='png', scale=8)
    img_base64 = base64.b64encode(out.getvalue()).decode('utf-8')
    
    msg = f"✨ *AGENDAMENTO CONFIRMADO* ✨%0A%0A👤 *Cliente:* {nome}%0A📅 *Data:* {data}%0A⏰ *Hora:* {hora}%0A💅 *Serviços:* {procedimentos_str}%0A💰 *Valor Total:* R$ {valor_total:.2f}"
    
    return render_template('pix.html', nome=nome, valor_total=f"{valor_total:.2f}", qr_code_img=img_base64, mensagem_wpp=msg, pix_copia_cola=pix_payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
