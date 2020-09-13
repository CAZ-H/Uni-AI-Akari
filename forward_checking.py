import os.path
import sys
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
MAX_RECURSION_DEPTH = 1400 # Default is around 997
HEURISTIC_MODE = HeuristicMode.HYBRID
SAVE_CSV = True

sys.setrecursionlimit(MAX_RECURSION_DEPTH + 100)

####################################
# Classes
####################################

class Node:
    def __init__(self, possibilitySet, x, y):
        self.possibilitySet = possibilitySet
        self.x = x
        self.y = y
    # __init__ end

    def getDecision(self):
        numChoices = len(self.possibilitySet)
        if numChoices == 1:
            (possibility,) = self.possibilitySet
            return possibility
        elif numChoices <= 0:
            return None
        return None
    # getDecision end

    def isDecided(self):
        return len(self.possibilitySet) > 1
    # isDecided end

    def __str__(self):
        return "[" + "".join(self.possibilitySet) + "]"
    # __str__ end

    def __repr__(self):
        return "[" + "".join(self.possibilitySet) + "]"
    # __repr__ end

    def __unicode__(self):
        return "[" + "".join(self.possibilitySet) + "]"
    # __unicode__ end
# Node end

class ForwardCheckingSolver:
    def __init__(self, graph, node2dArray):
        self.graph = graph
        self.board = node2dArray
        self.solved = False
        self.searchSteps = 0
        self.aborted = False

        self.depth = 0
    # __init__ end

    def solve(self):
        # Precalculate wall0 and wall4 states
        self.initializePossibilities(self.graph)

        # Get all numbered tiles
        wallNode3Count, wallNode4Count = 0, 0
        initWallNodes, initEmptyNodes, wallNodes = [], [], []
        csv_file_name = ""
        for n in self.graph:
            if self.stateIsWall(n.getDecision()):
                if n.getDecision() == NodeStates.WALL4:
                    initWallNodes.insert(0, n)
                    wallNode4Count += 1
                elif n.getDecision() != NodeStates.WALL0:
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
                empty_cell = len([v for v in self.graph[node] if v.getDecision() == NodeStates.EMPTY])
                if node.getDecision() == NodeStates.WALL3:
                    if empty_cell == 3:
                        combinations[0].append(node)
                    elif empty_cell == 4:
                        combinations[3].append(node)
                elif node.getDecision() == NodeStates.WALL2:
                    if empty_cell == 4:
                        combinations[4].append(node)
                    elif empty_cell == 3:
                        combinations[2].append(node)
                    elif empty_cell == 2:
                        combinations[0].append(node)
                elif node.getDecision() == NodeStates.WALL1:
                    combinations[empty_cell-1].append(node)
            for c in combinations:
                wallNodes += c
            csv_file_name = "fc_constrained.csv"
        elif HEURISTIC_MODE == HeuristicMode.MOST_CONSTRAINING:
            # Walls that could illuminate the most cells first
            def sortCountIlluminatedSpaces(node):
                return self.countIlluminatedSpaces(node, self.graph)
            # sortCountIlluminatedSpaces end

            wallNodes = sorted(initWallNodes, key=sortCountIlluminatedSpaces, reverse=True)
            csv_file_name = "fc_contraining.csv"

        elif HEURISTIC_MODE == HeuristicMode.HYBRID:
            # Combine both most constrained and most constraining by generating a score from both sorting methods

            # Constrained
            # Order of most possible combinations
            # combinations = [[1 combination], [2 combinations], [3 combinations], [4 combinations], [6 combinations]]
            combinations = [[], [], [], [], []]
            combinations[0].extend(wallNodes)
            for node in initWallNodes:
                empty_cell = len([v for v in self.graph[node] if v.getDecision() == NodeStates.EMPTY])
                if node.getDecision() == NodeStates.WALL3:
                    if empty_cell == 3:
                        combinations[0].append(node)
                    elif empty_cell == 4:
                        combinations[3].append(node)
                elif node.getDecision() == NodeStates.WALL2:
                    if empty_cell == 4:
                        combinations[4].append(node)
                    elif empty_cell == 3:
                        combinations[2].append(node)
                    elif empty_cell == 2:
                        combinations[0].append(node)
                elif node.getDecision() == NodeStates.WALL1:
                    combinations[empty_cell-1].append(node)

            # Constraining
            maxLitSpaces = 0
            litSpacesMap = {}
            for node in self.graph:
                litSpaces = self.countIlluminatedSpaces(node, self.graph)
                litSpacesMap[node] = litSpaces

                if litSpaces > maxLitSpaces:
                    maxLitSpaces = litSpaces

            # Generate score via hybrid
            def hybridSort(node):
                totalScore = 0
                litSpaces = self.countIlluminatedSpaces(node, self.graph)
                litSpacesPercentage = litSpaces / maxLitSpaces

                for score, combo in enumerate(combinations):
                    if node in combo:
                        totalScore = (score + 1) * litSpacesPercentage
                        break

                return totalScore
            # hybridSort end

            wallNodes = sorted(initWallNodes, key=hybridSort, reverse=True)

            csv_file_name = "fc_hybrid.csv"

        elif HEURISTIC_MODE == HeuristicMode.NONE:
            wallNodes = initWallNodes
            csv_file_name = "fc_no_h.csv"

        # Do forward checking
        startTime = time.time()
        result = self.forwardCheckingSolve(self.graph, self.board, wallNodes)
        timeTaken = time.time() - startTime

        # Print results
        if result == OverallStates.CANNOT_FINISH:
            colorPrint(AnsiColors.RED, "Exceeded allowed steps or recursion depth")
        else:
            colorPrint(AnsiColors.GREEN, "Finished")

        # Write results to csv
        if SAVE_CSV:
            to_write = []
            if self.searchSteps < MAX_SEARCH_ITERATIONS + 2:
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
        self.printState(self.graph, self.board)
        print(flush=True)
    # solve end

    def forwardCheckingSolve(self, graphState, boardState, wallList):
        # print(self.depth)

        if self.aborted or self.depth > MAX_RECURSION_DEPTH:
            return OverallStates.CANNOT_FINISH

        self.propagateConstraints(graphState, boardState)
        stateStatus = self.checkOverallStates(graphState)

        if stateStatus == OverallStates.INVALID:
            return OverallStates.INVALID # Backtrack
        elif stateStatus == OverallStates.COMPLETE:
            return OverallStates.COMPLETE # Escape recursion and output solution
        else:
            if self.searchSteps > MAX_SEARCH_ITERATIONS:
                self.aborted = True
            self.searchSteps += 1

            # For each wall, try placing bulbs around in each configuration
            while wallList:
                node = wallList.pop()

                # Try setting bulbs and propagating constraints
                # Get list of possible moves
                possibleBulbNodes = []

                if node.getDecision() == NodeStates.WALL1:
                    # If there is already a bulb then skip
                    hasBulb = False
                    for adjNode in graphState[node]:
                        if adjNode.getDecision() == NodeStates.BULB:
                            hasBulb = True
                            break

                    if not hasBulb:
                        for adjNode in graphState[node]:
                            if NodeStates.BULB in adjNode.possibilitySet:
                                possibleBulbNodes.append([adjNode])

                elif node.getDecision() == NodeStates.WALL2:
                    # If there is already a bulb then only take options containing it
                    # If there are already two bulbs then skip
                    bulbNodes = []
                    for adjNode in graphState[node]:
                        if adjNode.getDecision() == NodeStates.BULB:
                            bulbNodes.append(adjNode)

                    adjacents = graphState[node]
                    if len(bulbNodes) == 1:
                        for adjNode in graphState[node]:
                            if adjNode not in bulbNodes:
                                possibleBulbNodes.append([bulbNodes[0], adjNode])
                    elif len(bulbNodes) == 0:
                        for i in range(4):
                            iNext = (i+1) % 4
                            if NodeStates.BULB in adjacents[i].possibilitySet and NodeStates.BULB in adjacents[iNext].possibilitySet:
                                possibleBulbNodes.append([adjacents[i], adjacents[iNext]])
                        if NodeStates.BULB in adjacents[3].possibilitySet and NodeStates.BULB in adjacents[1].possibilitySet:
                            possibleBulbNodes.append([adjacents[3], adjacents[1]])
                        if NodeStates.BULB in adjacents[0].possibilitySet and NodeStates.BULB in adjacents[2].possibilitySet:
                            possibleBulbNodes.append([adjacents[0], adjacents[2]])

                elif node.getDecision() == NodeStates.WALL3:
                    # WIP do as above
                    adjacents = graphState[node]
                    if NodeStates.BULB in adjacents[3].possibilitySet and NodeStates.BULB in adjacents[0].possibilitySet and NodeStates.BULB in adjacents[1].possibilitySet:
                        possibleBulbNodes.append([adjacents[3], adjacents[0], adjacents[1]])
                    if NodeStates.BULB in adjacents[0].possibilitySet and NodeStates.BULB in adjacents[1].possibilitySet and NodeStates.BULB in adjacents[2].possibilitySet:
                        possibleBulbNodes.append([adjacents[0], adjacents[1], adjacents[2]])
                    if NodeStates.BULB in adjacents[1].possibilitySet and NodeStates.BULB in adjacents[2].possibilitySet and NodeStates.BULB in adjacents[3].possibilitySet:
                        possibleBulbNodes.append([adjacents[1], adjacents[2], adjacents[3]])
                    if NodeStates.BULB in adjacents[2].possibilitySet and NodeStates.BULB in adjacents[3].possibilitySet and NodeStates.BULB in adjacents[0].possibilitySet:
                        possibleBulbNodes.append([adjacents[2], adjacents[3], adjacents[0]])

                for possibleNodeSet in possibleBulbNodes:
                    # Deep copy state
                    newBoard, newGraph, newWallList = self.deepCopyState(boardState, wallList)

                    # Try set of bulbs
                    for possibleNode in possibleNodeSet:
                        # Find copied version of current node
                        for node in newGraph:
                            if node.x == possibleNode.x and node.y == possibleNode.y:
                                possibleNode = node
                                break

                        if NodeStates.BULB in possibleNode.possibilitySet:
                            possibleNode.possibilitySet.discard(NodeStates.EMPTY) # Try these tiles as bulbs and propagate
                            self.castLight(newGraph, possibleNode)
                    self.propagateConstraints(newGraph, newBoard)

                    # Check if done
                    status = self.checkOverallStates(newGraph)
                    if status == OverallStates.COMPLETE:
                        self.board = newBoard
                        self.graph = newGraph
                        return OverallStates.COMPLETE

                    # Recurse and try next wall
                    oldBoard = boardState
                    oldGraph = graphState
                    boardState = newBoard
                    graphState = newGraph
                    # print("1st - recurse", status)
                    self.depth += 1
                    result = self.forwardCheckingSolve(newGraph, newBoard, newWallList)
                    self.depth -= 1

                    if result == OverallStates.COMPLETE:
                        return OverallStates.COMPLETE
                    elif result == OverallStates.INVALID:
                        boardState = oldBoard
                        graphState = oldGraph
                    elif result == OverallStates.CANNOT_FINISH:
                        return OverallStates.CANNOT_FINISH

            # If state is ok and we have finished recursing, try placing bulbs in open unlit space
            if not wallList:
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


                # Forward checking search for bulb placement on unlit unoccupied non-wall-adjacent tiles
                for possibleNode in unlits:
                    # Deep copy state
                    newBoard, newGraph, newWallList = self.deepCopyState(boardState, wallList)
                    # Find copied version of current node
                    for node in newGraph:
                        if node.x == possibleNode.x and node.y == possibleNode.y:
                            possibleNode = node
                            break

                    if NodeStates.BULB in possibleNode.possibilitySet:
                        possibleNode.possibilitySet.discard(NodeStates.EMPTY) # Try this tile as bulb and propagate
                        self.castLight(newGraph, possibleNode)
                    self.propagateConstraints(newGraph, newBoard)

                    # Check if done
                    status = self.checkOverallStates(newGraph)
                    if status == OverallStates.COMPLETE:
                        self.board = newBoard
                        self.graph = newGraph
                        return OverallStates.COMPLETE

                    oldBoard = boardState
                    oldGraph = graphState
                    boardState = newBoard
                    graphState = newGraph
                    self.depth += 1
                    result = self.forwardCheckingSolve(newGraph, newBoard, newWallList)
                    self.depth -= 1

                    if result == OverallStates.COMPLETE:
                        return OverallStates.COMPLETE
                    elif result == OverallStates.INVALID:
                        boardState = oldBoard
                        graphState = oldGraph
                    elif result == OverallStates.CANNOT_FINISH:
                        return OverallStates.CANNOT_FINISH

            # Check if done
            status = self.checkOverallStates(graphState)
            if status == OverallStates.COMPLETE:
                self.board = boardState
                self.graph = graphState
                return OverallStates.COMPLETE

            return OverallStates.INVALID # The tip of this branch is invalid
    # forwardCheckingSolve end

    def propagateConstraints(self, graphState, boardState):
        settled = False

        # Propagate effects of constraints until no more propagation occurs
        # Assumes puzzle is solvable
        while not settled:
            settled = True

            for node in graphState:
                nodeState = node.getDecision()
                if not self.stateIsWall(nodeState):
                    continue

                # Check if walls can solidify bulb locations
                adjBulbs = self.getNodeAdjacentBulbs(graphState, node)
                unlitSpaces, litSpaces = self.getUnlitSpaces(graphState)
                adjUnlitSpaces = set()
                adjLitSpaces = set()
                adjWalls = set()
                adjBlocked = set()

                for adj in graphState[node]:
                    if adj in unlitSpaces:
                        adjUnlitSpaces.add(adj)
                    elif adj in litSpaces:
                        adjLitSpaces.add(adj)

                    if self.stateIsWall(adj.getDecision()):
                        adjWalls.add(adj)

                    if adj.getDecision() == NodeStates.EMPTY:
                        adjBlocked.add(adj)

                adjBlocked = adjBlocked.union(adjLitSpaces)
                adjBlocked = adjBlocked.union(adjWalls)

                if nodeState == NodeStates.WALL1:
                    # If already has a bulb, other spaces must be empty/blocked
                    if len(adjBulbs) >= 1:
                        for adj in graphState[node]:
                            if adj.getDecision() != NodeStates.BULB and (NodeStates.BULB in adj.possibilitySet):
                                adj.possibilitySet.discard(NodeStates.BULB)
                                settled = False
                            elif adj.getDecision() == NodeStates.BULB:
                                self.castLight(graphState, adj)
                    # If all but one side is lit/blocked, that side must be a bulb
                    elif len(adjBlocked) == 3:
                        for adj in graphState[node]:
                            if NodeStates.BULB in adj.possibilitySet:
                                adj.possibilitySet.discard(NodeStates.EMPTY)
                                self.castLight(graphState, adj)
                                settled = False
                                break
                elif nodeState == NodeStates.WALL2:
                    # If already has one bulb and all but one space is lit/blocked, it must be a bulb
                    if len(adjBulbs) == 1 and len(adjBlocked) == 2:
                        for adj in graphState[node]:
                            if (adj not in adjBulbs) and (adj not in adjBlocked) and (NodeStates.EMPTY in adj.possibilitySet):
                                adj.possibilitySet.discard(NodeStates.EMPTY)
                                self.castLight(graphState, adj)
                                settled = False
                    # If already has two bulbs, other spaces must be empty/blocked
                    elif len(adjBulbs) == 2:
                        for adj in graphState[node]:
                            if (adj not in adjBulbs) and (NodeStates.BULB in adj.possibilitySet):
                                adj.possibilitySet.discard(NodeStates.BULB)
                                settled = False
                            elif adj.getDecision() == NodeStates.BULB:
                                self.castLight(graphState, adj)
                    # If all but two side are lit/blocked, other sides must be bulbs
                    elif len(adjBlocked) == 2:
                        for adj in graphState[node]:
                            if (adj not in adjBlocked) and (NodeStates.EMPTY in adj.possibilitySet):
                                adj.possibilitySet.discard(NodeStates.EMPTY)
                                self.castLight(graphState, adj)
                                settled = False
                elif nodeState == NodeStates.WALL3:
                    # If already has three bulbs, other spaces must be empty/blocked
                    if len(adjBulbs) == 3:
                        for adj in graphState[node]:
                            if adj.getDecision() != NodeStates.BULB and (NodeStates.BULB in adj.possibilitySet):
                                adj.possibilitySet.discard(NodeStates.BULB)
                                settled = False
                            elif adj.getDecision() == NodeStates.BULB:
                                self.castLight(graphState, adj)
                    # If one side is lit/blocked, the rest must be bulbs
                    elif len(adjBlocked) == 1:
                        for adj in graphState[node]:
                            if (adj not in adjBlocked) and (NodeStates.EMPTY in adj.possibilitySet):
                                adj.possibilitySet.discard(NodeStates.EMPTY)
                                self.castLight(graphState, adj)
                                settled = False
    # propagateConstraints end

    def initializePossibilities(self, graphState):
        # Eliminate bulb possibilities around WALL0
        # Eliminate empty possibilities around WALL4
        for node in graphState:
            if node.getDecision() == NodeStates.WALL0:
                for adjNode in graphState[node]:
                    if not self.stateIsWall(adjNode.getDecision()):
                        adjNode.possibilitySet.discard(NodeStates.BULB)
            elif node.getDecision() == NodeStates.WALL4:
                for adjNode in graphState[node]:
                    if not self.stateIsWall(adjNode.getDecision()):
                        adjNode.possibilitySet.discard(NodeStates.EMPTY)
                        self.castLight(graphState, adjNode)
    # initializePossibilities end

    def countIlluminatedSpaces(self, node, graphState):
        numLitCells = 0
        adjNodes = graphState[node]

        for adjNode in adjNodes: # For each direction
            if adjNode.getDecision() == NodeStates.WALL: # Border walls aren't in graph
                continue

            bulbAdjNodes = graphState[adjNode]

            for idx, bulbAdjNode in enumerate(bulbAdjNodes): # For each direction around possible bulb
                rayNode = bulbAdjNode # Check each node outwards in a ray in that direction until wall

                while True: # Graph should be bordered by WALL, so this will always break eventually
                    if not self.stateIsWall(rayNode.getDecision()):
                        numLitCells += 1
                    elif self.stateIsWall(rayNode.getDecision()):
                        break # If hit wall, we're done checking in this direction

                    rayNode = graphState[rayNode][idx] # Get next node in this direction

        return numLitCells
    # countIlluminatedSpaces end

    # Eliminate bulb from possibilitySets in + shape from given node
    def castLight(self, graphState, node):
        adjNodes = graphState[node]

        for idx, adjNode in enumerate(adjNodes): # For each direction
            rayNode = adjNode # Check each node outwards in a ray in that direction until wall

            while True: # Graph should be bordered by WALL, so this will always break eventually
                if not self.stateIsWall(rayNode.getDecision()):
                    rayNode.possibilitySet.discard(NodeStates.BULB)
                else:
                    break # If hit wall, we're done checking in this direction

                rayNode = graphState[rayNode][idx] # Get next node in this direction
    # castLight end

    def stateIsWall(self, state):
        return state == NodeStates.WALL or \
            state == NodeStates.WALL0 or \
            state == NodeStates.WALL1 or \
            state == NodeStates.WALL2 or \
            state == NodeStates.WALL3 or \
            state == NodeStates.WALL4
    # stateIsWall end

    def getUnlitSpaces(self, graphState):
        litMap = {}
        empties = set()
        unlits = set()
        lits = set()
        bulbs = set()

        for node in graphState:
            if NodeStates.EMPTY in node.possibilitySet:
                litMap[node] = False # Initialize to unlit
                empties.add(node)
            elif node.getDecision() == NodeStates.BULB:
                bulbs.add(node)

        for bulb in bulbs:
            adjNodes = graphState[bulb]

            for idx, adjNode in enumerate(adjNodes): # For each direction
                rayNode = adjNode # Check each node outwards in a ray in that direction until wall

                while True: # Graph should be bordered by WALL, so this will always break eventually
                    if self.stateIsWall(rayNode.getDecision()):
                        break # If hit wall, we're done checking in this direction
                    elif NodeStates.EMPTY in rayNode.possibilitySet:
                        litMap[rayNode] = True

                    rayNode = graphState[rayNode][idx] # Get next node in this direction

        for node in empties:
            if not litMap[node]:
                unlits.add(node)
            else:
                lits.add(node)

        return unlits, lits
    # getUnlitSpaces end

    def deepCopyState(self, boardState, wallList):
        boardCopy = []
        wallListCopy = []

        for rowIdx, row in enumerate(boardState):
            rowCopy = []
            for columnIdx, node in enumerate(row):
                copyNode = Node(boardState[rowIdx][columnIdx].possibilitySet.copy(), rowIdx, columnIdx)

                if node in wallList:
                    wallListCopy.append(copyNode)

                rowCopy.append(copyNode)
            boardCopy.append(rowCopy)

        return boardCopy, createGraphFromNodeMatrix(boardCopy, len(boardCopy), len(boardCopy[0])), wallListCopy
    # deepCopyState end

    def getNodeAdjacentBulbs(self, graphState, node):
        adjBulbs = set()

        for adj in graphState[node]:
            if adj.getDecision() == NodeStates.BULB:
                adjBulbs.add(adj)

        return adjBulbs
    # getNodeAdjacentBulbs end

    def countNodeAdjacentBulbs(self, graphState, node):
        adjBulbs = 0

        for adj in graphState[node]:
            if adj.getDecision() == NodeStates.BULB:
                adjBulbs += 1

        return adjBulbs
    # countNodeAdjacentBulbs end

    def checkOverallStates(self, graphState):
        unlit, lit = self.getUnlitSpaces(graphState) # Not unlitSpacesList = no unlit spaces left
        isComplete = not unlit

        settled = True
        for node in graphState:
            if not node.getDecision():
                settled = False
                break

        for node in graphState:
            if node.getDecision() == NodeStates.BULB:
                # No bulbs in row or column until wall
                adjNodes = graphState[node]

                for idx, adjNode in enumerate(adjNodes): # For each direction
                    rayNode = adjNode # Check each node outwards in a ray in that direction until wall

                    while True: # Graph should be bordered by WALL, so this will always break eventually
                        if rayNode.getDecision() == NodeStates.BULB:
                            return OverallStates.INVALID # If hit bulb before wall, this state is invalid
                        elif self.stateIsWall(rayNode.getDecision()):
                            break # If hit wall, we're done checking in this direction

                        rayNode = graphState[rayNode][idx] # Get next node in this direction
            else:
                adjBulbs = self.countNodeAdjacentBulbs(graphState, node)

                if node.getDecision() == NodeStates.WALL0:
                    #Less than or equal to 0 adjacent bulbs
                    if adjBulbs > 0:
                        return OverallStates.INVALID
                    elif adjBulbs != 0:
                        isComplete = False
                elif node.getDecision() == NodeStates.WALL1:
                    # Less than or equal to 1 adjacent bulb
                    if adjBulbs > 1:
                        return OverallStates.INVALID
                    elif adjBulbs != 1:
                        isComplete = False
                elif node.getDecision() == NodeStates.WALL2:
                    # Less than or equal to 2 adjacent bulbs
                    if adjBulbs > 2:
                        return OverallStates.INVALID
                    elif adjBulbs != 2:
                        isComplete = False
                elif node.getDecision() == NodeStates.WALL3:
                    # Less than or equal to 3 adjacent bulbs
                    if adjBulbs > 3:
                        return OverallStates.INVALID
                    elif adjBulbs != 3:
                        isComplete = False
                elif node.getDecision() == NodeStates.WALL4:
                    # Less than or equal to 4 adjacent bulbs
                    if adjBulbs > 4:
                        return OverallStates.INVALID
                    elif adjBulbs != 4:
                        isComplete = False

        if settled and unlit:
            return OverallStates.INVALID

        if isComplete:
            return OverallStates.COMPLETE
        else:
            return OverallStates.VALID
    # checkOverallStates end

    def printState(self, graphState, boardState):
        unlit, lit = self.getUnlitSpaces(graphState)

        for row in boardState:
            for node in row:
                if node.getDecision() == NodeStates.BULB:
                    colorPrint(AnsiColors.YELLOW, str(node).ljust(4, " "), end="")
                elif node.getDecision() == NodeStates.EMPTY:
                    if node in unlit:
                        colorPrint(AnsiColors.GRAY, str(node).ljust(4, " "), end="")
                    else:
                        colorPrint(AnsiColors.YELLOW, str(node).ljust(4, " "), end="")
                elif node.getDecision() is not None:
                    colorPrint("", str(node).ljust(4, " "), end="")
                else:
                    colorPrint(AnsiColors.BLUE, str(node).ljust(4, " "), end="")
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

