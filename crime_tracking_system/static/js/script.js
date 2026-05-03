function buildChart(canvasId, labels, values, type = "bar") {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    new Chart(canvas, {
        type: type,
        data: {
            labels: labels,
            datasets: [
                {
                    label: canvasId,
                    data: values,
                    backgroundColor: [
                        "#0b1f3a",
                        "#dc3545",
                        "#198754",
                        "#0d6efd",
                        "#ffc107",
                        "#6f42c1",
                        "#20c997",
                    ],
                },
            ],
        },
        options: { responsive: true, maintainAspectRatio: false },
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const chartTag = document.getElementById("chartDataJson");
    if (!chartTag) return;

    const data = JSON.parse(chartTag.textContent);
    buildChart(
        "caseStatusChart",
        data.case_status.map((x) => x.label),
        data.case_status.map((x) => x.value),
        "pie"
    );
    buildChart(
        "severityChart",
        data.severity.map((x) => x.label),
        data.severity.map((x) => x.value),
        "doughnut"
    );
    buildChart(
        "stationChart",
        data.station_workload.map((x) => x.label),
        data.station_workload.map((x) => x.value),
        "bar"
    );
    buildChart(
        "officerChart",
        data.officer_assignments.map((x) => x.label),
        data.officer_assignments.map((x) => x.value),
        "bar"
    );
    buildChart(
        "monthlyChart",
        data.monthly_trends.map((x) => x.label),
        data.monthly_trends.map((x) => x.value),
        "line"
    );
});
