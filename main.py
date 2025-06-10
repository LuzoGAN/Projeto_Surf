import pandas as pd
import requests
import flet as ft


def main(page: ft.Page):
    page.title = "Previsão do Tempo e Condições Oceânicas"
    page.scroll = "auto"

    # Carregar estados
    r_estado = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados")
    df_estado = pd.DataFrame(r_estado.json()).sort_values(by="nome")
    estados_dict = dict(zip(df_estado["nome"], df_estado["sigla"]))

    # Variáveis de interface
    t_estado = ft.Text()
    t_cidade = ft.Text()
    t_codigo = ft.Text()
    cidade = ft.Dropdown(width=300, options=[])
    cards_container = ft.Column()

    # Diálogo para condições oceânicas
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Condições Oceânicas"),
        content=ft.Column([]),
        actions=[
            ft.TextButton("Fechar", on_click=lambda e: fechar_dialogo())
        ]
    )
    page.overlay.append(dialog)  # Adiciona o diálogo à sobreposição da página

    # Variáveis de estado
    codigo_cptec = {"valor": None}
    dados_ondas = {"dados": []}

    def fechar_dialogo():
        dialog.open = False
        page.update()

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
        """Busca dados de ondas e reestrutura para acesso mais fácil"""
        r = requests.get(f"https://brasilapi.com.br/api/cptec/v1/ondas/{codigo}/6")
        if r.status_code == 200:
            dados_brutos = r.json().get("ondas", [])

            # Reestrutura os dados para um formato plano com todas as horas
            dados_processados = []
            for dia in dados_brutos:
                data = dia["data"].split("T")[0]  # Garante formato YYYY-MM-DD
                #print(data)
                for hora_dado in dia["dados_ondas"]:
                    # Junta data e dados horários em um único objeto
                    registro = {
                        "data": data,
                        "hora": hora_dado["hora"],
                        "vento": hora_dado["vento"],
                        "direcao_vento_desc": hora_dado["direcao_vento"],
                        "altura_onda": hora_dado["altura_onda"],
                        "direcao_onda_desc": hora_dado["direcao_onda_desc"],
                        "agitacao": hora_dado["agitation"]  # Corrige o nome do campo
                    }
                    dados_processados.append(registro)

            dados_ondas["dados"] = dados_processados
            #print(dados_ondas)
        else:
            dados_ondas["dados"] = []

    def mostrar_condicoes_oceanicas(data):
        """Exibe condições oceânicas com verificação robusta de datas"""
        # Garante formato consistente para comparação
        data_selecionada = data.split("T")[0] if "T" in data else data

        ondas_dia = [
            o for o in dados_ondas["dados"]
            if o["data"] == data_selecionada
        ]

        if not ondas_dia:
            dialog.content = ft.Text("Sem dados oceânicos disponíveis para esta data.")
        else:
            col = ft.Column(scroll="auto", controls=[
                ft.Row([
                    ft.Icon(ft.Icons.WAVES, color=ft.Colors.BLUE_400),
                    ft.Text("Detalhes por Hora", size=16, weight="bold")
                ]),
                ft.Divider()
            ])
            for o in ondas_dia:
                col.controls.extend([
                    ft.Text(f"🕒 {o.get('hora', 'N/A')}"),
                    ft.Text(f"🌬️ Vento: {o.get('vento', 'N/A')} km/h - {o.get('direcao_vento_desc', 'N/A')}"),
                    ft.Text(f"🌊 Altura: {o.get('altura_onda', 'N/A')} m - {o.get('direcao_onda_desc', 'N/A')}"),
                    ft.Text(f"🌀 Agitação: {o.get('agitacao', 'N/A')}"),
                    ft.Divider()
                ])
            dialog.content = col

        dialog.open = True
        page.dialog = dialog  # ✅ Método correto para exibir diálogos no Flet
        page.update()

    # Dropdown de estados
    estado = ft.Dropdown(
        width=300,
        label="Selecione um estado",
        options=[ft.dropdown.Option(nome) for nome in df_estado["nome"].tolist()],
        on_change=on_estado_change
    )

    # Eventos dos componentes
    cidade.on_change = on_cidade_change
    botao_buscar = ft.ElevatedButton(text="Buscar Previsão do Tempo", on_click=buscar_codigo_cptec)

    # Layout da página
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


# Executa o app
ft.app(target=main)