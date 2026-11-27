from random import randint, choice
from collections import deque

#directions snake moves
DIRECTIONS = {
    'up': (-1, 0),
    'down': (1, 0),
    'left': (0, -1),
    'right': (0, 1)
}

OPPOSITES = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left"
}

#snake that moves across env    
class Snake():
    def __init__(self, head):
        self.size = 1
        self.head = head
        self.past = deque([head])
    
    def move(self, direction):
        dx, dy = DIRECTIONS[direction]
        self.head = (self.head[0] + dx, self.head[1] + dy)

#snake game env
class Env():
    def __init__(self, rad):
        self.rad = rad
        self.board = None
        self.gamestate = True
        self.gamesnake = Snake((self.rad // 2, self.rad // 2))
        self.count = 0
        self.fruitstate = False
        self.fruitlocation = None
        self.gamewon = False

    def setup(self):
        #board setup
        self.board = []
        self.gamestate = True

        #build board
        for row in range(self.rad):
            row_add = []
            for column in range(self.rad):
                row_add.append(0)
            self.board.append(row_add)

        #start snake head
        sx, sy = self.gamesnake.head
        self.board[sx][sy] = 1

        self.fruit()
        self.fruitstate = True

    def step(self, action):
        if not self.gamestate:
            return
        
        #movement
        self.count += 1
        self.gamesnake.move(action) 

        x, y = self.gamesnake.head
        self.gamesnake.past.append((x, y))

        #if square either blank or fruit
        if 0 <= x < self.rad and 0 <= y < self.rad:
            if self.board[x][y] != 1:
                if self.board[x][y] == 2:
                    self.gamesnake.size += 1
                    self.fruitstate = False
                else:
                    a, b = self.gamesnake.past.popleft()
                    self.board[a][b] = 0

                self.board[x][y] = 1
            else:
                self.gamestate = False 
        else: 
            self.gamestate = False

        #check win condition if all fruit eaten
        if self.gamesnake.size == self.rad * self.rad:
            self.gamewon = True
            self.gamestate = False
            return self.count

        if not self.fruitstate:
            self.fruit()
            self.fruitstate = True

    def play(self, agent):
        self.setup()
        while self.gamestate:
            action = agent(self)
            self.step(action)
        return {
            'steps': self.count,
            'score': self.gamesnake.size,
            'won': self.gamewon
        }
            
    def fruit(self):
        fx, fy = randint(0, self.rad - 1), randint(0, self.rad - 1)
        #checks if fruit square on snake
        while self.board[fx][fy] == 1:
            fx, fy = randint(0, self.rad - 1), randint(0, self.rad - 1)

        self.fruitlocation = (fx, fy)
        self.board[fx][fy] = 2

    def __str__(self):
        return '\n'.join(str(row) for row in self.board)
