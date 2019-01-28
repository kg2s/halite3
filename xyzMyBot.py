#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
import math
import statistics 
import queue

from collections import defaultdict


from hlt import constants
from hlt import positionals
#from hlt import Position
from hlt.positionals import Direction,Position

import random
import logging

def my_calculate_distance(source, target):
        """
        Compute the straight distance between two locations.
        Accounts for wrap-around.
        :param source: The source from where to calculate
        :param target: The target to where calculate
        :return: The distance between these items
        """
        dx= (source.x - target.x)
        dy= (source.x - target.x)
        return( math.sqrt( dx*dx + dy*dy ))
#********************************************************************************************************************        
def _get_target_direction(source, target):
    """
    Returns where in the cardinality spectrum the target is from source. e.g.: North, East; South, West; etc.
    NOTE: Ignores toroid
    :param source: The source position
    :param target: The target position
    :return: A tuple containing the target Direction. A tuple item (or both) could be None if within same coords
    """
    return (Direction.South if target.y > source.y else Direction.North if target.y < source.y else None,
            Direction.East if target.x > source.x else Direction.West if target.x < source.x else None)
            
#********************************************************************************************************************        
def get_unsafe_moves(game_map, source, destination):
    """
    Return the Direction(s) to move closer to the target point, or empty if the points are the same.
    This move mechanic does not account for collisions. The multiple directions are if both directional movements
    are viable.
    :param source: The starting position
    :param destination: The destination towards which you wish to move your object.
    :return: A list of valid (closest) Directions towards your target.
    """
    possible_moves = []
    #distance = abs(destination - source)
    distance = Position(abs(destination.x-source.x),abs(destination.y-source.y))
    y_cardinality, x_cardinality = _get_target_direction(source, destination)

    if distance.x != 0:
        possible_moves.append(x_cardinality if distance.x < (game_map.width / 2)
                              else Direction.invert(x_cardinality))
    if distance.y != 0:
        possible_moves.append(y_cardinality if distance.y < (game_map.height / 2)
                              else Direction.invert(y_cardinality))

    return possible_moves
    
#********************************************************************************************************************        
def get_surrounding_cardinals(pos):
    """
    :return: Returns a list of all positions around this specific position in each cardinal direction
    """
    return [pos.directional_offset(current_direction) for current_direction in Direction.get_all_cardinals()]
#********************************************************************************************************************
def my_navigate(game_map, ship, destination,safe_map,move_pos):
    """
    Returns a singular safe move towards the destination.
    :param ship: The ship to move.
    :param destination: Ending position
    :return: A direction.
    """

    min=10000
    min_dir =Direction.Still
    min_pos=ship.position
    #logging.info("my_navigate {}".format(min_pos.x))
    for direction in get_unsafe_moves(game_map,ship.position, destination):

        target_pos = game_map.normalize(ship.position.directional_offset(direction))
        
        if  target_pos not in mov_pos and safe_map[target_pos.y][target_pos.x] < 1 and game_map[target_pos].halite_amount <= min:
            min=game_map[target_pos].halite_amount

            min_dir = direction
            min_pos= target_pos


    if (game_map[min_pos].halite_amount  == 0 or ship.is_full) and min_dir==Direction.Still:
        min_dir= get_move(ship,game_map,safe_map)                

    return min_dir


def my_navigate_to(game_map, ship, destination,safe_map,mov_pos):
    """
    Returns a singular safe move towards the destination.
    :param ship: The ship to move.
    :param destination: Ending position
    :return: A direction.
    """

    max=-1
    max_dir =Direction.Still
    max_pos=ship.position
    for direction in get_unsafe_moves(game_map,ship.position, destination):
        target_pos = game_map.normalize(ship.position.directional_offset(direction))
        if  target_pos not in mov_pos and safe_map[target_pos.y][target_pos.x] <1 and game_map[target_pos].halite_amount > max:         
            max=game_map[target_pos].halite_amount

            max_dir = direction
            max_pos=target_pos

    
    if game_map[max_pos].halite_amount  == 0 and max_dir==Direction.Still:
        max_dir= get_move_d(ship,game_map,safe_map)        

    return max_dir
    #return Direction.Still
