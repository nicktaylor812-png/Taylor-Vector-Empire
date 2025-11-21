const PLAYER_DATA = [
    { rank: 1, player: "Russell Westbrook", season: "2016-17", year: 2017, tusg: 48.1, pvr: 25.11, mpg: 34.6, ppg: 31.6, apg: 10.4, fga: 24.0, fta: 10.4, tov: 5.4 },
    { rank: 2, player: "James Harden", season: "2018-19", year: 2019, tusg: 45.71, pvr: 18.55, mpg: 36.8, ppg: 36.1, apg: 7.5, fga: 24.5, fta: 11.0, tov: 5.0 },
    { rank: 3, player: "Wilt Chamberlain", season: "1961-62", year: 1962, tusg: 44.73, pvr: 0.63, mpg: 48.5, ppg: 50.4, apg: 2.4, fga: 39.5, fta: 17.0, tov: 5.0 },
    { rank: 4, player: "Giannis Antetokounmpo", season: "2019-20", year: 2020, tusg: 43.51, pvr: 28.35, mpg: 30.4, ppg: 29.5, apg: 5.6, fga: 19.7, fta: 10.5, tov: 3.1 },
    { rank: 5, player: "Kobe Bryant", season: "2005-06", year: 2006, tusg: 42.87, pvr: 10.72, mpg: 41.0, ppg: 35.4, apg: 4.5, fga: 27.2, fta: 10.2, tov: 3.1 },
    { rank: 6, player: "Michael Jordan", season: "1987-88", year: 1988, tusg: 40.13, pvr: 15.54, mpg: 40.4, ppg: 35.0, apg: 5.9, fga: 27.8, fta: 11.9, tov: 3.1 },
    { rank: 7, player: "Stephen Curry", season: "2015-16", year: 2016, tusg: 36.87, pvr: 40.27, mpg: 34.2, ppg: 30.1, apg: 6.7, fga: 20.2, fta: 5.1, tov: 3.3 },
    { rank: 8, player: "Kevin Durant", season: "2013-14", year: 2014, tusg: 36.06, pvr: 23.79, mpg: 38.5, ppg: 32.0, apg: 5.5, fga: 20.8, fta: 9.2, tov: 3.5 },
    { rank: 9, player: "Shaquille O'Neal", season: "1999-00", year: 2000, tusg: 34.82, pvr: 16.5, mpg: 40.0, ppg: 29.7, apg: 3.8, fga: 19.0, fta: 13.1, tov: 2.8 },
    { rank: 10, player: "Nikola Jokić", season: "2021-22", year: 2022, tusg: 33.73, pvr: 44.54, mpg: 33.5, ppg: 27.1, apg: 7.9, fga: 18.0, fta: 5.5, tov: 3.0 },
    { rank: 11, player: "Kareem Abdul-Jabbar", season: "1971-72", year: 1972, tusg: 33.29, pvr: 15.19, mpg: 44.2, ppg: 34.8, apg: 4.6, fga: 25.2, fta: 10.0, tov: 3.2 },
    { rank: 12, player: "LeBron James", season: "2012-13", year: 2013, tusg: 31.03, pvr: 39.21, mpg: 37.9, ppg: 26.8, apg: 7.3, fga: 17.8, fta: 7.3, tov: 3.0 },
    { rank: 13, player: "Tim Duncan", season: "2001-02", year: 2002, tusg: 30.18, pvr: 15.07, mpg: 40.6, ppg: 25.5, apg: 3.7, fga: 18.8, fta: 6.7, tov: 2.5 },
    { rank: 14, player: "Magic Johnson", season: "1986-87", year: 1987, tusg: 29.51, pvr: 44.03, mpg: 36.3, ppg: 23.9, apg: 12.2, fga: 17.7, fta: 5.4, tov: 3.8 },
    { rank: 15, player: "Larry Bird", season: "1987-88", year: 1988, tusg: 28.8, pvr: 44.35, mpg: 37.9, ppg: 29.9, apg: 6.1, fga: 19.1, fta: 5.3, tov: 2.9 }
];

