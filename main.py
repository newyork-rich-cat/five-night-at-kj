import pygame
import random
import sys
import time
import os

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_GRAY = (64, 64, 64)
YELLOW = (255, 255, 0)
OFFICE_COLOR = (0, 128, 255)  # Color to highlight the "office"

class Room:
    def __init__(self, name, x, y, width, height, connected_rooms):
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        self.connected_rooms = connected_rooms
        self.light_on = False

    @property
    def center(self):
        return (self.rect.centerx, self.rect.centery)

class Hallway:
    def __init__(self, name, room1, room2, connected_rooms, block_cost):
        self.name = name
        self.room1 = room1
        self.room2 = room2
        self.connected_rooms = connected_rooms
        self.blocked = False
        self.block_cost = block_cost
        self.start_pos = None
        self.end_pos = None
        self.rect = None

    def update_positions(self, rooms):
        self.start_pos = rooms[self.room1].center
        self.end_pos = rooms[self.room2].center
        width = 20  # Width of hallway
        dx = self.end_pos[0] - self.start_pos[0]
        dy = self.end_pos[1] - self.start_pos[1]
        if abs(dx) < abs(dy):
            x = min(self.start_pos[0], self.end_pos[0]) - width // 2
            y = min(self.start_pos[1], self.end_pos[1])
            w = width
            h = abs(dy)
            x = (self.start_pos[0] + self.end_pos[0]) // 2 - width // 2
            self.rect = pygame.Rect(x, y, w, h)
        else:
            x = min(self.start_pos[0], self.end_pos[0])
            y = min(self.start_pos[1], self.end_pos[1]) - width // 2
            w = abs(dx)
            h = width
            y = (self.start_pos[1] + self.end_pos[1]) // 2 - width // 2
            self.rect = pygame.Rect(x, y, w, h)

