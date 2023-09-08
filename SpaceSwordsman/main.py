#Author: Benjamin Carroll
#Description: A Space Invaders type game. The player is able to shoot blade beams and parry enemy blade beams over 10 waves

import os
import pygame
import random
import time

#Path from working directory to game
dir = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

#Initialize pygame
WIDTH = 800
HEIGHT = 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Swordsman")
pygame.font.init()

#Player sprites
PLAYER_IDLE_IMG = pygame.image.load((os.path.join(dir, "assets", "player_idle.png")))
PLAYER_SWING_IMG = pygame.image.load((os.path.join(dir, "assets", "player_swing.png")))
PLAYER_PARRY_IMG_1 = pygame.image.load((os.path.join(dir, "assets", "player_parry_1.png")))
PLAYER_PARRY_IMG_2 = pygame.image.load((os.path.join(dir, "assets", "player_parry_2.png")))

#Enemy sprites
GREEN_IDLE_IMG = pygame.image.load((os.path.join(dir, "assets", "green_idle.png")))
GREEN_SWING_IMG = pygame.image.load((os.path.join(dir, "assets", "green_swing.png")))

YELLOW_IDLE_IMG = pygame.image.load((os.path.join(dir, "assets", "yellow_idle.png")))
YELLOW_SWING_IMG = pygame.image.load((os.path.join(dir, "assets", "yellow_swing.png")))

RED_IDLE_IMG = pygame.image.load((os.path.join(dir, "assets", "red_idle.png")))
RED_SWING_IMG = pygame.image.load((os.path.join(dir, "assets", "red_swing.png")))

#Blade Beams
PLAYER_BEAM = pygame.image.load((os.path.join(dir, "assets", "player_beam.png")))
ENEMY_BEAM = pygame.image.load((os.path.join(dir, "assets", "enemy_beam.png")))

#Background
BACK_IMG = pygame.transform.scale(pygame.image.load(os.path.join(dir, "assets", "background.png")), (WIDTH, HEIGHT))


#Represents hitbox rectangle, used to translate rectangle to a mask for collision
class Hitbox:
    def __init__(self, x, y, length, width):
        self.__x = x
        self.__y = y
        self.__length = length
        self.__width = width
        self.__mask = pygame.mask.Mask((self.__length, self.__width), True)

    def move(self, x, y):
        self.__x = x
        self.__y = y

    def getX(self):
        return self.__x
    
    def getY(self):
        return self.__y
    
    def getMask(self):
        return self.__mask


#Blade beams that are shot by swordsmen
class Beam:
    def __init__(self, x, y, vel, image):
        self.__x = x
        self.__y = y
        self.__vel = vel
        self.__image = image
        self.__mask = pygame.mask.from_surface(image)

    def draw(self, window):
        window.blit(self.__image, (self.__x, self.__y))

    def move(self):
        self.__y -= self.__vel

    #Return whether the Beam is off of the screen or not
    def offscreen(self):
        return (self.__y + self.__image.get_height() < 0) or (self.__y > HEIGHT)
    
    #Return whether the current beam is colliding with a given hitbox object
    def collide(self, hitbox):
        offset_x = hitbox.getX() - self.__x
        offset_y = hitbox.getY() - self.__y
        return self.__mask.overlap(hitbox.getMask()  , (offset_x, offset_y)) != None
    
    def getX(self):
        return self.__x



#Contains all beams and handles checking collisions and movement
class BeamHandler:
    def __init__(self):
        self.__playerBeams = []
        self.__enemyBeams = []

    #Move each player beam, then check for/handle collisions
    def __updatePlayerBeams(self, window, enemies):
        for beam in self.__playerBeams[:]:
            beam.move()
            beam.draw(window)

            if beam.offscreen():
                self.__playerBeams.remove(beam)
            else:
                for enemy in enemies:
                    if beam.collide(enemy.getHitbox()):
                        self.__playerBeams.remove(beam)
                        enemy.hit()
                        if enemy.getHealth() == 0:
                            enemies.remove(enemy)
                            break

    #Move each enemy beam and check for collisions with player
    def __updateEnemyBeams(self, window, player):
        for beam in self.__enemyBeams[:]:
            beam.move()
            beam.draw(window)

            if beam.collide(player.getHitbox()):
                player.hit(beam.getX())
                self.__enemyBeams.remove(beam)

            elif beam.offscreen():
                self.__enemyBeams.remove(beam)

    #Updates all lasers for each frame
    def tick(self, window, player, enemies):
        self.__updatePlayerBeams(window, enemies)
        self.__updateEnemyBeams(window, player)
    
    def addPlayerBeam(self, playerBeam):
        self.__playerBeams.append(playerBeam)

    def addEnemyBeam(self, enemyBeam):
        self.__enemyBeams.append(enemyBeam)

    def reset(self):
        self.__playerBeams.clear()
        self.__enemyBeams.clear()



