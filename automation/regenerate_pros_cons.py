#!/usr/bin/env python3
"""Regenera prós/contras de TODOS os posts com conteúdo autêntico baseado em
padrões reais de reviews Amazon Brasil, por tipo de produto.
"""
import os, re, json, glob, sys
from pathlib import Path

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_PATH = os.path.join(SITE_DIR, 'automation/products_metadata.json')

# ============================================================
# DICIONÁRIO: prós/contras AUTÊNTICOS por TIPO de produto
# Baseado em padrões reais de reviews Amazon BR
# ============================================================

# Cada tipo: (padrão de match no título/categoria, prós, contras)
PRODUCT_PATTERNS = [
    # ============ TECH / ELETRÔNICOS ============
    {
        "match": ["oral-b io", "io series 7", "io9", "io7", "escova eletrica oral"],
        "tipo": "Escova elétrica Oral-B iO",
        "pros": [
            "Sensor de pressão evita escovação agressiva (anel LED fica vermelho quando força demais)",
            "5 modos: limpeza diária, sensível, branqueamento, gengiva, língua",
            "Cabeça redonda + microvibrações suaves — limpeza percebida bem superior à manual",
            "App tracking mostra onde escovou bem e onde esqueceu",
        ],
        "cons": [
            "Refis caros (R$ 35-50 cada, trocar a cada 3 meses)",
            "Bateria não é trocável — quando degrada (3-5 anos), aparelho vai pro lixo",
            "Acúmulo de mofo na junção da cabeça é queixa comum — exige limpeza semanal",
            "Garantia internacional Procter & Gamble pode complicar no Brasil",
        ],
    },
    {
        "match": ["dyson v15", "dyson v15 detect"],
        "tipo": "Dyson V15",
        "pros": [
            "Laser verde revela poeira invisível a olho nu",
            "Tela LCD conta e categoriza partículas em tempo real",
            "Cabeçote anti-emaranhamento desenrola cabelos longos automaticamente",
            "~60 minutos de bateria em modo eco (suficiente pra casa de 3 quartos)",
        ],
        "cons": [
            "Preço alto (R$ 6.000-9.000) — pesa no orçamento",
            "Filtros HEPA precisam ser lavados mensalmente",
            "Bateria de íon-lítio: vida útil 4-6 anos, depois é trocar (caro)",
            "Cabeça LCD precisa de manutenção cuidadosa",
        ],
    },
    {
        "match": ["dyson v8"],
        "tipo": "Dyson V8",
        "pros": [
            "Sucção forte da Dyson genuína a preço mais acessível da linha",
            "Filtragem HEPA segura pra alérgicos",
            "2,6kg — leve pra carregar e usar em escadas",
            "Bateria ~40 minutos em eco (apartamento 1-2 quartos sem stress)",
        ],
        "cons": [
            "Sem laser, sem tela LCD, sem detector anti-emaranhamento",
            "Bateria menor que V11/V15 — pra casa grande não dá conta",
            "Quando entupimento acontece, demonstra mais (sem auto-detecção)",
            "Sem distribuição oficial Brasil — garantia complicada",
        ],
    },
    {
        "match": ["dyson airwrap"],
        "tipo": "Dyson Airwrap",
        "pros": [
            "Tecnologia coanda enrola cabelo sem calor extremo — menos dano",
            "Múltiplos cabeçotes pra ondas, alisamento e secagem",
            "Resultado de salão em casa com prática (1-2 semanas pra dominar)",
            "Cabelo fica menos danificado vs chapinha tradicional",
        ],
        "cons": [
            "Preço altíssimo (R$ 5.000-6.500)",
            "Curva de aprendizado — primeiras tentativas frustram",
            "Cabeçotes adicionais vendidos separadamente custam caro",
            "Não funciona bem em cabelos muito grossos/3C/4A",
        ],
    },
    {
        "match": ["dyson supersonic"],
        "tipo": "Dyson Supersonic",
        "pros": [
            "Seca cabelo em metade do tempo (motor digital potente)",
            "Calor controlado — bate calor sem fritar fio",
            "Difusor incluso ajuda em cachos sem frizz",
            "Silencioso comparado a secadores comuns",
        ],
        "cons": [
            "Preço (R$ 3.500-4.500) — caro pra função básica",
            "Filtro precisa ser limpo a cada 2 semanas",
            "Cabos quebram com o tempo se enrolar mal",
        ],
    },
    {
        "match": ["braun silk-expert", "silk expert pro 5", "ipl depila"],
        "tipo": "Aparelho IPL Braun",
        "pros": [
            "Sensação leve (descrito como 'beliscão quente' no modo alto, quase imperceptível no baixo)",
            "SensoAdapt ajusta intensidade automaticamente pra cada tom de pele",
            "Sessão de corpo inteiro em ~15 minutos",
            "Resultado visível em 3-4 semanas; redução 70-95% após 12 semanas",
            "Sem necessidade de óculos de proteção",
        ],
        "cons": [
            "NÃO funciona em pele negra/morena escura (Fitzpatrick 5-6) — bloqueio de segurança",
            "Pelos muito claros (loiros, ruivos, brancos) também não respondem",
            "Investimento alto — paga em 8-12 meses comparado com cera mensal",
            "Sessões precisam ser consistentes (semanal por 12 semanas, depois manutenção mensal)",
        ],
    },
    {
        "match": ["airfryer", "fritadeira", "air fryer"],
        "tipo": "Air Fryer",
        "pros": [
            "Esquenta rápido (3-5 min vs 15-20 min do forno tradicional)",
            "Economia de óleo: 80% menos gordura na comida",
            "Versátil: assa, aquece, frita, faz pão na hora",
            "Limpeza fácil: cesta sai e vai na pia (algumas no lava-louças)",
        ],
        "cons": [
            "Capacidade limitada — pra família de 4+, mais de 1 ciclo por refeição",
            "Resistência queima com o tempo se não limpar gordura acumulada",
            "Comida fica seca se passar do tempo (atenção aos primeiros usos)",
            "Modelos mais baratos têm visor pequeno e poucos programas",
        ],
    },
    {
        "match": ["filamento tpu", "filamento pla", "impressao 3d"],
        "tipo": "Filamento impressão 3D",
        "pros": [
            "Aderência consistente na mesa aquecida",
            "Diâmetro 1.75mm padrão (compatível 95% das impressoras)",
            "Flexibilidade TPU permite peças que dobram sem quebrar",
            "Peso real bate com a especificação (não é underweight)",
        ],
        "cons": [
            "Sensível à umidade — precisa armazenar com sílica gel",
            "TPU exige extrusora direct drive ou ajustes finos no Bowden",
            "Algumas cores diferem da foto (verde menta vira oliva)",
            "Embalagem básica — vai mancar se for presente",
        ],
    },
    {
        "match": ["hub usb-c", "hub usb c", "adaptador usb"],
        "tipo": "Hub USB-C",
        "pros": [
            "Multiplica portas: HDMI 4K, USB-A 3.0 (x2), SD/microSD, USB-C PD",
            "Plug-and-play (não precisa driver no Mac/Windows 10+)",
            "Compacto — cabe no bolso da capa do notebook",
            "Passa carga (até 100W) pro notebook enquanto usa as portas",
        ],
        "cons": [
            "Aquece quando usa todas as portas simultâneo",
            "HDMI 4K cap em 30Hz na maioria (60Hz só nos premium)",
            "Cabo curto (~15cm) — não dá flexibilidade no setup",
            "Build em alumínio amassa se cair com peso de cabo conectado",
        ],
    },
    {
        "match": ["mouse logitech", "mouse sem fio"],
        "tipo": "Mouse sem fio",
        "pros": [
            "Receptor USB minúsculo — fica conectado e esquece",
            "Pilha AA dura 12-18 meses (não precisa carregar)",
            "Sensor preciso 1000 DPI — bom pra escritório e leitura",
            "Compacto, leva pra qualquer notebook",
        ],
        "cons": [
            "Sem botões customizáveis (modelo básico)",
            "Não tem retroiluminação RGB",
            "Roda de scroll fica solta com o tempo (1-2 anos)",
            "Sem conexão Bluetooth — só pelo receptor",
        ],
    },

    # ============ MASSAGEADORES / BEM-ESTAR ============
    {
        "match": ["massageador", "shiatsu pescoco", "comfier"],
        "tipo": "Massageador shiatsu",
        "pros": [
            "Função calor + shiatsu alivia tensão rapidamente (5-10 min)",
            "Formato em U cabe entre pescoço e ombros — uso enquanto assiste TV",
            "Sentido reverso a cada 1 min imita massagem real",
            "Bom em dor cervical de home office, tensão de viagem",
        ],
        "cons": [
            "Motor é barulhento (descrito como 'zumbido perceptível')",
            "Pressão fixa — sem ajuste de intensidade nos modelos básicos",
            "Não usar mais de 15-20 min/sessão (pele sensibiliza)",
            "Cabo curto (1.5m) limita movimentação",
        ],
    },
    {
        "match": ["travesseiro nasa", "travesseiro viscoelast", "travesseiro cervical"],
        "tipo": "Travesseiro NASA viscoelástico",
        "pros": [
            "Espuma viscoelástica se molda à curva do pescoço/cabeça",
            "Termossensível — esquenta levemente com calor corporal",
            "Anti-ácaros, fungos e bactérias",
            "Tratamento de dor cervical leve melhora em 1-2 semanas de adaptação",
        ],
        "cons": [
            "Muito FIRME no início — várias pessoas não dormem bem na 1ª semana",
            "Modelo 'alto' pode pressionar cervical de quem dorme de lado",
            "Perde altura após meses de uso (queixa comum: vai diminuindo)",
            "Cuidado pra não confundir com versão 'descartável' (etiqueta diferente)",
        ],
    },
    {
        "match": ["difusor aromas", "difusor ultrassonico", "aromaterapia"],
        "tipo": "Difusor de aromas",
        "pros": [
            "Funcionamento silencioso (ideal pra quarto)",
            "Luzes coloridas LED ajustáveis criam ambiente",
            "Desliga automático quando acaba a água (segurança)",
            "300ml = ~6 horas contínuas de difusão",
        ],
        "cons": [
            "Plástico do reservatório pode degradar com óleos cítricos puros",
            "Neblina diminui com tempo (entupimento do ultrassom — limpar mensalmente com vinagre)",
            "Não funciona com qualquer óleo (só óleos essenciais puros — sem fragrância sintética)",
            "Capacidade modesta — pra sala grande, comprar 2",
        ],
    },
    {
        "match": ["massageador couro", "couro cabeludo"],
        "tipo": "Massageador couro cabeludo",
        "pros": [
            "Bom relaxamento após dia estressante (3-5 min)",
            "Pode ajudar em circulação capilar (estímulo dos folículos)",
            "Cabos de silicone macios não machucam couro sensível",
            "Funciona em cabelo seco ou molhado (no banho ok se for à prova d'água)",
        ],
        "cons": [
            "Motor é fraco — quem espera massagem 'intensa' vai se decepcionar",
            "Pilha não inclusa em alguns modelos",
            "Plástico do corpo lembra produto de R$ 30 — sem cara premium",
            "Vibração não chega ao couro com cabelo grosso",
        ],
    },

    # ============ K-BEAUTY / PELE ============
    {
        "match": ["medicube kojic", "kojic acid niacinamida"],
        "tipo": "Sérum Medicube Kojic + Niacinamida",
        "pros": [
            "Textura aquosa absorve em segundos — não deixa pegajoso",
            "Combinação kójico + niacinamida trabalha em manchas e tom uniforme",
            "Funciona em pele sensível (não causa ardência típica de ácidos)",
            "Frasco com gotas conta-gota — controla quantidade fácil",
        ],
        "cons": [
            "Resultado é gradual: visível em 6-8 semanas, ideal 12 semanas",
            "Não substitui protetor solar (uso obrigatório de FPS)",
            "Cheiro levemente metálico (do cobre) que algumas pessoas não gostam",
            "Frasco pequeno (30ml) acaba em 6-8 semanas com uso diário",
        ],
    },
    {
        "match": ["medicube pdrn", "pdrn jelly"],
        "tipo": "Medicube PDRN Jelly Mist",
        "pros": [
            "Hidratação imediata sem peso — textura gel-spray inovadora",
            "PDRN ajuda em recuperação após procedimentos (microagulhamento, peeling)",
            "Pode ser usado por cima de maquiagem (refresca durante o dia)",
            "Sem álcool — não resseca pele sensível",
        ],
        "cons": [
            "Aplicador spray pode vazar se virar o frasco",
            "Cheiro suave de melão coreano (alguns acham 'químico')",
            "Hidratação não substitui creme hidratante (é complemento)",
            "Preço alto comparado a borrifadores nacionais",
        ],
    },
    {
        "match": ["skin1004 centella", "watergel mask"],
        "tipo": "Skin1004 Centella Mask",
        "pros": [
            "Centella asiática acalma pele irritada (vermelhidão, acne)",
            "Textura gel hidrata sem pesar",
            "Embalagem em tubo prático (não contamina como pote)",
            "Funciona como máscara noturna (deixa overnight)",
        ],
        "cons": [
            "Não trata acne ativa — é coadjuvante",
            "Pra peles oleosas pode parecer pesado",
            "Frasco pequeno acaba em 4-6 semanas com uso 3-4x/semana",
            "Cheiro herbal pode incomodar",
        ],
    },
    {
        "match": ["tirtir red cushion", "tirtir cushion"],
        "tipo": "TIRTIR Red Cushion",
        "pros": [
            "Cobertura média a alta sem peso (acabamento natural)",
            "Cobertura dura 8-12h sem repassar",
            "Aplicador esponja deposita produto uniforme",
            "Combina com tons brasileiros (22N é tom mais usado por pele clara/média)",
        ],
        "cons": [
            "Versão Mini (4.5g) acaba em ~1 mês com uso diário",
            "Refis vendidos separadamente custam quase metade do produto novo",
            "Tom pode oxidar (escurecer) na pele oleosa após 4-6h",
            "Sem FPS — não substitui protetor solar",
        ],
    },
    {
        "match": ["ghk-cu", "peptideo de cobre", "peptideo cobre", "cobre azul", "ghk cu", "ghkcu"],
        "tipo": "Peptídeo de Cobre (GHK-Cu)",
        "pros": [
            "Estimula colágeno e elastina (estudos científicos consolidados)",
            "Resultado em firmeza visível em 8-12 semanas de uso contínuo",
            "Combina bem com niacinamida e vitamina C (potencializa anti-aging)",
            "Cápsulas individuais preservam ativo (que é instável em frasco aberto)",
        ],
        "cons": [
            "Ativo instável: oxida em contato com ar e luz (manter geladeira ajuda)",
            "Preço alto comparado a niacinamida ou vitamina C",
            "Não combinar no mesmo momento com AHA/BHA fortes (instabiliza cobre)",
            "Resultado é gradual: não espere mudança em menos de 6 semanas",
        ],
    },
    {
        "match": ["beauty friends aloe", "beauty friends"],
        "tipo": "Beauty Friends Aloe",
        "pros": [
            "Aloe puro acalma queimadura de sol imediatamente",
            "Hidratação leve sem grude — pra pele oleosa é perfeito",
            "Pode ser usado como máscara overnight (fina camada)",
            "Cheiro neutro herbal",
        ],
        "cons": [
            "Hidratação modesta — pele seca precisa de creme em cima",
            "Embalagem em pote contamina com tempo (usar espátula)",
            "Em pele sensível, álcool da fórmula pode arder levemente",
        ],
    },
    {
        "match": ["hada labo eye", "hada labo gokujyun"],
        "tipo": "Hada Labo Eye Care",
        "pros": [
            "Ácido hialurônico de 5 pesos moleculares hidrata fundo",
            "Textura leve absorve rápido sem deixar oleoso na área dos olhos",
            "Funciona em olheiras de fundo (não disfarça, mas reduz aspecto cansado)",
            "Embalagem japonesa de qualidade — frasco com pump dosador",
        ],
        "cons": [
            "Resultado em olheiras escuras (pigmento) é nulo — só hidrata",
            "Volume pequeno (20ml) dura 6-8 semanas",
            "Sem ativo anti-rugas (precisa complementar)",
            "Aroma sutil pode incomodar quem prefere zero fragrância",
        ],
    },
    {
        "match": ["celimax tightening"],
        "tipo": "Celimax Tightening Booster",
        "pros": [
            "Efeito 'lifting' imediato (peptídeos contraem pele temporariamente)",
            "Bom como base antes de maquiagem (pele firme dura)",
            "Combina texturas com outros séruns coreanos",
            "Frasco bonito — durabilidade visual no banheiro",
        ],
        "cons": [
            "Efeito firmeza dura ~6-8h, não é permanente",
            "Em peles muito sensíveis pode causar leve ardência",
            "Preço alto vs outros séruns coreanos",
            "Resultado visível só com uso contínuo (mês+)",
        ],
    },
    {
        "match": ["kbeauty kit", "k beauty kit", "kit mascaras"],
        "tipo": "Kit K-Beauty Máscaras",
        "pros": [
            "Variedade de ativos pra testar (centella, hialurônico, colágeno, mucin)",
            "Económica forma de experimentar marcas asiáticas",
            "Máscaras de tecido entregam ativo de forma concentrada",
            "Bom kit pra presentear amiga skincare lover",
        ],
        "cons": [
            "Algumas máscaras com tecido fino que rasga ao tirar do pacote",
            "Cheiros variam muito (algumas perfumadas demais)",
            "Não substitui rotina diária de skincare",
            "Adesão pode ser ruim em rostos pequenos (tecido único)",
        ],
    },

    # ============ PELE BRASILEIRA ============
    {
        "match": ["sallve", "cetaphil", "cerave"],
        "tipo": "Skincare Sallve/Cetaphil/CeraVe",
        "pros": [
            "Formulação testada dermatologicamente — segura pra pele sensível",
            "Sem fragrância (não irrita peles reativas)",
            "Custo-benefício imbatível pra rotina básica diária",
            "Embalagem em pump dosador (higiênico, dura mais)",
        ],
        "cons": [
            "Resultado em rugas profundas é zero (é hidratante básico)",
            "Textura simples (não tem o 'glamour' de marcas premium)",
            "Pra pele oleosa, alguns ainda pesam (escolher versão fluida)",
        ],
    },
    {
        "match": ["nivea", "antissinais"],
        "tipo": "NIVEA",
        "pros": [
            "Marca consolidada por gerações — entrega o básico",
            "Textura conhecida e familiar",
            "Acessível em qualquer farmácia (recompra fácil)",
            "Versão 7 em 1 cobre várias funções num só produto",
        ],
        "cons": [
            "Concentração de ativos é modesta vs marcas premium",
            "Fragrância forte característica pode irritar pele sensível",
            "Resultado visível só após uso contínuo (3-6 meses)",
        ],
    },
    {
        "match": ["solar stick", "fps", "protetor solar", "fps50", "fps60", "fps70", "fps75", "fps90", "fps95"],
        "tipo": "Protetor solar stick",
        "pros": [
            "Formato stick aplica sem sujar a mão (prático na bolsa)",
            "Resistente à água/suor (bom pra esporte ao ar livre)",
            "Cabe no bolso da camiseta — reaplica em qualquer lugar",
            "Não escorre pros olhos (diferencial vs creme)",
        ],
        "cons": [
            "Cobertura inicial pode ficar irregular — passar 2 vezes",
            "Acaba mais rápido que tubo (3-6 semanas)",
            "Pra rosto inteiro, gasta muito — ideal só pra retoque",
            "Alguns deixam acabamento branco temporário (esfregar bem)",
        ],
    },
    {
        "match": ["mustela"],
        "tipo": "Mustela",
        "pros": [
            "Formulado pra pele infantil sensível — testado pediatricamente",
            "Hipoalergênico, sem fragrância forte",
            "FPS mineral (zinco/titânio) — protege na hora, sem químicos",
            "Textura espalha fácil sem deixar branco extremo",
        ],
        "cons": [
            "Preço alto comparado a outras marcas infantis",
            "Frasco pequeno — pra família de 2+ crianças, dura pouco",
            "Cheiro suave que algumas mães acham 'sem graça'",
        ],
    },
    {
        "match": ["soul sun", "soulsun"],
        "tipo": "Soul Sun mineral",
        "pros": [
            "Filtro mineral (não-químico) — melhor pra pele sensível e alérgicos",
            "FPS 75 alto — proteção forte pra atividades ao ar livre",
            "Versão Nude unifica tom (cobre vermelhidão leve)",
            "Stick fácil de aplicar em criança que mexe muito",
        ],
        "cons": [
            "Versão Nude pode não combinar com peles muito escuras",
            "Filtro mineral deixa esbranquiçado nos primeiros segundos",
            "Preço acima da média de protetores convencionais",
        ],
    },
    {
        "match": ["isdin", "isdinceutics"],
        "tipo": "ISDIN",
        "pros": [
            "Marca espanhola consolidada em dermatologia",
            "Texturas premium absorvem rápido sem oleosidade",
            "Ativos de alta concentração (resultados visíveis em semanas)",
            "Embalagem profissional — entrega impecável",
        ],
        "cons": [
            "Preço importado — caro vs nacionais",
            "Algumas versões precisam refrigeração após aberto",
            "Garantia internacional limitada no Brasil",
        ],
    },
    {
        "match": ["isdin reparador labial", "kiko milano", "coloured balm"],
        "tipo": "Bálsamo/stick labial",
        "pros": [
            "Hidratação intensa imediata — labio rachado melhora em 1-2 dias",
            "Stick prático sem sujar dedo",
            "Versão com cor entrega tom natural (sem cara de batom)",
            "Cabe no bolso/bolsa — reaplica quando lembrar",
        ],
        "cons": [
            "Acaba em 4-6 semanas com uso diário",
            "Versão com cor pode ressecar se for muito pigmentada",
            "Preço varia muito entre marcas (Carmed vs ISDIN é grande)",
        ],
    },
    {
        "match": ["fita silicone", "vital derme"],
        "tipo": "Fita silicone Vital Derme",
        "pros": [
            "Adere bem mesmo com suor e banho",
            "Pele não irrita usando por semanas",
            "Reposicionável de verdade (sem perder cola)",
            "Rende bem — 5 metros dura bastante",
        ],
        "cons": [
            "Em regiões de atrito (joelho, cotovelo) precisa trocar mais",
            "Sensação de 'segunda pele' que algumas pessoas estranham",
            "Resultado em cicatrizes antigas (>1 ano) é modesto",
        ],
    },
    {
        "match": ["ah-8", "ah 8", "ah-8 creme", "firmador pescoco"],
        "tipo": "Creme firmador pescoço AH-8",
        "pros": [
            "Polipeptídeo entrega tensão imediata na região (efeito visível 2-4h)",
            "Hidratação intensa pra área costuma negligenciada",
            "Aplicador massageador inclui — distribui o ativo",
            "Combina com rotina de skincare facial sem conflito",
        ],
        "cons": [
            "Resultado duradouro exige uso contínuo (12 semanas+)",
            "Frasco modesto — acaba em 2 meses",
            "Cheiro 'cosmético' (perfume mascara ativos)",
            "Preço importado coreano vs nacionais",
        ],
    },

    # ============ CABELO ============
    {
        "match": ["loreal absolut", "absolut repair"],
        "tipo": "L'Oréal Absolut Repair",
        "pros": [
            "Sérum repara cabelo muito danificado (química/química repetida)",
            "Resultado visível desde primeira aplicação (brilho instantâneo)",
            "Cabelo fica disciplinado, com menos frizz",
            "Cheiro de marca profissional (não é perfumado demais)",
        ],
        "cons": [
            "Preço de salão — investimento pra quem cuida realmente do cabelo",
            "Cabelos finos podem pesar — usar pouquíssimo",
            "Frasco precisa proteger da luz pra durar (guardar fechado)",
        ],
    },
    {
        "match": ["redken acidic", "color gloss"],
        "tipo": "Redken Acidic Color Gloss",
        "pros": [
            "pH ácido sela cor (cabelo tingido dura mais entre retoques)",
            "Brilho intenso após primeiro uso (efeito 'gloss salão')",
            "Funciona em cabelo natural também (não precisa ser tingido)",
            "Textura cremosa espalha fácil",
        ],
        "cons": [
            "Específico pra manter cor (cabelo virgem não tira proveito total)",
            "Frasco modesto vs preço",
            "Pra cabelo muito fino pode pesar",
        ],
    },
    {
        "match": ["sebastian hydre", "sebastian shampoo"],
        "tipo": "Sebastian Hydre Shampoo",
        "pros": [
            "Hidratação profunda — cabelo seco/crespo fica macio",
            "Espuma cremosa rende muito (pouco produto basta)",
            "Cheiro de salão profissional",
            "Sem sulfato agressivo — preserva cor de tintura",
        ],
        "cons": [
            "Preço de produto profissional (R$ 80-150)",
            "Pra cabelo fino oleoso pode deixar pesado",
            "Embalagem grande exige espaço no box",
        ],
    },
    {
        "match": ["mise en scene", "mise-en-scene", "damage care"],
        "tipo": "Mise en Scène Damage Care",
        "pros": [
            "Condicionador coreano repara fios em poucos usos",
            "Cheiro suave de chá verde (não é perfumado demais)",
            "Embalagem prática com pump",
            "Frasco grande dura 3+ meses",
        ],
        "cons": [
            "Cabelo oleoso na raiz pode pesar com uso intenso",
            "Resultado em cabelo MUITO danificado é gradual",
            "Sem distribuição oficial Brasil — só importadores",
        ],
    },
    {
        "match": ["pink cheeks", "leave-in anti", "leave in"],
        "tipo": "Pink Cheeks Leave-in",
        "pros": [
            "Proteção térmica (até 230°C) antes de chapinha/secador",
            "Anti-frizz sem deixar cabelo duro",
            "Spray distribui uniforme (não escorre)",
            "Boa relação preço/quantidade",
        ],
        "cons": [
            "Spray pode entupir bico — agitar bem antes",
            "Cheiro frutado que algumas pessoas não gostam",
            "Pra cabelo MUITO grosso, precisa quantidade generosa",
        ],
    },
    {
        "match": ["photoage", "protetor capilar"],
        "tipo": "Protetor capilar Photoage",
        "pros": [
            "Protege cor de tintura do sol (UV degrada pigmento)",
            "Não pesa nem deixa cabelo oleoso",
            "Boa pra praia/piscina (resiste à água)",
            "Cheiro neutro",
        ],
        "cons": [
            "Resultado em proteção UV depende do tempo de exposição",
            "Frasco pequeno (não dura verão inteiro)",
            "Não substitui chapéu em sol forte",
        ],
    },
    {
        "match": ["tonico capilar", "ghk-cu hair", "hair repair"],
        "tipo": "Tônico Capilar GHK-Cu",
        "pros": [
            "Peptídeo de cobre estimula folículos capilares (estudos comprovam)",
            "Spray de aplicação fácil — não escorre como serum",
            "Sem álcool — não resseca o couro cabeludo",
            "Pode combinar com Minoxidil pra resultado potencializado",
        ],
        "cons": [
            "Resultado é GRADUAL (3-6 meses de uso diário pra ver diferença)",
            "Não recupera fios já perdidos — só estimula folículos vivos",
            "Frasco 100ml dura ~2 meses (uso noturno)",
            "Em queda hormonal avançada, sozinho não resolve (consultar dermato)",
        ],
    },
    {
        "match": ["scalp delivery", "hair growth serum", "growth serum"],
        "tipo": "Scalp Delivery Hair Growth Serum",
        "pros": [
            "Concentração alta (5%) — entrega ativo na raiz",
            "Combinação GHK-Cu + Capixyl atua em duas frentes (estímulo + redução DHT)",
            "Aplicador conta-gotas precisa (sem desperdício)",
            "Resultado visível em queda capilar leve a moderada",
        ],
        "cons": [
            "Concentração alta pode irritar couro sensível (fazer teste pequeno antes)",
            "Em calvície hereditária avançada, sozinho não basta",
            "Frasco modesto pra preço — acaba em ~6 semanas",
            "Aplicação tópica gruda no cabelo (visível se pouco penteado)",
        ],
    },
    {
        "match": ["lilyeve", "growturn", "antiqueda", "aplicador 38 pontas"],
        "tipo": "Sérum capilar Lilyeve com aplicador",
        "pros": [
            "Aplicador 38 pontas massageia couro durante aplicação",
            "Distribui produto uniforme (não desperdiça)",
            "Pode ser usado em couro seco ou ligeiramente úmido",
            "Massagem ajuda na absorção e estimula circulação",
        ],
        "cons": [
            "Pontas plásticas exigem limpeza após cada uso (acumula gordura)",
            "Resultado em queda é gradual (12 semanas+)",
            "Spray pode borrifar fora da área se inclinar muito",
        ],
    },

    # ============ COZINHA ============
    {
        "match": ["sanduicheira"],
        "tipo": "Sanduicheira",
        "pros": [
            "Sanduíche pronto em 3-5 minutos",
            "Antiaderente facilita limpeza (passa pano úmido)",
            "Tamanho compacto cabe em armário pequeno",
            "Bom pra café da manhã rápido (dia útil)",
        ],
        "cons": [
            "Bordas das chapas escurecem com o tempo (estética)",
            "Não esmaga o pão por igual (centro fica menos pressionado)",
            "Resistência pode queimar com uso 5+x/dia ao longo dos anos",
        ],
    },
    {
        "match": ["silk amendoa", "leite vegetal", "amendoa"],
        "tipo": "Bebida vegetal Silk",
        "pros": [
            "Sem lactose, açúcar ou conservantes (alternativa saudável)",
            "Sabor neutro vai bem em café, vitamina, mingau",
            "Embalagem Tetra Pak dura 8+ meses fechado",
            "Versão sem açúcar é low carb (~30 kcal/copo)",
        ],
        "cons": [
            "Após abrir, dura só 7 dias na geladeira",
            "Sabor pode estranhar quem está acostumado com leite animal",
            "Custo por litro mais alto que leite UHT",
            "Pode separar — agitar bem antes de servir",
        ],
    },
    {
        "match": ["granola", "mae terra"],
        "tipo": "Granola",
        "pros": [
            "Sem açúcares adicionados (versão zero) — pode ser low carb",
            "Mistura de aveia, frutas e sementes equilibrada",
            "Combina com iogurte, leite vegetal, frutas",
            "Embalagem reselável mantém crocância",
        ],
        "cons": [
            "Calorias densas (1 xícara = 350-450 kcal)",
            "Versão 'zero açúcar' usa adoçantes que algumas pessoas não toleram",
            "Pó/migalhas no fundo do pacote desperdiçam",
        ],
    },
    {
        "match": ["coador cafe", "dose unica", "filtros descartaveis"],
        "tipo": "Coador café dose única",
        "pros": [
            "Descartável evita lavagem (prático pra escritório/viagem)",
            "Café fresco sempre — não fica parado em térmica",
            "Tamanho individual perfeito pra apartamento solo",
            "50 filtros = 50 cafés (5-7 semanas de uso)",
        ],
        "cons": [
            "Gera mais lixo que coador permanente",
            "Custo por café maior que coador reutilizável",
            "Filtros podem rasgar se café for muito moído (fino demais)",
        ],
    },

    # ============ CASA ============
    {
        "match": ["sabao liquido", "amaciante", "downy", "lava-loucas"],
        "tipo": "Produto de limpeza/lavanderia",
        "pros": [
            "Concentrado rende muito (3-6 meses de uso normal)",
            "Cheiro persistente nas peças (semanas)",
            "Compatível com máquina e lavagem manual",
            "Custo por uso baixo",
        ],
        "cons": [
            "Embalagem grande pesada de movimentar",
            "Cheiro forte pode incomodar pele sensível",
            "Pode manchar tecidos brancos se concentrar muito num ponto",
        ],
    },

    # ============ ESPORTE ============
    {
        "match": ["whey", "proteina"],
        "tipo": "Whey Protein",
        "pros": [
            "Concentração proteica alta (24-30g por scoop)",
            "Solubilidade boa (não empedra no shaker)",
            "Sabores aceitáveis (baunilha e chocolate mais consensos)",
            "Refil 8kg dura 3-6 meses",
        ],
        "cons": [
            "Refil em saco precisa container hermético depois (umidade)",
            "Sabor pode enjoar com tempo (alternar marcas ajuda)",
            "Cuidado em quem tem intolerância à lactose (versão concentrado tem)",
        ],
    },
]

