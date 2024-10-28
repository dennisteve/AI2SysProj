# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 16:30:39 2024

@author: Dennis
"""
import numpy as np
import random

def get_neighbours(x, y): # 'S', 'N', 'W', 'E'
    return [(x+1, y), (x-1, y), (x, y-1), (x, y+1)]
    
def moveWumpus(grid, move, posX, posY):
    if (move == 'N'): 
        if (grid[posX - 1,posY] != 'X'): posX -= 1
    if (move == 'E'): 
        if (grid[posX,posY + 1] != 'X'): posY += 1
    if (move == 'S'): 
        if (grid[posX + 1,posY] != 'X'): posX += 1
    if (move == 'W'): 
        if (grid[posX,posY - 1] != 'X'): posY -= 1
    
    return posX, posY

def agent_function(request_dict, _info):
    # TOOD: Implement this function in a better way
    print('I got the following request:')
    print(request_dict)
    return {"actions": ["GO south", "GO east"], "success-chance": 0.5, "expected-time": 1.5}

def calc_cell_value(terrain, hasGear, firstCell):
    cell_value = 1 if hasGear == False else 1.2
    
    if terrain == 'R': cell_value = 4 if hasGear == False else 2
        
    if firstCell: cell_value = cell_value / 2
    
    return cell_value

def buildMap(initial_json):
    mapString = initial_json['map']
    map = []
    
    # Prepare the lines of the map
    for x in range(len(mapString)):
        map.append(mapString[x])
        
    numerRows = map.count('\n') + 1 
    numberColumns = mapString.find('\n')
    
    # Remove the line breaks
    for i in range(map.count('\n')):
        map.remove('\n')
    
    # Build the map in a grid format
    mapMatrix = np.array(map).reshape(numberColumns,numerRows)
    
    # Create a NxN matrix filled with "M"
    matrix_nxn = np.full((numerRows*3, numberColumns*3), "M")
    
    # Calculates the center position of the matrix
    X = int((numerRows*3 - numerRows)/2)
    Y = int(X + numerRows)
    
    # Place the 5x5 matrix in the center of the 10x10 matrix
    matrix_nxn[X:Y, X:Y] = mapMatrix
    
    return matrix_nxn

def generatePlan(mapString):
    currPos = ''
    cellWest = ''
    climbGear = False
    maxTime = initial_json["max-time"]
    if 'current-cell' in initial_json['observations']:
        currPos = initial_json['observations']['current-cell']
        
    if 'cell-west' in initial_json['observations']:
        cellWest = initial_json['observations']['cell-west']
    
    if 'climbing-gear' in initial_json['initial-equipment']:
        climbGear = initial_json["initial-equipment"][0] == 'climbing-gear'
        
    # If there is an initial position, start from it
    lis=[] # list of starting points
    for i in range(len(mapString)):
        for j in range(len(mapString[i])):
            if cellWest == '':
                if mapString[i][j]==currPos:
                    lis.extend([i,j])
            else:
                if mapString[i][j]==currPos and mapString[i][j-1]==cellWest:
                    lis.extend([i,j])
    lis = np.array(lis).reshape(-1,2)
    print(lis) # List of current cells possibility
    
    # For each possible state, generate plan
    plans = []
    success_plan = []
    delMoves = []
    moves = ['S', 'N', 'W', 'E']
    json_final = []    
    firstCell = True
    tries = 0
    rating = 0
    plan_bk = ""
    while rating == 0 and tries <= 1000:
        tries += 1
        for p in range(6): # loop for the size of the plan
            moveTo = random.choice(moves)
            
            if len(delMoves) > 0:
                moves.append(delMoves[0])
                
            delMoves = []
            plans.append(moveTo) # add the plan to a list
        
            # If N is choose, remove S so it won't go back, and so on...
            if moveTo == 'N': 
                removeMove = 'S'
            elif moveTo == 'S': 
                removeMove = 'N'
            elif moveTo == 'E': 
                removeMove = 'W'
            else: 
                removeMove = 'E'
            
            moves.remove(removeMove)
            delMoves.append(removeMove)
            firstCell = False
        
        json_final.append({"plan": plans})
        
        print(json_final)
        plans = []
            
        # Calculate the path value for each generated plan
        path = []
        
        for plan in json_final: # for each plan
            print('Plan: ' + str(plan['plan']))
            for a in lis: # loop for the amount of plans (for each starting cell)
                PosX = a[0]
                PosY = a[1]
                firstCell = True
                cellValue = 0
                cv = 0
                # print('Starting ' + str(PosX) + ' ' + str(PosY))
                for p in plan['plan']: # for each step in the current plan
                    if firstCell: path.append(mapString[PosX,PosY]) # I keep the path from the starting point
                    try:
                        PosX, PosY = moveWumpus(mapString, p, PosX, PosY)
                    except Exception:
                        pass
                    path.append(mapString[PosX,PosY]) # add to the path the result after the move
                    
                    # Calculates the terrain value
                    cv = calc_cell_value(mapString[PosX,PosY], climbGear, firstCell)
                    cellValue += cv
                    firstCell = False
                    
                    if mapString[PosX,PosY] == 'W':
                        # print('FOUND THE CAVE!! ' + str(cellValue))
                        if cellValue <= (maxTime / 2):
                            success_plan.append([plan['plan'], cellValue])
                            break
                        elif cellValue <= (maxTime / 2) + 1: 
                            plan_bk = [plan['plan'], cellValue]
                            break
                        elif cellValue <= maxTime and plan_bk == "":
                            plan_bk = [plan['plan'], cellValue]
                            break
                    
                # print('Path Value: ' + str(cellValue))
                cellValue = 0
                
            if tries == 1000 and len(success_plan) == 0 and plan_bk != "": success_plan.append(plan_bk)
            
            # rating = success-chance · expected-time + (1 − success-chance) · max-time
            success_chances = round(len(success_plan) / len(lis),2)
            
            expected_time = 0
            for pp in success_plan:
                print('Success Plan: ' + str(pp))
                expected_time += round(pp[1] * (1 / len(success_plan)),2)
            
            rating = round(success_chances * expected_time + (1 - success_chances) * maxTime, 2)
            
            if rating <= maxTime * 0.65:
                # print('TSP: ' + str(len(success_plan)))
                # print('TPP: ' + str(len(lis)))
                # print('SC: ' + str(success_chances))
                # print('ET: ' + str(expected_time))
                # print('MT: ' + str(maxTime))
                # print('Rating = ' + str(rating))
                break
            else: # Not a good rating; start over
                rating = 0
                success_plan = []
                plan_bk = ""
    
    print('Total tries: ' + str(tries))
    
    return rating, pp, expected_time, success_chances

def buildJson(success_plan, expected_time, success_chances):
    l = []
    for ll in success_plan[0]:
        if ll == 'N': tex = 'GO north'
        if ll == 'S': tex = 'GO south'
        if ll == 'E': tex = 'GO east'
        if ll == 'W': tex = 'GO west'
        l.append(tex)
        
    fj = {
        "actions": l,
        "expected-time": expected_time,
        "success-chance": success_chances
    }

    return fj

if __name__ == '__main__':
    
    initial_json = {
        "initial-equipment": ["climbing-gear"],
        "map": "CWBBB\nRRRBB\nWRRRR\nBBRWB\nMWRRR",
        "max-time": 6,
        "observations": {"cell-west": "R", "current-cell": "B"}
    }
    
    map = buildMap(initial_json)
    ratings, success_plan, expected_time, success_chances = generatePlan(map)
    final_json = buildJson(success_plan, expected_time, success_chances)
    print('Final rating: ' + str(ratings))
    print('JSON: ' + str(final_json))
    
    """
    try:
        from client import run
    except ImportError:
        raise ImportError('You need to have the client.py file in the same directory as this file')

    import logging
    logging.basicConfig(level=logging.INFO)

    import sys
    config_file = sys.argv[1]

    run(
        config_file,        # path to config file for the environment (in your personal repository)
        agent_function,
        processes=1,        # higher values will call the agent function on multiple requests in parallel
        run_limit=1000,     # stop after 1000 runs (then the rating is "complete")
        parallel_runs=True  # multiple requests are bundled in one server interaction (more efficient)
    )
    """