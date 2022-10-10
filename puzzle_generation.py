'''
Generate Checkmate Puzzles from the games that have been played by a user on chess.com

Usage:

python puzzle-generation.py -u CHESSDOTCOM_USERNAME -p PATH_TO_STOCKFISH [-n NUMBER_OF_GAMES_USED]

A json file with generated checkmate puzzles extracted from the supplied user's games is created
in src/assets/puzzles.json. This may take a while, because all the user's games have to be
downloaded and NUMBER_OF_GAMES_USED games have to be evaluated by stockfish.
'''

import io
import json
from typing import List, Dict
import argparse
import requests

import chess
import chess.engine
import chess.pgn
from chess import Board


# Initialize parser
parser = argparse.ArgumentParser()

# Adding optional argument
parser.add_argument("-u", "--Username", help = "Chess.com Username", type=str)
parser.add_argument("-p", "--EnginePath", help = "Path to Stockfish", type=str)
parser.add_argument("-n", "--NGames", help = "Number of Games used", type=int)

# Read arguments from command line
args = parser.parse_args()

# defaults:
N_GAMES = 100

user = args.Username
engine_path = args.EnginePath
engine = chess.engine.SimpleEngine.popen_uci(engine_path)

if args.NGames:
    N_GAMES = args.NGames

def get_games(username: str) -> List:
    """
        Parameters:
        ----------
        username : str
            The name of the chess.com user from which the games are downloaded

        Returns:
        ----------
        games_list : List
            A list that contains dictionaries of games

        Description:
        ----------
        Download all games of {username} via chess.com's API and store them in variable games_list
    """

    print(f"Download all games from chess.com for user: {username}")
    req = requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", timeout=600)
    archive_urls = req.json()["archives"]
    games_list = []

    for url in archive_urls:
        archived_games = requests.get(url, timeout=600).json()["games"]

        for game in archived_games:
            games_list.append(game)

    return games_list


def stockfish_evaluation(board : Board, time_limit: float = 0.01) -> float:
    """
        Parameters:
        ----------
        board : Board
            chess Board class object
        time_limit: float | default = 0.01
            time for the engine to evaluate the position

        Returns:
        ----------
        result["score"] : float
            Engine evaluation of baord position

        Description:
        ----------
        Analyze a {board} position with the engine under the constraint of a given {time_limit}.
    """

    result = engine.analyse(board, chess.engine.Limit(time=time_limit))
    return result['score']

def evaluate_games(games_list: List, max_games: int = 100) -> List:
    """
        Parameters:
        ----------
        games_list : List
            A list that contains dictionaries of games
        max_games: int | default = 100
            Maximum number of games that should be evaluated

        Returns:
        ----------
        games_list : List
            A list that contains dictionaries of games with new entry "evaluation"

        Description:
        ----------
        Evaluate the first {max_games} and store it in the dictionary under the key "evaluation"
    """

    print(f"Evaluate with the engine {max_games} games from chess.com for user: {user}")
    for games in games_list[0:max_games]:

        pgn = io.StringIO(games["pgn"])
        game = chess.pgn.read_game(pgn)
        board = game.board()
        evaluation = []
        for move in game.mainline_moves():
            evaluation.append(stockfish_evaluation(board).white().score())
            board.push(move)

        games["evaluation"] = evaluation

    return games_list

def forced_mate(game: Dict) -> bool:
    """
        Parameters:
        ----------
        game: dict
            dictionary of game
        Returns:
        ----------
        ismate : bool
            True if a forced checkmate is present in the game

        Description:
        ----------
        Check if a forced checkmate is present in a provided game
    """

    ismate = None in game["evaluation"]
    return ismate


def create_puzzles(games_list: List, max_games: int = 100, max_complexity: int = 9) -> None:
    """
        Parameters:
        ----------
        games_list : List
            A list that contains dictionaries of games
        max_games: int | default = 100
            Maximum number of games that should be evaluated
        max_complexity: int
            Maximum number of moves (black & white) until checkmate

        Returns:
        ----------
        None

        Description:
        ----------
        Create checkmate puzzzles based on {max_games} of {games_list} with a {max_complexity}.
        The resulting puzzles are stored at src/assets/puzzles.json.
    """

    print(f"Create checkmate puzzles based on {max_games} games from chess.com of user: {user}")
    puzzle_list = []

    for games in games_list[0:max_games]:

        if forced_mate(games):
            pgn = io.StringIO(games["pgn"])
            game = chess.pgn.read_game(pgn)
            board = game.board()

            counter = 0
            for move in game.mainline_moves():

                if games["evaluation"][counter] is None:
                    solution = engine.analyse(board, chess.engine.Limit(time=0.05))["pv"]
                    moves = []
                    for string in list(str(solution).split(',')):
                        tmp = (string[string.find("(")+1:string.find(")")])
                        moves.append(tmp[1:len(tmp)-1])

                    if (len(moves) <= max_complexity and (len(moves)%2 == 1)):
                        puzzle_list.append({'puzzle-uuid': games["uuid"] ,'puzzle-fen': board.fen(),
                                            'puzzle-solution' : moves, 'puzzle_type' : 'checkmate',
                                            'puzzle-complexity' : len(moves)})

                counter = counter + 1
                board.push(move)

    print("Write checkmate puzzles to src/assets/puzzles.json")

    with open('src/assets/puzzles.json', 'w', encoding='utf-8') as file:
        json.dump(puzzle_list, file, ensure_ascii=False, indent=4)

    file.close()

    return None


###############################
# Execute the puzzle creation #
###############################

chess_games = []
chess_games = get_games(username=user)
chess_games = evaluate_games(chess_games, max_games=min(N_GAMES, len(chess_games)))

create_puzzles(games_list=chess_games, max_games=min(N_GAMES, len(chess_games)))

# close connection to the chess engine
engine.close()
