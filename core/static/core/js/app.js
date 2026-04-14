// ── Rate Limiting (persists across page reloads) ──
function getRateLimit(key) {
    const data = JSON.parse(localStorage.getItem(key) || '{"count":0,"reset":0}');
    if (Date.now() > data.reset) {
        data.count = 0;
        data.reset = Date.now() + 3600000;
        localStorage.setItem(key, JSON.stringify(data));
    }
    return data;
}

function incrementRate(key) {
    const data = getRateLimit(key);
    data.count++;
    localStorage.setItem(key, JSON.stringify(data));
    return data.count;
}

function checkRate(key, max) {
    const data = getRateLimit(key);
    if (data.count >= max) {
        const mins = Math.ceil((data.reset - Date.now()) / 60000);
        showError(`Hourly limit reached. Try again in ${mins} minutes.`);
        return false;
    }
    return true;
}

// ── State ──
const state = {
    category: null,
    latitude: null,
    longitude: null,
    results: [],
    competitors: [],
    selectedBusiness: null,
    chatHistory: [],
    countryCode: null,
    areaType: null,
    areaName: null,
    locations: null,
    userName: null,
    userRole: null,
};

// Country flags mapping
const FLAGS = {
    'AZ': '🇦🇿', 'TR_IST': '🇹🇷', 'TR_ANK': '🇹🇷', 'TR_IZM': '🇹🇷',
    'TR_MUG': '🇹🇷', 'TR_BRS': '🇹🇷', 'GE': '🇬🇪', 'RO': '🇷🇴',
    'BG': '🇧🇬', 'PL': '🇵🇱', 'PT': '🇵🇹', 'DE': '🇩🇪',
    'IT_ROM': '🇮🇹', 'FR_PAR': '🇫🇷', 'UK_LON': '🇬🇧', 'ES_MAD': '🇪🇸',
    'US_NYC': '🇺🇸',
};

// ── DOM ──
const loader = document.getElementById('app-loader');
const errorEl = document.getElementById('error-msg');

function showLoader() { loader.classList.remove('hidden'); }
function hideLoader() { loader.classList.add('hidden'); }
function showError(msg) { errorEl.textContent = msg; errorEl.classList.remove('hidden'); setTimeout(() => errorEl.classList.add('hidden'), 4000); }

function goStep(num) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    const el = document.getElementById(`step-${num}`);
    if (el) { el.classList.remove('hidden'); el.classList.add('active'); }
}

function esc(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

// ── Hero Animation ──
function runHero() {
    const el = document.getElementById('hero-title');
    if (!el) return;
    const lines = ["Detect. Discover.", "Dominate the market."];
    el.innerHTML = lines.map(line =>
        `<div style="white-space:nowrap">${line.split('').map((c, i) =>
            `<span class="char-anim" style="transition-delay:${i * 25}ms">${c === ' ' ? '&nbsp;' : c}</span>`
        ).join('')}</div>`
    ).join('');

    setTimeout(() => {
        document.querySelectorAll('.char-anim').forEach(s => s.classList.add('visible'));
        document.querySelectorAll('.fade-node').forEach(s => s.classList.add('visible'));
        const sub2 = document.getElementById('hero-subtitle-2');
        if (sub2) sub2.style.opacity = '1';
    }, 150);
}

// ── Start App ──
function startApp() {
    document.getElementById('hero-section').classList.add('hidden');
    document.getElementById('app-root').classList.remove('hidden');
    loadCategories();
}

// ── 1. Categories ──
async function loadCategories() {
    showLoader();
    try {
        const res = await fetch('/api/categories/');
        const data = await res.json();
        const grid = document.getElementById('categories');
        grid.innerHTML = '';
        data.categories.forEach(cat => {
            const btn = document.createElement('button');
            btn.className = 'cat-btn';
            btn.textContent = cat;
            btn.addEventListener('click', () => {
                grid.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                state.category = cat;
                goStep(2);
            });
            grid.appendChild(btn);
        });
    } catch (e) { showError('Failed to load categories'); }
    hideLoader();
}

// ── 2. Location ──
function useMyLocation() {
    if (!navigator.geolocation) { showError('Geolocation not supported'); return; }
    const btn = document.getElementById('btn-my-location');
    const label = btn.querySelector('.method-label');
    label.textContent = 'Locating...';

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            state.latitude = pos.coords.latitude;
            state.longitude = pos.coords.longitude;
            document.getElementById('location-info').textContent = `${state.latitude.toFixed(4)}, ${state.longitude.toFixed(4)}`;
            searchByCoords();
        },
        () => {
            label.textContent = 'Near Me';
            showError('Could not get your location. Please allow access.');
        }
    );
}

