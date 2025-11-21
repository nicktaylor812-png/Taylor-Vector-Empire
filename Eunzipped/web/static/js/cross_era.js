let playersData = [];
let selectedPlayers = {};
let tusgChart = null;
let pvrChart = null;

const ERA_PACE_MAP = {
    '1960s': { years: [1950, 1970], slider: 'pace-1960s', default: 115.0 },
    '1970s': { years: [1970, 1980], slider: 'pace-1970s', default: 107.0 },
    '1980s': { years: [1980, 1990], slider: 'pace-1970s', default: 107.0 },
    '1990s': { years: [1990, 2000], slider: 'pace-1990s', default: 95.0 },
    '2000s': { years: [2000, 2010], slider: 'pace-1990s', default: 95.0 },
    '2010s': { years: [2010, 2020], slider: 'pace-2010s', default: 98.0 },
    '2020s': { years: [2020, 2030], slider: 'pace-2020s', default: 99.5 }
};

function getPlayerEra(season) {
    const year = parseInt(season.split('-')[0]);
    
    if (year >= 1950 && year < 1970) return '1960s';
    if (year >= 1970 && year < 1980) return '1970s';
    if (year >= 1980 && year < 1990) return '1980s';
    if (year >= 1990 && year < 2000) return '1990s';
    if (year >= 2000 && year < 2010) return '2000s';
    if (year >= 2010 && year < 2020) return '2010s';
    if (year >= 2020 && year < 2030) return '2020s';
    
    return '2020s';
}

function getCurrentPace(era) {
    const sliderId = ERA_PACE_MAP[era].slider;
    const slider = document.getElementById(sliderId);
    return parseFloat(slider.value);
}

function calculateTUSG(player, adjustedPace) {
    const mpg = player.mpg;
    const fga = calculateFGA(player);
    const tov = calculateTOV(player);
    const fta = calculateFTA(player);
    
    if (mpg === 0 || adjustedPace === 0) return 0;
    
    const numerator = fga + tov + (fta * 0.44);
    const denominator = (mpg / 48) * adjustedPace;
    
    if (denominator === 0) return 0;
    
    return (numerator / denominator) * 100;
}

function calculateFGA(player) {
    const ppg = player.ppg;
    const fta = calculateFTA(player);
    const estimatedFG = (ppg - (fta * 0.75)) / 2.0;
    return Math.max(estimatedFG, ppg * 0.5);
}

function calculateFTA(player) {
    const ppg = player.ppg;
    return ppg * 0.30;
}

function calculateTOV(player) {
    const apg = player.apg;
    const ppg = player.ppg;
    return Math.max(apg * 0.25, ppg * 0.10);
}

function calculatePVR(player) {
    const pts = player.ppg;
    const ast = player.apg;
    const fga = calculateFGA(player);
    const tov = calculateTOV(player);
    const fta = calculateFTA(player);
    
    const astTovRatio = tov === 0 ? (ast > 0 ? ast : 0) : ast / tov;
    const multiplier = astTovRatio > 1.8 ? 2.3 : 1.8;
    
    const numerator = pts + (ast * multiplier);
    const denominator = fga + tov + (0.44 * fta) + ast;
    
    if (denominator === 0) return 0;
    
    return ((numerator / denominator) - 1.00) * 100;
}

async function loadPlayers() {
    try {
        const response = await fetch('/api/cross-era/players');
        const data = await response.json();
        playersData = data.players;
        
        populatePlayerSelects();
        
        setDefaultPlayers();
    } catch (error) {
        console.error('Error loading players:', error);
    }
}

function populatePlayerSelects() {
    const selects = ['player1', 'player2', 'player3', 'player4'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select Player...</option>';
        
        playersData.forEach(player => {
            const option = document.createElement('option');
            option.value = player.rank;
            option.textContent = `${player.player} (${player.season})`;
            select.appendChild(option);
        });
        
        select.addEventListener('change', handlePlayerSelection);
    });
}

function setDefaultPlayers() {
    const defaults = [
        { id: 'player1', name: 'Michael Jordan' },
        { id: 'player2', name: 'LeBron James' },
        { id: 'player3', name: 'Kobe Bryant' },
        { id: 'player4', name: 'Wilt Chamberlain' }
    ];
    
    defaults.forEach(def => {
        const player = playersData.find(p => p.player === def.name);
        if (player) {
            const select = document.getElementById(def.id);
            select.value = player.rank;
            selectedPlayers[def.id] = player;
        }
    });
    
    updateAllVisualizations();
}

function handlePlayerSelection(event) {
    const selectId = event.target.id;
    const rank = parseInt(event.target.value);
    
    if (rank) {
        const player = playersData.find(p => p.rank === rank);
        selectedPlayers[selectId] = player;
    } else {
        delete selectedPlayers[selectId];
    }
    
    updateAllVisualizations();
}

function updateAllVisualizations() {
    updateCharts();
    updateWhatIfScenarios();
    updateDetailedStats();
}

let pvrEvolutionChart = null;

function updateCharts() {
    const players = Object.values(selectedPlayers);
    
    if (players.length === 0) {
        return;
    }
    
    const labels = players.map(p => p.player);
    const colors = [
        'rgba(0, 212, 255, 0.8)',
        'rgba(0, 255, 136, 0.8)',
        'rgba(255, 68, 136, 0.8)',
        'rgba(255, 204, 0, 0.8)'
    ];
    
    const tusgData = players.map(p => {
        const era = getPlayerEra(p.season);
        const adjustedPace = getCurrentPace(era);
        return calculateTUSG(p, adjustedPace).toFixed(2);
    });
    
    const pvrData = players.map(p => calculatePVR(p).toFixed(2));
    
    updateTUSGChart(labels, tusgData, colors);
    updatePVRChart(labels, pvrData, colors);
    updatePVREvolutionChart(players, colors);
}

