import os.path
import csv
import time

####################################
# Enums
####################################

class AnsiColors:
    GRAY = "\033[90m"
    RED = '\033[91m'
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
# AnsiColors end

class NodeStates:
    BULB = "b"
    WALL = "W"
    WALL0 = "0"
    WALL1 = "1"
    WALL2 = "2"
    WALL3 = "3"
    WALL4 = "4"
    EMPTY = "_"
# NodeStates end

class OverallStates:
    INVALID = 0
    VALID = 1
    COMPLETE = 2
    CANNOT_FINISH = 3
# OverallStates end

class HeuristicMode:
    NONE = 0
    MOST_CONSTRAINED = 1
    MOST_CONSTRAINING = 2
    HYBRID = 3
# HeuristicMode end

####################################
# Globals
####################################

USE_COLOR_PRINT = True # Disable if terminal doesn't support ANSI escape codes (e.g. prints gibberish)
MAX_SEARCH_ITERATIONS = 100000
HEURISTIC_MODE = 1
SAVE_CSV = True

####################################
# Classes
####################################

class Node:
    def __init__(self, state, x, y):
        self.state = state
        self.x = x
        self.y = y
    # __init__ end

    def __str__(self):
        return self.state
    # __str__ end

    def __repr__(self):
        return self.state
    # __repr__ end

    def __unicode__(self):
        return self.state
    # __unicode__ end
# Node end

