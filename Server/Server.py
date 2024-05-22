import random
import errno
import socket
import threading
import queue
import time
import States
from Encryption import Cipher

""" Constants """
# Money
MAX_WAGER_LOWER_BOUND = 2
MAX_WAGER_UPPER_BOUND = 99999
DEFAULT_BALANCE = 1000


""" Server Related Stuff """


class Server:
    # Create a Server OBJECT
    def __init__(self, host="127.0.0.1", port=50001):
        self.HOST = host
        self.PORT = port
        # Buffers responsible for storing Incoming and Outgoing messages
        self.InputBuffer = queue.Queue()
        self.OutputBuffer = queue.Queue()
        # Booleans for loops
        self.Running = True
        self.Writing = True
        self.Reading = True
        self.Processing = True
        # Connection information
        self.Conn = None
        self.Addr = None
        self.ClientConnected = False
        # Threads used to run read/write asynchronously
        self.ReadThread = threading.Thread(target=self.read)
        self.WriteThread = threading.Thread(target=self.write)

    # Write THREAD function
    def write(self):
        print("Write Thread Started")
        while self.Writing:
            # Server has stopped and all messages have been sent
            if not self.Running and self.OutputBuffer.empty():
                self.Writing = False
            # Messages still remain in the Output BUFFER to send
            if not self.OutputBuffer.empty():
                # Encrypt data
                data = Cipher.cipher(self.OutputBuffer.get(), True)
                self.Conn.sendall(data.encode("utf-8"))

    # Read THREAD function
    def read(self):
        print("Reading Thread Started")
        # Create the Server Socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.HOST, self.PORT))

            # Wait for Client connection
            s.listen()
            self.Conn, self.Addr = s.accept()
            self.ClientConnected = True

            # Client has connected
            with self.Conn:
                # Prevent blocking
                self.Conn.setblocking(False)
                print(f"Connected {self.Addr}")

                while self.Reading:
                    if not self.Running:
                        self.Reading = False
                        break

                    # Socket has activity
                    try:
                        # Receive data from Client
                        data = self.Conn.recv(1024)
                        if data:
                            # Decrypt data
                            message = Cipher.cipher(data.decode("utf-8"), False)
                            # Add it to the Input BUFFER
                            self.InputBuffer.put(message)

                    # Socket is inactive
                    except socket.error as e:
                        err = e.args[0]
                        # Either repeated inactivity or actions would cause blocking
                        if err in [errno.EAGAIN, errno.EWOULDBLOCK]:
                            time.sleep(0)
                        # Socket has closed
                        else:
                            self.Running = False
                            self.Conn.shutdown(socket.SHUT_RDWR)

    # Start the Read and Write THREADS
    def process(self):
        self.ReadThread.start()
        self.WriteThread.start()

    # Get messages from the Input BUFFER
    def get_message(self):
        # BUFFER has data
        if not self.InputBuffer.empty():
            message = self.InputBuffer.get()
            print(f"Received {self.Addr}: {message}")
            # Handle "quit" message from Client
            if message.lower() == "quit":
                print(f"Disconnected {self.Addr}: Shutting down!")
                self.Running = False
            return message
        else:
            return None

    # Put message in the Output BUFFER
    def push_message(self, message):
        self.OutputBuffer.put(message)

    # Stop the main loop and both THREADS
    def quit(self):
        self.Running = False
        self.ReadThread.join()
        self.WriteThread.join()


""" Game Related Stuff """


# Values for each Card OBJECT
class CardValues:
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


class Hand:
    # Create a new Hand OBJECT
    def __init__(self, wager_amount=0):
        self.State = States.HandStates.Idle
        self.Cards = []
        self.Value = 0
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


class Player:
    # Create a new Player OBJECT
    def __init__(self):
        self.State = States.PlayerStates.WaitingForGame
        self.Username = None
        self.Balance = 1000
        self.Wager = 0
        self.TotalWager = 0
        self.Hands = [Hand()]

    # Self-explanatory
    def output_bet_info(self):
        return f"OUTPUT \n{self.Username}: Betting ({self.Wager})" \
               f"\nCurrent Balance ({self.Balance})" \
               f"\nTotal Wager ({self.TotalWager}).||"

    # Create Wager VALUE for the Player OBJECT and their Hand OBJECT
    def wager_bet(self, amount):
        self.Balance -= amount
        self.Wager = amount
        self.TotalWager += self.Wager
        self.Hands[0].Wager = amount
        return self.output_bet_info()

    # Increase TotalWager VALUE of the Player OBJECT and their current Hand OBJECT's Wager VALUE
    def increase_bet(self, hand_obj):
        self.Balance -= self.Wager
        self.TotalWager += self.Wager
        hand_obj.Wager += self.Wager
        return self.output_bet_info()

    # Payout Hand OBJECT's Wager VALUE * multiplier VALUE
    def win_bet(self, hand_obj, mult):
        self.Balance += hand_obj.Wager * mult
        hand_obj.Wager = 0

    # Payout Hand OBJECT's Wager Value
    def push_bet(self, hand_obj):
        self.Balance += hand_obj.Wager
        hand_obj.Wager = 0


