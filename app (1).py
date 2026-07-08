import streamlit as st
import re
from datetime import date

st.set_page_config(page_title="Assistente GGWEB - Orçamentos", layout="wide")

st.title("Assistente de Orçamentos GGWEB")
st.caption("Ferramenta de apoio à análise de pedidos de orçamento para gráfica.")

# ----------------------------
# Base simples de produtos
# ----------------------------
PRODUTOS = {
    "Cartões de visita": {
        "keywords": ["cartão", "cartoes", "cartões", "visita", "business card"],
        "formato": "85x55 mm ou 90x50 mm",
        "papel": "Couché 350g / Cartolina 350g",
        "impressao": "4/4 cores se frente e verso; 4/0 se apenas frente",
        "acabamentos": ["Corte", "Plastificação opcional", "Cantos redondos opcional"],
        "perguntas": ["Qual o formato final?", "Frente apenas ou frente e verso?", "Com ou sem plastificação?", "O cliente fornece arte-final?"],
    },
    "Flyer / Panfleto": {
        "keywords": ["flyer", "panfleto", "folheto", "a5", "a6", "a4"],
        "formato": "A6, A5, A4 ou formato personalizado",
        "papel": "Couché 135g / 170g",
        "impressao": "4/0 ou 4/4 cores",
        "acabamentos": ["Corte", "Dobra se aplicável"],
        "perguntas": ["Qual o formato final?", "Quantas unidades?", "Frente apenas ou frente e verso?", "Qual a gramagem do papel?", "Tem dobra?"],
    },
    "Cartaz": {
        "keywords": ["cartaz", "poster", "a3", "a2", "mupi"],
        "formato": "A3, A2, A1 ou formato personalizado",
        "papel": "Couché 170g / 200g ou outro",
        "impressao": "4/0 cores, normalmente só frente",
        "acabamentos": ["Corte", "Plastificação opcional"],
        "perguntas": ["Qual o formato final?", "Interior ou exterior?", "Qual a quantidade?", "Com ou sem plastificação?"],
    },
    "Lona": {
        "keywords": ["lona", "banner", "faixa"],
        "formato": "Medida personalizada em metros",
        "papel": "Lona PVC",
        "impressao": "Impressão digital grande formato",
        "acabamentos": ["Corte", "Bainha opcional", "Ilhós opcional"],
        "perguntas": ["Quais as medidas finais?", "Interior ou exterior?", "Com bainha?", "Com ilhós?", "Inclui aplicação/instalação?"],
    },
    "Vinil": {
        "keywords": ["vinil", "autocolante", "sticker", "montra"],
        "formato": "Medida personalizada",
        "papel": "Vinil branco / transparente / recorte",
        "impressao": "Impressão digital ou recorte",
        "acabamentos": ["Corte", "Laminação opcional", "Aplicação opcional"],
        "perguntas": ["Qual a medida?", "Vinil impresso ou de recorte?", "Interior ou exterior?", "Com laminação?", "Inclui aplicação?"],
    },
    "Revista / Brochura": {
        "keywords": ["revista", "brochura", "catálogo", "catalogo", "livreto", "booklet"],
        "formato": "A4, A5 ou personalizado fechado",
        "papel": "Interior e capa podem ter papéis diferentes",
        "impressao": "Impressão 1 para interior; Impressão 2 para capa se papel diferente",
        "acabamentos": ["Corte", "Dobra", "Agrafo ou cola", "Plastificação da capa opcional"],
        "perguntas": ["Quantas páginas interiores?", "Capa incluída?", "Papel da capa é diferente do interior?", "Agrafo ou lombada colada?", "Formato fechado?"],
    },
    "Roll-up": {
        "keywords": ["roll up", "roll-up", "rollup", "expositor"],
        "formato": "Normalmente 85x200 cm",
        "papel": "Tela / material próprio para roll-up",
        "impressao": "Impressão digital grande formato",
        "acabamentos": ["Montagem em estrutura", "Bolsa de transporte"],
        "perguntas": ["Qual a medida?", "Inclui estrutura?", "O cliente fornece arte-final?", "Prazo de entrega?"],
    },
}

