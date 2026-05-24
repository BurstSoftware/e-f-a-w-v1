# Basic combat (shooting and melee attacks)
# Improved AI awareness (line-of-sight, noise detection, and stealth)
# Squad-based coordination (leaders giving orders)
# Faction reputation system
#  VOX system with dynamic responses

from panda3d.core import Vec3, NodePath, LPoint3f, CollisionRay, CollisionNode, CollisionHandlerQueue
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence, Func
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
        self.player_stealth = False  # Toggle stealth mode

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

        # Spawn AI squads
        self.spawnPMCs()

        # Input bindings
        self.accept("mouse1", self.playerAttack)
        self.accept("w", self.movePlayer, [Vec3(0, 1, 0)])
        self.accept("s", self.movePlayer, [Vec3(0, -1, 0)])
        self.accept("a", self.movePlayer, [Vec3(-1, 0, 0)])
        self.accept("d", self.movePlayer, [Vec3(1, 0, 0)])
        self.accept("shift", self.toggleStealth)

        # Task for AI updates
        self.taskMgr.add(self.updateGame, "UpdateGame")

    def spawnPMCs(self):
        for faction, data in self.factions.items():
            squad = {
                "faction": faction,
                "units": [],
                "position": Vec3(random.uniform(-20, 20), random.uniform(-20, 20), 0),
                "state": "neutral",
                "leader": None
            }
            for i in range(3):
                pmc = Actor("models/panda-model")
                pmc.reparentTo(self.render)
                pmc.setScale(0.005)
                pmc.setColor(data["color"])
                pmc.setPos(squad["position"] + Vec3(i * 2, 0, 0))
                squad["units"].append(pmc)

            squad["leader"] = squad["units"][0]  # First unit is the leader
            self.pmc_squads.append(squad)
            print(f"Spawned {faction} squad at {squad['position']}")

    def movePlayer(self, direction):
        self.player.setPos(self.player.getPos() + direction * self.player_speed * globalClock.getDt())

    def toggleStealth(self):
        self.player_stealth = not self.player_stealth
        print("Stealth mode:", "ON" if self.player_stealth else "OFF")

    def playerAttack(self):
        player_pos = self.player.getPos()
        for squad in self.pmc_squads:
            squad_pos = squad["position"]
            distance = (player_pos - squad_pos).length()
            if distance < 10:
                if squad["state"] == "neutral":
                    squad["state"] = "hostile"
                    self.triggerVox(squad, "hostile")
                    print(f"Attacked {squad['faction']} squad!")

    def updateGame(self, task):
        player_pos = self.player.getPos()
        for squad in self.pmc_squads:
            if squad["state"] == "hostile":
                for unit in squad["units"]:
                    direction = (player_pos - unit.getPos()).normalized()
                    unit.setPos(unit.getPos() + direction * 5 * globalClock.getDt())

        self.camera.setPos(self.player.getX(), self.player.getY() - 10, 5)
        self.camera.lookAt(self.player)
        return Task.cont

    def triggerVox(self, squad, context):
        vox_lines = self.factions[squad["faction"]]["vox"]
        if context == "hostile":
            line = f"{squad['faction']}: {vox_lines[0]}"
        else:
            line = f"{squad['faction']}: {vox_lines[1]}"
        print(line)

game = WastelandGame()
game.run()
