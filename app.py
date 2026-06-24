from flask import Flask, render_template, request
import urllib.parse
import segno
import io
import base64

app = Flask(__name__)

# CONFIGURAÇÕES OFICIAIS
WHATSAPP_NUMERO = "5568999900690"  
CHAVE_PIX = "d881c964-ee6b-45a6-8e51-2e069fb597b2" 

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

def calcular_crc16(texto):
    crc = 0xFFFF
    for char in texto:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def gerar_payload_pix(chave, valor):
    gui = "0014br.gov.bcb.pix"
    key_tag = f"01{len(chave):02d}{chave}"
    merchant_info = f"{gui}{key_tag}"
    amount = f"{valor:.2f}"
    parts = [
        "000201",
        f"26{len(merchant_info):02d}{merchant_info}",
        "52040000",
        "5303986",
        f"54{len(amount):02d}{amount}",
        "5802BR",
        "5911Karine Luna", 
        "6010Rio Branco", 
        "62070503***",    
        "6304"            
    ]
    raw_payload = "".join(parts)
    return raw_payload + calcular_crc16(raw_payload)

@app.route('/')
def home():
    return render_template('index.html', servicos=SERVICOS)

@app.route('/pagamento', methods=['POST'])
def pagamento():
    nome = request.form.get('nome')
    procedimento = request.form.get('procedimento')
    data = request.form.get('data')
    hora = request.form.get('hora')
    valor_total = SERVICOS.get(procedimento, 0.00)
    
    if procedimento == "Maquiagem (Noiva/Eventos/Artística)":
        valor_taxa = 60.00
    elif procedimento == "Maquiagem Luxo Elaborada":
        valor_taxa = 40.00
    elif procedimento == "Maquiagem Express Básica":
        valor_taxa = 32.50
    else:
        valor_taxa = 20.00

    data_f = "/".join(data.split("-")[::-1])
    pix_string = gerar_payload_pix(CHAVE_PIX, valor_taxa)
    qrcode = segno.make(pix_string)
    
    buff = io.BytesIO()
    qrcode.save(buff, kind='png', scale=8)
    img_base64 = base64.b64encode(buff.getvalue()).decode('utf-8')
    
    msg = f"🌙 *AGENDAMENTO STUDIO KARINE LUNA*\n\n👤 *Cliente:* {nome}\n✨ *Proc:* {procedimento}\n📅 *Data:* {data_f}\n⏰ *Hora:* {hora}\n💵 *Taxa:* R$ {valor_taxa:.2f}"
    link = f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMERO}&text={urllib.parse.quote(msg)}"

    return render_template('pix.html', nome=nome, procedimento=procedimento, valor_total=f"{valor_total:.2f}", valor_taxa=f"{valor_taxa:.2f}", data=data_f, hora=hora, pix_string=pix_string, qr_code_img=img_base64, link_whatsapp=link)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
