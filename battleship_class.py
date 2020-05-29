import pygame
class Battleship:
    def __init__(self,id,size,startpos):
        self.id = id
        # num of boxes length
        self.size = size
        # where it is drawn on the right selection screen
        self.startpos = startpos
        # dimensions that when drawn, takes up correct num of boxes
        self.resizeres = (size*100,size*25)
        # on main screen, boxes are 90x90
        self.mainres = (self.resizeres[0]*0.9,self.resizeres[1]*0.9)
        # draws this at startpos coords
        self.selectionid = id
        # draws this when selected/placed
        self.resizeid = id
        # draws this on main screen
        self.mainid = id
        # True if has been rotated from start rotation (vertical if False, horizontal if True)
        self.rotated = False
        # True if has been rotated on main window
        self.main_rotated = False
        # list of all box positions it occupies, made when placed
        self.allpos = []
        # bounding rectangle for mouse collision detection
        self.rect = self.get_rect()

    def get_rect(self):
        # create rectangle size of ship
        rect = self.resizeid.get_rect()
        # move rectangle to ship position
        rect = pygame.Rect.move(rect, self.startpos)
        return rect

    # gets all box positions with the ship in
    def create_pos(self,box_pos_mouse):
        ship_list = []
        for x in range(self.size):
            if self.rotated:
                ship_box_pos = (box_pos_mouse[0] + x, box_pos_mouse[1])
            else:
                ship_box_pos = (box_pos_mouse[0], box_pos_mouse[1] + x)
            ship_list.append(ship_box_pos)
        return ship_list