#*************************************************************************************************************
def get_move(ship,game_map,safe_map):
    r=1        
    max = 0
    pos = ship.position 
    all_pos = get_surrounding_cardinals(pos)
    max_dir =Direction.Still

    
    for p in all_pos:

        distance = Position(abs(p.x-pos.x),abs(p.y-pos.y))
        y_cardinality, x_cardinality = _get_target_direction(pos, p)
        p=game_map.normalize(p)
        if safe_map[p.y][p.x] < 1:
            #max_pos = p
            if distance.x != 0:
                max_dir = (x_cardinality if distance.x < (game_map.width / 2)
                              else Direction.invert(x_cardinality))
            if distance.y != 0:
                max_dir=(y_cardinality if distance.y < (game_map.height / 2)
                              else Direction.invert(y_cardinality))
            #return max_dir




    return max_dir
#*************************************************************************************************************
def get_move_d(ship,game_map,safe_map):
    r=1        
    max = 0
    pos = ship.position 
    all_pos = get_surrounding_cardinals(pos)
    max_dir =Direction.Still

    
    for p in all_pos:

        distance = Position(abs(p.x-pos.x),abs(p.y-pos.y))
        y_cardinality, x_cardinality = _get_target_direction(pos, p)
        p=game_map.normalize(p)
        if safe_map[p.y][p.x] < 1 and game_map[p].halite_amount >= max:
            max = game_map[p].halite_amount
            if distance.x != 0:
                max_dir = (x_cardinality if distance.x < (game_map.width / 2)
                              else Direction.invert(x_cardinality))
            if distance.y != 0:
                max_dir=(y_cardinality if distance.y < (game_map.height / 2)
                              else Direction.invert(y_cardinality))
            #return max_dir

    return max_dir
#*************************************************************************************************************
def get_move_max(ship,game_map,safe_map,other_ships):
    r=1        
    max = 0.25*game_map[ship.position].halite_amount
    pos = ship.position 
    all_pos = get_surrounding_cardinals(pos)
    max_dir =None
    pct=0.35
    if game_map.width >40:
        pct=0.4
    if ship.halite_amount < 0.1*game_map[ship.position].halite_amount:
        return max_dir
    for p in all_pos:

        distance = Position(abs(p.x-pos.x),abs(p.y-pos.y))
        y_cardinality, x_cardinality = _get_target_direction(pos, p)
        p=game_map.normalize(p)
        if game_map[p].halite_amount < 50:
            continue

        if is_inspired(p,other_ships):
            new_amt=0.5*game_map[p].halite_amount - pct*game_map[ship.position].halite_amount 
        else:
            new_amt=0.25*game_map[p].halite_amount - pct*game_map[ship.position].halite_amount
        if safe_map[p.y][p.x] !=2 and (new_amt) > max:
            #max_pos = p
            max=new_amt
            if distance.x != 0:
                max_dir = (x_cardinality if distance.x < (game_map.width / 2)
                              else Direction.invert(x_cardinality))
            if distance.y != 0:
                max_dir=(y_cardinality if distance.y < (game_map.height / 2)
                              else Direction.invert(y_cardinality))
            #return max_dir

    return max_dir

#*************************************************************************************************************
def get_new_move2(game_map,ship,search_rad,safe_map,target_pos):

    r_max= math.ceil(0.25*game_map.width )
    pos = ship.position 
    max = 0
    max_pos=pos
    max_gain = -10000
    gain=0
    rx = random.randint( search_rad,r_max+1)
    ry = random.randint( search_rad,r_max+1)

    # rx=r_max
    # ry=r_max

    startx = pos.x - rx 
    endx = pos.x + rx
    starty = pos.y - ry
    endy = pos.y + ry

    
    for i in range(startx, endx):
        for j in range(starty, endy):
            p=game_map.normalize(Position(i,j))
            #gain= get_amt(p,game_map)
            if 0.25*game_map[p].halite_amount > 3*(constants.MAX_HALITE- ship.halite_amount):
                continue
            if p != pos and not game_map[p].is_occupied:
                #d = game_map.calculate_distance(p, pos)             
                gain= game_map[p].halite_amount#/d
                if gain > max_gain  and safe_map[p.y][p.x] !=2:                 
                    max_gain = gain
                    max_pos = p

    target_pos.append(max_pos)    
    return max_pos
