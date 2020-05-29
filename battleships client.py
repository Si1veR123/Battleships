import pygame, os, _thread, queue, socket, pickle
from tkinter import *

# battleship class
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
        # True if all positions hit
        self.destroyed = False

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

class Network:
    def __init__(self):
        # info to connect
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "192.168.1.117"
        self.port = 5555
        self.addr = (self.server, self.port)
        self.id = self.connect()

    def connect(self):
        while True:
            try:
                self.client.connect(self.addr)
                return pickle.loads(self.client.recv(2048))
            except:
                print('error1')

    def send(self, data,player):
        try:
            data = [data, player]
            self.client.send(pickle.dumps(data))
        except socket.error:
            print('error2')

    def receive(self):
        try:
            data = pickle.loads(self.client.recv(2048))
            return data
        except socket.error:
            print('error3')

    def sendreceive(self):
        self.send(pickle.dumps('Reply'), self.id)
        data = self.receive()
        return data

# creates network instance
n = Network()

# creates queues
q = queue.Queue()
main_q = queue.Queue()

# waits to execute selection window until both clients connected
def connect_window():
    window = Tk()
    text = 'Waiting for connection'
    connection_label = Label(text = text)
    connection_label.pack()
    while True:
        status = n.sendreceive()
        if status == 'Ready':
            break
        window.update()
    print(n.id ,'connected')
    window.destroy()
    return

# creates list to store all ship objects
battleship_object_list = []

# centers windows
os.environ['SDL_VIDEO_CENTERED'] = '1'

# start pygame
pygame.init()

# load images
explosion_image = pygame.image.load('explosion.png')
hit_image = pygame.image.load('hit.png')
miss_image = pygame.image.load('splash.png')
ship_image_carrier = pygame.image.load('battleships carrier.png')
ship_image_large = pygame.image.load('battleships large.png')
ship_image_medium = pygame.image.load('battleships medium.png')
ship_image_small = pygame.image.load('battleships small.png')

# make new instance in class Battleship with each ship's image, size and starting positions and adds it to a list for iterating
new_ship = Battleship(ship_image_carrier,4,(1020, 0))
battleship_object_list.append(new_ship)
new_ship = Battleship(ship_image_large,3,(1020, 400))
battleship_object_list.append(new_ship)
new_ship = Battleship(ship_image_medium,2,(1100, 0))
battleship_object_list.append(new_ship)
new_ship = Battleship(ship_image_small,2,(1100, 400))
battleship_object_list.append(new_ship)

'''

Defining functions

'''

# resizes given image to given dimensions
def resize_image(image,dimensions):
    x = int(dimensions[0])
    y = int(dimensions[1])
    scale = (x,y)
    return pygame.transform.scale(image,scale)

# rotates given image by 90 degrees in given dir
def rotate_image(image,dir):
    if dir == 'clockwise':
        rotation = 90
    else:
        rotation = -90
    return pygame.transform.rotate(image, rotation)

# converts given coordinates in tuple to box coords, sf = size of box
def convert_to_box_pos(coords,sf):
    x = coords[0]
    y = coords[1]
    boxx = x // sf
    boxy = y // sf
    return (boxx,boxy)

# converts box coords to grid coords, size of each box is sf
def convert_from_box(coords,sf):
    boxx = coords[0]*sf
    boxy = coords[1]*sf
    return(boxx,boxy)

# runs in the background as a thread when thread created, receives signal 'placed' from server if all clients ships' placed
def receive_thread():
    while True:
        choose_ship_data = n.receive()
        q.put(choose_ship_data)
        if choose_ship_data == 'placed':
            break


# approximately centers ship position to center of boxes depending on ship size
def placed_location(coords,size,rotated):
    size = 5-size # inverts size
    x = coords[0]
    y = coords[1]
    if size != 1:
        if rotated:
            y = y + size*10
        else:
            x = x + size*10
    location = (x,y)
    return location