const ERA_PACE_DEFAULTS = {
    '1960s': 115.0,
    '1970s': 107.0,
    '1990s': 95.0,
    '2010s': 98.0,
    '2020s': 99.5
};

let selectedPlayers = new Set();
let charts = {};

function getPlayerEra(year) {
    if (year >= 1950 && year < 1970) return '1960s';
    if (year >= 1970 && year < 1990) return '1970s';
    if (year >= 1990 && year < 2010) return '1990s';
    if (year >= 2010 && year < 2020) return '2010s';
    if (year >= 2020) return '2020s';
    return '2020s';
}

function getEraPace(era) {
    const sliderMap = {
        '1960s': 'pace-1960s',
        '1970s': 'pace-1970s',
        '1990s': 'pace-1990s',
        '2010s': 'pace-2010s',
        '2020s': 'pace-2020s'
    };
    return parseFloat(document.getElementById(sliderMap[era]).value);
}

function calculateAdjustedTUSG(player) {
    const era = getPlayerEra(player.year);
    const adjustedPace = getEraPace(era);
    const usageScaling = parseFloat(document.getElementById('usage-scaling').value);
    
    const mpg = player.mpg;
    const fga = player.fga;
    const tov = player.tov;
    const fta = player.fta;
    
    if (mpg === 0 || adjustedPace === 0) return 0;
    
    const numerator = (fga + tov + (fta * 0.44)) * usageScaling;
    const denominator = (mpg / 48) * adjustedPace;
    
    return denominator === 0 ? 0 : (numerator / denominator) * 100;
}

function calculateAdjustedPVR(player) {
    const era = getPlayerEra(player.year);
    const year = player.year;
    
    const pts = player.ppg;
    const ast = player.apg;
    const fga = player.fga;
    const tov = player.tov;
    const fta = player.fta;
    
    const astTovRatio = tov === 0 ? (ast > 0 ? ast : 0) : ast / tov;
    const multiplier = astTovRatio > 1.8 ? 2.3 : 1.8;
    
    let adjustedPts = pts;
    let adjustedFga = fga;
    
    const defenseMultiplier = parseFloat(document.getElementById('defense-multiplier').value);
    adjustedPts = adjustedPts / defenseMultiplier;
    
    const handcheckPenalty = parseFloat(document.getElementById('handcheck-penalty').value);
    if (year < 2004 && handcheckPenalty > 0) {
        adjustedPts = adjustedPts * (1 - handcheckPenalty / 100);
    }
    
    const spacingBonus = parseFloat(document.getElementById('spacing-bonus').value);
    if (year >= 2010 && spacingBonus > 0) {
        adjustedPts = adjustedPts * (1 + spacingBonus / 100);
    }
    
    const numerator = adjustedPts + (ast * multiplier);
    const denominator = adjustedFga + tov + (0.44 * fta) + ast;
    
    if (denominator === 0) return 0;
    
    return ((numerator / denominator) - 1.00) * 100;
}

function initializePlayerGrid() {
    const grid = document.getElementById('player-grid');
    grid.innerHTML = '';
    
    PLAYER_DATA.forEach(player => {
        const card = document.createElement('div');
        card.className = 'player-card';
        card.onclick = () => togglePlayer(player, card);
        
        const era = getPlayerEra(player.year);
        
        card.innerHTML = `
            <h3>${player.player}</h3>
            <div class="season">${player.season} <span class="era-badge era-${era}">${era}</span></div>
            <div class="quick-stats">
                <div class="stat">PPG: <span>${player.ppg.toFixed(1)}</span></div>
                <div class="stat">APG: <span>${player.apg.toFixed(1)}</span></div>
                <div class="stat">MPG: <span>${player.mpg.toFixed(1)}</span></div>
            </div>
        `;
        
        grid.appendChild(card);
        
        if (['Michael Jordan', 'LeBron James', 'Kobe Bryant', 'Wilt Chamberlain', 'Magic Johnson', 'Larry Bird'].includes(player.player)) {
            selectedPlayers.add(player.player);
            card.classList.add('selected');
        }
    });
}

