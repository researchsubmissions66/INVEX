
import { Organ } from "./Organ.js";
import { Tooltip } from "./Tooltip.js";
import { Heatmap } from "./Heatmap.js";
import { LeaderLines } from "./LeaderLines.js";
import { throttle } from "./Utils.js";

export class HumanBody {
    constructor(selector) {
        this.container = document.querySelector(selector);
        this.organs = new Map();
        this.tooltip = new Tooltip();
        this.heatmap = new Heatmap();
        this.leaderLines = new LeaderLines(this.container);
        this.currentSex = "male"; 
        
        // Event hooks
        this.onSelectionChange = null;
    }
    
    async init() {
        // Load metadata
        const metaRes = await fetch("data/organs.json");
        const metadata = await metaRes.json();
        
        // Load SVG
        const svgRes = await fetch("assets/anatomy.svg");
        const svgText = await svgRes.text();
        this.container.innerHTML = svgText;
        
        const svgElement = this.container.querySelector("svg");
        svgElement.style.width = "100%";
        svgElement.style.height = "100%";
        
        // Re-append leader line SVG properly so it overlays
        this.container.appendChild(this.leaderLines.svg);
        
        // Map elements
        metadata.forEach(data => {
            const node = svgElement.querySelector(`[id="${data.id}"]`);
            if (node) {
                this.organs.set(data.id, new Organ(node, data));
            }
        });
        
        this._bindEvents();
        this.setSex(this.currentSex);
    }
    
    _bindEvents() {
        const svg = this.container.querySelector("svg");
        
        svg.addEventListener("mouseover", (e) => {
            const node = e.target.closest(".human-organ");
            if (node && !this.tooltip.isPinned) {
                const organ = this.organs.get(node.id);
                if (organ && organ.isVisible()) {
                    organ.highlight();
                    this.tooltip.show(organ.label, organ.system, `Aliases: ${organ.aliases.join(", ") || "None"}`, e.clientX, e.clientY);
                }
            }
        });
        
        svg.addEventListener("mousemove", throttle((e) => {
            if (!this.tooltip.isPinned) {
                this.tooltip.move(e.clientX, e.clientY);
            }
        }, 16));
        
        svg.addEventListener("mouseout", (e) => {
            const node = e.target.closest(".human-organ");
            if (node) {
                const organ = this.organs.get(node.id);
                if (organ) organ.unhighlight();
                if (!this.tooltip.isPinned) this.tooltip.hide();
            }
        });
        
        svg.addEventListener("click", (e) => {
            const node = e.target.closest(".human-organ");
            if (node) {
                const organ = this.organs.get(node.id);
                if (!organ || !organ.isVisible()) return;
                
                if (e.ctrlKey || e.metaKey || e.shiftKey) {
                    this.toggle(organ.id);
                } else {
                    this.select(organ.id);
                }
                
                // Pin tooltip behavior
                if (this.tooltip.isPinned && this.tooltip.pinnedOrgan === organ.id) {
                    this.tooltip.unpin();
                } else {
                    this.tooltip.show(organ.label, organ.system, "Pinned Data Mode...", e.clientX, e.clientY);
                    this.tooltip.pin();
                    this.tooltip.pinnedOrgan = organ.id;
                }
            } else {
                // Clicked outside
                this.tooltip.unpin();
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey) {
                    this.clear();
                }
            }
        });
        
        // Keyboard access
        svg.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                const node = document.activeElement;
                if (node && node.classList.contains("human-organ")) {
                    e.preventDefault();
                    this.toggle(node.id);
                }
            }
        });
        
        window.addEventListener("resize", throttle(() => {
            this.leaderLines.redraw(this.getSelected());
        }, 100));
    }
    
    getOrgan(id) {
        return this.organs.get(id);
    }
    
    getAllOrgans() {
        return Array.from(this.organs.values());
    }
    
    getSelected() {
        return this.getAllOrgans().filter(o => o.selected);
    }
    
    select(id) {
        this.clear();
        this.toggle(id, true);
    }
    
    selectMany(ids) {
        this.clear();
        ids.forEach(id => this.toggle(id, true));
    }
    
    deselect(id) {
        this.toggle(id, false);
    }
    
    toggle(id, forceState) {
        const organ = this.getOrgan(id);
        if (organ) {
            const newState = forceState !== undefined ? forceState : !organ.selected;
            if (newState) organ.select();
            else organ.deselect();
            
            this._dispatchSelectionChange();
        }
    }
    
    clear() {
        this.getAllOrgans().forEach(organ => organ.deselect());
        this._dispatchSelectionChange();
    }
    
    highlight(id) {
        const organ = this.getOrgan(id);
        if (organ) organ.highlight();
    }
    
    flash(id) {
        const organ = this.getOrgan(id);
        if (organ) organ.flash();
    }
    
    search(query) {
        query = query.toLowerCase().trim();
        if (!query) return;
        
        let found = false;
        for (const organ of this.getAllOrgans()) {
            if (!organ.isVisible()) continue;
            
            const match = organ.id.includes(query) || 
                          organ.label.toLowerCase().includes(query) || 
                          organ.aliases.some(a => a.toLowerCase().includes(query));
            
            if (match) {
                organ.flash();
                organ.node.focus();
                found = true;
                break;
            }
        }
        return found;
    }
    
    setHeatmap(data) {
        this.heatmap.apply(this, data);
        
        // Disable pointer events for organs not covered by the datasets
        this.getAllOrgans().forEach(organ => {
            if (!data[organ.id]) {
                organ.node.style.pointerEvents = "none";
            } else {
                organ.node.style.pointerEvents = "auto";
            }
        });
    }
    
    setTheme(themeName) {
        document.documentElement.setAttribute("data-theme", themeName);
    }
    
    setSex(sex) {
        this.currentSex = sex;
        this.getAllOrgans().forEach(organ => {
            if (organ.sex === "both") {
                organ.setVisible(true);
            } else {
                organ.setVisible(organ.sex === sex);
            }
            
            // if we hide a selected organ, deselect it
            if (!organ.isVisible() && organ.selected) {
                organ.deselect();
            }
        });
        
        this.leaderLines.redraw(this.getSelected());
        this._dispatchSelectionChange();
    }
    
    focus(id) {
        const organ = this.getOrgan(id);
        if (organ && organ.isVisible()) {
            organ.node.focus();
        }
    }
    
    destroy() {
        this.container.innerHTML = "";
        this.organs.clear();
        this.tooltip.element.remove();
    }
    
    _dispatchSelectionChange() {
        this.leaderLines.redraw(this.getSelected());
        if (this.onSelectionChange) {
            this.onSelectionChange(this.getSelected());
        }
    }
}