#Base class for player and enemy
class Swordsman:
    def __init__(self, x, y, image, beamHandler, maxHealth=5):
        self._x = x
        self._y = y
        self._maxHealth = maxHealth
        self._image = image
        self._beamHandler = beamHandler
        self._health = maxHealth
        self._hitbox = None

    def _draw(self, window):
        window.blit(self._image, (self._x, self._y))

    def hit(self):
        self._health -= 1

    def getHealth(self):
        return self._health

    def getHitbox(self):
        return self._hitbox



#Player, includes parry functions 
class Player(Swordsman):
    __parryWindow = 10 #Frames a parry can be successful
    __parryCounter = 0 #Keeps track of current frames after parry command
    __parryCooldown = 40 #How long a player is locked into a parry/until a parry can be done again
    __shotCooldown = 30 #How many frames between shots
    __shotCounter = 15 #Default value of 15 to avoid sword swing on start
    __moveVelocity = 5 #Player movement velocity
    
    def __init__(self, x, y, beamHandler):
        super().__init__(x, y, PLAYER_IDLE_IMG, beamHandler)
        self._hitbox = Hitbox(self._x + 54, self._y + 40, 21, 21)

    #Move player left or right as long as it would remain on screen
    def move(self, right):
        if right and self._x + self._image.get_width() + self.__moveVelocity < WIDTH and self.__parryCounter == 0:
            self._x += self.__moveVelocity
            self._hitbox.move(self._x + 54, self._y + 40)
        elif not right and self._x - self.__moveVelocity > 0 and self.__parryCounter == 0:
            self._x -= self.__moveVelocity
            self._hitbox.move(self._x + 54, self._y + 40)

    #If the player can shoot and is not locked into a parry, create a new beam and give it to the BeamHandler, then start cooldown, change sprite
    def shoot(self):
        if self.__shotCounter == 0 and self.__parryCounter == 0:
            beam = Beam(self._x, self._y - 10, 10, PLAYER_BEAM)
            self._beamHandler.addPlayerBeam(beam)
            self._image = PLAYER_SWING_IMG
            self.__shotCounter = 1

    #Start parry counter and change sprite
    def parry(self):
        if self.__parryCounter == 0:
            self._image = PLAYER_PARRY_IMG_1
            self.__parryCounter += 1

    #Draw player, increment player cooldowns, and handle sprite changes for each clock tick
    def tick(self, window):
        self._draw(window)
        if self.__shotCounter > self.__shotCooldown:
            self._image = PLAYER_IDLE_IMG
            self.__shotCounter = 0
        elif self.__shotCounter != 0 and self.__shotCounter <= self.__shotCooldown:
            self.__shotCounter += 1


        if self.__parryCounter == self.__parryWindow + 1:
            self._image = PLAYER_PARRY_IMG_2 #Parry IMG 2 shows the player is locked into the parry from a miss
        elif self.__parryCounter > self.__parryWindow + self.__parryCooldown:
            self._image = PLAYER_IDLE_IMG
            self.__parryCounter = 0

        if self.__parryCounter != 0 and self.__parryCounter <= self.__parryWindow + self.__parryCooldown:
            self.__parryCounter += 1

    #Reflect beam if parrying by creating a new beam in opposite direction and reset all cooldowns, otherwise take damage
    def hit(self, x):
        if self.__parryCounter != 0 and self.__parryCounter <= self.__parryWindow:
            beam = Beam(x, self._y, 10, PLAYER_BEAM)
            self._beamHandler.addPlayerBeam(beam)
            self.__parryCounter = 0
            self.__shotCounter = 0
            self._image = PLAYER_IDLE_IMG

        else:
            super().hit()

    def setHealth(self, health):
        self._health = health

    def resetHealth(self):
        self._health = self._maxHealth



