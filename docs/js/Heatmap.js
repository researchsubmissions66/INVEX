
export class Heatmap {
    constructor() {}

    /**
     * Set heatmap data
     * data format: { "liver": { value: 0.9, color: "#d73027" }, "brain": { value: 0.2 } }
     */
    apply(body, data, type = "sequential") {
        this.clear(body);
        
        let min = Infinity;
        let max = -Infinity;
        
        // Find min/max if we need to auto-color
        for (const key in data) {
            if (data[key].value !== undefined) {
                if (data[key].value < min) min = data[key].value;
                if (data[key].value > max) max = data[key].value;
            }
        }
        
        for (const organId in data) {
            const organ = body.getOrgan(organId);
            if (!organ) continue;
            
            const info = data[organId];
            if (info.color) {
                organ.node.style.fill = info.color;
            } else if (info.value !== undefined) {
                // simple interpolation from light to dark blue if sequential
                const ratio = (info.value - min) / (max - min || 1);
                organ.node.style.fill = this.interpolateColor("#bae6fd", "#0284c7", ratio);
            }
        }
    }
    
    clear(body) {
        body.getAllOrgans().forEach(organ => {
            organ.node.style.fill = ""; // fallback to CSS
        });
    }

    interpolateColor(color1, color2, factor) {
        if (arguments.length < 3) { 
            factor = 0.5; 
        }
        var result = color1.slice(1).match(/.{2}/g).map((c, i) => {
            return Math.round(
                parseInt(c, 16) + factor * (parseInt(color2.slice(1).match(/.{2}/g)[i], 16) - parseInt(c, 16))
            );
        });
        return "#" + result.map(c => c.toString(16).padStart(2, "0")).join("");
    }
}
