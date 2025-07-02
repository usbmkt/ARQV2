from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os
import json
from datetime import datetime
import logging
from supabase import create_client, Client
from .analysis_fallback import create_fallback_analysis

analysis_bp = Blueprint('analysis', __name__)

# Configure Gemini AI
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
except Exception as e:
    print(f"Erro ao configurar Gemini AI: {e}")

# Configure Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = None

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Erro ao configurar Supabase: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@analysis_bp.route('/analyze', methods=['POST'])
def analyze_market():
    try:
        data = request.get_json()
        
        if not data or not data.get('nicho'):
            return jsonify({'error': 'Nicho é obrigatório'}), 400
        
        # Extract form data with validation
        nicho = data.get('nicho', '').strip()
        produto = data.get('produto', '').strip()
        descricao = data.get('descricao', '').strip()
        preco = data.get('preco', '')
        publico = data.get('publico', '').strip()
        concorrentes = data.get('concorrentes', '').strip()
        dados_adicionais = data.get('dadosAdicionais', '').strip()
        
        # Validate price
        try:
            preco_float = float(preco) if preco else None
        except ValueError:
            preco_float = None
        
        # Save initial analysis record to Supabase
        analysis_id = None
        if supabase:
            try:
                analysis_record = {
                    'nicho': nicho,
                    'produto': produto,
                    'descricao': descricao,
                    'preco': preco_float,
                    'publico': publico,
                    'concorrentes': concorrentes,
                    'dados_adicionais': dados_adicionais,
                    'status': 'processing',
                    'created_at': datetime.utcnow().isoformat()
                }
                
                result = supabase.table('analyses').insert(analysis_record).execute()
                if result.data:
                    analysis_id = result.data[0]['id']
                    logger.info(f"Análise criada no Supabase com ID: {analysis_id}")
            except Exception as e:
                logger.warning(f"Erro ao salvar no Supabase: {str(e)}")
        
        # Generate analysis using Gemini AI
        analysis_result = generate_market_analysis(
            nicho, produto, descricao, preco, publico, concorrentes, dados_adicionais
        )
        
        # Update analysis record in Supabase with results
        if supabase and analysis_id:
            try:
                update_data = {
                    'avatar_data': analysis_result.get('avatar', {}),
                    'positioning_data': analysis_result.get('positioning', {}),
                    'competition_data': analysis_result.get('competition', {}),
                    'marketing_data': analysis_result.get('marketing', {}),
                    'metrics_data': analysis_result.get('metrics', {}),
                    'funnel_data': analysis_result.get('funnel', {}),
                    'status': 'completed',
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                supabase.table('analyses').update(update_data).eq('id', analysis_id).execute()
                logger.info(f"Análise {analysis_id} atualizada no Supabase")
                
                # Add analysis_id to response
                analysis_result['analysis_id'] = analysis_id
                
            except Exception as e:
                logger.warning(f"Erro ao atualizar análise no Supabase: {str(e)}")
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Erro na análise: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@analysis_bp.route('/analyses', methods=['GET'])
def get_analyses():
    """Get list of recent analyses"""
    try:
        if not supabase:
            return jsonify({'error': 'Banco de dados não configurado'}), 500
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        nicho = request.args.get('nicho')
        
        query = supabase.table('analyses').select('*').order('created_at', desc=True)
        
        if nicho:
            query = query.eq('nicho', nicho)
        
        result = query.limit(limit).execute()
        
        return jsonify({
            'analyses': result.data,
            'count': len(result.data)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar análises: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@analysis_bp.route('/analyses/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Get specific analysis by ID"""
    try:
        if not supabase:
            return jsonify({'error': 'Banco de dados não configurado'}), 500
        
        result = supabase.table('analyses').select('*').eq('id', analysis_id).execute()
        
        if not result.data:
            return jsonify({'error': 'Análise não encontrada'}), 404
        
        analysis = result.data[0]
        
        # Structure the response
        structured_analysis = {
            'id': analysis['id'],
            'nicho': analysis['nicho'],
            'produto': analysis['produto'],
            'avatar': analysis['avatar_data'],
            'positioning': analysis['positioning_data'],
            'competition': analysis['competition_data'],
            'marketing': analysis['marketing_data'],
            'metrics': analysis['metrics_data'],
            'funnel': analysis['funnel_data'],
            'created_at': analysis['created_at'],
            'status': analysis['status']
        }
        
        return jsonify(structured_analysis)
        
    except Exception as e:
        logger.error(f"Erro ao buscar análise: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@analysis_bp.route('/nichos', methods=['GET'])
def get_nichos():
    """Get list of unique niches from analyses"""
    try:
        if not supabase:
            return jsonify({'error': 'Banco de dados não configurado'}), 500
        
        result = supabase.table('analyses').select('nicho').execute()
        
        # Extract unique niches
        nichos = list(set([item['nicho'] for item in result.data if item['nicho']]))
        nichos.sort()
        
        return jsonify({
            'nichos': nichos,
            'count': len(nichos)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar nichos: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

def generate_market_analysis(nicho, produto, descricao, preco, publico, concorrentes, dados_adicionais):
    """Generate comprehensive market analysis using Gemini AI"""
    
    # Create the prompt for Gemini
    prompt = create_analysis_prompt(nicho, produto, descricao, preco, publico, concorrentes, dados_adicionais)
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Parse the response and structure it
        analysis_text = response.text
        
        # Structure the analysis into the expected format
        structured_analysis = structure_analysis_response(analysis_text, nicho, produto, preco)
        
        return structured_analysis
        
    except Exception as e:
        logger.error(f"Erro ao gerar análise com Gemini: {str(e)}")
        # Return fallback analysis
        return create_fallback_analysis(nicho, produto, preco)

def create_analysis_prompt(nicho, produto, descricao, preco, publico, concorrentes, dados_adicionais):
    """Create a comprehensive prompt for Gemini AI analysis"""
    
    prompt = f"""Você é um especialista em análise de mercado e estratégia de lançamento de produtos digitais no Brasil. Sua missão é ir além do óbvio, entregando uma análise extremamente detalhada, estratégica e acionável, capaz de surpreender e guiar o lançamento de um produto com profundidade e inteligência. Pense como um consultor de alto nível que precisa justificar cada recomendação com dados e lógica de mercado.

INFORMAÇÕES DO PRODUTO/SERVIÇO:
- Nicho: {nicho}
- Produto/Serviço: {produto if produto else 'Não especificado'}
- Descrição: {descricao if descricao else 'Não fornecida'}
- Preço: R$ {preco if preco else 'Não definido'}
- Público-Alvo: {publico if publico else 'Não especificado'}
- Concorrentes: {concorrentes if concorrentes else 'Não informados'}
- Dados Adicionais: {dados_adicionais if dados_adicionais else 'Nenhum'}

INSTRUÇÕES DETALHADAS PARA ANÁLISE (SEJA EXTREMAMENTE ESPECÍFICO E PROFUNDO):

## 🎯 DEFINIÇÃO DO ESCOPO
Identifique e detalhe:
- Nicho principal e subnichos
- Produto/serviço ideal para lançamento
- Proposta de valor única

## 👥 ANÁLISE DO AVATAR (CLIENTE IDEAL)

### Demografia:
Pesquise e defina:
- Faixa etária predominante
- Gênero e distribuição
- Localização geográfica principal
- Faixa de renda média
- Nível de escolaridade comum
- Profissões mais frequentes

### Psicografia:
Mapeie:
- 3 valores principais
- Estilo de vida característico
- 2 principais aspirações
- 3 medos mais comuns
- 2 frustrações recorrentes

### Comportamento Digital:
Identifique:
- 2 plataformas mais usadas
- Horários de pico online
- Tipos de conteúdo preferidos
- Influenciadores que seguem

## 💔 MAPEAMENTO DE DORES E DESEJOS

Liste as 5 principais dores com:
- Descrição detalhada
- Como impacta a vida
- Nível de urgência (Alta/Média/Baixa)

Identifique:
- Estado atual vs. Estado desejado
- Obstáculos percebidos
- Sonho secreto não verbalizado

## 🏆 ANÁLISE DA CONCORRÊNCIA

Pesquise e liste:
- 2 concorrentes diretos principais (com preços, USP, forças e fraquezas)
- 2 concorrentes indiretos
- 3 gaps identificados no mercado

## 💰 ANÁLISE DE MERCADO E METRIFICAÇÃO

### Calcule o TAM/SAM/SOM:
- TAM: População total × % mercado × ticket médio anual
- SAM: TAM × % segmento × % alcance realista
- SOM: SAM × % market share possível

### Identifique:
- Volume de busca mensal do nicho
- Tendências em alta e em queda
- Sazonalidade (melhores e piores meses)

## 🎯 ANÁLISE DE PALAVRAS-CHAVE E CUSTOS

Pesquise as 5 principais palavras-chave com:
- Volume de busca mensal
- CPC e CPM médios
- Dificuldade SEO
- Intenção de busca

### Custos por plataforma:
Estime para Facebook, Google, YouTube e TikTok:
- CPM médio
- CPC médio
- CPL médio
- Taxa de conversão esperada

## 📊 MÉTRICAS DE PERFORMANCE

Defina benchmarks do mercado:
- CAC médio por canal
- Funil de conversão padrão (%)
- LTV médio e LTV:CAC ratio
- ROI esperado por canal

## 🗣️ VOZ DO MERCADO

Identifique:
- 3 principais objeções e como contorná-las
- Linguagem específica (termos, gírias, gatilhos)
- 3 crenças limitantes comuns

## 📊 HISTÓRICO DE LANÇAMENTOS

Pesquise:
- 2 cases de sucesso (com números)
- 1 fracasso notável e lições aprendidas

## 💸 ANÁLISE DE PREÇOS

Mapeie:
- Faixas de preço (Low/Mid/High ticket)
- Elasticidade e sensibilidade a preço
- Sweet spot de preço

## 🚀 ESTRATÉGIA DE AQUISIÇÃO

Recomende:
- Mix ideal de canais (% do budget)
- Budget por fase (pré/lançamento/pós)
- CPL esperado por canal

## 📈 PROJEÇÕES

Apresente 3 cenários (conservador/realista/otimista):
- Taxa de conversão
- Faturamento projetado
- ROI esperado

## 🎁 BÔNUS E GARANTIAS

Sugira:
- 3 bônus valorizados com valor percebido
- Tipo de garantia ideal

## 🎯 SÍNTESE ESTRATÉGICA

Crie:
- Big Idea única para o lançamento
- Promessa principal irresistível
- Mecanismo único de entrega
- Provas de conceito necessárias
- Meta SMART completa

## 💡 PLANO DE AÇÃO

Liste 7 próximos passos prioritários e práticos.

FORMATO DE RESPOSTA:
Responda EXCLUSIVAMENTE em formato JSON estruturado, seguindo rigorosamente o esquema abaixo. Cada campo deve ser preenchido com dados relevantes e detalhados, conforme as instruções acima. Se um campo não puder ser preenchido com informações específicas, use 'N/A' ou um array vazio, mas evite omitir seções inteiras.

```json
{{
  "avatar": {{
    "nome": "[Nome do Avatar]",
    "idade": "[Idade]",
    "profissao": "[Profissão]",
    "renda": "[Faixa Salarial]",
    "localizacao": "[Cidade/Estado]",
    "estado_civil": "[Estado Civil]",
    "contexto": "[Parágrafo sobre estilo de vida e rotina]",
    "barreira_critica": "[A dor latente e suas consequências]",
    "estado_desejado": "[O cenário ideal e transformador]",
    "frustracoes": [
      "[Frustração 1]",
      "[Frustração 2]",
      "[Frustração 3]",
      "[Frustração 4]",
      "[Frustração 5]"
    ],
    "crenca_limitante": "[A crença enraizada e sua formação]",
    "sonhos_aspiracoes": [
      "[Sonho/Aspiração 1]",
      "[Sonho/Aspiração 2]",
      "[Sonho/Aspiração 3]"
    ],
    "onde_online": [
      "[Rede Social/Fórum 1]",
      "[Rede Social/Fórum 2]"
    ]
  }},
  "positioning": {{
    "declaracao": "[Declaração de Posicionamento Única]",
    "angulos": [
      {{
        "tipo": "Lógico",
        "mensagem": "[Mensagem lógica com dados]"
      }},
      {{
        "tipo": "Emocional",
        "mensagem": "[Mensagem emocional]"
      }},
      {{
        "tipo": "Contraste",
        "mensagem": "[Mensagem de contraste]"
      }},
      {{
        "tipo": "Urgência/Escassez",
        "mensagem": "[Mensagem de urgência/escassez]"
      }}
    ],
    "proposta_valor_irrefutavel": "[Proposta de Valor Irrefutável]"
  }},
  "competition": {{
    "concorrentes": [
      {{
        "nome": "[Nome Concorrente 1]",
        "produto_servico": "[Produto/Serviço Concorrente 1]",
        "preco": "[Preço Concorrente 1]",
        "forcas": "[Forças Concorrente 1]",
        "fraquezas": "[Fraquezas Concorrente 1]",
        "oportunidade_diferenciacao": "[Oportunidade de Diferenciação 1]"
      }},
      {{
        "nome": "[Nome Concorrente 2]",
        "produto_servico": "[Produto/Serviço Concorrente 2]",
        "preco": "[Preço Concorrente 2]",
        "forcas": "[Forças Concorrente 2]",
        "fraquezas": "[Fraquezas Concorrente 2]",
        "oportunidade_diferenciacao": "[Oportunidade de Diferenciação 2]"
      }}
    ],
    "lacunas_mercado": [
      "[Lacuna 1]",
      "[Lacuna 2]",
      "[Lacuna 3]"
    ],
    "benchmarking_melhores_praticas": [
      "[Melhor Prática 1]",
      "[Melhor Prática 2]"
    ]
  }},
  "marketing": {{
    "landing_page_headlines": [
      "[Headline 1]",
      "[Headline 2]",
      "[Headline 3]"
    ],
    "pagina_vendas_estrutura": [
      {{
        "titulo": "[Título Seção 1]",
        "resumo_conteudo": "[Resumo Conteúdo Seção 1]"
      }},
      {{
        "titulo": "[Título Seção 2]",
        "resumo_conteudo": "[Resumo Conteúdo Seção 2]"
      }}
    ],
    "emails_assuntos": [
      "[Assunto E-mail 1]",
      "[Assunto E-mail 2]",
      "[Assunto E-mail 3]",
      "[Assunto E-mail 4]",
      "[Assunto E-mail 5]"
    ],
    "anuncios_roteiros": [
      {{
        "angulo": "[Ângulo do Anúncio 1]",
        "roteiro": "[Roteiro Anúncio 1]"
      }},
      {{
        "angulo": "[Ângulo do Anúncio 2]",
        "roteiro": "[Roteiro Anúncio 2]"
      }},
      {{
        "angulo": "[Ângulo do Anúncio 3]",
        "roteiro": "[Roteiro Anúncio 3]"
      }}
    ]
  }},
  "metrics": {{
    "leads_necessarios": "[Número de Leads]",
    "taxa_conversao_realista": "[Taxa de Conversão]%",
    "projecao_faturamento_3_meses": "R$ [Valor]",
    "projecao_faturamento_6_meses": "R$ [Valor]",
    "projecao_faturamento_12_meses": "R$ [Valor]",
    "roi_otimista": "[ROI Otimista]%",
    "roi_realista": "[ROI Realista]%",
    "distribuicao_investimento": [
      {{
        "canal": "[Canal 1]",
        "percentual": "[Percentual]%",
        "valor": "R$ [Valor]"
      }},
      {{
        "canal": "[Canal 2]",
        "percentual": "[Percentual]%",
        "valor": "R$ [Valor]"
      }}
    ]
  }},
  "funnel": {{
    "fases": [
      {{
        "nome": "[Nome Fase 1]",
        "objetivo": "[Objetivo Fase 1]",
        "acoes_marketing": "[Ações de Marketing Fase 1]",
        "metricas_acompanhamento": [
          "[Métrica 1]",
          "[Métrica 2]"
        ]
      }},
      {{
        "nome": "[Nome Fase 2]",
        "objetivo": "[Objetivo Fase 2]",
        "acoes_marketing": "[Ações de Marketing Fase 2]",
        "metricas_acompanhamento": [
          "[Métrica 1]",
          "[Métrica 2]"
        ]
      }}
    ],
    "cronograma_execucao": "[Exemplo de Cronograma]",
    "metricas_criticas": [
      "[Métrica Crítica 1]",
      "[Métrica Crítica 2]",
      "[Métrica Crítica 3]",
      "[Métrica Crítica 4]",
      "[Métrica Crítica 5]"
    ]
  }}
}}
```

Seja criativo, analítico e entregue uma análise que realmente agregue valor estratégico. Não use placeholders como "[Nome do Avatar]", preencha com informações concretas e realistas. Surpreenda-me com a profundidade e a aplicabilidade das suas análises!

IMPORTANTE: 
- Use dados reais e atualizados quando possível
- Faça estimativas conservadoras baseadas em padrões do mercado
- Seja específico com números e métricas
- Foque em insights acionáveis"""

    return prompt[Escassez] Últimas Vagas para {produto} - Não Fique de Fora!",
                f"[Último Aviso] ⏰ {produto} Encerra Hoje à Meia-Noite - Sua Última Chance!"
            ],
            "anuncios_roteiros": [
                {
                    "angulo": "Dor e Solução",
                    "roteiro": f"Você se sente estagnado(a) em {nicho}, sem saber como escalar seus resultados? Apresentamos {produto}, a metodologia que vai te guiar do zero ao sucesso, com estratégias comprovadas e acompanhamento exclusivo. Clique em 'Saiba Mais' e transforme sua realidade!"
                },
                {
                    "angulo": "Prova Social e Transformação",
                    "roteiro": f"Conheça a história de João, que saiu do zero e alcançou R$X mil em {nicho} com {produto}. Se ele conseguiu, você também pode! Clique em 'Inscreva-se' e comece sua transformação hoje mesmo!"
                },
                {
                    "angulo": "Urgência e Benefício",
                    "roteiro": f"As vagas para {produto} estão se esgotando! Não perca a oportunidade de dominar {nicho} e conquistar a liberdade que você sempre sonhou. Clique em 'Garanta Sua Vaga' antes que seja tarde demais!"
                }
            ]
        },
        "metrics": {
            "leads_necessarios": leads_projetados,
            "taxa_conversao_realista": conversao,
            "projecao_faturamento_3_meses": f"R$ {int(faturamento * 0.3).toLocaleString()}",
            "projecao_faturamento_6_meses": f"R$ {int(faturamento * 0.6).toLocaleString()}",
            "projecao_faturamento_12_meses": f"R$ {faturamento.toLocaleString()}",
            "roi_otimista": int(((faturamento * 1.5 - investimento_total) / investimento_total) * 100) if investimento_total > 0 else 0,
            "roi_realista": roi,
            "distribuicao_investimento": [
                {
                    "canal": "Tráfego Pago (Meta Ads, Google Ads)",
                    "percentual": 60,
                    "valor": f"R$ {int(investimento_total * 0.6).toLocaleString()}"
                },
                {
                    "canal": "Conteúdo Orgânico (SEO, Blog, Redes Sociais)",
                    "percentual": 20,
                    "valor": f"R$ {int(investimento_total * 0.2).toLocaleString()}"
                },
                {
                    "canal": "E-mail Marketing e Automação",
                    "percentual": 10,
                    "valor": f"R$ {int(investimento_total * 0.1).toLocaleString()}"
                },
                {
                    "canal": "Parcerias e Afiliados",
                    "percentual": 10,
                    "valor": f"R$ {int(investimento_total * 0.1).toLocaleString()}"
                }
            ]
        },
        "funnel": {
            "fases": [
                {
                    "nome": "Consciência (Awareness)",
                    "objetivo": "Atrair a atenção do público-alvo e gerar reconhecimento da marca/produto.",
                    "acoes_marketing": "Anúncios em redes sociais, conteúdo de blog otimizado para SEO, vídeos curtos no YouTube/TikTok, posts informativos no Instagram.",
                    "metricas_acompanhamento": [
                        "Alcance e Impressões",
                        "Tráfego no Site/Landing Page",
                        "Engajamento (curtidas, comentários, compartilhamentos)"
                    ]
                },
                {
                    "nome": "Interesse (Interest)",
                    "objetivo": "Educar o lead sobre o problema e a solução, despertando o interesse no produto.",
                    "acoes_marketing": "Webinars gratuitos, e-books/guias, sequências de e-mail marketing com conteúdo de valor, retargeting de anúncios para visitantes do site.",
                    "metricas_acompanhamento": [
                        "Leads Gerados (e-mails capturados)",
                        "Taxa de Abertura de E-mails",
                        "Taxa de Conversão de Landing Pages"
                    ]
                },
                {
                    "nome": "Consideração (Consideration)",
                    "objetivo": "Apresentar o produto como a melhor solução, construindo confiança e credibilidade.",
                    "acoes_marketing": "Página de vendas detalhada, depoimentos de clientes, estudos de caso, lives de perguntas e respostas, demonstrações do produto.",
                    "metricas_acompanhamento": [
                        "Cliques na Página de Vendas",
                        "Tempo na Página de Vendas",
                        "Interações com Prova Social"
                    ]
                },
                {
                    "nome": "Intenção (Intent)",
                    "objetivo": "Remover objeções finais e incentivar a decisão de compra.",
                    "acoes_marketing": "E-mails de quebra de objeções, bônus exclusivos por tempo limitado, ofertas especiais, remarketing para carrinhos abandonados.",
                    "metricas_acompanhamento": [
                        "Adições ao Carrinho",
                        "Inícios de Checkout",
                        "Taxa de Abandono de Carrinho"
                    ]
                },
                {
                    "nome": "Compra (Purchase)",
                    "objetivo": "Converter o lead em cliente.",
                    "acoes_marketing": "Processo de checkout simplificado, múltiplas opções de pagamento, suporte ao cliente disponível.",
                    "metricas_acompanhamento": [
                        "Vendas Realizadas",
                        "Ticket Médio",
                        "Custo por Aquisição (CPA)"
                    ]
                },
                {
                    "nome": "Pós-Venda e Fidelização (Retention & Advocacy)",
                    "objetivo": "Garantir a satisfação do cliente, incentivar a recompra e transformá-lo em promotor da marca.",
                    "acoes_marketing": "E-mails de onboarding, suporte contínuo, programas de fidelidade, pedidos de feedback, incentivo a depoimentos e indicações.",
                    "metricas_acompanhamento": [
                        "Taxa de Retenção de Clientes",
                        "Lifetime Value (LTV)",
                        "Net Promoter Score (NPS)",
                        "Indicações"
                    ]
                }
            ],
            "cronograma_execucao": "**Semana 1: Aquecimento e Consciência** (Foco em conteúdo de valor e anúncios de topo de funil). **Semana 2: Lançamento e Interesse** (Webinar, sequência de e-mails, abertura de carrinho). **Semana 3: Consideração e Objeções** (Lives de Q&A, depoimentos, e-mails de quebra de objeções). **Semana 4: Urgência e Fechamento** (Bônus final, últimos avisos, fechamento do carrinho). **Pós-Lançamento:** Onboarding e fidelização contínua.",
            "metricas_criticas": [
                "Custo por Lead (CPL)",
                "Taxa de Conversão do Funil",
                "Custo por Aquisição (CPA)",
                "Retorno sobre Investimento (ROI)",
                "Lifetime Value (LTV)"
            ]
        }
    }