function togglePlayer(player, card) {
    if (selectedPlayers.has(player.player)) {
        selectedPlayers.delete(player.player);
        card.classList.remove('selected');
    } else {
        if (selectedPlayers.size >= 6) {
            alert('Maximum 6 players can be selected for comparison');
            return;
        }
        selectedPlayers.add(player.player);
        card.classList.add('selected');
    }
    updateAllVisualizations();
}

function getSelectedPlayerData() {
    return PLAYER_DATA.filter(p => selectedPlayers.has(p.player));
}

function setupSliders() {
    const sliders = [
        { id: 'pace-1960s', valueId: 'pace-1960s-val' },
        { id: 'pace-1970s', valueId: 'pace-1970s-val' },
        { id: 'pace-1990s', valueId: 'pace-1990s-val' },
        { id: 'pace-2010s', valueId: 'pace-2010s-val' },
        { id: 'pace-2020s', valueId: 'pace-2020s-val' },
        { id: 'defense-multiplier', valueId: 'defense-val', suffix: 'x' },
        { id: 'handcheck-penalty', valueId: 'handcheck-val', suffix: '%' },
        { id: 'usage-scaling', valueId: 'usage-val', suffix: 'x' },
        { id: 'spacing-bonus', valueId: 'spacing-val', suffix: '%' }
    ];

    sliders.forEach(slider => {
        const element = document.getElementById(slider.id);
        const valueElement = document.getElementById(slider.valueId);
        
        element.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            valueElement.textContent = value.toFixed(slider.suffix === 'x' ? 2 : 1) + (slider.suffix || '');
            updateAllVisualizations();
        });
    });
}

function resetAllControls() {
    document.getElementById('pace-1960s').value = 115.0;
    document.getElementById('pace-1970s').value = 107.0;
    document.getElementById('pace-1990s').value = 95.0;
    document.getElementById('pace-2010s').value = 98.0;
    document.getElementById('pace-2020s').value = 99.5;
    document.getElementById('defense-multiplier').value = 1.00;
    document.getElementById('handcheck-penalty').value = 0;
    document.getElementById('usage-scaling').value = 1.00;
    document.getElementById('spacing-bonus').value = 0;

    document.getElementById('pace-1960s-val').textContent = '115.0';
    document.getElementById('pace-1970s-val').textContent = '107.0';
    document.getElementById('pace-1990s-val').textContent = '95.0';
    document.getElementById('pace-2010s-val').textContent = '98.0';
    document.getElementById('pace-2020s-val').textContent = '99.5';
    document.getElementById('defense-val').textContent = '1.00x';
    document.getElementById('handcheck-val').textContent = '0%';
    document.getElementById('usage-val').textContent = '1.00x';
    document.getElementById('spacing-val').textContent = '0%';

    updateAllVisualizations();
}

function updateAllVisualizations() {
    updateCharts();
    updateTimeline();
    updateWhatIfScenarios();
    updateStatsTable();
}

