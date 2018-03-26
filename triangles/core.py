from triangles.models import deep_are_equal


def increment_boards(boards):

    new_boards = []
    won_boards = []
    for board in boards:

        moves = board.moves()
        if len(moves) < 1:
            continue

        for start, end, jump in moves:
            new_board = board.copy()
            new_board.move(start, end, jump)

            if new_board.is_won():
                won_boards.append(new_board)
            else:
                new_boards.append(new_board)

    return new_boards, won_boards


def find_solutions(board):

    # Establish a root board
    boards = [board]
    won_boards = []
    solution_found = False

    while len(boards) > 0:
        initial_boards_count = len(boards)
        boards, won_boards = increment_boards(boards)
        print('Incremented boards, {} boards became {}'.format(initial_boards_count, len(boards)))
        

    return won_boards


def consolidate_solutions(boards):

    # Validate that passed boards have been won
    for board in boards:
        if not board.is_won():
            return ValueError('Board {} has not been won'.format(board.__repr__()))

    solution_sets = []
    # Group matching solutions
    for board in boards:
        if not solution_sets:
            solution_sets.append([board])
            continue

        for solution_set in solution_sets:
            if board == solution_set[0]:
                solution_set.append(board)
                break
        else:
            solution_sets.append([board])

    return solution_sets

