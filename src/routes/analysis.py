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
    
    prompt = f"""
Você é um especialista em análise de mercado e estratégia de lançamento de produtos digitais no Brasil. Sua missão é ir além do óbvio, entregando uma análise extremamente detalhada, estratégica e acionável, capaz de surpreender e guiar o lançamento de um produto com profundidade e inteligência. Pense como um consultor de alto nível que precisa justificar cada recomendação com dados e lógica de mercado.

INFORMAÇÕES DO PRODUTO/SERVIÇO:
- Nicho: {nicho}
- Produto/Serviço: {produto if produto else 'Não especificado'}
- Descrição: {descricao if descricao else 'Não fornecida'}
- Preço: R$ {preco if preco else 'Não definido'}
- Público-Alvo: {publico if publico else 'Não especificado'}
- Concorrentes: {concorrentes if concorrentes else 'Não informados'}
- Dados Adicionais: {dados_adicionais if dados_adicionais else 'Nenhum'}

INSTRUÇÕES DETALHADAS PARA ANÁLISE (SEJA EXTREMAMENTE ESPECÍFICO E PROFUNDO):

1.  **PERFIL DO AVATAR (Arqueologia Profunda):**
    -   **Nome e Contexto:** Crie um nome, idade, profissão, nível de renda (faixa salarial), localização (cidade/estado brasileiro), estado civil e um breve parágrafo sobre seu estilo de vida e rotina diária. Detalhe como o nicho se encaixa ou impacta a vida desse avatar.
    -   **Barreira Crítica (A Dor Latente):** Identifique a dor mais profunda e não óbvia que o avatar enfrenta, aquela que ele talvez nem verbalize, mas que o impede de avançar. Explique as consequências dessa dor.
    -   **Estado Desejado (A Transformação):** Descreva o cenário ideal e transformador que o avatar busca, indo além da solução do problema. Como a vida dele será radicalmente melhor após a transformação?
    -   **Frustrações Diárias (Mínimo 5):** Liste no mínimo 5 frustrações específicas e cotidianas relacionadas ao nicho, com exemplos práticos. Como essas frustrações se manifestam no dia a dia do avatar?
    -   **Crença Limitante Principal:** Qual a principal crença enraizada que o avatar possui e que o impede de buscar ou acreditar na solução? Como essa crença foi formada?
    -   **Sonhos e Aspirações:** Quais são os 3 maiores sonhos e aspirações do avatar, e como o produto/serviço se conecta a eles?
    -   **Onde o Avatar Está Online:** Quais redes sociais, fóruns, grupos, blogs ou sites ele frequenta para buscar informações ou se conectar com pessoas do nicho?

2.  **ESTRATÉGIA DE POSICIONAMENTO (Diferenciação Inovadora):**
    -   **Declaração de Posicionamento Única (DPU):** Crie uma DPU que seja concisa, memorável e que destaque o diferencial competitivo de forma irrefutável. Deve ser algo que o concorrente não possa copiar facilmente.
    -   **Ângulos de Mensagem (Mínimo 4 - Lógico, Emocional, Contraste, Urgência/Escassez):**
        -   **Lógico:** Foco em dados, fatos, metodologia e resultados comprováveis. Use números e estatísticas (mesmo que hipotéticas, mas realistas).
        -   **Emocional:** Conecte-se com os sentimentos, medos e desejos mais profundos do avatar. Como o produto resolve a dor emocional?
        -   **Contraste:** Compare o produto com a concorrência ou com a situação atual do avatar, destacando claramente a superioridade.
        -   **Urgência/Escassez:** Crie um senso de oportunidade limitada, sem ser agressivo, mas incentivando a ação imediata.
    -   **Proposta de Valor Irrefutável (PVI):** Detalhe a PVI, explicando por que o produto é a melhor e mais segura escolha para o avatar, e o que o torna indispensável.

3.  **ANÁLISE COMPETITIVA (Inteligência de Mercado):**
    -   **Concorrentes Diretos (Mínimo 3):** Analise no mínimo 3 concorrentes diretos (se não houver, crie perfis realistas). Para cada um:
        -   **Nome e Produto/Serviço:**
        -   **Preço:** (Estime se não souber, com base no nicho)
        -   **Forças:** O que eles fazem bem? Qual o ponto forte?
        -   **Fraquezas:** Onde eles falham? Quais as reclamações comuns?
        -   **Oportunidades de Diferenciação:** Como o seu produto pode se destacar e preencher as lacunas deixadas por eles?
    -   **Lacunas no Mercado:** Identifique no mínimo 3 lacunas claras e inexploradas no mercado que o seu produto pode preencher, transformando-as em vantagens competitivas.
    -   **Benchmarking de Melhores Práticas:** Quais são as 2-3 melhores práticas dos concorrentes que podem ser adaptadas ou superadas pelo seu produto?

4.  **MATERIAIS DE MARKETING (Copy Persuasiva e Estratégica):**
    -   **Headline para Landing Page (Mínimo 3 Opções):** Crie 3 headlines altamente persuasivas, utilizando diferentes gatilhos mentais (benefício, curiosidade, prova social, urgência).
    -   **Estrutura de Página de Vendas (Seções Detalhadas):** Desenvolva uma estrutura completa para uma página de vendas de alta conversão, com títulos e um breve resumo do conteúdo de cada seção (ex: Título, Problema, Solução, Prova Social, Oferta, Bônus, FAQ, CTA).
    -   **Assuntos de E-mail para Sequência (Mínimo 5):** Sugira 5 assuntos de e-mail para uma sequência de vendas, com foco em diferentes etapas do funil (aquecimento, lançamento, quebra de objeções, escassez, último aviso).
    -   **Roteiros de Anúncios de 15-30 Segundos (Mínimo 3):** Crie 3 roteiros de anúncios curtos para vídeo (15-30 segundos), com foco em diferentes ângulos de mensagem e chamadas para ação claras.

5.  **PROJEÇÕES FINANCEIRAS (Realistas e Otimistas):**
    -   **Leads Necessários para o Faturamento:** Estime o número de leads qualificados necessários para atingir uma meta de faturamento mensal realista (ex: R$ 10.000, R$ 50.000, R$ 100.000), considerando o preço do produto.
    -   **Taxa de Conversão Realista:** Calcule uma taxa de conversão realista para o nicho e produto (ex: 1% a 5%), justificando o valor.
    -   **Projeção de Faturamento Mensal/Anual:** Apresente uma projeção de faturamento para os primeiros 3, 6 e 12 meses, com base nas estimativas anteriores.
    -   **ROI Esperado (Cenário Otimista e Realista):** Calcule o Retorno sobre Investimento (ROI) esperado para um cenário otimista e um realista, considerando um investimento inicial hipotético em marketing.
    -   **Distribuição de Investimento por Canal (Percentual e Valor):** Sugira uma distribuição percentual e em valor (ex: R$ 20.000) do investimento em marketing por canal (ex: Tráfego Pago, Conteúdo Orgânico, E-mail Marketing, Parcerias).

6.  **FUNIL DE VENDAS (Estratégia Detalhada):**
    -   **Fases do Funil (Mínimo 5):** Defina no mínimo 5 fases detalhadas do funil de vendas (ex: Consciência, Interesse, Consideração, Intenção, Avaliação, Compra, Pós-Venda). Para cada fase, descreva:
        -   **Objetivo:** O que se espera do lead nessa fase?
        -   **Ações de Marketing:** Quais ações serão tomadas para mover o lead para a próxima fase?
        -   **Métricas de Acompanhamento:** Quais KPIs serão monitorados?
    -   **Cronograma de Execução (Exemplo de 30-60 dias):** Estabeleça um cronograma de execução realista para o lançamento, com marcos importantes e prazos (ex: Semana 1: Aquecimento, Semana 2: Lançamento, etc.).
    -   **Métricas de Acompanhamento Críticas:** Liste as 5 métricas mais importantes para acompanhar o sucesso do funil, justificando cada uma.

FORMATO DE RESPOSTA:
Responda EXCLUSIVAMENTE em formato JSON estruturado, seguindo rigorosamente o esquema abaixo. Cada campo deve ser preenchido com dados relevantes e detalhados, conforme as instruções acima. Se um campo não puder ser preenchido com informações específicas, use 'N/A' ou um array vazio, mas evite omitir seções inteiras.

```json
{
  "avatar": {
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
  },
  "positioning": {
    "declaracao": "[Declaração de Posicionamento Única]",
    "angulos": [
      {
        "tipo": "Lógico",
        "mensagem": "[Mensagem lógica com dados]"
      },
      {
        "tipo": "Emocional",
        "mensagem": "[Mensagem emocional]"
      },
      {
        "tipo": "Contraste",
        "mensagem": "[Mensagem de contraste]"
      },
      {
        "tipo": "Urgência/Escassez",
        "mensagem": "[Mensagem de urgência/escassez]"
      }
    ],
    "proposta_valor_irrefutavel": "[Proposta de Valor Irrefutável]"
  },
  "competition": {
    "concorrentes": [
      {
        "nome": "[Nome Concorrente 1]",
        "produto_servico": "[Produto/Serviço Concorrente 1]",
        "preco": "[Preço Concorrente 1]",
        "forcas": "[Forças Concorrente 1]",
        "fraquezas": "[Fraquezas Concorrente 1]",
        "oportunidade_diferenciacao": "[Oportunidade de Diferenciação 1]"
      },
      {
        "nome": "[Nome Concorrente 2]",
        "produto_servico": "[Produto/Serviço Concorrente 2]",
        "preco": "[Preço Concorrente 2]",
        "forcas": "[Forças Concorrente 2]",
        "fraquezas": "[Fraquezas Concorrente 2]",
        "oportunidade_diferenciacao": "[Oportunidade de Diferenciação 2]"
      },
      {
        "nome": "[Nome Concorrente 3]",
        "produto_servico": "[Produto/Serviço Concorrente 3]",
        "preco": "[Preço Concorrente 3]",
        "forcas": "[Forças Concorrente 3]",
        "fraquezas": "[Fraquezas Concorrente 3]",
        "oportunidade_diferenciacao": "[Oportunidade de Diferenciação 3]"
      }
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
  },
  "marketing": {
    "landing_page_headlines": [
      "[Headline 1]",
      "[Headline 2]",
      "[Headline 3]"
    ],
    "pagina_vendas_estrutura": [
      {
        "titulo": "[Título Seção 1]",
        "resumo_conteudo": "[Resumo Conteúdo Seção 1]"
      },
      {
        "titulo": "[Título Seção 2]",
        "resumo_conteudo": "[Resumo Conteúdo Seção 2]"
      }
    ],
    "emails_assuntos": [
      "[Assunto E-mail 1]",
      "[Assunto E-mail 2]",
      "[Assunto E-mail 3]",
      "[Assunto E-mail 4]",
      "[Assunto E-mail 5]"
    ],
    "anuncios_roteiros": [
      {
        "angulo": "[Ângulo do Anúncio 1]",
        "roteiro": "[Roteiro Anúncio 1]"
      },
      {
        "angulo": "[Ângulo do Anúncio 2]",
        "roteiro": "[Roteiro Anúncio 2]"
      },
      {
        "angulo": "[Ângulo do Anúncio 3]",
        "roteiro": "[Roteiro Anúncio 3]"
      }
    ]
  },
  "metrics": {
    "leads_necessarios": "[Número de Leads]",
    "taxa_conversao_realista": "[Taxa de Conversão]%",
    "projecao_faturamento_3_meses": "R$ [Valor]",
    "projecao_faturamento_6_meses": "R$ [Valor]",
    "projecao_faturamento_12_meses": "R$ [Valor]",
    "roi_otimista": "[ROI Otimista]%",
    "roi_realista": "[ROI Realista]%",
    "distribuicao_investimento": [
      {
        "canal": "[Canal 1]",
        "percentual": "[Percentual]%",
        "valor": "R$ [Valor]"
      },
      {
        "canal": "[Canal 2]",
        "percentual": "[Percentual]%",
        "valor": "R$ [Valor]"
      }
    ]
  },
  "funnel": {
    "fases": [
      {
        "nome": "[Nome Fase 1]",
        "objetivo": "[Objetivo Fase 1]",
        "acoes_marketing": "[Ações de Marketing Fase 1]",
        "metricas_acompanhamento": [
          "[Métrica 1]",
          "[Métrica 2]"
        ]
      },
      {
        "nome": "[Nome Fase 2]",
        "objetivo": "[Objetivo Fase 2]",
        "acoes_marketing": "[Ações de Marketing Fase 2]",
        "metricas_acompanhamento": [
          "[Métrica 1]",
          "[Métrica 2]"
        ]
      }
    ],
    "cronograma_execucao": "[Exemplo de Cronograma]",
    "metricas_criticas": [
      "[Métrica Crítica 1]",
      "[Métrica Crítica 2]",
      "[Métrica Crítica 3]",
      "[Métrica Crítica 4]",
      "[Métrica Crítica 5]"
    ]
  }
}
```

Seja criativo, analítico e entregue uma análise que realmente agregue valor estratégico. Não use placeholders como "[Nome do Avatar]", preencha com informações concretas e realistas. Surpreenda-me com a profundidade e a aplicabilidade das suas análises!"""
    
    return prompt

