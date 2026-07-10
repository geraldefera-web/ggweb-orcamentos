import re
import unicodedata
from datetime import date
from typing import Dict, List, Tuple

import streamlit as st

st.set_page_config(page_title='Assistente GGWEB - Orçamentos', layout='wide')
st.title('Assistente de Orçamentos GGWEB')
st.caption('Interpreta pedidos, separa trabalhos, calcula áreas e gera um guião técnico para o GGWEB.')

PRODUTOS = ['Automático','Vinil','Lona','Flyer / Panfleto','Cartaz','Cartões de visita','Livro / Brochura / Catálogo','Roll-up','PVC / Placa rígida','Embalagem / Caixa','Caderno / Bloco','Outro']
GRANDE_FORMATO = {'Vinil','Lona','Roll-up','PVC / Placa rígida'}
TERMOS_SUBCONTRATACAO = ['termo-estampagem','termo estampagem','hot stamping','verniz uv','uv localizado','relevo','cunho','gravação','gravacao','corte laser','fornecedor externo','subcontratação','subcontratacao']

def sem_acentos(texto:str)->str:
    texto=unicodedata.normalize('NFD',texto)
    return ''.join(ch for ch in texto if unicodedata.category(ch)!='Mn')

def normalizar(texto:str)->str:
    texto=sem_acentos(texto.lower()).replace('×','x').replace(',','.')
    return re.sub(r'\s+',' ',texto).strip()

def moeda_para_float(texto:str):
    m=re.search(r'(\d+(?:[.,]\d{1,2})?)\s*€',texto or '')
    return float(m.group(1).replace(',','.')) if m else None

def identificar_produto(texto:str)->str:
    t=normalizar(texto)
    regras=[('Vinil',['vinil','autocolante','sticker','easydot']),('Lona',['lona','banner','faixa']),('Flyer / Panfleto',['flyer','panfleto','folheto']),('Cartaz',['cartaz','poster']),('Cartões de visita',['cartao de visita','cartoes de visita','business card']),('Livro / Brochura / Catálogo',['livro','brochura','catalogo','revista','publicacao']),('Roll-up',['roll-up','roll up','rollup']),('PVC / Placa rígida',['placa pvc','pvc','placa rigida']),('Embalagem / Caixa',['caixa','embalagem','packaging']),('Caderno / Bloco',['caderno','bloco de notas','bloco espiral'])]
    for produto,termos in regras:
        if any(x in t for x in termos): return produto
    return 'Outro'

def extrair_quantidade(texto:str)->int:
    t=normalizar(texto)
    for p in [r'\b(\d+)\s*(?:unidades|unidade|unds|unid|exemplares|exemplar)\b',r'^\s*(\d+)\s+']:
        m=re.search(p,t)
        if m:return int(m.group(1))
    return 1

def extrair_dimensoes(texto:str)->Dict:
    t=normalizar(texto)
    m=re.search(r'(\d+(?:\.\d+)?)\s*(mm|cm|m)?\s*x\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?',t)
    if not m:return {'formato':'','largura_m':None,'altura_m':None,'area_unitaria':None}
    largura=float(m.group(1)); altura=float(m.group(3)); unidade=m.group(2) or m.group(4) or 'mm'
    if unidade=='mm': largura_m,altura_m=largura/1000,altura/1000
    elif unidade=='cm': largura_m,altura_m=largura/100,altura/100
    else: largura_m,altura_m=largura,altura
    return {'formato':f'{largura:g} x {altura:g} {unidade}','largura_m':largura_m,'altura_m':altura_m,'area_unitaria':round(largura_m*altura_m,3)}

def extrair_data(texto:str,tipo:str)->str:
    t=normalizar(texto)
    if tipo=='aplicacao': padrao=r'(?:colocacao|aplicacao|instalacao)\s*(?:dia)?\s*(\d{1,2})\s*(?:de)?\s*([a-z]+)'
    else: padrao=r'remocao.*?(\d{1,2})\s*(?:de)?\s*([a-z]+)'
    m=re.search(padrao,t)
    return f'{m.group(1)} de {m.group(2).capitalize()}' if m else ''

