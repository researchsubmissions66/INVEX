
export class Tooltip {
    constructor() {
        this.element = document.createElement("div");
        this.element.className = "hb-tooltip";
        
        this.titleEl = document.createElement("div");
        this.titleEl.className = "hb-tooltip-title";
        
        this.subtitleEl = document.createElement("div");
        this.subtitleEl.className = "hb-tooltip-subtitle";
        
        this.bodyEl = document.createElement("div");
        this.bodyEl.className = "hb-tooltip-body";
        
        this.element.appendChild(this.titleEl);
        this.element.appendChild(this.subtitleEl);
        this.element.appendChild(this.bodyEl);
        
        document.body.appendChild(this.element);
        
        this.isPinned = false;
        this.pinnedOrgan = null;
    }
    
    show(title, subtitle, content, x, y) {
        this.titleEl.textContent = title;
        this.subtitleEl.textContent = subtitle;
        
        if (typeof content === "string") {
            this.bodyEl.innerHTML = content;
        } else if (content instanceof HTMLElement) {
            this.bodyEl.innerHTML = "";
            this.bodyEl.appendChild(content);
        } else {
            this.bodyEl.innerHTML = "";
        }
        
        this.element.classList.add("visible");
        this.move(x, y);
    }
    
    move(x, y) {
        // Basic collision detection with viewport
        const rect = this.element.getBoundingClientRect();
        let left = x + 15;
        let top = y + 15;
        
        if (left + rect.width > window.innerWidth) {
            left = x - rect.width - 15;
        }
        if (top + rect.height > window.innerHeight) {
            top = y - rect.height - 15;
        }
        
        this.element.style.left = `${left}px`;
        this.element.style.top = `${top}px`;
    }
    
    hide() {
        if (!this.isPinned) {
            this.element.classList.remove("visible");
        }
    }
    
    pin() {
        this.isPinned = true;
        this.element.classList.add("pinned");
    }
    
    unpin() {
        this.isPinned = false;
        this.element.classList.remove("pinned");
        this.hide();
    }
}