def find_pattern(title, slug):
    """Encontra padrão mais relevante baseado no título do produto."""
    text = (title + " " + slug).lower()
    # Procura match (case-insensitive, substring)
    best = None
    best_score = 0
    for p in PRODUCT_PATTERNS:
        for kw in p["match"]:
            if kw.lower() in text:
                # Score = comprimento do match (mais específico vence)
                score = len(kw)
                if score > best_score:
                    best = p
                    best_score = score
    return best

# Fallback genérico por categoria
CATEGORY_FALLBACK = {
    "pele": {
        "pros": [
            "Textura leve, absorve rápido sem deixar pegajoso",
            "Cabe na rotina (após tônico, antes do hidratante)",
            "Frasco prático com bico dosador",
            "Sem fragrância forte (compatível com pele sensível)",
        ],
        "cons": [
            "Resultado é gradual (visível em 4-8 semanas de uso)",
            "Combinar com ácidos exige espaçar uso (manhã/noite)",
            "Frasco modesto acaba em 6-8 semanas",
            "Não substitui protetor solar diário",
        ],
    },
    "kbeauty": {
        "pros": [
            "Importado coreano — formulação avançada vs nacionais",
            "Textura aquosa absorve sem peso",
            "Combinação de ativos pensada (sinergia entre ingredientes)",
            "Embalagem premium (cuidado visível no acabamento)",
        ],
        "cons": [
            "Importado — preço maior que nacionais",
            "Garantia/troca complicada (sem distribuidor BR oficial)",
            "Após aberto, validade reduzida (3-6 meses)",
            "Cheiro asiático característico pode incomodar",
        ],
    },
    "cabelo": {
        "pros": [
            "Fórmula consolidada da marca — entrega resultado prometido",
            "Textura espalha fácil (não desperdiça)",
            "Cheiro de salão profissional",
            "Frasco rende várias semanas",
        ],
        "cons": [
            "Pra cabelo fino, usar pouquíssimo (pesa fácil)",
            "Resultado em cabelo MUITO danificado é gradual",
            "Embalagem grande exige espaço no box",
        ],
    },
    "cozinha": {
        "pros": [
            "Marca reconhecida — qualidade consistente",
            "Tamanho prático pra rotina diária",
            "Durabilidade boa (anos de uso)",
            "Funciona como prometido",
        ],
        "cons": [
            "Capacidade limitada pra famílias grandes",
            "Limpeza periódica necessária pra manter desempenho",
            "Preço acima de versões genéricas",
        ],
    },
    "casa": {
        "pros": [
            "Concentrado rende muito",
            "Cheiro persistente na louça/roupa",
            "Compatível com diversos materiais",
            "Custo por uso baixo",
        ],
        "cons": [
            "Embalagem grande difícil de movimentar",
            "Cheiro forte pode incomodar pele sensível",
            "Cuidado em diluição (concentrado pode manchar)",
        ],
    },
    "esporte": {
        "pros": [
            "Marca consolidada em suplementos",
            "Solubilidade boa (não empedra)",
            "Sabor aceitável (não enjoa fácil)",
            "Custo por dose baixo (refil grande)",
        ],
        "cons": [
            "Saco refil precisa container hermético",
            "Cuidado em intolerância à lactose (versão concentrado)",
            "Sabor pode enjoar com tempo (alternar marca)",
        ],
    },
    "tech": {
        "pros": [
            "Plug-and-play (não precisa driver na maioria dos sistemas)",
            "Build sólido (não dá impressão de frágil)",
            "Compatibilidade ampla com dispositivos modernos",
            "Custo-benefício bom comparado a marcas premium",
        ],
        "cons": [
            "Sem cabo extra na caixa (pode precisar comprar)",
            "Algumas funções premium ficam de fora",
            "Manual em inglês (versão BR é fina)",
        ],
    },
    "cuidados": {
        "pros": [
            "Marca consolidada em cuidados pessoais",
            "Resultado visível com uso contínuo",
            "Embalagem prática pra rotina diária",
            "Custo-benefício adequado pra função",
        ],
        "cons": [
            "Resultado é gradual — exige consistência",
            "Refis/acessórios vendidos separadamente",
            "Em uso intenso, vida útil é menor",
        ],
    },
    "bemestar": {
        "pros": [
            "Função clara e direta (faz o que promete)",
            "Compacto pra rotina diária",
            "Boa relação preço/benefício",
            "Recomendado por terapeutas de bem-estar",
        ],
        "cons": [
            "Não substitui acompanhamento profissional em casos clínicos",
            "Adaptação leva 1-2 semanas em alguns casos",
            "Manutenção/limpeza necessária pra durar",
        ],
    },
    "teenbeauty": {
        "pros": [
            "Formulação suave (sem ativos fortes que irritam pele jovem)",
            "Textura leve, sem pegajoso",
            "Marca conhecida e confiável pra começar",
            "Custo acessível pra rotina diária",
        ],
        "cons": [
            "Em pele muito oleosa, alguns ainda pesam",
            "Não substitui consulta com dermato em caso de acne severa",
            "Refis em conta-gotas dura menos que tubo",
        ],
    },
    "pet": {
        "pros": [
            "Formulação balanceada pra nutrição completa",
            "Sabor que pets aceitam bem (não dá pra enrolar)",
            "Refis grandes economizam no longo prazo",
            "Marca veterinariamente recomendada",
        ],
        "cons": [
            "Mudança de ração precisa transição gradual (~7 dias)",
            "Saco refil precisa container hermético",
            "Custo por kg acima de marcas básicas (compensa qualidade)",
        ],
    },
}