class Dealer:
    # Create a new Dealer OBJECT
    def __init__(self):
        self.State = States.DealerStates.WaitingForGame
        self.Hand = Hand()


class Game:
    # Create a new Game OBJECT
    def __init__(self):
        self.State = States.GameStates.SetUsername
        # Server OBJECT
        self.Server = Server()
        self.Running = True
        # Setup options initialisation
        self.NoDecks = None
        self.ShuffleAfter = None
        self.MinWager = None
        self.MaxWager = None
        # Game-related OBJECTS
        self.Shoe = Shoe()
        self.Dealer = Dealer()
        self.Player = Player()
        # Game-related ARRAYS
        self.Players = []
        self.PlayingPlayers = []
        self.BrokePlayers = []

    # Main function
    def process(self):
        # Run whilst Server SCRIPT is still running
        try:
            # Start the Server OBJECT's THREADS
            self.Server.process()

            # Wait for a Client connection
            while not self.Server.ClientConnected:
                time.sleep(1)

            # Main loop
            while self.Running:
                # State machine
                if self.State == States.GameStates.SetUsername:
                    print("GAME: Setting Username!")
                    self.set_username()
                    self.Players.append(self.Player)
                    self.State = States.GameStates.Setup
                elif self.State == States.GameStates.Setup:
                    print("GAME: Setting up Game!")
                    self.setup()  # Default VALUES used in Testing: (4, 2, 1000, 2)
                elif self.State == States.GameStates.Start:
                    print("GAME: Starting Game!")
                    self.State = States.GameStates.Shuffling
                elif self.State == States.GameStates.Shuffling:
                    print("GAME: Shuffling Cards!")
                    self.shuffle_cards()
                elif self.State == States.GameStates.PlaceBets:
                    print("GAME: Place Bets!")
                    self.place_bets()
                elif self.State == States.GameStates.DealingCards:
                    print("GAME: Dealing Cards!")
                    self.deal_cards()
                elif self.State == States.GameStates.PlayersTurn:
                    print("GAME: Players' Turn!")
                    self.players_turn()
                elif self.State == States.GameStates.DealerTurn:
                    print("GAME: Dealer's Turn!")
                    self.dealer_turn()
                elif self.State == States.GameStates.Payout:
                    print("GAME: Paying Out Winnings!")
                    self.payout()
                elif self.State == States.GameStates.EndRound:
                    print("GAME: Ending Round!")
                    self.end_round()
                elif self.State == States.GameStates.NewRound:
                    print("GAME: Starting New Round!")
                    # Shuffle the Shoe OBJECT's Card OBJECTS after the given number of
                    # Deck OBJECTS' Card OBJECTS has been moved to the DiscardedCards LIST
                    if len(self.Shoe.DiscardedCards) > (self.ShuffleAfter * 52):
                        self.State = States.GameStates.Shuffling
                    # Skip Shuffling STATE of loop if conditions are not met
                    else:
                        self.State = States.GameStates.PlaceBets
                elif self.State == States.GameStates.EndGame:
                    print("GAME: Ending Game!")
                    self.end_game()
                elif self.State == States.GameStates.Deleted:
                    print("GAME: Deleted Game!")
                    return
                elif self.State == States.GameStates.Error:
                    # print("GAME: CRITICAL ERROR!")
                    break
        # Server SCRIPT was forcefully closed
        except KeyboardInterrupt:
            print("Keyboard Interrupt: Shutting down!")
        # Stop the Server THREADS and delete the Game OBJECT
        finally:
            self.Server.quit()
            del self

    # Get messages from the Server OBJECT's Input BUFFER
    def get_message(self):
        while True:
            message = self.Server.get_message()
            if message:
                # Handle "quit" message from Client
                if message.lower() == "quit":
                    self.Running = False
                    return message, True
                return message, False

    # Self-explanatory
    def set_username(self):
        while True:
            self.Server.push_message("INPUT \nGAME: Input Username:\n->||")
            # Get message from Client
            message, is_quit = self.get_message()
            # Client sent "quit" message
            if is_quit:
                return
            if len(message) <= 0:
                self.Server.push_message("OUTPUT GAME: Username cannot be empty.\n||")
            else:
                self.Player.Username = message
                break

    # Setup Game OBJECT specific variables rather than initialising the Game OBJECT with static variables
    def setup(self, no_decks=None, shuffle_after=None, max_wager=None, min_wager=None):
        # Ensure the setup is only run once upon creation of the Game OBJECT
        if self.State != States.GameStates.Setup:
            self.State = States.GameStates.Error
            return

        # Register number of Deck OBJECTS to include in the Shoe OBJECT's Cards LIST
        if no_decks is None:
            while True:
                self.Server.push_message("INPUT \nGAME: Input number of decks to include in the shoe\n(2 - 8)\n->||")
                message, is_quit = self.get_message()
                if is_quit:
                    return
                try:
                    self.NoDecks = int(message)
                    if self.NoDecks <= 1:
                        self.Server.push_message("OUTPUT GAME: Number of decks cannot be less than 2.\n||")
                    elif self.NoDecks > 8:
                        self.Server.push_message("OUTPUT GAME: Number of decks cannot be more than 8.\n||")
                    else:
                        break
                except (TypeError, ValueError):
                    self.Server.push_message("OUTPUT GAME: Please enter a valid number.\n||")
        else:
            self.NoDecks = no_decks

        self.Shoe.generate_shoe(self.NoDecks)
        # Register number of Deck OBJECTS played before shuffling
        if shuffle_after is None:
            while True:
                self.Server.push_message(f"INPUT \nGAME: Input how many decks in should the shoe be shuffled\n"
                                         f"(1 - {self.NoDecks - 1})\n->||")
                message, is_quit = self.get_message()
                if is_quit:
                    return
                try:
                    self.ShuffleAfter = int(message)
                    if self.ShuffleAfter <= 0:
                        self.Server.push_message("OUTPUT GAME: Number of decks in cannot be less than 1.\n||")
                    elif self.ShuffleAfter >= self.NoDecks:
                        self.Server.push_message(f"OUTPUT GAME: Number of decks in cannot be more than the total "
                                                 f"number of decks - 1 ({self.NoDecks - 1}).\n||")
                    else:
                        break
                except (TypeError, ValueError):
                    self.Server.push_message("OUTPUT GAME: Please enter a valid number.\n||")
        else:
            self.ShuffleAfter = shuffle_after

        # Register the maximum wager VALUE
        if max_wager is None:
            while True:
                self.Server.push_message("INPUT \nGAME: Input the maximum wager\n->||")
                message, is_quit = self.get_message()
                if is_quit:
                    return
                try:
                    self.MaxWager = int(message)
                    if self.MaxWager <= MAX_WAGER_LOWER_BOUND:
                        self.Server.push_message(f"OUTPUT GAME: Maximum wager cannot be less than or equal to "
                                                 f"{MAX_WAGER_LOWER_BOUND}.\n||")
                    elif self.MaxWager > MAX_WAGER_UPPER_BOUND:
                        self.Server.push_message(f"OUTPUT GAME: Maximum wager cannot be more than "
                                                 f"{MAX_WAGER_UPPER_BOUND}.\n||")
                    else:
                        break
                except (TypeError, ValueError):
                    self.Server.push_message("OUTPUT GAME: Please enter a valid number.\n||")
        else:
            self.MaxWager = max_wager

        # Register the minimum wager VALUE
        if min_wager is None:
            while True:
                self.Server.push_message("INPUT \nGAME: Input the minimum wager\n->||")
                message, is_quit = self.get_message()
                if is_quit:
                    return
                try:
                    self.MinWager = int(message)
                    if self.MinWager <= 0:
                        self.Server.push_message("OUTPUT GAME: Minimum wager cannot be less than or equal to 0.\n||")
                    elif self.MinWager > self.MaxWager:
                        self.Server.push_message(f"OUTPUT GAME: Minimum wager cannot be more than the maximum wager "
                                                 f"({self.MaxWager}).\n||")
                    else:
                        break
                except (TypeError, ValueError):
                    self.Server.push_message("OUTPUT GAME: Please enter a valid number.\n||")
        else:
            self.MinWager = min_wager
        self.State = States.GameStates.Start

    # Shuffle the Shoe LIST a random number of times between X and Y
    def shuffle_cards(self):
        for i in range(random.randint(3, 5)):
            self.Shoe.shuffle_shoe()
        self.State = States.GameStates.PlaceBets

    # Place a bet for each Player OBJECT
    def place_bets(self):
        for player in self.Players:
            player.State = States.PlayerStates.Betting
            # If Player OBJECT's Balance VALUE is lower than the MinWager VALUE, they cannot bet and must spectate
            if player.Balance < self.MinWager:
                self.Server.push_message(f"OUTPUT \n{player.Username}: Cannot bet at this game as balance is too low!"
                                         f"\nCurrent Balance ({player.Balance})"
                                         f"\nGame Minimum Bet ({self.MinWager})\n"
                                         f"\n{player.Username}: No longer playing.||")
                player.State = States.PlayerStates.Broke
                self.BrokePlayers.append(player)
                continue
            # User input for Player OBJECT's bet
            while True:
                self.Server.push_message(f"INPUT \n{player.Username}: Current Balance ({player.Balance})"
                                         f"\nEnter bet amount ({self.MinWager} - {self.MaxWager})\n->||")
                message, is_quit = self.get_message()
                if is_quit:
                    return
                try:
                    wager = int(message)
                    if wager < self.MinWager:
                        self.Server.push_message(f"OUTPUT {player.Username}: Cannot bet less than the minimum bet "
                                                 f"({self.MinWager}).||")
                    elif wager > player.Balance:
                        self.Server.push_message(f"OUTPUT {player.Username}: Cannot bet more than your current balance "
                                                 f"({player.Balance}).||")
                    elif wager > self.MaxWager:
                        self.Server.push_message(f"OUTPUT {player.Username}: Cannot bet more than the maximum bet "
                                                 f"({self.MaxWager}).||")
                    else:
                        self.Server.push_message(player.wager_bet(wager))
                        player.State = States.PlayerStates.WaitingForTurn
                        self.PlayingPlayers.append(player)
                        break
                except (ValueError, TypeError):
                    if message.lower() == "spectate":
                        player.State = States.PlayerStates.Spectating
                        self.Server.push_message(f"OUTPUT {player.Username}: Spectating this round.\n||")
                        break
                    else:
                        self.Server.push_message(f"OUTPUT {player.Username}: Please enter a valid amount.||")

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
                hand_obj.State = States.HandStates.Busted
                self.Server.push_message(f"OUTPUT \n{player_obj.Username}: ({hand_obj.evaluate_value()}) "
                                         f"{hand_obj.display_hand()}.\n{player_obj.Username}: BUST!||")
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
                self.Server.push_message(f"OUTPUT \n{player.Username}: ({hand_obj.evaluate_value()}) "
                                         f"{hand_obj.display_hand()}.||")
                if hand_obj.evaluate_value() == 21:
                    self.Server.push_message(f"OUTPUT {player.Username}: BLACKJACK!||")
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
                    # Allow DoubleDown if Player OBJECT has enough Balance VALUE to bet their Wager VALUE
                    if (player.TotalWager + player.Wager) <= (player.Balance + player.Wager):
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
                self.Server.push_message(f"INPUT {player.Username}: Available Actions ({player_action_string}).\n->||")
                message, is_quit = self.get_message()
                if is_quit:
                    # Used to break out of recursive loops (many Hand OBJECTS)
                    raise ValueError("Exiting Recursion")
                player_action = States.PlayerActions.from_string(message.lower())

                if player_action not in available_actions:
                    self.Server.push_message(f"OUTPUT {player.Username}: Enter a valid action "
                                             f"({player_action_string}).||")
                    continue

                if player_action == States.PlayerActions.Hit:
                    self.Shoe.play_card(hand_obj.Cards)
                    if check_if_bust(player, hand_obj):
                        if player.Hands.index(hand_obj) == 0:
                            player.State = States.PlayerStates.TurnEnd
                        break

                elif player_action == States.PlayerActions.DoubleDown:
                    self.Server.push_message(player.increase_bet(hand_obj))
                    self.Shoe.play_card(hand_obj.Cards)
                    self.Server.push_message(f"OUTPUT \n{player.Username}: {hand_obj.display_hand()} "
                                             f"({hand_obj.evaluate_value()}).||")
                    if not check_if_bust(player, hand_obj):
                        hand_obj.State = States.HandStates.DoubleDown
                    if player.Hands.index(hand_obj) == 0:
                        player.State = States.PlayerStates.TurnEnd
                    break

                elif player_action == States.PlayerActions.Split:
                    player.Hands.append(Hand())
                    player.Hands[-1].Cards.append(hand_obj.Cards.pop())
                    self.Server.push_message(player.increase_bet(player.Hands[-1]))
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
            player.State = States.PlayerStates.Playing
            self.Server.push_message(f"OUTPUT \nDealer: ({self.Dealer.Hand.evaluate_value()}) "
                                     f"{self.Dealer.Hand.display_hand()}.||")
            # Ensure Client can "quit" by having a purposefully raised "ValueError" to bring
            # possible recursion back to top level and exit safely
            try:
                player_turn_hand(player.Hands[0])
            except ValueError:
                return
        self.State = States.GameStates.DealerTurn

    # Display Hand LIST of the Dealer OBJECT and play based on regular Dealer Blackjack rules
    # (Stand if Hand OBJECT's VALUE is 17 or higher, else Hit)
    def dealer_turn(self):
        self.Dealer.State = States.DealerStates.Playing
        self.Dealer.Hand.Cards[-1].flip_card()
        while True:
            message = f"OUTPUT \nDealer: ({self.Dealer.Hand.evaluate_value()}) {self.Dealer.Hand.display_hand()}."
            if self.Dealer.State != States.DealerStates.Playing:
                break
            if self.Dealer.Hand.evaluate_value() == 21:
                message += "\nDealer: BLACKJACK!||"
                self.Dealer.State = States.DealerStates.Blackjack
            elif self.Dealer.Hand.evaluate_value() > 21:
                message += "\nDealer: BUST!||"
                self.Dealer.State = States.DealerStates.Busted
            elif self.Dealer.Hand.evaluate_value() < 17:
                message += "\nDealer: HIT!||"
                self.Shoe.play_card(self.Dealer.Hand.Cards)
            elif self.Dealer.Hand.evaluate_value() >= 17:
                message += "\nDealer: STAND!||"
                self.Dealer.State = States.DealerStates.Standing
            self.Server.push_message(message)
        self.State = States.GameStates.Payout

    # Process each Player OBJECT's Hand OBJECT for win/lose conditions
    def payout(self):
        for player in self.PlayingPlayers:
            self.Server.push_message(f"OUTPUT \n{player.Username} Payouts:||")
            for hand in player.Hands:
                # Hand Busted = no payout
                if hand.State == States.HandStates.Busted:
                    self.Server.push_message(f"OUTPUT {player.Username}: Hand Number {player.Hands.index(hand) + 1} "
                                             f"BUSTED! No Payout.||")
                    continue
                # Player Hand more than Dealer Hand OR Dealer Hand Busted = payout depending on Hand State
                if hand.evaluate_value() > self.Dealer.Hand.evaluate_value() \
                        or self.Dealer.State == States.DealerStates.Busted:
                    # Hand Blackjack = payout * 3
                    if hand.State == States.HandStates.Blackjack:
                        self.Server.push_message(f"OUTPUT {player.Username}: Hand Number {player.Hands.index(hand) + 1}"
                                                 f" BLACKJACK! Payout {hand.Wager * 3}||")
                        player.win_bet(hand, 3)
                    # Hand NOT Blackjack
                    else:
                        self.Server.push_message(f"OUTPUT {player.Username}: Hand Number {player.Hands.index(hand) + 1}"
                                                 f" Won! Payout {hand.Wager * 2}||")
                        player.win_bet(hand, 2)
                # Player Hand same as Dealer Hand = payout * 1 (Pushback)
                elif hand.evaluate_value() == self.Dealer.Hand.evaluate_value():
                    self.Server.push_message(f"OUTPUT {player.Username}: Hand Number {player.Hands.index(hand) + 1} "
                                             f"Tied! Payout {hand.Wager}||")
                    player.win_bet(hand, 1)
                # Player Hand less than Dealer Hand = no payout
                else:
                    self.Server.push_message(f"OUTPUT {player.Username}: Hand Number {player.Hands.index(hand) + 1} "
                                             f"Lost! No Payout.||")
            self.Server.push_message(f"OUTPUT {player.Username}: Balance ({player.Balance})||")
        self.State = States.GameStates.EndRound

    # Cleanup Player OBJECTS in PlayingPlayers LIST then cleanup Dealer OBJECT
    def end_round(self):
        for player in self.PlayingPlayers:
            for hand in player.Hands:
                # Move all Card OBJECTS from each Hand OBJECT to the Shoe OBJECT's DiscardedCards LIST
                while len(hand.Cards) > 0:
                    self.Shoe.DiscardedCards.append(hand.Cards.pop())
                # Delete the Hand OBJECT for memory optimisation
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

    # End Game OBJECT
    def end_game(self):
        self.State = States.GameStates.Deleted


# Entry to the SCRIPT
if __name__ == "__main__":
    random.seed()
    game = Game()
    game.process()
