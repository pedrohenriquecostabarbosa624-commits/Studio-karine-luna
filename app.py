from flask import Flask, render_template, request
import urllib.parse, segno, io, base64, os

app = Flask(__name__)
WHATSAPP_NUMERO = "5568999900690"
CHAVE_PIX = "d881c964-ee6b-45a6-8e51-2e069fb597b2"
ARQUIVO_AGENDAMENTOS = "agendamentos.txt"

def gerar_payload_pix(valor):
    v = f"{valor:.2f}"
    payload = f"00020126360014BR.GOV.BCB.PIX0114{CHAVE_PIX}5204000053039865405{v}5802BR5916Estudio Karine6008BRASILIA62070503***6304"
    return payload

@app.route('/pagamento', methods=['POST'])
def pagamento():
    nome, proc, data, hora = request.form.get('nome'), request.form.get('procedimento'), request.form.get('data'), request.form.get('hora')
    horario = f"{data} {hora}"
    if os.path.exists(ARQUIVO_AGENDAMENTOS):
        with open(ARQUIVO_AGENDAMENTOS, "r") as f:
            if horario in f.read().splitlines(): return "❌ Horário já reservado!"
    with open(ARQUIVO_AGENDAMENTOS, "a") as f: f.write(horario + "\n")
    
    qr = segno.make(gerar_payload_pix(40.00)) # Ajuste o valor conforme necessário
    out = io.BytesIO()
    qr.save(out, kind='png', scale=8)
    img = base64.b64encode(out.getvalue()).decode('utf-8')
    msg = f"✨ *AGENDAMENTO CONFIRMADO* ✨%0A%0A👤 *Cliente:* {nome}%0A📅 *Data:* {data}%0A⏰ *Hora:* {hora}%0A💅 *Serviço:* {proc}"
    return render_template('pix.html', nome=nome, procedimento=proc, valor_total="40.00", qr_code_img=img, mensagem_wpp=msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
