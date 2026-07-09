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

# ----------------------------
# Interface
# ----------------------------

with st.sidebar:
    st.header("Configuração")
    produto_manual = st.selectbox("Tipo de trabalho", PRODUTOS)
    cliente = st.text_input("Cliente", "")
    data_pedido = st.date_input("Data do pedido", value=date.today())

pedido = st.text_area(
    "Cole aqui o pedido do cliente",
    height=180,
    placeholder="Ex.: Lona 9m x 1,5m, ilhós a toda a volta, impressão digital..."
)

if pedido.strip():
    produto_detectado = identificar_produto(pedido)
    produto = produto_detectado if produto_manual == "Automático" else produto_manual

    modelos, por_modelo = extrair_modelos(pedido)
    formato = extrair_formato(pedido)
    largura_m, altura_m, area_unitaria = extrair_dimensoes_m2(formato)
    quantidade = extrair_quantidade(pedido)

    try:
        area_total = round(area_unitaria * int(quantidade), 3) if area_unitaria and quantidade else ""
    except:
        area_total = ""

    dados = {
        "produto": produto,
        "quantidade": quantidade,
        "modelos": modelos,
        "por_modelo": por_modelo,
        "formato": formato,
        "papel": extrair_papel(pedido),
        "cores": extrair_cores(pedido),
        "paginas": extrair_paginas(pedido),
        "acabamentos": extrair_acabamentos(pedido),
        "area_unitaria": area_unitaria,
        "area_total": area_total,
        "arte_final": "",
        "prazo": "",
        "entrega": "",
        "aplicacao": "",
        "revestimento": "",
        "acabamento_texto": "",
        "outros": "",
        "capa": "",
        "miolo_1": "",
        "miolo_2": "",
        "guardas": "",
        "forra": "",
        "embalagem": "",
        "subcontratacoes_detectadas": detetar_subcontratacao(pedido),
        "subcontratacao": ""
    }

    st.subheader("1. Pedido interpretado")

    col1, col2, col3 = st.columns(3)
    col1.metric("Produto", dados["produto"])
    col2.metric("Quantidade", dados["quantidade"] or "Por confirmar")
    col3.metric("Formato/medida", dados["formato"] or "Por confirmar")

    st.write("**Matéria-prima identificada:**", dados["papel"] or "Por confirmar")
    st.write("**Impressão/cores:**", dados["cores"] or "Por confirmar")
    st.write("**N.º de páginas:**", dados["paginas"] or "Não aplicável / por confirmar")
    st.write("**Acabamentos identificados:**", ", ".join(dados["acabamentos"]) if dados["acabamentos"] else "A confirmar")

    if dados["produto"] in ["Lona", "Vinil", "Roll-up", "PVC / Placa rígida"]:
        st.write("**Área unitária:**", f"{dados['area_unitaria']} m²" if dados["area_unitaria"] else "Por confirmar")
        st.write("**Área total:**", f"{dados['area_total']} m²" if dados["area_total"] else "Por confirmar")

    if dados["subcontratacoes_detectadas"]:
        st.error("Possível subcontratação detetada: " + ", ".join(dados["subcontratacoes_detectadas"]))

    st.subheader("2. Patamares de exigência ativados")

    exigencia = patamares_exigencia(produto)
    st.warning(exigencia["alerta"])

    cex1, cex2 = st.columns(2)
    cex1.metric("Complexidade", exigencia["complexidade"])
    cex2.metric("Risco de erro", exigencia["risco"])

    st.write("**Campos a confirmar antes de orçamentar:**")
    for campo in exigencia["campos"]:
        st.write(f"- {campo}")

    st.subheader("3. Confirmar ou corrigir dados")

    c1, c2 = st.columns(2)

    with c1:
        produto_final = st.selectbox("Produto", PRODUTOS[1:], index=PRODUTOS[1:].index(dados["produto"]) if dados["produto"] in PRODUTOS[1:] else 0)
        quantidade_final = st.text_input("Quantidade total", dados["quantidade"])
        modelos_final = st.text_input("N.º de modelos", dados["modelos"])
        por_modelo_final = st.text_input("Quantidade por modelo", dados["por_modelo"])
        formato_final = st.text_input("Formato/medida", dados["formato"])
        papel_final = st.text_input("Matéria-prima / papel / material", dados["papel"])
        paginas_final = st.text_input("N.º de páginas", dados["paginas"])

    with c2:
        cores_final = st.text_input("Impressão/cores", dados["cores"])
        revestimento = st.text_input("Revestimento", "")
        acabamento_texto = st.text_input("Acabamento", ", ".join(dados["acabamentos"]))
        arte_final = st.selectbox("Arte-final", ["", "Cliente fornece arte-final pronta", "Necessita adaptação", "Necessita criação"])
        prazo = st.text_input("Prazo de entrega", "")
        entrega = st.text_input("Entrega", "")

    aplicacao = ""
    if produto_final in ["Lona", "Vinil", "Roll-up", "PVC / Placa rígida"]:
        st.markdown("### Dados específicos para preço por m² / grande formato")
        g1, g2 = st.columns(2)

        with g1:
            area_unitaria_manual = st.text_input("Área unitária m²", str(dados["area_unitaria"]) if dados["area_unitaria"] else "")
            area_total_manual = st.text_input("Área total m²", str(dados["area_total"]) if dados["area_total"] else "")
            aplicacao = st.selectbox("Aplicação/instalação", ["", "Não inclui aplicação", "Inclui aplicação", "Confirmar aplicação"])

        with g2:
            tipo_preco = st.selectbox("Tipo de preço", ["Preço por m²", "Preço por unidade", "Confirmar"])
            transporte = st.text_input("Transporte", "")
    else:
        area_unitaria_manual = ""
        area_total_manual = ""
        tipo_preco = ""
        transporte = ""

    if produto_final == "Livro / Brochura / Catálogo":
        st.markdown("### Dados específicos para livro/brochura/catálogo")

        l1, l2 = st.columns(2)

        with l1:
            capa = st.text_input("Capa — papel, cores e acabamento", "")
            miolo_1 = st.text_input("Miolo 1 — papel, cores e páginas", "")
            miolo_2 = st.text_input("Miolo 2 — se existir papel/cores diferentes", "")
            guardas = st.selectbox("Guardas", ["", "Não tem", "Tem guardas — preencher no GGWEB"])

        with l2:
            forra = st.selectbox("Forra", ["", "Não tem", "Tem forra — preencher como componente/acabamento"])
            acabamento_livro = st.text_input("Acabamento do livro/brochura", acabamento_texto)
            embalagem = st.text_input("Tipo de embalagem", "")
            subcontratacao_livro = st.text_input("Subcontratações", "")

    else:
        capa = miolo_1 = miolo_2 = guardas = forra = embalagem = subcontratacao_livro = ""
        acabamento_livro = ""

    if produto_final == "Embalagem / Caixa":
        st.markdown("### Dados específicos para embalagem/caixa")

        e1, e2 = st.columns(2)

        with e1:
            formato_planificado = st.text_input("Formato planificado", formato_final)
            materia_caixa = st.text_input("Matéria-prima da caixa", papel_final)
            impressao_caixa = st.text_input("Impressão", cores_final)
            revestimento_caixa = st.text_input("Revestimento", revestimento)

        with e2:
            outros_caixa = st.text_input("Outro processo especial", ", ".join(dados["subcontratacoes_detectadas"]))
            acabamento_caixa = st.text_input("Acabamento da caixa", acabamento_texto)
            entrega_caixa = st.text_input("Entrega da caixa", entrega)
            subcontratacao_caixa = st.text_input("Subcontratação externa", ", ".join(dados["subcontratacoes_detectadas"]))

        formato_final = formato_planificado
        papel_final = materia_caixa
        cores_final = impressao_caixa
        revestimento = revestimento_caixa
        acabamento_texto = acabamento_caixa
        entrega = entrega_caixa
        outros = outros_caixa
        subcontratacao = subcontratacao_caixa

    else:
        outros = ""
        subcontratacao = subcontratacao_livro if produto_final == "Livro / Brochura / Catálogo" else ""

    dados_corrigidos = {
        "produto": produto_final,
        "quantidade": quantidade_final,
        "modelos": modelos_final,
        "por_modelo": por_modelo_final,
        "formato": formato_final,
        "papel": papel_final,
        "cores": cores_final,
        "paginas": paginas_final,
        "acabamentos": [a.strip() for a in acabamento_texto.split(",") if a.strip()],
        "arte_final": arte_final,
        "prazo": prazo,
        "entrega": entrega,
        "aplicacao": aplicacao,
        "revestimento": revestimento,
        "acabamento_texto": acabamento_texto,
        "outros": outros,
        "area_unitaria": area_unitaria_manual,
        "area_total": area_total_manual,
        "capa": capa,
        "miolo_1": miolo_1,
        "miolo_2": miolo_2,
        "guardas": guardas,
        "forra": forra,
        "embalagem": embalagem,
        "subcontratacoes_detectadas": dados["subcontratacoes_detectadas"],
        "subcontratacao": subcontratacao
    }

    equipamento = sugerir_equipamento(produto_final, quantidade_final)

    st.subheader("4. Informação em falta")
    faltas = perguntas_em_falta(dados_corrigidos)

    if faltas:
        for f in faltas:
            st.warning(f)
    else:
        st.success("Pedido com informação suficiente para preparar o guião GGWEB.")

    st.subheader("5. Descrição técnica para comunicação interna")

    descricao_estruturada = gerar_descricao_estruturada(dados_corrigidos)
    st.code(descricao_estruturada, language="text")

    st.subheader("6. Guião de preenchimento no GGWEB")

    st.markdown("### A. Descrição do trabalho")
    st.code(descricao_estruturada, language="text")

    st.markdown("### B. Pré-impressão")
    if arte_final == "Cliente fornece arte-final pronta":
        st.write("- Preencher apenas verificação/preparação de ficheiro para impressão.")
        st.write("- Usar tempo reduzido de operador para conferência técnica.")
    elif arte_final == "Necessita adaptação":
        st.write("- Preencher tempo de operador/design para adaptação da arte-final.")
        st.write("- Confirmar margens, sangrias, medidas, paginação e conteúdos.")
    elif arte_final == "Necessita criação":
        st.write("- Preencher tempo de criação gráfica.")
        st.write("- Valorizar separadamente da produção/impressão.")
    else:
        st.write("- Confirmar se a arte-final vem pronta para impressão.")
        st.write("- Sem esta informação, não fechar a pré-impressão.")

    st.markdown("### C. Impressão 1")
    st.write("- Usar para o suporte principal do trabalho.")
    st.write(f"- Produto/material: {dados_corrigidos['papel'] or 'por confirmar'}")
    st.write(f"- Quantidade: {dados_corrigidos['quantidade'] or 'por confirmar'}")
    st.write(f"- Formato/medida: {dados_corrigidos['formato'] or 'por confirmar'}")
    st.write(f"- Impressão/cores: {dados_corrigidos['cores'] or 'por confirmar'}")
    st.write(f"- Equipamento sugerido: {equipamento}")

    if produto_final in ["Lona", "Vinil", "Roll-up", "PVC / Placa rígida"]:
        st.write("- Considerar preço por m², salvo indicação contrária.")
        st.write(f"- Área unitária: {dados_corrigidos['area_unitaria'] or 'por confirmar'} m²")
        st.write(f"- Área total: {dados_corrigidos['area_total'] or 'por confirmar'} m²")
        st.write("- Preencher como impressão digital/grande formato.")

    if produto_final == "Embalagem / Caixa":
        st.write("- Confirmar se o equipamento é Offset, especialmente em quantidades iguais ou superiores a 1000.")
        st.write("- Preencher Pantone quando aplicável.")
        st.write("- Confirmar planos e folhas.")

    st.markdown("### D. Impressão 2")
    if produto_final == "Livro / Brochura / Catálogo" and miolo_2:
        st.write("- Usar Impressão 2 porque existe segundo miolo/papel/cores diferentes.")
        st.write(f"- Miolo 2: {miolo_2}")
    else:
        st.write("- Não preencher, salvo se existir segundo suporte, papel ou componente diferente.")

    st.markdown("### E. Outras tarefas")
    if dados_corrigidos["revestimento"]:
        st.write(f"- Revestimento: {dados_corrigidos['revestimento']}")
    if dados_corrigidos["acabamento_texto"]:
        st.write(f"- Acabamento: {dados_corrigidos['acabamento_texto']}")
    if produto_final == "Embalagem / Caixa":
        st.write("- Confirmar Corte/Vinco.")
        st.write("- Confirmar Colagem.")
    if produto_final in ["Lona", "Vinil", "Roll-up", "PVC / Placa rígida"]:
        st.write("- Confirmar corte final.")
        st.write("- Confirmar bainha/ilhós/laminação/aplicação, se aplicável.")

    st.markdown("### F. Subcontratações")
    if dados_corrigidos.get("subcontracao") or dados_corrigidos.get("subcontratacoes_detectadas"):
        st.error("Preencher subcontratação externa.")
        if dados_corrigidos.get("subcontracao"):
            st.write(f"- Subcontratação indicada: {dados_corrigidos['subcontracao']}")
        if dados_corrigidos.get("subcontratacoes_detectadas"):
            st.write(f"- Processos detetados: {', '.join(dados_corrigidos['subcontratacoes_detectadas'])}")
        st.write("- Confirmar fornecedor externo, custo, prazo e margem.")
    else:
        st.write("- Não preencher, salvo se alguma tarefa for feita por fornecedor externo.")

    st.markdown("### G. Entrega / Transporte / Instalação")
    st.write(f"- Entrega: {dados_corrigidos['entrega'] or 'por confirmar'}")
    if produto_final in ["Lona", "Vinil", "Roll-up", "PVC / Placa rígida"]:
        st.write(f"- Aplicação/instalação: {dados_corrigidos['aplicacao'] or 'por confirmar'}")

    st.markdown("### H. Recalcular")
    st.write("- Depois de preencher todas as secções, clicar em Recalcular no GGWEB.")

    st.subheader("7. Nota interna")
    st.info("Confirmar sempre com a produção quando houver materiais especiais, formatos fora do padrão, acabamentos pouco habituais, livros com vários componentes, grande formato, aplicação ou subcontratação externa.")

else:
    st.info("Cole o pedido do cliente para gerar o guião GGWEB.")
