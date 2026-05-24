from panda3d.core import Vec3, NodePath, LPoint3f
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence, Func
import random
import math

# Game class inheriting from ShowBase (Panda3D's base class)
class WastelandGame(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        # Load a simple environment (flat terrain for now)
        self.environ = self.loader.loadModel("models/environment")
        self.environ.reparentTo(self.render)
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(-8, 42, 0)

        # Player setup (simple capsule for now)
        self.player = Actor("models/panda-model")
        self.player.reparentTo(self.render)
        self.player.setScale(0.005)
        self.player.setPos(0, 0, 0)
        self.player_speed = 10.0

        # Camera setup (third-person view)
        self.disableMouse()
        self.camera.setPos(0, -10, 5)
        self.camera.lookAt(self.player)

        # PMC faction data
        self.factions = {
            "Iron Reavers": {
                "color": (0.8, 0.2, 0.2, 1),
                "vox": [
                    "Hold the line!",
                    "Drop scrap or bleed!"
                ]
            },
            "Dust Vipers": {
                "color": (0.5, 0.5, 0.1, 1),
                "vox": [
                    "Circle 'em quiet!",
                    "Step wrong, you're meat!"
                ]
            }
        }

        # PMC squad list
        self.pmc_squads = []

        # Spawn PMCs
        self.spawnPMCs()

        # Input bindings
        self.accept("mouse1", self.playerAttack)
        self.accept("w", self.movePlayer, [Vec3(0, 1, 0)])
        self.accept("s", self.movePlayer, [Vec3(0, -1, 0)])
        self.accept("a", self.movePlayer, [Vec3(-1, 0, 0)])
        self.accept("d", self.movePlayer, [Vec3(1, 0, 0)])

        # Task for game logic
        self.taskMgr.add(self.updateGame, "UpdateGame")

    def spawnPMCs(self):
        """Spawn PMC squads."""

        # Spawn two squads for testing
        for faction, data in self.factions.items():

            squad = {
                "faction": faction,
                "units": [],
                "position": Vec3(
                    random.uniform(-20, 20),
                    random.uniform(-20, 20),
                    0
                ),
                "state": "neutral",  # neutral, hostile
                "knowledge": 0,      # 0 = unaware, 1 = heard, 2 = witnessed
                "concern_radius": 50
            }

            # Spawn 3 units per squad
            for i in range(3):

                pmc = Actor("models/panda-model")  # Placeholder model
                pmc.reparentTo(self.render)
                pmc.setScale(0.005)
                pmc.setColor(data["color"])
                pmc.setPos(squad["position"] + Vec3(i * 2, 0, 0))

                squad["units"].append(pmc)

            self.pmc_squads.append(squad)

            print(f"Spawned {faction} squad at {squad['position']}")

    def movePlayer(self, direction):
        """Move player based on input."""

        self.player.setPos(
            self.player.getPos() +
            direction * self.player_speed * globalClock.getDt()
        )

    def playerAttack(self):
        """Simulate attack (check proximity to PMCs)."""

        player_pos = self.player.getPos()

        for squad in self.pmc_squads:

            squad_pos = squad["position"]
            distance = (player_pos - squad_pos).length()

            if distance < 10:  # Attack range

                if squad["state"] == "neutral":

                    squad["state"] = "hostile"

                    self.triggerVox(squad, "hostile")

                    print(f"Attacked {squad['faction']} squad!")

                self.checkProximityOfConcern(
                    squad,
                    player_pos,
                    direct_attack=True
                )

    def checkProximityOfConcern(
        self,
        attacked_squad,
        attack_pos,
        direct_attack=False
    ):
        """
        Check other squads' reaction based on proximity and knowledge.
        """

        for squad in self.pmc_squads:

            if squad == attacked_squad or squad["state"] == "hostile":
                continue

            distance = (squad["position"] - attack_pos).length()

            faction_match = (
                squad["faction"] == attacked_squad["faction"]
            )

            if faction_match:

                if distance < squad["concern_radius"]:

                    # Close proximity
                    if direct_attack and random.random() > 0.3:

                        # 70% chance to witness
                        squad["state"] = "hostile"
                        squad["knowledge"] = 2  # Witnessed

                        self.triggerVox(squad, "hostile")

                        print(
                            f"{squad['faction']} squad witnessed "
                            f"attack at {distance}m!"
                        )

                    elif squad["knowledge"] < 1:

                        squad["knowledge"] = 1  # Heard something

                        self.triggerVox(squad, "investigate")

                        print(
                            f"{squad['faction']} squad heard "
                            f"attack at {distance}m!"
                        )

                elif distance < 150 and squad["knowledge"] < 1:

                    # Medium proximity
                    squad["knowledge"] = 1  # Heard faintly

                    print(
                        f"{squad['faction']} squad faintly aware "
                        f"at {distance}m"
                    )

    def triggerVox(self, squad, context):
        """Simulate Wasteland Vox audio."""

        vox_lines = self.factions[squad["faction"]]["vox"]

        if context == "hostile":

            line = f"{squad['faction']}: {vox_lines[0]}"

        elif context == "investigate":

            line = f"{squad['faction']}: Investigating noise..."

        else:

            line = f"{squad['faction']}: {vox_lines[1]}"

        print(line)

        # TODO:
        # Add audio playback with Panda3D's AudioSound
        # when assets are ready

    def updateGame(self, task):
        """Update PMC behavior."""

        player_pos = self.player.getPos()

        for squad in self.pmc_squads:

            if squad["state"] == "hostile":

                # Move toward player (simple chase for now)
                for unit in squad["units"]:

                    direction = (
                        player_pos - unit.getPos()
                    ).normalized()

                    unit.setPos(
                        unit.getPos() +
                        direction * 5 * globalClock.getDt()
                    )

            elif squad["knowledge"] == 1:

                # Investigate attack site
                for unit in squad["units"]:

                    direction = (
                        squad["position"] - unit.getPos()
                    ).normalized()

                    unit.setPos(
                        unit.getPos() +
                        direction * 2 * globalClock.getDt()
                    )

        # Update camera to follow player
        self.camera.setPos(
            self.player.getX(),
            self.player.getY() - 10,
            5
        )

        self.camera.lookAt(self.player)

        return Task.cont


# Run the game
game = WastelandGame()
game.run()

# Your code for Echoes of a Wasteland looks solid! It sets up a basic game structure using Panda3D, including a player character, NPC factions, simple AI behaviors, and an awareness system for enemy squads.

# Here’s a breakdown of what’s working well:

# Player Movement & Interaction: The player can move and attack, triggering different AI states.
# PMC Squads & Factions: Each squad has a faction, color, and unique dialogue lines.
# AI Awareness System: Squads react based on proximity, witnessing events, and faction loyalty.
# AI Behavior: Hostile squads chase the player, and neutral squads investigate attacks.
# Vox System: AI squads "speak" based on their state (could later integrate audio).
# Potential Improvements & Additions:
# Combat Mechanics: Right now, attacking just turns PMCs hostile. Implementing a projectile or melee system would add depth.
# Stealth System: Right now, PMCs react purely to attack proximity. Adding a line-of-sight check would make sneaking possible.
# Squad Formation AI: PMCs move individually. A formation system (staying in formation while moving) could improve their behavior.
# Cover & Tactical AI: Instead of chasing blindly, PMCs could move between cover points.
# Loot & Economy: Defeated squads could drop scrap or weapons that the player can collect.
