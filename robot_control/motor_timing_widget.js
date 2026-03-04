import 'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js';

const DEFAULT_TOPIC = 'motors/wheels/timing';

function build_chart_data() {
    const data = [{
        time: Date.now(),
        avg_gap_us: 0,
        max_gap_us: 0,
        avg_total_us: 0,
        max_total_us: 0,
    }];

    return {
        datasets: [
            {
                label: 'avg_gap_us',
                data,
                parsing: { xAxisKey: 'time', yAxisKey: 'avg_gap_us' },
            },
            {
                label: 'max_gap_us',
                data,
                parsing: { xAxisKey: 'time', yAxisKey: 'max_gap_us' },
            },
            {
                label: 'avg_total_us',
                data,
                parsing: { xAxisKey: 'time', yAxisKey: 'avg_total_us' },
            },
            {
                label: 'max_total_us',
                data,
                parsing: { xAxisKey: 'time', yAxisKey: 'max_total_us' },
            },
        ]
    };
}

export class MotorTimingWidget {
    constructor(element_id, options = {}) {
        this.topic = options.topic ?? DEFAULT_TOPIC;
        this.max_points = options.max_points ?? 300;
        this.stats_element_id = options.stats_element_id ?? null;
        this.chart_data = build_chart_data();
        this.first_item = true;

        const ctx = document.getElementById(element_id);
        this.chart = new Chart(ctx, {
            type: 'line',
            data: this.chart_data,
            options: {
                responsive: true,
                animation: false,
                scales: {
                    x: { type: 'time' }
                },
            },
        });
    }

    render_stats(data) {
        if (!this.stats_element_id) {
            return;
        }

        const stats_element = document.getElementById(this.stats_element_id);
        if (!stats_element) {
            return;
        }

        stats_element.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <th>Samples</th>
                        <td><samp>${data.samples ?? 0}</samp></td>
                    </tr>
                    <tr>
                        <th>Avg gap (μs)</th>
                        <td><samp>${(data.avg_gap_us ?? 0).toFixed(2)}</samp></td>
                    </tr>
                    <tr>
                        <th>Max gap (μs)</th>
                        <td><samp>${(data.max_gap_us ?? 0).toFixed(2)}</samp></td>
                    </tr>
                    <tr>
                        <th>Avg total (μs)</th>
                        <td><samp>${(data.avg_total_us ?? 0).toFixed(2)}</samp></td>
                    </tr>
                    <tr>
                        <th>Max total (μs)</th>
                        <td><samp>${(data.max_total_us ?? 0).toFixed(2)}</samp></td>
                    </tr>
                </tbody>
            </table>
        `;
    }

    handle_mqtt_data(data) {
        const data_item = {
            ...data,
            time: (data.timestamp ?? (Date.now() / 1000)) * 1000,
        };

        if (this.first_item) {
            this.chart_data.datasets[0].data[0] = data_item;
            this.first_item = false;
        } else {
            this.chart_data.datasets[0].data.push(data_item);
        }

        const points = this.chart_data.datasets[0].data;
        if (points.length > this.max_points) {
            points.splice(0, points.length - this.max_points);
        }

        this.chart.update();
        this.render_stats(data_item);
    }

    handle_mqtt_message(topic, message) {
        if (topic !== this.topic) {
            return;
        }

        const payload = JSON.parse(message);
        this.handle_mqtt_data(payload);
    }
}

export function create_motor_timing_widget(element_id, options = {}) {
    return new MotorTimingWidget(element_id, options);
}