function browseAreas() { loadCountries(); }

// ── 2b. Countries ──
async function loadCountries() {
    showLoader();
    try {
        const res = await fetch('/api/countries/');
        const data = await res.json();
        const grid = document.getElementById('country-list');
        grid.innerHTML = '';
        document.getElementById('area-types-wrap').classList.add('hidden');
        document.getElementById('area-list-wrap').classList.add('hidden');

        data.countries.forEach((c, i) => {
            const btn = document.createElement('button');
            btn.className = 'country-btn';
            btn.style.animationDelay = `${i * 40}ms`;
            btn.innerHTML = `<span class="country-flag">${FLAGS[c.code] || '🌍'}</span>${c.name}`;
            btn.addEventListener('click', () => selectCountry(c.code, btn));
            grid.appendChild(btn);
        });
        goStep('2b');
    } catch (e) { showError('Failed to load countries'); }
    hideLoader();
}

async function selectCountry(code, btn) {
    document.querySelectorAll('.country-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    state.countryCode = code;
    showLoader();
    try {
        const res = await fetch(`/api/locations/${code}/`);
        const data = await res.json();
        state.locations = data.areas;
        renderAreaTypes();
    } catch (e) { showError('Failed to load locations'); }
    hideLoader();
}

function renderAreaTypes() {
    const wrap = document.getElementById('area-types-wrap');
    const grid = document.getElementById('area-types');
    document.getElementById('area-list-wrap').classList.add('hidden');
    grid.innerHTML = '';

    const types = [
        { key: 'metro', label: 'Metro / Station' },
        { key: 'cadde', label: 'Street / Avenue' },
        { key: 'rayon', label: 'District / Borough' },
    ];

    types.forEach(t => {
        const btn = document.createElement('button');
        btn.className = 'area-type-btn';
        btn.textContent = t.label;
        btn.addEventListener('click', () => {
            grid.querySelectorAll('.area-type-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            state.areaType = t.key;
            renderAreas(t.key);
        });
        grid.appendChild(btn);
    });
    wrap.classList.remove('hidden');
}

function renderAreas(type) {
    const wrap = document.getElementById('area-list-wrap');
    const grid = document.getElementById('area-list');
    grid.innerHTML = '';
    const areas = state.locations[type];

    if (!areas || areas.length === 0) {
        grid.innerHTML = '<p style="color:var(--text-dim);font-size:13px;">No areas available for this type.</p>';
        wrap.classList.remove('hidden');
        return;
    }

    areas.forEach((area, i) => {
        const btn = document.createElement('button');
        btn.className = 'area-btn';
        btn.style.animationDelay = `${i * 30}ms`;
        btn.textContent = area.name;
        btn.addEventListener('click', () => {
            grid.querySelectorAll('.area-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            state.areaName = area.name;
            searchByArea();
        });
        grid.appendChild(btn);
    });
    wrap.classList.remove('hidden');
}

// ── Search ──
async function searchByCoords() {
    if (!checkRate('search_limit', 20)) return;
    showLoader();
    try {
        const res = await fetch('/api/search/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                latitude: state.latitude,
                longitude: state.longitude,
                category: state.category,
                radius: 1000,
            }),
        });
        const data = await res.json();
        if (data.error) { showError(data.error); hideLoader(); return; }
        state.results = data.results;
        state.competitors = data.competitors || [];
        incrementRate('search_limit');
        renderResults(data);
        goStep(3);
    } catch (e) { showError('Search failed'); }
    hideLoader();
}

