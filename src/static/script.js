// Global variables
let currentAnalysis = null;
let analysisInProgress = false;

// DOM Elements
const sections = {
    home: document.getElementById('home'),
    analyzer: document.getElementById('analyzer'),
    dashboard: document.getElementById('dashboard')
};

const navLinks = document.querySelectorAll('.neo-nav-link');
const analyzerForm = document.getElementById('analyzerForm');
const loadingState = document.getElementById('loadingState');
const resultsContainer = document.getElementById('resultsContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const loadingText = document.getElementById('loadingText');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeForm();
    initializeHeader();
});

// Navigation functionality
function initializeNavigation() {
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            showSection(targetId);
            updateActiveNav(this);
        });
    });
}

function showSection(sectionId) {
    // Hide all sections
    Object.values(sections).forEach(section => {
        if (section) section.style.display = 'none';
    });
    
    // Show target section
    if (sections[sectionId]) {
        sections[sectionId].style.display = 'block';
    }
}

function updateActiveNav(activeLink) {
    navLinks.forEach(link => link.classList.remove('active'));
    activeLink.classList.add('active');
}

function showAnalyzer() {
    showSection('analyzer');
    updateActiveNav(document.querySelector('a[href="#analyzer"]'));
}

// Header scroll effect
function initializeHeader() {
    const header = document.getElementById('header');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

// Form functionality
function initializeForm() {
    if (analyzerForm) {
        analyzerForm.addEventListener('submit', handleFormSubmit);
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (analysisInProgress) return;
    
    const formData = new FormData(analyzerForm);
    const data = Object.fromEntries(formData.entries());
    
    // Validate required fields
    if (!data.nicho.trim()) {
        showNotification('Por favor, informe o nicho de atuação.', 'error');
        return;
    }
    
    analysisInProgress = true;
    showDashboard();
    showLoading();
    
    try {
        await performAnalysis(data);
    } catch (error) {
        console.error('Erro na análise:', error);
        showNotification('Erro ao realizar análise. Tente novamente.', 'error');
        analysisInProgress = false;
    }
}

function showDashboard() {
    showSection('dashboard');
    updateActiveNav(document.querySelector('a[href="#dashboard"]'));
}

function showLoading() {
    loadingState.style.display = 'block';
    resultsContainer.style.display = 'none';
    
    // Simulate progress
    simulateProgress();
}

function simulateProgress() {
    const steps = [
        { progress: 10, text: 'Analisando nicho de mercado...' },
        { progress: 25, text: 'Pesquisando concorrência...' },
        { progress: 40, text: 'Identificando avatar ideal...' },
        { progress: 60, text: 'Gerando estratégias de posicionamento...' },
        { progress: 80, text: 'Criando materiais de marketing...' },
        { progress: 95, text: 'Finalizando análise...' },
        { progress: 100, text: 'Análise concluída!' }
    ];
    
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep < steps.length) {
            const step = steps[currentStep];
            updateProgress(step.progress, step.text);
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 1500);
}

function updateProgress(percentage, text) {
    progressBar.style.width = percentage + '%';
    progressText.textContent = percentage + '%';
    loadingText.textContent = text;
}

async function performAnalysis(data) {
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        currentAnalysis = result;
        
        // Wait for progress simulation to complete
        setTimeout(() => {
            hideLoading();
            displayResults(result);
            analysisInProgress = false;
        }, 12000); // 12 seconds total for progress simulation
        
    } catch (error) {
        console.error('Erro na análise:', error);
        hideLoading();
        showNotification('Erro ao realizar análise. Verifique sua conexão e tente novamente.', 'error');
        analysisInProgress = false;
    }
}

function hideLoading() {
    loadingState.style.display = 'none';
    resultsContainer.style.display = 'block';
}

function displayResults(analysis) {
    resultsContainer.innerHTML = generateResultsHTML(analysis);
    
    // Initialize interactive elements
    initializeResultsInteractions();
}