def structure_analysis_response(analysis_text, nicho, produto, preco):
    """Structure the Gemini response into the expected format"""
    
    try:
        # Try to parse JSON if Gemini returned structured data
        if analysis_text.strip().startswith('{'):
            return json.loads(analysis_text)
    except:
        pass
    
    # If not JSON, create structured response from text
    return create_structured_analysis(analysis_text, nicho, produto, preco)

def create_structured_analysis(analysis_text, nicho, produto, preco):
    """Create structured analysis from text response or use fallback if Gemini fails to return JSON"""
    
    # Default values for projections if not provided by Gemini or if parsing fails
    preco_num = float(preco) if preco else 997
    
    # Fallback projections (more realistic)
    leads_projetados = 5000  # Aumentado para refletir um cenário mais ambicioso
    conversao = 2.0        # Taxa de conversão ligeiramente otimista
    vendas = int(leads_projetados * (conversao / 100))
    faturamento = int(vendas * preco_num)
    investimento_total = 30000 # Aumentado o investimento inicial
    roi = int(((faturamento - investimento_total) / investimento_total) * 100) if investimento_total > 0 else 0

    # Fallback structure, should ideally be replaced by Gemini's output
    return {
        "avatar": {
            "nome": f"Avatar Ideal - {nicho}",
            "idade": "30-45 anos",
            "profissao": "Empreendedor Digital, Profissional Liberal ou Gestor",
            "renda": "R$ 8.000 - R$ 25.000",
            "localizacao": "Grandes centros urbanos (São Paulo, Rio de Janeiro, Belo Horizonte)",
            "estado_civil": "Casado(a) com filhos ou solteiro(a) focado(a) na carreira",
            "contexto": f"Busca constante por crescimento profissional e financeiro, mas sente-se sobrecarregado(a) com a quantidade de informações e a falta de um método claro para {nicho}. Valoriza a família e o tempo livre, mas muitas vezes sacrifica ambos em busca de resultados.",
            "barreira_critica": f"A incapacidade de transformar conhecimento em resultados práticos e escaláveis em {nicho}, levando à estagnação e frustração, apesar de todo o esforço e investimento em cursos e mentorias. A dor é a sensação de estar sempre correndo, mas nunca saindo do lugar.",
            "estado_desejado": f"Alcançar a maestria em {nicho}, com um negócio ou carreira próspera que proporcione liberdade financeira e de tempo, permitindo desfrutar mais da vida e da família, sem abrir mão do crescimento.",
            "frustracoes": [
                f"Excesso de informação e dificuldade em filtrar o que realmente funciona em {nicho}",
                f"Investimento em cursos que não entregam resultados práticos ou aplicáveis",
                f"Sensação de estar sempre apagando incêndios e sem tempo para planejar estrategicamente",
                f"Dificuldade em delegar tarefas e construir uma equipe eficiente",
                f"Medo de perder oportunidades por não estar atualizado(a) com as últimas tendências em {nicho}"
            ],
            "crenca_limitante": f"Acredita que o sucesso em {nicho} exige sacrifícios extremos e que é preciso trabalhar exaustivamente para ter resultados, ou que não possui o 'dom' natural para a área.",
            "sonhos_aspiracoes": [
                "Ter um negócio autogerenciável e lucrativo em {nicho}",
                "Ter mais tempo de qualidade com a família e para hobbies",
                "Ser reconhecido(a) como autoridade em {nicho}"
            ],
            "onde_online": [
                "LinkedIn (grupos de empreendedorismo e marketing)",
                "Instagram (perfis de mentores e influenciadores do nicho)",
                "YouTube (canais de conteúdo sobre {nicho} e negócios)",
                "Grupos de Facebook e Telegram focados em {nicho}"
            ]
        },
        "positioning": {
            "declaracao": f"Para empreendedores e profissionais ambiciosos que buscam resultados exponenciais em {nicho}, {produto} é a metodologia que transforma conhecimento em lucro, oferecendo um caminho claro e comprovado para a liberdade financeira e de tempo, diferente de tudo que você já viu.",
            "angulos": [
                {
                    "tipo": "Lógico - Focado em Resultados",
                    "mensagem": f"Descubra o método validado que já gerou X% de aumento no faturamento para nossos alunos em {nicho}. Chega de tentativa e erro, siga um plano que funciona."
                },
                {
                    "tipo": "Emocional - Focado na Realização", 
                    "mensagem": f"Imagine a sensação de ter seu negócio em {nicho} crescendo no automático, enquanto você desfruta de mais tempo com sua família e realiza seus sonhos. Isso é possível com {produto}."
                },
                {
                    "tipo": "Contraste - Focado na Inovação",
                    "mensagem": f"Enquanto a maioria oferece fórmulas genéricas, {produto} é a única solução em {nicho} que se adapta à sua realidade, com estratégias personalizadas e suporte contínuo para garantir seu sucesso."
                },
                {
                    "tipo": "Urgência/Escassez - Focado na Oportunidade",
                    "mensagem": f"As vagas para a próxima turma de {produto} são limitadas e fecham em breve. Não perca a chance de transformar seu futuro em {nicho} antes que seja tarde demais."
                }
            ],
            "proposta_valor_irrefutavel": f"Com {produto}, você não apenas aprende as melhores estratégias para {nicho}, mas também recebe acompanhamento personalizado e acesso a uma comunidade exclusiva, garantindo que você implemente cada passo e alcance resultados concretos em tempo recorde, ou seu investimento de volta."
        },
        "competition": {
            "concorrentes": [
                {
                    "nome": f"Concorrente A - {nicho} (Plataforma de Cursos Online)",
                    "produto_servico": "Cursos gravados sobre {nicho}",
                    "preco": int(preco_num * 0.7),
                    "forcas": "Grande volume de conteúdo, preço acessível, reconhecimento de marca.",
                    "fraquezas": "Conteúdo genérico, falta de suporte personalizado, baixa taxa de conclusão, não foca em aplicação prática.",
                    "oportunidade_diferenciacao": "Oferecer mentoria individualizada, comunidade ativa, foco em resultados práticos e estudos de caso de sucesso."
                },
                {
                    "nome": f"Concorrente B - {nicho} (Consultoria Individual)",
                    "produto_servico": "Sessões de consultoria 1-a-1",
                    "preco": int(preco_num * 2.5),
                    "forcas": "Atendimento personalizado, alta qualidade do consultor, resultados pontuais.",
                    "fraquezas": "Preço muito elevado, escalabilidade limitada, dependência total do consultor, não oferece comunidade.",
                    "oportunidade_diferenciacao": "Criar um programa híbrido com aulas gravadas e sessões em grupo, reduzindo o custo e aumentando o alcance, mantendo a qualidade."
                },
                {
                    "nome": f"Concorrente C - {nicho} (Agência de Marketing)",
                    "produto_servico": "Serviços de gestão de tráfego e conteúdo",
                    "preco": int(preco_num * 3.0),
                    "forcas": "Execução completa para o cliente, expertise técnica, resultados diretos.",
                    "fraquezas": "Alto custo mensal, cliente não aprende o processo, falta de controle sobre as estratégias, não foca em capacitação.",
                    "oportunidade_diferenciacao": "Capacitar o cliente para que ele mesmo possa gerenciar suas estratégias, oferecendo ferramentas e conhecimento, em vez de apenas executar o serviço."
                }
            ],
            "lacunas_mercado": [
                f"Falta de uma metodologia passo a passo e comprovada para {nicho} que seja acessível e escalável.",
                "Ausência de suporte contínuo e comunidade engajada para troca de experiências e resolução de dúvidas.",
                "Pouco foco na mentalidade e nas crenças limitantes que impedem o sucesso dos profissionais em {nicho}.",
                "Carência de ferramentas e templates prontos para aplicação imediata das estratégias."
            ],
            "benchmarking_melhores_praticas": [
                "Programas de mentoria em grupo com encontros semanais para acompanhamento e tira-dúvidas.",
                "Criação de uma comunidade exclusiva (Discord, Telegram) para networking e suporte.",
                "Oferecer bônus de ferramentas e templates editáveis para acelerar a implementação."
            ]
        },
        "marketing": {
            "landing_page_headlines": [
                f"Desvende os Segredos de {nicho}: A Metodologia Que Transforma Conhecimento em Lucro!",
                f"Chega de Frustração em {nicho}: Conquiste a Liberdade Financeira com Nosso Método Comprovado!",
                f"O Caminho Rápido para o Sucesso em {nicho}: Garanta Sua Vaga na Próxima Turma e Transforme Sua Realidade!"
            ],
            "pagina_vendas_estrutura": [
                {
                    "titulo": "A Dor Que Você Sente",
                    "resumo_conteudo": f"Comece com uma copy que ressoa com as frustrações e desafios do avatar em {nicho}, mostrando que você entende a dor dele."
                },
                {
                    "titulo": "A Solução Que Você Precisa",
                    "resumo_conteudo": f"Apresente {produto} como a solução definitiva para os problemas do avatar, destacando a metodologia única e os benefícios transformadores."
                },
                {
                    "titulo": "Prova Social Irrefutável",
                    "resumo_conteudo": "Depoimentos em vídeo e texto de alunos satisfeitos, com resultados comprovados e histórias de sucesso."
                },
                {
                    "titulo": "O Que Você Vai Receber",
                    "resumo_conteudo": "Detalhe todos os módulos, aulas, bônus e materiais de apoio, com foco nos benefícios e na transformação que cada um oferece."
                },
                {
                    "titulo": "A Oferta Irresistível",
                    "resumo_conteudo": f"Apresente o preço, as condições de pagamento e os bônus exclusivos por tempo limitado, criando um senso de urgência e valor."
                },
                {
                    "titulo": "Perguntas Frequentes (FAQ)",
                    "resumo_conteudo": "Responda às principais objeções e dúvidas, quebrando barreiras e facilitando a decisão de compra."
                },
                {
                    "titulo": "Chamada para Ação (CTA)",
                    "resumo_conteudo": "Botão claro e persuasivo para a compra, com frases como 'Quero Minha Vaga Agora!' ou 'Transforme Meu Negócio!'"
                }
            ],
            "emails_assuntos": [
                f"[Aquecimento] O Segredo que Ninguém Te Conta sobre {nicho}",
                f"[Lançamento] 🚀 {produto} - Sua Jornada para o Sucesso Começa Agora!",
                f"[Objeção] 'Não Tenho Tempo' é a Desculpa que Te Impede de Dominar {nicho}",
                f"[Escassez] Últimas Vagas para {produto} - Não Fique de Fora!",
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

