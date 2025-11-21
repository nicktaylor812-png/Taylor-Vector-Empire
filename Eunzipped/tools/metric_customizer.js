const PLAYER_DATA = [
    { rank: 1, player: "Russell Westbrook", season: "2016-17", year: 2017, tusg: 48.1, pvr: 25.11, mpg: 34.6, ppg: 31.6, apg: 10.4, fga: 24.0, fta: 10.4, tov: 5.4, era_pace: 98.0 },
    { rank: 2, player: "James Harden", season: "2018-19", year: 2019, tusg: 45.71, pvr: 18.55, mpg: 36.8, ppg: 36.1, apg: 7.5, fga: 24.5, fta: 11.0, tov: 5.0, era_pace: 98.0 },
    { rank: 3, player: "Wilt Chamberlain", season: "1961-62", year: 1962, tusg: 44.73, pvr: 0.63, mpg: 48.5, ppg: 50.4, apg: 2.4, fga: 39.5, fta: 17.0, tov: 5.0, era_pace: 115.0 },
    { rank: 4, player: "Giannis Antetokounmpo", season: "2019-20", year: 2020, tusg: 43.51, pvr: 28.35, mpg: 30.4, ppg: 29.5, apg: 5.6, fga: 19.7, fta: 10.5, tov: 3.1, era_pace: 99.5 },
    { rank: 5, player: "Kobe Bryant", season: "2005-06", year: 2006, tusg: 42.87, pvr: 10.72, mpg: 41.0, ppg: 35.4, apg: 4.5, fga: 27.2, fta: 10.2, tov: 3.1, era_pace: 95.0 },
    { rank: 6, player: "Michael Jordan", season: "1987-88", year: 1988, tusg: 40.13, pvr: 15.54, mpg: 40.4, ppg: 35.0, apg: 5.9, fga: 27.8, fta: 11.9, tov: 3.1, era_pace: 107.0 },
    { rank: 7, player: "Stephen Curry", season: "2015-16", year: 2016, tusg: 36.87, pvr: 40.27, mpg: 34.2, ppg: 30.1, apg: 6.7, fga: 20.2, fta: 5.1, tov: 3.3, era_pace: 98.0 },
    { rank: 8, player: "Kevin Durant", season: "2013-14", year: 2014, tusg: 36.06, pvr: 23.79, mpg: 38.5, ppg: 32.0, apg: 5.5, fga: 20.8, fta: 9.2, tov: 3.5, era_pace: 98.0 },
    { rank: 9, player: "Shaquille O'Neal", season: "1999-00", year: 2000, tusg: 34.82, pvr: 16.5, mpg: 40.0, ppg: 29.7, apg: 3.8, fga: 19.0, fta: 13.1, tov: 2.8, era_pace: 95.0 },
    { rank: 10, player: "Nikola Jokić", season: "2021-22", year: 2022, tusg: 33.73, pvr: 44.54, mpg: 33.5, ppg: 27.1, apg: 7.9, fga: 18.0, fta: 5.5, tov: 3.0, era_pace: 99.5 },
    { rank: 11, player: "Kareem Abdul-Jabbar", season: "1971-72", year: 1972, tusg: 33.29, pvr: 15.19, mpg: 44.2, ppg: 34.8, apg: 4.6, fga: 25.2, fta: 10.0, tov: 3.2, era_pace: 107.0 },
    { rank: 12, player: "LeBron James", season: "2012-13", year: 2013, tusg: 31.03, pvr: 39.21, mpg: 37.9, ppg: 26.8, apg: 7.3, fga: 17.8, fta: 7.3, tov: 3.0, era_pace: 98.0 },
    { rank: 13, player: "Tim Duncan", season: "2001-02", year: 2002, tusg: 30.18, pvr: 15.07, mpg: 40.6, ppg: 25.5, apg: 3.7, fga: 18.8, fta: 6.7, tov: 2.5, era_pace: 95.0 },
    { rank: 14, player: "Magic Johnson", season: "1986-87", year: 1987, tusg: 29.51, pvr: 44.03, mpg: 36.3, ppg: 23.9, apg: 12.2, fga: 17.7, fta: 5.4, tov: 3.8, era_pace: 107.0 },
    { rank: 15, player: "Larry Bird", season: "1987-88", year: 1988, tusg: 28.8, pvr: 44.35, mpg: 37.9, ppg: 29.9, apg: 6.1, fga: 19.1, fta: 5.3, tov: 2.9, era_pace: 107.0 }
];

const DEFAULT_PARAMS = {
    ftaMultiplier: 0.44,
    astHighMultiplier: 2.3,
    astLowMultiplier: 1.8,
    astThreshold: 1.8
};

let currentParams = { ...DEFAULT_PARAMS };
let originalRankings = {};