function generateResultsHTML(analysis) {
    return `
        <div class="results-header">
            <div class="neo-enhanced-card">
                <div class="neo-card-header">
                    <div class="neo-card-icon">
                        <i class="fas fa-trophy"></i>
                    </div>
                    <h3 class="neo-card-title">Análise Concluída com Sucesso</h3>
                </div>
                <div class="neo-card-content">
                    <p>Sua análise de mercado foi processada pela IA Gemini. Explore os resultados abaixo para descobrir insights valiosos sobre seu nicho.</p>
                    <div class="results-actions">
                        <button class="neo-cta-button" onclick="downloadReport()">
                            <i class="fas fa-download"></i>
                            <span>Baixar Relatório</span>
                        </button>
                        <button class="neo-cta-button" onclick="shareResults()" style="background: var(--neo-bg); color: var(--text-primary); box-shadow: var(--neo-shadow-1);">
                            <i class="fas fa-share"></i>
                            <span>Compartilhar</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="results-grid">
            ${generateAvatarSection(analysis.avatar)}
            ${generatePositioningSection(analysis.positioning)}
            ${generateMarketingSection(analysis.marketing)}
            ${generateMetricsSection(analysis.metrics)}
            ${generateCompetitionSection(analysis.competition)}
            ${generateFunnelSection(analysis.funnel)}
        </div>
    `;
}

