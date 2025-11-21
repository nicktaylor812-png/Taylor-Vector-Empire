let allPlayers = [];
let selectedPlayer1 = null;
let selectedPlayer2 = null;
let radarChart = null;

async function fetchPlayers() {
    try {
        const response = await fetch('/api/comparison/players');
        const data = await response.json();
        allPlayers = data.players || [];
        populatePlayerSelects();
    } catch (error) {
        console.error('Error fetching players:', error);
        document.getElementById('player1-select').innerHTML = '<option value="">Error loading players</option>';
        document.getElementById('player2-select').innerHTML = '<option value="">Error loading players</option>';
    }
}

function populatePlayerSelects() {
    const player1Select = document.getElementById('player1-select');
    const player2Select = document.getElementById('player2-select');
    
    const options = allPlayers.map(player => {
        const label = player.is_historical 
            ? `${player.name} (${player.season})` 
            : `${player.name} (2024-25)`;
        return `<option value="${player.id}">${label}</option>`;
    }).join('');
    
    player1Select.innerHTML = options;
    player2Select.innerHTML = options;
}

function filterPlayers(searchText, selectId) {
    const select = document.getElementById(selectId);
    const filteredPlayers = allPlayers.filter(player => 
        player.name.toLowerCase().includes(searchText.toLowerCase())
    );
    
    const options = filteredPlayers.map(player => {
        const label = player.is_historical 
            ? `${player.name} (${player.season})` 
            : `${player.name} (2024-25)`;
        return `<option value="${player.id}">${label}</option>`;
    }).join('');
    
    select.innerHTML = options || '<option value="">No players found</option>';
}

function getPlayerById(playerId) {
    return allPlayers.find(p => p.id === playerId);
}

function displayPlayerInfo(player, infoElementId) {
    const infoElement = document.getElementById(infoElementId);
    if (!player) {
        infoElement.innerHTML = '';
        return;
    }
    
    const season = player.is_historical ? player.season : '2024-25';
    infoElement.innerHTML = `
        <div class="player-card">
            <h4>${player.name}</h4>
            <p class="season">${season}</p>
            <div class="quick-stats">
                <div class="stat-item">
                    <span class="stat-label">PPG:</span>
                    <span class="stat-value">${player.ppg?.toFixed(1) || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">APG:</span>
                    <span class="stat-value">${player.apg?.toFixed(1) || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">MPG:</span>
                    <span class="stat-value">${player.mpg?.toFixed(1) || 'N/A'}</span>
                </div>
            </div>
        </div>
    `;
}

function calculateMetrics(player) {
    const tusg = player.tusg || 0;
    const pvr = player.pvr || 0;
    const ppg = player.ppg || 0;
    const apg = player.apg || 0;
    const mpg = player.mpg || 0;
    
    const fga = player.fga || 0;
    const fgm = player.fgm || 0;
    const tov = player.tov || 0;
    
    let efficiency = 50;
    if (fga > 0) {
        const fg_pct = (fgm / fga) * 100;
        const tov_rate = tov / (fga + tov);
        efficiency = fg_pct * (1 - tov_rate);
    }
    
    return {
        tusg: Math.min(tusg, 100),
        pvr: Math.min(Math.max(pvr + 50, 0), 100),
        ppg: Math.min(ppg * 2, 100),
        apg: Math.min(apg * 8, 100),
        mpg: Math.min(mpg * 2.5, 100),
        efficiency: Math.min(efficiency, 100)
    };
}

function createRadarChart(player1, player2) {
    const ctx = document.getElementById('radarChart').getContext('2d');
    
    const metrics1 = calculateMetrics(player1);
    const metrics2 = calculateMetrics(player2);
    
    if (radarChart) {
        radarChart.destroy();
    }
    
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['TUSG%', 'PVR', 'PPG', 'APG', 'MPG', 'Efficiency'],
            datasets: [
                {
                    label: player1.name,
                    data: [
                        metrics1.tusg,
                        metrics1.pvr,
                        metrics1.ppg,
                        metrics1.apg,
                        metrics1.mpg,
                        metrics1.efficiency
                    ],
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(255, 99, 132, 1)'
                },
                {
                    label: player2.name,
                    data: [
                        metrics2.tusg,
                        metrics2.pvr,
                        metrics2.ppg,
                        metrics2.apg,
                        metrics2.mpg,
                        metrics2.efficiency
                    ],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        font: {
                            size: 12
                        }
                    },
                    pointLabels: {
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        padding: 20
                    }
                }
            }
        }
    });
}

