import random
from time import sleep
from Game import States
import gc

# Constants
MAX_WAGER_LOWER_BOUND = 2
MAX_WAGER_UPPER_BOUND = 99999
DEFAULT_BALANCE = 1000
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 15
MIN_PASSWORD_LENGTH = 4
MAX_PASSWORD_LENGTH = 20
SHIFTING_KEY = 17
CHARS = list("7AqOcLNMTeplv$45IVsmCQ#yUBrbnG9?_2PDFtigw&ZXH1KJYk3jxaSW6u£%Eod80z@h!fR")


class CardValues:
    # Prevent issue regarding lack of __init__ function
    def __init__(self):
        pass
    Ace = 1, 11
    Two = 2
    Three = 3
    Four = 4
    Five = 5
    Six = 6
    Seven = 7
    Eight = 8
    Nine = 9
    Ten = 10
    Jack = 10
    Queen = 10
    King = 10


class Card:
    # Creates a new Card OBJECT
    def __init__(self, suit, rank, value, face_up):
        self.Suit = suit
        self.Rank = rank
        self.Value = value
        self.FaceUp = face_up

    # Returns the formatted string of the Card OBJECT
    def display_card(self):
        return f"{self.Rank} of {self.Suit}"

    # Flip the Card OBJECT
    def flip_card(self):
        self.FaceUp = not self.FaceUp

    # TODO: CLEANUP CARD OBJECT
    # Delete the Card OBJECT
    def __del__(self):
        pass


class Shoe:
    # Creates a new Shoe OBJECT
    def __init__(self):
        self.UnplayedCards = []
        self.DiscardedCards = []

    # Generates a new LIST of Card OBJECTS and adds them to the UnplayedCards LIST
    def generate_deck(self):
        for suit in ["Hearts", "Diamonds", "Clubs", "Spades"]:
            for (rank, value) in CardValues.__dict__.items():
                # Exclude __dict__ default items
                if rank in ['__module__', '__dict__', '__weakref__', '__doc__']:
                    continue
                self.UnplayedCards.append(Card(suit, rank, value, True))

    # Generates a new Deck OBJECT and adds its Card OBJECTS to the UnplayedCards LIST
    def generate_shoe(self, no_decks):
        for deck in range(no_decks):
            self.generate_deck()

    # Moves all remaining Card OBJECTS from the UnplayedCards LISTS to the DiscardedCards LIST
    def discard_shoe(self):
        while len(self.UnplayedCards) > 0:
            self.DiscardedCards.append(self.UnplayedCards.pop())

    # Calls discard_shoe FUNCTION
    # Moves all Card OBJECTS from the DiscardedCards LIST to the UnplayedCards LIST
    # Shuffles the UnplayedCards LIST
    def shuffle_shoe(self):
        self.discard_shoe()
        while len(self.DiscardedCards) > 0:
            self.UnplayedCards.append(self.DiscardedCards.pop())
        random.shuffle(self.UnplayedCards)

    # Moves a Card OBJECT from the UnplayedCards LIST to a Hand OBJECT's Cards LIST
    def play_card(self, hand_cards):
        hand_cards.append(self.UnplayedCards.pop())

    # TODO: CLEANUP SHOE OBJECT
    # Delete the Shoe OBJECT
    def __del__(self):
        pass


class Hand:
    # Create a new Hand OBJECT
    def __init__(self, wager_amount=0):
        self.Cards = []
        self.Value = 0
        self.State = States.HandStates.Idle
        self.Wager = wager_amount

    # Returns the total VALUE of the Card OBJECTS in the Cards LIST
    def evaluate_value(self):
        aces = 0
        self.Value = 0
        for card in self.Cards:
            # Don't evaluate value of face-down Card OBJECTS
            if not card.FaceUp:
                continue
            if CardValues.__dict__[card.Rank] == (1, 11):
                aces += 1
                continue
            self.Value += card.Value
        # Process Ace Card OBJECTS LAST!
        for ace in range(aces):
            if (self.Value + 11) > 21:
                self.Value += 1
            else:
                self.Value += 11
        return self.Value

    # Returns the formatted string of all Card OBJECTS where Card.FaceUp is TRUE
    def display_hand(self):
        face_up_cards = []
        for card in self.Cards:
            if card.FaceUp:
                face_up_cards.append(card)
        hand_message = ""
        for i, card in enumerate(face_up_cards):
            if not card.FaceUp:
                continue
            hand_message += face_up_cards[i].display_card()
            if i != len(face_up_cards) - 1:
                hand_message += ", "
        return hand_message

    # Delete the Hand OBJECT
    def __del__(self):
        pass


