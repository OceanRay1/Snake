from random import randint
from collections import deque

#snake game env
class Env():
    def __init__(self, rad):
        self.rad = rad
        self.board = None
        self.gamestate = True
        self.gamesnake = Snake((self.rad // 2, self.rad // 2))
        self.count = 0
        self.fruitstate = False
        self.gamewon = False

    def setup(self):
        #board setup
        self.board = []
        for row in range(self.rad):
            row_add = []
            for column in range(self.rad):
                row_add.append(0)
            self.board.append(row_add)

        #start snake head
        sx, sy = self.gamesnake.head
        self.board[sx][sy] = 1

    def play(self):
        while self.gamestate:

            for row in self.board:
                if 2 in row:
                    self.fruitstate = True 
            
            if not self.fruitstate:
                self.fruit()

            #movement
            self.count += 1
            self.gamesnake.move() 

            x, y = self.gamesnake.head
            self.gamesnake.past.append((x, y))
            print(self.gamesnake.past)

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

            #every fruit eaten
            if self.gamesnake.size == self.rad * self.rad:
                self.gamewon = True
                self.gamestate = False
                return self.count

    def fruit(self):
        fx, fy = randint(0, self.rad - 1), randint(0, self.rad - 1)
        #checks if fruit square on snake
        while self.board[fx][fy] == 1:
            fx, fy = randint(0, self.rad - 1), randint(0, self.rad - 1)

        self.board[fx][fy] = 2
         
    def __str__(self):
        return '\n'.join(str(row) for row in self.board)

#snake that moves across env    
class Snake():
    def __init__(self, head):
        self.size = 1
        self.head = head
        self.left = True
        self.right = False
        self.up = False
        self.down = False
        self.past = deque()
        self.past.append(self.head)
    
    def move(self):
        if self.up:
            self.head = (self.head[0] - 1, self.head[1])  # row - 1
        elif self.down:
            self.head = (self.head[0] + 1, self.head[1])  # row + 1
        elif self.left:
            self.head = (self.head[0], self.head[1] - 1)  # col - 1
        elif self.right:
            self.head = (self.head[0], self.head[1] + 1)  # col + 1


# board/env test
env = Env(5) 
env.setup()
print(env.gamesnake.head)

print("Start:")
print(env)
print("Active:", env.gamestate)

# Run the game

env.play()


print("\nEnd:")
print(env)
print("Total moves:", env.count)
print(env.gamesnake.size)
print("Active:", env.gamestate)
