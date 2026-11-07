import qrcode
import unicodedata
import re
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

# Diretório onde está o script
BASE_DIR = Path(__file__).resolve().parent

ARQUIVO_JSON = BASE_DIR / "presentes.json"
DIRETORIO_PIX = BASE_DIR / "pix"

def normalizar(texto, limite):
    """Remove acentos, converte para maiúsculas e limita o tamanho."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return texto.upper()[:limite]


def tlv(tag, valor):
    """Campo EMV: ID + tamanho (2 dígitos) + conteúdo."""
    valor = str(valor)

    if len(valor) > 99:
        raise ValueError(f"Campo {tag} excedeu 99 caracteres")

    return f"{tag}{len(valor):02d}{valor}"


def crc16(payload):
    """CRC-16/CCITT-FALSE, usado no BR Code Pix."""
    crc = 0xFFFF

    for byte in payload.encode("utf-8"):
        crc ^= byte << 8

        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

    return f"{crc:04X}"


def gerar_pix(
    chave,
    nome,
    cidade,
    valor=None,
    txid=None,
    descricao=None,
    arquivo="pix.png"
):
    # Dados do recebedor
    nome = normalizar(nome, 25)
    cidade = normalizar(cidade, 15)

    if not chave or not nome or not cidade:
        raise ValueError("Chave, nome e cidade são obrigatórios")

    if len(chave) > 77:
        raise ValueError("Chave Pix excede 77 caracteres")

    # Conta Pix: GUI + chave + descrição opcional
    conta_pix = (
        tlv("00", "br.gov.bcb.pix")
        + tlv("01", chave)
    )

    if descricao:
        descricao = normalizar(descricao, 60)
        conta_pix += tlv("02", descricao)

    # Campo 26: Merchant Account Information
    campo_pix = tlv("26", conta_pix)

    # Identificador da transação
    txid = txid or "***"

    if txid != "***":
        if not re.fullmatch(r"[A-Za-z0-9]{1,25}", txid):
            raise ValueError(
                "TXID deve ter 1-25 caracteres alfanuméricos"
            )

    campo_txid = tlv("62", tlv("05", txid))

    # Payload Pix estático
    payload = (
        tlv("00", "01")       # Payload Format Indicator
        + tlv("01", "11")     # QR reutilizável
        + campo_pix
        + tlv("52", "0000")  # Merchant Category
        + tlv("53", "986")   # BRL
    )

    # Valor opcional
    if valor is not None:
        try:
            valor = Decimal(str(valor))
        except InvalidOperation:
            raise ValueError("Valor inválido")

        if valor <= 0:
            raise ValueError("Valor deve ser maior que zero")

        if valor != valor.quantize(Decimal("0.01")):
            raise ValueError("Use no máximo duas casas decimais")

        payload += tlv("54", format(valor, ".2f"))

    payload += (
        tlv("58", "BR")
        + tlv("59", nome)
        + tlv("60", cidade)
        + campo_txid
    )

    # CRC: acrescenta o campo 6304 antes de calcular
    payload += "6304"
    payload += crc16(payload)

    # Gerar imagem QR
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(payload)
    qr.make(fit=True)

    imagem = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    imagem.save(arquivo)

    print("QR Code gerado:", arquivo)
    print()
    print("Pix Copia e Cola:")
    print(payload)

    return payload

def carregar_presentes():

    with open(
        ARQUIVO_JSON,
        "r",
        encoding="utf-8"
    ) as arquivo:

        dados = json.load(arquivo)

    return dados

def gerar_todos_pix():

    dados = carregar_presentes()

    pix = dados["pix"]

    DIRETORIO_PIX.mkdir(
        parents=True,
        exist_ok=True
    )

    for presente in dados["presentes"]:

        identificador = presente["id"]

        arquivo_qr = (
            DIRETORIO_PIX
            / f"qr_{identificador}.png"
        )

        payload = gerar_pix(
            chave=pix["chave"],
            nome=pix["nome"],
            cidade=pix["cidade"],
            valor=presente["valor"],
            txid=identificador.upper(),
            descricao=presente["nome"],
            arquivo=str(arquivo_qr)
        )

        presente["pix"] = payload

        print(
            f"Gerado: {arquivo_qr.name}"
        )

        # Salva os dados com os payloads
        with open(
            ARQUIVO_JSON,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                dados,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

if __name__ == "__main__":

    gerar_todos_pix()

