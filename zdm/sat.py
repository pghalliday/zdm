# -*- coding: utf-8 -*-

from __future__ import print_function
from collections import deque
from sys import stderr, argv

# TODO: why isn't this an instance method of the class?
def setup_watchlist(instance):
    # create a double ended queue for every possible literal (2 * no of variables)
    # aparently double ended queues are faster for this (TODO: check why?)
    watchlist = [deque() for __ in range(2 * len(instance.variables))]
    for clause in instance.clauses:
        # append the clause to the queue associated with
        # the first literal in the clause (ie. watch the first
        # literal in the clause)
        watchlist[clause[0]].append(clause)
    return watchlist

def update_watchlist(instance,
                     watchlist,
                     false_literal,
                     assignment,
                     verbose):
    """
    Updates the watchlist after literal 'false_literal' was just assigned
    False by making any clause watching false_literal watch something else.
    Returns False if it is impossible to do so, meaning a clause is contradicted
    by the current assignment.
    """
    # TODO: why don't we also update true_literal watchlists?
    # loop until watch list is empty
    while watchlist[false_literal]:
        clause = watchlist[false_literal][0]
        found_alternative = False
        for alternative in clause:
            # get the alternative variable index
            v = alternative >> 1
            # is the alternative negated
            a = alternative & 1
            # if not assigned yet or the assignment is different
            # then we can use this alternative and update the
            # watch list
            # TODO: I still don't get what is going on here, maybe
            # it will be apparent after the next step where we
            # create/update assigments
            if assignment[v] is None or assignment[v] == a ^ 1:
                found_alternative = True
                del watchlist[false_literal][0]
                watchlist[alternative].append(clause)
                break

        if not found_alternative:
            if verbose:
                #dump_watchlist(instance, watchlist)
                print('Current assignment: {}'.format(
                      instance.assignment_to_string(assignment)),
                      file=stderr)
                print('Clause {} contradicted.'.format(
                      instance.clause_to_string(clause)),
                      file=stderr)
            return False

    return True


def solve(instance, watchlist, assignment, d, verbose):
    """
    Recursively solve SAT by assigning to variables d, d+1, ..., n-1. Assumes
    variables 0, ..., d-1 are assigned so far. A generator for all the satisfying
    assignments is returned.
    """
    if d == len(instance.variables):
        yield assignment
        return

    for a in [0, 1]:
        if verbose:
            print('Trying {} = {}'.format(instance.variables[d], a),
                  file=stderr)
        assignment[d] = a
        if update_watchlist(instance,
                            watchlist,
                            (d << 1) | a,
                            assignment,
                            verbose):
            for a in solve(instance, watchlist, assignment, d + 1, verbose):
                yield a

    assignment[d] = None


class SATInstance(object):
    def __init__(self):
        # list of variables
        self.variables = []
        # dictionary of variables to their indices
        self.variable_table = dict()
        # list of clauses
        self.clauses = []

    # TODO: refactor this as we will not be using lines
    # we probably want functions to add clauses and then
    # add literals to clauses by name and negated -
    # no point going through a string representation of
    # the clause (except maybe for logging/debugging)
    # Perhaps add a class for a clause?
    def parse_and_add_clause(self, line):
        clause = []
        for literal in line.split():
            # will add 1 to literal if negated
            negated = 1 if literal.startswith('-') else 0
            # overloaded use of negated as also the number
            # of characters to strip to get the real variable name
            variable = literal[negated:]
            # assign an index to the variable and store it
            # in a dictionary for fast lookups if an index has
            # not been assigned already
            if variable not in self.variable_table:
                self.variable_table[variable] = len(self.variables)
                self.variables.append(variable)
            # encode the literal for this clause, we do this by
            # (2 * index) + (1 * negated) from which we can
            # easily reverse to get the index and the negated values
            encoded_literal = self.variable_table[variable] << 1 | negated
            clause.append(encoded_literal)
        # convert the clause array to a tuple and append to our clauses
        # TODO: why is this better as a tuple?
        self.clauses.append(tuple(set(clause)))

    # TODO: we won't really need to read clauses from a file
    # this will be refactored out
    @classmethod
    def from_file(cls, file):
        instance = cls()
        for line in file:
            line = line.strip()
            if len(line) > 0 and not line.startswith(('c', 'p')):
                for clause in line.split(' 0'):
                    clause = clause.strip()
                    if len(clause) > 0:
                        instance.parse_and_add_clause(clause)
        return instance

    # TODO: later we will not be interested in strings
    # and will likely want to convert to a structure
    def literal_to_string(self, literal):
        # see how easy it is to revert the encoded literal
        s = '-' if literal & 1 else ''
        return s + self.variables[literal >> 1]

    # TODO: later we will not be interested in strings
    # and will likley want to convert to a structure
    def clause_to_string(self, clause):
        return ' '.join(self.literal_to_string(l) for l in clause)

    # TODO: later we will not be interested in strings
    # and will likley want to convert to a structure
    def assignment_to_string(self, assignment, brief=False, starting_with=''):
        # The assignment is an array of 1s and 0s corresponding
        # to the array of variables - 1 means include the variable, 0
        # means don't include the variable
        literals = []
        # We create a list of (assignment, variable) tuples filtered
        # by the starting_with argument, then we convert to the string literal
        # for each variable (if brief is set then we just skip the variables
        # not included and if not brief then we add them with the negated
        # indicator)
        for a, v in ((a, v) for a, v in zip(assignment, self.variables)
                     if v.startswith(starting_with)):
            if a == 0 and not brief:
                literals.append('-' + v)
            elif a:
                literals.append(v)
        return ' '.join(literals)

if __name__ == '__main__':
    with open(argv[1]) as f:
        contents = f.readlines()
    instance = SATInstance.from_file(contents)
    watchlist = setup_watchlist(instance)
    generator = solve(instance,
                      watchlist,
                      [None] * len(instance.variables),
                      0, len(argv) > 2)
    for assignment in generator:
        print(instance.assignment_to_string(assignment))
