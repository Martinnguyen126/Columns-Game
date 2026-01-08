EMPTY_JEWEL = 'EMPTY STATE'
FALLER_MOVING_JEWEL = 'FALLER_MOVING STATE'
FALLER_STOPPED_CELL = 'FALLER_STOPPED STATE'
OCCUPIED_JEWEL = 'OCCUPIED STATE'
MATCHED_JEWEL = 'MATCHED STATE'
FALLER_STOPPED = 10
FALLER_MOVING = 11
LEFT = -1
RIGHT = 1
DOWN = 0
DOWN_LEFT = 2
DOWN_RIGHT = 3
NO_GEM = 'NONE'
EMPTY = ' '


def is_matchable_state(state: str) -> bool:
    return state == OCCUPIED_JEWEL or state == MATCHED_JEWEL


class ColumnsState:
    def __init__(self, rows: int, cols: int):
        self._rows = rows
        self._columns = cols
        self._boardRows = []
        self._boardStates = []
        self._faller = _Faller()
        for i in range(rows):
            row = []
            stateRow = []
            for j in range(cols):
                row.append(EMPTY)
                stateRow.append(EMPTY_JEWEL)
            self._boardRows.append(row)
            self._boardStates.append(stateRow)

    def get_rows(self) -> int:
        return self._rows

    def get_columns(self) -> int:
        return self._columns

    def get_cell_state(self, row: int, col: int) -> str:
        if row < 0 or row >= self._rows or col < 0 or col >= self._columns:
            return EMPTY_JEWEL
        return self._boardStates[row][col]

    def get_cell_contents(self, row: int, col: int) -> str:
        if row < 0 or row >= self._rows or col < 0 or col >= self._columns:
            return EMPTY
        return self._boardRows[row][col]

    def set_cell_contents(self, row: int, col: int, contents: str) -> None:
        if row < 0 or row >= self._rows or col < 0 or col >= self._columns:
            return
        self._boardRows[row][col] = contents

    def set_cell_state(self, row: int, col: int, state: str) -> None:
        if row < 0 or row >= self._rows or col < 0 or col >= self._columns:
            return
        self._boardStates[row][col] = state

    def set_cell(self, row: int, col: int, contents: str, state: str) -> None:
        if row < 0 or row >= self._rows or col < 0 or col >= self._columns:
            return
        self.set_cell_contents(row, col, contents)
        self.set_cell_state(row, col, state)

    def initialize_board_contents(self, contents: list) -> None:
        for row in range(self.get_rows()):
            for col in range(self.get_columns()):
                value = contents[row][col]
                if value == EMPTY:
                    self.set_cell(row, col, EMPTY, EMPTY_JEWEL)
                else:
                    self.set_cell(row, col, value, OCCUPIED_JEWEL)

        self._gem_gravity()
        # Find and mark matches, but don't clear them yet (so they display with asterisks)
        # The clearing will happen on the first tick
        # This matches the teacher's example where matches are shown with asterisks before clearing
        self._find_and_mark_matches()

    def spawn_faller(self, column: int, faller: list) -> bool:
        """
        Spawn a new faller in the specified column.
        Returns True if game should end (column is full), False otherwise.
        """
        if self._faller.active:
            return False
        
        col_index = column - 1
        # Check if column is already full (has a frozen jewel at row 0)
        if self.get_cell_state(0, col_index) == OCCUPIED_JEWEL:
            # Game ends when trying to create faller in full column
            return True

        self._faller.active = True
        self._faller.contents = faller
        self._faller.set_row(-1)
        self._faller.set_col(col_index)
        self._faller.state = FALLER_MOVING
        self.update_faller_state()
        return False

    def has_faller(self) -> bool:
        return self._faller.active

    def rotate_faller(self) -> None:
        if not self._faller.active:
            return

        # Rotate: bottom becomes top, others shift down
        bottom = self._faller.contents[2]
        middle = self._faller.contents[1]
        top = self._faller.contents[0]

        self._faller.contents = [bottom, top, middle]

        self.update_faller_state()

    def shift_faller_sideways(self, direction: int) -> None:
        if not self._faller.active:
            return

        if direction != RIGHT and direction != LEFT:
            return

        if (direction == LEFT and self._faller.get_col() == 0) or (direction == RIGHT and self._faller.get_col() == self.get_columns() - 1):
            return

        targetColumn = self._faller.get_col() + direction
        
        # Check if movement is blocked
        bottom_row = self._faller.get_row()
        for i in range(3):
            check_row = bottom_row - i
            if check_row < 0:
                continue
            if check_row >= 0 and self.get_cell_state(check_row, targetColumn) == OCCUPIED_JEWEL:
                return
        
        # Clear old column before moving (update_faller_state only clears the current column)
        old_col = self._faller.get_col()
        for row in range(self.get_rows()):
            if self.get_cell_state(row, old_col) == FALLER_MOVING_JEWEL or self.get_cell_state(row, old_col) == FALLER_STOPPED_CELL:
                self.set_cell(row, old_col, EMPTY, EMPTY_JEWEL)
        
        self._faller.set_col(targetColumn)
        self.update_faller_state()

    def _gem_gravity(self) -> None:
        changed = True
        while changed:
            changed = False
            for col in range(self.get_columns()):
                for row in range(self.get_rows() - 2, -1, -1):
                    state = self.get_cell_state(row, col)
                    if state == FALLER_MOVING_JEWEL or state == FALLER_STOPPED_CELL:
                        continue
                    if state == OCCUPIED_JEWEL or state == MATCHED_JEWEL:
                        if not self._is_solid(row + 1, col):
                            contents = self.get_cell_contents(row, col)
                            self.set_cell(row + 1, col, contents, state)
                            self.set_cell(row, col, EMPTY, EMPTY_JEWEL)
                            changed = True

    def _matching(self) -> bool:
        # First, remove matched jewels
        for row in range(self.get_rows()):
            for col in range(self.get_columns()):
                if self.get_cell_state(row, col) == MATCHED_JEWEL:
                    self.set_cell(row, col, EMPTY, EMPTY_JEWEL)

        # Apply gravity
        self._gem_gravity()

        # Find new matches
        found_match = False
        self.match_x_axis()
        self.match_y_axis()
        self.match_diagonal()
        
        # Check if any matches were found
        for row in range(self.get_rows()):
            for col in range(self.get_columns()):
                if self.get_cell_state(row, col) == MATCHED_JEWEL:
                    found_match = True
                    break
            if found_match:
                break
        
        return found_match

    def _find_and_mark_matches(self) -> None:
        """Find and mark matches without clearing them (for display purposes)."""
        self.match_x_axis()
        self.match_y_axis()
        self.match_diagonal()

    def match_x_axis(self) -> None:
        for currentRow in range(self.get_rows()):
            matches = 0
            gem = NO_GEM
            for col in range(self.get_columns()):
                contents = self.get_cell_contents(currentRow, col)
                state = self.get_cell_state(currentRow, col)
                is_Matchable = is_matchable_state(state)
                cell_Match = (contents == gem and is_Matchable)

                if cell_Match:
                    matches += 1
                    if col == self.get_columns() - 1 and matches >= 3:
                        self._mark_matched_cells(currentRow, col, LEFT, matches)
                else:
                    if matches >= 3:
                        self._mark_matched_cells(currentRow, col - 1, LEFT, matches)

                    if is_matchable_state(state):
                        gem = contents
                        matches = 1
                    else:
                        gem = NO_GEM
                        matches = 0

    def match_y_axis(self) -> None:
        for currentCol in range(self.get_columns()):
            matches = 0
            gem = NO_GEM
            for row in range(self.get_rows() - 1, -1, -1):
                contents = self.get_cell_contents(row, currentCol)
                state = self.get_cell_state(row, currentCol)
                is_Matchable = is_matchable_state(state)
                cell_Match = (contents == gem and is_Matchable)

                if cell_Match:
                    matches += 1

                if not cell_Match or row == 0:
                    if row == 0 and cell_Match:
                        if matches >= 3:
                            self._mark_matched_cells(row, currentCol, DOWN, matches)
                    elif matches >= 3:
                        start_row = row + 1
                        self._mark_matched_cells(start_row, currentCol, DOWN, matches)

                    if is_matchable_state(state):
                        gem = contents
                        matches = 1
                    else:
                        gem = NO_GEM
                        matches = 0

    def match_diagonal(self) -> None:
        # Check diagonal from top-left to bottom-right
        for start_row in range(self.get_rows()):
            for start_col in range(self.get_columns()):
                matches = 0
                gem = NO_GEM
                row = start_row
                col = start_col
                while row < self.get_rows() and col < self.get_columns():
                    contents = self.get_cell_contents(row, col)
                    state = self.get_cell_state(row, col)
                    is_Matchable = is_matchable_state(state)
                    cell_Match = (contents == gem and is_Matchable)

                    if cell_Match:
                        matches += 1
                    else:
                        if matches >= 3:
                            self._mark_matched_cells(row - 1, col - 1, DOWN_RIGHT, matches)

                        if is_matchable_state(state):
                            gem = contents
                            matches = 1
                        else:
                            gem = NO_GEM
                            matches = 0

                    row += 1
                    col += 1

                if matches >= 3:
                    self._mark_matched_cells(row - 1, col - 1, DOWN_RIGHT, matches)

        # Check diagonal from top-right to bottom-left
        for start_row in range(self.get_rows()):
            for start_col in range(self.get_columns()):
                matches = 0
                gem = NO_GEM
                row = start_row
                col = start_col
                while row < self.get_rows() and col >= 0:
                    contents = self.get_cell_contents(row, col)
                    state = self.get_cell_state(row, col)
                    is_Matchable = is_matchable_state(state)
                    cell_Match = (contents == gem and is_Matchable)

                    if cell_Match:
                        matches += 1
                    else:
                        if matches >= 3:
                            self._mark_matched_cells(row - 1, col + 1, DOWN_LEFT, matches)

                        if is_matchable_state(state):
                            gem = contents
                            matches = 1
                        else:
                            gem = NO_GEM
                            matches = 0

                    row += 1
                    col -= 1

                if matches >= 3:
                    self._mark_matched_cells(row - 1, col + 1, DOWN_LEFT, matches)

    def _mark_matched_cells(self, row: int, col: int, direction: int, amount: int) -> None:
        if direction == LEFT:
            for i in range(amount):
                targetColumn = col - i
                if targetColumn >= 0:
                    self.set_cell_state(row, targetColumn, MATCHED_JEWEL)
        elif direction == DOWN:
            for i in range(amount):
                targetRow = row + i
                if targetRow < self.get_rows():
                    self.set_cell_state(targetRow, col, MATCHED_JEWEL)
        elif direction == DOWN_LEFT:
            for i in range(amount):
                targetRow = row + i
                targetCol = col - i
                if targetRow < self.get_rows() and targetCol >= 0:
                    self.set_cell_state(targetRow, targetCol, MATCHED_JEWEL)
        elif direction == DOWN_RIGHT:
            for i in range(amount):
                targetRow = row + i
                targetCol = col + i
                if targetRow < self.get_rows() and targetCol < self.get_columns():
                    self.set_cell_state(targetRow, targetCol, MATCHED_JEWEL)

    def _is_solid(self, row: int, col: int) -> bool:
        if row >= self.get_rows():
            return True

        if self.get_cell_state(row, col) == OCCUPIED_JEWEL:
            return True

        return False

    def update_faller_state(self) -> None:
        if not self._faller.active:
            return

        # Clear old faller positions in this column FIRST
        col = self._faller.get_col()
        for row in range(self.get_rows()):
            if self.get_cell_state(row, col) == FALLER_MOVING_JEWEL or self.get_cell_state(row, col) == FALLER_STOPPED_CELL:
                self.set_cell(row, col, EMPTY, EMPTY_JEWEL)

        # The faller's row represents where the bottom jewel would be
        # Check if faller can move down (check the row below the bottom jewel)
        bottom_row = self._faller.get_row()
        targetRow = bottom_row + 1
        # Special case: when faller is at row -1, bottom is displayed at row 0, so check row 1
        if bottom_row == -1:
            targetRow = 1
        
        if self._is_solid(targetRow, self._faller.get_col()):
            state = FALLER_STOPPED_CELL
            self._faller.state = FALLER_STOPPED
        else:
            state = FALLER_MOVING_JEWEL
            self._faller.state = FALLER_MOVING

        # Draw faller in new positions
        # Bottom jewel is at faller.row, middle at faller.row-1, top at faller.row-2
        # When faller.row = -1, only bottom jewel is visible at row 0
        for i in range(3):
            row = bottom_row - i  # i=0: bottom, i=1: middle, i=2: top
            # Special case: when faller is at row -1, bottom jewel appears at row 0
            if row == -1 and i == 0:
                row = 0
            jewel_content = self._faller.contents[2 - i]  # contents[2] is bottom, contents[1] is middle, contents[0] is top
            if row >= 0 and row < self.get_rows():
                self.set_cell(row, col, jewel_content, state)

    def move_faller_down(self) -> None:
        if not self._faller.active:
            return
        
        bottom_row = self._faller.get_row()
        check_row = bottom_row + 1
        # If faller is at row -1, bottom jewel is displayed at row 0, so check row 1
        if bottom_row == -1:
            check_row = 1
        
        if self._is_solid(check_row, self._faller.get_col()):
            return

        # When faller is at row -1, moving down should take it to row 1 (skipping row 0)
        # because row 0 is where it's currently displayed
        if bottom_row == -1:
            self._faller.set_row(1)
        else:
            self._faller.set_row(self._faller.get_row() + 1)
        self.update_faller_state()

    def tick(self) -> bool:
        """
        Handle one tick of game time.
        Returns True if game should end, False otherwise.
        """
        # First, handle any existing matched jewels (clear them and find new matches)
        # This happens on every tick, even if there's no active faller
        # Clear existing matches, apply gravity, then find and mark new matches (but don't clear them yet)
        has_matched = False
        for row in range(self.get_rows()):
            for col in range(self.get_columns()):
                if self.get_cell_state(row, col) == MATCHED_JEWEL:
                    has_matched = True
                    break
            if has_matched:
                break
        
        if has_matched:
            # Clear matched jewels
            for row in range(self.get_rows()):
                for col in range(self.get_columns()):
                    if self.get_cell_state(row, col) == MATCHED_JEWEL:
                        self.set_cell(row, col, EMPTY, EMPTY_JEWEL)
            
            # Apply gravity
            self._gem_gravity()
            
            # Find and mark new matches (but don't clear them - they'll be displayed with asterisks)
            self._find_and_mark_matches()
        
        if not self._faller.active:
            return False

        # If faller was stopped (landed), freeze it
        if self._faller.state == FALLER_STOPPED:
            # Freeze the faller - convert to occupied jewels
            faller_col = self._faller.get_col()
            for i in range(3):
                row = self._faller.get_row() - i
                if row >= 0:
                    contents = self.get_cell_contents(row, faller_col)
                    self.set_cell(row, faller_col, contents, OCCUPIED_JEWEL)
            
            # Check if all three jewels are visible (top jewel must be at row >= 0)
            top_jewel_row = self._faller.get_row() - 2
            if top_jewel_row < 0:
                # Not all jewels are visible - game over
                return True
            
            self._faller.active = False
            
            # Find and mark matches (but don't clear them yet - they'll be cleared on next tick)
            # This allows matched jewels to be displayed with asterisks before being cleared
            self._find_and_mark_matches()
            
            # After matching, check if there are any jewels above row 0 in the column
            # This would indicate that not all three jewels fit
            for row in range(self.get_rows()):
                if self.get_cell_state(row, faller_col) == OCCUPIED_JEWEL:
                    # Found first occupied cell, check if there are any above it
                    if row > 0:
                        # Check rows above
                        for check_row in range(row):
                            if self.get_cell_state(check_row, faller_col) == OCCUPIED_JEWEL:
                                # There's a jewel above - game over
                                return True
                    break
            
            return False
        else:
            # Faller is moving, try to move it down
            # Check if it can move down
            # When faller is at row -1, bottom jewel is at row 0, so check row 1
            bottom_row = self._faller.get_row()
            check_row = bottom_row + 1
            # If faller is at row -1, the actual bottom position is row 0, so check row 1
            if bottom_row == -1:
                check_row = 1
            
            if self._is_solid(check_row, self._faller.get_col()):
                # Can't move down - land it (mark as stopped)
                self._faller.state = FALLER_STOPPED
                self.update_faller_state()
            else:
                # Can move down
                self.move_faller_down()
            return False


class _Faller:
    def __init__(self):
        self.active = False
        self.row = 0
        self.column = 0
        self.contents = [EMPTY, EMPTY, EMPTY]
        self.state = FALLER_MOVING

    def get_row(self) -> int:
        return self.row

    def get_col(self) -> int:
        return self.column

    def set_row(self, row: int) -> None:
        self.row = row

    def set_col(self, col: int) -> None:
        self.column = col