'''

Selection Window

'''
# executes first window where player selects ship locations
def choose_ship_pos():
    window = pygame.display.set_mode((1200, 1000))

    # create coordinates for grid with list comprehension
    lines = [i*100 for i in range(1,11)]

    exit_var = True

    selected = None
    placed_ships = {}

    # resize images
    for i in battleship_object_list:
        # changes size and rotation
        resized_ship_image = rotate_image(resize_image(i.id,i.resizeres),'clockwise')
        i.resizeid = resized_ship_image
        # this gets drawn when on right side of selection window
        selection_resize_image = rotate_image(resize_image(i.id,(300,75)),'clockwise')
        i.selectionid = selection_resize_image


    # makes fonts and font surfaces
    font_go = pygame.font.SysFont(pygame.font.get_default_font(), 70)
    font_waiting = pygame.font.SysFont(pygame.font.get_default_font(), 40)
    font_surface_go = font_go.render('GO!', True, (0,0,0))
    font_surface_waiting = font_waiting.render('WAITING', True, (0,0,0))

    placed = False

    started_thread = True

    sent = False

    '''
    
    Selection window loop
    
    '''

    # main game loop
    while exit_var:

        # white background
        window.fill((255,255,255))

        found = False

        # iterate through events
        for event in pygame.event.get():
            # check for quit
            if event.type == pygame.QUIT:
                exit_var = False
            # check for r keypress
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    try:
                        # toggle for rotating
                        if battleship_object_list[selected_pos_in_list].rotated:
                            selected.resizeid = rotate_image(selected.resizeid,'clockwise')
                            battleship_object_list[selected_pos_in_list].rotated = False
                        else:
                            selected.resizeid = rotate_image(selected.resizeid, 'anti clockwise')
                            battleship_object_list[selected_pos_in_list].rotated = True
                    except:
                        print('Select ship first')

        # draw lines for grid
        for x in lines:
            pygame.draw.line(window,(0,0,0),(x,0),(x,1000))
        for y in lines:
            pygame.draw.line(window, (0, 0, 0), (0, y), (1000, y))

        '''
        
        Drawing ships
        
        '''

        # iterates through every ship
        for i in range(len(battleship_object_list)):

            # draws green squares underneath ships
            for y in battleship_object_list[i].allpos:
                rect_grid_x, rect_grid_y = convert_from_box(y,100)
                rect_placement = (rect_grid_x+1, rect_grid_y+1, 99,99)
                pygame.draw.rect(window,(100,255,100),(rect_placement))

            # draws ship if it is selected
            if selected is not None:
                # if current ship is selected
                if selected.resizeid == battleship_object_list[i].resizeid:
                    # draw selected ship to mouse position
                    selected_pos = (pygame.mouse.get_pos()[0] - 65, pygame.mouse.get_pos()[1])
                    window.blit(selected.resizeid, selected_pos)

            # draws ship if it is placed
            if battleship_object_list[i] in placed_ships:
                placed_ships_location = placed_ships[battleship_object_list[i]]
                window.blit(battleship_object_list[i].resizeid,placed_ships_location)

            # draws ships on selection menu
            elif battleship_object_list[i] != selected:
                window.blit(battleship_object_list[i].selectionid,battleship_object_list[i].startpos)


        '''
        
        Mouse clicks
        
        '''

        # get mouse state, returns a tuple where it is true if pressed (left click, ?, rightclick)
        mouse_state = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # selecting ships
        if mouse_state[0]:

            # check if mouse pos == pos of rectangle over image
            for i in range(len(battleship_object_list)):
                if placed_ships.get(battleship_object_list[i]) is None:
                    # if mouse click is over rectangle, selects the ship
                    if pygame.Rect.collidepoint(battleship_object_list[i].rect,(mouse_pos)) == 1:
                        selected = battleship_object_list[i]
                        selected_pos_in_list = i
                        # selected_unrotated is ship at default angle
                        selected_unrotated = selected.resizeid

        # placing ship
        if mouse_state[0] and selected is not None:
            if mouse_pos[0] <= 1000:
                #get mouse box coords
                box_pos_mouse = convert_to_box_pos(mouse_pos,100)
                # grid coords
                grid_pos = convert_from_box(box_pos_mouse,100)

                # if NO SHIPS PLACED, get position of mouse
                if len(placed_ships) == 0:
                    # get all positions of ship
                    selected_check_pos = selected.create_pos(box_pos_mouse)
                    for i in selected_check_pos:
                        if i[0] < 0 or i[0] > 9 or i[1] < 0 or i[1] > 9:
                            found = True

                # get all individual placed ship box coords and if it equals any selected box coords, found = True
                # if ships have been placed
                else:
                    # search though ships
                    for i in battleship_object_list:
                        # search through each position of placed ships
                        for y in i.allpos:
                            # get all SELECTED ship positions
                            selected_check_pos = selected.create_pos(box_pos_mouse)
                            # search through each selected ship positions
                            for x in selected_check_pos:
                                # if y (a ship box position) == any selected ship box position:
                                if y == x:
                                    found = True

                    # checks position is not off boundaries
                    for i in selected_check_pos:
                        if i[0] < 0 or i[0] > 9 or i[1] < 0 or i[1] > 9:
                            found = True


                if not found:
                    # selected positions get changed to check positions
                    selected.allpos = selected_check_pos
                    #draw ship at box position
                    window.blit(selected.resizeid,grid_pos)
                    #add to dictionary (ship : position)
                    placed_ship_position = placed_location(grid_pos,selected.size,selected.rotated)
                    placed_ships[selected] = placed_ship_position
                    selected = None

        # deselect
        if mouse_state[2]:
            battleship_object_list[selected_pos_in_list].resizeid = selected_unrotated
            battleship_object_list[selected_pos_in_list].rotated = False
            selected = None


        # if all ships placed, end
        if len(placed_ships) == len(battleship_object_list):
            #draw rectangle for button
            go_button = pygame.draw.rect(window,(0,255,0),(1010,800,180,195))
            # draw go text
            window.blit(font_surface_go,(1045,870))
            ship_pos_send = []
            if mouse_state[0]:
                # if click is on go rectangle
                if pygame.Rect.collidepoint(go_button,(mouse_pos)):
                    for i in battleship_object_list:
                        # gets a list of all ships positions
                        ship_pos_send.append(i.allpos)
                    # prevents positions being sent twice
                    if not sent:
                        print(n.id,'sending',ship_pos_send)
                        sent = True
                        n.send(ship_pos_send,n.id)
                    placed = True
        if placed:
            # starts new thread so it can update window and receive data from server
            if started_thread:
                _thread.start_new_thread(receive_thread,())
                started_thread = False
            # retrieves data from queue sent by thread
            choose_ship_data = q.get()
            window.blit(font_surface_waiting,(1030,740))
            # if server sends 'placed' both clients have placed all ships
            if choose_ship_data == 'placed':
                # breaks from loop
                exit_var = False
        pygame.display.update()