class Player:
    # Create a new Player OBJECT
    def __init__(self, username, money, state=States.PlayerStates.WaitingForGame):
        self.State = state
        self.Username = username
        self.Money = money
        self.Wager = 0
        self.TotalWager = 0
        self.Hands = [Hand()]

    # Self-explanatory
    def output_bet_info(self):
        print(f"\n{self.Username}: Betting ({self.Wager})"
              f"\nCurrent Balance ({self.Money})"
              f"\nTotal Wager ({self.TotalWager}).")

    # Create Wager VALUE for the Player OBJECT and their Hand OBJECT
    def wager_bet(self, amount):
        self.Money -= amount
        self.Wager = amount
        self.TotalWager += self.Wager
        self.Hands[0].Wager = amount
        self.output_bet_info()

    # Increase TotalWager VALUE of the Player OBJECT and their current Hand OBJECT's Wager VALUE
    def increase_bet(self, hand_obj):
        self.Money -= self.Wager
        self.TotalWager += self.Wager
        hand_obj.Wager += self.Wager
        self.output_bet_info()

    # Payout Hand OBJECT's Wager VALUE * multiplier VALUE
    def win_bet(self, hand_obj, mult):
        self.Money += hand_obj.Wager * mult
        hand_obj.Wager = 0

    # Payout Hand OBJECT's Wager Value
    def push_bet(self, hand_obj):
        self.Money += hand_obj.Wager
        hand_obj.Wager = 0

    # TODO: REPLACE WITH REMOVAL OF PLAYER
    # Delete the Player OBJECT
    def __del__(self):
        pass


class Dealer:
    # Create a new Dealer OBJECT
    def __init__(self):
        self.State = States.DealerStates.WaitingForGame
        self.Hand = Hand()

    # TODO: CLEANUP DEALER OBJECT
    # Delete the Dealer OBJECT
    def __del__(self):
        pass


