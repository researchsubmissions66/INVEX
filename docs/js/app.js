
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
                            htmlContent += `<div style="margin-bottom: 2rem;">`;
                            if (window.marked) {
                                htmlContent += marked.parse(ds.note);
                            } else {
                                htmlContent += `<pre style="white-space: pre-wrap; font-family: inherit;">${ds.note}</pre>`;
                            }
                            htmlContent += `</div>`;
                        });
                        
                        // Style markdown elements (tables, etc.) inside the container
                        htmlContent = htmlContent.replace(/<table>/g, '<table style="width: 100%; border-collapse: collapse; margin-bottom: 1rem;">');
                        htmlContent = htmlContent.replace(/<th>/g, '<th style="border-bottom: 2px solid #cbd5e1; padding: 0.5rem; text-align: left;">');
                        htmlContent = htmlContent.replace(/<td>/g, '<td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">');
                        htmlContent = htmlContent.replace(/<h1>|<h2>|<h3>|<h4>/g, match => {
                            return match.substring(0, match.length - 1) + ' style="margin-top: 1rem; margin-bottom: 0.5rem; color: #0f172a;">';
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
