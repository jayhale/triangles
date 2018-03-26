# coding: utf8

class Board:
    """Represents the state of the game board at any time

    Board layout:

    0     1     2     3     4
       5     6     7     8
          9     10    11
             12    13
                14

    The game begins with one of the 15 pin positions empty (status=False) and all others occupied
    (status=True). The game is won by reducing the number of pins on the board to 1. Pins are
    removed by jumping: the jumped pin is removed. Jumps are valid only for immediately adjacent
    pins. See Board.valid_moves_for_position() for valid jumps.

    """

    def __init__(self, empty_position=14, previous_board=None):

        # Check the empty position:
        self._validate_position(empty_position, 'empty_position')

        # Set up an initial board
        self._pins = {}
        for position in range(15):
            if position == empty_position:
                self._pins[position] = False
            else:
                self._pins[position] = True

        self.previous_board = previous_board
        self.empty_position = empty_position


    def __eq__(self, board):
        """If the two boards have pins in all of the same locations, then they are equal"""
        comparisons = [self.pin_status(pos) == status for pos, status in board.pins.items()]
        return not False in comparisons


    def __repr__(self):
        return '<Board at {}, won={}>'.format(id(self), self.is_won())


    def __str__(self):
        return ''.join(['1' if s else '0' for p, s in self.pins.items()])


    def copy(self):
        """Return a copy of the board, with the new board's `previous_board` set to the board being
        copied
        """
        board = Board(self.empty_position, previous_board=self)
        for position, status in self.pins.items():
            board.set_pin_status(position, status)
        return board


    @classmethod
    def from_configuration_id(cls, conf_id):
        key = '{:015b}'.format(conf_id)
        board = cls()

        for pos,char in enumerate(key):
            if char == '1':
                board.set_pin_status(pos, True)
                continue

            if char == '0':
                board.set_pin_status(pos, False)
                continue

            raise ValueError('Invalid character in key: {}'.format(char))

        return board


    def is_won(self):
        """Return True if the game has been won (just one pin remaining)"""
        return sum(v == True for v in self._pins.values()) == 1


    def move(self, start, end, jump):
        """Execute a move and update the board"""
        self._validate_position(start, 'start')
        self._validate_position(end, 'end')
        self._validate_position(jump, 'jump')

        # Check that the starting position is occupied
        if not self.pin_status(start):
            raise ValueError('start is empty')

        # Check that the ending position is empty
        if self.pin_status(end):
            raise ValueError('end is occupied')

        # Check that the jump position is occupied
        if not self.pin_status(jump):
            raise ValueError('jump is empty')

        # Update the board
        self.set_pin_status(start, False)
        self.set_pin_status(jump, False)
        self.set_pin_status(end, True)


    def moves(self):
        """Return a list of all possible moves for the current configuration of the board"""
        moves = []
        for position in self.occupied_positions():
            moves.extend(self.moves_for_position(position))

        return moves


    def moves_for_position(self, position):
        """Return a list of moves for a given position, taking in to account the status of pins
        If no moves are possible, and empty list is returned
        """
        self._validate_position(position)

        # If no pin is present, return no moves
        if not self._pins[position]:
            return []

        moves = []
        for start, end, jump in self.valid_moves_for_position(position):
            # Check that the ending position is empty
            if self.pin_status(end):
                continue

            # Check that the jump position is occupied
            if not self.pin_status(jump):
                continue

            moves.append((start, end, jump))

        return moves


    def occupied_positions(self):
        """Return a list of all positions that are occupied"""
        return [position for position, status in self._pins.items() if status == True]


    def pin_status(self, position):
        """Return the status of a single pin"""
        self._validate_position(position)
        return self._pins[position]


    @property
    def pins(self):
        """Access the dictionary of pins directly"""
        return self._pins


    def transform(self, position_substitutions):
        """Transforms the current board according to the position substitutions passed"""

        # Copy the current pin statuses
        prev_pins = self.pins.copy()

        # Update the statuses
        for prev_pos, new_pos in position_substitutions:
            self._validate_position(prev_pos, 'prev_pos')
            self._validate_position(new_pos, 'new_pos')
            self.set_pin_status(new_pos, prev_pins[prev_pos])


    @staticmethod
    def valid_transformations():
        """Return a tuple of valid transformations. Each member is a tuple of tuples representing
        position substitutions that are valid if all taken together"""
        return (
            (
                'Reflection',
                (
                    (0,4), (1,3), (2,2), (3,1), (4,0),
                    (5,8), (6,7), (7,6), (8,5),
                    (9,11), (10,10), (11,9),
                    (12,13), (13,12),
                    (14,14)
                )
            ),
            (
                'Clockwise rotation',
                (
                    (0,14), (1,12), (2,9), (3,5), (4,0),
                    (5,13), (6,10), (7,6), (8,1),
                    (9,11), (10,7), (11,2),
                    (12,8), (13,3),
                    (14,4)
                )
            ),
            (
                'Counter-clockwise rotation',
                (
                    (0,4), (1,8), (2,11), (3,13), (4,14),
                    (5,3), (6,7), (7,10), (8,12),
                    (9,2), (10,6), (11,9),
                    (12,1), (13,5),
                    (14,0)
                )
            ),
            (
                'Clockwise rotation and reflection',
                (
                    (0,0), (1,5), (2,9), (3,12), (4,14),
                    (5,1), (6,6), (7,10), (8,13),
                    (9,2), (10,7), (11,11),
                    (12,3), (13,8),
                    (14,4)
                )
            ),
            (
                'Counter-clockwise rotation and reflection',
                (
                    (0,14), (1,13), (2,11), (3,8), (4,4),
                    (5,12), (6,10), (7,7), (8,3),
                    (9,9), (10,6), (11,2),
                    (12,5), (13,1),
                    (14,0)
                )
            )
        )


    def set_pin_status(self, position, status):
        """Set the status of a single pin"""
        self._validate_position(position)
        self._pins[position] = status


    def to_pretty_str(self, indent=0):
        """Print a pretty representation of the board to the screen"""
        format_vals = ['●' if v else '○' for k,v in self.pins.items()]
        format_str = ' '*indent + ' {}   {}   {}   {}   {}\n' \
                     + ' '*indent + '   {}   {}   {}   {}\n' \
                     + ' '*indent + '     {}   {}   {}\n' \
                     + ' '*indent + '       {}   {}\n' \
                     +  ' '*indent + '         {}'
        return format_str.format(*format_vals)


    @staticmethod
    def valid_moves_for_position(position):
        """Return all rule-abiding moves for a position, ignoring the status of any pins
        Moves are returned as a tuple-of-tuples. Each inner tuple object represents one valid move
        in the form `(starting position, ending position, jumped position)`
        """
        Board._validate_position(position)

        if position == 0:
            return (
                (0, 2, 1),
                (0, 9, 5)
            )
        elif position == 1:
            return (
                (1, 3, 2),
                (1, 10, 6)
            )
        elif position == 2:
            return (
                (2, 0, 1),
                (2, 9, 6),
                (2, 11, 7),
                (2, 4, 3)
            )
        elif position == 3:
            return (
                (3, 1, 2),
                (3, 10, 7)
            )
        elif position == 4:
            return (
                (4, 2, 3),
                (4, 11, 8)
            )
        elif position == 5:
            return (
                (5, 7, 6),
                (5, 12, 9)
            )
        elif position == 6:
            return (
                (6, 8, 7),
                (6, 13, 10)
            )
        elif position == 7:
            return (
                (7, 5, 6),
                (7, 12, 10)
            )
        elif position == 8:
            return (
                (8, 6, 7),
                (8, 13, 11)
            )
        elif position == 9:
            return (
                (9, 0, 5),
                (9, 2, 6),
                (9, 11, 10),
                (9, 14, 12)
            )
        elif position == 10:
            return (
                (10, 1, 6),
                (10, 3, 7)
            )
        elif position == 11:
            return (
                (11, 4, 8),
                (11, 2, 7),
                (11, 9, 10),
                (11, 14, 13)
            )
        elif position == 12:
            return (
                (12, 5, 9),
                (12, 7, 10)
            )
        elif position == 13:
            return (
                (13, 6, 10),
                (13, 8, 11)
            )
        else:
            return (
                (14, 9, 12),
                (14, 11, 13)
            )


    @staticmethod
    def _validate_position(position, name=None):
        """Validate a position parameter"""
        if not (0 <= position <= 14):
            error = 'position out of range (must be 0 through 14)'
            if name:
                error = '{} out of range (must be 0 through 14)'.format(name)
            raise ValueError(error)
