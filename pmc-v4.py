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
        self.bullets = []
        self.cover_points = [Vec3(-10, 10, 0), Vec3(5, -5, 0), Vec3(15, 20, 0)]  # Predefined cover locations

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
                "reinforcement_called": False
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
                    self.callReinforcements(squad)
                    print(f"Player attacked {squad['faction']}!")

    def callReinforcements(self, attacked_squad):
        """Alert nearby squads if an attack occurs."""
        if attacked_squad["reinforcement_called"]:
            return  # Only call reinforcements once

        for squad in self.pmc_squads:
            if squad != attacked_squad and squad["state"] == "neutral":
                distance = (squad["position"] - attacked_squad["position"]).length()
                if distance < 30:  # Reinforcements within 30 meters
                    squad["state"] = "hostile"
                    print(f"{squad['faction']} received a distress call and is moving in!")
        
        attacked_squad["reinforcement_called"] = True

    def spawnBullet(self, start_pos, target_pos):
        """Creates a simple bullet projectile moving toward the target."""
        bullet = NodePath("bullet")
        bullet.reparentTo(self.render)
        bullet.setPos(start_pos)
        bullet.velocity = (target_pos - start_pos).normalized() * 15
        self.bullets.append(bullet)

    def updateGame(self, task):
        """Update AI movement, patrols, and bullet physics."""
        player_pos = self.player.getPos()

        # Update AI
        for squad in self.pmc_squads:
            if squad["state"] == "hostile":
                self.attackPlayer(squad)
                self.findCover(squad)

        # Update bullets
        for bullet in self.bullets:
            bullet.setPos(bullet.getPos() + bullet.velocity * globalClock.getDt())

        self.camera.setPos(self.player.getX(), self.player.getY() - 10, 5)
        self.camera.lookAt(self.player)
        return Task.cont

    def findCover(self, squad):
        """If under fire, AI moves to nearest cover point."""
        for unit in squad["units"]:
            closest_cover = min(self.cover_points, key=lambda cover: (unit.getPos() - cover).length())
            if (unit.getPos() - closest_cover).length() > 2:
                direction = (closest_cover - unit.getPos()).normalized()
                unit.setPos(unit.getPos() + direction * 3 * globalClock.getDt())

    def attackPlayer(self, squad):
        """AI attacks player with shooting and flanking."""
        for unit in squad["units"]:
            distance = (self.player.getPos() - unit.getPos()).length()
            if distance < 15:
                if random.random() < 0.02:
                    self.spawnBullet(unit.getPos(), self.player.getPos())
                    print(f"{squad['faction']} unit fired at player!")
            elif distance > 10:
                # If not in range, flank instead of charging straight
                flank_offset = Vec3(random.choice([-5, 5]), random.choice([-5, 5]), 0)
                flank_pos = self.player.getPos() + flank_offset
                direction = (flank_pos - unit.getPos()).normalized()
                unit.setPos(unit.getPos() + direction * 2 * globalClock.getDt())

game = WastelandGame()
game.run()
