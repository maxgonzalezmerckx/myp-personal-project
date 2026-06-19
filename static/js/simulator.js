/**
 * Volleyball serve trajectory simulator — frontend logic.
 * Sends parameters to /api/simulate and renders the result with Plotly.
 */

(function () {
  "use strict";

  const NET_DISTANCE = 9.0;
  const COURT_DEPTH = 9.0;
  const NET_HEIGHTS = { men: 2.43, women: 2.24 };

  const speedInput = document.getElementById("speed");
  const angleInput = document.getElementById("angle");
  const spinInput = document.getElementById("spin");
  const heightInput = document.getElementById("height");
  const netTypeSelect = document.getElementById("net-type");
  const includeDragCheck = document.getElementById("include-drag");
  const includeMagnusCheck = document.getElementById("include-magnus");
  const simulateBtn = document.getElementById("simulate-btn");
  const chartEl = document.getElementById("trajectory-chart");
  const statsPanel = document.getElementById("stats-panel");

  if (!speedInput) return;

  function updateLabels() {
    document.getElementById("speed-val").textContent = `${speedInput.value} m/s`;
    document.getElementById("angle-val").textContent = `${angleInput.value}°`;
    const spin = parseFloat(spinInput.value);
    const spinLabel = spin > 0 ? "topspin" : spin < 0 ? "backspin" : "none";
    document.getElementById("spin-val").textContent = `${spin} rpm (${spinLabel})`;
    document.getElementById("height-val").textContent = `${heightInput.value} m`;
  }

  function getParams() {
    return {
      speed: parseFloat(speedInput.value),
      angle_deg: parseFloat(angleInput.value),
      spin_rpm: parseFloat(spinInput.value),
      height: parseFloat(heightInput.value),
      net_type: netTypeSelect.value,
      include_drag: includeDragCheck.checked,
      include_magnus: includeMagnusCheck.checked,
    };
  }

  function buildCourtShapes(netType) {
    const netHeight = NET_HEIGHTS[netType] || NET_HEIGHTS.men;
    const courtEnd = NET_DISTANCE + COURT_DEPTH;

    return [
      // Ground line
      {
        type: "line",
        x0: 0,
        x1: courtEnd + 1,
        y0: 0,
        y1: 0,
        line: { color: "#94a3b8", width: 2 },
      },
      // Net post left
      {
        type: "line",
        x0: NET_DISTANCE,
        x1: NET_DISTANCE,
        y0: 0,
        y1: netHeight,
        line: { color: "#dc2626", width: 3 },
      },
      // Net tape
      {
        type: "line",
        x0: NET_DISTANCE - 0.3,
        x1: NET_DISTANCE + 0.3,
        y0: netHeight,
        y1: netHeight,
        line: { color: "#dc2626", width: 4 },
      },
      // Serve line
      {
        type: "line",
        x0: 0,
        x1: 0,
        y0: 0,
        y1: 4.5,
        line: { color: "#64748b", width: 1, dash: "dot" },
      },
      // End line
      {
        type: "line",
        x0: courtEnd,
        x1: courtEnd,
        y0: 0,
        y1: 4.5,
        line: { color: "#64748b", width: 1, dash: "dot" },
      },
      // Opponent court shading
      {
        type: "rect",
        x0: NET_DISTANCE,
        x1: courtEnd,
        y0: 0,
        y1: 4.5,
        fillcolor: "rgba(26, 107, 74, 0.06)",
        line: { width: 0 },
      },
    ];
  }

  function renderChart(data, netType) {
    const { x, y } = data;

    const trace = {
      x,
      y,
      mode: "lines",
      name: "Trajectory",
      line: { color: "#e85d04", width: 3 },
      hovertemplate: "x: %{x:.2f} m<br>y: %{y:.2f} m<extra></extra>",
    };

    const netHeight = NET_HEIGHTS[netType] || NET_HEIGHTS.men;

    const layout = {
      title: { text: "Serve Trajectory (side view)", font: { size: 16 } },
      xaxis: {
        title: "Horizontal distance (m)",
        range: [0, NET_DISTANCE + COURT_DEPTH + 1],
        zeroline: false,
      },
      yaxis: {
        title: "Height (m)",
        range: [0, Math.max(5, ...y) + 0.5],
        zeroline: false,
      },
      shapes: buildCourtShapes(netType),
      annotations: [
        {
          x: NET_DISTANCE,
          y: netHeight + 0.15,
          text: "Net",
          showarrow: false,
          font: { size: 11, color: "#dc2626" },
        },
      ],
      margin: { t: 50, r: 20, b: 50, l: 55 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      showlegend: false,
    };

    Plotly.react(chartEl, [trace], layout, { responsive: true, displayModeBar: false });
  }

  function renderStats(stats) {
    const items = [
      { label: "Range", value: `${stats.range_m} m` },
      { label: "Max height", value: `${stats.max_height_m} m` },
      { label: "Flight time", value: `${stats.flight_time_s} s` },
      {
        label: "Height at net",
        value: stats.net_height_at_net_m != null ? `${stats.net_height_at_net_m} m` : "N/A",
      },
      {
        label: "Clears net",
        value: stats.clears_net ? "Yes" : "No",
        className: stats.clears_net ? "success" : "danger",
      },
      {
        label: "In bounds",
        value: stats.lands_in_bounds ? "Yes" : "No",
        className: stats.lands_in_bounds ? "success" : "danger",
      },
    ];

    statsPanel.innerHTML = items
      .map(
        (item) => `
      <div class="stat-item ${item.className || ""}">
        <span class="stat-label">${item.label}</span>
        <span class="stat-value">${item.value}</span>
      </div>`
      )
      .join("");
  }

  async function runSimulation() {
    simulateBtn.disabled = true;
    simulateBtn.textContent = "Computing…";

    try {
      const response = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(getParams()),
      });

      const data = await response.json();

      if (!response.ok) {
        statsPanel.innerHTML = `<p class="stats-placeholder">${data.error || "Simulation failed."}</p>`;
        return;
      }

      renderChart(data, netTypeSelect.value);
      renderStats(data.stats);
    } catch (err) {
      statsPanel.innerHTML = `<p class="stats-placeholder">Network error: ${err.message}</p>`;
    } finally {
      simulateBtn.disabled = false;
      simulateBtn.textContent = "Simulate";
    }
  }

  // Event listeners
  [speedInput, angleInput, spinInput, heightInput].forEach((el) => {
    el.addEventListener("input", updateLabels);
  });

  simulateBtn.addEventListener("click", runSimulation);

  // Auto-simulate on slider change (debounced)
  let debounceTimer;
  function scheduleSimulate() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runSimulation, 300);
  }

  [speedInput, angleInput, spinInput, heightInput, netTypeSelect, includeDragCheck, includeMagnusCheck].forEach(
    (el) => {
      el.addEventListener("change", scheduleSimulate);
      if (el.type === "range") {
        el.addEventListener("input", scheduleSimulate);
      }
    }
  );

  updateLabels();
  runSimulation();
})();
