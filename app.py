import streamlit as st
import re
from datetime import date

st.set_page_config(page_title="Assistente GGWEB - Orçamentos", layout="wide")

st.title("Assistente de Orçamentos GGWEB")
st.caption("Tradutor de pedidos de clientes para linguagem técnica de gráfica e guião GGWEB.")

PRODUTOS = [
    "Automático",
    "Cartões de visita",
    "Flyer / Panfleto",
    "Cartaz",
    "Livro / Brochura / Catálogo",
    "Lona",
    "Vinil",
    "Roll-up",
    "PVC / Placa rígida",
    "Embalagem / Caixa",
    "Outro"
]

def normalizar(texto):
    return texto.lower().replace(",", ".").replace("×", "x")

def identificar_produto(texto):
    t = normalizar(texto)
    if any(x in t for x in ["caixa", "embalagem", "packaging"]):
        return "Embalagem / Caixa"
    if any(x in t for x in ["livro", "brochura", "catálogo", "catalogo", "revista", "publicação", "publicacao"]):
        return "Livro / Brochura / Catálogo"
    if any(x in t for x in ["lona", "banner", "faixa"]):
        return "Lona"
    if any(x in t for x in ["vinil", "autocolante", "sticker", "easydot"]):
        return "Vinil"
    if any(x in t for x in ["flyer", "panfleto", "folheto"]):
        return "Flyer / Panfleto"
    if any(x in t for x in ["cartão", "cartao", "visita"]):
        return "Cartões de visita"
    if "cartaz" in t or "poster" in t:
        return "Cartaz"
    if any(x in t for x in ["roll-up", "roll up", "rollup"]):
        return "Roll-up"
    if any(x in t for x in ["pvc", "placa"]):
        return "PVC / Placa rígida"
    return "Outro"

def extrair_quantidade(texto):
    t = normalizar(texto)
    m = re.search(r"(\d{1,6})\s*(unidades|unds|unid|exemplares|livros|flyers|folhetos|cartazes|cartões|cartoes|lonas|vinis|caixas)", t)
    if m:
        return m.group(1)
    nums = re.findall(r"\b\d{2,6}\b", t)
    return nums[-1] if nums else ""

def extrair_modelos(texto):
    t = normalizar(texto)
    m = re.search(r"(\d+)\s*modelos?", t)
    modelos = m.group(1) if m else ""
    q = re.search(r"(\d+)\s*modelos?\s*x\s*(\d+)", t)
    por_modelo = q.group(2) if q else ""
    return modelos, por_modelo

def extrair_formato(texto):
    t = normalizar(texto)

    for f in ["a7", "a6", "a5", "a4", "a3", "a2", "a1", "a0"]:
        if re.search(rf"\b{f}\b", t):
            return f.upper()

    m = re.search(r"(\d{1,4}(?:\.\d+)?)\s*(mm|cm|m)?\s*x\s*(\d{1,4}(?:\.\d+)?)\s*(mm|cm|m)?", t)
    if m:
        n1 = m.group(1).replace(".", ",")
        n2 = m.group(3).replace(".", ",")
        unidade = m.group(2) or m.group(4) or "mm"
        return f"{n1} x {n2} {unidade}"

    return ""

def extrair_dimensoes_m2(formato):
    if not formato:
        return "", "", ""

    f = formato.lower().replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)", f)

    if not m:
        return "", "", ""

    largura = float(m.group(1))
    altura = float(m.group(2))
    unidade = m.group(3)

    if unidade == "mm":
        largura_m = largura / 1000
        altura_m = altura / 1000
    elif unidade == "cm":
        largura_m = largura / 100
        altura_m = altura / 100
    else:
        largura_m = largura
        altura_m = altura

    area = largura_m * altura_m

    return round(largura_m, 3), round(altura_m, 3), round(area, 3)

def extrair_papel(texto):
    t = normalizar(texto)
    gramagem = re.search(r"(\d{2,3})\s*(grs|gr|g|gsm)", t)
    gram = f"{gramagem.group(1)} g" if gramagem else ""

    tipo = ""
    if "couche" in t or "couché" in t:
        tipo = "Couché"
    if "mate" in t:
        tipo = f"{tipo} mate".strip()
    if "brilho" in t:
        tipo = f"{tipo} brilho".strip()
    if "offset" in t:
        tipo = "Offset"
    if "cartolina" in t:
        tipo = "Cartolina"
    if "lona" in t:
        tipo = "Lona PVC"
    if "vinil" in t:
        tipo = "Vinil"
    if "easydot" in t:
        tipo = "Vinil EasyDot"

    if tipo and gram:
        return f"{tipo} {gram}"
    if tipo:
        return tipo
    if gram:
        return gram
    return ""

def extrair_cores(texto):
    t = normalizar(texto)
    m = re.search(r"\b([124])\s*/\s*([124])\b", t)
    if m:
        return f"{m.group(1)}/{m.group(2)} cores"
    if "pantone" in t:
        return "Pantone — confirmar referência"
    if "frente e verso" in t or "2 lados" in t:
        return "4/4 cores a confirmar"
    if "1 face" in t or "só frente" in t or "so frente" in t:
        return "4/0 cores a confirmar"
    if "cores" in t or "cor" in t:
        return "A cores — confirmar 4/0, 4/1, 4/2 ou 4/4"
    return ""

def extrair_paginas(texto):
    t = normalizar(texto)
    m = re.search(r"(\d{1,4})\s*(páginas|paginas|pags|págs|pp)", t)
    return m.group(1) if m else ""

def extrair_acabamentos(texto):
    t = normalizar(texto)
    acabamentos = []

    if "plastificado mate" in t or "plastificação mate" in t or "plastificacao mate" in t:
        acabamentos.append("Plastificação mate 1 face" if "1 face" in t else "Plastificação mate")
    elif "plastificação brilho" in t or "plastificacao brilho" in t:
        acabamentos.append("Plastificação brilho")
    elif "plastificado" in t or "plastificação" in t or "plastificacao" in t:
        acabamentos.append("Plastificação — confirmar tipo e faces")

    if "laminação mate" in t or "laminacao mate" in t:
        acabamentos.append("Laminação mate")
    elif "laminação" in t or "laminacao" in t:
        acabamentos.append("Laminação — confirmar tipo")

    if "dobra" in t or "dobrado" in t or "vinco" in t:
        acabamentos.append("Dobra / vinco")
    if "agrafo" in t or "agrafado" in t:
        acabamentos.append("Agrafo")
    if "cola" in t or "pur" in t or "lombada" in t:
        acabamentos.append("Cola / lombada")
    if "forra" in t:
        acabamentos.append("Forra")
    if "guardas" in t:
        acabamentos.append("Guardas")
    if "ilhós" in t or "ilhos" in t:
        acabamentos.append("Ilhós")
    if "bainha" in t:
        acabamentos.append("Bainha")
    if "corte/vinco" in t or "corte vinco" in t:
        acabamentos.append("Corte/Vinco")
    elif "corte especial" in t or "corte forma" in t:
        acabamentos.append("Corte especial")
    if "colagem" in t:
        acabamentos.append("Colagem")

    return acabamentos
