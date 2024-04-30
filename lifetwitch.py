import pygame
import numpy as np
import random
import math
import asyncio
import configparser
import time
import logging

from twitchio.ext import commands
from threading import Thread

USE_TWITCH=True

class Bot(commands.Bot):
    def __init__(self):
        config = configparser.ConfigParser()
        try:
            config.read('config_tokens.ini')
            token = config['DEFAULT']['Token']
            client_id = config['DEFAULT']['ClientID']
            nick = config['DEFAULT']['Nick']
            initial_channels = config['DEFAULT']['InitialChannels'].split(',')
        except (configparser.Error, KeyError) as e:
            print(f"Error reading configuration: {e}")
            sys.exit(1)
        
        super().__init__(token=token, client_id=client_id, prefix='!', nick=nick, initial_channels=initial_channels)

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        if message.echo:
            return
        print(message.content)
        pygame.event.post(pygame.event.Event(pygame.USEREVENT, message=message.content))
        await self.handle_commands(message)

    @commands.command()
    async def help(self, ctx: commands.Context):
        await ctx.send(f'➤ !b [0-1]: ratio of cells to be born ➤ !d [0-1]: ratio of cells to die ➤ !r [0-1]: restart with ratio of cells alive ➤ !s or !u [x,y] set or unset cell at coordinates ie. !s 100 200 ➤ !p : pause/unpause ➤ !x switch between the grid of different rules and using the whole board for classic Life ➤ !l [laws]: change the laws (ie. classic is "!l B3S23"')

def randomize_cells(cells, probability, state):
    for r, c in np.ndindex(cells.shape):
        if random.random() < probability:
            cells[r, c] = state

def update(surface, cur, sz, gamemode, laws, paused):
    """
    Update the game state for each frame.

    :param surface: Pygame surface object
    :param cur: Current state of the cells
    :param sz: Size of each cell
    :param gamemode: Current game mode
    :param laws: Ruleset for cell survival and birth
    :param paused: Pause state of the game
    :return: Updated state of the cells
    """
    nxt = np.zeros((cur.shape[0], cur.shape[1]))
    stepr=cur.shape[0]/8
    stepc=cur.shape[0]/16
    setborn=[]
    setsurvive=[]
    if laws[:1]!="B" or not ("S" in laws):
        laws="B3S23"
    lawsplit=laws[1:].split("S", 1)
    for ch in lawsplit[0]:
        try:
            setborn.append(int(ch))
        except:
            print("error")
    for ch in lawsplit[1]:
        try:
            setsurvive.append(int(ch))
        except:
            print("error")
    for r, c in np.ndindex(cur.shape):
        if paused==1:
            nxt[r, c]=cur[r,c]
        else:
            num_alive = np.sum(cur[r-1:r+2, c-1:c+2]) - cur[r, c]
            rzone=int(r/stepr)
            czone=int(c/stepr)
            if gamemode=="g":
                if czone>7:
                    if (cur[r, c] == 1 and (czone-8) <= num_alive <= (czone-8)+2) or (cur[r, c] == 0 and rzone <= num_alive <= rzone):
                        nxt[r, c] = 1
                else:
                    if (cur[r, c] == 1 and czone <= num_alive <= czone+1) or (cur[r, c] == 0 and rzone <= num_alive <= rzone):
                        nxt[r, c] = 1
            else:
                if (cur[r, c] == 1 and num_alive in setsurvive) or (cur[r, c] == 0 and num_alive in setborn):
                    nxt[r, c] = 1

        col = col_alive if cur[r, c] == 1 else col_background
        pygame.draw.rect(surface, col, (c*sz+bord_size, r*sz+bord_size, sz-1, sz-1))

    return nxt

def init(dimx, dimy):
    cells = np.zeros((dimy, dimx))
    for r, c in np.ndindex(cells.shape):
        cells[r,c] = (random.randint (0,1))
    return cells

def callmain():
    main(352, 176, 3)
    
def handle_key_events(event, cells, dimx, dimy):
    if event.key == pygame.K_d: #death
        randomize_cells(cells, 1/50, 0)
    if event.key == pygame.K_h: #hyperdeath
        randomize_cells(cells, 1/4, 0)
    if event.key == pygame.K_x: #xtinction
        randomize_cells(cells, 1/1, 0)
    if event.key == pygame.K_l: #live
        randomize_cells(cells, 1/100, 1)
    if event.key == pygame.K_b: #bloom
        randomize_cells(cells, 1/5, 1)
    if event.key == pygame.K_p: #panspermia
        randomize_cells(cells, 1/1, 1)
    if event.key == pygame.K_r:
        cells = init(dimx, dimy)