#Enemy, shoots differently than a player by shooting a number of lasers within a second
class Enemy(Swordsman):
    def __init__(self, x, y, idleImage, swingImage, shotNum, beamHandler, maxHealth):
        super().__init__(x, y, idleImage, beamHandler, maxHealth)
        self.__idleImage = idleImage
        self.__swingImage = swingImage
        self.__burstCooldown = 120 #Cooldown after shots have been fired
        self.__burstWindow = 60 #Time that all shots will take collectively
        self.__shotCounter = random.randint(0, self.__burstWindow) #Start counter at random time for asynchronous enemy beams
        self.__moveVelocity = 1.5 #Movement speed of enemies
        self.__shotNum = shotNum #number of shots per burst
        self.__currShots = random.randint(0, self.__shotNum) #Current shots in burst fired, start random for random spawn fire patterns
        self._hitbox = Hitbox(self._x + 53, self._y + 60, 21, 21)

    def __move(self):
        self._y += self.__moveVelocity
        self._hitbox.move(self._x + 54, self._y + 40)

    #If the player can shoot, create a new beam and give it to the BeamHandler, then start cooldown, change sprite, and increment currShots to keep track of the burst
    def __shoot(self):
        if self.__shotCounter == 0:
            beam = Beam(self._x, self._y - 10, -9, ENEMY_BEAM)
            self._beamHandler.addEnemyBeam(beam)
            self._image = self.__swingImage
            self.__shotCounter = 1
            self.__currShots += 1
    
    #Draw, move, and shoot each frame and handle cooldowns
    def tick(self, window):
        self._draw(window)


        #If burst isn't done, use cooldown determined by shots in the burst window
        if self.__currShots < self.__shotNum:
            if self.__shotCounter > (self.__burstWindow / self.__shotNum):
                self.__shotCounter = 0
            elif self.__shotCounter != 0 and self.__shotCounter <= (self.__burstWindow / self.__shotNum):
                self.__shotCounter += 1
            if self.__shotCounter > 15:
                self._image = self.__idleImage

        #If burst is finished, use burst cooldown
        else:
            if self.__shotCounter > self.__burstCooldown:
                self.__shotCounter = 0
                self.__currShots = 0
            elif self.__shotCounter != 0 and self.__shotCounter <= self.__burstCooldown:
                self.__shotCounter += 1
            if self.__shotCounter > 30:
                self._image = self.__idleImage
        
        self.__move()
        self.__shoot()

    def getY(self):
        return self._y




#Fills the enemy list based on given colors for the next round
def nextRound(enemyList, enemyColors, beamHandler):
    for enemy in enemyColors:
        if enemy == "green":
            enemyList.append(Enemy(random.randint(0, WIDTH-PLAYER_IDLE_IMG.get_width()), random.randint(-2000, -50), GREEN_IDLE_IMG, GREEN_SWING_IMG, 1, beamHandler, 1))
        elif enemy == "yellow":
            enemyList.append(Enemy(random.randint(0, WIDTH-PLAYER_IDLE_IMG.get_width()), random.randint(-2000, -50), YELLOW_IDLE_IMG, YELLOW_SWING_IMG, 2, beamHandler, 2))
        elif enemy == "red":
            enemyList.append(Enemy(random.randint(0, WIDTH-PLAYER_IDLE_IMG.get_width()), random.randint(-2000, -50), RED_IDLE_IMG, RED_SWING_IMG, 3, beamHandler, 3))



#Main game loop
def game_loop():
    run = title_screen() #If there was a quit on title screen, do not run the game
    clock = pygame.time.Clock()
    beamHandler = BeamHandler()
    player = Player(WIDTH/2 - PLAYER_IDLE_IMG.get_width()/2, 650, beamHandler) #set player in center of the screen
    infoFont = pygame.font.SysFont("arial", 40)

    #Holds present enemy combinations for each round for 10 rounds
    roundEnemies = {1: ["green", "green", "green", "green", "green"],
                      2: ["green", "green", "green", "green", "green", "green", "green", "green", "green", "green"],
                      3: ["green", "green", "green", "yellow", "yellow"],
                      4: ["green", "green", "green", "green", "yellow", "yellow", "yellow"],
                      5: ["green", "green", "yellow", "red"],
                      6: ["green", "green", "yellow", "yellow", "red", "red"],
                      7: ["green", "green", "green", "green", "red", "red", "red"],
                      8: ["yellow", "yellow", "yellow", "yellow", "red"],
                      9: ["red", "red", "red", "red", "red"],
                      10: ["green", "green", "green", "green" "yellow", "yellow", "yellow", "yellow", "red", "red", "red", "red"]}
    
    round = 9
    enemies = []
    while run:
        clock.tick(60) #Set the game to 60 FPS

        if len(enemies) == 0 and round < 10: #Increment round once all enemies are defeated
            round += 1
            nextRound(enemies, roundEnemies[round], beamHandler)
        elif len(enemies) == 0: #Reset the game and show win screen
            round = 1
            player.resetHealth()
            nextRound(enemies, roundEnemies[round], beamHandler)
            beamHandler.reset()
            run = win_screen() #If there was a quit on win screen, do not run the game

        #Check for quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            #User input for parry only on keydown input
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_LSHIFT:
                    player.parry()
        
        #User input detection
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_LEFT]:
            player.move(False)
        elif pressed[pygame.K_RIGHT]:
            player.move(True)
        if pressed[pygame.K_SPACE]:
            player.shoot()

        

        #Draw/update entities of the game
        WIN.blit(BACK_IMG, (0, 0))
        for enemy in enemies[:]:
            enemy.tick(WIN)
            if enemy.getY() > HEIGHT: #if an enemy got off screen, give player damage
                enemies.remove(enemy)
                player.setHealth(player.getHealth() - 1)
        player.tick(WIN)
        beamHandler.tick(WIN, player, enemies)
        

        #Draw text
        roundText = infoFont.render(f"Round: {round}", 1, (255, 255, 255))
        WIN.blit(roundText, (0, 0))
        healthText = infoFont.render(f"Health: {player.getHealth()}", 1, (255, 255, 255))
        WIN.blit(healthText, (0, 40))

        pygame.display.update()

        #Lose condition, show lose screen and reset the game
        if player.getHealth() <= 0:
            run = lose_screen(round) #If there was a quit on lose screen, do not run the game
            round = 0
            enemies.clear()
            player.resetHealth()
            beamHandler.reset()


    pygame.quit()