#*************************************************************************************************************
def get_new_move(game_map,ship,safe_map,top_pos,other_ships):

    md=1000
    pos=ship.position
    max_pos=None
    max_gain=0
    if (len(top_pos)<1):
        return None
    for p in top_pos:
        p2=p[0]
        if p2==pos:
            continue
        d=game_map.calculate_distance(p2, pos)# + game_map.calculate_distance(p2,get_drop_point(me,game_map,ship))
        if d > 15:
            continue
        if d < md and safe_map[p2.y][p2.x] !=2:
            md = d
            max_pos=p2
            #max_gain=gain
            p1=p
    if (max_pos is None):
        return None
    if max_pos !=pos:
        top_pos.remove(p1)
    return max_pos
#*************************************************************************************************************
def get_drop_point(me,game_map,ship):
    min=100
    min_point = me.shipyard.position
    
    for dropoff in me.get_dropoffs():
        dist=game_map.calculate_distance(ship.position, dropoff.position)
        if dist < min:# and not surrounded(game_map,dropoff.position):
            min= dist
            min_point = dropoff.position
    
    if game_map.calculate_distance(ship.position, me.shipyard.position) < game_map.calculate_distance(ship.position, min_point):
        return me.shipyard.position
    else:
        return min_point
#*************************************************************************************************************
def is_dropoff(ship,me):
    
    for dropoff in me.get_dropoffs():
        if ship.position==dropoff.position:
            return True
            
    return False
#*************************************************************************************************************
def surrounded(game_map,pos):
    
    s=True
    all_pos = get_surrounding_cardinals(pos)
    for p in all_pos:
        p=game_map.normalize(p)
        if not game_map[p].is_occupied:
            s=False
            
    return s
#*************************************************************************************************************
def enemy_next(game_map,pos,other_ships):
    
    s=False
    all_pos = get_surrounding_cardinals(pos)
    for p in all_pos:
        p=game_map.normalize(p)
        if other_ships[p.y][p.x]==1:
            s=True
            
    return s
#*************************************************************************************************************
def get_amt(pos,game_map):
#get amount of halite available in a radius
    r=2  
    #pos = ship.position
    sum =0
    for i in range(pos.x - r, pos.x + r+1):
        for j in range(pos.y - r, pos.y + r+1):
            nor_pos=game_map.normalize(Position(i,j))
            sum=game_map[nor_pos].halite_amount + sum
          
    return sum
#*************************************************************************************************************
def is_inspired(pos,other_ships):
#Check for inspiration
    r=4  
    #pos = ship.position
    num =0
    for i in range(pos.x - 4, pos.x + 4+1):
        d= 4-abs(pos.x-i)
        for j in range(pos.y - d, pos.y + d+1):
            p=game_map.normalize(Position(i,j))
            if other_ships[p.y][p.x]==1:
                num=num+1
        if num >1:
            return True
    
    return False
#*************************************************************************************************************
def get_total_amt(game_map,other_ships):
#Get current high halite squares and total available
    total=0
    m=[]
    loc=1
    #halite_amout = [[c.halite_amount for c in row] for row in game_map._cells]
    #total = sum(map(sum, halite_amout))
    for i in range(0, game_map.width):
        for j in range(0,game_map.height):            
            total=game_map[Position(i,j)].halite_amount + total
            if not game_map[Position(i,j)].is_occupied and game_map[Position(i,j)].halite_amount>50:
                if  is_inspired(Position(i,j),other_ships):
                    m.append([Position(i,j),0.5*game_map[Position(i,j)].halite_amount])
                else:
                    m.append([Position(i,j),0.25*game_map[Position(i,j)].halite_amount])
            loc=loc+1
    ms= sorted(m, key = lambda x: x[1],reverse=True)      
    
    #logging.info("top {} ".format(ms[0]))
    return total,ms
#*************************************************************************************************************
def get_total_amt1(game_map):
#Get current high halite squares and total available
    total=0
    m=[]
    loc=1
    #halite_amout = [[c.halite_amount for c in row] for row in game_map._cells]
    #total = sum(map(sum, halite_amout))
    for i in range(0, game_map.width):
        for j in range(0,game_map.height):            
            total=game_map[Position(i,j)].halite_amount + total
            if not game_map[Position(i,j)].is_occupied and game_map[Position(i,j)].halite_amount>100:
                m.append([Position(i,j),game_map[Position(i,j)].halite_amount])
            loc=loc+1
    ms= sorted(m, key = lambda x: x[1],reverse=True)      
    
    #logging.info("top {} ".format(ms[0]))
    return total,ms