function calculateCustomTUSG(player) {
    const mpg = player.mpg;
    const fga = player.fga;
    const tov = player.tov;
    const fta = player.fta;
    const teamPace = player.era_pace;

    if (mpg === 0 || teamPace === 0) return 0;

    const numerator = fga + tov + (fta * currentParams.ftaMultiplier);
    const denominator = (mpg / 48) * teamPace;

    if (denominator === 0) return 0;

    return (numerator / denominator) * 100;
}

function calculateCustomPVR(player) {
    const pts = player.ppg;
    const ast = player.apg;
    const fga = player.fga;
    const tov = player.tov;
    const fta = player.fta;

    const astTovRatio = tov === 0 ? (ast > 0 ? ast : 0) : ast / tov;

    const multiplier = astTovRatio > currentParams.astThreshold 
        ? currentParams.astHighMultiplier 
        : currentParams.astLowMultiplier;

    const numerator = pts + (ast * multiplier);
    const denominator = fga + tov + (currentParams.ftaMultiplier * fta) + ast;

    if (denominator === 0) return 0;

    return ((numerator / denominator) - 1.00) * 100;
}

function updateLeaderboard() {
    const playersWithCustomMetrics = PLAYER_DATA.map(player => {
        const customTUSG = calculateCustomTUSG(player);
        const customPVR = calculateCustomPVR(player);
        
        return {
            ...player,
            customTUSG,
            customPVR
        };
    });

    playersWithCustomMetrics.sort((a, b) => b.customTUSG - a.customTUSG);

    const top10 = playersWithCustomMetrics.slice(0, 10);

    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';

    top10.forEach((player, index) => {
        const newRank = index + 1;
        const originalRank = player.rank;
        const rankChange = originalRank - newRank;

        let rankChangeHTML = '';
        if (rankChange > 0) {
            rankChangeHTML = `<span class="rank-change up">↑ ${rankChange}</span>`;
        } else if (rankChange < 0) {
            rankChangeHTML = `<span class="rank-change down">↓ ${Math.abs(rankChange)}</span>`;
        } else {
            rankChangeHTML = `<span class="rank-change same">—</span>`;
        }

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="center highlight">${newRank}</td>
            <td class="player-col">${player.player}</td>
            <td>${player.season}</td>
            <td class="center">${player.tusg.toFixed(2)}%</td>
            <td class="center highlight">${player.customTUSG.toFixed(2)}%</td>
            <td class="center">${player.pvr.toFixed(2)}</td>
            <td class="center highlight">${player.customPVR.toFixed(2)}</td>
            <td class="center">${rankChangeHTML}</td>
        `;
        tbody.appendChild(row);
    });

    updateInsights(playersWithCustomMetrics);
}

function updateInsights(playersWithCustomMetrics) {
    const insightsGrid = document.getElementById('insights-grid');
    insightsGrid.innerHTML = '';

    const sortedByCustomTUSG = [...playersWithCustomMetrics].sort((a, b) => b.customTUSG - a.customTUSG);
    const sortedByCustomPVR = [...playersWithCustomMetrics].sort((a, b) => b.customPVR - a.customPVR);

    const insights = [];

    const biggestRiseByTUSG = sortedByCustomTUSG
        .map((p, idx) => ({ player: p, newRank: idx + 1, rise: p.rank - (idx + 1) }))
        .sort((a, b) => b.rise - a.rise)[0];

    if (biggestRiseByTUSG && biggestRiseByTUSG.rise > 0) {
        insights.push({
            icon: '🚀',
            title: 'Biggest TUSG% Riser',
            text: `${biggestRiseByTUSG.player.player} jumped from #${biggestRiseByTUSG.player.rank} to <span class="metric-highlight">#${biggestRiseByTUSG.newRank}</span> in TUSG% rankings (+${biggestRiseByTUSG.rise} spots) with FTA multiplier at ${currentParams.ftaMultiplier.toFixed(2)}.`
        });
    }

    const biggestRiseByPVR = sortedByCustomPVR
        .map((p, idx) => ({ player: p, newRank: idx + 1, rise: p.rank - (idx + 1) }))
        .sort((a, b) => b.rise - a.rise)[0];

    if (biggestRiseByPVR && biggestRiseByPVR.rise > 0 && biggestRiseByPVR.player.player !== biggestRiseByTUSG?.player.player) {
        insights.push({
            icon: '📈',
            title: 'Top PVR Improver',
            text: `${biggestRiseByPVR.player.player} benefits most from current PVR settings, rising <span class="metric-highlight">+${biggestRiseByPVR.rise} ranks</span> with AST multipliers at ${currentParams.astLowMultiplier.toFixed(1)}/${currentParams.astHighMultiplier.toFixed(1)}.`
        });
    }

    const ftaDiff = currentParams.ftaMultiplier - DEFAULT_PARAMS.ftaMultiplier;
    if (Math.abs(ftaDiff) > 0.05) {
        const direction = ftaDiff > 0 ? 'increased' : 'decreased';
        const impact = ftaDiff > 0 ? 'boosts high FTA players' : 'reduces FTA impact';
        insights.push({
            icon: '⚖️',
            title: 'FTA Multiplier Impact',
            text: `FTA multiplier ${direction} to <span class="metric-highlight">${currentParams.ftaMultiplier.toFixed(2)}</span> from default 0.44, which ${impact} like Harden and Westbrook.`
        });
    }

    const thresholdDiff = currentParams.astThreshold - DEFAULT_PARAMS.astThreshold;
    if (Math.abs(thresholdDiff) > 0.2) {
        const direction = thresholdDiff > 0 ? 'raised' : 'lowered';
        const impact = thresholdDiff > 0 ? 'fewer players qualify for high multiplier' : 'more players qualify for high multiplier';
        insights.push({
            icon: '🎯',
            title: 'AST/TOV Threshold Change',
            text: `AST/TOV threshold ${direction} to <span class="metric-highlight">${currentParams.astThreshold.toFixed(1)}</span>, meaning ${impact}, affecting playmakers significantly.`
        });
    }

    if (insights.length === 0) {
        insights.push({
            icon: '💡',
            title: 'Default Settings',
            text: 'Using default formula parameters. Adjust sliders above to see how rankings change and generate insights!'
        });
    }

    insights.forEach(insight => {
        const card = document.createElement('div');
        card.className = 'insight-card';
        card.innerHTML = `
            <h4>${insight.icon} ${insight.title}</h4>
            <p>${insight.text}</p>
        `;
        insightsGrid.appendChild(card);
    });
}

