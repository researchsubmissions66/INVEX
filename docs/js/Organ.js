
export class Organ {
    constructor(node, data) {
        this.node = node;
        this.id = data.id;
        this.label = data.label;
        this.aliases = data.aliases || [];
        this.system = data.system || "Unknown";
        this.sex = data.sex || "both";
        this.selected = false;
        
        // Add a11y
        this.node.setAttribute("role", "button");
        this.node.setAttribute("aria-label", this.label);
        this.node.setAttribute("tabindex", "0");
    }

    select() {
        this.selected = true;
        this.node.classList.add("selected");
        this.node.setAttribute("aria-pressed", "true");
    }

    deselect() {
        this.selected = false;
        this.node.classList.remove("selected");
        this.node.setAttribute("aria-pressed", "false");
    }

    highlight() {
        this.node.classList.add("highlight");
    }
    
    unhighlight() {
        this.node.classList.remove("highlight");
    }
    
    flash() {
        this.node.classList.add("flashing");
        setTimeout(() => this.node.classList.remove("flashing"), 600);
    }
    
    setVisible(isVisible) {
        this.node.style.display = isVisible ? "" : "none";
    }
    
    isVisible() {
        return this.node.style.display !== "none";
    }
}
