import pandas as pd
import requests
import flet as ft

def main(page: ft.Page):
    page.title = "Previsão do Tempo e Condições Oceânicas"
    page.scroll = "auto"

    r_estado = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados")
    df_estado = pd.DataFrame(r_estado.json()).sort_values(by="nome")
    estados_dict = dict(zip(df_estado["nome"], df_estado["sigla"]))

    t_estado = ft.Text()
    t_cidade = ft.Text()
    t_codigo = ft.Text()
    cidade = ft.Dropdown(width=300, options=[])
    cards_container = ft.Column()
    dialog = ft.AlertDialog(modal=True)
    codigo_cptec = {"valor": None}
    dados_ondas = {"dados": []}

    def on_estado_change(e):
        estado_nome = estado.value
        estado_sigla = estados_dict.get(estado_nome)
        t_estado.value = f"Estado: {estado_nome}"
        t_cidade.value = ""
        cidade.options = []
        cards_container.controls.clear()
        if estado_sigla:
            r_cidade = requests.get(
                f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{estado_sigla}/municipios")
            df_cidade = pd.DataFrame(r_cidade.json()).sort_values(by="nome")
            cidade.data = df_cidade
            cidade.options = [ft.dropdown.Option(c) for c in df_cidade["nome"].tolist()]
        page.update()

    def on_cidade_change(e):
        nome_cidade = cidade.value
        t_cidade.value = f"Cidade: {nome_cidade}"
        t_codigo.value = ""
        cards_container.controls.clear()
        page.update()

    def buscar_codigo_cptec(e):
        nome_cidade = cidade.value
        if nome_cidade:
            r = requests.get(f"https://brasilapi.com.br/api/cptec/v1/cidade/{nome_cidade}")
            if r.status_code == 200:
                dados = r.json()
                if isinstance(dados, list) and len(dados) > 0:
                    codigo = dados[0]["id"]
                    codigo_cptec["valor"] = codigo
                    t_codigo.value = f"Código CPTEC: {codigo}"
                    buscar_previsao(codigo)
                    buscar_ondas(codigo)
                else:
                    t_codigo.value = "Cidade não encontrada na BrasilAPI."
            else:
                t_codigo.value = f"Erro ao buscar cidade: {r.status_code}"
        else:
            t_codigo.value = "Selecione uma cidade primeiro."
        page.update()

    def buscar_previsao(codigo):
        r = requests.get(f"https://brasilapi.com.br/api/cptec/v1/clima/previsao/{codigo}/6")
        if r.status_code == 200:
            previsao = r.json().get("clima", [])
            cards_container.controls.clear()
            for dia in previsao:
                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        on_click=lambda e, data=dia["data"]: mostrar_condicoes_oceanicas(data),
                        content=ft.Column([
                            ft.Text(f"📅 {dia['data']}", weight="bold"),
                            ft.Text(f"🌤️ Condição: {dia['condicao_desc']}"),
                            ft.Text(f"🌡️ Mínima: {dia['min']}°C"),
                            ft.Text(f"🌡️ Máxima: {dia['max']}°C"),
                            ft.Text(f"🔆 Índice UV: {dia['indice_uv']}")
                        ])
                    )
                )
                cards_container.controls.append(card)
        else:
            cards_container.controls = [ft.Text("Erro ao buscar previsão do tempo.")]
        page.update()

    def buscar_ondas(codigo):
        r = requests.get(f"https://brasilapi.com.br/api/cptec/v1/ondas/{codigo}/6")
        if r.status_code == 200:
            dados_ondas["dados"] = r.json().get("ondas", [])
        else:
            dados_ondas["dados"] = []

    def mostrar_condicoes_oceanicas(data):
        ondas_dia = [o for o in dados_ondas["dados"] if o["data"] == data]
        if not ondas_dia:
            dialog.content = ft.Text("Sem dados oceânicos para este dia.")
        else:
            col = ft.Column(scroll="auto")
            for o in ondas_dia:
                col.controls.append(ft.Text(f"🕒 {o['hora']}"))
                col.controls.append(ft.Text(f"💨 Vento: {o['vento']} km/h - {o['direcao_vento_desc']}"))
                col.controls.append(ft.Text(f"🌊 Altura da Onda: {o['altura_onda']} m - {o['direcao_onda_desc']}"))
                col.controls.append(ft.Text(f"🌊 Agitação: {o['agitacao']}"))
                col.controls.append(ft.Divider())
            dialog.content = col
        page.dialog = dialog
        dialog.open = True
        page.update()

    estado = ft.Dropdown(
        width=300,
        label="Selecione um estado",
        options=[ft.dropdown.Option(nome) for nome in df_estado["nome"].tolist()],
        on_change=on_estado_change
    )

    cidade.on_change = on_cidade_change
    botao_buscar = ft.ElevatedButton(text="Buscar Previsão do Tempo", on_click=buscar_codigo_cptec)

    page.add(
        estado,
        t_estado,
        cidade,
        t_cidade,
        botao_buscar,
        t_codigo,
        ft.Divider(),
        ft.Text("Previsão para os próximos 6 dias:", size=16, weight="bold"),
        cards_container
    )

ft.app(target=main)
