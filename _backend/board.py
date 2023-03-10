import pygame
import random

from config import *
from accessory import Button, Timer
from player import *
from piece import King, Queen, Rook, Bishop, Knight, Pawn


class Board:
    def __init__(self, manager):
        self.manager = manager
        self.board_turns = all(type(player) is Human for player in self.manager.players)
        self.blocks = [(x, y) for x in range(8) for y in range(8)]
        
        
        self.current_turn = 0
        self.turn_count = 0
        
        
        self.board_panel = None
        self.check_state = None
        self.made_a_turn = False
        
        
        # Game State
        self.pause = False
        
        
        
        self.board_turning = False
        self.delay = 1
        self._reset_selected()
        self._reset_pieces()

    def input(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.selected_block = self.select_block(mouse_pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # release left click to drop the piece
                self.drop(mouse_pos[0], mouse_pos[1])
        elif pygame.mouse.get_pressed()[0]:  # if dragging, move the piece
            self.drag(mouse_pos[0], mouse_pos[1])
        elif event.type == pygame.KEYDOWN:
            if self.needs_change:
                pos = self.needs_change.current_pos
                turn = self.needs_change.turn
                
                if event.key == pygame.K_1:
                    self.change_piece(Queen(pos, turn), True)
                elif event.key == pygame.K_2:
                    self.change_piece(Bishop(pos, turn), True)
                elif event.key == pygame.K_3:
                    self.change_piece(Knight(pos, turn), True)
                elif event.key == pygame.K_4:
                    self.change_piece(Rook(pos, turn), True)
                
        if self.board_turning and event.type == pygame.USEREVENT:
            if self.delay > 0:
                self.delay -= 1
            else:
                self.next_turn()
                self.board_turning = False
                self.delay = 1
                pygame.time.set_timer(pygame.USEREVENT, 1000)

    ##################
    # Draw the Board #
    ##################
    def draw(self, screen):
        screen_center = (screen.get_width()/2, screen.get_height()/2)
        board_width = (screen.get_height())
        board_height = board_width
        playing_field_width = board_width/1.2
        playing_field_height = board_height/1.2
        board = pygame.Rect(0, 0, board_width, board_height)
        playing_field = pygame.Rect(0, 0, playing_field_width, playing_field_height)
        playing_field.center = board.center = screen_center
        self.board_panel = playing_field

        pygame.draw.rect(screen, BROWN, board)
        pygame.draw.rect(screen, OAK, playing_field)

        self.draw_squares(screen, playing_field)
        self.draw_texture(screen, board)
        self.draw_border(screen, playing_field)
        self.draw_pieces(screen)
        
        # Transition Between Turns #TODO move to Scene somehow
        if self.board_turning and self.board_turns:
            r = pygame.Rect(0, 0, 400, 200)
            r.center = screen.get_rect().center
            pygame.draw.rect(screen, OAK, r, 0, 10)
            text = GET_FONT('elephant', 40).render("White's turn!" if self.current_turn == 1 else "Black's turn!", True, WHITE)
            screen.blit(text, text.get_rect(center=(screen.get_rect().centerx, screen.get_rect().centery)))
            
        
        
        if self.needs_change == None:
            self.pause = False
        else:
            self.pause = True
            
        if not self.board_turns and self.current_turn != 0 and self.game_state('1','2','3') != '3':
            pieces = [p for p in self.pieces if p.turn == self.current_turn and len(p.get_movement(self.pieces)) > 1 or len(p.get_capturables(self.pieces)) > 0]
            selected_piece = random.sample(pieces, 1)[0]
            drop_pos = random.sample(selected_piece.get_movement(self.pieces) + selected_piece.get_capturables(self.pieces), 1)[0]
            self.select_block((0, 0), (selected_piece.current_pos[0], selected_piece.current_pos[1]))
            self.drop(drop_pos[0], drop_pos[1], (drop_pos[0], drop_pos[1])) 

    def draw_squares(self,screen, playing_field):
        '''Draws individual squares of the board.'''
        sq_width, sq_height = playing_field.width/8, playing_field.height/8
        square = pygame.Rect(self.board_panel.left, self.board_panel.top, sq_width, sq_height)
        for x, y in self.blocks:
            sq_left = x * sq_width + playing_field.x
            sq_top = y * sq_height + playing_field.y
            sq = pygame.Rect(sq_left, sq_top, sq_width, sq_height)
            
            if (x + y) % 2 == 0:
                pygame.draw.rect(screen, OAK, sq)
            else:
                pygame.draw.rect(screen, BROWN, sq)
            if (x, y) in self.feedback_blocks:
                pygame.draw.rect(screen, self.feedback_blocks[(x, y)], sq)
            elif (x, y) == self.selected_block:
                self.draw_rect(screen, LIGHT_GREEN, sq, 300)
            if (x, y) in self.movable_blocks:
                self.draw_rect(screen, LIGHT_GREEN, sq, 300)
            if (x, y) in self.capturables:
                pygame.draw.rect(screen, RED, sq, 3)
        
        self.draw_labels(screen, square, playing_field)
    
    def draw_pieces(self, screen):
        '''Draws each piece on the board.'''
        img_width = self.board_panel.width / 8 - 10
        img_height = self.board_panel.height / 8 - 10
        for piece in self.pieces:
            piece.update(self.pieces, self.board_turns)
            
            if piece == self.selected_piece: #TODO why?
                continue
            
            #TODO Make knight face proper direction
            # if type(piece) == Knight:
            #     piece.draw(screen, (img_width, img_height), self.board_panel, 180 if piece.turn == 0 else 0)
            #     continue ##Draw knights fliped
            
            piece.draw(screen, (img_width, img_height), self.board_panel)
            
            
        if self.selected_piece != None:
            self.selected_piece.draw(screen, (img_width, img_height), self.board_panel)
    
    def draw_feedback(self, xy: (int, int), color, reset_feedbacks):
        if reset_feedbacks:
            self.feedback_blocks = {xy: color}
        else:
            self.feedback_blocks[xy] = color

    def draw_rect(self, screen, color, rect: pygame.Rect, opacity = 255):
        s = pygame.Surface(rect.size)
        s.set_alpha(opacity)        
        s.fill(color)
        screen.blit(s, (rect.x, rect.y))
    
    def draw_labels(self, screen, square, playing_field):
        letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
        if self.current_turn != 0 and self.board_turns:
            letters.reverse()
        label_font = pygame.font.SysFont('arial', 36, bold = True)
        number_font = pygame.font.SysFont('arial', 40, bold = True)

        for i in range (0, 8):
            label_text = label_font.render(letters[i], True, DARK_OAK)
            label_rect = label_text.get_rect()
            label_rect.centerx = square.centerx
            label_rect.centery = self.board_panel.top - square.height / 2
            screen.blit(label_text, label_rect)
            square.left += square.width
            
            number_text = number_font.render(str(8 - i) if self.current_turn == 0 and self.board_turns else str(i + 1), True, DARK_OAK)
            number_rect = number_text.get_rect()
            number_rect.centerx = playing_field.left - playing_field.width * 0.05
            number_rect.centery = square.centery
            screen.blit(number_text, number_rect)
            square.top += square.height
        
        square.topleft = playing_field.topleft

    def draw_texture(self, screen, board):
        texture = pygame.image.load(TEXTURE_PATH + "wood_grain.png")
        texture = pygame.transform.scale(texture, (board.width, board.height))
        texture_rect = texture.get_rect()
        texture.set_alpha(80)
        texture_rect.topleft = board.topleft
        screen.blit(texture, texture_rect)

    def draw_border(self, screen, playing_field):
        border = pygame.Rect(0, 0, playing_field.width, playing_field.height)
        border.top = playing_field.top-2
        border.left = playing_field.left - 2
        pygame.draw.rect(screen, GOLD, border, 4)
        shadow = pygame.Rect(0, 0, playing_field.width, playing_field.height)
        shadow.top = border.top + 2
        shadow.left = border.left + 2
        pygame.draw.rect(screen, GOLD_SHADOW, shadow, 2)
        highlight = pygame.Rect(0, 0, playing_field.width, playing_field.height)
        highlight.top = playing_field.top - 3
        highlight.left = playing_field.left - 3
        pygame.draw.rect(screen, WHITE, highlight, 1)
        
 
 
    #################
    # Drag and Drop #
    #################
    def drag(self, x, y): #TODO view
        """Since draw_pieces renders the piece by its position, drag_piece changes
        the position of the held piece to the mouse position until drop_piece runs."""
        if self.board_panel == None or self.pause:
            return
        
        block_size = self.board_panel.width / 8
        x = (x - self.board_panel.x) / block_size - 0.5
        y = (y - self.board_panel.y) / block_size - 0.5
        
        for i in self.pieces:
            if (self.selected_block == i.current_pos and not self.holding_piece and not i.captured):
                self.holding_piece = True
                self.selected_piece = i
                return
        
        if self.selected_piece is not None:
            self.selected_piece.pos = (x, y)
    
    def drop(self, x, y, grid_pos: tuple = None): #TODO view
        """Calculates the grid point of the mouse position, after this method called
        it will set the piece position to the grid point. which will give the snap effect."""
        if self.board_panel == None:
            return False
        # converts x, y to grid position
        if grid_pos == None:
            block_x, block_y = self._get_grid_position(x, y)
        else:
            block_x, block_y = grid_pos
        
        if self.selected_piece == None:
            return False
        if (block_x, block_y) in self.castling_blocks:
            self.selected_piece.do_castling((block_x, block_y))
            self.pawn_at_end(self.selected_piece)
            # self.next_turn()
            if self.board_turns: 
                self.board_turning = True
                pygame.time.set_timer(pygame.USEREVENT, 300)
            else: self.next_turn()
            self._reset_selected()
            return True
        
        piece_positions = [p.current_pos for p in self.pieces]
        prev_pos = self.selected_piece.current_pos
        
        self.selected_piece.move_piece(block_x, block_y, self.current_turn, self.pieces)
        
        if self.selected_piece.current_pos == prev_pos:
            return False

        if (block_x, block_y) in self.capturables:
            self.captured_pieces.append(self.pieces[piece_positions.index((block_x, block_y))])
            self.pieces[piece_positions.index((block_x, block_y))].destroy_piece()
            self.pawn_at_end(self.selected_piece)
            # self.next_turn()
            if self.board_turns: 
                self.board_turning = True
                pygame.time.set_timer(pygame.USEREVENT, 300)
            else: self.next_turn()
            self._reset_selected()
            return True
        
        if (block_x, block_y) != self.selected_block:
            self.pawn_at_end(self.selected_piece)
            # self.next_turn()
            if self.board_turns: 
                self.board_turning = True
                pygame.time.set_timer(pygame.USEREVENT, 300)
            else: self.next_turn()
            self._reset_selected()
            return True
        
        self._reset_selected()
        return False       

    def select_block(self, pos: tuple, grid_pos: tuple = None): #TODO view
        x, y = pos
        piece_positions = [i.current_pos for i in self.pieces]
        if self.pause:
            return
        if self.drop(x, y, grid_pos) or self.board_panel == None:
            return
        if grid_pos == None:
            x, y = self._get_grid_position(x, y)
        else:
            x, y = grid_pos
        if (x, y) not in self.movable_blocks or (x, y) not in self.capturables:
            self._reset_selected()
        if (x >= 0 and x <= 7) and (y >= 0) and (y <= 7):
            self.selected_block = (x, y)
            if self.selected_block in piece_positions:
                if (self.pieces[piece_positions.index(self.selected_block)].turn == self.current_turn):
                    self.selected_piece = self.pieces[piece_positions.index(self.selected_block)]
                    self.check()
                    if self.selected_piece.piece_name == 'king':
                        if self.selected_piece.check_castling(self.pieces):
                            for block in self.selected_piece.castling_blocks:
                                self.castling_blocks += [tuple(block)]
                                self.draw_feedback(block, PURPLE, False)

                    self.movable_blocks = self.selected_piece.get_movement(self.pieces)
                    self.capturables = self.selected_piece.get_capturables(self.pieces)
                else:
                    self.draw_feedback(self.selected_block, RED, True)
                    self._reset_selected(True)
        return (x, y)

    
    ###############
    # Game States #
    ###############
    def game_state(self): #TODO view
        '''Returns the status of the game.'''
        if self.check_state == None:
            return 'Playing'
        elif any([len(piece.get_movement(self.pieces)) > 1 or len(piece.get_capturables(self.pieces)) > 0 for piece in self.pieces if piece.turn == self.current_turn]):
            return 'Check'
        elif False: #TODO stalemate
            pass
        else:
            return 'Check-Mate'
    
    def check(self): #TODO view
        '''Executes when the king is in check.'''
        self.check_state = None
        for piece in self.pieces:
            if piece.piece_name == 'king':
                if piece.turn == self.current_turn:
                    piece.set_disabled_moves(self.pieces)
                if piece.is_check(self.pieces, piece.current_pos):
                    self.check_state = piece.turn
    
    
    
    ### Pawn Promotion ###
    def pawn_at_end(self, piece): #TODO move to Pawn class?
        target_pos_y = 0
        if not self.board_turns:
            target_pos_y = 0 if self.current_turn == 0 else 7
        if piece.piece_name == 'pawn' and piece.current_pos != None and piece.turn == self.current_turn and piece.current_pos[1] == target_pos_y:
            self.needs_change = piece
            return True
        return False
    
    
    def change_piece(self, piece, change_turn = False): #TODO view
        if self.needs_change == None or self.needs_change not in self.pieces:
            return
        piece.current_pos = self.needs_change.current_pos
        self.pieces.remove(self.needs_change)
        self.pieces.append(piece)
        self.needs_change = None
        self.pause = False
        if change_turn: self.next_turn()

    def next_turn(self): #TODO view
        if self.pause or self.needs_change != None:
            return
        if self.current_turn < max(self.turns):
            self.current_turn += 1
        else:
            self.current_turn = min(self.turns)
        if self.board_turns: self.flip_places()
        self.check()
        self.made_a_turn = True

    ### Flip Board ###
    def flip_places(self): #TODO view
        for piece in self.pieces:
            piece.reflect_place()

    def _get_grid_position(self, x: float, y: float): #TODO view
        block_size = self.board_panel.width / 8
        if x > self.board_panel.x and y > self.board_panel.y:
            x = int((x - self.board_panel.x) / block_size)
            y = int((y - self.board_panel.y) / block_size)
        return x, y
    
    def _grid_to_screen_pos(self, x: float, y: float): #TODO view
        block_size = self.board_panel.width / 8
        x = x + self.board_panel.x * block_size
        y = y + self.board_panel.y * block_size
        return x, y
    
    def _reset_selected(self, keep_feedback=False): #TODO view
        self.selected_piece = None
        self.holding_piece = False
        self.selected_block = None
        self.movable_blocks = []
        self.capturables = []
        self.castling_blocks = []
        if not keep_feedback:
            self.feedback_blocks = {}
    
    def _reset_pieces(self): #TODO view
        '''Set up board with bieces '''
        self.selected_block = None
        self.stuck_indicator = None
        self.holding_piece = False
        self.selected_piece = None
        self.needs_change = None
        self.captured_pieces = []
        
        # Create Pieces
        pawns = [[Pawn((i, 6), 0) for i in range(8)], [Pawn((i, 1), 1) for i in range(8)]]
        rooks = [ [Rook((0, 7), 0), Rook((7, 7), 0)], [Rook((0, 0), 1), Rook((7, 0), 1)] ]
        knights = [ [Knight((1, 7), 0), Knight((6, 7), 0)], [Knight((1, 0), 1), Knight((6, 0), 1)] ]
        bishops = [[Bishop((2, 7), 0), Bishop((5, 7), 0)], [Bishop((2, 0), 1), Bishop((5, 0), 1)]]
        queen = [Queen((3, 7), 0), Queen((3, 0), 1)]
        king = [King((4, 7), 0), King((4, 0), 1)]
        
        # Assign to Players
        self.manager.players[0].pieces = [ pawns[0], knights[0], bishops[0], rooks[0], queen[0], king[0] ]
        self.manager.players[1].pieces = [ pawns[1], knights[1], bishops[1], rooks[1], queen[1], king[1] ]
        
        
        self.pieces = self.manager.players[0].pieces + self.manager.players[1].pieces #TODO remove need for this
        
        self.turns = [p.turn for p in self.pieces] #TODO unsure?