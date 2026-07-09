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

def detetar_subcontratacao(texto):
    t = normalizar(texto)
    palavras = [
        "termo-estampagem",
        "termo estampagem",
        "hot stamping",
        "stamping",
        "verniz uv",
        "uv localizado",
        "relevo",
        "cunho",
        "gravação",
        "gravacao",
        "corte laser",
        "aplicação externa",
        "aplicacao externa",
        "fornecedor externo"
    ]

    encontrados = [p for p in palavras if p in t]
    return encontrados

def sugerir_equipamento(produto, quantidade):
    try:
        qtd = int(quantidade)
    except:
        qtd = 0

    if produto in ["Lona", "Vinil", "Roll-up", "PVC / Placa rígida"]:
        return "Impressão digital / grande formato"

    if qtd >= 1000:
        return "Offset recomendado"

    if qtd > 0:
        return "Impressão digital recomendada"

    return "Por definir após confirmação da quantidade"

def patamares_exigencia(produto):
    if produto == "Livro / Brochura / Catálogo":
        return {
            "complexidade": "Alta",
            "risco": "Elevado",
            "alerta": "Pedido identificado como livro/brochura/catálogo. Confirmar estrutura, capa, miolo, guardas, forra, acabamento, embalagem e possível segundo miolo.",
            "campos": [
                "Quantidade",
                "Formato aberto e formato fechado, se aplicável",
                "N.º de páginas",
                "Capa: papel, cores e acabamento",
                "Miolo 1: papel, cores, páginas e planos",
                "Miolo 2: se existir papel/cores diferentes",
                "Guardas",
                "Forra",
                "Pantones",
                "Equipamento: digital ou offset",
                "Acabamento: agrafo, cola, lombada, corte, plastificação",
                "Tipo de embalagem",
                "Subcontratações"
            ]
        }

    if produto in ["Lona", "Vinil", "Roll-up", "PVC / Placa rígida"]:
        return {
            "complexidade": "Média",
            "risco": "Médio",
            "alerta": "Pedido de grande formato/preço por m². Confirmar medidas, quantidade, área total, material, acabamento, aplicação e transporte.",
            "campos": [
                "Quantidade",
                "Largura",
                "Altura",
                "Área unitária em m²",
                "Área total em m²",
                "Material",
                "Impressão",
                "Revestimento/laminação, se aplicável",
                "Acabamento",
                "Aplicação/instalação",
                "Entrega/transporte"
            ]
        }

    if produto == "Embalagem / Caixa":
        return {
            "complexidade": "Alta",
            "risco": "Elevado",
            "alerta": "Pedido identificado como embalagem/caixa. Confirmar formato planificado, matéria-prima, impressão, revestimento, corte/vinco, colagem e eventuais subcontratações.",
            "campos": [
                "Quantidade",
                "Formato planificado",
                "Matéria-prima",
                "Impressão",
                "Pantones",
                "Revestimento",
                "Outros processos",
                "Corte/Vinco",
                "Colagem",
                "Entrega",
                "Subcontratação externa"
            ]
        }

    return {
        "complexidade": "Normal",
        "risco": "Baixo/Médio",
        "alerta": "Pedido de produção gráfica simples. Confirmar formato, quantidade, papel, cores, arte-final e acabamento.",
        "campos": [
            "Quantidade",
            "Formato",
            "Papel/material",
            "Cores",
            "Arte-final",
            "Acabamentos",
            "Prazo"
        ]
    }