class Game:
    # Create a new Game OBJECT
    def __init__(self):
        self.State = States.GameStates.Setup
        self.NoDecks = None
        self.ShuffleAfter = None
        self.Shoe = Shoe()
        self.MinWager = None
        self.MaxWager = None
        self.Dealer = Dealer()
        self.Players = []
        self.PlayingPlayers = []
        self.BrokePlayers = []

    # Setup Game OBJECT specific variables rather than initialising the Game OBJECT with static variables
    def setup(self, no_decks, shuffle_after, max_wager, min_wager):
        # Ensure the setup is only run once upon creation of the Game OBJECT
        if self.State != States.GameStates.Setup:
            self.State = States.GameStates.Error
            return

        # self.Players = players_list

        # Register number of Deck OBJECTS to include in the Shoe OBJECT's Cards LIST
        if no_decks is None:
            while True:
                self.NoDecks = input("GAME: Input number of decks to include in the shoe\n(2 - 8)\n->")
                try:
                    self.NoDecks = int(self.NoDecks)
                    if self.NoDecks <= 1:
                        print("GAME: Number of decks cannot be less than 2.\n")
                    elif self.NoDecks > 8:
                        print("GAME: Number of decks cannot be more than 8.\n")
                    else:
                        break
                except (TypeError, ValueError):
                    print("GAME: Please enter a valid number.\n")
        else:
            self.NoDecks = no_decks

        self.Shoe.generate_shoe(self.NoDecks)
        # Register number of Deck OBJECTS played before shuffling
        if shuffle_after is None:
            while True:
                self.ShuffleAfter = input(f"GAME: Input how many decks in should the shoe be shuffled\n"
                                          f"(1 - {self.NoDecks - 1})\n->")
                try:
                    self.ShuffleAfter = int(self.ShuffleAfter)
                    if self.ShuffleAfter <= 0:
                        print("GAME: Number of decks in cannot be less than 1.\n")
                    elif self.ShuffleAfter >= self.NoDecks:
                        print(f"GAME: Number of decks in cannot be more than the total number of decks - 1 "
                              f"({self.NoDecks - 1}).\n")
                    else:
                        break
                except (TypeError, ValueError):
                    print("GAME: Please enter a valid number.\n")
        else:
            self.ShuffleAfter = shuffle_after

        # Register the maximum wager VALUE
        if max_wager is None:
            while True:
                self.MaxWager = input("GAME: Input the maximum wager\n->")
                try:
                    self.MaxWager = int(self.MaxWager)
                    if self.MaxWager <= MAX_WAGER_LOWER_BOUND:  # NEED TO SET APPROPRIATE VALUE FOR LOWER/UPPER BOUNDS
                        print(f"GAME: Maximum wager cannot be less than or equal to {MAX_WAGER_LOWER_BOUND}.\n")
                    elif self.MaxWager > MAX_WAGER_UPPER_BOUND:
                        print(f"GAME: Maximum wager cannot be more than {MAX_WAGER_UPPER_BOUND}.\n")
                    else:
                        break
                except (TypeError, ValueError):
                    print("GAME: Please enter a valid number.\n")
        else:
            self.MaxWager = max_wager

        # Register the minimum wager VALUE
        if min_wager is None:
            while True:
                self.MinWager = input("GAME: Input the minimum wager\n->")
                try:
                    self.MinWager = int(self.MinWager)
                    if self.MinWager <= 0:
                        print("GAME: Minimum wager cannot be less than or equal to 0.\n")
                    elif self.MinWager > self.MaxWager:
                        print(f"GAME: Minimum wager cannot be more than the maximum wager ({self.MaxWager}).\n")
                    else:
                        break
                except (TypeError, ValueError):
                    print("GAME: Please enter a valid number.\n")
        else:
            self.MinWager = min_wager

        self.State = States.GameStates.Start
        self.start()

    # Player OBJECT joins the Game OBJECT
    def player_join(self, player_object):
        self.Players.append(player_object)

    # Player OBJECT leaves the Game OBJECT
    def player_leave(self, player_object):
        if player_object in self.Players:
            self.Players.remove(player_object)
        if player_object in self.PlayingPlayers:
            self.PlayingPlayers.remove(player_object)
        if player_object in self.BrokePlayers:
            self.BrokePlayers.remove(player_object)

    # Start the Game OBJECT
    def start(self):
        # Check Game OBJECT's STATE repeatedly to handle main Game OBJECT loop
        while True:
            sleep(1)
            # Game OBJECT's STATE handler, allows for future asynchronous loop implementation
            # Main Game OBJECT loop:
            # Shuffle if necessary > Place bets > Deal cards > Player turns (1 > 2 > ...)
            # > Dealer turn > Payout winnings > End round cleanup > REPEAT
            if self.State == States.GameStates.Start:
                print("\nGAME: Starting Game!")
                if len(self.Players) > 0:
                    self.State = States.GameStates.Shuffling
                else:
                    self.State = States.GameStates.WaitingForPlayers
            if self.State == States.GameStates.WaitingForPlayers:
                sleep(1)
                if len(self.Players) > 0:
                    self.State = States.GameStates.Shuffling
            elif self.State == States.GameStates.Shuffling:
                print("\nGAME: Shuffling Cards!")
                self.shuffle_cards()
            elif self.State == States.GameStates.PlaceBets:
                print("\nGAME: Place Bets!")
                self.place_bets()
            elif self.State == States.GameStates.DealingCards:
                print("\nGAME: Dealing Cards!")
                self.deal_cards()
            elif self.State == States.GameStates.PlayersTurn:
                print("\nGAME: Players' Turn!")
                self.players_turn()
            elif self.State == States.GameStates.DealerTurn:
                print("\nGAME: Dealer's Turn!")
                self.dealer_turn()
            elif self.State == States.GameStates.Payout:
                print("\nGAME: Paying Out Winnings!")
                self.payout()
            elif self.State == States.GameStates.EndRound:
                print("\nGAME: Ending Round!")
                self.end_round()
            elif self.State == States.GameStates.NewRound:
                print("\nGAME: Starting New Round!")
                # Shuffle the Shoe OBJECT's Card OBJECTS after the given number of
                # Deck OBJECTS' Card OBJECTS has been moved to the DiscardedCards LIST
                if len(self.Shoe.DiscardedCards) > (self.ShuffleAfter * 52):
                    self.State = States.GameStates.Shuffling
                # Skip Shuffling STATE of loop if conditions are not met
                else:
                    self.State = States.GameStates.PlaceBets
            elif self.State == States.GameStates.EndGame:
                print("\nGAME: Ending Game!")
                self.end_game()
            elif self.State == States.GameStates.Deleted:
                print("\nGAME: Deleted Game!")
                del self
                return
            elif self.State == States.GameStates.Error:
                print("OH GOD HOW DID YOU GET HERE")
                break

    # Shuffle the Shoe LIST a random number of times between X and Y
    def shuffle_cards(self):
        for i in range(random.randint(3, 5)):
            self.Shoe.shuffle_shoe()
        self.State = States.GameStates.PlaceBets

    # Place a bet for each Player OBJECT
    def place_bets(self):
        for player in self.Players:
            sleep(0.5)
            player.State = States.PlayerStates.Betting
            # If Player OBJECT's Money VALUE is lower than the MinWager VALUE, they cannot bet and must spectate
            if player.Money < self.MinWager:
                print(f"\n{player.Username}: Cannot bet at this game as balance is too low!"
                      f"\nCurrent Balance ({player.Money})\nGame Minimum Bet ({self.MinWager})\n")
                print(f"{player.Username}: No longer playing.")
                player.State = States.PlayerStates.Broke  # FIND A WAY TO REMOVE THEM FROM GAME WITHOUT DELETION
                self.BrokePlayers.append(player)
                continue
            # User input for Player OBJECT's bet
            while True:
                wager = input(f"\n{player.Username}: Current Balance ({player.Money})"
                              f"\nEnter bet amount ({self.MinWager} - {self.MaxWager})\n->")
                try:
                    wager = int(wager)
                    if wager < self.MinWager:
                        print(f"{player.Username}: Cannot bet less than the minimum bet ({self.MinWager}).")
                    elif wager > player.Money:
                        print(f"{player.Username}: Cannot bet more than your current balance ({player.Money}).")
                    elif wager > self.MaxWager:
                        print(f"{player.Username}: Cannot bet more than the maximum bet ({self.MaxWager}).")
                    else:
                        player.wager_bet(wager)
                        player.State = States.PlayerStates.WaitingForTurn
                        self.PlayingPlayers.append(player)
                        break
                except (ValueError, TypeError):
                    if wager.lower() == "spectate":
                        player.State = States.PlayerStates.Spectating
                        print(f"{player.Username}: Spectating this round.\n")
                        break
                    else:
                        print(f"{player.Username}: Please enter a valid amount.")
        # Remove Player OBJECTS with Broke STATE from the Players LIST
        for player in self.BrokePlayers:
            if self.Players.__contains__(player):
                self.Players.remove(player)
        # If there are no Player OBJECTS left in the game, end the game
        if len(self.Players) == 0:
            self.State = States.GameStates.EndGame
            return
        # If there are no Player OBJECTS in the PlayingPlayers LIST, go straight to end_round() for cleanup
        if len(self.PlayingPlayers) == 0:
            self.State = States.GameStates.EndRound
        else:
            self.State = States.GameStates.DealingCards

    # Hand out a Card OBJECT in order (Players (1 > 2 > ...) > Dealer) twice
    def deal_cards(self):
        while len(self.Dealer.Hand.Cards) != 2:
            for player in self.PlayingPlayers:
                self.Shoe.play_card(player.Hands[0].Cards)

            self.Shoe.play_card(self.Dealer.Hand.Cards)
            self.Dealer.State = States.DealerStates.WaitingForTurn

            if len(self.Dealer.Hand.Cards) == 2:
                self.Dealer.Hand.Cards[-1].flip_card()
        self.State = States.GameStates.PlayersTurn

    # Display Hand LIST of each Player OBJECT and the first Card OBJECT of the Dealer OBJECT
    def players_turn(self):
        # Returns TRUE if the VALUE of Card OBJECTS in a Player OBJECT's Hand LIST is over 21
        def check_if_bust(player_obj, hand_obj):
            if hand_obj.evaluate_value() > 21:
                sleep(0.5)
                hand_obj.State = States.HandStates.Busted
                print(f"\n{player_obj.Username}: ({hand_obj.evaluate_value()}) {hand_obj.display_hand()}.")
                print(f"{player_obj.Username}: BUST!")
                return True
            return False

        # Returns a STRING of available actions
        def update_player_action_list(available_actions_list):
            player_action_list = ""
            for i, action in enumerate(available_actions_list):
                player_action_list += str(available_actions_list.__getitem__(i).name)
                if i != len(available_actions_list) - 1:
                    player_action_list += " | "
            return player_action_list

        # Play through a Player OBJECT's Hand OBJECT
        def player_turn_hand(hand_obj):
            hand_obj.State = States.HandStates.Playing
            # Allow multiple actions for a single Hand OBJECT
            while True:
                sleep(0.5)
                print(f"\n{player.Username}: ({hand_obj.evaluate_value()}) {hand_obj.display_hand()}.")
                if hand_obj.evaluate_value() == 21:
                    print(f"{player.Username}: BLACKJACK!")
                    hand_obj.State = States.HandStates.Blackjack
                    if player.Hands.index(hand_obj) == 0:
                        player.State = States.PlayerStates.TurnEnd
                    break

                # Reset Hand OBJECT's STATE when returning after playing a Split hand
                if hand_obj.State == States.HandStates.Split:
                    hand_obj.State = States.HandStates.Playing
                # Set default actions
                available_actions = [States.PlayerActions.Hit, States.PlayerActions.Stand]

                # Provide additional actions if the Hand OBJECT has 2 Card OBJECTS
                if len(hand_obj.Cards) == 2:
                    # Allow DoubleDown if Player OBJECT has enough Money VALUE to bet their Wager VALUE
                    if (player.TotalWager + player.Wager) <= (player.Money + player.Wager):
                        available_actions.append(States.PlayerActions.DoubleDown)
                        # Allow Split if both Card OBJECTS in the Hand OBJECT have the same VALUE
                        if hand_obj.Cards[0].Value == hand_obj.Cards[1].Value:
                            available_actions.append(States.PlayerActions.Split)

                # Prevent Player OBJECT from performing a Split or DoubleDown
                # If the Hand OBJECT has more than 2 Card OBJECTS
                elif len(hand_obj.Cards) > 2:
                    if available_actions.__contains__(States.PlayerActions.Split):
                        available_actions.remove(States.PlayerActions.Split)
                    if available_actions.__contains__(States.PlayerActions.DoubleDown):
                        available_actions.remove(States.PlayerActions.DoubleDown)

                # Get user input for Player OBJECT's action
                player_action_string = update_player_action_list(available_actions)
                player_action_request = input(f"{player.Username}: Available Actions ({player_action_string}).\n->")
                player_action = States.PlayerActions.from_string(player_action_request.lower())

                if player_action not in available_actions:
                    print(f"{player.Username}: Enter a valid action ({player_action_string}).")
                    continue

                if player_action == States.PlayerActions.Hit:
                    self.Shoe.play_card(hand_obj.Cards)
                    if check_if_bust(player, hand_obj):
                        if player.Hands.index(hand_obj) == 0:
                            player.State = States.PlayerStates.TurnEnd
                        break

                elif player_action == States.PlayerActions.DoubleDown:
                    player.increase_bet(hand_obj)
                    self.Shoe.play_card(hand_obj.Cards)
                    print(f"\n{player.Username}: {hand_obj.display_hand()} ({hand_obj.evaluate_value()}).")
                    if not check_if_bust(player, hand_obj):
                        hand_obj.State = States.HandStates.DoubleDown
                    if player.Hands.index(hand_obj) == 0:
                        player.State = States.PlayerStates.TurnEnd
                    break

                elif player_action == States.PlayerActions.Split:
                    player.Hands.append(Hand())
                    player.Hands[-1].Cards.append(hand_obj.Cards.pop())
                    player.increase_bet(player.Hands[-1])
                    hand_obj.State = States.HandStates.Split
                    self.Shoe.play_card(player.Hands[-1].Cards)
                    self.Shoe.play_card(hand_obj.Cards)
                    player_turn_hand(player.Hands[-1])

                elif player_action == States.PlayerActions.Stand:
                    hand_obj.State = States.HandStates.Stand
                    if player.Hands.index(hand_obj) == 0:
                        player.State = States.PlayerStates.TurnEnd
                    break

        # Iterate through each Player OBJECT and play their turn
        for player in self.PlayingPlayers:
            sleep(0.5)
            player.State = States.PlayerStates.Playing
            print(f"\nDealer: ({self.Dealer.Hand.evaluate_value()}) {self.Dealer.Hand.display_hand()}.")
            player_turn_hand(player.Hands[0])
        self.State = States.GameStates.DealerTurn

    # Display Hand LIST of the Dealer OBJECT and play based on regular Dealer Blackjack rules
    # (Stand if Hand OBJECT's VALUE is 17 or higher, else Hit)
    def dealer_turn(self):
        self.Dealer.State = States.DealerStates.Playing
        self.Dealer.Hand.Cards[-1].flip_card()
        while True:
            sleep(1)
            print(f"\nDealer: ({self.Dealer.Hand.evaluate_value()}) {self.Dealer.Hand.display_hand()}.")
            sleep(0.5)
            if self.Dealer.State != States.DealerStates.Playing:
                break
            if self.Dealer.Hand.evaluate_value() == 21:
                print(f"Dealer: BLACKJACK!")
                self.Dealer.State = States.DealerStates.Blackjack
            elif self.Dealer.Hand.evaluate_value() > 21:
                print(f"Dealer: BUST!")
                self.Dealer.State = States.DealerStates.Busted
            elif self.Dealer.Hand.evaluate_value() < 17:
                print(f"Dealer: HIT!")
                self.Shoe.play_card(self.Dealer.Hand.Cards)
            elif self.Dealer.Hand.evaluate_value() >= 17:
                print(f"Dealer: STAND!")
                self.Dealer.State = States.DealerStates.Standing
        self.State = States.GameStates.Payout

    # Process each Player OBJECT's Hand OBJECT for win/lose conditions
    def payout(self):
        for player in self.PlayingPlayers:
            sleep(1)
            print(f"\n{player.Username} Payouts:")
            for hand in player.Hands:
                sleep(0.5)
                # Hand Busted = no payout
                if hand.State == States.HandStates.Busted:
                    print(f"{player.Username}: Hand Number {player.Hands.index(hand) + 1} BUSTED! No Payout.")
                    continue
                # Player Hand more than Dealer Hand OR Dealer Hand Busted = payout depending on Hand State
                if hand.evaluate_value() > self.Dealer.Hand.evaluate_value() \
                        or self.Dealer.State == States.DealerStates.Busted:
                    # Hand Blackjack = payout * 3
                    if hand.State == States.HandStates.Blackjack:
                        print(f"{player.Username}: Hand Number {player.Hands.index(hand) + 1} BLACKJACK! "
                              f"Payout {hand.Wager * 3}")
                        player.win_bet(hand, 3)
                    # Hand NOT Blackjack
                    else:
                        print(f"{player.Username}: Hand Number {player.Hands.index(hand) + 1} Won! "
                              f"Payout {hand.Wager * 2}")
                        player.win_bet(hand, 2)
                # Player Hand same as Dealer Hand = payout * 1 (Pushback)
                elif hand.evaluate_value() == self.Dealer.Hand.evaluate_value():
                    print(f"{player.Username}: Hand Number {player.Hands.index(hand) + 1} Tied! "
                          f"Payout {hand.Wager}")
                    player.win_bet(hand, 1)
                # Player Hand less than Dealer Hand = no payout
                else:
                    print(f"{player.Username}: Hand Number {player.Hands.index(hand) + 1} Lost! No Payout.")
            sleep(0.5)
            print(f"{player.Username}: Money ({player.Money})")
        self.State = States.GameStates.EndRound

    # Cleanup Player OBJECTS in PlayingPlayers LIST then cleanup Dealer OBJECT
    def end_round(self):
        for player in self.PlayingPlayers:
            for hand in player.Hands:
                # Move all Card OBJECTS from each Hand OBJECT to the Shoe OBJECT's DiscardedCards LIST
                while len(hand.Cards) > 0:
                    self.Shoe.DiscardedCards.append(hand.Cards.pop())
                # Delete the Hand OBJECT to prevent memory leak
                del hand
            # Reset the Player OBJECT's temporary data for the next round
            player.Wager = 0
            player.TotalWager = 0
            player.Hands = [Hand()]

        # Reset PlayingPlayers LIST
        self.PlayingPlayers = []
        # Set all Player OBJECTS' STATE to wait for a new game
        for player in self.Players:
            player.State = States.PlayerStates.WaitingForGame

        # Reset Dealer OBJECT's temporary data for the next round
        while len(self.Dealer.Hand.Cards) > 0:
            self.Shoe.DiscardedCards.append((self.Dealer.Hand.Cards.pop()))
        del self.Dealer.Hand
        self.Dealer.Hand = Hand()
        self.Dealer.State = States.DealerStates.WaitingForGame
        self.State = States.GameStates.NewRound

    # TODO: PROCESS REMOVAL OF PLAYER FROM GAME
    # End Game OBJECT
    def end_game(self):
        self.State = States.GameStates.Deleted

    # TODO: PROCESS GAME ENDING PROPERLY WHEN NETWORK IMPLEMENTED
    # Delete the Game OBJECT
    def __del__(self):
        pass