function updatePVREvolutionChart(players, colors) {
    const ctx = document.getElementById('pvr-evolution-chart');
    if (!ctx) return;
    
    if (pvrEvolutionChart) {
        pvrEvolutionChart.destroy();
    }

    const datasets = players.map((player, index) => {
        const paceRange = [90, 95, 100, 105, 110, 115, 120, 125, 130];
        const pvrValues = paceRange.map(pace => {
            return calculatePVR(player).toFixed(2);
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

    pvrEvolutionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [90, 95, 100, 105, 110, 115, 120, 125, 130],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
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
                    borderWidth: 1,
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
                        font: { size: 12, weight: 'bold' }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#aaa' },
                    title: {
                        display: true,
                        text: 'Pace (Possessions per 48 min)',
                        color: '#00ff88',
                        font: { size: 12, weight: 'bold' }
                    }
                }
            }
        }
    });
}

function updateTUSGChart(labels, data, colors) {
    const ctx = document.getElementById('tusg-chart').getContext('2d');
    
    if (tusgChart) {
        tusgChart.destroy();
    }
    
    tusgChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'TUSG%',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#00d4ff',
                    bodyColor: '#fff',
                    borderColor: '#00d4ff',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `TUSG%: ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#aaa',
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#aaa'
                    }
                }
            }
        }
    });
}

function updatePVRChart(labels, data, colors) {
    const ctx = document.getElementById('pvr-chart').getContext('2d');
    
    if (pvrChart) {
        pvrChart.destroy();
    }
    
    pvrChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'PVR',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#00ff88',
                    bodyColor: '#fff',
                    borderColor: '#00ff88',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `PVR: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#aaa'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#aaa'
                    }
                }
            }
        }
    });
}

function updateWhatIfScenarios() {
    const container = document.getElementById('what-if-container');
    const players = Object.values(selectedPlayers);
    
    if (players.length === 0) {
        container.innerHTML = '<p class="placeholder-text">Select players and adjust era pace to see "what if" scenarios</p>';
        return;
    }
    
    container.innerHTML = '';
    
    players.forEach(player => {
        const playerEra = getPlayerEra(player.season);
        const originalPace = player.era_pace;
        const currentPace = getCurrentPace(playerEra);
        
        const originalTUSG = player.tusg;
        const adjustedTUSG = calculateTUSG(player, currentPace);
        const tusgChange = adjustedTUSG - originalTUSG;
        
        const card = document.createElement('div');
        card.className = 'what-if-card';
        
        const changeClass = tusgChange >= 0 ? 'positive' : 'negative';
        const changeSymbol = tusgChange >= 0 ? '+' : '';
        
        card.innerHTML = `
            <h4>${player.player}</h4>
            <p><strong>Season:</strong> ${player.season}</p>
            <p><strong>Original Era:</strong> ${playerEra} (${originalPace} pace)</p>
            <p><strong>Adjusted Pace:</strong> ${currentPace.toFixed(1)}</p>
            
            <div class="metric">
                <span class="metric-label">Original TUSG%:</span>
                <span class="metric-value">${originalTUSG.toFixed(2)}%</span>
            </div>
            <div class="metric">
                <span class="metric-label">Adjusted TUSG%:</span>
                <span class="metric-value">
                    ${adjustedTUSG.toFixed(2)}%
                    <span class="metric-change ${changeClass}">(${changeSymbol}${tusgChange.toFixed(2)}%)</span>
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">PVR (unchanged):</span>
                <span class="metric-value">${player.pvr.toFixed(2)}</span>
            </div>
        `;
        
        container.appendChild(card);
    });
}

function updateDetailedStats() {
    const tbody = document.getElementById('stats-table-body');
    const players = Object.values(selectedPlayers);
    
    if (players.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">Select players to see detailed comparison</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    players.forEach(player => {
        const era = getPlayerEra(player.season);
        const adjustedPace = getCurrentPace(era);
        const adjustedTUSG = calculateTUSG(player, adjustedPace);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="player-name">${player.player}</td>
            <td>${player.season}</td>
            <td class="stat-highlight">${player.tusg.toFixed(2)}%</td>
            <td class="stat-highlight">${adjustedTUSG.toFixed(2)}%</td>
            <td class="stat-highlight">${player.pvr.toFixed(2)}</td>
            <td>${player.ppg.toFixed(1)}</td>
            <td>${player.apg.toFixed(1)}</td>
            <td>${player.mpg.toFixed(1)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

function setupSliders() {
    const sliders = document.querySelectorAll('.era-slider');
    
    sliders.forEach(slider => {
        const valueDisplay = document.getElementById(`${slider.id}-value`);
        
        slider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            valueDisplay.textContent = value.toFixed(1);
            updateAllVisualizations();
        });
    });
}

function setupResetButton() {
    const resetBtn = document.getElementById('reset-pace');
    
    resetBtn.addEventListener('click', () => {
        Object.keys(ERA_PACE_MAP).forEach(era => {
            const sliderId = ERA_PACE_MAP[era].slider;
            const slider = document.getElementById(sliderId);
            const valueDisplay = document.getElementById(`${sliderId}-value`);
            const defaultValue = ERA_PACE_MAP[era].default;
            
            slider.value = defaultValue;
            valueDisplay.textContent = defaultValue.toFixed(1);
        });
        
        updateAllVisualizations();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    setupSliders();
    setupResetButton();
    loadPlayers();
});
