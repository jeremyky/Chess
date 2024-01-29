"""
Class responsible for storing all information about current state of Chess game.
Responsible for determining valid moves at the current state.
Keeps a move log.
"""

class GameState():
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
            ]
        self.moveFunctions = {'P': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'Q': self.getQueenMoves, 'K': self.getKingMoves}
        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkMate = False
        self.staleMate = False
        self.inCheck = False
        self.pins = []
        self.checks = []
        self.enPassantPossible = () # coordinates for square where en passant capture is possible
        self.enPassantPossibleLog = [self.enPassantPossible]
        # castling rights
        self.currentCastlingRights = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                             self.currentCastlingRights.wqs, self.currentCastlingRights.bqs)]


    '''
    Takes move as a parameter and executes it. doesn't work for pawn promotion, en passant, castling
    '''
    def makeMove(self, move):
        self.board[move.endRow][move.endCol] = move.pieceMoved # piece in new location
        self.board[move.startRow][move.startCol] = "--" # moving piece leave square behind it empty
        self.moveLog.append(move) # log move so we can undo it later or display history of game
        self.whiteToMove = not self.whiteToMove # switch turns

        # update kings location
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)

        # if pawn moves twice, next move can capture en passant
        if move.pieceMoved[1] == "P" and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.endRow + move.startRow) // 2, move.endCol)
        else:
            self.enPassantPossible = ()

        # if en passant move, must update board to capture the pawn
        if move.enPassant:
            self.board[move.startRow][move.endCol] = "--"

        # if pawn promotion change piece
        if move.pawnPromotion:
            promotedPiece = input("Promote to Q, R, B, or N:")
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + promotedPiece

        # castle move
        if move.castle:
            if move.endCol - move.startCol == 2:  # king side castle move
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][
                    move.endCol + 1]  # moves the rook to its new square
                self.board[move.endRow][move.endCol + 1] = '--'  # erase old rook
            else:  # queen side castle move
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][
                    move.endCol - 2]  # moves the rook to its new square
                self.board[move.endRow][move.endCol - 2] = '--'  # erase old rook

        self.enPassantPossibleLog.append(self.enPassantPossible)

        # update castling rights - whenever it is a rook or king move
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                                 self.currentCastlingRights.wqs, self.currentCastlingRights.bqs))

    '''
    Undo the last move made
    '''
    def undoMove(self):
        if len(self.moveLog) != 0: # make sure there is a move to undo
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove

            # update kings location
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)

            # undo en passant
            if move.enPassant:
                self.board[move.endRow][move.endCol] = "--" # removes the pawn that was added in wrong square
                self.board[move.startRow][move.endCol] = move.pieceCaptured # puts pawn back on correct square it was captured from
            self.enPassantPossibleLog.pop()
            self.enPassantPossible = self.enPassantPossibleLog[-1] # allow an en passant to happen on the next move

            # undo a 2 square pawn advance should make enPassantPossible = () again
            if move.pieceMoved[1] == "P" and abs(move.startRow - move.endRow) == 2:
                self.enPassantPossible = ()

            # undo castle rights
            self.castleRightsLog.pop()  # get rid of the new castle rights from the move we are undoing
            self.currentCastlingRights = self.castleRightsLog[-1]  # set the current castle rights to the last one in the list

            # undo the castle move
            if move.castle:
                if move.endCol - move.startCol == 2:  # king-side
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = '--'
                else:  # queen-side
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = '--'
            self.checkMate = False
            self.staleMate = False


    '''
    All moves considering checks
    '''
    def getValidMoves(self):
        tempCastleRights = CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                          self.currentCastlingRights.wqs, self.currentCastlingRights.bqs)
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
        if self.inCheck:
            if len(self.checks) == 1: # only 1 check, block check or move king
                moves = self.getAllPossibleMoves()
                # to block a check we must move a piece into one of the squares between the enemy piece and king
                check = self.checks[0] # check information
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol] # enemy piece causing check
                validSquares = [] # squares that pieces (ours) can move to
                if pieceChecking[1] == 'N': # if knight, we must capture knight or move king b/c it check cannot be blocked
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8): # generates a list of coordinates that a piece can move to to block a check
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i) # check[2] and check[3] are the check directions
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: # once we get to piece end checks
                            break
                for i in range(len(moves) - 1, -1, -1): # go through backwards to remove moves from list as iterating
                    if moves[i].pieceMoved[1] != "K": # move doesn't move king so it must block or capture
                        if not (moves[i].endRow, moves[i].endCol) in validSquares: # move doesn't block check or capture piece
                            moves.remove(moves[i])
            else: # double check, king has to move
                self.getKingMoves(kingRow, kingCol, moves)
        else: # not in check, so all moves are valid (minus ones that deal with pins)
            moves = self.getAllPossibleMoves()
            if self.whiteToMove:
                self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
            else:
                self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)

        if len(moves) == 0:
            if self.inCheck:
                self.checkMate = True
            else:
                self.staleMate = True
        else:
            self.checkMate = False
            self.staleMate = False

        self.currentCastlingRights = tempCastleRights
        return moves

    def checkForPinsAndChecks(self):
        pins = [] # squares where the allied pinned piece is and direction pinned from
        checks = [] # squares where enemy is applying a check
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]
        # check outward from king for pins and checks, keep track of pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1,-1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = () # reset possible pins. keep track of it when we run into it,
            # then look beyond it to make sure there is no piece attacking this pin and going through it
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: # on board
                    endPiece = self.board[endRow][endCol] # if there is a piece there
                    if endPiece[0] == allyColor and endPiece[1] != "K": # has potential to be a pin
                        # the King portion it allows us to move along the line that is being checked, even tho we are in check
                        # this is because in the generation of king moves, we change the kings location to the original square to look out in directions
                        # so this changed king would be protected by the real location of the king, assuming a pin/block
                        if possiblePin == (): # 1st allied piece could be pinned
                            possiblePin = (endRow, endCol, d[0], d[1])
                            # any piece can be a pin if it's the first piece between an enemy piece and the king
                        else: # 2nd allied piece, so no pin or check possible in this direction
                            break # change directions to check now
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        # 5 possibilities here in this complex conditional
                        # 1. orthogonally away from king and piece is a rook
                        # 2. diagonally away from king and piece is a bishop
                        # 3. 1 square diagonally away from king but the piece is a pawn
                        # 4. any direction away from the king is a queen
                        # 5. any direction one square away from the king is the other king
                        if (0 <= j <= 3 and type == "R") or \
                                (4 <= j <= 7 and type == "B") or \
                                (i == 1 and type == "P" and ((enemyColor == "w" and 6 <= j <= 7) or (enemyColor == "b" and 4 <= j <= 5))) or \
                                (type == "Q") or (i == 1 and type == "K"):
                            if possiblePin == (): # no piece blocking, so check
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else: # piece blocking so pin
                                pins.append(possiblePin)
                                break
                        else: #enemy piece not applying check
                            break
                else: # off board
                    break
        # check for knight checks
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == "N": # enemy knight attacking king
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks

    """
    Update the castle rights given the move
    """
    def updateCastleRights(self, move):
        if move.pieceCaptured == "wR":
            if move.endCol == 0:  # left rook
                self.currentCastlingRights.wqs = False
            elif move.endCol == 7:  # right rook
                self.currentCastlingRights.wks = False
        elif move.pieceCaptured == "bR":
            if move.endCol == 0:  # left rook
                self.currentCastlingRights.bqs = False
            elif move.endCol == 7:  # right rook
                self.currentCastlingRights.bks = False

        if move.pieceMoved == 'wK':
            self.currentCastlingRights.wqs = False
            self.currentCastlingRights.wks = False
        elif move.pieceMoved == 'bK':
            self.currentCastlingRights.bqs = False
            self.currentCastlingRights.bks = False
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0:  # left rook
                    self.currentCastlingRights.wqs = False
                elif move.startCol == 7:  # right rook
                    self.currentCastlingRights.wks = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0:  # left rook
                    self.currentCastlingRights.bqs = False
                elif move.startCol == 7:  # right rook
                    self.currentCastlingRights.bks = False

    '''
    Determine if the current player is in check
    '''
    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    '''
    Determine if the enemy can attack the square row, col
    '''
    def squareUnderAttack(self, row, col):
        self.whiteToMove = not self.whiteToMove # switch to opponents moves
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove # go back to original turn
        for move in oppMoves:
            if move.endRow == row and move.endCol == col: #square is under attack
                return True
        return False

    '''
    All moves without considering checks
    '''
    def getAllPossibleMoves(self):
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                color = self.board[row][col][0]
                if (color == 'w' and self.whiteToMove) or (color == 'b' and not self.whiteToMove):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves) #calls appropriate move function based on piece type
        return moves


    '''
    Get all the pawn moves for the pawn located at row, col and add these moves to the list
    '''
    def getPawnMoves(self, row, col, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            backRow = 0
            enemyColor = "b"
            kingRow, kingCol = self.whiteKingLocation
        else:
            moveAmount = 1
            startRow = 1
            backRow = 7
            enemyColor = "w"
            kingRow, kingCol = self.blackKingLocation
        pawnPromotion = False

        if self.board[row + moveAmount][col] == "--":  # 1 square pawn advance
            if not piecePinned or pinDirection == (moveAmount, 0):
                moves.append(Move((row, col), (row + moveAmount, col), self.board))
                if row == startRow and self.board[row + 2 * moveAmount][col] == "--":  # 2 square pawn advance
                    moves.append(Move((row, col), (row + 2 * moveAmount, col), self.board))
        #captures

        if col - 1 >= 0:  # capture to the left
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[row + moveAmount][col - 1][0] == enemyColor:
                    moves.append(Move((row, col), (row + moveAmount, col - 1), self.board))
                if (row + moveAmount, col - 1) == self.enPassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == row:
                        if kingCol < col:  # king is left of the pawn
                            # inside: between king and the pawn;
                            # outside: between pawn and border;
                            insideRange = range(kingCol + 1, col - 1)
                            outsideRange = range(col + 1, 8)
                        else:  # king right of the pawn
                            insideRange = range(kingCol - 1, col, -1)
                            outsideRange = range(col - 2, -1, -1)
                        for i in insideRange:
                            if self.board[row][i] != "--":  # some piece beside en-passant pawn blocks
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[row][i]
                            if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((row, col), (row + moveAmount, col - 1), self.board, enPassant=True))
        if col + 1 <= 7:  # capture to the right
            if not piecePinned or pinDirection == (moveAmount, +1):
                if self.board[row + moveAmount][col + 1][0] == enemyColor:
                    moves.append(Move((row, col), (row + moveAmount, col + 1), self.board))
                if (row + moveAmount, col + 1) == self.enPassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == row:
                        if kingCol < col:  # king is left of the pawn
                            # inside: between king and the pawn;
                            # outside: between pawn and border;
                            insideRange = range(kingCol + 1, col)
                            outsideRange = range(col + 2, 8)
                        else:  # king right of the pawn
                            insideRange = range(kingCol - 1, col + 1, -1)
                            outsideRange = range(col - 1, -1, -1)
                        for i in insideRange:
                            if self.board[row][i] != "--":  # some piece beside en-passant pawn blocks
                                blocking_piece = True
                        for i in outsideRange:
                            square = self.board[row][i]
                            if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((row, col), (row + moveAmount, col + 1), self.board, enPassant=True))
    '''
    Get all the rook moves for the rook located at row, col and add these moves to the list
    '''
    def getRookMoves(self, row, col, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][1] != "Q": # can't remove queen from pin on rook moves, only remove it on bishop moves
                    # this is because our queen moves generate rook moves, so we can't remove it from the pin list
                    self.pins.remove(self.pins[i])
                    break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1)) # up, left, down, right respectively
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1,8): # calculates distance traveled based on direction
                endRow = row + d[0] * i
                endCol = col + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: # on board
                        # in direction or opposite direction b/c it can still block the orthogonal between queen
                        if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                            endPiece = self.board[endRow][endCol]
                            if endPiece == "--":
                                moves.append(Move((row, col), (endRow, endCol), self.board))
                            elif endPiece[0] == enemyColor:
                                moves.append(Move((row, col), (endRow, endCol), self.board))
                                break # can take enemy piece but can't go past that in this direction
                            else:
                                break # friendly piece, cannot move here so stop moving in this direction
                else: # off board
                    break

    '''
    Get all the knight moves for the rook located at row, col and add these moves to the list
    '''

    def getKnightMoves(self, row, col, moves):
        piecePinned = False
        # we don't check for pin direction because regardless of pin, knight would not be able
        # to capture it due to it's movement restraints
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1,2), (2, -1), (2, 1)) # all possible knight moves
        allyColor = "w" if self.whiteToMove else "b"
        for m in knightMoves: # update position based on move
            endRow = row + m[0]
            endCol = col + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8: # on board
                if not piecePinned:
                    endPiece = self.board[endRow][endCol] # check landing position to see if can move there
                    if endPiece[0] != allyColor: # empty square or enemy square
                        moves.append(Move((row, col), (endRow, endCol), self.board))


    '''
    Get all the bishop moves for the rook located at row, col and add these moves to the list
    '''

    def getBishopMoves(self, row, col, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1)) # diagonals
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8): # maximum movement per direction
                endRow = row + d[0] * i
                endCol = col + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((row, col), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((row, col), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else: # off board
                    break

    '''
    Get all the queen moves for the rook located at row, col and add these moves to the list
    '''

    def getQueenMoves(self, row, col, moves):
        self.getRookMoves(row, col, moves)
        self.getBishopMoves(row, col, moves)

    '''
    Get all the king moves for the rook located at row, col and add these moves to the list
    '''

    def getKingMoves(self, row, col, moves):
        # possible landing locations
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8): # selects movement tuple and collects the specific direction moved
            endRow = row + rowMoves[i]
            endCol = col + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                # temporarily place king on end square and check for checks
                # go ahead and run the check for pins and checks
                    if allyColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck: # then the king move is fine
                        moves.append(Move((row, col), (endRow, endCol), self.board))
                    # place king back on original location
                    if allyColor == "w":
                        self.whiteKingLocation = (row, col)
                    else:
                        self.blackKingLocation = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        Generate all valid castle moves for the king at (row, col) and add them to the list of moves.
        """
        if self.squareUnderAttack(row, col):
            return  # can't castle while in check
        if (self.whiteToMove and self.currentCastlingRights.wks) or (
                not self.whiteToMove and self.currentCastlingRights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.whiteToMove and self.currentCastlingRights.wqs) or (
                not self.whiteToMove and self.currentCastlingRights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, castle=True))

    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, castle=True))

class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs

class Move():
    #maps keys to values
    #key:value
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, enPassant = False, castle = False):
        #decoupling tuples
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.pawnPromotion = (self.pieceMoved == "wP" and self.endRow == 0) or (
                self.pieceMoved == "bP" and self.endRow == 7)
        # en passant
        self.enPassant = enPassant
        if self.enPassant:
            self.pieceCaptured = "wP" if self.pieceMoved == "bP" else "bP"
        # castle move
        self.castle = castle
        self.isCapture = self.pieceCaptured != "--"
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    '''
    Overriding the equals method
    '''
    def __eq__(self,other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False
    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)
    def getRankFile(self, row, col):
        return self.colsToFiles[col] + self.rowsToRanks[row]