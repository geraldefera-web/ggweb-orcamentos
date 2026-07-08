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
    "Lona",
    "Vinil",
    "Revista / Brochura",
    "Roll-up",
    "Outro"
]

def normalizar(texto):
    return texto.lower().replace(",", ".").replace("×", "x")

def identificar_produto(texto):
    t = normalizar(texto)
    if any(x in t for x in ["flyer", "panfleto", "folheto"]):
        return "Flyer / Panfleto"
    if any(x in t for x in ["cartão", "cartao", "visita"]):
        return "Cartões de visita"
    if "cartaz" in t or "poster" in t:
        return "Cartaz"
    if "lona" in t or "banner" in t:
        return "Lona"
    if "vinil" in t or "autocolante" in t:
        return "Vinil"
    if any(x in t for x in ["revista", "brochura", "catálogo", "catalogo"]):
        return "Revista / Brochura"
    if any(x in t for x in ["roll-up", "roll up", "rollup"]):
        return "Roll-up"
    return "Outro"

def extrair_quantidade(texto):
    t = normalizar(texto)
    padrao = re.search(r"(\d{2,6})\s*(unidades|unds|unid|exemplares|flyers|folhetos|cartazes|cartões|cartoes)", t)
    if padrao:
        return padrao.group(1)
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

    formatos_padrao = ["a7", "a6", "a5", "a4", "a3", "a2", "a1", "a0"]
    for f in formatos_padrao:
        if re.search(rf"\b{f}\b", t):
            return f.upper()

    m = re.search(r"(\d{2,4}(?:\.\d+)?)\s*(mm|cm|m)?\s*x\s*(\d{2,4}(?:\.\d+)?)\s*(mm|cm|m)?", t)
    if m:
        n1 = m.group(1).replace(".", ",")
        n2 = m.group(3).replace(".", ",")
        unidade = m.group(2) or m.group(4) or "mm"
        return f"{n1} x {n2} {unidade}"

    return ""

def aproximar_formato(formato):
    f = formato.lower().replace(" ", "")
    if "105x147" in f or "105x148" in f:
        return "A6 aproximado"
    if "148x210" in f or "147x210" in f:
        return "A5 aproximado"
    if "210x297" in f:
        return "A4"
    if "297x420" in f:
        return "A3"
    return ""

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

    if "frente e verso" in t or "2 lados" in t:
        return "4/4 cores a confirmar"
    if "1 face" in t or "só frente" in t or "so frente" in t:
        return "4/0 cores a confirmar"
    if "cores" in t or "cor" in t:
        return "A cores — confirmar 4/0 ou 4/4"
    return ""

def extrair_acabamentos(texto):
    t = normalizar(texto)
    acabamentos = []

    if "plastificado mate" in t or "plastificação mate" in t or "plastificacao mate" in t:
        if "1 face" in t:
            acabamentos.append("Plastificação mate 1 face")
        else:
            acabamentos.append("Plastificação mate")
    elif "plastificado" in t or "plastificação" in t or "plastificacao" in t:
        acabamentos.append("Plastificação — confirmar tipo e faces")

    if "dobra" in t or "dobrado" in t or "vinco" in t:
        acabamentos.append("Dobra / vinco")
    if "agrafo" in t or "agrafado" in t:
        acabamentos.append("Agrafo")
    if "ilhós" in t or "ilhos" in t:
        acabamentos.append("Ilhós")
    if "bainha" in t:
        acabamentos.append("Bainha")
    if "corte especial" in t or "corte forma" in t:
        acabamentos.append("Corte especial")

    return acabamentos

def perguntas_em_falta(dados):
    perguntas = []

    if not dados["formato"]:
        perguntas.append("Qual é o formato final?")
    if not dados["quantidade"]:
        perguntas.append("Qual é a quantidade total?")
    if not dados["papel"]:
        perguntas.append("Qual é o papel/material e gramagem?")
    if not dados["cores"]:
        perguntas.append("A impressão é 4/0, 4/4, 4/1 ou 4/2?")
    if not dados["arte_final"]:
        perguntas.append("O cliente fornece arte-final pronta para impressão?")
    if not dados["prazo"]:
        perguntas.append("Existe prazo de entrega obrigatório?")
    if dados["acabamentos"] == []:
        perguntas.append("Leva algum acabamento além do corte normal?")

    return perguntas

