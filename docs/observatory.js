/* ═══════════════════════════════════════════════════
   Pipeline Observatory — Interactive Logic
   Antigravity OS v1.4.0
   ═══════════════════════════════════════════════════ */

// ── Tab Navigation ──────────────────────────────────
document.querySelectorAll('.nav-pill').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-pill').forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        document.querySelectorAll('.tab-content').forEach(p => p.classList.remove('visible'));
        document.getElementById('panel-' + btn.dataset.tab).classList.add('visible');
    });
});

// ── LoRA Tenant Selector ────────────────────────────
document.querySelectorAll('.lora-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.lora-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const tenant = chip.dataset.tenant;
        updateTenantMetrics(tenant);
        log('telemetry', `LoRA adapter switched: ${tenant.toUpperCase()}`, 'hi');
    });
});

const tenantData = {
    il: { latency: '142ms', tps: '847', cost: '$0.003', experts: '4/64' },
    pl: { latency: '168ms', tps: '792', cost: '$0.004', experts: '6/64' },
    cz: { latency: '175ms', tps: '761', cost: '$0.004', experts: '5/64' },
    us: { latency: '128ms', tps: '912', cost: '$0.003', experts: '4/64' },
    de: { latency: '155ms', tps: '831', cost: '$0.003', experts: '5/64' },
};

function updateTenantMetrics(tenant) {
    const d = tenantData[tenant] || tenantData.il;
    document.getElementById('m-latency').textContent = d.latency;
    document.getElementById('m-tps').textContent = d.tps;
    document.getElementById('m-cost').textContent = d.cost;
    document.getElementById('m-expert').textContent = d.experts;
}

// ── DAG Node Detail Views ───────────────────────────
const nodeDetails = {
    market: {
        title: 'Market Intelligence',
        desc: 'Deterministic data gathering across search engines, competitor sites, and market databases.',
        subagents: [
            { name: 'SERP Analyzer', type: 'deterministic', tools: 'Google Search API, SerpAPI' },
            { name: 'Competitor Scanner', type: 'deterministic', tools: 'Web scraper, diff engine' },
            { name: 'Trend Detector', type: 'probabilistic', tools: 'Gemma 4 MoE, time-series' },
        ]
    },
    keyword: {
        title: 'Keyword Strategy',
        desc: 'Probabilistic keyword clustering and intent classification using tenant-specific LoRA adapters.',
        subagents: [
            { name: 'Intent Classifier', type: 'probabilistic', tools: 'Gemma 4 + LoRA adapter' },
            { name: 'Cluster Engine', type: 'deterministic', tools: 'TF-IDF, embedding similarity' },
        ]
    },
    content: {
        title: 'Content Engine',
        desc: 'Hybrid generation pipeline — deterministic structure, probabilistic creative writing, per-tenant voice adaptation.',
        subagents: [
            { name: 'Outline Generator', type: 'deterministic', tools: 'Template engine, schema' },
            { name: 'Draft Writer', type: 'probabilistic', tools: 'Gemma 4 MoE + LoRA' },
            { name: 'Style Adapter', type: 'probabilistic', tools: 'Tenant LoRA, tone scoring' },
            { name: 'Media Planner', type: 'deterministic', tools: 'Asset registry, placement' },
        ]
    },
    seo: {
        title: 'Technical SEO',
        desc: 'Deterministic validation of structured data, meta tags, internal linking, and performance budgets.',
        subagents: [
            { name: 'Schema Validator', type: 'deterministic', tools: 'JSON-LD parser, schema.org' },
            { name: 'Link Optimizer', type: 'deterministic', tools: 'Graph analysis, PageRank sim' },
        ]
    },
    eval: {
        title: 'QA & Evaluation',
        desc: 'Multi-dimensional quality scoring via LLM-as-Judge. Three judge models score independently, then pairwise ranking produces final grades.',
        subagents: [
            { name: 'Gemini Judge', type: 'probabilistic', tools: 'Gemini 2.5 Pro, rubric eval' },
            { name: 'Claude Judge', type: 'probabilistic', tools: 'Claude Sonnet 4, rubric eval' },
            { name: 'GPT-4 Judge', type: 'probabilistic', tools: 'GPT-4.1, rubric eval' },
        ]
    },
    deploy: {
        title: 'Deploy & Publish',
        desc: 'Deterministic deployment to target CMS platforms with rollback capability and performance verification.',
        subagents: [
            { name: 'Publisher', type: 'deterministic', tools: 'WordPress API, staging env' },
        ]
    },
    govern: {
        title: 'Governance Kernel',
        desc: 'Antigravity OS — cost enforcement, solvency gating, state machine integrity, and DreamEngine self-improvement. Zero LLM dependencies.',
        subagents: [
            { name: 'Cost Guard', type: 'deterministic', tools: 'Budget tracking, tier rates' },
            { name: 'Rules Engine', type: 'deterministic', tools: 'Policy-as-code, YAML rules' },
            { name: 'Flight Recorder', type: 'deterministic', tools: 'SQLite WAL, state log' },
            { name: 'DreamEngine', type: 'heuristic', tools: 'Friction scan, patch synth' },
        ]
    }
};