def extrair_material(texto:str,produto:str)->str:
    t=normalizar(texto)
    if produto=='Vinil':
        if 'removivel' in t:return 'Vinil removível EasyDot' if 'easydot' in t else 'Vinil removível'
        if 'exterior' in t:return 'Vinil para exterior'
        return 'Vinil'
    if produto=='Lona':return 'Lona PVC'
    if produto=='PVC / Placa rígida':return 'PVC / placa rígida'
    gramagem=re.search(r'(\d{2,3})\s*(?:g|gr|grs|gsm)\b',t); gram=f'{gramagem.group(1)} g' if gramagem else ''
    tipo='Couché' if 'couche' in t else 'Offset' if 'offset' in t else 'Cartolina' if 'cartolina' in t else ''
    if 'mate' in t and tipo:tipo+=' mate'
    elif 'brilho' in t and tipo:tipo+=' brilho'
    return ' '.join(x for x in [tipo,gram] if x).strip()

def extrair_impressao(texto:str,produto:str)->str:
    t=normalizar(texto); m=re.search(r'\b([124])\s*/\s*([124])\b',t)
    if m:return f'{m.group(1)}/{m.group(2)} cores'
    if 'pantone' in t:return 'Pantone — confirmar referência'
    if produto in GRANDE_FORMATO:return 'Impressão digital a cores' if ('impresso' in t or 'impressao' in t) else 'Impressão digital — confirmar'
    if 'frente e verso' in t:return '4/4 cores a confirmar'
    if '1 face' in t or 'so frente' in t:return '4/0 cores a confirmar'
    if 'cores' in t or 'cor' in t:return 'A cores — confirmar configuração'
    return ''

def extrair_revestimento(texto:str)->str:
    t=normalizar(texto)
    if 'laminacao mate' in t:return 'Laminação mate'
    if 'laminacao brilho' in t:return 'Laminação brilho'
    if 'laminacao' in t:return 'Laminação — confirmar tipo'
    if 'plastificacao mate' in t or 'plastificado mate' in t:return 'Plastificação mate'
    if 'plastificacao brilho' in t or 'plastificado brilho' in t:return 'Plastificação brilho'
    if 'plastificacao' in t or 'plastificado' in t:return 'Plastificação — confirmar tipo'
    return ''

def extrair_acabamentos(texto:str)->List[str]:
    t=normalizar(texto); acab=[]
    mapa=[('Corte circular',['corte circulo','corte circular']),('Corte de contorno',['corte contorno']),('Corte/Vinco',['corte/vinco','corte vinco']),('Corte reto',['corte reto','cortes retos']),('Ilhós',['ilhos']),('Bainha',['bainha']),('Dobra / vinco',['dobra','dobrado','vinco']),('Agrafo',['agrafo','agrafado']),('Colagem',['colagem']),('Lombada / cola PUR',['lombada','cola pur','pur']),('Forra',['forra']),('Guardas',['guardas']),('Espiral metálica',['espiral metalica']),('Espiral plástica',['espiral plastica']),('Relevo seco',['relevo seco','embossing'])]
    for nome,termos in mapa:
        if any(x in t for x in termos):acab.append(nome)
    return acab

def extrair_aplicacao(texto:str)->Dict:
    t=normalizar(texto)
    return {'inclui_aplicacao':any(x in t for x in ['colocacao','aplicacao','instalacao']),'exterior':'exterior' in t,'inclui_remocao':'remocao' in t,'data_aplicacao':extrair_data(texto,'aplicacao'),'data_remocao':extrair_data(texto,'remocao')}

def detetar_subcontratacao(texto:str)->List[str]:
    t=normalizar(texto); return [x for x in TERMOS_SUBCONTRATACAO if x in t]

def extrair_designacao(texto:str)->str:
    primeira=texto.split('-')[0].strip(); primeira=re.sub(r'^\s*\d+\s*(?:unidades|unidade|unds|unid)?\s*','',primeira,flags=re.I).strip(); return primeira or 'Trabalho sem designação'

def extrair_local(texto:str)->str:
    for local in ['BMcar Póvoa de Varzim','Póvoa de Varzim','Selecor']:
        if local.lower() in texto.lower():return local
    return ''

def analisar_linha(texto:str)->Dict:
    produto=identificar_produto(texto); qtd=extrair_quantidade(texto); dim=extrair_dimensoes(texto); aplic=extrair_aplicacao(texto); preco=moeda_para_float(texto)
    area_total=round(dim['area_unitaria']*qtd,3) if dim['area_unitaria'] else None
    return {'texto_original':texto.strip(),'designacao':extrair_designacao(texto),'produto':produto,'quantidade':qtd,'formato':dim['formato'],'area_unitaria':dim['area_unitaria'],'area_total':area_total,'material':extrair_material(texto,produto),'impressao':extrair_impressao(texto,produto),'revestimento':extrair_revestimento(texto),'acabamentos':extrair_acabamentos(texto),'aplicacao':aplic,'local':extrair_local(texto),'preco':preco,'preco_m2':round(preco/area_total,2) if preco and area_total else None,'subcontratacoes':detetar_subcontratacao(texto)}