class BacktrackingSolver:
    def __init__(self, graph, node2dArray):
        self.graph = graph
        self.board = node2dArray
        self.solved = False
        self.searchSteps = 0
        self.aborted = False
    # __init__ end

    def solve(self):
        # Get all numbered tiles
        wallNode3Count, wallNode4Count = 0, 0
        initWallNodes, initEmptyNodes, wallNodes = [], [], []
        csv_file_name = ""
        for n in self.graph:
            if self.nodeStateIsWall(n):
                if n.state == NodeStates.WALL4:
                    initWallNodes.insert(0, n)
                    wallNode4Count += 1
                elif n.state != NodeStates.WALL0:
                    initWallNodes.append(n)
            else:
                initEmptyNodes.append(n)

        wallNodes.extend(initWallNodes[:wallNode4Count])

        # Sort wall tiles for heuristic
        if HEURISTIC_MODE == HeuristicMode.MOST_CONSTRAINED:
            # combinations = [[1 combination], [2 combinations], [3 combinations], [4 combinations], [6 combinations]]
            combinations = [[], [], [], [], []]
            combinations[0].extend(wallNodes)
            for node in initWallNodes:
                adjEmptyCells = len([v for v in self.graph[node] if v.state == NodeStates.EMPTY])
                if node.state == NodeStates.WALL3:
                    if adjEmptyCells == 3:
                        combinations[0].append(node)
                    elif adjEmptyCells == 4:
                        combinations[3].append(node)
                elif node.state == NodeStates.WALL2:
                    if adjEmptyCells == 4:
                        combinations[4].append(node)
                    elif adjEmptyCells == 3:
                        combinations[2].append(node)
                    elif adjEmptyCells == 2:
                        combinations[0].append(node)
                elif node.state == NodeStates.WALL1:
                    combinations[adjEmptyCells-1].append(node)

            for c in combinations:
                wallNodes += c

            csv_file_name = "bt_constrained.csv"

        elif HEURISTIC_MODE == HeuristicMode.MOST_CONSTRAINING:
            # Walls that could illuminate the most cells first
            def countIlluminatedSpaces(node):
                numLitCells = 0
                adjNodes = self.graph[node]

                for adjNode in adjNodes: # For each direction
                    if adjNode.state == NodeStates.WALL:
                        continue

                    bulbAdjNodes = self.graph[adjNode]

                    for idx, bulbAdjNode in enumerate(bulbAdjNodes): # For each direction around possible bulb
                        rayNode = bulbAdjNode # Check each node outwards in a ray in that direction until wall

                        while True: # Graph should be bordered by WALL, so this will always break eventually
                            if rayNode.state == NodeStates.EMPTY:
                                numLitCells += 1
                            elif self.nodeStateIsWall(rayNode):
                                break # If hit wall, we're done checking in this direction

                            rayNode = self.graph[rayNode][idx] # Get next node in this direction

                return numLitCells
            # countIlluminatedSpaces end

            wallNodes = sorted(initWallNodes, key=countIlluminatedSpaces, reverse=True)
            csv_file_name = "bt_constraining.csv"

        elif HEURISTIC_MODE == HeuristicMode.HYBRID:
            # Combine both most constrained and most constraining by generating a score from both sorting methods

            # Constrained
            # Order of most possible combinations
            # combinations = [[1 combination], [2 combinations], [3 combinations], [4 combinations], [6 combinations]]
            combinations = [[], [], [], [], []]
            combinations[0].extend(wallNodes)
            for node in initWallNodes:
                adjEmptyCells = len([v for v in self.graph[node] if v.state == NodeStates.EMPTY])
                if node.state == NodeStates.WALL3:
                    if adjEmptyCells == 3:
                        combinations[0].append(node)
                    elif adjEmptyCells == 4:
                        combinations[3].append(node)
                elif node.state == NodeStates.WALL2:
                    if adjEmptyCells == 4:
                        combinations[4].append(node)
                    elif adjEmptyCells == 3:
                        combinations[2].append(node)
                    elif adjEmptyCells == 2:
                        combinations[0].append(node)
                elif node.state == NodeStates.WALL1:
                    combinations[adjEmptyCells-1].append(node)

            # Constraining
            def countIlluminatedSpaces(node):
                numLitCells = 0
                adjNodes = self.graph[node]

                for adjNode in adjNodes: # For each direction
                    if adjNode.state == NodeStates.WALL:
                        continue

                    bulbAdjNodes = self.graph[adjNode]

                    for idx, bulbAdjNode in enumerate(bulbAdjNodes): # For each direction around possible bulb
                        rayNode = bulbAdjNode # Check each node outwards in a ray in that direction until wall

                        while True: # Graph should be bordered by WALL, so this will always break eventually
                            if rayNode.state == NodeStates.EMPTY:
                                numLitCells += 1
                            elif self.nodeStateIsWall(rayNode):
                                break # If hit wall, we're done checking in this direction

                            rayNode = self.graph[rayNode][idx] # Get next node in this direction

                return numLitCells
            # countIlluminatedSpaces end

            maxLitSpaces = 0
            litSpacesMap = {}
            for node in self.graph:
                litSpaces = countIlluminatedSpaces(node)
                litSpacesMap[node] = litSpaces

                if litSpaces > maxLitSpaces:
                    maxLitSpaces = litSpaces

            # Generate score via hybrid
            def hybridSort(node):
                totalScore = 0
                litSpaces = countIlluminatedSpaces(node)
                litSpacesPercentage = litSpaces / maxLitSpaces

                for score, combo in enumerate(combinations):
                    if node in combo:
                        totalScore = (score + 1) * litSpacesPercentage
                        break

                return totalScore
            # hybridSort end

            wallNodes = sorted(initWallNodes, key=hybridSort, reverse=True)

            csv_file_name = "bt_hybrid.csv"

        elif HEURISTIC_MODE == HeuristicMode.NONE:
            wallNodes = initWallNodes
            csv_file_name = "bt_no_h.csv"

        # Place bulbs around WALL4 tiles - there's no other choice
        for node in wallNodes:
            if node.state == NodeStates.WALL4:
                for adjNode in self.graph[node]:
                    if adjNode.state == NodeStates.EMPTY:
                        adjNode.state = NodeStates.BULB

        # Remove WALL4 tiles from list
        wallNodes = [node for node in wallNodes if node.state != NodeStates.WALL4]

        # Backtracking search for placement around rest of tiles
        startTime = time.time()
        result = self.backtrackingSolve(wallNodes, self.graph)
        timeTaken = time.time() - startTime

        if result == OverallStates.CANNOT_FINISH:
            colorPrint(AnsiColors.RED, "Exceeded allowed steps")
        else:
            colorPrint(AnsiColors.GREEN, "Finished")

        # Write results to csv
        if SAVE_CSV:
            to_write = []
            if self.searchSteps < 50002:
                to_write = [len(self.board), self.searchSteps, "yes"]
            else:
                to_write = [len(self.board), self.searchSteps, "no"]

            if not os.path.isfile(csv_file_name):
                with open(csv_file_name, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["board_size", "steps_taken", "solved"])
                    writer.writerow(to_write)
            else:
                with open(csv_file_name, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow(to_write)

        print("Steps taken:", self.searchSteps)
        print("Seconds taken:", timeTaken)
        self.printState()
        print(flush=True)
    # solve end

    def backtrackingSolve(self, wallNodes, graphState):
        if self.aborted:
            return OverallStates.CANNOT_FINISH

        stateStatus = self.checkOverallStates(graphState)

        if stateStatus == OverallStates.INVALID:
            return OverallStates.INVALID # Backtrack
        elif stateStatus == OverallStates.COMPLETE:
            return OverallStates.COMPLETE # Escape recursion and output solution
        else:
            if self.searchSteps > MAX_SEARCH_ITERATIONS:
                self.aborted = True
            self.searchSteps += 1

            while wallNodes:
                node = wallNodes.pop()

                # Get list of possible moves
                possibleBulbNodes = []

                if node.state == NodeStates.WALL1:
                    for adjNode in graphState[node]:
                        if adjNode.state == NodeStates.EMPTY:
                            possibleBulbNodes.append([adjNode])
                elif node.state == NodeStates.WALL2:
                    adjacents = graphState[node]
                    if adjacents[0].state == NodeStates.EMPTY and adjacents[1].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[0], adjacents[1]])
                    if adjacents[1].state == NodeStates.EMPTY and adjacents[2].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[1], adjacents[2]])
                    if adjacents[2].state == NodeStates.EMPTY and adjacents[3].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[2], adjacents[3]])
                    if adjacents[3].state == NodeStates.EMPTY and adjacents[0].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[3], adjacents[0]])
                    if adjacents[3].state == NodeStates.EMPTY and adjacents[1].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[3], adjacents[1]])
                    if adjacents[0].state == NodeStates.EMPTY and adjacents[2].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[0], adjacents[2]])

                elif node.state == NodeStates.WALL3:
                    adjacents = graphState[node]
                    if adjacents[3].state == NodeStates.EMPTY and adjacents[0].state == NodeStates.EMPTY and adjacents[1].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[3], adjacents[0], adjacents[1]])
                    if adjacents[0].state == NodeStates.EMPTY and adjacents[1].state == NodeStates.EMPTY and adjacents[2].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[0], adjacents[1], adjacents[2]])
                    if adjacents[1].state == NodeStates.EMPTY and adjacents[2].state == NodeStates.EMPTY and adjacents[3].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[1], adjacents[2], adjacents[3]])
                    if adjacents[2].state == NodeStates.EMPTY and adjacents[3].state == NodeStates.EMPTY and adjacents[0].state == NodeStates.EMPTY:
                        possibleBulbNodes.append([adjacents[2], adjacents[3], adjacents[0]])

                # Try possible bulb placements via backtracking search
                for possibleNodeSet in possibleBulbNodes:
                    for possibleNode in possibleNodeSet:
                        possibleNode.state = NodeStates.BULB # Try these tiles as bulbs and recurse

                    backtrackingResult = self.backtrackingSolve(wallNodes.copy(), graphState)

                    if backtrackingResult == OverallStates.INVALID:
                        for possibleNode in possibleNodeSet:
                            possibleNode.state = NodeStates.EMPTY # Reset tile states if failure
                    elif backtrackingResult == OverallStates.CANNOT_FINISH:
                        return OverallStates.CANNOT_FINISH

            # Test open spaces with backtracking
            if not wallNodes:
                # Get list of unlit unoccupied tiles
                unlits, lits = self.getUnlitSpaces(graphState)
                unlits = list(unlits)
                lits = list(lits)

                # Sort unlits by heuristics
                if HEURISTIC_MODE == HeuristicMode.MOST_CONSTRAINED:
                    # Most adjacent lit spaces
                    def countAdjacentLits(node):
                        count = 0

                        for adj in graphState[node]:
                            if adj in lits:
                                count += 1

                        return count
                    # countAdjacentLits end

                    unlits.sort(key=countAdjacentLits, reverse=True)
                elif HEURISTIC_MODE == HeuristicMode.MOST_CONSTRAINING:
                    # Lights the most tiles
                    def sortCountIlluminatedSpaces(node):
                        return self.countIlluminatedSpaces(node, graphState)
                    # sortCountIlluminatedSpaces end

                    unlits.sort(key=sortCountIlluminatedSpaces, reverse=True)
                elif HEURISTIC_MODE == HeuristicMode.HYBRID:
                    # Combine scores
                    def countAdjacentLits(node):
                        count = 0

                        for adj in graphState[node]:
                            if adj in lits:
                                count += 1

                        return count
                    # countAdjacentLits end

                    def hybridSort(node):
                        litSpaces = self.countIlluminatedSpaces(node, graphState)
                        adjLitSpaces = countAdjacentLits(node)
                        adjLitPercentage = adjLitSpaces/4

                        return adjLitPercentage * litSpaces
                    # hybridSort end

                    unlits.sort(key=hybridSort, reverse=True)

                # Backtracking search for bulb placement on unlit unoccupied non-wall-adjacent tiles
                for possibleNode in unlits:
                    possibleNode.state = NodeStates.BULB # Try this tile as bulb and recurse

                    backtrackingResult = self.backtrackingSolve(wallNodes.copy(), graphState)

                    if backtrackingResult == OverallStates.INVALID:
                        possibleNode.state = NodeStates.EMPTY # Reset tile state if failure
                    elif backtrackingResult == OverallStates.COMPLETE:
                        return OverallStates.COMPLETE
                    elif backtrackingResult == OverallStates.CANNOT_FINISH:
                        return OverallStates.CANNOT_FINISH

            return OverallStates.INVALID # The tip of this branch is invalid
    # backtrackingSolve end

    def nodeStateIsWall(self, node):
        return node.state == NodeStates.WALL or \
            node.state == NodeStates.WALL0 or \
            node.state == NodeStates.WALL1 or \
            node.state == NodeStates.WALL2 or \
            node.state == NodeStates.WALL3 or \
            node.state == NodeStates.WALL4
    # nodeStateIsWall end

    def countIlluminatedSpaces(self, node, graphState):
        numLitCells = 0
        adjNodes = graphState[node]

        for adjNode in adjNodes: # For each direction
            if adjNode.state == NodeStates.WALL: # Border walls aren't in graph
                continue

            bulbAdjNodes = graphState[adjNode]

            for idx, bulbAdjNode in enumerate(bulbAdjNodes): # For each direction around possible bulb
                rayNode = bulbAdjNode # Check each node outwards in a ray in that direction until wall

                while True: # Graph should be bordered by WALL, so this will always break eventually
                    if not self.nodeStateIsWall(rayNode):
                        numLitCells += 1
                    elif self.nodeStateIsWall(rayNode):
                        break # If hit wall, we're done checking in this direction

                    rayNode = graphState[rayNode][idx] # Get next node in this direction

        return numLitCells
    # countIlluminatedSpaces end

    def countUnlitSpaces(self, graphState, node):
        count = 0
        litMap = {}
        empties, unlits, bulbs = [], [], []

        for node in graphState:
            if node.state == NodeStates.EMPTY:
                litMap[node] = False # Initialize to unlit
                empties.append(node)
            elif node.state == NodeStates.BULB:
                bulbs.append(node)

        for bulb in bulbs:
            adjNodes = graphState[bulb]

            for idx, adjNode in enumerate(adjNodes): # For each direction
                rayNode = adjNode # Check each node outwards in a ray in that direction until wall

                while True: # Graph should be bordered by WALL, so this will always break eventually
                    if rayNode.state == NodeStates.EMPTY:
                        litMap[rayNode] = True
                    elif self.nodeStateIsWall(rayNode):
                        break # If hit wall, we're done checking in this direction

                    rayNode = graphState[rayNode][idx] # Get next node in this direction

        for node in empties:
            if not litMap[node]:
                unlits.append(node)

        return count

    def getUnlitSpaces(self, graphState):
        litMap = {}
        empties = set()
        unlits = set()
        lits = set()
        bulbs = set()

        for node in graphState:
            if node.state == NodeStates.EMPTY:
                litMap[node] = False # Initialize to unlit
                empties.add(node)
            elif node.state == NodeStates.BULB:
                bulbs.add(node)

        for bulb in bulbs:
            adjNodes = graphState[bulb]

            for idx, adjNode in enumerate(adjNodes): # For each direction
                rayNode = adjNode # Check each node outwards in a ray in that direction until wall

                while True: # Graph should be bordered by WALL, so this will always break eventually
                    if self.nodeStateIsWall(rayNode):
                        break # If hit wall, we're done checking in this direction
                    elif rayNode.state == NodeStates.EMPTY:
                        litMap[rayNode] = True

                    rayNode = graphState[rayNode][idx] # Get next node in this direction

        for node in empties:
            if not litMap[node]:
                unlits.add(node)
            else:
                lits.add(node)

        return unlits, lits
    # getUnlitSpaces end

    def countNodeAdjacentBulbs(self, graphState, node):
        adjBulbs = 0

        for adj in graphState[node]:
            if adj.state == NodeStates.BULB:
                adjBulbs += 1

        return adjBulbs
    # countNodeAdjacentBulbs end

    def checkOverallStates(self, graphState):
        unlit, lit = self.getUnlitSpaces(graphState) # Not unlitSpacesList = no unlit spaces left
        isComplete = not unlit

        for node in graphState:
            if node.state == NodeStates.BULB:
                # No bulbs in row or column until wall
                adjNodes = graphState[node]

                for idx, adjNode in enumerate(adjNodes): # For each direction
                    rayNode = adjNode # Check each node outwards in a ray in that direction until wall

                    while True: # Graph should be bordered by WALL, so this will always break eventually
                        if rayNode.state == NodeStates.BULB:
                            return OverallStates.INVALID # If hit bulb before wall, this state is invalid
                        elif self.nodeStateIsWall(rayNode):
                            break # If hit wall, we're done checking in this direction

                        rayNode = graphState[rayNode][idx] # Get next node in this direction
            else:
                adjBulbs = self.countNodeAdjacentBulbs(graphState, node)

                if node.state == NodeStates.WALL0:
                    #Less than or equal to 0 adjacent bulbs
                    if adjBulbs > 0:
                        return OverallStates.INVALID
                    elif adjBulbs != 0:
                        isComplete = False
                elif node.state == NodeStates.WALL1:
                    # Less than or equal to 1 adjacent bulb
                    if adjBulbs > 1:
                        return OverallStates.INVALID
                    elif adjBulbs != 1:
                        isComplete = False
                elif node.state == NodeStates.WALL2:
                    # Less than or equal to 2 adjacent bulbs
                    if adjBulbs > 2:
                        return OverallStates.INVALID
                    elif adjBulbs != 2:
                        isComplete = False
                elif node.state == NodeStates.WALL3:
                    # Less than or equal to 3 adjacent bulbs
                    if adjBulbs > 3:
                        return OverallStates.INVALID
                    elif adjBulbs != 3:
                        isComplete = False
                elif node.state == NodeStates.WALL4:
                    # Less than or equal to 4 adjacent bulbs
                    if adjBulbs > 4:
                        return OverallStates.INVALID
                    elif adjBulbs != 4:
                        isComplete = False
        if isComplete:
            return OverallStates.COMPLETE
        else:
            return OverallStates.VALID
    # stateIsInvalid end

    def printState(self):
        unlit, lit = self.getUnlitSpaces(self.graph)

        for row in self.board:
            for node in row:
                if node.state == NodeStates.BULB:
                    colorPrint(AnsiColors.YELLOW, node, end="")
                elif node.state == NodeStates.EMPTY:
                    if node in unlit:
                        colorPrint(AnsiColors.GRAY, node, end="")
                    else:
                        colorPrint(AnsiColors.YELLOW, node, end="")
                else:
                    colorPrint("", node, end="")
            print()