#*************************************************************************************************************    
# This game object contains the initial game state.
game = hlt.Game()
total,tops = get_total_amt1(game.game_map)
average = total/(game.game_map.width*game.game_map.width)
# Respond with your name.
game.ready("xyzBot v2.185")
ship_status = {}
ship_move = {}
blocker=1
left_frac = 5
go_home = defaultdict(lambda: False)
leave_amt = defaultdict(lambda: average/(4-(game.game_map.width/32)))
#leave_amt = defaultdict(lambda:80)
go_middle = defaultdict(lambda: False)
Reached_MaxShips = False
spawn_ships=False
return_amt= 0.92*constants.MAX_HALITE
MAX_SHIPS= game.game_map.width
num_drop=math.floor(game.game_map.width/16)
num_players = len(game.players.values())
logging.info("total {} ".format(total))
logging.info("average {} ".format(average))
crash_amt = 550
kill_rad = 2
if num_players == 4:# and game.game_map.width < 45:
    crash_amt = 850
crash_amt = 950
if num_players == 2:# and game.game_map.width < 45:
    crash_amt = 850

if game.game_map.width ==32:
    stop_ship_turn=constants.MAX_TURNS*0.5

if game.game_map.width ==40:
    stop_ship_turn=constants.MAX_TURNS*0.5

if game.game_map.width ==48:
    stop_ship_turn=constants.MAX_TURNS*0.5

if game.game_map.width ==56:
    stop_ship_turn=constants.MAX_TURNS*0.55
    
if game.game_map.width ==64:
    stop_ship_turn=constants.MAX_TURNS*0.6
    switch_move=constants.MAX_TURNS*0.75