FORMATOS = ["A6", "A5", "A4", "A3", "A2", "A1", "85x55", "90x50"]
PAPEIS = ["135g", "170g", "200g", "250g", "300g", "350g"]


def identificar_produto(texto: str):
    t = texto.lower()
    scores = {}
    for produto, cfg in PRODUTOS.items():
        score = sum(1 for k in cfg["keywords"] if k in t)
        if score:
            scores[produto] = score
    if not scores:
        return "Não identificado"
    return max(scores, key=scores.get)


def extrair_quantidade(texto: str):
    # Procura números antes de palavras típicas ou número isolado relevante
    padroes = [
        r"(\d+[\.,]?\d*)\s*(unidades|unid|unds|exemplares|flyers|cartazes|cartões|cartoes|revistas|lonas|roll)",
        r"(\d+)\s*x",
    ]
    for p in padroes:
        m = re.search(p, texto.lower())
        if m:
            return m.group(1).replace(".", "")
    nums = re.findall(r"\b\d{2,6}\b", texto)
    return nums[0] if nums else "Não indicado"


def extrair_formato(texto: str):
    t = texto.upper().replace(" ", "")
    for f in FORMATOS:
        if f.replace(" ", "").upper() in t:
            return f
    m = re.search(r"\d+[,.]?\d*\s*[xX]\s*\d+[,.]?\d*\s*(cm|mm|m)?", texto)
    return m.group(0) if m else "Não indicado"


def extrair_papel(texto: str):
    for p in PAPEIS:
        if p.lower() in texto.lower().replace(" ", ""):
            return p
    if "couch" in texto.lower():
        return "Couché — gramagem não indicada"
    return "Não indicado"


def extrair_cores(texto: str):
    t = texto.lower()
    if any(x in t for x in ["frente e verso", "2 lados", "dupla face"]):
        return "4/4 cores, se for a cores dos dois lados"
    if any(x in t for x in ["frente", "só frente", "so frente", "1 lado"]):
        return "4/0 cores, se for a cores só frente"
    if any(x in t for x in ["preto", "pb", "p/b"]):
        return "Preto — confirmar 1/0 ou 1/1"
    if any(x in t for x in ["cor", "cores", "colorido"]):
        return "A cores — confirmar 4/0 ou 4/4"
    return "Não indicado"


def detetar_acabamentos(texto: str):
    t = texto.lower()
    acab = []
    mapa = {
        "dobra": ["dobra", "dobrado", "vinco"],
        "plastificação": ["plastificação", "plastificado", "laminação", "laminado"],
        "agrafo": ["agrafo", "agrafado"],
        "cola/lombada": ["cola", "lombada"],
        "ilhós": ["ilhós", "ilhos"],
        "bainha": ["bainha"],
        "corte especial": ["corte especial", "corte forma"],
    }
    for nome, keys in mapa.items():
        if any(k in t for k in keys):
            acab.append(nome)
    return acab or ["Não indicado — confirmar se apenas leva corte normal"]


def gerar_resumo(texto, produto_manual):
    produto = produto_manual if produto_manual != "Automático" else identificar_produto(texto)
    cfg = PRODUTOS.get(produto, {})
    quantidade = extrair_quantidade(texto)
    formato = extrair_formato(texto)
    papel = extrair_papel(texto)
    cores = extrair_cores(texto)
    acabamentos = extrair_acabamentos(texto)

    perguntas = []
    if cfg:
        perguntas.extend(cfg["perguntas"])
    if quantidade == "Não indicado": perguntas.append("Qual a quantidade pretendida?")
    if formato == "Não indicado": perguntas.append("Qual o formato/medida final?")
    if papel == "Não indicado": perguntas.append("Qual o papel/material pretendido?")
    if cores == "Não indicado": perguntas.append("A impressão é só frente ou frente e verso? A cores ou preto?")
    perguntas.append("O cliente fornece arte-final pronta para impressão?")
    perguntas.append("Existe prazo de entrega obrigatório?")

    # remover duplicados mantendo ordem
    perguntas_unicas = []
    for p in perguntas:
        if p not in perguntas_unicas:
            perguntas_unicas.append(p)

    return produto, quantidade, formato, papel, cores, acabamentos, perguntas_unicas

