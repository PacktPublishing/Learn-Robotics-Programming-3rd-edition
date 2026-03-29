# Learn-Robotics-Programming-3rd-edition
Learn Robotics Programming, 3rd edition, Published by Packt

## Code organisation

The code in this repository is laid out mostly chapter by chapter.

- Chapter N
    - stage 1 - intermediate stage, earlier section of the chapter
    - stage 2 - later section of the chapter, building on stage 1
    - complete - the complete code for the chapter, with all stages integrated

Under each stage there's generally the following structure:

- Chapter N/stage M
    - deploy - PyInfra code to depoy examples, configuration, and code to the robot
    - experiments - Experimental code, jupyter notebooks, etc.
    - robot - code that will run on the robot - python
        - common - common modules between different robot modules
    - robot_control - web app for controlling and interacting with the robot. Served on the robot.

At the top level:

- code_diagrams
    - chapter-N - jupyter notebooks used to generate code diagrams for chapter N
- local_tools - a collection of tools for local testing and development
- inventory.py - the PyInfra inventory file
- dotfiles, pyproject files - configuration for development environment, linters, formatters, etc.