function updateFormulaDisplay() {
    document.getElementById('formula-fta').textContent = currentParams.ftaMultiplier.toFixed(2);
    document.getElementById('formula-pvr-fta').textContent = currentParams.ftaMultiplier.toFixed(2);
    document.getElementById('formula-high').textContent = currentParams.astHighMultiplier.toFixed(1);
    document.getElementById('formula-low').textContent = currentParams.astLowMultiplier.toFixed(1);
    document.getElementById('formula-threshold').textContent = currentParams.astThreshold.toFixed(1);
}

function setupSliders() {
    const ftaSlider = document.getElementById('fta-multiplier');
    const ftaValue = document.getElementById('fta-mult-val');
    
    ftaSlider.addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        currentParams.ftaMultiplier = value;
        ftaValue.textContent = value.toFixed(2);
        updateFormulaDisplay();
        updateLeaderboard();
    });

    const astHighSlider = document.getElementById('ast-high-multiplier');
    const astHighValue = document.getElementById('ast-high-val');
    
    astHighSlider.addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        currentParams.astHighMultiplier = value;
        astHighValue.textContent = value.toFixed(1);
        updateFormulaDisplay();
        updateLeaderboard();
    });

    const astLowSlider = document.getElementById('ast-low-multiplier');
    const astLowValue = document.getElementById('ast-low-val');
    
    astLowSlider.addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        currentParams.astLowMultiplier = value;
        astLowValue.textContent = value.toFixed(1);
        updateFormulaDisplay();
        updateLeaderboard();
    });

    const astThresholdSlider = document.getElementById('ast-threshold');
    const astThresholdValue = document.getElementById('ast-threshold-val');
    
    astThresholdSlider.addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        currentParams.astThreshold = value;
        astThresholdValue.textContent = value.toFixed(1);
        updateFormulaDisplay();
        updateLeaderboard();
    });
}

function resetToDefaults() {
    currentParams = { ...DEFAULT_PARAMS };

    document.getElementById('fta-multiplier').value = DEFAULT_PARAMS.ftaMultiplier;
    document.getElementById('fta-mult-val').textContent = DEFAULT_PARAMS.ftaMultiplier.toFixed(2);

    document.getElementById('ast-high-multiplier').value = DEFAULT_PARAMS.astHighMultiplier;
    document.getElementById('ast-high-val').textContent = DEFAULT_PARAMS.astHighMultiplier.toFixed(1);

    document.getElementById('ast-low-multiplier').value = DEFAULT_PARAMS.astLowMultiplier;
    document.getElementById('ast-low-val').textContent = DEFAULT_PARAMS.astLowMultiplier.toFixed(1);

    document.getElementById('ast-threshold').value = DEFAULT_PARAMS.astThreshold;
    document.getElementById('ast-threshold-val').textContent = DEFAULT_PARAMS.astThreshold.toFixed(1);

    updateFormulaDisplay();
    updateLeaderboard();
}

document.addEventListener('DOMContentLoaded', () => {
    PLAYER_DATA.forEach(player => {
        originalRankings[player.player] = player.rank;
    });

    setupSliders();
    updateFormulaDisplay();
    updateLeaderboard();
});
