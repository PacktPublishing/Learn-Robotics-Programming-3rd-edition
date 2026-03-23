# Git default branch roadmap

I'd like to set up the default branch now.
Can we start by taking the defualt branch and bringing the poetry/pyproject files, root dotfiles (lint configs etc) inventory, README into it from the branch chapter-17/complete.
Then create a chapter-6/complete folder. In this, copy the deploy, robot and robot_control folders from the branch chapter-6/complete.

The overall goal (and we can make a git_roadmap.md to jhelp with context) is that every chapter will have a:
- chapter-n/complete folder
- containing the robot, robot_control, deploy, experiments folders from the appropriate branch copied in. Make commits after each branch so we can figure out any problems.
- Code diagrams can simply go into the root code_diagrams folder.
- Any .vscode settings go into the root.

We will then need to visit chapter stages, and make subfolders.

Local tools - in one of the latest chapter -17 branches I think there's a local_tools folder. We can move that to the root, and copy the relevant files in.
- Simulations
- Smoke tests that are intended to run locally on the pc and not the robot

We can verify each commit and the state of things.
- We MUST not change the code for any speicfic chapter, but we can move it around and make sure it is in the right place
- We MUST review common code that changes and consider if we mean that, or what implications are.
- We MUST make commits after each chapter subfolder (a chapter-n/complete or chapter-n/stage) is done, so we can easily review the history and changes.
- We MUST ensure any local branches not push are pushed to the remote before we start, so we have a clean slate to work with.
- We MUST use all REMOTE branches
- We MUST ignore branches marked with expo, old, archive, bokeh, https, experiments, jinja for now. We will come back to them.
- Summarise chapters incorporated in a roadmap complete table at the bottom of this document.

## Issues


### Chapter-10/expo

Hmm - so there's an issue here - one branch (Chapter-10/original) was an expo branch.
It should be chapter-10/expo I think. I've renamed the folder, but we need to recreate an expo branch, and put it on the remote, removing this version.