# ----------------------------
# Interface
# ----------------------------
with st.sidebar:
    st.header("Configuração")
    produto_manual = st.selectbox("Tipo de trabalho", ["Automático"] + list(PRODUTOS.keys()))
    cliente = st.text_input("Cliente", "")
    data_pedido = st.date_input("Data do pedido", value=date.today())

pedido = st.text_area(
    "Cole aqui o pedido do cliente",
    height=180,
    placeholder="Ex.: Preciso de orçamento para 1000 flyers A5, frente e verso, a cores, em papel couché 135g..."
)

if st.button("Gerar guião GGWEB", type="primary"):
    if not pedido.strip():
        st.warning("Insira primeiro o pedido do cliente.")
        st.stop()

    produto, quantidade, formato, papel, cores, acabamentos, perguntas = gerar_resumo(pedido, produto_manual)
    cfg = PRODUTOS.get(produto, {})

    st.subheader("1. Interpretação do pedido")
    col1, col2, col3 = st.columns(3)
    col1.metric("Produto", produto)
    col2.metric("Quantidade", quantidade)
    col3.metric("Formato", formato)

    st.write("**Papel/material identificado:**", papel)
    st.write("**Impressão/cores:**", cores)
    st.write("**Acabamentos identificados:**", ", ".join(acabamentos))

    st.subheader("2. Informação em falta ou a confirmar")
    for p in perguntas:
        st.checkbox(p, value=False)

    st.subheader("3. Guião de preenchimento no GGWEB")

    st.markdown("### Descrição do trabalho")
    descricao = f"{produto} | Qtd: {quantidade} | Formato: {formato} | Papel/material: {papel} | Impressão: {cores} | Acabamentos: {', '.join(acabamentos)}"
    st.code(descricao, language="text")

    st.markdown("### Pré-impressão")
    st.write("Preencher quando existir preparação, verificação, adaptação ou criação de ficheiro.")
    st.write("Sugestão: confirmar se a arte-final vem pronta para impressão. Se não vier, estimar tempo de operador.")

    st.markdown("### Impressão 1")
    st.write("Usar para o suporte principal do trabalho.")
    st.write(f"- Produto/material: {papel}")
    st.write(f"- Formato: {formato}")
    st.write(f"- Quantidade: {quantidade}")
    st.write(f"- Cores: {cores}")
    st.write("- Corte: normalmente sim, salvo trabalhos de grande formato ou material já final.")

    st.markdown("### Impressão 2")
    if produto == "Revista / Brochura":
        st.write("Usar se a capa tiver papel diferente do interior.")
        st.write("Exemplo: interior em 135g e capa em 300g.")
    else:
        st.write("Normalmente não usar, salvo se existir segundo papel/material diferente.")

    st.markdown("### Outras tarefas")
    st.write("Selecionar acabamentos e operações adicionais:")
    for a in acabamentos:
        st.write(f"- {a}")

    st.markdown("### Subcontratações")
    st.write("Usar apenas se houver trabalho externo: aplicação, estrutura, acabamento fora, transporte especial, etc.")

    st.markdown("### Recalcular")
    st.write("Depois de preencher todas as secções, clicar em Recalcular no GGWEB.")

    st.subheader("4. Nota interna")
    st.info("Este guião é uma proposta de apoio. Confirmar sempre com a produção em trabalhos fora do padrão, materiais especiais, prazos urgentes ou acabamentos não habituais.")

else:
    st.info("Insira o pedido do cliente e clique em 'Gerar guião GGWEB'.")

st.divider()
st.caption("Versão inicial. A precisão aumenta com exemplos reais de orçamentos já preenchidos no GGWEB.")
