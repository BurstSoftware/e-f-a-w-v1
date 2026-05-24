from panda3d.core import Vec3, NodePath, LPoint3f
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.task import Task
import random
import math

class WastelandGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Load environment
        self.environ = self.loader.loadModel("models/environment")
        self.environ.reparentTo(self.render)
        self.environ.setScale(0.25)
        self.environ.setPos(-8, 42, 0)

        # Player setup
        self.player = Actor("models/panda-model")
        self.player.reparentTo(self.render)
        self.player.setScale(0.005)
        self.player.setPos(0, 0, 0)
        self.player_speed = 10.0

        # Camera setup
        self.disableMouse()
        self.camera.setPos(0, -10, 5)
        self.camera.lookAt(self.player)

        # Faction system
        self.factions = {
            "Iron Reavers": {"color": (0.8, 0.2, 0.2, 1), "vox": ["Hold the line!", "Drop scrap or bleed!"], "reputation": 0},
            "Dust Vipers": {"color": (0.5, 0.5, 0.1, 1), "vox": ["Circle 'em quiet!", "Step wrong, you're meat!"], "reputation": 0}
        }

        self.pmc_squads = []
        self.bullets = []  # List to store active bullets

        # Spawn AI squads
        self.spawnPMCs()

        # Input bindings
        self.accept("mouse1", self.playerAttack)
        self.accept("w", self.movePlayer, [Vec3(0, 1, 0)])
        self.accept("s", self.movePlayer, [Vec3(0, -1, 0)])
        self.accept("a", self.movePlayer, [Vec3(-1, 0, 0)])
        self.accept("d", self.movePlayer, [Vec3(1, 0, 0)])

        # Task for AI updates
        self.taskMgr.add(self.updateGame, "UpdateGame")

    def spawnPMCs(self):
        for faction, data in self.factions.items():
            squad = {
                "faction": faction,
                "units": [],
                "position": Vec3(random.uniform(-20, 20), random.uniform(-20, 20), 0),
                "state": "neutral",
                "patrol_path": [Vec3(random.uniform(-30, 30), random.uniform(-30, 30), 0), 
                                Vec3(random.uniform(-30, 30), random.uniform(-30, 30), 0)],
                "patrol_index": 0
            }
            for i in range(3):
                pmc = Actor("models/panda-model")
                pmc.reparentTo(self.render)
                pmc.setScale(0.005)
                pmc.setColor(data["color"])
                pmc.setPos(squad["position"] + Vec3(i * 2, 0, 0))
                squad["units"].append(pmc)

            self.pmc_squads.append(squad)
            print(f"Spawned {faction} squad at {squad['position']}")

    def movePlayer(self, direction):
        self.player.setPos(self.player.getPos() + direction * self.player_speed * globalClock.getDt())

    def playerAttack(self):
        """Player fires a shot at closest enemy."""
        player_pos = self.player.getPos()
        for squad in self.pmc_squads:
            for unit in squad["units"]:
                distance = (player_pos - unit.getPos()).length()
                if distance < 10:
                    squad["state"] = "hostile"
                    self.spawnBullet(self.player.getPos(), unit.getPos())
                    print(f"Player attacked {squad['faction']}!")

    def spawnBullet(self, start_pos, target_pos):
        """Creates a simple bullet projectile moving toward the target."""
        bullet = NodePath("bullet")
        bullet.reparentTo(self.render)
        bullet.setPos(start_pos)

        bullet.velocity = (target_pos - start_pos).normalized() * 15  # Speed of bullet
        self.bullets.append(bullet)

    def updateGame(self, task):
        """Update AI movement, patrols, and bullet physics."""
        player_pos = self.player.getPos()

        # Update AI
        for squad in self.pmc_squads:
            if squad["state"] == "neutral":
                self.patrol(squad)  # AI follows patrol path
            elif squad["state"] == "hostile":
                self.attackPlayer(squad)  # AI engages in combat

        # Update bullets
        for bullet in self.bullets:
            bullet.setPos(bullet.getPos() + bullet.velocity * globalClock.getDt())

        self.camera.setPos(self.player.getX(), self.player.getY() - 10, 5)
        self.camera.lookAt(self.player)
        return Task.cont

    def patrol(self, squad):
        """AI follows a set patrol path."""
        current_target = squad["patrol_path"][squad["patrol_index"]]
        for unit in squad["units"]:
            direction = (current_target - unit.getPos()).normalized()
            unit.setPos(unit.getPos() + direction * 2 * globalClock.getDt())

        # Check if close to patrol target, then switch to next
        if (squad["units"][0].getPos() - current_target).length() < 2:
            squad["patrol_index"] = (squad["patrol_index"] + 1) % len(squad["patrol_path"])

    def attackPlayer(self, squad):
        """AI attacks player with shooting."""
        for unit in squad["units"]:
            distance = (self.player.getPos() - unit.getPos()).length()
            if distance < 15:  # If within shooting range
                if random.random() < 0.02:  # AI has a small chance to shoot each frame
                    self.spawnBullet(unit.getPos(), self.player.getPos())
                    print(f"{squad['faction']} unit fired at player!")

game = WastelandGame()
game.run()