function displayStatsTable(player1, player2) {
    const tableBody = document.getElementById('stats-table-body');
    
    const stats = [
        { label: 'TUSG%', key: 'tusg', format: (v) => v.toFixed(2) + '%' },
        { label: 'PVR', key: 'pvr', format: (v) => v.toFixed(2) },
        { label: 'PPG', key: 'ppg', format: (v) => v.toFixed(1) },
        { label: 'APG', key: 'apg', format: (v) => v.toFixed(1) },
        { label: 'MPG', key: 'mpg', format: (v) => v.toFixed(1) },
        { label: 'FGA', key: 'fga', format: (v) => v.toFixed(1) },
        { label: 'FTA', key: 'fta', format: (v) => v.toFixed(1) },
        { label: 'TOV', key: 'tov', format: (v) => v.toFixed(1) }
    ];
    
    const rows = stats.map(stat => {
        const val1 = player1[stat.key] || 0;
        const val2 = player2[stat.key] || 0;
        const diff = val1 - val2;
        const diffClass = diff > 0 ? 'positive' : diff < 0 ? 'negative' : 'neutral';
        const diffText = diff > 0 ? `+${stat.format(Math.abs(diff))}` : diff < 0 ? `-${stat.format(Math.abs(diff))}` : '0';
        
        return `
            <tr>
                <td class="stat-label">${stat.label}</td>
                <td class="stat-value">${stat.format(val1)}</td>
                <td class="stat-value">${stat.format(val2)}</td>
                <td class="stat-diff ${diffClass}">${diffText}</td>
            </tr>
        `;
    }).join('');
    
    tableBody.innerHTML = rows;
    
    document.getElementById('player1-name-header').textContent = player1.name;
    document.getElementById('player2-name-header').textContent = player2.name;
}

async function compareSelected() {
    if (!selectedPlayer1 || !selectedPlayer2) {
        alert('Please select both players to compare');
        return;
    }
    
    try {
        const response = await fetch('/api/comparison/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player1_id: selectedPlayer1.id,
                player2_id: selectedPlayer2.id
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error comparing players: ' + data.error);
            return;
        }
        
        const player1Data = data.player1;
        const player2Data = data.player2;
        
        createRadarChart(player1Data, player2Data);
        displayStatsTable(player1Data, player2Data);
        
        document.getElementById('comparison-results').style.display = 'block';
        document.getElementById('comparison-results').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error comparing players:', error);
        alert('Failed to compare players. Please try again.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchPlayers();
    
    document.getElementById('player1-search').addEventListener('input', (e) => {
        filterPlayers(e.target.value, 'player1-select');
    });
    
    document.getElementById('player2-search').addEventListener('input', (e) => {
        filterPlayers(e.target.value, 'player2-select');
    });
    
    document.getElementById('player1-select').addEventListener('change', (e) => {
        selectedPlayer1 = getPlayerById(e.target.value);
        displayPlayerInfo(selectedPlayer1, 'player1-info');
        
        const compareBtn = document.getElementById('compare-btn');
        compareBtn.disabled = !(selectedPlayer1 && selectedPlayer2);
    });
    
    document.getElementById('player2-select').addEventListener('change', (e) => {
        selectedPlayer2 = getPlayerById(e.target.value);
        displayPlayerInfo(selectedPlayer2, 'player2-info');
        
        const compareBtn = document.getElementById('compare-btn');
        compareBtn.disabled = !(selectedPlayer1 && selectedPlayer2);
    });
    
    document.getElementById('compare-btn').addEventListener('click', compareSelected);
});
