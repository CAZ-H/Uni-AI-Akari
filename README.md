# Introduction

This repo was the working repo for a university Artificial Intelligence course assignment.  
Implemented here are two constraint satisfaction problem solvers for the [Light-up / Akari](https://www.puzzle-light-up.com/) puzzle game, one using backtracking only, and one using forward-checking with constraint propagation. This assignment was completed as a pair project with another student.

Below is the handed-in writeup accompanying this repo, enhanced with some embedded images.

---

# Running

Run backtrack.py and forward-checking.py to run the solvers. Both will prompt you to provide the path to an input file containing puzzles in the form described below.

# Input

The solvers process puzzles in the following form, one at a time from a text file.  
Numbers 0-4 denote walls that can have only that many bulbs around them, and _ denotes empty space.
```
# Start
12 12
__1__2_3__1_
21____3_2___
____0___0___
__3_1_1___12
1__3__1___1_
__3____1__0_
12_4_____0_1
__3__0__20__
__011__4___2
__0___2_3___
2____1___3_3
_2_2___02_3_
# End
```

# Output

The solver will produce solutions like so, where b denotes bulbs placed on the puzzle such that they illuminate all _ tiles, no other bulbs, and satisfy the demands of all wall tiles.
```
b_1_b2b3b_1_
21b___3b2_b_
b___0_b_0__b
_b3b1_1__b12
1_b3_b1___1b
b_3b___1b_0_
12b4b____0_1
_b3b_0_b20_b
__011_b4b__2
b_0_b_2b3__b
2__b_1__b3b3
b2b2_b_02b3b
```

Backtracking:

![](/output-bk.png)

Forward-checking:

![](/output-fw.png)


# Implementation

A unique solver class is implemented for both backtrack.py and forward_checking.py.
This class implements a solve() function.

For both algorithms, processing is broken up into two stages:
- Placement of bulbs around walls
- Placement of bulbs in leftover open space

First, walls are collected from the puzzle and preprocessed to eliminate wall0s and wall4s since the state of the board around these tiles cannot change. The rest are then sorted according to the enabled heuristic:
- None: no particular order is imposed.
- Most constrained: Walls are sorted according to how many possible bulb configurations they could have.
- Most constraining: Walls are sorted according to how many tiles they would light up (constrain) when surrounded by bulbs.
- Hybrid: Both methods are used and a [0..1] score is generated from one of the heuristics and used to scale the influence of the other during sorting.

Possible bulb configurations around these walls are explored with backtracking / forward checking.

Once all walls are satisfied by bulbs, the algorithm moves into the second stage. All unlit empty spaces are collected and sorted according to the enabled heuristic:
- None: no particular order is imposed.
- Most constrained: Spaces are sorted according to how many lit tiles they're surrounded by.
- Most constraining: Spaces are sorted according to how many tiles they would light up (constrain) when changed to a bulb.
- Hybrid: Both methods are used and a [0..1] score is generated from one of the heuristics and used to scale the influence of the other during sorting.

If at any point an invalid state is reached, the algorithm backtracks, potentially back into the first stage.

For forward checking, after trying to place any bulb or bulb configuration, the resulting constraints are propagated throughought the puzzle, which in most cases eliminates the need to explore the rest of the puzzle space by forcing walls to settle on bulb configurations and propagating constraints further.

# Analysis

## Part 1
### Backtracking Results
```
map_size heuristic solved steps             
6        h1        yes    202               
6        h2        yes    9                 
6        h3        yes    9                 
8        h1        no     exceed node limit
8        h2        yes    471               
8        h3        yes    13                
10       h1        no     exceed node limit             
10       h2        no     exceed node limit
10       h3        yes    26                
```

### Forward-Checking Results
```
map_size heuristic solved steps
6        h1        yes    0     
6        h2        yes    0     
6        h3        yes    0     
8        h1        yes    0     
8        h2        yes    0     
8        h3        yes    0     
10       h1        yes    0     
10       h2        yes    0     
10       h3        yes    0     
```

In both of our algorithms, ties were not randomized, so average steps will be the same for any given puzzle
every time you run the code. The depth limit into the search node tree before giving up is 100,000.

For backtracking, 2/3 of the puzzles could be solved with at least one heuristic type, but when the size of
the puzzles increased to 10, only the hybrid heuristic can solve the puzzle. On the other hand,
forward checking can solve all the sample puzzle without even getting into the recursion phase, that is,
without generating the search nodes, the puzzle can be solved solely by constraint propagation.

## Part 2
### Backtracking Results
```
board_size  heuristic  solved  steps              time_used(s)
12          h1         no      exceed node limit  252.3618     
12          h2         no      exceed node limit  243.9480     
12          h3         no      exceed node limit  197.3970     
24          h1         no      exceed node limit  201.3647     
24          h2         no      exceed node limit  308.0707     
24          h3         no      exceed node limit  307.8786     
48          h1         no      exceed node limit  320.4833     
48          h2         no      exceed node limit  353.5627     
48          h3         no      exceed node limit  354.7329    
```

### Forward-Checking Results
```
board_size  heuristic  solved  steps             time_used(s)
12          h1         no      exceed sys limit  13.2537      
12          h2         no      exceed sys limit  16.6607      
12          h3         no      exceed sys limit  46.1944      
24          h1         yes     4                 0.1007       
24          h2         no      exceed sys limit  25.9835      
24          h3         no      exceed sys limit  58.3974      
48          h1         yes     0                 0.0527       
48          h2         yes     0                 0.0699       
48          h3         yes     0                 0.0671       
```

At the 'steps' column:
- integer means the average search nodes that were generated
- 'exceed sys limit' means the recursive search steps exceed the Python interpreter system recursion depth limit.
- 'exceed node limit' means the nodes that generated exceed the search nodes amount limit, which is 100,000 deep.

It is difficult to tell from the backtracking since our algorithms could not solve the map with different size of walls,
but clearly, we can tell that in the forward checking result, more walls reduced searching steps, and for some of them
could finish the puzzle during the propagation steps for 48 walls puzzles with very short run-time. Therefore, we can
conclude, the total number of walls does affect the performance of the algorithm; more walls results in shorter runtime.

# Analysis Summary
The solving rate regarding the data in part 1, backtracking = 66.7% versus forward checking = 100%, and on
average, the average search nodes for backtracking is at least over 100 whereas the searching nodes for
forward checking is actually 0. This is because the puzzle space is primarily being solved at the propagation phase,
which saves a lot of work compared to the pure recursion strategy applied in backtracking.

In conclusion, forward checking performs better than backtracking in most of the cases.