while True:
    game.update_frame()
    me = game.me  # Here we extract our player metadata from the game state
    game_map = game.game_map  # And here we extract the map metadata
    #other_players = [p for pid, p in game.players.values() if pid != game.my_id]

    command_queue = []
    other_players=[]
    for p in game.players.values():
        if p.id != game.my_id:
            other_players.append(p)
    
    spawn_ships=False
    reserve_amt=constants.SHIP_COST
        
    if len(me.get_dropoffs()) < num_drop:
        mydrop_off = False        
    else:
        mydrop_off = True   
    
    #drop_off = False
    
    if (game.turn_number > 0.5*constants.MAX_TURNS and game_map.width < 41):    
        return_amt= 0.85*constants.MAX_HALITE
    
    if (game.turn_number > 0.5*constants.MAX_TURNS and game_map.width > 41):    
        return_amt= random.uniform(0.89,0.93)*constants.MAX_HALITE

    if (game.turn_number > 0.8*constants.MAX_TURNS ):    
        return_amt= 0.995*constants.MAX_HALITE


    #if not Reached_MaxShips:
    if game.turn_number%25==0:
        MAX_SHIPS = MAX_SHIPS*(1+0.05*len(me.get_dropoffs()))

    spawn_drop=False    
    safe_map=[]
    other_ships=[]
    num_other_ships=[]
    #get safe/occupied spots
    safe_map=[x[:] for x in [[0] * game_map.width] * game_map.height]
    other_ships=[x[:] for x in [[0] * game_map.width] * game_map.height]
            
    for p in other_players:
        num_other_ships.append( len(p.get_ships()))
        for sp in p.get_ships():
            other_ships[sp.position.y][sp.position.x]=1
            if(game_map.calculate_distance(sp.position,me.shipyard.position) < kill_rad) or sp.halite_amount > crash_amt:
                safe_map[sp.position.y][sp.position.x]=0

            if(sp.position==get_drop_point(me,game_map,sp)):
                safe_map[sp.position.y][sp.position.x]=0
            else:
                safe_map[sp.position.y][sp.position.x]=3
                if game.turn_number > constants.MAX_TURNS*0.25 and game.turn_number < constants.MAX_TURNS*0.92:
                    if(my_calculate_distance(sp.position,get_drop_point(me,game_map,sp)) > 3):
                        for tps in get_surrounding_cardinals(sp.position):
                            tp1=game_map.normalize(tps)
                            safe_map[tp1.y][tp1.x]=1
            if (game.turn_number > 0.75*constants.MAX_TURNS ) and (game_map.calculate_distance(sp.position,me.shipyard.position) < 4):
                safe_map[sp.position.y][sp.position.x]=0
        
    for sp in me.get_ships():  
        safe_map[sp.position.y][sp.position.x]=0
        if sp.halite_amount < math.ceil(game_map[sp.position].halite_amount*0.1):
            safe_map[sp.position.y][sp.position.x]=1        
              
 #Sort the ships.
    ships=[]
    temp = me.get_ships()
    for ship in temp:
        if ship.halite_amount < math.ceil(game_map[ship.position].halite_amount*0.1):
            ships.append(ship)
            temp.remove(ship)
            
    for ship in temp:
        if surrounded(game_map,ship.position):
            ships.append(ship)
            temp.remove(ship)        

    for ship in temp:
        if go_home[ship.id]:
            ships.append(ship)
            temp.remove(ship)  
            
    for ship in temp:
        ships.append(ship)
        
    ctotal,tops = get_total_amt(game_map,other_ships)
    caverage = ctotal/(game_map.width*game_map.width)
    percent_taken = (total-ctotal)/total
    logging.info("total {} left {}".format(ctotal,percent_taken))
    logging.info("average {} ".format(caverage))
    
    if len(tops) > len(me.get_ships())+15:
        tp=tops[0:len(me.get_ships())+10]        
    else:
        tp=tops



    mov_pos=[]
    target_pos=[]
    count =0

    for ship in ships:  # For each of the ships   
        
        count = count + 1
        
        if  leave_amt[ship.id] > caverage:
            leave_amt[ship.id]=random.uniform(0.6,0.9)*caverage
        if (game.turn_number > 0.55*constants.MAX_TURNS ):    
            leave_amt[ship.id]=random.uniform(0.5,0.9)*caverage
        if (game.turn_number > 0.85*constants.MAX_TURNS ):    
            leave_amt[ship.id]=random.uniform(0.1,0.7)*caverage

        if (game.turn_number > 0.88*constants.MAX_TURNS and game_map.width < 41 ):    
            leave_amt[ship.id]=random.random()*caverage*.6    

        if (caverage < 15 and game_map.width < 41 ):    
            leave_amt[ship.id]=1    

        leave= leave_amt[ship.id]
        if game.turn_number > constants.MAX_TURNS*0.82 and ship.halite_amount >= 0.9*constants.MAX_HALITE:
            leave=5

        if is_inspired(ship.position,other_ships):
            leave=leave*0.25

        # Tell ships to leave dropoff and go back to searching
        if go_home[ship.id] and (ship.position == me.shipyard.position or is_dropoff(ship,me)):
            go_home[ship.id] = False            
            movement = get_move_d(ship,game_map,safe_map)
            pos = game_map.normalize(ship.position.directional_offset(movement))
            safe_map[pos.y][pos.x] = 2
            mov_pos.append(pos)
            command_queue.append(ship.move(movement))
            logging.info("get off dropoff {} from {} x {} to {} x {}".format(ship.id, ship.position.x,ship.position.y,pos.x,pos.y))   
            continue
            

        #end of game returns
        if game.turn_number > constants.MAX_TURNS*0.92 and ship.halite_amount >= 0.3*constants.MAX_HALITE and num_players==2:
                go_home[ship.id] = True
        if game.turn_number > constants.MAX_TURNS*0.88 and ship.halite_amount >= 0.2*constants.MAX_HALITE and num_players==4:
                go_home[ship.id] = True

        if game.turn_number > constants.MAX_TURNS*0.95 and ship.halite_amount >= 0.005*constants.MAX_HALITE:
                go_home[ship.id] = True
                                
        #create dropoffs
        if not mydrop_off :
            if ship.position.y != 0 and ship.position.x != 0 and ship.position.x != game_map.width-1 and ship.position.y != game_map.width-1:
                if ctotal > 100000 and (game.turn_number < constants.MAX_TURNS*0.65 ):
                    if game_map.calculate_distance(ship.position, get_drop_point(me,game_map,ship)) > 0.35*game_map.width and (me.halite_amount+ship.halite_amount+game_map[ship.position].halite_amount) > 4100 and (get_amt(ship.position,game_map)) > 18*average: 
                        if len(me.get_dropoffs()) < num_drop :
                            mydrop_off = True 
                            spawn_drop=True                    
                            command_queue.append(ship.make_dropoff())
                            continue

        #ship is returning to dropoff       
        if go_home[ship.id] :
            drop_here=get_drop_point(me,game_map,ship)
            #logging.info("dropoff {}x{}".format(drop_here.x,drop_here.y))
            #crash at the end
            if game_map.calculate_distance(ship.position, drop_here) == 1 and game_map[drop_here].is_occupied and  game.turn_number > 0.92*constants.MAX_TURNS:
                bad_move =game_map.get_unsafe_moves(ship.position, drop_here)
                command_queue.append(ship.move(bad_move[0]))       
                logging.info("Crashing Ship {}".format(ship.id))
            else:
                

                movement =my_navigate(game_map,ship, drop_here,safe_map,mov_pos)
                pos = game_map.normalize(ship.position.directional_offset(movement))
                if movement is not None and safe_map[pos.y][pos.x] < 1:
                    safe_map[pos.y][pos.x] = 2
                    command_queue.append(ship.move(movement))
                    mov_pos.append(pos)
                    logging.info("Returning {} from: ({}, {}) to {} x {}".format(ship.id, ship.position.x,ship.position.y,pos.x,pos.y))
                else:
                    if(safe_map[ship.position.y][ship.position.x] >1):
                        ml_move = get_move(ship,game_map,safe_map)
                        #movement =my_navigate(game_map,ship, ml_move)
                        pos = game_map.normalize(ship.position.directional_offset(ml_move))
                        safe_map[pos.y][pos.x] = 2
                        mov_pos.append(pos)
                        command_queue.append(ship.move(ml_move))
                        logging.info("return escaping1 {} from {} x {} to {} x {}".format(ship.id, ship.position.x,ship.position.y,pos.x,pos.y))   
                    else:
                        logging.info("Return stay still {} Loc: ({}, {})".format(ship.id, ship.position.x,ship.position.y))
                        safe_map[ship.position.y][ship.position.x] = 2
                        mov_pos.append(ship.position)
                        ship.stay_still()
            continue
        
        #Go home
        if ship.halite_amount > 900 and 0.25*game_map[ship.position].halite_amount < 10 and go_home[ship.id] == False:
            go_home[ship.id] = True

        if ship.halite_amount > return_amt and go_home[ship.id] == False:
            go_home[ship.id] = True
        
        

        if go_home[ship.id]:
            movement =my_navigate(game_map,ship, get_drop_point(me,game_map,ship),safe_map,mov_pos)
            pos = game_map.normalize(ship.position.directional_offset(movement))
            if movement is not None and safe_map[pos.y][pos.x] <1:
                logging.info("Return Ship {} to {} x {}".format(ship.id, pos.x, pos.y))
                safe_map[pos.y][pos.x] = 2
                mov_pos.append(pos)
                command_queue.append(ship.move(movement))
            else:
                logging.info("Return Ship {} wait".format(ship.id))
                safe_map[ship.position.y][ship.position.x] = 2
                mov_pos.append(ship.position)
                ship.stay_still()
            continue

        search_rad = 2
        #search_rad = random.randint( 1,6)
            
        ml_move = None  
        # get a move
        alt_move=get_move_max(ship,game_map,safe_map,other_ships)
        if (game_map[ship.position].halite_amount < leave) or  alt_move is not None:# or ship.halite_amount > 0.85*constants.MAX_HALITE):
            if alt_move is None:
                ml_move = get_new_move(game_map,ship,safe_map,tp,other_ships)
                if ml_move is None:
                    ml_move = get_new_move2(game_map,ship,search_rad,safe_map,target_pos)
                logging.info("Moving Ship {}: {}x{}, Target {}x{}".format(ship.id,ship.position.x,ship.position.y,ml_move.x,ml_move.y))
            else:
                 ml_move=game_map.normalize(ship.position.directional_offset(alt_move))
                 logging.info("Moving Ship Alt {}: {}x{}-{}, Target {}x{}-{}".format(ship.id,ship.position.x,ship.position.y,game_map[ship.position].halite_amount,ml_move.x,ml_move.y,game_map[ml_move].halite_amount))
            if game.turn_number > constants.MAX_TURNS*0.82 and ship.halite_amount >= 0.9*constants.MAX_HALITE:
                ml_move=game_map.normalize(get_drop_point(me,game_map,ship))
               
        else:
            if ml_move is None and game_map[ship.position].halite_amount ==0:
                movement = get_move_d(ship,game_map,safe_map)
                pos = game_map.normalize(ship.position.directional_offset(movement))           
                safe_map[pos.y][pos.x] = 2
                mov_pos.append(pos)
                command_queue.append(ship.move(movement))
                continue
            else:
                ml_move = None
            logging.info("Moving Ship {}: {}x{}, No move amt:{} leave:{}".format(ship.id,ship.position.x,ship.position.y,game_map[ship.position].halite_amount,leave))
            
        

        if ml_move is not None:
            movement =my_navigate_to(game_map,ship, ml_move,safe_map,mov_pos)
            if game.turn_number > constants.MAX_TURNS*0.82 and ship.halite_amount >= 0.9*constants.MAX_HALITE:
                movement =my_navigate(game_map,ship, ml_move,safe_map,mov_pos)

            pos = game_map.normalize(ship.position.directional_offset(movement))

            if movement is not None and ship.halite_amount >= game_map[ship.position].halite_amount*0.1 and safe_map[pos.y][pos.x] <1:
                safe_map[pos.y][pos.x] = 2
                logging.info("Moving Ship {} from {} x {} to {} x {}".format(ship.id, ship.position.x,ship.position.y,pos.x,pos.y))
                #game_map[ship.position.directional_offset(movement)].mark_unsafe(ship)
                mov_pos.append(pos)
                command_queue.append(ship.move(movement))
                continue
        
        if(enemy_next(game_map,pos,other_ships) and ship.halite_amount > 200):
            ml_move = get_move(ship,game_map,safe_map)
            pos = game_map.normalize(ship.position.directional_offset(ml_move))
            safe_map[pos.y][pos.x] = 2
            mov_pos.append(pos)
            command_queue.append(ship.move(ml_move))
            logging.info("Escaping {} from enemy {} x {} to {} x {}".format(ship.id, ship.position.x,ship.position.y,pos.x,pos.y))        
            continue  

        if(safe_map[ship.position.y][ship.position.x] >1):
            ml_move = get_move(ship,game_map,safe_map)
            pos = game_map.normalize(ship.position.directional_offset(ml_move))
            safe_map[pos.y][pos.x] = 2
            mov_pos.append(pos)
            command_queue.append(ship.move(ml_move))
            logging.info("Escaping3 {} from {} x {} to {} x {}".format(ship.id, ship.position.x,ship.position.y,pos.x,pos.y))        
            continue
        else:
            logging.info("Stay3 {} on {} x {}".format(ship.id, ship.position.x,ship.position.y))
            mov_pos.append(ship.position)
            safe_map[ship.position.y][ship.position.x] = 2
            ship.stay_still()
            continue
        
        
                
        
        
          
    # Spawn some more ships
    if len(me.get_ships()) > MAX_SHIPS:
        Reached_MaxShips = True
    

    if (ctotal > 75000 and game.turn_number < stop_ship_turn) and me.halite_amount >= reserve_amt and len(me.get_ships()) <= MAX_SHIPS:
        if(safe_map[me.shipyard.position.y][me.shipyard.position.x] < 1):
            spawn_ships=True
           
    if num_players ==2:        
        if  game.turn_number < 0.8*constants.MAX_TURNS and ctotal>50000 and len(me.get_ships()) - max(num_other_ships) < 3 :
            spawn_ships=True
        if len(me.get_ships()) - max(num_other_ships) > 18 :
            spawn_ships=False 

    if num_players ==4:
        if game.turn_number < 0.75*constants.MAX_TURNS and ctotal>100000 and len(me.get_ships()) - max(num_other_ships) < -5 :
            spawn_ships=True
        if game.turn_number < 0.7*constants.MAX_TURNS and ctotal>20000 and game_map.width < 41 and len(me.get_ships()) - max(num_other_ships) < -5 :
            spawn_ships=True
        if len(me.get_ships()) - max(num_other_ships) > 15 :
            spawn_ships=False 
            
    if game.turn_number < 0.8*constants.MAX_TURNS and ctotal>10000 and len(me.get_ships())< 10 :
        spawn_ships=True
    
    if spawn_drop:
        spawn_ships=False    
                 
    if spawn_ships and (safe_map[me.shipyard.position.y][me.shipyard.position.x] < 1)and me.halite_amount >= reserve_amt:
        command_queue.append(game.me.shipyard.spawn())

    game.end_turn(command_queue)  # Send our moves back to the game environment