def main_receive_thread():
    while True:
        try:
            data = n.receive()
            print('waiter received', data)
            main_q.put(data)
            if data[0] == 'won':
                break
        except:
            pass

def main_game():
    # make main window
    main_window = pygame.display.set_mode((1800,1000))

    # create gridline positions
    x_gridlines = [x * 90 for x in range(1, 11)]
    y_gridlines = [y * 90 for y in range(1, 21)]

    # gets ships' id for main window
    for i in battleship_object_list:
        i.mainid = rotate_image(resize_image(i.id, i.mainres), 'clockwise')

    # 1st player goes first
    if n.id == 1:
        turn = True
    else:
        turn = False

    # creates list for guessing positions
    hit_list = []
    miss_list = []
    enemy_hit_list = []
    enemy_miss_list = []

    enemy_ships = []
    own_ships = []

    # starts new thread to receive data from server
    _thread.start_new_thread(main_receive_thread, ())

    # creates your turn text surface
    font_turn = pygame.font.SysFont(pygame.font.get_default_font(), 70)
    font_turn_surface = font_turn.render('YOUR TURN',False,(255,0,0))

    main_exit_var = True

    # main game loop
    while main_exit_var:

        position_filled = False

        # white background
        main_window.fill((255, 255, 255))

        # iterate through events
        for event in pygame.event.get():
            # check for quit
            if event.type == pygame.QUIT:
                main_exit_var = False

        # draw grid
        for i in x_gridlines:
            pygame.draw.line(main_window, (0, 0, 0), (0, i), (2000, i))
        for i in y_gridlines:
            # creates bold y axis line to seperate 2 sides
            if i == 900:
                width = 3
            else:
                width = 1
            pygame.draw.line(main_window, (0, 0, 0), (i, 0), (i, 900),width)

        # draw all players ships
        for i in battleship_object_list:
            if not i.destroyed:
                # if y axis is the same at start and end of ship (ship is vertical) and ship hasnt been rotated
                if i.allpos[-1][1] == i.allpos[0][1] and not i.main_rotated:
                    # rotates image
                    i.mainid = rotate_image(i.mainid,'anti clockwise')
                    i.main_rotated = True
                coord = (i.allpos[0][0]*90, i.allpos[0][1]*90)
                main_window.blit(i.mainid,coord)

        # draw all hits and misses
        for i in hit_list:
                draw_hit_grid_pos = convert_from_box(i,90)
                draw_hit_grid_pos = (draw_hit_grid_pos[0] + 900, draw_hit_grid_pos[1])
                main_window.blit(hit_image,draw_hit_grid_pos)

        for i in miss_list:
            draw_miss_grid_pos = convert_from_box(i,90)
            draw_miss_grid_pos = (draw_miss_grid_pos[0]+900,draw_miss_grid_pos[1])
            main_window.blit(miss_image,draw_miss_grid_pos)

        for i in enemy_hit_list:
                draw_hit_grid_pos = convert_from_box(i,90)
                draw_hit_grid_pos = (draw_hit_grid_pos[0], draw_hit_grid_pos[1])
                main_window.blit(hit_image,draw_hit_grid_pos)

        for i in enemy_miss_list:
            draw_miss_grid_pos = convert_from_box(i,90)
            draw_miss_grid_pos = (draw_miss_grid_pos[0],draw_miss_grid_pos[1])
            main_window.blit(miss_image,draw_miss_grid_pos)

        # draw explosions
        for ship in enemy_ships:
            for y in ship:
                x_destroyed, y_destroyed = convert_from_box(y, 90)
                destroyed_ship_grid = (x_destroyed + 900, y_destroyed)
                main_window.blit(explosion_image, destroyed_ship_grid)

        for ship in own_ships:
            for y in ship:
                x_destroyed, y_destroyed = convert_from_box(y, 90)
                destroyed_ship_grid = (x_destroyed, y_destroyed)
                main_window.blit(explosion_image, destroyed_ship_grid)

        mouse_status = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # if it is the client's turn
        if turn:
            # draw your turn text
            main_window.blit(font_turn_surface,(200,905))
            if mouse_status[0]:
                if mouse_pos[0]>900:
                    # convert mouse pos to box pos
                    mouse_box_pos = convert_to_box_pos(mouse_pos,90)
                    for i in hit_list:
                        if i == mouse_box_pos:
                            position_filled = True

                    for i in miss_list:
                        if i == mouse_box_pos:
                            position_filled = True

                    if not position_filled:
                        # takes away 10 from grid to compensate for click on right half of screen
                        mouse_box_pos_send = (mouse_box_pos[0]-10,mouse_box_pos[1])
                        # sends data
                        n.send(mouse_box_pos_send,n.id)
                        # receives data from thread
                        data = main_q.get()
                        # if server send back hit, add coords to hit list
                        if data[1] == 'hit':
                            hit_list.append(data[0])
                        # if server send back miss, add coords to miss list
                        elif data[1] == 'miss':
                            miss_list.append(data[0])
                        elif data[1] == 'destroy':
                            enemy_ships.append(data[0])
                            hit_list.append(data[2])
                        elif data[0] == 'won':
                            pygame.display.quit()
                            return data[1]

                        # stops turn
                        turn = False
                        print(n.id, 'stopping turn')

        # if its not the player's turn
        else:
            if not main_q.empty():
                data = main_q.get()
                if data[1] == 'hit':
                    enemy_hit_list.append(data[0])
                elif data[1] == 'miss':
                    enemy_miss_list.append(data[0])
                elif data[1] == 'destroy':
                    for i in battleship_object_list:
                        if i.allpos == data[0]:
                            i.destroyed = True
                            enemy_hit_list.append(data[2])
                            own_ships.append(data[0])
                elif data[0] == 'won':
                    pygame.display.quit()
                    return data[1]


                turn = True
                print(n.id, 'starting turn')

        pygame.display.update()

connect_window()
choose_ship_pos()
winner = main_game()
if winner == n.id:
    did_win = 'You won!'
else:
    did_win = 'You lost!'

winner_window = Tk()
winner_label = Label(text=did_win)
winner_label.pack()
winner_label.mainloop()
