# Ideas for simulation

## Web based ui

I'm wondering about this UI - is pygame the best strategy in this context, could a python service + a javascript front end suit better?
IE - let something like raygun do the front end, and the backend just sends data to the front end via websockets or something?

It would be more work to set up, but it would be more flexible and easier to extend in the future. Pygame is great for quick prototyping, but it can be a bit clunky for more complex UIs. A web-based UI would also allow us to easily add features like logging, data visualization, and remote control.

The display panels could then be CSS and normal HTML parts, while the main render could be a canvas or WebGL element. This would allow us to have a more modern and responsive UI, and we could also leverage existing libraries for things like charts and graphs.

The pymunk physics engine could still be used for the simulation, and we could use something like Flask or FastAPI to serve the backend API. The frontend could then use something like Socket.IO to receive real-time updates from the backend.

Given that we are rendering telemetry data, this could still use the MQTT approach the rest of the book does, but with a /simulation/telemetry topic. For messgaes we already would be sending (like distance sensor data), we could just have the front end subscribe to those topics directly, and the backend could handle any additional processing or aggregation of data as needed to preprocess for the simulation topic.

For the Javascriptr front-end, maybe time to do that properly - a package.json with dependencies, and a build step using Vite. This would allow us to use modern JavaScript features and libraries, and also make it easier to manage our dependencies. We can have a frontend directory in the simulation folder.
