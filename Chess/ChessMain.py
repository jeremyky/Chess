"""
Main driver file. Responsible for handling user input and displaying current GameState Objects.
"""

import pygame as p
from Chess import ChessEngine

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = WIDTH//DIMENSION
MAX_FPS = 15 # for animations
IMAGES = {}

'''
Initialize a global disctonary of images, will be called exactly once in main
'''

def loadImages():
    pieces = ['wP','wR','wN','wB','wK','wQ','bP','bR','bN','bB','bK','bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"),(SQ_SIZE,SQ_SIZE))
    # access image by using IMAGES['wP']

'''
Main driver for the code. Will handle user input and updating the graphics
'''

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False # flag variable for when a move is made, so we don't constantly generate validMoves since it is an expensive operation
    animate = False # flag variable for when we should animate a move
    loadImages() # only do this once
    running = True
    sqSelected = () #no square selected initially
    playerClicks = []
    gameOver = False
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            #mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver:
                    location = p.mouse.get_pos() #(x,y) of mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row,col): #the user clicked on the same square twice
                        sqSelected = () #deselect
                        playerClicks = [] #clear
                    else:
                        sqSelected = (row,col)
                        playerClicks.append(sqSelected) #up to two clicks stored in playerClicks, append both 1st and 2nd
                    if len(playerClicks) == 2: #after 2nd click, make the engine make the move, keep track of the move
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                        print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = () #reset user clicks
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            #key handlers
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:#undo when 'z' is pressed
                    gs.undoMove()
                    moveMade = True
                    animate = False
                if e.key == p.K_r: # reset the board when 'r' is pressed
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False

        drawGameState(screen, gs, validMoves, sqSelected)

        if gs.checkMate:
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, "black wins by checkmate")
            else:
                drawText(screen, "white wins by checkmate")
        elif gs.staleMate:
            gameOver = True
            drawText(screen, "stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()

'''
Highlight square selected and moves for piece selected
'''
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        row, col = sqSelected
        if gs.board[row][col][0] == ("w" if gs.whiteToMove else "b"): # square selected is a piece that can be moved
            # highlight selected square
            surface = p.Surface((SQ_SIZE, SQ_SIZE))
            surface.set_alpha(100) # transparency value -> 0 = transparent, 255 = opaque
            surface.fill(p.Color("blue"))
            screen.blit(surface, (col * SQ_SIZE, row * SQ_SIZE))
            # highlight moves from that square
            surface.fill(p.Color("yellow"))
            for move in validMoves:
                if move.startRow == row and move.startCol == col:
                    screen.blit(surface, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))
'''
Responsible for all graphics within a current game state
'''
def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen) #draw squares on board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board) #draw pieces on top of squares

'''
Draw squares on the board
'''
def drawBoard(screen):
    global colors
    colors = [p.Color(240, 217, 181), p.Color(181, 136, 99)] #first is light, second is dark
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[(row + col) % 2]
            p.draw.rect(screen, color, p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
'''
Draw pieces on the board using the current GameState.board
'''
def drawPieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--": #not an empty square
                screen.blit(IMAGES[piece], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

'''
Animating a move
'''
def animateMove(move, screen, board, clock):
    global colors
    coords = [] # list of coordinates that the animation will move through
    dRow = move.endRow - move.startRow
    dCol = move.endCol - move.startCol
    framesPerSquare = 10 # frames to move one square of an animation
    frameCount = (abs(dRow) + abs(dCol)) * framesPerSquare
    for frame in range(frameCount + 1):
        row, col = (move.startRow + dRow*frame/frameCount, move.startCol + dCol*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from it's ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != "--":
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def drawText(screen, text):
    font = p.font.SysFont("Montserrat", 32, False, False)
    textObject = font.render(text, 0, p.Color("Black"))
    textLocation = p.Rect(0,0, WIDTH, HEIGHT).move(WIDTH / 2 - textObject.get_width() / 2,
                                                   HEIGHT / 2 - textObject.get_height() / 2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color("Gray"))
    screen.blit(textObject, textLocation.move(2, 2))

if __name__ == "__main__":
    main()