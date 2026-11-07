let presentes = [];
let dadosPix = {};
let presenteSelecionado = null;


function formatarValor(valor) {

    return valor.toLocaleString(
        "pt-BR",
        {
            style: "currency",
            currency: "BRL"
        }
    );

}

function renderizarPresentes() {

    const lista = document.getElementById("listaPresentes");

    lista.innerHTML = "";

    presentes.forEach(presente => {

        const card = document.createElement("article");

        card.className = "presente";

        card.innerHTML = `
            <img
                src="${presente.imagem}"
                alt="${presente.nome}"
            >

            <div class="presente-conteudo">

                <h2>${presente.nome}</h2>

                <p>${presente.descricao}</p>

                <div class="valor">
                    ${formatarValor(presente.valor)}
                </div>

                <button
                    class="btn-principal"
                    data-presente="${presente.id}"
                >
                    Presentear
                </button>

            </div>
        `;

        lista.appendChild(card);

    });
}

async function carregarPresentes() {

    const resposta = await fetch("presentes.json");

    if (!resposta.ok) {

        throw new Error(
            "Não foi possível carregar os presentes"
        );

    }

    const dados = await resposta.json();

    dadosPix = dados.pix;
    presentes = dados.presentes;

    renderizarPresentes();

}



document.addEventListener(
    "DOMContentLoaded",
    function() {

        // Carrega os presentes

        carregarPresentes().catch(erro => {
            console.error(erro);
        });


        // Configura os botões

        document.getElementById(
            "listaPresentes"
        ).addEventListener("click", function(event) {

            const botao = event.target.closest(
                "[data-presente]"
            );

            if (!botao) {
                return;
            }

            abrirPix(botao.dataset.presente);

        });

    }
);

// Abre o popup


function abrirPix(id) {

    // 1. Busca o presente selecionado no JSON

    const presente = presentes.find(
        item => item.id === id
    );

    if (!presente) {
        return;
    }

    // 2. Guarda o presente selecionado

    presenteSelecionado = presente;


    // 3. Atualiza o título do popup

    document.getElementById("modalTitulo").textContent =
        presente.nome;


    // 4. Atualiza o valor

    document.querySelector(".modal-valor").textContent =
        formatarValor(presente.valor);


    // 5. Atualiza o QR Code

    const qrCode = document.getElementById("qrCode");

    qrCode.src = `pix/qr_${presente.id}.png`;

    qrCode.alt =
        `QR Code Pix de ${formatarValor(presente.valor)}`;


    // 6. Atualiza o destinatário usando o JSON

    document.getElementById("destinatario").textContent =
        dadosPix.nome;


    // 7. Limpa mensagens anteriores

    document.getElementById("mensagem").textContent = "";


    // 8. Abre o popup

    document.getElementById("modalPix").classList.add(
        "aberto"
    );

    document.body.style.overflow = "hidden";

}


// Fecha o popup

function fecharPix() {

    const modal = document.getElementById("modalPix");

    modal.classList.remove("aberto");

    document.body.style.overflow = "";

}


// Fecha ao clicar no fundo

function fecharFundo(event) {

    if (event.target.id === "modalPix") {

        fecharPix();

    }

}


// Fecha pressionando Esc

document.addEventListener("keydown", function(event) {

    if (event.key === "Escape") {

        fecharPix();

    }

});


// Copia o Pix Copia e Cola


async function copiarPix() {

    if (!presenteSelecionado) {
        return;
    }

    const mensagem = document.getElementById("mensagem");

    if (!presenteSelecionado.pix) {

        mensagem.textContent =
            "Pix não disponível para este presente.";

        return;

    }

    try {

        await navigator.clipboard.writeText(
            presenteSelecionado.pix
        );

        mensagem.textContent =
            "Pix Copia e Cola copiado!";

    } catch (erro) {

        mensagem.textContent =
            "Não foi possível copiar o Pix.";

        console.error(erro);

    }

}