# BacktrackingSolver end

####################################
# Utility Functions
####################################

# ansi = string: from AnsiColors class
def colorPrint(ansi, *args, end=None, sep=" "):
    if USE_COLOR_PRINT:
        print(ansi, end="")
        print(*args, end="", sep=sep)
        print(AnsiColors.RESET, end="")
        print(end=end)
    else:
        print(*args, end=end)
# colorPrint end

####################################
# Core Functions
####################################

# mapData = list: strings representing each row of map; its initial state
# mapSize = list: rows, columns
def createGraphFromMapData(mapData, mapSize):
    # Convert mapData to discrete nodes
    nodes = []

    for y, line in enumerate(mapData):
        nodeRow = []
        for x, char in enumerate(line):
            nodeRow.append(Node(char, x, y))
        nodes.append(nodeRow)

    # Create graph from nodes
    graph = {}

    for rowIdx in range(mapSize[0]):
        for columnIdx in range(mapSize[1]):
            # Gather adjacent nodes of node
            node = nodes[rowIdx][columnIdx]
            adjacencyList = []

            up = None
            down = None
            left = None
            right = None

            if rowIdx-1 >= 0:
                up = nodes[rowIdx-1][columnIdx]
            if rowIdx+1 < mapSize[0]:
                down = nodes[rowIdx+1][columnIdx]
            if columnIdx-1 >= 0:
                left = nodes[rowIdx][columnIdx-1]
            if columnIdx+1 < mapSize[1]:
                right = nodes[rowIdx][columnIdx+1]

            if up is not None:
                adjacencyList.append(up)
            else:
                adjacencyList.append(Node(NodeStates.WALL, rowIdx, columnIdx))

            if right is not None:
                adjacencyList.append(right)
            else:
                adjacencyList.append(Node(NodeStates.WALL, rowIdx, columnIdx))

            if down is not None:
                adjacencyList.append(down)
            else:
                adjacencyList.append(Node(NodeStates.WALL, rowIdx, columnIdx))

            if left is not None:
                adjacencyList.append(left)
            else:
                adjacencyList.append(Node(NodeStates.WALL, rowIdx, columnIdx))

            graph[node] = adjacencyList

    return graph, nodes
