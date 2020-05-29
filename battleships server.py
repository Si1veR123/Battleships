import socket, pickle, time, queue
from _thread import *

server = "192.168.1.117" #local ip
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port)) # connect ip with socket initialization
except socket.error:
    print('Error1')

s.listen(1) # wait for connections
print("Waiting for a connection, Server Started")



def threaded_client(conn_dict,p,a,q,q2): # send and recieve data once connected
    conn = conn_dict[p]
    try:
        conn.send(pickle.dumps(p)) # send player id
        connected = False

        while not connected:
            pickle.loads(conn.recv(2048))
            if len(conn_dict) >= 2:
                # allows client script to catch up
                time.sleep(0.5)
                conn.send(pickle.dumps('Ready'))
                connected = True
                print('2 players connected')
            else:
                conn.send(pickle.dumps('Not ready'))

        placed = False

        if p == 1:
            other_conn = conn_dict[2]
        elif p == 2:
            other_conn = conn_dict[1]

        place_data = pickle.loads(conn.recv(2048))
        # while ships are being placed
        while not placed:
            # checks which thread is running which player
            if p == 1:
                p_pos = place_data[0]
                # put player 1 pos in queue to be received by other thread
                q.put(p_pos)

            elif p == 2:
                p2_pos = place_data[0]
                # put player 2 pos in queue to be received by other thread
                q2.put(p2_pos)

            if not q.empty() and not q2.empty():
                conn.send(pickle.dumps('placed'))
                p_pos = q.get()
                p2_pos = q2.get()
                # places its coords back into queue for the other thread to get
                if p ==1:
                    q.put(p_pos)
                else:
                    q2.put(p2_pos)
                placed = True
            else:
                conn.send(pickle.dumps('waiting'))
            time.sleep(2)

        ship_hit_list = []
        ship_hit_list_2 = []
        # add empty lists for each ship
        for i in range(len(p_pos)):
            ship_hit_list.append([])
            ship_hit_list_2.append([])

        while True:
            won_p = True
            won_p2 = True
            destroyed = False
            has_hit = 'miss'
            data = pickle.loads(conn.recv(2048)) # receive data

            # if its player 1's turn
            if data[1] == 1:
                search_list = p2_pos
            else:
                search_list = p_pos

            if p == data[1]:
                # search through other player ships
                for num, ship in enumerate(search_list):
                    # search through each ships' position
                    for pos in ship:
                        # if position is equal to guess
                        if pos == data[0]:
                            has_hit = 'hit'

                            if data[1] == 1:
                                ship_hit_list_2[num].append('hit')
                            else:
                                ship_hit_list[num].append('hit')

                    # if length of the current ship is equal to length of corresponding ship in ship_hit_list
                    if len(ship) == len(ship_hit_list[num]):
                        destroyed = True
                        destroyed_ship = p_pos[num]
                        ship_hit_list[num].append('finished')

                    elif len(ship) == len(ship_hit_list_2[num]):
                        destroyed = True
                        destroyed_ship = p2_pos[num]
                        ship_hit_list_2[num].append('finished')

                # if there is a destroyed ship
                if destroyed:
                    print(destroyed_ship, 'destroyed')
                    # send the ships' positions
                    send_data = (destroyed_ship,'destroy',data[0])
                    destroyed_ship = None
                # else, send position and if it has been hit
                else:
                    send_data = (data[0],has_hit)

                for i in ship_hit_list:
                    if len(i) > 0:
                        if i[-1] != 'finished':
                            won_p2 = False
                    else:
                        won_p2 = False

                for i in ship_hit_list_2:
                    if len(i) > 0:
                        if i[-1] != 'finished':
                            won_p = False
                    else:
                        won_p = False

                if won_p:
                    send_data = ('won', 1)

                elif won_p2:
                    send_data = ('won', 2)

                print('sending', send_data)
                conn.send(pickle.dumps(send_data))
                other_conn.send(pickle.dumps(send_data))

    except error as e:
        print(e)
        del conn_dict[p]
        print('Disconnecting from: ', a)
        conn.close()

player = 1
conn_dict = {}
q = queue.Queue()
q2 = queue.Queue()
while True:
    conn, addr = s.accept() # get connection data from client
    conn_dict[player] = conn # saves player num : connection info in dictionary
    print("Connected to:", addr)
    start_new_thread(threaded_client, (conn_dict,player,addr,q,q2)) # new thread for client
    player += 1