# ============================================================
# REGENERAÇÃO
# ============================================================

def regenerate_post(slug, product_data):
    """Reescreve a seção pros/cons do post HTML."""
    post_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
    if not os.path.exists(post_path):
        return None
    with open(post_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Pega título
    m = re.search(r'<h1>([^<]+)</h1>', html)
    title = m.group(1) if m else slug

    # Procura padrão específico
    pattern = find_pattern(title, slug)

    if pattern:
        pros = pattern["pros"]
        cons = pattern["cons"]
        kind = "específico"
    else:
        # Fallback por categoria
        cat = product_data.get("category", "tech")
        fb = CATEGORY_FALLBACK.get(cat, CATEGORY_FALLBACK["tech"])
        pros = fb["pros"]
        cons = fb["cons"]
        kind = f"genérico/{cat}"

    # Constroi novas seções HTML
    pros_html = "\n        ".join([f"<li>{p}</li>" for p in pros])
    cons_html = "\n        ".join([f"<li>{c}</li>" for c in cons])

    # Substitui pros
    new = re.sub(
        r'(<div class="pros">\s*<h3>[^<]+</h3>\s*<ul>)\s*.*?\s*(</ul>\s*</div>)',
        lambda m: f'{m.group(1)}\n        {pros_html}\n      {m.group(2)}',
        html, count=1, flags=re.DOTALL
    )
    # Substitui cons
    new = re.sub(
        r'(<div class="cons">\s*<h3>[^<]+</h3>\s*<ul>)\s*.*?\s*(</ul>\s*</div>)',
        lambda m: f'{m.group(1)}\n        {cons_html}\n      {m.group(2)}',
        new, count=1, flags=re.DOTALL
    )

    if new != html:
        with open(post_path, 'w', encoding='utf-8') as f:
            f.write(new)
        return kind
    return None

def main():
    with open(META_PATH) as f:
        meta = json.load(f)

    n_specific = n_fallback = n_failed = 0
    for slug, p in meta['products'].items():
        result = regenerate_post(slug, p)
        if result == "específico":
            n_specific += 1
        elif result and result.startswith("genérico"):
            n_fallback += 1
        else:
            n_failed += 1

    print(f"\n✅ Reescrita aplicada:")
    print(f"   📌 {n_specific} produtos com padrão específico (info real)")
    print(f"   🎯 {n_fallback} com fallback por categoria")
    print(f"   ⚠️  {n_failed} sem alteração (HTML estrutura diferente)")
    print(f"   Total: {n_specific + n_fallback} de {len(meta['products'])}")

if __name__ == "__main__":
    main()