class Animatronic:
    def __init__(self, name, starting_room, image_path, jumpscare_image_path, move_probability=1.0, teleport_probability=0.0, step_size=1):
        self.name = name
        self.current_room = starting_room
        self.move_probability = move_probability
        self.teleport_probability = teleport_probability
        self.step_size = step_size
        # Load the character image and jumpscare image
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (40, 40))  # Scale to fit in rooms
        self.jumpscare_image = pygame.image.load(jumpscare_image_path)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Five Nights at Freddy's")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        self.battery = 100
        self.turns_remaining = 20
        self.game_over = False
        self.won = False
        self.death_reason = ""
        self.battery_drained = False
        self.last_turn_time = time.time()
        self.jumpscare_image = None
        self.jumpscare_opacity = 0

        self.rooms = {
            'office': Room('Office', 462, 600, 100, 80, ['left_hall', 'right_hall']),
            'stage': Room('Stage', 462, 100, 100, 80, ['stage_left', 'stage_right']),
            'bathroom': Room('Bathroom', 462, 350, 100, 80, ['bath_left', 'bath_right']),
            'party': Room('Party Room', 262, 225, 100, 80, ['stage_left', 'left_hall', 'party_left']),
            'arcade': Room('Arcade', 262, 475, 100, 80, ['left_hall', 'arcade_left', 'bath_left']),
            'storage': Room('Storage', 62, 225, 100, 80, ['party_left', 'storage_vert']),
            'basement': Room('Basement', 62, 475, 100, 80, ['arcade_left', 'storage_vert']),
            'kitchen': Room('Kitchen', 662, 225, 100, 80, ['stage_right', 'right_hall', 'kitchen_right']),
            'generator': Room('Generator', 662, 475, 100, 80, ['right_hall', 'gen_right', 'bath_right']),
            'backstage': Room('Backstage', 862, 225, 100, 80, ['kitchen_right', 'back_vert']),
            'supply': Room('Supply Room', 862, 475, 100, 80, ['gen_right', 'back_vert'])
        }

        self.hallways = {
            'left_hall': Hallway('Left Hall', 'office', 'arcade', ['office', 'arcade'], 3),
            'right_hall': Hallway('Right Hall', 'office', 'supply', ['office', 'supply'], 3),
            'stage_left': Hallway('Stage Left', 'stage', 'party', ['stage', 'party'], 1),
            'party_left': Hallway('Party Left', 'party', 'storage', ['party', 'storage'], 1),
            'arcade_left': Hallway('Arcade Left', 'arcade', 'basement', ['arcade', 'basement'], 1),
            'storage_vert': Hallway('Storage Vertical', 'storage', 'basement', ['storage', 'basement'], 2),
            'bath_left': Hallway('Bath Left', 'bathroom', 'arcade', ['bathroom', 'arcade'], 1),
            'stage_right': Hallway('Stage Right', 'stage', 'kitchen', ['stage', 'kitchen'], 1),
            'kitchen_right': Hallway('Kitchen Right', 'kitchen', 'backstage', ['kitchen', 'backstage'], 1),
            'gen_right': Hallway('Generator Right', 'generator', 'supply', ['generator', 'supply'], 1),
            'back_vert': Hallway('Back Vertical', 'backstage', 'supply', ['backstage', 'supply'], 2),
            'bath_right': Hallway('Bath Right', 'bathroom', 'generator', ['bathroom', 'generator'], 1)
        }

        for hallway in self.hallways.values():
            hallway.update_positions(self.rooms)

        # Initialize animatronics with images and jumpscare images
        self.animatronics = [
            Animatronic('Freddy', 'stage', os.path.join("images", "freddy.png"), os.path.join("images", "freddy_jumpscare.jpg"), move_probability=0.8),
            Animatronic('Bonnie', 'stage', os.path.join("images", "bonnie.png"), os.path.join("images", "bonnie_jumpscare.jpg"), move_probability=0.7),
            Animatronic('Chica', 'stage', os.path.join("images", "chica.png"), os.path.join("images", "chica_jumpscare.jpg"), move_probability=0.9),
            Animatronic('Foxy', 'storage', os.path.join("images", "foxy.png"), os.path.join("images", "foxy_jumpscare.jpg"), step_size=2),
            Animatronic('Golden Freddy', 'basement', os.path.join("images", "golden_freddy.png"), os.path.join("images", "Golden_freddy_jumpscare.webp"), teleport_probability=0.3)
        ]

        self.next_turn_button = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 50, 120, 40)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over and not self.won and not self.battery_drained:
                mouse_pos = pygame.mouse.get_pos()
                if self.next_turn_button.collidepoint(mouse_pos):
                    self.next_turn()
                else:
                    self.handle_click(mouse_pos)
        return True

    def handle_click(self, pos):
        for room in self.rooms.values():
            if room.rect.collidepoint(pos):
                self.toggle_light(room)
                return
        for hallway in self.hallways.values():
            if hallway.rect.collidepoint(pos):
                hallway.blocked = not hallway.blocked
                return

    def toggle_light(self, room):
        if self.battery >= 2:
            room.light_on = not room.light_on
            if room.light_on:
                self.battery -= 2

    def next_turn(self):
        if self.battery < 0:
            self.battery_drained_mode()
        else:
            battery_cost = sum(hallway.block_cost for hallway in self.hallways.values() if hallway.blocked)
            if self.battery > battery_cost:
                self.battery -= battery_cost
            else: 
                self.battery_drained = True
                self.battery_drained_mode()
                return
            self.move_animatronics()
            self.turns_remaining -= 1
            for room in self.rooms.values():
                room.light_on = False
            if self.turns_remaining <= 0:
                self.won = True

    def battery_drained_mode(self):
        self.battery_drained = True
        for room in self.rooms.values():
            room.light_on = True
        for hallway in self.hallways.values():
            hallway.blocked = False

        if time.time() - self.last_turn_time >= 3:
            self.turns_remaining -= 1
            self.move_animatronics()
            self.last_turn_time = time.time()

    def move_animatronics(self):
        for animatronic in self.animatronics:
            if random.random() > animatronic.move_probability:
                continue
            if random.random() < animatronic.teleport_probability:
                possible_rooms = [room for room in self.rooms.keys() if room != 'office']
                animatronic.current_room = random.choice(possible_rooms)
                continue
            current_room = animatronic.current_room
            for _ in range(animatronic.step_size):
                possible_moves = []
                for hallway in self.hallways.values():
                    if current_room in hallway.connected_rooms and not hallway.blocked:
                        other_rooms = [r for r in hallway.connected_rooms if r != current_room]
                        possible_moves.extend(other_rooms)
                if possible_moves:
                    new_room = random.choice(possible_moves)
                    animatronic.current_room = new_room
                    current_room = new_room
                if animatronic.current_room == 'office':
                    self.game_over = True
                    self.jumpscare_image = animatronic.jumpscare_image  # Set jumpscare image for the animatronic
                    self.jumpscare_opacity = 0
                    self.death_reason = f"You were caught by {animatronic.name}!"
                    return

    def draw(self):
        self.screen.fill(BLACK)
        
        for hallway in self.hallways.values():
            color = RED if hallway.blocked else DARK_GRAY
            pygame.draw.line(self.screen, color, hallway.start_pos, hallway.end_pos, 20)
            cost_text = self.font.render(f'{hallway.block_cost}', True, WHITE)
            mid_point = ((hallway.start_pos[0] + hallway.end_pos[0]) // 2, 
                         (hallway.start_pos[1] + hallway.end_pos[1]) // 2)
            self.screen.blit(cost_text, cost_text.get_rect(center=mid_point))

        for room_name, room in self.rooms.items():
            color = OFFICE_COLOR if room_name == 'office' else (WHITE if room.light_on else GRAY)
            pygame.draw.rect(self.screen, color, room.rect)
            text = self.font.render(room.name, True, BLACK)
            text_rect = text.get_rect(midtop=(room.rect.centerx, room.rect.top + 5))
            self.screen.blit(text, text_rect)
            
            if room.light_on:
                animatronics_here = [a for a in self.animatronics if a.current_room == room_name]
                if animatronics_here:
                    for i, animatronic in enumerate(animatronics_here):
                        y_offset = 25 + (i * 45)
                        image_rect = animatronic.image.get_rect(center=(room.rect.centerx, room.rect.centery + y_offset))
                        self.screen.blit(animatronic.image, image_rect)
            elif room_name != 'office':
                text = self.font.render('?', True, DARK_GRAY)
                text_rect = text.get_rect(center=room.rect.center)
                self.screen.blit(text, text_rect)
        
        pygame.draw.rect(self.screen, GREEN, self.next_turn_button)
        text = self.font.render('Next Turn', True, BLACK)
        text_rect = text.get_rect(center=self.next_turn_button.center)
        self.screen.blit(text, text_rect)
        
        battery_text = self.font.render(f'Battery: {self.battery}%', True, WHITE)
        turns_text = self.font.render(f'Turns: {self.turns_remaining}', True, WHITE)
        block_cost = sum(hallway.block_cost for hallway in self.hallways.values() if hallway.blocked)
        block_text = self.font.render(f'Block Cost: {block_cost}%', True, WHITE)
        self.screen.blit(battery_text, (10, 10))
        self.screen.blit(turns_text, (10, 50))
        self.screen.blit(block_text, (10, 90))
        
        if self.game_over:
            if self.jumpscare_image:
                # Fade-in jumpscare effect
                self.jumpscare_opacity = min(255, self.jumpscare_opacity + 5)
                jumpscare_surface = self.jumpscare_image.convert_alpha()
                jumpscare_surface.set_alpha(self.jumpscare_opacity)
                jumpscare_rect = jumpscare_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                self.screen.blit(jumpscare_surface, jumpscare_rect)

            death_reason_text = self.font.render(self.death_reason, True, WHITE)
            reason_rect = death_reason_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 200))
            self.screen.blit(death_reason_text, reason_rect)
        
        if self.won:
            win_text = self.font.render('You Survived!', True, WHITE)
            text_rect = win_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
            self.screen.blit(win_text, text_rect)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            if not self.battery_drained:
                self.draw()
            else:
                self.battery_drained_mode()
                self.draw()
            self.clock.tick(FPS)
            if self.game_over and self.jumpscare_opacity >= 255:
                pygame.time.wait(2000)
                running = False
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
