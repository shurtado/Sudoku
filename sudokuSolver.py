"""

The following code was taken from Mark Byer's shortest Python code solver. And was re-writen in 
a comprehensible manner.
References:

http://www.scottkirkwood.com/2006/07/shortest-sudoku-solver-in-python.html
http://stackoverflow.com/questions/201461/shortest-sudoku-solver-in-python-how-does-it-work

"""
import sys


def same_row(i,j): return (i/9 == j/9)
def same_col(i,j): return (i-j) % 9 == 0
def same_block(i,j): return (i/27 == j/27 and i%9/3 == j%9/3)
def split(s, size): return [s[i:i+size] for i in range(0, len(s), size)]

def solve(a):
  i = a.find('0')
  if i == -1:
    print "\nSudoku Puzzle Solved: \n"
    puzzle = split(a,9)
    for x in range(9):  
        print puzzle[x]
    sys.exit(0)

  excluded_numbers = set()
  for j in range(81):
    if same_row(i,j) or same_col(i,j) or same_block(i,j):
      excluded_numbers.add(a[j])

  for m in '123456789':
    if m not in excluded_numbers:
      # At this point, m is not excluded by any row, column, or block, so let's place it and recurse
      solve(a[:i]+m+a[i+1:])