# createGraphFromMapData end

# filename = string: filename of input file
# SolverClass = class: constructor accepting dictionary graph as first argument, implementing solve method
def parse(filename, SolverClass):
    if not os.path.isfile(filename):
        print("File does not exist:", filename)
        return

    file = open(filename, "r")

    if file.mode == "r":
        lines = file.readlines()
        mapSize = [0,0] # Integers x, y
        mapData = [] # List of strings denoting map rows
        readingSize = False # Reading first line of map data

        for line in lines:
            line = line.strip()

            if "# Start" in line:
                # Begin reading map
                readingSize = True

            elif "# End" in line:
                # Solve the puzzle
                if SolverClass is not None:
                    graph, board = createGraphFromMapData(mapData, mapSize)
                    solver = SolverClass(graph, board)
                    solver.solve()

                # Reset for next map
                mapSize = [0,0]
                mapData = []
                readingSize = False

            elif len(line) > 0 and line[0] != "#":
                if readingSize:
                    # Read map size from first line
                    split = line.split(" ")
                    mapSize[0] = int(split[0])
                    mapSize[1] = int(split[1])
                    readingSize = False

                else:
                    # Read map data from rest of lines
                    mapData.append(line)

        file.close()
    else:
        print("Failed to read file:", filename)
# parse end

####################################
# Main
####################################

filename = input("Enter filename or press enter to use default (lightup puzzles.txt).\n") or "lightup puzzles.txt"
parse(filename, BacktrackingSolver)
#input("Completed. Press any key to exit.")
