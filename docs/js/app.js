
import { HumanBody } from "./HumanBody.js";

document.addEventListener("DOMContentLoaded", async () => {
    // Setup Modal
    const modal = document.getElementById("anatomyModal");
    const openBtn = document.getElementById("openAnatomyBtn");
    const closeBtn = document.getElementById("closeAnatomyBtn");

    if(!modal || !openBtn || !closeBtn) return;

    let bodyInitialized = false;
    let body = null;

    openBtn.addEventListener("click", async () => {
        modal.classList.add("show");
        
        if(!bodyInitialized) {
            body = new HumanBody("#human-body-wrapper");
            await body.init();
            body.setSex("male"); // use generic male
            
            // Set different colors for showcased organs
            const heatmapData = {
                "lung": { color: "#38bdf8" },        // Light blue
                "breast": { color: "#f472b6" },      // Pink
                "colon": { color: "#a78bfa" },       // Purple
                "rectum": { color: "#a78bfa" },
                "small_intestine": { color: "#a78bfa" },
                "kidney": { color: "#fb923c" },      // Orange
                "lymph_node": { color: "#facc15" },  // Yellow
                "prostate": { color: "#2dd4bf" },    // Teal
                "stomach": { color: "#a3e635" }      // Lime Green
            };
            
            // Apply Heatmap colors and show leader lines for them
            body.setHeatmap(heatmapData);
            
            // Force select them so they get leader lines (leader lines only show for selected by default)
            Object.keys(heatmapData).forEach(id => {
                if(body.getOrgan(id)) body.toggle(id, true);
            });
            
            bodyInitialized = true;
        }
    });

    closeBtn.addEventListener("click", () => {
        modal.classList.remove("show");
    });
    
    // Close when clicking outside
    modal.addEventListener("click", (e) => {
        if(e.target === modal) {
            modal.classList.remove("show");
        }
    });
});