function updateCharts() {
    const players = getSelectedPlayerData();
    if (players.length === 0) return;

    const labels = players.map(p => p.player);
    const colors = [
        'rgba(0, 212, 255, 0.8)',
        'rgba(0, 255, 136, 0.8)',
        'rgba(255, 68, 136, 0.8)',
        'rgba(255, 204, 0, 0.8)',
        'rgba(138, 43, 226, 0.8)',
        'rgba(255, 140, 0, 0.8)'
    ];

    const originalTUSG = players.map(p => p.tusg.toFixed(2));
    const adjustedTUSG = players.map(p => calculateAdjustedTUSG(p).toFixed(2));
    const originalPVR = players.map(p => p.pvr.toFixed(2));
    const adjustedPVR = players.map(p => calculateAdjustedPVR(p).toFixed(2));

    createChart('tusg-chart', 'Original TUSG%', labels, originalTUSG, colors, '%', 'bar');
    createChart('adjusted-tusg-chart', 'Era-Adjusted TUSG%', labels, adjustedTUSG, colors, '%', 'bar');
    createChart('pvr-chart', 'Original PVR', labels, originalPVR, colors, '', 'bar');
    createChart('adjusted-pvr-chart', 'Adjusted PVR', labels, adjustedPVR, colors, '', 'bar');
    
    if (document.getElementById('pvr-evolution-chart')) {
        createPVREvolutionChart(players, colors);
    }
}

