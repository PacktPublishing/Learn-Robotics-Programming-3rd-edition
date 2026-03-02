
# 2026-02-26 Improvements to Deployment

Deploymetns can be slow. 
I've added some vscode launchers to help, and made an rsync version of update code.

## Ideas

1. Using rsync in the deploy service script to speed up the syncs
2. Local build of page templates, and send over the build items, instead fo templating each in a loop
3. Local build of service templates, send over the rendered templates, instead of rendering on the pi
4. Use local way/quick way to detect the changed services, so starting/restarting can be done faster