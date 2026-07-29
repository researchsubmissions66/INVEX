
import { HumanBody } from "./HumanBody.js";

document.addEventListener("DOMContentLoaded", async () => {
    // Setup Modal
    const modal = document.getElementById("anatomyModal");
    const openBtn = document.getElementById("openAnatomyBtn");
    const closeBtn = document.getElementById("closeAnatomyBtn");
    const datasetPanel = document.getElementById("dataset-info-panel");
    const datasetTitle = document.getElementById("dataset-info-title");
    const datasetCount = document.getElementById("dataset-info-count");
    const datasetContent = document.getElementById("dataset-info-content");

    if(!modal || !openBtn || !closeBtn) return;

    let bodyInitialized = false;
    let body = null;
    let datasetsInfo = {};

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
            
            // Fetch dataset info
            fetch("data/datasets_info.json")
                .then(res => res.json())
                .then(data => {
                    datasetsInfo = data;
                })
                .catch(err => console.error("Failed to load dataset info:", err));

            // Apply Heatmap colors and show leader lines for them
            body.setHeatmap(heatmapData);
            
            // Handle selection changes to show dataset info
            body.onSelectionChange = (selectedOrgans) => {
                if (selectedOrgans.length === 1) {
                    const organ = selectedOrgans[0];
                    const datasets = datasetsInfo[organ.id];
                    if (datasets && datasets.length > 0) {
                        datasetPanel.style.display = "flex";
                        datasetTitle.textContent = organ.label + " Datasets";
                        datasetCount.textContent = `${datasets.length} Datasets`;
                        
                        let htmlContent = "";
                        datasets.forEach(ds => {
                            htmlContent += `
                            <div class="dataset-item">
                                <h4 class="dataset-title">${ds.dataset}</h4>
                                <p class="dataset-ref"><i class="fas fa-book" style="margin-right: 0.4rem; color: #94a3b8;"></i> ${ds.reference}</p>
                            </div>`;
                        });
                        datasetContent.innerHTML = htmlContent;
                    } else {
                        datasetPanel.style.display = "flex";
                        datasetTitle.textContent = organ.label;
                        datasetCount.textContent = "0 Datasets";
                        datasetContent.innerHTML = "<p>No dataset information available for this organ.</p>";
                    }
                } else {
                    datasetPanel.style.display = "none";
                }
            };
            
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
