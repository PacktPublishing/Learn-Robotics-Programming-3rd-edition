    function convert_data(raw_data) {
        const clipped_data = raw_data.map(d => Math.min(d, 1000));
        const normalised_data = clipped_data.map(d => d / 1000);
        return normalised_data.map(
            (data, index) => (
                {
                    x: 8 - (index % 8 + 0.5),
                    y: Math.floor(index / 8) + 0.5,
                    distance: data
                }
            )
        );
    }

function prepare_dataset() {
    const empty = Array(64);
    empty.fill(0, 0, 64);

    return {
        datasets: [
            {
                label: 'Distance',
                data: convert_data(empty),
                backgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex].distance;
                    const intensity = value * 255;
                    return `rgba(${intensity}, ${intensity}, ${intensity}, 100)`;
                },
            }
        ]
    };
}

export function make_distance_chart() {
    const element = document.getElementById('distance_chart');

    const data = prepare_dataset();

    const options = {
        pointStyle: 'rect',
        radius: 25,
    };

    const chart = new Chart(element, {
        type: 'scatter',
        data: data,
        options: options
    });

    return {
        update_data: function(raw_data) {
            data.datasets[0].data = convert_data(raw_data);
            chart.update();
        }
    }
}