def createGraphFromNodeMatrix(nodeMatrix, sizeX, sizeY):
    graph = {}

    for rowIdx in range(sizeY):
        for columnIdx in range(sizeX):
            # Gather adjacent nodes of node
            node = nodeMatrix[rowIdx][columnIdx]
            adjacencyList = []

            up = None
            down = None
            left = None
            right = None

            if rowIdx-1 >= 0:
                up = nodeMatrix[rowIdx-1][columnIdx]
            if rowIdx+1 < sizeY:
                down = nodeMatrix[rowIdx+1][columnIdx]
            if columnIdx-1 >= 0:
                left = nodeMatrix[rowIdx][columnIdx-1]
            if columnIdx+1 < sizeX:
                right = nodeMatrix[rowIdx][columnIdx+1]

            if up is not None:
                adjacencyList.append(up)
            else:
                adjacencyList.append(Node({NodeStates.WALL}, rowIdx, columnIdx))

            if right is not None:
                adjacencyList.append(right)
            else:
                adjacencyList.append(Node({NodeStates.WALL}, rowIdx, columnIdx))

            if down is not None:
                adjacencyList.append(down)
            else:
                adjacencyList.append(Node({NodeStates.WALL}, rowIdx, columnIdx))

            if left is not None:
                adjacencyList.append(left)
            else:
                adjacencyList.append(Node({NodeStates.WALL}, rowIdx, columnIdx))

            graph[node] = adjacencyList
    return graph
# createGraphFromNodeMatrix end

# mapData = list: strings representing each row of map; its initial state
# mapSize = list: rows, columns
def createGraphFromMapData(mapData, mapSize):
    # Convert mapData to discrete nodes
    nodes = []

    for y, line in enumerate(mapData):
        nodeRow = []
        for x, char in enumerate(line):
            if char == NodeStates.EMPTY:
                nodeRow.append(Node({NodeStates.EMPTY, NodeStates.BULB}, x, y))
            else:
                nodeRow.append(Node({char}, x, y))
        nodes.append(nodeRow)

    # Create graph from nodes
    graph = createGraphFromNodeMatrix(nodes, mapSize[1], mapSize[0])

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

filename = input("Enter filename or press enter to use default (lightup puzzles.txt).\n") or 'lightup puzzles.txt'
parse(filename, ForwardCheckingSolver)
#input("Completed. Press any key to exit.")
