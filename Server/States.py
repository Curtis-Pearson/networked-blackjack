from enum import Enum


# Handle Game OBJECT loop
class GameStates(Enum):
    SetUsername = 1
    Setup = 2
    Start = 3
    Shuffling = 10
    PlaceBets = 20
    DealingCards = 21
    PlayersTurn = 30
    DealerTurn = 40
    Payout = 50
    EndRound = 51
    NewRound = 52
    EndGame = 60
    Deleted = 90
    Error = 91


# Handle individual Player OBJECT Hand OBJECTS
class HandStates(Enum):
    Idle = 1
    Playing = 2
    Blackjack = 3
    Split = 4
    DoubleDown = 5
    Stand = 6
    Busted = 7
    Disconnected = 98
    Error = 99


# Handle each Player OBJECT
class PlayerStates(Enum):
    Spectating = 1
    Broke = 2
    WaitingForGame = 3
    Betting = 4
    WaitingForTurn = 5
    Playing = 6
    TurnEnd = 7
    Disconnected = 98
    Error = 99


# Handle available Player OBJECT actions during gameplay
class PlayerActions(Enum):
    Spectate = 1
    Bet = 2
    Hit = 3
    DoubleDown = 4
    Split = 5
    Stand = 6
    Error = 99

    @staticmethod
    def from_string(action):
        if action == "spectate":
            return PlayerActions.Spectate
        elif action == "bet":
            return PlayerActions.Bet
        elif action == "hit":
            return PlayerActions.Hit
        elif action == "doubledown":
            return PlayerActions.DoubleDown
        elif action == "split":
            return PlayerActions.Split
        elif action == "stand":
            return PlayerActions.Stand
        else:
            return PlayerActions.Error


# Handle Dealer OBJECT
class DealerStates(Enum):
    WaitingForGame = 1
    WaitingForTurn = 2
    Playing = 2
    Blackjack = 3
    Standing = 4
    Busted = 5
    Error = 99
