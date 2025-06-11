from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd

app = Flask(__name__)


# Carregar estados ao iniciar o app
def carregar_estados():
    r_estado = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados")
    df_estado = pd.DataFrame(r_estado.json()).sort_values(by="nome")
    return df_estado.to_dict(orient="records")


@app.route("/")
def index():
    estados = carregar_estados()
    return render_template("index.html", estados=estados)


@app.route("/buscar-cidade", methods=["POST"])
def buscar_cidade():
    estado_sigla = request.json["estado"]
    r_cidade = requests.get(f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{estado_sigla}/municipios")
    cidades = sorted([c["nome"] for c in r_cidade.json()])
    return jsonify(cidades)


@app.route("/buscar-dados", methods=["POST"])
def buscar_dados():
    cidade_nome = request.json["cidade"]
    # Buscar código CPTEC
    r_codigo = requests.get(f"https://brasilapi.com.br/api/cptec/v1/cidade/{cidade_nome}")
    if r_codigo.status_code != 200 or not r_codigo.json():
        return jsonify({"erro": "Cidade não encontrada"})

    codigo = r_codigo.json()[0]["id"]

    # Buscar previsão do tempo
    r_previsao = requests.get(f"https://brasilapi.com.br/api/cptec/v1/clima/previsao/{codigo}/6")
    previsao = r_previsao.json().get("clima", []) if r_previsao.status_code == 200 else []

    # Buscar dados de ondas
    r_ondas = requests.get(f"https://brasilapi.com.br/api/cptec/v1/ondas/{codigo}/6")
    ondas = []
    if r_ondas.status_code == 200:
        for dia in r_ondas.json().get("ondas", []):
            data = dia["data"].split("T")[0]
            for hora_dado in dia["dados_ondas"]:
                ondas.append({
                    "data": data,
                    "hora": hora_dado["hora"],
                    "vento": hora_dado["vento"],
                    "direcao_vento_desc": hora_dado["direcao_vento"],
                    "altura_onda": hora_dado["altura_onda"],
                    "direcao_onda_desc": hora_dado["direcao_onda_desc"],
                    "agitacao": hora_dado["agitation"]
                })

    return jsonify({
        "previsao": previsao,
        "ondas": ondas
    })

    console.log("Dados de ondas carregados:", window.dadosOndas);
    console.log("Data selecionada:", dataSelecionada);


if __name__ == "__main__":
    app.run(debug=True)