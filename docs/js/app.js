
import { HumanBody } from "./HumanBody.js";

document.addEventListener("DOMContentLoaded", async () => {
    // Setup Modal
    const modal = document.getElementById("anatomyModal");
    const openBtn = document.getElementById("openAnatomyBtn");
    const closeBtn = document.getElementById("closeAnatomyBtn");
    const legendContainer = document.getElementById("anatomy-legend");

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
                "breast": { color: "#ec4899" },           // Pink
                "prostate": { color: "#14b8a6" },         // Teal
                "colon": { color: "#7e22ce" },            // Dark Purple
                "rectum": { color: "#ef4444" },           // Red
                "small_intestine": { color: "#3b82f6" },  // Blue
                "lung": { color: "#0ea5e9" },             // Sky Blue
                "lymph_node": { color: "#eab308" },       // Yellow
                "kidney": { color: "#f97316" },           // Orange
                "stomach": { color: "#22c55e" }           // Green
            };
            
            // Apply Heatmap colors and show leader lines for them
            body.setHeatmap(heatmapData);
            
            // Add Legend
            if (legendContainer) {
                legendContainer.innerHTML = "";
                Object.keys(heatmapData).forEach(organId => {
                    const info = heatmapData[organId];
                    const organName = organId.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase());
                    
                    const item = document.createElement("div");
                    item.style.display = "flex";
                    item.style.alignItems = "center";
                    item.style.gap = "0.5rem";
                    item.style.fontSize = "0.9rem";
                    item.style.color = "#475569";
                    item.style.cursor = "pointer";
                    item.style.transition = "transform 0.1s";
                    
                    item.addEventListener("mouseenter", () => {
                        item.style.transform = "scale(1.05)";
                        body.highlight(organId);
                    });
                    item.addEventListener("mouseleave", () => {
                        item.style.transform = "scale(1)";
                        body.getOrgan(organId)?.unhighlight();
                    });
                    item.addEventListener("click", () => {
                        body.select(organId);
                        body.flash(organId);
                    });
                    
                    const colorBox = document.createElement("div");
                    colorBox.style.width = "16px";
                    colorBox.style.height = "16px";
                    colorBox.style.borderRadius = "4px";
                    colorBox.style.backgroundColor = info.color;
                    
                    const label = document.createElement("span");
                    label.textContent = organName;
                    
                    item.appendChild(colorBox);
                    item.appendChild(label);
                    legendContainer.appendChild(item);
                });
            }
            
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
