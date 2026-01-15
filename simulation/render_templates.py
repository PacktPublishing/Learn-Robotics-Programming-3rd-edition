"""Render Jinja2 templates in robot_control directory."""
import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_templates():
    """Render all .j2 template files in robot_control directory."""
    robot_control_dir = Path("/app/robot_control")

    # Load environment config
    env_json_path = robot_control_dir / ".env.json"
    if env_json_path.exists():
        with open(env_json_path) as f:
            env_config = json.load(f)
    else:
        # Default configuration for simulation
        # Browser needs localhost (not mqtt) since WebSocket connects from host
        env_config = {
            "PI_HOSTNAME": "localhost",
            "MQTT_USERNAME": "robot",
            "MQTT_PASSWORD": "robot"
        }

    # Create Jinja2 environment with /app as root so "robot_control/page.html.j2" resolves
    env = Environment(
        loader=FileSystemLoader("/app"),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Render all .j2 templates
    for template_file in robot_control_dir.glob("*.j2"):
        template_name = "robot_control/" + template_file.name
        output_name = template_file.name.replace(".j2", "")
        output_path = robot_control_dir / output_name

        print(f"Rendering {template_file.name} -> {output_name}")

        template = env.get_template(template_name)
        rendered = template.render(**env_config)

        with open(output_path, 'w') as f:
            f.write(rendered)

    # Also render HTML files that extend templates
    for html_file in robot_control_dir.glob("*.html"):
        # Check if file contains Jinja2 syntax
        with open(html_file) as f:
            content = f.read()

        if '{%' in content or '{{' in content:
            print(f"Rendering template {html_file.name}")
            template = env.get_template("robot_control/" + html_file.name)
            rendered = template.render(**env_config)

            with open(html_file, 'w') as f:
                f.write(rendered)

    # Generate .env.js for browser-side configuration
    env_js_path = robot_control_dir / ".env.js"
    with open(env_js_path, 'w') as f:
        f.write(f"""const env = {{
    PI_HOSTNAME: "{env_config['PI_HOSTNAME']}",
    MQTT_USERNAME: "{env_config['MQTT_USERNAME']}",
    MQTT_PASSWORD: "{env_config['MQTT_PASSWORD']}"
}};
""")
    print(f"Generated .env.js with PI_HOSTNAME={env_config['PI_HOSTNAME']}")


if __name__ == "__main__":
    render_templates()
    print("Template rendering complete")
