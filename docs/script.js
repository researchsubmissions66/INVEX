// INVEX Interactive Elements
document.addEventListener('DOMContentLoaded', function() {
    // Scroll animations (IntersectionObserver)
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-up').forEach(el => observer.observe(el));

    // Scroll Progress Bar
    const progressBar = document.getElementById('scroll-progress');
    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrollPercent = (scrollTop / scrollHeight) * 100;
        if (progressBar) {
            progressBar.style.width = scrollPercent + '%';
        }
    });
    // Patch Rotation & Manifold Animation
    const patch = document.getElementById('animated-patch');
    const label = document.getElementById('patch-angle-label');
    const manifoldContainer = document.getElementById('manifold-points');
    
    if (patch && label && manifoldContainer) {
        let currentAngle = 0;
        let totalRotation = 0;
        
        // Base center of the tight cluster on the manifold
        const baseX = 110; // moved left
        const baseY = 100;
        
        // Minor offsets to show they map to *almost* the same point (invariance)
        const offsets = [
            {dx: 0, dy: 0},
            {dx: 4, dy: -3},
            {dx: -3, dy: 4},
            {dx: 3, dy: 3}
        ];
        
        // Colors for each rotation
        const colors = ['#a855f7', '#3b82f6', '#10b981', '#f59e0b'];
        
        let rotationStep = 0;
        
        // Initial dot for 0 deg
        const initialDot = document.createElement('div');
        initialDot.className = 'manifold-dot';
        initialDot.style.left = `${baseX + offsets[0].dx}px`;
        initialDot.style.top = `${baseY + offsets[0].dy}px`;
        initialDot.style.setProperty('--dot-color', colors[0]);
        manifoldContainer.appendChild(initialDot);
        
        setInterval(() => {
            rotationStep++;
            if (rotationStep >= 4) {
                // Clear the dots to start over
                manifoldContainer.innerHTML = '';
                rotationStep = 0;
            }
            
            currentAngle = (currentAngle + 90) % 360;
            totalRotation += 90;
            patch.style.transform = `rotate(${totalRotation}deg)`;
            label.innerText = `${currentAngle}° Rotation`;
            
            // Spawn new dot mapped for this rotation
            const dot = document.createElement('div');
            dot.className = 'manifold-dot';
            dot.style.left = `${((baseX + offsets[rotationStep].dx) / 280) * 100}%`;
            dot.style.top = `${((baseY + offsets[rotationStep].dy) / 200) * 100}%`;
            dot.style.setProperty('--dot-color', colors[rotationStep]);
            manifoldContainer.appendChild(dot);
            
        }, 1800);
    }

    // Expressiveness Animation
    const collapsedContainer = document.getElementById('manifold-collapsed-points');
    const expressiveContainer = document.getElementById('manifold-expressive-points');
    
    if (collapsedContainer && expressiveContainer) {
        // Base center of the tight cluster for collapsed
        const collapsedBaseX = 140;
        const collapsedBaseY = 100;
        
        // Base centers for expressive (4 distinct clusters mapping 4 different tissues)
        const expressiveCenters = [
            {x: 140, y: 112},  // Top left (Red)
            {x: 260, y: 122},  // Top right (Blue)
            {x: 20, y: 140},   // Bottom left (Green)
            {x: 140, y: 160}   // Bottom right (Orange)
        ];
        
        // Colors for the 4 tissue types
        const tissueColors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b'];
        
        let tissueStep = 0;
        
        setInterval(() => {
            tissueStep++;
            if (tissueStep >= 16) { // 16 dots total (4 of each color)
                collapsedContainer.innerHTML = '';
                expressiveContainer.innerHTML = '';
                tissueStep = 0;
            }
            
            const colorIndex = tissueStep % 4;
            const color = tissueColors[colorIndex];
            
            // Random offset for natural clustering scatter
            const offsetX = (Math.random() - 0.5) * 20;
            const offsetY = (Math.random() - 0.5) * 20;
            
            // Spawn dot in collapsed manifold (all mixed at center)
            const dotC = document.createElement('div');
            dotC.className = 'manifold-dot';
            dotC.style.left = `${((collapsedBaseX + offsetX) / 280) * 100}%`;
            dotC.style.top = `${((collapsedBaseY + offsetY) / 200) * 100}%`;
            dotC.style.setProperty('--dot-color', color);
            collapsedContainer.appendChild(dotC);
            
            // Spawn dot in expressive manifold (cleanly separated at specific clusters)
            const center = expressiveCenters[colorIndex];
            const dotE = document.createElement('div');
            dotE.className = 'manifold-dot';
            dotE.style.left = `${((center.x + offsetX) / 280) * 100}%`;
            dotE.style.top = `${((center.y + offsetY) / 200) * 100}%`;
            dotE.style.setProperty('--dot-color', color);
            expressiveContainer.appendChild(dotE);
            
        }, 350); // fast spawning
    }

    // Results Tab Logic
    const tabs = document.querySelectorAll('.results-tab');
    const panels = document.querySelectorAll('.result-panel');
    
    if (tabs.length > 0 && panels.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Hide all panels
                panels.forEach(p => p.style.display = 'none');
                
                // Show the target panel
                const targetId = tab.getAttribute('data-target');
                const targetPanel = document.getElementById(targetId);
                if (targetPanel) {
                    targetPanel.style.display = 'block';
                    // Re-trigger animation
                    targetPanel.classList.remove('visible');
                    setTimeout(() => targetPanel.classList.add('visible'), 50);
                }
            });
        });
    }
});

