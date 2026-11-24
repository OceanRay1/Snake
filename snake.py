class Env():
    def __init__(self, rad):
        self.rad = rad
        self.board = None

    def setup(self):
        self.board = []
        for column in range(self.rad):
            row_add = []
            for row in range(self.rad):
                row_add.append(0)
            self.board.append(row_add)
        return '\n'.join(str(row) for row in self.board)

    def snake_square():
        pass

class Snake():
    def __init__(self, size, head):
        self.size = 2
        self.head = None
    
    def directions():
        pass

    def get_pos():
        pass

a = Env(5)
print(a.setup())