def handle_user_events(event, cells):
    print(event.message)
    splitmessage=event.message.split(" ",2)
    if len(splitmessage)==1:
        if splitmessage[0]=="!x":
            if gamemode=="g":
                gamemode="o"
            else:
                gamemode="g"
        if splitmessage[0]=="!p":
            if paused==0:
                paused=1
            else:
                paused=0
    if len(splitmessage)>=2:
        if splitmessage[0]=="!l":
            laws=splitmessage[1]
        try:
            proportion=float(splitmessage[1])
        except:
            proportion=0.
        if proportion <0:
            proportion=0.
        if proportion>1:
            proportion=1.
        if splitmessage[0]=="!r":
            for r, c in np.ndindex(cells.shape):
                if (random.random()<proportion):
                    cells[r,c]=1
                else:
                    cells[r,c]=0
        if splitmessage[0]=="!b":
            randomize_cells(cells, proportion, 1)
        if splitmessage[0]=="!d":
            randomize_cells(cells, proportion, 0)

        if len(splitmessage)==3:
            try:
                xcord=int(splitmessage[1])
                ycord=int(splitmessage[2])
            except:
                xcord=0
                ycord=0
            if xcord<0:
                xcord=0
            if ycord<0:
                ycord=0
            if xcord>=cells.shape[0]:
                xcord=cells.shape[0]-1
            if ycord>=cells.shape[1]:
                ycord=cells.shape[1]-1

        if splitmessage[0]=="!s":
            cells[xcord,ycord]=1
        if splitmessage[0]=="!u":
            cells[xcord,ycord]=0

def main(dimx, dimy, cellsize):
    pygame.init()
    surface = pygame.display.set_mode(((dimx * cellsize)+bord_size, (dimy * cellsize)+bord_size))
    pygame.display.set_caption("Twitch Plays Conway's Game of Life")
    green = (0, 255, 0)
    blue = (0, 0, 128)
    gamemode="g"
    laws="B3S23"
    paused=0
    cells = init(dimx, dimy)
    font = pygame.font.Font('freesansbold.ttf', 32)
    text1 = font.render('Survive', True, col_alive, col_grid)
    text2 = font.render('0-1  1-2  2-3  3-4  4-5  5-6  6-7  7-8   0-2  1-3  2-4  3-5  4-6  5-7  6-8  7-9', True, col_alive, col_grid)
    text3 = font.render('Born', True, col_alive, col_grid)
    text3 = pygame.transform.rotate(text3, 90)
    text4 = font.render('7      6     5     4      3     2      1     0', True, col_alive, col_grid)
    text4 = pygame.transform.rotate(text4, 90)
 
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                handle_key_events(event, cells, dimx, dimy)
            if event.type == pygame.USEREVENT:
                handle_user_events(event, cells)

        surface.fill(col_grid)
        if gamemode=="g":
            surface.blit(text1, (550,0))
            surface.blit(text2, (95,45))
            surface.blit(text3, (0,280))
            surface.blit(text4, (40,100))
            for r in range(1,9):
#                print (r,r*(dimx*cellsize/8)-1)

                pygame.draw.line(surface,col_grid2, (bord_size, (r*(dimy*cellsize//8))+bord_size), ((dimx*cellsize)+bord_size, (r*(dimy*cellsize//8))+bord_size),1)
                pygame.draw.line(surface,col_grid2, ((r*(dimy*cellsize//8))+bord_size, bord_size), ((r*(dimy*cellsize//8))+bord_size,(dimy*cellsize)+bord_size),1)
                pygame.draw.line(surface,col_grid2, (((r+8)*(dimy*cellsize//8))+bord_size, bord_size), (((r+8)*(dimy*cellsize//8))+bord_size,(dimy*cellsize)+bord_size),1)

        cells = update(surface, cells, cellsize, gamemode, laws, paused)
        pygame.display.update()
        pygame.time.wait(400)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    col_alive = tuple(map(int, config['COLORS']['Alive'].split(',')))
    col_background = tuple(map(int, config['COLORS']['Background'].split(',')))
    col_grid = tuple(map(int, config['COLORS']['GridColor'].split(',')))
    col_grid2 = tuple(map(int, config['COLORS']['GridColor2'].split(',')))
    bord_size = int(config['DISPLAY']['BorderSize'])
    logging.basicConfig(level=logging.INFO)

    t = Thread(target=callmain)
    t.start()
    if USE_TWITCH:
        bot = Bot()
        loop = asyncio.get_event_loop()
        loop.create_task(bot.run())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.close()
    else:
        time.sleep(99999999)