def linha_e_trabalho(texto:str)->bool:
    t=normalizar(texto)
    if not t or t.startswith(('observacoes','prazo de entrega','entrega das bandeiras','a/c')):return False
    return any(s in t for s in ['vinil','lona','flyer','panfleto','cartaz','livro','brochura','caixa','placa','roll','unidade','unidades'])

def separar_trabalhos(pedido:str)->Tuple[List[Dict],List[str]]:
    trabalhos=[]; notas=[]
    for linha in [l.strip(' \t•') for l in pedido.splitlines() if l.strip()]:
        (trabalhos if linha_e_trabalho(linha) else notas).append(analisar_linha(linha) if linha_e_trabalho(linha) else linha)
    return trabalhos,notas

def campos_em_falta(t:Dict)->List[str]:
    faltas=[]
    if not t['formato']:faltas.append('Formato/medida')
    if not t['material']:faltas.append('Matéria-prima/material')
    if not t['impressao']:faltas.append('Tipo de impressão')
    if t['produto'] in GRANDE_FORMATO and not t['area_total']:faltas.append('Área total em m²')
    if t['produto']=='Vinil' and not t['revestimento']:faltas.append('Revestimento/laminação')
    if t['aplicacao']['inclui_aplicacao'] and not t['local']:faltas.append('Local de aplicação')
    if t['aplicacao']['inclui_aplicacao'] and not t['aplicacao']['data_aplicacao']:faltas.append('Data de aplicação')
    if not t['acabamentos']:faltas.append('Acabamento/corte')
    return faltas

def descricao_interna(t:Dict)->str:
    linhas=[f"Produto: {t['produto']}",f"Designação: {t['designacao']}",f"Quantidade: {t['quantidade']} unidade(s)",f"Formato/medida: {t['formato'] or '[por confirmar]'}"]
    if t['area_unitaria'] is not None:linhas.append(f"Área unitária: {t['area_unitaria']} m²")
    if t['area_total'] is not None:linhas.append(f"Área total: {t['area_total']} m²")
    linhas += [f"Matéria-prima: {t['material'] or '[por confirmar]'}",f"Impressão: {t['impressao'] or '[por confirmar]'}",f"Revestimento: {t['revestimento'] or '[não indicado / confirmar]'}",f"Acabamento: {', '.join(t['acabamentos']) if t['acabamentos'] else '[confirmar]'}"]
    if t['aplicacao']['inclui_aplicacao']:linhas.append('Aplicação/instalação: Sim')
    if t['aplicacao']['exterior']:linhas.append('Aplicação exterior: Sim')
    if t['aplicacao']['data_aplicacao']:linhas.append(f"Data de aplicação: {t['aplicacao']['data_aplicacao']}")
    if t['aplicacao']['inclui_remocao']:linhas.append('Remoção posterior: Sim')
    if t['aplicacao']['data_remocao']:linhas.append(f"Data de remoção: {t['aplicacao']['data_remocao']}")
    if t['local']:linhas.append(f"Local: {t['local']}")
    if t['preco'] is not None:linhas.append(f"Preço indicado: {t['preco']:.2f} €")
    if t['preco_m2'] is not None:linhas.append(f"Preço de referência: {t['preco_m2']:.2f} €/m²")
    if t['subcontratacoes']:linhas.append(f"Possível subcontratação: {', '.join(t['subcontratacoes'])}")
    return '\n'.join(linhas)

