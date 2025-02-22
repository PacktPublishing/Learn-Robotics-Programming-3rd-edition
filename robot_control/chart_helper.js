import 'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js';



function prepare_datasets(initial_data) {
    // Create a set of datasets from initial_data
    // Example should be {"field_a": 0, "field_b": 1, "time": time_code}
    const field_names = Object.keys(initial_data[0]).filter((key) => key !== "time");
    return {
        datasets: field_names.map((key) => {
            return {
                label: key,
                data: initial_data,
                parsing: {
                    xAxisKey: "time",
                    yAxisKey: key,
                }
            }
        })
    };
}

const options_for_timeseries = {
    scales: {
        x: { type: 'time' }
    },
    adaptors: {
        type: 'time',
    },
    responsive: true,
};

export function create_timeseries_chart(element_name, chart_data) {
    // Create a timeseries chart from an example
    const ctx = document.getElementById(element_name);
    const chart=new Chart(ctx, {
        type: 'line',
        data: prepare_datasets(chart_data),
        options: options_for_timeseries
    });

    return {
        update_data: (data_item) => {
            data_item.time = data_item.time * 1000;
            chart_data.push(data_item);
            chart.update();
        }
    }
}
