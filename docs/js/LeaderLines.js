
export class LeaderLines {
    constructor(container) {
        this.container = container;
        this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        this.svg.classList.add("hb-leader-line");
        
        // Define arrow marker
        const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        const marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
        marker.setAttribute("id", "hb-arrow");
        marker.setAttribute("viewBox", "0 0 10 10");
        marker.setAttribute("refX", "8");
        marker.setAttribute("refY", "5");
        marker.setAttribute("markerWidth", "5");
        marker.setAttribute("markerHeight", "5");
        marker.setAttribute("orient", "auto-start-reverse");
        
        const arrowPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
        arrowPath.setAttribute("d", "M 0 1 L 10 5 L 0 9 z");
        // Inherit color from CSS or hardcode a decent color
        arrowPath.style.fill = "#94a3b8"; 
        
        marker.appendChild(arrowPath);
        defs.appendChild(marker);
        this.svg.appendChild(defs);
        
        this.container.appendChild(this.svg);
        this.lines = new Map();
    }
    
    clear() {
        // Keep the defs element, remove all groups
        const groups = this.svg.querySelectorAll("g");
        groups.forEach(g => g.remove());
        this.lines.clear();
    }
    
    redraw(selectedOrgans) {
        this.clear();
        
        const containerRect = this.container.getBoundingClientRect();
        if (containerRect.width === 0) return;
        
        const items = [];
        
        selectedOrgans.forEach(organ => {
            if (organ.isVisible()) {
                // Find the first actual path to avoid pointing to the empty center of multi-part organs (like lungs/kidneys)
                const targetNode = organ.node.tagName.toLowerCase() === 'path' ? organ.node : (organ.node.querySelector('path') || organ.node);
                const rect = targetNode.getBoundingClientRect();
                const centerX = (rect.left + rect.right) / 2 - containerRect.left;
                const centerY = (rect.top + rect.bottom) / 2 - containerRect.top;
                
                const isRight = centerX > containerRect.width / 2;
                items.push({ organ, centerX, centerY, isRight });
            }
        });
        
        const processSide = (sideItems, isRight) => {
            sideItems.sort((a, b) => a.centerY - b.centerY);
            
            let currentY = 15;
            const SPACING = 25;
            
            sideItems.forEach(item => {
                let targetY = Math.max(currentY, item.centerY);
                item.targetY = targetY;
                currentY = targetY + SPACING;
            });
            
            sideItems.forEach(item => {
                this.drawItem(item.organ, item.centerX, item.centerY, item.targetY, isRight, containerRect.width);
            });
        };
        
        processSide(items.filter(i => !i.isRight), false);
        processSide(items.filter(i => i.isRight), true);
    }
    
    drawItem(organ, startX, startY, endY, isRight, containerWidth) {
        let group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        
        let path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.classList.add("hb-leader-path");
        
        const endX = isRight ? containerWidth - 10 : 10;
        const bendX = isRight ? endX - 80 : endX + 80;
        
        // Path starts at the organ, goes to bendX, then horizontal to text
        path.setAttribute("d", `M ${startX},${startY} L ${bendX},${endY} L ${endX},${endY}`);
        path.setAttribute("marker-start", "url(#hb-arrow)");
        
        let text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.classList.add("hb-leader-label");
        text.setAttribute("x", isRight ? endX - 5 : endX + 5);
        text.setAttribute("y", endY + 4);
        text.setAttribute("text-anchor", isRight ? "end" : "start");
        text.textContent = organ.label;
        
        text.style.cursor = "pointer";
        text.style.pointerEvents = "all";
        text.addEventListener("click", (e) => {
            e.stopPropagation();
            organ.node.dispatchEvent(new MouseEvent("click", {
                bubbles: true,
                cancelable: true,
                view: window
            }));
        });
        
        group.appendChild(path);
        group.appendChild(text);
        this.svg.appendChild(group);
        this.lines.set(organ.id, group);
    }
}