with st.sidebar:
    st.header("Configuração")
    produto_manual = st.selectbox("Tipo de trabalho", PRODUTOS)
    cliente = st.text_input("Cliente", "")
    data_pedido = st.date_input("Data do pedido", value=date.today())

pedido = st.text_area(
    "Cole aqui o pedido do cliente",
    height=170,
    placeholder="Ex.: Flyers couché mate 350 grs, formato 105 mm x 147 mm, 4/2 cores, plastificado mate 1 face, 500 unidades..."
)

if pedido.strip():
    produto_detectado = identificar_produto(pedido)
    produto = produto_detectado if produto_manual == "Automático" else produto_manual

    modelos, por_modelo = extrair_modelos(pedido)

    dados = {
        "produto": produto,
        "quantidade": extrair_quantidade(pedido),
        "modelos": modelos,
        "por_modelo": por_modelo,
        "formato": extrair_formato(pedido),
        "formato_aprox": aproximar_formato(extrair_formato(pedido)),
        "papel": extrair_papel(pedido),
        "cores": extrair_cores(pedido),
        "acabamentos": extrair_acabamentos(pedido),
        "arte_final": "",
        "prazo": ""
    }

    st.subheader("1. Pedido interpretado")

    col1, col2, col3 = st.columns(3)
    col1.metric("Produto", dados["produto"])
    col2.metric("Quantidade", dados["quantidade"] or "Por confirmar")
    col3.metric("Formato", dados["formato"] or "Por confirmar")

    st.write("**Formato aproximado:**", dados["formato_aprox"] or "Não aplicável")
    st.write("**Papel/material:**", dados["papel"] or "Por confirmar")
    st.write("**Impressão/cores:**", dados["cores"] or "Por confirmar")
    st.write("**Acabamentos:**", ", ".join(dados["acabamentos"]) if dados["acabamentos"] else "A confirmar")

    st.subheader("2. Confirmar ou corrigir dados")

    c1, c2 = st.columns(2)

    with c1:
        produto_final = st.selectbox("Produto", PRODUTOS[1:], index=PRODUTOS[1:].index(dados["produto"]) if dados["produto"] in PRODUTOS[1:] else 0)
        quantidade_final = st.text_input("Quantidade total", dados["quantidade"])
        modelos_final = st.text_input("N.º de modelos", dados["modelos"])
        por_modelo_final = st.text_input("Quantidade por modelo", dados["por_modelo"])
        formato_final = st.text_input("Formato final", dados["formato"])
        papel_final = st.text_input("Papel/material", dados["papel"])

    with c2:
        cores_final = st.text_input("Impressão/cores", dados["cores"])
        acabamentos_final = st.text_area("Acabamentos", ", ".join(dados["acabamentos"]))
        arte_final = st.selectbox("Arte-final", ["Por confirmar", "Cliente fornece arte-final pronta", "Necessita adaptação", "Necessita criação"])
        prazo = st.text_input("Prazo de entrega", "")
        observacoes = st.text_area("Observações internas", "")

    dados_corrigidos = {
        "produto": produto_final,
        "quantidade": quantidade_final,
        "modelos": modelos_final,
        "por_modelo": por_modelo_final,
        "formato": formato_final,
        "papel": papel_final,
        "cores": cores_final,
        "acabamentos": [a.strip() for a in acabamentos_final.split(",") if a.strip()],
        "arte_final": arte_final,
        "prazo": prazo
    }

    st.subheader("3. Informação em falta")

    faltas = perguntas_em_falta(dados_corrigidos)
    if faltas:
        for f in faltas:
            st.warning(f)
    else:
        st.success("Pedido com informação suficiente para preparar o guião GGWEB.")

    st.subheader("4. Linguagem técnica de gráfica")

    descricao_tecnica = (
        f"{dados_corrigidos['quantidade']} unidades de {dados_corrigidos['produto']}, "
        f"formato {dados_corrigidos['formato']}, "
        f"em {dados_corrigidos['papel']}, "
        f"impressão {dados_corrigidos['cores']}"
    )

    if dados_corrigidos["modelos"]:
        descricao_tecnica += f", {dados_corrigidos['modelos']} modelos"
    if dados_corrigidos["por_modelo"]:
        descricao_tecnica += f" x {dados_corrigidos['por_modelo']} unidades"
    if dados_corrigidos["acabamentos"]:
        descricao_tecnica += f", acabamento: {', '.join(dados_corrigidos['acabamentos'])}"

    st.code(descricao_tecnica, language="text")

    st.subheader("5. Guião de preenchimento no GGWEB")

    st.markdown("### A. Descrição do trabalho")
    st.code(descricao_tecnica, language="text")

    st.markdown("### B. Pré-impressão")
    if arte_final == "Cliente fornece arte-final pronta":
        st.write("Preencher apenas verificação/preparação de ficheiro para impressão.")
        st.write("Sugestão: tempo reduzido de operador, apenas para conferência técnica.")
    elif arte_final == "Necessita adaptação":
        st.write("Preencher tempo de operador/design para adaptação da arte-final.")
        st.write("Confirmar se é apenas ajuste de medidas, margens, sangrias ou alteração de conteúdos.")
    elif arte_final == "Necessita criação":
        st.write("Preencher tempo de criação gráfica.")
        st.write("Este ponto deve ser valorizado separadamente da impressão.")
    else:
        st.write("Confirmar se a arte-final vem pronta para impressão.")
        st.write("Sem esta informação, não é seguro fechar a pré-impressão.")

    st.markdown("### C. Impressão 1")
    st.write("Usar para o suporte principal do trabalho.")
    st.write(f"- Produto/material: {dados_corrigidos['papel'] or 'por confirmar'}")
    st.write(f"- Quantidade: {dados_corrigidos['quantidade'] or 'por confirmar'}")
    st.write(f"- Formato final: {dados_corrigidos['formato'] or 'por confirmar'}")
    st.write(f"- Cores: {dados_corrigidos['cores'] or 'por confirmar'}")
    if dados_corrigidos["modelos"]:
        st.write(f"- Modelos: {dados_corrigidos['modelos']} modelos")
    if dados_corrigidos["por_modelo"]:
        st.write(f"- Quantidade por modelo: {dados_corrigidos['por_modelo']} unidades")
    st.write("- Corte: considerar corte final ao formato indicado.")

    st.markdown("### D. Impressão 2")
    if dados_corrigidos["produto"] == "Revista / Brochura":
        st.write("Usar apenas se capa e miolo tiverem papéis diferentes.")
    else:
        st.write("Não preencher, salvo se existir um segundo suporte/papel diferente.")

    st.markdown("### E. Outras tarefas")
    if dados_corrigidos["acabamentos"]:
        for a in dados_corrigidos["acabamentos"]:
            st.write(f"- Selecionar/adicionar: {a}")
    else:
        st.write("- Confirmar se existe apenas corte normal ou algum acabamento adicional.")

    st.markdown("### F. Subcontratações")
    st.write("Preencher apenas se alguma tarefa for externa: plastificação externa, aplicação, transporte, estrutura, acabamento especial ou outro fornecedor.")

    st.markdown("### G. Recalcular")
    st.write("Depois de preencher descrição, pré-impressão, impressão, outras tarefas e subcontratações, clicar em Recalcular no GGWEB.")

    st.subheader("6. Nota interna")
    st.info("Este guião serve para apoiar o preenchimento. Confirmar sempre com a produção quando houver materiais especiais, formatos fora do padrão, acabamentos pouco habituais ou prazos urgentes.")

else:
    st.info("Cole o pedido do cliente para gerar o guião GGWEB.")