def gerar_descricao_estruturada(dados):
    linhas = []

    linhas.append(f"Produto: {dados.get('produto') or '[por confirmar]'}")

    if dados.get("quantidade"):
        linhas.append(f"Quantidade: {dados.get('quantidade')} unidades")
    else:
        linhas.append("Quantidade: [por confirmar]")

    if dados.get("formato"):
        if dados.get("produto") == "Embalagem / Caixa":
            linhas.append(f"Formato planificado: {dados.get('formato')}")
        else:
            linhas.append(f"Formato/medida: {dados.get('formato')}")
    else:
        linhas.append("Formato/medida: [por confirmar]")

    if dados.get("area_total"):
        linhas.append(f"Área total: {dados.get('area_total')} m²")

    if dados.get("papel"):
        linhas.append(f"Matéria-prima: {dados.get('papel')}")
    else:
        linhas.append("Matéria-prima: [por confirmar]")

    if dados.get("cores"):
        linhas.append(f"Impressão: {dados.get('cores')}")
    else:
        linhas.append("Impressão: [por confirmar]")

    if dados.get("revestimento"):
        linhas.append(f"Revestimento: {dados.get('revestimento')}")
    elif any("plastificação" in a.lower() or "laminação" in a.lower() for a in dados.get("acabamentos", [])):
        revest = [a for a in dados.get("acabamentos", []) if "plastificação" in a.lower() or "laminação" in a.lower()]
        linhas.append(f"Revestimento: {', '.join(revest)}")
    else:
        linhas.append("Revestimento: [não indicado / não aplicável]")

    outros = []
    if dados.get("subcontratacoes_detectadas"):
        outros.extend(dados.get("subcontratacoes_detectadas"))
    if dados.get("outros"):
        outros.append(dados.get("outros"))

    if outros:
        linhas.append(f"Outro: {', '.join(outros)}")

    acabamento = dados.get("acabamento_texto") or ", ".join(dados.get("acabamentos", []))
    if acabamento:
        linhas.append(f"Acabamento: {acabamento}")
    else:
        linhas.append("Acabamento: [confirmar se apenas corte normal]")

    if dados.get("entrega"):
        linhas.append(f"Entrega: {dados.get('entrega')}")
    else:
        linhas.append("Entrega: [por confirmar]")

    return "\n".join(linhas)

def perguntas_em_falta(dados):
    perguntas = []

    campos_base = [
        ("quantidade", "Qual é a quantidade total?"),
        ("formato", "Qual é o formato/medida final?"),
        ("papel", "Qual é a matéria-prima/papel/material?"),
        ("cores", "Qual é o tipo de impressão? 4/0, 4/4, 4/2, Pantone ou digital?"),
        ("arte_final", "O cliente fornece arte-final pronta para impressão?"),
        ("entrega", "Qual é a forma de entrega? Levantamento, entrega na Selecor, transporte ou instalação?")
    ]

    for campo, pergunta in campos_base:
        if not dados.get(campo):
            perguntas.append(pergunta)

    if dados["produto"] in ["Lona", "Vinil", "Roll-up", "PVC / Placa rígida"]:
        if not dados.get("area_total"):
            perguntas.append("Confirmar largura, altura e quantidade para cálculo de m².")
        if not dados.get("acabamento_texto") and not dados.get("acabamentos"):
            perguntas.append("Qual é o acabamento? Corte, bainha, ilhós, laminação, aplicação?")
        if not dados.get("aplicacao"):
            perguntas.append("Inclui aplicação/instalação?")

    if dados["produto"] == "Livro / Brochura / Catálogo":
        livro_campos = [
            ("paginas", "Quantas páginas tem?"),
            ("capa", "A capa tem papel, cores ou acabamento próprio?"),
            ("miolo_1", "Qual é o papel, cores e páginas do miolo principal?"),
            ("guardas", "Tem guardas?"),
            ("forra", "Tem forra?"),
            ("embalagem", "Qual é o tipo de embalagem?"),
        ]
        for campo, pergunta in livro_campos:
            if not dados.get(campo):
                perguntas.append(pergunta)

    if dados["produto"] == "Embalagem / Caixa":
        caixa_campos = [
            ("revestimento", "Tem revestimento/plastificação?"),
            ("acabamento_texto", "Qual é o acabamento? Corte/Vinco, colagem, dobra?"),
            ("outros", "Existe algum processo especial, como termo-estampagem ou verniz UV?"),
        ]
        for campo, pergunta in caixa_campos:
            if not dados.get(campo):
                perguntas.append(pergunta)

    return perguntas
