import chesspuzzle from './assets/puzzles.json';

var game = new Chess()
        
var solution
var movecounter
var color

function onDragStart (source, piece, position, orientation) {
// do not pick up pieces if the game is over
    if (game.isGameOver()) return false

// only pick up pieces for the side to move
    if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
        (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
        return false
    }
}

function onDrop (source, target) {

    // see if the move is legal
    if (solution[movecounter].length == 5){
        var move = game.move({
            from: source,
            to: target,
            promotion: 'q'
        })
    }
    else
    {
        var move = game.move({
            from: source,
            to: target,
        })
    }

    // illegal move
    if (move === null) {
        return 'snapback'
    }
    // check if move is correct 
    if (source+target != solution[movecounter] && source+target+'q' != solution[movecounter]){
        game.undo();
        return 'snapback'
    }
    else {
        movecounter++
    }

    updateStatus()
    autoMove()

}

function autoMove(){

    if (!game.isCheckmate()){
        var from = solution[movecounter].substring(0, 2);
        var to = solution[movecounter].substring(2, 4);

        game.move({ from: from,
                    to : to
        })

        movecounter++
    }
    else {
        initialize()
    }
}
// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd () {
    board.position(game.fen())
}

function updateStatus () {
    var status = ''

    var moveColor = 'White'
    if (game.turn() === 'b') {
        moveColor = 'Black'
    }

    // checkmate?
    if (game.isCheckmate()) {
        status = 'Game over, ' + moveColor + ' is in checkmate.'
    }
    //draw?
    else if (game.isDraw()) {
        status = 'Game over, drawn position'
    }
    // game still on
    else {
        status = moveColor + ' to move'

        // check?
        if (game.isCheck()) {
            status += ', ' + moveColor + ' is in check'
        }
    }
}

var cfg = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd
};

var board = ChessBoard('board', cfg)

initialize();
updateStatus()


function initialize () {
    
    function getRandomInt(max) {
        return Math.floor(Math.random() * max);
    }
      
    var random_int = getRandomInt(chesspuzzle.length)
    console.log("Puzzle Number" + random_int);

    board.position(chesspuzzle[random_int]["puzzle-fen"])
    game = new Chess(chesspuzzle[random_int]["puzzle-fen"])

    // flip board if it is blacks turn
    color = chesspuzzle[random_int]["puzzle-fen"].split(" ")[1]

    if (color == "b") {
        board.orientation("black")
    }else{
        board.orientation("white")
    }

    solution = chesspuzzle[random_int]["puzzle-solution"]
    movecounter = 0
}

$('#skipBtn').on('click', function () {
    initialize()
}) 