document.querySelectorAll('.dag-node[data-node]').forEach(node => {
    node.addEventListener('click', () => {
        const key = node.dataset.node;
        const info = nodeDetails[key];
        if (!info) return;

        document.querySelectorAll('.dag-node[data-node]').forEach(n => n.classList.remove('active'));
        node.classList.add('active');

        document.getElementById('detail-title').textContent = info.title;
        document.getElementById('detail-desc').textContent = info.desc;

        const list = document.getElementById('subagent-list');
        list.innerHTML = info.subagents.map(s => {
            const color = s.type === 'deterministic' ? 'ok' : s.type === 'probabilistic' ? 'hi' : 'warn';
            return `<div class="tel-row">
                <span class="tel-msg ${color}">${s.name}</span>
                <span class="tel-ts">${s.type}</span>
            </div>
            <div class="tel-row">
                <span class="tel-ts" style="padding-left:12px">↳ ${s.tools}</span>
            </div>`;
        }).join('');
    });
});

// ── Logging ─────────────────────────────────────────
function log(feedId, msg, type = '') {
    const feed = document.getElementById(feedId);
    if (!feed) return;
    const ts = new Date().toISOString().substring(11, 23);
    const div = document.createElement('div');
    div.className = 'tel-row';
    div.innerHTML = `<span class="tel-ts">${ts}</span><span class="tel-msg ${type}">${msg}</span>`;
    feed.appendChild(div);
    feed.scrollTop = feed.scrollHeight;
}

// ── Simulation ──────────────────────────────────────
const sleep = ms => new Promise(r => setTimeout(r, ms));
let simRunning = false;

function setSimNode(id, state) {
    const el = document.getElementById('sn-' + id);
    if (el) el.className = 'dag-node' + (state ? ' ' + state : '');
}