def guiao_ggweb(t:Dict)->List[str]:
    passos=['Descrição do trabalho: usar a descrição técnica estruturada.','Pré-impressão: confirmar arte-final e tempo de operador/design.']
    if t['produto'] in GRANDE_FORMATO:
        passos.append(f"Impressão 1: {t['material'] or 'material por confirmar'}, impressão digital/grande formato, quantidade {t['quantidade']}, formato {t['formato'] or 'por confirmar'} e área total {t['area_total'] if t['area_total'] is not None else 'por confirmar'} m².")
        passos.append('Impressão 2: normalmente não preencher, salvo segundo material diferente.')
        tarefas=[]
        if t['revestimento']:tarefas.append(t['revestimento'])
        tarefas.extend(t['acabamentos'])
        if t['aplicacao']['inclui_aplicacao']:tarefas.append('Aplicação/instalação')
        if t['aplicacao']['inclui_remocao']:tarefas.append('Remoção posterior')
        passos.append('Outras tarefas: '+(', '.join(tarefas) if tarefas else 'confirmar corte e acabamento.'))
    else:
        passos.append(f"Impressão 1: material {t['material'] or 'por confirmar'}, quantidade {t['quantidade']}, formato {t['formato'] or 'por confirmar'} e impressão {t['impressao'] or 'por confirmar'}.")
        passos.append('Impressão 2: usar apenas com segundo papel, capa, miolo ou componente diferente.')
        passos.append('Outras tarefas: selecionar acabamentos, corte, dobra, plastificação, encadernação ou colagem.')
    passos.append('Subcontratações: preencher apenas se existir fornecedor externo; indicar serviço, custo, prazo e margem.' if t['subcontratacoes'] else 'Subcontratações: não preencher, salvo tarefa externa.')
    passos.append('Recalcular: depois de confirmar todas as secções, clicar em Recalcular no GGWEB.')
    return passos

with st.sidebar:
    st.header('Configuração')
    produto_manual=st.selectbox('Tipo de trabalho',PRODUTOS)
    cliente=st.text_input('Cliente','')
    data_pedido=st.date_input('Data do pedido',value=date.today())

pedido=st.text_area('Cole aqui o pedido completo do cliente',height=260,placeholder='Cole o pedido com uma linha por trabalho...')
imagem=st.file_uploader('Carregar imagem do produto ou amostra (opcional)',type=['jpg','jpeg','png'])
if imagem is not None:
    st.image(imagem,caption='Imagem carregada',use_container_width=True)
    st.info('A imagem fica associada ao pedido. Nesta versão, a interpretação automática principal baseia-se no texto.')

if pedido.strip():
    trabalhos,notas=separar_trabalhos(pedido)
    if produto_manual!='Automático':
        for t in trabalhos:t['produto']=produto_manual
    if not trabalhos:
        st.warning('Não foi possível identificar linhas de trabalho no pedido.'); st.stop()
    total_area=round(sum(t['area_total'] or 0 for t in trabalhos),3)
    total_preco=round(sum(t['preco'] or 0 for t in trabalhos),2)
    st.subheader('1. Resumo geral do pedido')
    c1,c2,c3=st.columns(3); c1.metric('Linhas de trabalho',len(trabalhos)); c2.metric('Área total identificada',f'{total_area} m²'); c3.metric('Valor total indicado',f'{total_preco:.2f} €')
    if cliente:st.write(f'**Cliente:** {cliente}')
    st.write(f"**Data do pedido:** {data_pedido.strftime('%d/%m/%Y')}")
    if notas:
        st.markdown('**Notas gerais detetadas:**')
        for n in notas:st.write(f'- {n}')
    st.subheader('2. Trabalhos identificados')
    for idx,t in enumerate(trabalhos,1):
        with st.expander(f"{idx}. {t['designacao']} — {t['produto']}",expanded=(idx==1)):
            a,b,c=st.columns(3); a.metric('Quantidade',t['quantidade']); b.metric('Área total',f"{t['area_total']} m²" if t['area_total'] is not None else 'Por confirmar'); c.metric('Preço indicado',f"{t['preco']:.2f} €" if t['preco'] is not None else 'Não indicado')
            if t['preco_m2'] is not None:st.write(f"**Preço de referência:** {t['preco_m2']:.2f} €/m²")
            st.markdown('#### Descrição técnica para comunicação interna'); st.code(descricao_interna(t),language='text')
            st.markdown('#### Informação em falta ou a confirmar')
            faltas=campos_em_falta(t)
            if faltas:
                for f in faltas:st.warning(f)
            else:st.success('Informação técnica suficiente para preparar o orçamento.')
            st.markdown('#### Guião GGWEB')
            for p in guiao_ggweb(t):st.write(f'- {p}')
    st.subheader('3. Recomendação operacional')
    st.info('O pedido contém vários trabalhos. Recomenda-se separar no GGWEB por linha de produto ou por grupo operacional: produção, aplicação/remoção e preçários.' if len(trabalhos)>1 else 'Pedido simples. Pode ser tratado num único orçamento, desde que produção, aplicação e subcontratações estejam separadas.')
else:
    st.info('Cole o pedido do cliente para iniciar a análise.')