async function searchByArea() {
    if (!checkRate('search_limit', 20)) return;
    showLoader();
    try {
        const res = await fetch('/api/search/area/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                country_code: state.countryCode,
                area_type: state.areaType,
                area_name: state.areaName,
                category: state.category,
            }),
        });
        const data = await res.json();
        if (data.error) { showError(data.error); hideLoader(); return; }
        state.results = data.results;
        state.competitors = data.competitors || [];
        incrementRate('search_limit');
        renderResults(data);
        goStep(3);
    } catch (e) { showError('Search failed'); }
    hideLoader();
}

function renderResults(data) {
    document.getElementById('results-count').textContent = `${data.without_website} of ${data.total_found}`;
    const grid = document.getElementById('results-list');
    grid.innerHTML = '';

    if (data.results.length === 0) {
        grid.innerHTML = '<div class="no-results">No businesses without websites found in this category.</div>';
        return;
    }

    data.results.forEach(biz => {
        const card = document.createElement('div');
        card.className = 'biz-card';
        card.innerHTML = `
            <h3>${esc(biz.name)}</h3>
            <p>${esc(biz.address)}</p>
            ${biz.phone ? `<p>📞 ${esc(biz.phone)}</p>` : ''}
            <span class="biz-type">${esc(biz.type)}</span>
        `;
        card.addEventListener('click', () => selectBusiness(biz));
        grid.appendChild(card);
    });
}

// ── 4. Chat ──
function selectBusiness(biz) {
    state.selectedBusiness = biz;
    state.chatHistory = [];

    document.getElementById('selected-business').innerHTML = `
        <h3>${esc(biz.name)}</h3>
        <p>${esc(biz.address)} ${biz.phone ? '· ' + esc(biz.phone) : ''}</p>
    `;

    document.getElementById('chat-messages').innerHTML = '';
    goStep(4);

    if (state.userName && state.userRole) {
        sendToAI(`My name is ${state.userName}, I'm a ${state.userRole}. Write the sales message now.`, true);
    } else {
        sendToAI('Show business info and ask for my name and profession.', true);
    }
}

document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';

    if (!state.userName) {
        const parts = text.split(',').map(s => s.trim());
        if (parts.length >= 2) {
            state.userName = parts[0];
            state.userRole = parts.slice(1).join(', ');
        } else {
            state.userName = text;
            state.userRole = '';
        }
    }

    addBubble(text, 'user');
    sendToAI(text, false);
}

async function sendToAI(text, isSystem) {
    if (!checkRate('chat_limit', 10)) return;

    state.chatHistory.push({ role: 'user', content: text });

    const sendBtn = document.getElementById('send-btn');
    const input = document.getElementById('chat-input');
    sendBtn.disabled = true;
    input.disabled = true;

    try {
        const res = await fetch('/api/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: state.chatHistory,
                business_info: state.selectedBusiness,
                competitors: state.competitors,
            }),
        });
        const data = await res.json();
        if (data.error) {
            showError(data.error);
        } else {
            state.chatHistory.push({ role: 'assistant', content: data.reply });
            addBubble(data.reply, 'ai');
            incrementRate('chat_limit');
        }
    } catch (e) { showError('AI failed to respond'); }

    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
}

function addBubble(text, type) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `msg msg-${type}`;

    const textEl = document.createElement('div');
    textEl.textContent = text;
    div.appendChild(textEl);

    if (type === 'ai') {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = 'Copy';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(text).then(() => {
                copyBtn.textContent = 'Copied!';
                setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500);
            });
        });
        div.appendChild(copyBtn);
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ── Navigation ──
function goHome() {
    document.getElementById('app-root').classList.add('hidden');
    document.getElementById('hero-section').classList.remove('hidden');
    runHero();
}

window.onload = runHero;