async function runSimulation() {
    if (simRunning) return;
    simRunning = true;
    const btn = document.getElementById('btn-run');
    btn.disabled = true;

    // Reset
    ['idle','plan','act','eval','fail','halt','dream'].forEach(n => setSimNode(n, ''));
    document.getElementById('sim-telemetry').innerHTML = '';
    document.getElementById('dream-report').style.display = 'none';
    document.getElementById('sim-memory').style.display = 'none';

    const L = (m, t) => log('sim-telemetry', m, t);
    let spend = 0;

    L('Pipeline execution initiated.', 'hi');
    await sleep(400);

    // 3 failure cycles
    for (let i = 1; i <= 3; i++) {
        L(`[Cycle ${i}] Operation dispatched.`, 'hi');
        setSimNode('idle', 'processing');
        await sleep(300);
        setSimNode('idle', '');

        setSimNode('plan', 'processing');
        L(`[Cycle ${i}] Planning — loading context window.`, '');
        await sleep(400);
        setSimNode('plan', '');

        setSimNode('act', 'processing');
        spend += 0.012;
        L(`[Cycle ${i}] Executing — ${(spend).toFixed(3)} spent.`, '');
        document.getElementById('sol-val').textContent = `$${spend.toFixed(2)} / $100.00`;
        document.getElementById('sol-bar').style.width = `${spend}%`;
        await sleep(500);
        setSimNode('act', '');

        setSimNode('eval', 'processing');
        L(`[Cycle ${i}] Evaluating output variance.`, '');
        await sleep(400);

        L(`[Cycle ${i}] Evaluation FAILED: context threshold exceeded.`, 'err');
        setSimNode('eval', 'error');
        await sleep(300);
        setSimNode('eval', '');

        setSimNode('fail', 'error');
        L(`[Cycle ${i}] Rolled back. Re-entering planning.`, 'warn');
        await sleep(400);
        setSimNode('fail', '');
    }

    // Terminal block
    L('[Cycle 4] Loop breaker triggered.', 'warn');
    setSimNode('plan', 'processing');
    await sleep(300);
    setSimNode('plan', '');
    setSimNode('act', 'error');
    L('[Cycle 4] Agent halted.', 'err');
    await sleep(300);
    setSimNode('act', '');
    setSimNode('halt', 'error');
    L('[Cycle 4] Terminal state reached.', 'err');
    await sleep(800);

    // Dream sequence
    L('--- INITIATING SELF-IMPROVEMENT LOOP ---', 'warn');
    setSimNode('halt', '');
    setSimNode('dream', 'dreaming');
    L('DreamEngine engaged. Scanning telemetry traces.', 'hi');
    await sleep(700);
    L('Friction: [ROLLBACK_CYCLE x3] [EXCESSIVE_TRANSITIONS x12]', 'err');
    await sleep(500);
    L('Success: [CLEAN_COMPLETION x5] [FIRST_ATTEMPT x3]', 'ok');
    await sleep(500);
    L('Synthesizing governance patches.', 'hi');
    await sleep(600);

    // Show patches
    const report = document.getElementById('dream-report');
    report.style.display = 'block';
    document.getElementById('patch-container').innerHTML = `
        <div style="background:rgba(0,0,0,0.25);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:0.65rem;margin-bottom:6px;">
                <span style="color:var(--gold)">[THRESHOLD]</span>
                <span style="color:var(--text-dim)">antigravity.yaml</span>
            </div>
            <div style="font-size:0.78rem;color:#ccc;line-height:1.5;">Reduce max_loop_count from 5 → 3 to prevent compute exhaustion.</div>
        </div>
        <div style="background:rgba(0,0,0,0.25);border:1px solid var(--border);border-radius:8px;padding:14px;">
            <div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:0.65rem;margin-bottom:6px;">
                <span style="color:var(--gold)">[RULE]</span>
                <span style="color:var(--text-dim)">rules/09-circuit-breaker.md</span>
            </div>
            <div style="font-size:0.78rem;color:#ccc;line-height:1.5;">Halt after 2 identical rollbacks and request human intervention.</div>
        </div>`;

    L('Patches synthesized. System rules updated.', 'ok');
    await sleep(600);

    document.getElementById('sim-memory').style.display = 'block';
    L('Long-term memory consolidated.', 'ok');
    setSimNode('dream', '');

    btn.disabled = false;
    btn.textContent = 'Restart Simulation';
    simRunning = false;
}

// ── Animated Metric Ticker ──────────────────────────
setInterval(() => {
    const latEl = document.getElementById('m-latency');
    if (!latEl) return;
    const base = parseInt(latEl.textContent);
    if (isNaN(base)) return;
    const jitter = Math.floor(Math.random() * 20) - 10;
    latEl.textContent = Math.max(80, base + jitter) + 'ms';

    const tpsEl = document.getElementById('m-tps');
    const tpsBase = parseInt(tpsEl.textContent);
    if (!isNaN(tpsBase)) {
        tpsEl.textContent = Math.max(600, tpsBase + Math.floor(Math.random() * 40) - 20);
    }
}, 3000);

// ── Architecture flow animation (subtle node pulsing) ──
let flowIdx = 0;
const dagNodeEls = document.querySelectorAll('#dag-nodes .dag-node');
setInterval(() => {
    dagNodeEls.forEach(n => {
        if (!n.classList.contains('active')) {
            n.style.borderColor = '';
        }
    });
    if (dagNodeEls[flowIdx] && !dagNodeEls[flowIdx].classList.contains('active')) {
        dagNodeEls[flowIdx].style.borderColor = 'rgba(56,189,248,0.25)';
    }
    flowIdx = (flowIdx + 1) % dagNodeEls.length;
}, 1200);