# Encrypt/Decrypt password
def cypher(password, encrypt):
    new_password = ""
    # Iterate over each character in the password
    for char in password:
        index = CHARS.index(char)
        # If it contains a character not found in CHARS, add it to new_password
        if not CHARS[index]:
            new_password += char
            continue
        if encrypt:
            # Increase the index by SHIFTING_KEY constant
            index += SHIFTING_KEY
            # If it goes out of range, loop it back to the start
            if index >= len(CHARS):
                index -= len(CHARS)
        else:
            # Decrease the index by SHIFTING_KEY constant
            index -= SHIFTING_KEY
            # If it goes out of range, loop it back to the end
            if index < 0:
                index += len(CHARS)
        new_password += CHARS[index]
    return new_password


# TODO: CREATE CLIENT HANDLER
class Client:
    # Create a Client OBJECT
    # ASSUME CLIENT HAS ALREADY CONNECTED TO SERVER, PROCEED WITH LOGIN STATE
    def __init__(self):  # TODO: INCLUDE HOST, PORT WHEN WORKING WITH NETWORK
        self.State = States.ClientStates.Account
        self.Username = None
        self.Player = self.init_player()

    # Decide whether to login or signup
    def init_player(self):
        while True:
            action = input("\nLogin or Signup?\n->")
            if action.strip().lower() == "login":
                self.State = States.ClientStates.LoggingIn
                return self.login()
            elif action.strip().lower() == "signup":
                self.State = States.ClientStates.SigningUp
                return self.signup()
            else:
                print("Please enter 'Login' or 'Signup'.\n")

    # Create a login (Username and Password) with a default balance
    def signup(self):
        # Username
        while True:
            username = input("\nPlease enter a Username (Case Sensitive).\n->").strip()
            # Validate and sanitise
            if len(username) <= MIN_USERNAME_LENGTH:
                print(f"Username cannot be smaller than {MIN_USERNAME_LENGTH} characters.\n")
            elif len(username) > MAX_USERNAME_LENGTH:
                print(f"Username cannot be longer than {MAX_USERNAME_LENGTH} characters.\n")
            elif '|' in username or ' ' in username:
                print(f"Invalid character(s) in '{username}'.\n")
            else:
                # Remove possible duplication
                exists = False
                with open("accounts.txt", "r") as accounts:
                    for account in accounts:
                        info = account.split('|')
                        if info[0] == username:
                            exists = True
                            break
                if exists:
                    print(f"Username '{username}' already exists!\n")
                    continue
                break

        # Password
        while True:
            password = input("\nPlease enter a Password (Case Sensitive).\n->").strip()
            # Validate and sanitise
            if len(password) <= MIN_PASSWORD_LENGTH:
                print(f"Password cannot be smaller than {MIN_PASSWORD_LENGTH} characters.\n")
            elif len(password) > MAX_PASSWORD_LENGTH:
                print(f"Password cannot be longer than {MAX_PASSWORD_LENGTH} characters.\n")
            elif '|' in password or ' ' in password:
                print("Invalid character(s) in Password.\n")
            # Password policy: Must contain at least 1 capital letter and 1 number
            elif not any(char.isupper() for char in password):
                print("Password must contain at least 1 capital letter.\n")
            elif not any(char.isdigit() for char in password):
                print("Password must contain at least 1 number.\n")
            else:
                # Ensure password is typed correctly
                password_repeat = input("\nPlease enter the Password again.\n->").strip()
                if password_repeat != password:
                    print("Passwords do not match, try again.\n")
                    continue
                break

        # Encrypt password for safe storage
        new_password = cypher(password, True)
        with open("accounts.txt", "a") as accounts:
            accounts.write(username + "|" + new_password + "|" + str(DEFAULT_BALANCE) + "|\n")
        self.Username = username
        self.State = States.ClientStates.LoggedIn
        return Player(username, DEFAULT_BALANCE)

    # Login using Username and Password, then create a Player OBJECT from account
    def login(self):
        while True:
            # Username
            while True:
                username = input("\nPlease enter the Username (Case Sensitive).\n->").strip()
                if len(username) <= 0:
                    print("Username cannot be empty.\n")
                    continue
                break

            # Password
            while True:
                password = input("Please enter the Password (Case Sensitive).\n->").strip()
                if len(username) <= 0:
                    print(f"Password cannot be empty.\n")
                    continue
                break

            # Check login credentials
            with open("accounts.txt", "r") as accounts:
                for account in accounts:
                    info = account.split('|')
                    # Username not correct for account, goto next account
                    if info[0] != username:
                        continue
                    new_password = cypher(info[1], False)
                    # Password not associated with Username, prevent unnecessary continue, break with unsuccessful login
                    if new_password != password:
                        break
                    print(new_password)
                    # Username and Password match, logged in successfully
                    print(f"Logged in successfully! Hello {username}.\n")
                    self.Username = username
                    self.State = States.ClientStates.LoggedIn
                    return Player(info[0], int(info[2]))
                # Username not in list or Password incorrect, unsuccessful login
                print("Incorrect Username or Password, please try again.\n")

    # Log out the Client OBJECT, sending them back to 'Login' STATE
    def logout(self):
        pass

    # Disconnect Client OBJECT from SERVER
    def disconnect(self):
        pass

    # Delete the Client OBJECT
    def __del__(self):
        pass


# Main start function
def main():
    # Login
    # clients = [Client() for i in range(3)]
    # players = [clients[i].Player for i in range(len(clients))]
    # Players = [Player("Bob", 1000), Player("Jim", 1000), Player("Vin", 1000)]
    client = Client()
    players = [client.Player]
    """
    game_lobby = Lobby()
    game_lobby.create_game(6, 3, 10000, 25)
    for client in clients:
        GameLobby.client_join_lobby(client)

    for client in game_lobby.ConnectedClients:
        game_lobby.client_join_game(client, game_lobby.Games[0])
    """

    new_game = Game()
    new_game.Players = players
    new_game.setup(6, 3, 10000, 25)
    # Once the Game OBJECT has finished, delete the Game OBJECT and cleanup OBJECTS
    del new_game
    gc.collect()


# Start the program
if __name__ == "__main__":
    random.seed()
    main()
