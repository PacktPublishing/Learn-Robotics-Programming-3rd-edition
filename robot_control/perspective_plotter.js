export const PerspectivePlotter = {
    perspectiveScale(z) {
        return 1 / 1.1 ** z;
    },
    project3D(x, y, z, scales) {
        const scale = this.perspectiveScale(z);

        return {
            x: scales.x.getPixelForValue(x * scale),
            y: scales.y.getPixelForValue(y * scale ),
        };
    },
    drawLine(ctx, scales, start, end, color) {
        const startProjected = this.project3D(start.x, start.y, start.z, scales);
        const endProjected = this.project3D(end.x, end.y, end.z, scales);

        ctx.beginPath();
        ctx.moveTo(startProjected.x, startProjected.y);
        ctx.lineTo(endProjected.x, endProjected.y);
        ctx.closePath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
    },
    filledCircle(ctx, scales, center, radius, color) {
        const { x, y } = this.project3D(center.x, center.y, center.z, scales);
        // Radius not projected

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.closePath();
    },
};

