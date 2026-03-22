from trajectory_behavior_base import TrajectoryBehaviorBase


class StraightStopTrajectoryService(TrajectoryBehaviorBase):
    trajectory_tag = "straight_stop"

    def run_trajectory(self, client):
        self.speed = 140
        self.drive_line(client, 500)
        self.pause()
        self.drive_line(client, 500)
        self.pause()


service = StraightStopTrajectoryService()
service.start()
