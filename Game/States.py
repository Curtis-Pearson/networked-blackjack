from enum import Enum


# Handle CLIENT, placeholder for now
class ClientStates(Enum):
    WaitingForConnection = 1
    ConnectedToServer = 2
    WaitingForLogin = 3
    Account = 4
    LoggingIn = 5
    SigningUp = 6
    LoggedIn = 7
    WaitingInLobby = 8
    ConnectingToGame = 9
    ConnectedToGame = 10
    PlayingGame = 11
    DisconnectingFromGame = 12
    LoggedOut = 13
    DisconnectingFromServer = 14
    ConnectionClosed = 98
    Error = 99


# Handle Game OBJECT loop
class GameStates(Enum):
    Setup = 1
    Start = 2
    WaitingForPlayers = 3
    Shuffling = 4
    PlaceBets = 5
    DealingCards = 6
    PlayersTurn = 7
    DealerTurn = 8
    Payout = 9
    EndRound = 10
    NewRound = 11
    EndGame = 12
    Deleted = 98
    Error = 99


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
    async def from_string(action):
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