function createChart(canvasId, label, labels, data, colors, suffix, type = 'bar') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 2,
                tension: 0.4,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#00d4ff',
                    bodyColor: '#fff',
                    borderColor: '#00d4ff',
                    borderWidth: 2,
                    padding: 12,
                    callbacks: {
                        label: (context) => `${label}: ${context.parsed.y}${suffix}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: {
                        color: '#aaa',
                        callback: (value) => value + suffix
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#aaa' }
                }
            }
        }
    });
}

function createPVREvolutionChart(players, colors) {
    const ctx = document.getElementById('pvr-evolution-chart');
    if (!ctx) return;
    
    if (charts['pvr-evolution-chart']) {
        charts['pvr-evolution-chart'].destroy();
    }

    const datasets = players.map((player, index) => {
        const paceRange = [90, 95, 100, 105, 110, 115, 120, 125, 130];
        const pvrValues = paceRange.map(pace => {
            const originalPace = getEraPace(getPlayerEra(player.year));
            document.getElementById(`pace-${getPlayerEra(player.year)}`).value = pace;
            const pvr = calculateAdjustedPVR(player);
            document.getElementById(`pace-${getPlayerEra(player.year)}`).value = originalPace;
            return pvr.toFixed(2);
        });

        return {
            label: player.player,
            data: pvrValues,
            borderColor: colors[index].replace('0.8', '1'),
            backgroundColor: colors[index],
            borderWidth: 3,
            tension: 0.4,
            fill: false,
            pointRadius: 5,
            pointHoverRadius: 7
        };
    });

    charts['pvr-evolution-chart'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [90, 95, 100, 105, 110, 115, 120, 125, 130],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        color: '#aaa',
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#00d4ff',
                    bodyColor: '#fff',
                    borderColor: '#00d4ff',
                    borderWidth: 2,
                    padding: 12,
                    callbacks: {
                        title: (context) => `Pace: ${context[0].label}`,
                        label: (context) => `${context.dataset.label}: ${context.parsed.y} PVR`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: {
                        color: '#aaa',
                        callback: (value) => value.toFixed(1)
                    },
                    title: {
                        display: true,
                        text: 'PVR (Possession Value Rating)',
                        color: '#00ff88',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#aaa' },
                    title: {
                        display: true,
                        text: 'Pace (Possessions per 48 min)',
                        color: '#00ff88',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        }
    });
}

function updateTimeline() {
    const timeline = document.getElementById('timeline');
    if (!timeline) return;
    
    const players = getSelectedPlayerData();
    
    if (players.length === 0) {
        timeline.innerHTML = '<div style="text-align:center;padding:40px;color:#666;">Select players to see timeline</div>';
        return;
    }

    const minYear = Math.min(...players.map(p => p.year));
    const maxYear = Math.max(...players.map(p => p.year));
    const yearRange = maxYear - minYear || 1;

    timeline.innerHTML = '<div class="timeline-axis"></div>';

    const colors = ['#00d4ff', '#00ff88', '#ff4488', '#ffcc00', '#ba55d3', '#ff8c00'];

    players.forEach((player, index) => {
        const position = ((player.year - minYear) / yearRange) * 100;
        const marker = document.createElement('div');
        marker.className = 'timeline-marker';
        marker.style.left = position + '%';
        marker.style.background = colors[index % colors.length];
        marker.title = `${player.player} - ${player.season}`;

        const label = document.createElement('div');
        label.className = `timeline-label ${index % 2 === 0 ? 'above' : 'below'}`;
        label.style.left = position + '%';
        label.style.transform = 'translateX(-50%)';
        label.style.color = colors[index % colors.length];
        label.innerHTML = `<strong>${player.player}</strong><br>${player.season}`;

        marker.appendChild(label);
        timeline.appendChild(marker);
    });
}

function updateWhatIfScenarios() {
    const grid = document.getElementById('what-if-grid');
    const players = getSelectedPlayerData();

    if (players.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center;padding:40px;color:#666;">Select players to see what-if scenarios</div>';
        return;
    }

    grid.innerHTML = '';

    players.forEach(player => {
        const era = getPlayerEra(player.year);
        const originalTUSG = player.tusg;
        const adjustedTUSG = calculateAdjustedTUSG(player);
        const tusgChange = adjustedTUSG - originalTUSG;
        
        const originalPVR = player.pvr;
        const adjustedPVR = calculateAdjustedPVR(player);
        const pvrChange = adjustedPVR - originalPVR;

        const card = document.createElement('div');
        card.className = 'scenario-card';

        const targetEra = era === '1960s' ? '2020s' : '1960s';
        
        card.innerHTML = `
            <h4>🔮 ${player.player}</h4>
            <div class="scenario-text">
                What if <strong>${player.player}</strong> from the <span class="era-badge era-${era}">${era}</span> 
                played in the <span class="era-badge era-${targetEra}">${targetEra}</span> with current adjustments?
            </div>
            <div class="metric-row">
                <span class="metric-label">Original TUSG%</span>
                <span class="metric-value">${originalTUSG.toFixed(2)}%</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Adjusted TUSG%</span>
                <span class="metric-value">
                    ${adjustedTUSG.toFixed(2)}%
                    <span class="metric-change ${tusgChange >= 0 ? 'positive' : 'negative'}">
                        (${tusgChange >= 0 ? '+' : ''}${tusgChange.toFixed(2)}%)
                    </span>
                </span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Original PVR</span>
                <span class="metric-value">${originalPVR.toFixed(2)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Adjusted PVR</span>
                <span class="metric-value">
                    ${adjustedPVR.toFixed(2)}
                    <span class="metric-change ${pvrChange >= 0 ? 'positive' : 'negative'}">
                        (${pvrChange >= 0 ? '+' : ''}${pvrChange.toFixed(2)})
                    </span>
                </span>
            </div>
        `;

        grid.appendChild(card);
    });
}

function updateStatsTable() {
    const tbody = document.getElementById('stats-table-body');
    const players = getSelectedPlayerData();

    if (players.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:40px;color:#666;">Select players above to see detailed comparison</td></tr>';
        return;
    }

    tbody.innerHTML = '';

    players.forEach(player => {
        const era = getPlayerEra(player.year);
        const adjustedTUSG = calculateAdjustedTUSG(player);
        const adjustedPVR = calculateAdjustedPVR(player);

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="player-col">${player.player}</td>
            <td>${player.season}</td>
            <td><span class="era-badge era-${era}">${era}</span></td>
            <td class="highlight">${player.tusg.toFixed(2)}%</td>
            <td class="highlight">${adjustedTUSG.toFixed(2)}%</td>
            <td class="highlight">${player.pvr.toFixed(2)}</td>
            <td class="highlight">${adjustedPVR.toFixed(2)}</td>
            <td>${player.ppg.toFixed(1)}</td>
            <td>${player.apg.toFixed(1)}</td>
        `;
        tbody.appendChild(row);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initializePlayerGrid();
    setupSliders();
    updateAllVisualizations();
});
