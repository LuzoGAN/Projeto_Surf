function atualizarCidades() {
    const estado = document.getElementById("estado").value;
    fetch("/buscar-cidade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estado: estado })
    })
    .then(response => response.json())
    .then(cidades => {
        const cidadeSelect = document.getElementById("cidade");
        cidadeSelect.innerHTML = "";
        cidades.forEach(cidade => {
            const option = document.createElement("option");
            option.value = cidade;
            option.textContent = cidade;
            cidadeSelect.appendChild(option);
        });
    });
}

function limparPrevisao() {
    document.getElementById("resultado").innerHTML = "";
}

function buscarPrevisao() {
    const cidade = document.getElementById("cidade").value;
    fetch("/buscar-dados", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cidade: cidade })
    })
    .then(response => response.json())
    .then(data => {
        if (data.erro) {
            document.getElementById("resultado").innerHTML = `<div class="alert alert-danger">${data.erro}</div>`;
            return;
        }

        let html = `<h3>Previsão para os próximos 6 dias:</h3><div class="row">`;

        data.previsao.forEach(dia => {
            html += `
            <div class="col-md-4 mb-3">
                <div class="card" onclick="mostrarOndas('${dia.data}')">
                    <div class="card-body">
                        <h5 class="card-title">📅 ${dia.data}</h5>
                        <p class="card-text">
                            ☀️ ${dia.condicao_desc}<br>
                            🌡️ Min: ${dia.min}°C | Max: ${dia.max}°C<br>
                            🔆 Índice UV: ${dia.indice_uv}
                        </p>
                    </div>
                </div>
            </div>`;
        });

        html += "</div>";
        document.getElementById("resultado").innerHTML = html;
        window.dadosOndas = data.ondas; // Armazena dados para uso no modal
    });
}

function mostrarOndas(dataSelecionada) {
    if (!window.dadosOndas || window.dadosOndas.length === 0) {
        document.getElementById("conteudoModal").innerHTML = "Nenhum dado oceânico disponível.";
        new bootstrap.Modal(document.getElementById("modalOndas")).show();
        return;
    }

    const ondasDia = window.dadosOndas.filter(o => o.data === dataSelecionada);

    if (!ondasDia.length) {
        document.getElementById("conteudoModal").innerHTML = "Sem dados oceânicos para esta data.";
    } else {
        let html = `<h6>Dados por Hora</h6><hr>`;
        ondasDia.forEach(o => {
            html += `
            <p class="mb-2">
                🕒 ${o.hora}<br>
                🌬️ Vento: ${o.vento} km/h - ${o.direcao_vento_desc}<br>
                🌊 Altura: ${o.altura_onda} m - ${o.direcao_onda_desc}<br>
                🌀 Agitação: ${o.agitacao}
            </p>
            <hr>`;
        });
        document.getElementById("conteudoModal").innerHTML = html;
    }

    new bootstrap.Modal(document.getElementById("modalOndas")).show();
}