function generateAvatarSection(avatar) {
    return `
        <div class="neo-enhanced-card result-card">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-user-circle"></i>
                </div>
                <h3 class="neo-card-title">Perfil do Avatar</h3>
            </div>
            <div class="neo-card-content">
                <div class="avatar-profile">
                    <div class="avatar-basic-info">
                        <h4>${avatar.nome}</h4>
                        <p class="avatar-context">${avatar.contexto}</p>
                    </div>
                    
                    <div class="avatar-details">
                        <div class="detail-item">
                            <strong>Barreira Crítica:</strong>
                            <p>${avatar.barreira_critica}</p>
                        </div>
                        
                        <div class="detail-item">
                            <strong>Estado Desejado:</strong>
                            <p>${avatar.estado_desejado}</p>
                        </div>
                        
                        <div class="detail-item">
                            <strong>Principais Frustrações:</strong>
                            <ul>
                                ${avatar.frustracoes.map(f => `<li>${f}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div class="detail-item">
                            <strong>Crença Limitante:</strong>
                            <p>${avatar.crenca_limitante}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generatePositioningSection(positioning) {
    return `
        <div class="neo-enhanced-card result-card">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-bullseye"></i>
                </div>
                <h3 class="neo-card-title">Estratégia de Posicionamento</h3>
            </div>
            <div class="neo-card-content">
                <div class="positioning-content">
                    <div class="positioning-statement">
                        <h4>Declaração de Posicionamento</h4>
                        <blockquote>${positioning.declaracao}</blockquote>
                    </div>
                    
                    <div class="messaging-angles">
                        <h4>Ângulos de Mensagem</h4>
                        ${positioning.angulos.map((angulo, index) => `
                            <div class="angle-item">
                                <h5>Ângulo ${index + 1}: ${angulo.tipo}</h5>
                                <p>${angulo.mensagem}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateMarketingSection(marketing) {
    return `
        <div class="neo-enhanced-card result-card">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-megaphone"></i>
                </div>
                <h3 class="neo-card-title">Materiais de Marketing</h3>
            </div>
            <div class="neo-card-content">
                <div class="marketing-materials">
                    <div class="material-tabs">
                        <button class="tab-btn active" onclick="showMaterialTab('landing')">Landing Page</button>
                        <button class="tab-btn" onclick="showMaterialTab('emails')">E-mails</button>
                        <button class="tab-btn" onclick="showMaterialTab('ads')">Anúncios</button>
                    </div>
                    
                    <div class="material-content">
                        <div id="landing-content" class="tab-content active">
                            <h4>Página de Vendas</h4>
                            <div class="material-preview">
                                <p>${marketing.landing_page.headline}</p>
                                <div class="preview-sections">
                                    ${marketing.landing_page.secoes.map(secao => `
                                        <div class="section-preview">
                                            <h5>${secao.titulo}</h5>
                                            <p>${secao.conteudo.substring(0, 150)}...</p>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                        
                        <div id="emails-content" class="tab-content">
                            <h4>Sequência de E-mails</h4>
                            ${marketing.emails.map((email, index) => `
                                <div class="email-preview">
                                    <h5>E-mail ${index + 1}: ${email.tipo}</h5>
                                    <p><strong>Assunto:</strong> ${email.assunto}</p>
                                    <p>${email.preview}</p>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div id="ads-content" class="tab-content">
                            <h4>Roteiros de Anúncios</h4>
                            ${marketing.anuncios.map((ad, index) => `
                                <div class="ad-preview">
                                    <h5>Anúncio ${index + 1}: ${ad.angulo}</h5>
                                    <p>${ad.roteiro}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateMetricsSection(metrics) {
    return `
        <div class="neo-enhanced-card result-card">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <h3 class="neo-card-title">Projeções e Métricas</h3>
            </div>
            <div class="neo-card-content">
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">${metrics.leads_projetados}</div>
                        <div class="metric-label">Leads Projetados</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-value">${metrics.conversao}%</div>
                        <div class="metric-label">Taxa de Conversão</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-value">R$ ${metrics.faturamento.toLocaleString()}</div>
                        <div class="metric-label">Faturamento Projetado</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-value">${metrics.roi}%</div>
                        <div class="metric-label">ROI Esperado</div>
                    </div>
                </div>
                
                <div class="investment-breakdown">
                    <h4>Distribuição do Investimento</h4>
                    <div class="investment-items">
                        ${metrics.investimento.map(item => `
                            <div class="investment-item">
                                <span class="channel">${item.canal}</span>
                                <span class="percentage">${item.percentual}%</span>
                                <span class="amount">R$ ${item.valor.toLocaleString()}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateCompetitionSection(competition) {
    return `
        <div class="neo-enhanced-card result-card">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-chess"></i>
                </div>
                <h3 class="neo-card-title">Análise Competitiva</h3>
            </div>
            <div class="neo-card-content">
                <div class="competition-analysis">
                    ${competition.concorrentes.map(concorrente => `
                        <div class="competitor-item">
                            <h4>${concorrente.nome}</h4>
                            <div class="competitor-details">
                                <p><strong>Preço:</strong> R$ ${concorrente.preco}</p>
                                <p><strong>Forças:</strong> ${concorrente.forcas}</p>
                                <p><strong>Fraquezas:</strong> ${concorrente.fraquezas}</p>
                                <p><strong>Oportunidade:</strong> ${concorrente.oportunidade}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="market-gaps">
                    <h4>Lacunas do Mercado</h4>
                    <ul>
                        ${competition.lacunas.map(lacuna => `<li>${lacuna}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function generateFunnelSection(funnel) {
    return `
        <div class="neo-enhanced-card result-card full-width">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-funnel-dollar"></i>
                </div>
                <h3 class="neo-card-title">Funil de Vendas</h3>
            </div>
            <div class="neo-card-content">
                <div class="funnel-timeline">
                    ${funnel.fases.map((fase, index) => `
                        <div class="funnel-phase">
                            <div class="phase-number">${index + 1}</div>
                            <div class="phase-content">
                                <h4>${fase.nome}</h4>
                                <p><strong>Duração:</strong> ${fase.duracao}</p>
                                <p><strong>Objetivo:</strong> ${fase.objetivo}</p>
                                <div class="phase-actions">
                                    <h5>Principais Ações:</h5>
                                    <ul>
                                        ${fase.acoes.map(acao => `<li>${acao}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="funnel-metrics">
                    <h4>Cronograma de Execução</h4>
                    <div class="timeline">
                        ${funnel.cronograma.map(item => `
                            <div class="timeline-item">
                                <div class="timeline-date">${item.periodo}</div>
                                <div class="timeline-content">
                                    <h5>${item.atividade}</h5>
                                    <p>${item.descricao}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function initializeResultsInteractions() {
    // Initialize tab functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.getAttribute('onclick').match(/'([^']+)'/)[1];
            showMaterialTab(target);
        });
    });
}

function showMaterialTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Show target content and activate button
    const targetContent = document.getElementById(`${tabName}-content`);
    if (targetContent) {
        targetContent.classList.add('active');
    }
    
    const targetButton = document.querySelector(`[onclick*="${tabName}"]`);
    if (targetButton) {
        targetButton.classList.add('active');
    }
}

function downloadReport() {
    if (!currentAnalysis) {
        showNotification('Nenhuma análise disponível para download.', 'error');
        return;
    }
    
    // Create and download report
    const reportData = generateReportData(currentAnalysis);
    const blob = new Blob([reportData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `analise-avatar-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Relatório baixado com sucesso!', 'success');
}

function generateReportData(analysis) {
    return `
RELATÓRIO DE ANÁLISE DE AVATAR
===============================

PERFIL DO AVATAR
----------------
Nome: ${analysis.avatar.nome}
Contexto: ${analysis.avatar.contexto}

Barreira Crítica: ${analysis.avatar.barreira_critica}
Estado Desejado: ${analysis.avatar.estado_desejado}
Crença Limitante: ${analysis.avatar.crenca_limitante}

ESTRATÉGIA DE POSICIONAMENTO
----------------------------
${analysis.positioning.declaracao}

PROJEÇÕES FINANCEIRAS
---------------------
Leads Projetados: ${analysis.metrics.leads_projetados}
Taxa de Conversão: ${analysis.metrics.conversao}%
Faturamento Projetado: R$ ${analysis.metrics.faturamento.toLocaleString()}
ROI Esperado: ${analysis.metrics.roi}%

Gerado em: ${new Date().toLocaleString()}
    `;
}

function shareResults() {
    if (navigator.share) {
        navigator.share({
            title: 'Análise de Avatar - UP Lançamentos',
            text: 'Confira minha análise de mercado completa!',
            url: window.location.href
        });
    } else {
        // Fallback for browsers that don't support Web Share API
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            showNotification('Link copiado para a área de transferência!', 'success');
        });
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: var(--neo-border-radius);
        color: var(--text-light);
        font-weight: 600;
        z-index: 10000;
        box-shadow: var(--neo-shadow-2);
        transition: var(--neo-transition);
        transform: translateX(100%);
    `;
    
    // Set background color based on type
    switch (type) {
        case 'success':
            notification.style.background = 'linear-gradient(135deg, #10b981, #059669)';
            break;
        case 'error':
            notification.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
            break;
        default:
            notification.style.background = 'var(--brand-gradient)';
    }
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Additional CSS for results
const additionalCSS = `
.results-header {
    margin-bottom: 2rem;
}

.results-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
}

.result-card.full-width {
    grid-column: 1 / -1;
}

.avatar-profile {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.avatar-basic-info h4 {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--brand-primary);
    margin-bottom: 0.5rem;
}

.avatar-context {
    color: var(--text-secondary);
    font-style: italic;
    margin-bottom: 1rem;
}

.detail-item {
    margin-bottom: 1rem;
    padding: 1rem;
    background: var(--neo-bg-dark);
    border-radius: var(--neo-border-radius-small);
}

.detail-item strong {
    color: var(--brand-primary);
    display: block;
    margin-bottom: 0.5rem;
}

.detail-item ul {
    margin-left: 1rem;
    color: var(--text-secondary);
}

.positioning-statement blockquote {
    background: var(--neo-bg-dark);
    padding: 1.5rem;
    border-radius: var(--neo-border-radius-small);
    border-left: 4px solid var(--brand-primary);
    font-style: italic;
    margin: 1rem 0;
}

.angle-item {
    margin-bottom: 1rem;
    padding: 1rem;
    background: var(--neo-bg-dark);
    border-radius: var(--neo-border-radius-small);
}

.angle-item h5 {
    color: var(--brand-primary);
    margin-bottom: 0.5rem;
}

.material-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    background: var(--neo-bg-dark);
    padding: 0.5rem;
    border-radius: var(--neo-border-radius);
}

.tab-btn {
    flex: 1;
    padding: 0.8rem 1rem;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    border-radius: var(--neo-border-radius-small);
    cursor: pointer;
    transition: var(--neo-transition);
    font-weight: 600;
}

.tab-btn.active,
.tab-btn:hover {
    background: var(--brand-gradient);
    color: var(--text-light);
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.metric-item {
    text-align: center;
    padding: 1.5rem;
    background: var(--neo-bg-dark);
    border-radius: var(--neo-border-radius-small);
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--brand-primary);
    margin-bottom: 0.5rem;
}

.metric-label {
    font-size: 0.9rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.investment-breakdown {
    background: var(--neo-bg-dark);
    padding: 1.5rem;
    border-radius: var(--neo-border-radius-small);
}

.investment-item {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 1rem;
    padding: 0.8rem 0;
    border-bottom: 1px solid var(--neo-bg);
}

.investment-item:last-child {
    border-bottom: none;
}

.competitor-item {
    margin-bottom: 1.5rem;
    padding: 1.5rem;
    background: var(--neo-bg-dark);
    border-radius: var(--neo-border-radius-small);
}

.competitor-item h4 {
    color: var(--brand-primary);
    margin-bottom: 1rem;
}

.funnel-timeline {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.funnel-phase {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
}

.phase-number {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--brand-gradient);
    color: var(--text-light);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    flex-shrink: 0;
}

.phase-content {
    flex: 1;
    background: var(--neo-bg-dark);
    padding: 1.5rem;
    border-radius: var(--neo-border-radius-small);
}

.timeline {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.timeline-item {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
}

.timeline-date {
    background: var(--brand-gradient);
    color: var(--text-light);
    padding: 0.5rem 1rem;
    border-radius: var(--neo-border-radius-small);
    font-weight: 600;
    white-space: nowrap;
}

.timeline-content {
    flex: 1;
}

@media (max-width: 768px) {
    .results-grid {
        grid-template-columns: 1fr;
    }
    
    .results-actions {
        flex-direction: column;
    }
    
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .investment-item {
        grid-template-columns: 1fr;
        text-align: center;
    }
    
    .timeline-item {
        flex-direction: column;
    }
}
`;

// Inject additional CSS
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);


// Chart.js integration for interactive charts
function loadChartJS() {
    if (typeof Chart === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = function() {
            console.log('Chart.js loaded successfully');
        };
        document.head.appendChild(script);
    }
}

// Load Chart.js when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadChartJS();
});

// Enhanced results display with interactive charts
function displayResultsWithCharts(analysis) {
    resultsContainer.innerHTML = generateEnhancedResultsHTML(analysis);
    
    // Initialize interactive elements
    initializeResultsInteractions();
    
    // Create charts after a short delay to ensure DOM is ready
    setTimeout(() => {
        createMetricsCharts(analysis.metrics);
        createFunnelChart(analysis.funnel);
        createCompetitionChart(analysis.competition);
    }, 500);
}

function generateEnhancedResultsHTML(analysis) {
    return `
        <div class="results-header">
            <div class="neo-enhanced-card">
                <div class="neo-card-header">
                    <div class="neo-card-icon">
                        <i class="fas fa-trophy"></i>
                    </div>
                    <h3 class="neo-card-title">Análise Concluída com Sucesso</h3>
                </div>
                <div class="neo-card-content">
                    <p>Sua análise de mercado foi processada pela IA Gemini. Explore os resultados abaixo para descobrir insights valiosos sobre seu nicho.</p>
                    <div class="results-actions">
                        <button class="neo-cta-button" onclick="downloadReport()">
                            <i class="fas fa-download"></i>
                            <span>Baixar Relatório</span>
                        </button>
                        <button class="neo-cta-button" onclick="shareResults()" style="background: var(--neo-bg); color: var(--text-primary); box-shadow: var(--neo-shadow-1);">
                            <i class="fas fa-share"></i>
                            <span>Compartilhar</span>
                        </button>
                        <button class="neo-cta-button" onclick="exportToPDF()" style="background: var(--neo-bg); color: var(--text-primary); box-shadow: var(--neo-shadow-1);">
                            <i class="fas fa-file-pdf"></i>
                            <span>Exportar PDF</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="results-grid">
            ${generateAvatarSection(analysis.avatar)}
            ${generatePositioningSection(analysis.positioning)}
            ${generateMetricsChartSection(analysis.metrics)}
            ${generateMarketingSection(analysis.marketing)}
            ${generateCompetitionChartSection(analysis.competition)}
            ${generateFunnelChartSection(analysis.funnel)}
        </div>
    `;
}

function generateMetricsChartSection(metrics) {
    return `
        <div class="neo-enhanced-card result-card">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <h3 class="neo-card-title">Projeções e Métricas</h3>
            </div>
            <div class="neo-card-content">
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">${metrics.leads_projetados}</div>
                        <div class="metric-label">Leads Projetados</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-value">${metrics.conversao}%</div>
                        <div class="metric-label">Taxa de Conversão</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-value">R$ ${metrics.faturamento.toLocaleString()}</div>
                        <div class="metric-label">Faturamento Projetado</div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-value">${metrics.roi}%</div>
                        <div class="metric-label">ROI Esperado</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="investmentChart" width="400" height="200"></canvas>
                </div>
                
                <div class="investment-breakdown">
                    <h4>Distribuição do Investimento</h4>
                    <div class="investment-items">
                        ${metrics.investimento.map(item => `
                            <div class="investment-item">
                                <span class="channel">${item.canal}</span>
                                <span class="percentage">${item.percentual}%</span>
                                <span class="amount">R$ ${item.valor.toLocaleString()}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateCompetitionChartSection(competition) {
    return `
        <div class="neo-enhanced-card result-card">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-chess"></i>
                </div>
                <h3 class="neo-card-title">Análise Competitiva</h3>
            </div>
            <div class="neo-card-content">
                <div class="chart-container">
                    <canvas id="competitionChart" width="400" height="200"></canvas>
                </div>
                
                <div class="competition-analysis">
                    ${competition.concorrentes.map(concorrente => `
                        <div class="competitor-item">
                            <h4>${concorrente.nome}</h4>
                            <div class="competitor-details">
                                <p><strong>Preço:</strong> R$ ${concorrente.preco}</p>
                                <p><strong>Forças:</strong> ${concorrente.forcas}</p>
                                <p><strong>Fraquezas:</strong> ${concorrente.fraquezas}</p>
                                <p><strong>Oportunidade:</strong> ${concorrente.oportunidade}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="market-gaps">
                    <h4>Lacunas do Mercado</h4>
                    <ul>
                        ${competition.lacunas.map(lacuna => `<li>${lacuna}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function generateFunnelChartSection(funnel) {
    return `
        <div class="neo-enhanced-card result-card full-width">
            <div class="neo-card-header">
                <div class="neo-card-icon">
                    <i class="fas fa-funnel-dollar"></i>
                </div>
                <h3 class="neo-card-title">Funil de Vendas</h3>
            </div>
            <div class="neo-card-content">
                <div class="chart-container">
                    <canvas id="funnelChart" width="800" height="300"></canvas>
                </div>
                
                <div class="funnel-timeline">
                    ${funnel.fases.map((fase, index) => `
                        <div class="funnel-phase">
                            <div class="phase-number">${index + 1}</div>
                            <div class="phase-content">
                                <h4>${fase.nome}</h4>
                                <p><strong>Duração:</strong> ${fase.duracao}</p>
                                <p><strong>Objetivo:</strong> ${fase.objetivo}</p>
                                <div class="phase-actions">
                                    <h5>Principais Ações:</h5>
                                    <ul>
                                        ${fase.acoes.map(acao => `<li>${acao}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="funnel-metrics">
                    <h4>Cronograma de Execução</h4>
                    <div class="timeline">
                        ${funnel.cronograma.map(item => `
                            <div class="timeline-item">
                                <div class="timeline-date">${item.periodo}</div>
                                <div class="timeline-content">
                                    <h5>${item.atividade}</h5>
                                    <p>${item.descricao}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function createMetricsCharts(metrics) {
    if (typeof Chart === 'undefined') {
        setTimeout(() => createMetricsCharts(metrics), 1000);
        return;
    }

    // Investment Distribution Chart
    const investmentCtx = document.getElementById('investmentChart');
    if (investmentCtx) {
        new Chart(investmentCtx, {
            type: 'doughnut',
            data: {
                labels: metrics.investimento.map(item => item.canal),
                datasets: [{
                    data: metrics.investimento.map(item => item.valor),
                    backgroundColor: [
                        '#ff6b35',
                        '#f7931e',
                        '#ff4757',
                        '#3742fa',
                        '#2ed573'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f8fafc',
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f8fafc',
                        bodyColor: '#e2e8f0',
                        borderColor: '#ff6b35',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const percentage = metrics.investimento[context.dataIndex].percentual;
                                return `${context.label}: R$ ${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
}

function createCompetitionChart(competition) {
    if (typeof Chart === 'undefined') {
        setTimeout(() => createCompetitionChart(competition), 1000);
        return;
    }

    const competitionCtx = document.getElementById('competitionChart');
    if (competitionCtx) {
        new Chart(competitionCtx, {
            type: 'bar',
            data: {
                labels: competition.concorrentes.map(c => c.nome),
                datasets: [{
                    label: 'Preço (R$)',
                    data: competition.concorrentes.map(c => c.preco),
                    backgroundColor: '#ff6b35',
                    borderColor: '#f7931e',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8fafc'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f8fafc',
                        bodyColor: '#e2e8f0',
                        borderColor: '#ff6b35',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#e2e8f0',
                            callback: function(value) {
                                return 'R$ ' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: '#334155'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#e2e8f0'
                        },
                        grid: {
                            color: '#334155'
                        }
                    }
                }
            }
        });
    }
}

function createFunnelChart(funnel) {
    if (typeof Chart === 'undefined') {
        setTimeout(() => createFunnelChart(funnel), 1000);
        return;
    }

    const funnelCtx = document.getElementById('funnelChart');
    if (funnelCtx) {
        // Simulate funnel data
        const funnelData = [2500, 1500, 600, 150, 38]; // Example conversion funnel
        
        new Chart(funnelCtx, {
            type: 'bar',
            data: {
                labels: funnel.fases.map(fase => fase.nome),
                datasets: [{
                    label: 'Volume',
                    data: funnelData,
                    backgroundColor: [
                        '#ff6b35',
                        '#f7931e',
                        '#ff4757',
                        '#3742fa',
                        '#2ed573'
                    ],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f8fafc',
                        bodyColor: '#e2e8f0',
                        borderColor: '#ff6b35',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#e2e8f0'
                        },
                        grid: {
                            color: '#334155'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#e2e8f0'
                        },
                        grid: {
                            color: '#334155'
                        }
                    }
                }
            }
        });
    }
}

function exportToPDF() {
    if (!currentAnalysis) {
        showNotification('Nenhuma análise disponível para exportar.', 'error');
        return;
    }
    
    // Create a simplified version for PDF export
    const printWindow = window.open('', '_blank');
    const printContent = generatePrintableReport(currentAnalysis);
    
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório de Análise - ${currentAnalysis.avatar.nome}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
                h1, h2, h3 { color: #ff6b35; }
                .section { margin-bottom: 30px; page-break-inside: avoid; }
                .metric { display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
                .competitor { margin: 15px 0; padding: 15px; background: #f9f9f9; border-radius: 8px; }
                @media print { .no-print { display: none; } }
            </style>
        </head>
        <body>
            ${printContent}
        </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.focus();
    
    setTimeout(() => {
        printWindow.print();
    }, 500);
    
    showNotification('Relatório preparado para impressão/PDF!', 'success');
}

function generatePrintableReport(analysis) {
    return `
        <h1>Relatório de Análise de Avatar</h1>
        <p><strong>Data:</strong> ${new Date().toLocaleDateString()}</p>
        
        <div class="section">
            <h2>Perfil do Avatar</h2>
            <h3>${analysis.avatar.nome}</h3>
            <p><strong>Contexto:</strong> ${analysis.avatar.contexto}</p>
            <p><strong>Barreira Crítica:</strong> ${analysis.avatar.barreira_critica}</p>
            <p><strong>Estado Desejado:</strong> ${analysis.avatar.estado_desejado}</p>
            <p><strong>Crença Limitante:</strong> ${analysis.avatar.crenca_limitante}</p>
        </div>
        
        <div class="section">
            <h2>Estratégia de Posicionamento</h2>
            <p>${analysis.positioning.declaracao}</p>
        </div>
        
        <div class="section">
            <h2>Métricas Projetadas</h2>
            <div class="metric">
                <strong>Leads:</strong> ${analysis.metrics.leads_projetados}
            </div>
            <div class="metric">
                <strong>Conversão:</strong> ${analysis.metrics.conversao}%
            </div>
            <div class="metric">
                <strong>Faturamento:</strong> R$ ${analysis.metrics.faturamento.toLocaleString()}
            </div>
            <div class="metric">
                <strong>ROI:</strong> ${analysis.metrics.roi}%
            </div>
        </div>
        
        <div class="section">
            <h2>Análise Competitiva</h2>
            ${analysis.competition.concorrentes.map(c => `
                <div class="competitor">
                    <h4>${c.nome}</h4>
                    <p><strong>Preço:</strong> R$ ${c.preco}</p>
                    <p><strong>Forças:</strong> ${c.forcas}</p>
                    <p><strong>Fraquezas:</strong> ${c.fraquezas}</p>
                </div>
            `).join('')}
        </div>
    `;
}

// Update the main performAnalysis function to use the enhanced display
async function performAnalysis(data) {
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        currentAnalysis = result;
        
        // Wait for progress simulation to complete
        setTimeout(() => {
            hideLoading();
            displayResultsWithCharts(result); // Use enhanced display with charts
            analysisInProgress = false;
        }, 12000);
        
    } catch (error) {
        console.error('Erro na análise:', error);
        hideLoading();
        showNotification('Erro ao realizar análise. Verifique sua conexão e tente novamente.', 'error');
        analysisInProgress = false;
    }
}

// Add search functionality
function initializeSearch() {
    const searchInput = document.querySelector('.neo-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            if (query.length > 2) {
                searchNichos(query);
            }
        });
    }
}

async function searchNichos(query) {
    try {
        const response = await fetch(`/api/nichos?search=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        // Display search suggestions
        displaySearchSuggestions(data.nichos);
        
    } catch (error) {
        console.error('Erro na busca:', error);
    }
}

function displaySearchSuggestions(nichos) {
    // Implementation for search suggestions dropdown
    console.log('Nichos encontrados:', nichos);
}

// Initialize search when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
});

