// Universal Theme Manager - DeepSeek Style
(function() {
    const html = document.documentElement;
    
    // Apply saved theme immediately (before page renders)
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        const themeToggle = document.getElementById('theme-toggle');
        const themeText = document.getElementById('theme-text');
        
        if (themeToggle) {
            // Update button text
            if (themeText) {
                themeText.textContent = savedTheme === 'light' ? 'Dark' : 'Light';
            }
            
            // Add click handler
            themeToggle.addEventListener('click', function() {
                const currentTheme = html.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                
                html.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                
                if (themeText) {
                    themeText.textContent = newTheme === 'light' ? 'Dark' : 'Light';
                }
            });
        }
    });
})();