#Draw title screen
def title_screen():
     titleFont = pygame.font.SysFont("arial", 80)
     instructFont = pygame.font.SysFont("arial", 40)
     controlFont = pygame.font.SysFont("arial", 20)
     mainMenuActive = True

     while mainMenuActive:
            WIN.blit(BACK_IMG, (0,0))
            titleText = titleFont.render("Space Swordsman", 1, (200, 255, 200))
            WIN.blit(titleText, (WIDTH/2 - titleText.get_width()/2, 200))
            instructText = instructFont.render('Press "Space" to play', 1, (255, 255, 255))
            WIN.blit(instructText, (WIDTH/2 - instructText.get_width()/2, 600))

            controlText1 = controlFont.render("Left/Right Arrows - Move", 1, (255, 255, 255))
            controlText2 = controlFont.render("Space - Shoot Blade Beam", 1, (255, 255, 255))
            controlText3 = controlFont.render("Left Shift - Parry", 1, (255, 255, 255))
            controlTextX = WIDTH - controlText2.get_width()
            WIN.blit(controlText1, (controlTextX, 680))
            WIN.blit(controlText2, (controlTextX, 720))
            WIN.blit(controlText3, (controlTextX, 760))
            pygame.display.update()

            #Move on and return false if game was quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                    break

            #Move on and return true if space is pressed
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_SPACE]:
                mainMenuActive = False
                return True



#Draw win screen
def win_screen():
     titleFont = pygame.font.SysFont("arial", 80)
     instructFont = pygame.font.SysFont("arial", 40)
     winActive = True

     while winActive:
            WIN.blit(BACK_IMG, (0,0))
            titleText = titleFont.render("You Won!", 1, (255, 255, 200))
            WIN.blit(titleText, (WIDTH/2 - titleText.get_width()/2, 200))
            instructText = instructFont.render('Press "Space" to play again', 1, (255, 255, 255))
            WIN.blit(instructText, (WIDTH/2 - instructText.get_width()/2, 600))
            pygame.display.update()

            #Move on and return false if game was quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                    break

            #Move on and return true if space is pressed
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_SPACE]:
                winActive = False
                return True


   
#Draw lose screen
def lose_screen(round):
     titleFont = pygame.font.SysFont("arial", 80)
     instructFont = pygame.font.SysFont("arial", 40)
     winActive = True

     while winActive:
            WIN.blit(BACK_IMG, (0,0))
            titleText = titleFont.render("You Lost!", 1, (255, 255, 200))
            roundText = titleFont.render(f"You made it to round {round}", 1, (255, 255, 200))
            WIN.blit(titleText, (WIDTH/2 - titleText.get_width()/2, 200))
            WIN.blit(roundText, (WIDTH/2 - roundText.get_width()/2, 300))
            instructText = instructFont.render('Press "Space" to play again', 1, (255, 255, 255))
            WIN.blit(instructText, (WIDTH/2 - instructText.get_width()/2, 600))
            pygame.display.update()

            #Move on and return false if game was quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                    break

            #Move on and return true if space is pressed
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_SPACE]:
                winActive = False
                return True
        


        
if __name__ == "__main__":
    game_loop()