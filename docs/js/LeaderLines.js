
export class LeaderLines {
    constructor(container) {
        this.container = container;
        this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        this.svg.classList.add("hb-leader-line");
        this.container.appendChild(this.svg);
        this.lines = new Map();
    }
    
    draw(organ, x1, y1, labelText) {
        // To draw properly, we need the bounding box of the organ relative to the SVG.
        // For simplicity, well just use the bounding rect of the organ node.
        const rect = organ.node.getBoundingClientRect();
        const containerRect = this.container.getBoundingClientRect();
        
        const centerX = (rect.left + rect.right) / 2 - containerRect.left;
        const centerY = (rect.top + rect.bottom) / 2 - containerRect.top;
        
        // Draw a path from organ center to label
        let group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        
        let path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.classList.add("hb-leader-path");
        
        // Target offset for text
        const endX = centerX > containerRect.width / 2 ? containerRect.width - 20 : 20;
        const endY = centerY;
        
        path.setAttribute("d", `M ${centerX},${centerY} L ${endX},${endY}`);
        
        let text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.classList.add("hb-leader-label");
        text.setAttribute("x", endX > 20 ? endX - 5 : endX + 5);
        text.setAttribute("y", endY - 5);
        text.setAttribute("text-anchor", endX > 20 ? "end" : "start");
        text.textContent = labelText;
        
        // Make text act as a button to isolate organ
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
    
    clear() {
        while(this.svg.firstChild) {
            this.svg.removeChild(this.svg.firstChild);
        }
        this.lines.clear();
    }
    
    redraw(selectedOrgans) {
        this.clear();
        selectedOrgans.forEach(organ => {
            if (organ.isVisible()) {
                this.draw(organ, 0, 0, organ.label);
            }
        });
    }
}
