export function setup_keyboard_drive({
    mqtt_client,
    publish_interval_ms = 75,
    throttle_scale = 0.7,
    turn_scale = 0.45,
}) {
    const kd = window.kd;

    function update() {
        const throttle = (kd.W.isDown() ? 1 : 0) - (kd.S.isDown() ? 1 : 0);
        const turn = (kd.D.isDown() ? 1 : 0) - (kd.A.isDown() ? 1 : 0);

        const left_motor = Math.max(-1, Math.min(1, throttle * throttle_scale + turn * turn_scale));
        const right_motor = Math.max(-1, Math.min(1, throttle * throttle_scale - turn * turn_scale));
        mqtt_client.publish('motors/wheels', JSON.stringify([left_motor, right_motor]));
    }

    setInterval(update, publish_interval_ms);
}
