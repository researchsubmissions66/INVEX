
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
            
            const btnContainer = document.getElementById("organ-buttons-container");
            if(btnContainer) {
                btnContainer.innerHTML = "";
                Object.keys(heatmapData).forEach(id => {
                    const btn = document.createElement("button");
                    btn.className = "btn btn-secondary";
                    btn.style.textAlign = "left";
                    btn.style.padding = "0.6rem 1rem";
                    btn.style.fontSize = "0.9rem";
                    btn.style.display = "flex";
                    btn.style.alignItems = "center";
                    btn.style.justifyContent = "space-between";
                    btn.style.border = "1px solid var(--border)";
                    btn.style.background = "#fff";
                    btn.style.cursor = "pointer";
                    
                    const label = id.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
                    
                    const colorSwatch = document.createElement("span");
                    colorSwatch.style.width = "12px";
                    colorSwatch.style.height = "12px";
                    colorSwatch.style.borderRadius = "50%";
                    colorSwatch.style.backgroundColor = heatmapData[id].color;
                    
                    const textSpan = document.createElement("span");
                    textSpan.textContent = label;
                    
                    btn.appendChild(textSpan);
                    btn.appendChild(colorSwatch);
                    
                    btn.addEventListener("click", () => {
                        // Unselect all
                        Object.keys(heatmapData).forEach(otherId => {
                            if(body.getOrgan(otherId)) body.toggle(otherId, false);
                        });
                        // Select this one
                        if(body.getOrgan(id)) body.toggle(id, true);
                    });
                    
                    btnContainer.appendChild(btn);
                });
            }
            
            // Force select them so they get leader lines (leader lines only show for selected by default)
            Object.keys(heatmapData).forEach(id => {
                if(body.getOrgan(id)) body.toggle(id, true);
            });
            
            const showAllBtn = document.getElementById("showAllOrgansBtn");
            if(showAllBtn) {
                showAllBtn.addEventListener("click", () => {
                    Object.keys(heatmapData).forEach(id => {
                        if(body.getOrgan(id)) body.toggle(id, true);
                    });
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
