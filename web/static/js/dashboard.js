// TAYLOR VECTOR TERMINAL - Dashboard JavaScript

let updateInterval;

// Fetch and update stats
async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('total-picks').textContent = stats.total_picks || 0;
        document.getElementById('avg-edge').textContent = stats.avg_edge ? `${stats.avg_edge}%` : '--';
        document.getElementById('highest-edge').textContent = stats.highest_edge ? `${stats.highest_edge}%` : '--';
        
        if (stats.last_updated) {
            const date = new Date(stats.last_updated);
            document.getElementById('last-update').textContent = `Last Update: ${date.toLocaleString()}`;
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// Fetch and display picks
async function updatePicks() {
    try {
        const response = await fetch('/api/picks');
        const picks = await response.json();
        
        const container = document.getElementById('picks-container');
        
        if (picks.length === 0) {
            container.innerHTML = '<div class="no-picks">No edges found yet. System is monitoring...</div>';
            return;
        }
        
        container.innerHTML = picks.map(pick => `
            <div class="pick-card">
                <div class="pick-header">
                    <div class="game-matchup">🔥 ${pick.game}</div>
                    <div class="edge-badge">${pick.edge.toFixed(1)}% EDGE</div>
                </div>
                <div class="pick-details">
                    <div class="detail-item">
                        <div class="detail-label">Pick</div>
                        <div class="detail-value">${pick.pick}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Home TUSG%</div>
                        <div class="detail-value">${pick.home_tusg.toFixed(1)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Away TUSG%</div>
                        <div class="detail-value">${pick.away_tusg.toFixed(1)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Home PVR</div>
                        <div class="detail-value">${pick.home_pvr.toFixed(1)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Away PVR</div>
                        <div class="detail-value">${pick.away_pvr.toFixed(1)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Spread</div>
                        <div class="detail-value">${pick.spread > 0 ? '+' : ''}${pick.spread}</div>
                    </div>
                </div>
                <div class="pick-timestamp">${new Date(pick.timestamp).toLocaleString()}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error fetching picks:', error);
        document.getElementById('picks-container').innerHTML = 
            '<div class="no-picks">Error loading picks. Please refresh.</div>';
    }
}

// Check live status
async function updateLiveStatus() {
    try {
        const response = await fetch('/api/live');
        const data = await response.json();
        
        const statusBadge = document.getElementById('live-status');
        if (data.live) {
            statusBadge.textContent = '● LIVE';
            statusBadge.className = 'status-badge live';
        } else {
            statusBadge.textContent = '● OFFLINE';
            statusBadge.className = 'status-badge offline';
        }
    } catch (error) {
        console.error('Error checking live status:', error);
    }
}

// Initialize dashboard
function init() {
    updateStats();
    updatePicks();
    updateLiveStatus();
    
    // Auto-refresh every 10 seconds
    updateInterval = setInterval(() => {
        updateStats();
        updatePicks();
        updateLiveStatus();
    }, 10000);
}

// Run on page load
document.addEventListener('DOMContentLoaded', init);
