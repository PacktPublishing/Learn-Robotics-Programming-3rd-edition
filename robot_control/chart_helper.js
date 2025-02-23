import 'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js';

const options_for_timeseries = {
    scales: {
        x: { type: 'time' }
    },
    adaptors: {
        type: 'time',
    },
    responsive: true,
};

function prepare_datasets(columns) {
    const data = []
    data.push(
        Object.fromEntries(columns.map(label => [label, 0]))
    );
    data[0].time = new Date().getTime();
    return {
        datasets: columns.map((label) => {
            return {
                label: label,
                data: data,
                parsing: {
                    xAxisKey: "time",
                    yAxisKey: label,
                }
            };
        })
    };
}

export function create_timeseries_chart(element_name, columns) {
    const chart_data = prepare_datasets(columns);
    const ctx = document.getElementById(element_name);
    const chart=new Chart(ctx, {
        type: 'line',
        data: chart_data,
        options: options_for_timeseries
    });

    return {
        update_data: (data_item) => {
            data_item.time = data_item.time * 1000;
            chart_data.datasets[0].data.push(data_item);
            chart.update();
        }
    }
}
