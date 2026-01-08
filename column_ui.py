import pygame
import random
import columnlogic
import time 

Rows = 13
Columns = 6
Tick_Interval = 1.0

Jewels_Colors = {
    'R': (255, 0, 0),
    'G': (0, 255, 0),
    'O': (255, 128, 0),
    'P': (102, 0, 204),
    'B': (0, 0, 255),
    'Y': (255, 255, 0),
    'T': (51, 255, 255)
}

Background_Color = (255, 255, 255)
Grind_Color = (0, 0, 0)
Landing_Color = (255, 255, 0)
Matching_Color = (255, 255, 255)

Jewel_Types = list(Jewels_Colors.keys())

class ColumnsVisual:
    def __init__(self):
        pygame.init()

        self.state = columnlogic.ColumnsState(Rows, Columns)
        self.game_over = False

        self.game_width = 600
        self.game_height = 800
        self.surface = pygame.display.set_mode((self.game_width, self.game_height), pygame.RESIZABLE)
        pygame.display.set_caption("ICS H32 Columns Game")

        self.calculate_cell_size()
        self.last_tick_time = time.time()

        self.landing_flash_time = 0
        self.matching_flash_time = 0

    def get_jewel_color(self, char: str) -> tuple:
        if char in Jewels_Colors:
            return Jewels_Colors[char]
        return (128, 128, 128)

    def calculate_cell_size(self):
        padding = 20
        width = self.game_width - (2 * padding)
        height = self.game_height - (2 * padding)

        cell_width = width/Columns
        cell_height = height/Rows

        self.cell_size = min(cell_width, cell_height)

        board_width = self.cell_size * Columns
        board_height = self.cell_size * Rows

        self.board_x_component = (self.game_width - board_width) // 2
        self.board_y_component = (self.game_height - board_height) // 2

    def spawn_faller(self):
        if self.state.has_faller():
            return

        available_cols = []

        for col in range(1, Columns + 1):
            if self.state.get_cell_state(0, col - 1) != columnlogic.OCCUPIED_JEWEL:
                available_cols.append(col)

        if not available_cols:
                self.game_over = True
                return

        col = random.choice(available_cols)
        colors = [random.choice(Jewel_Types) for _ in range(3)]

        game_over = self.state.spawn_faller(col, colors)
        if game_over:
            self.game_over = True


    def input_keys(self, input):
        if self.game_over:
            return

        if not self.state.has_faller():
            return

        if input == pygame.K_LEFT:
            self.state.shift_faller_sideways(columnlogic.LEFT)
        elif input == pygame.K_RIGHT:
            self.state.shift_faller_sideways(columnlogic.RIGHT)
        elif input == pygame.K_SPACE:
            self.state.rotate_faller()

    def trigger_matching(self):
        for row in range(Rows):
            for col in range(Columns):
                if self.state.get_cell_state(row,col) == columnlogic.MATCHED_JEWEL:
                    self.matching_flash_time = time.time()
                    return

    def draw_board(self):
        self.surface.fill(Background_Color)
        now_time = time.time()
        landing_flash = (now_time - self.landing_flash_time) < 0.3
        matching_flash = (now_time - self.matching_flash_time) < 0.3

        for row in range(Rows):
            for col in range(Columns):
                x = self.board_x_component + col * self.cell_size
                y = self.board_y_component + row * self.cell_size

                contents = self.state.get_cell_contents(row, col)
                cell_state = self.state.get_cell_state(row, col)

                flash = False
                if cell_state == columnlogic.FALLER_STOPPED_CELL and landing_flash:
                    flash = True
                elif cell_state == columnlogic.MATCHED_JEWEL and matching_flash:
                    flash = True

                if contents != columnlogic.EMPTY:
                    self.draw_jewel(self.surface, x, y, contents, cell_state, flash)

                else:
                    rect = pygame.Rect(x, y, self.cell_size - 2, self.cell_size - 2)
                    pygame.draw.rect(self.surface, Grind_Color, rect, width=1)

        if self.game_over:
            font = pygame.font.Font(None, 72)
            text = font.render("GAME OVER", True, (255, 0, 0))
            text_rect = text.get_rect(center=(self.game_width // 2, self.game_height // 2))
            self.surface.blit(text, text_rect)

        pygame.display.flip()

    def draw_jewel(self, surface: pygame.Surface, x: int, y: int, char: str, state: str, flash: bool = False):
        jewel_color = self.get_jewel_color(char)

        if flash:
            if state == columnlogic.FALLER_STOPPED_CELL:
                jewel_color = tuple(min(255, c + 100) for c in jewel_color)
            elif state == columnlogic.MATCHED_JEWEL:
                jewel_color = tuple(min(255, c + 150) for c in jewel_color)

        rect = pygame.Rect(x, y, self.cell_size - 2, self.cell_size - 2)

        if state == columnlogic.FALLER_MOVING_JEWEL:
            pygame.draw.rect(surface, jewel_color, rect, border_radius=5)
            pygame.draw.rect(surface, (0,0,0), rect, width=2, border_radius=5)
        elif state == columnlogic.FALLER_STOPPED_CELL:
            pygame.draw.rect(surface, jewel_color, rect, border_radius=5)
            pygame.draw.rect(surface, Landing_Color, rect, width=3, border_radius=5)
        elif state == columnlogic.MATCHED_JEWEL:
            pygame.draw.rect(surface, jewel_color, rect, border_radius=5)
            pygame.draw.rect(surface, Matching_Color, rect, width=3, border_radius=5)

            center_x = x + self.cell_size // 2
            center_y = y + self.cell_size // 2
            size = self.cell_size // 4

            pygame.draw.line(surface, Matching_Color, (center_x - size, center_y), (center_x + size, center_y), 2)
            pygame.draw.line(surface, Matching_Color, (center_x, center_y - size), (center_x, center_y + size), 2)
            pygame.draw.line(surface, Matching_Color,(int(center_x - size*0.7), int(center_y - size*0.7)),(int(center_x + size*0.7), int(center_y + size*0.7)), 2)
            pygame.draw.line(surface, Matching_Color,(int(center_x - size*0.7), int(center_y + size*0.7)),(int(center_x + size*0.7), int(center_y - size*0.7)), 2)
        elif state == columnlogic.OCCUPIED_JEWEL:
            pygame.draw.rect(surface, jewel_color, rect, border_radius=5)
        else:
            pygame.draw.rect(surface, Grind_Color, rect, width=1)

    def run(self):
        clock = pygame.time.Clock()
        running = True

        self.spawn_faller()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.game_width = event.w
                    self.game_height = event.h
                    self.surface = pygame.display.set_mode((self.game_width, self.game_height), pygame.RESIZABLE)
                    self.calculate_cell_size()
                elif event.type == pygame.KEYDOWN:
                    self.input_keys(event.key)
            now_time = time.time()
            if now_time - self.last_tick_time >= Tick_Interval:
                if not self.game_over:
                    had_faller = self.state.has_faller()

                    was_moving = False
                    if had_faller:
                        for row in range(Rows):
                            for col in range(Columns):
                                state = self.state.get_cell_state(row, col)
                                if state == columnlogic.FALLER_MOVING_JEWEL:
                                    was_moving = True
                                    break
                            if was_moving:
                                break
                    self.game_over = self.state.tick()

                    if had_faller and was_moving:
                        is_stopped = False
                        for row in range(Rows):
                            for col in range(Columns):
                                state = self.state.get_cell_state(row, col)
                                if state == columnlogic.FALLER_STOPPED_CELL:
                                    is_stopped = True
                                    break
                            if is_stopped:
                                break
                        if is_stopped:
                            self.landing_flash_time = time.time()
                    self.trigger_matching()

                    if not self.state.has_faller() and not self.game_over:
                        self.spawn_faller()
                self.last_tick_time = now_time

            self.draw_board()
            clock.tick(60)

        pygame.quit()
            


if __name__ == '__main__':
    ColumnsVisual().run()

                
                
