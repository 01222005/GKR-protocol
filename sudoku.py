import hashlib, random, copy, pprint
from typing import List, Tuple

random.seed(42)  # demo用的固定隨機種子

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def make_nonce() -> str:
    return ''.join(random.choice('0123456789abcdef') for _ in range(16))

# 題目 (0=空格)
puzzle = [
    [5,3,0,0,7,0,0,0,0],
    [6,0,0,1,9,5,0,0,0],
    [0,9,8,0,0,0,0,6,0],
    [8,0,0,0,6,0,0,0,3],
    [4,0,0,8,0,3,0,0,1],
    [7,0,0,0,2,0,0,0,6],
    [0,6,0,0,0,0,2,8,0],
    [0,0,0,4,1,9,0,0,5],
    [0,0,0,0,8,0,0,7,9],
]

# 正確解答
solution = [
    [5,3,4,6,7,8,9,1,2],
    [6,7,2,1,9,5,3,4,8],
    [1,9,8,3,4,2,5,6,7],
    [8,5,9,7,6,1,4,2,3],
    [4,2,6,8,5,3,7,9,1],
    [7,1,3,9,2,4,8,5,6],
    [9,6,1,5,3,7,2,8,4],
    [2,8,7,4,1,9,6,3,5],
    [3,4,5,2,8,6,1,7,9]
]

# -----------------------------
# Prover：產生每格3張牌的commitment
# -----------------------------
class Prover:
    def __init__(self, puzzle, solution):
        self.puzzle = puzzle
        self.solution = solution
        self.cards = [[ None for _ in range(9)] for __ in range(9)]
        for r in range(9):
            for c in range(9):
                val = solution[r][c]
                cell_cards = []
                for i in range(3):
                    nonce = make_nonce()
                    commit = sha256_hex(f"{val}|{nonce}")
                    cell_cards.append({"value":val,"nonce":nonce,"commit":commit})
                self.cards[r][c] = cell_cards

    def get_commitment_board(self):
        board = []
        for r in range(9):
            row = []
            for c in range(9):
                cell = [self.cards[r][c][i]['commit'] for i in range(3)]
                row.append(cell)
            board.append(row)
        return board


    def open_selected(self, selections:List[Tuple[int,int,int]]):
        # 回應 Verifier 挑選的卡片並打亂順序
        openings = []
        for (r,c,i) in selections:
            card = self.cards[r][c][i]
            openings.append((card['value'], (r,c,i), card['nonce']))
        random.shuffle(openings)
        return openings

# -----------------------------
# Verifier：挑戰、檢查承諾與驗證packet是否1..9
# -----------------------------
class Verifier:
    def __init__(self, puzzle, commitment_board):
        self.puzzle = puzzle
        self.commitment_board = commitment_board

    def make_packet_challenge_for_row(self, row:int):
        return [(row,c,random.randint(0,2)) for c in range(9)]

    def verify_openings(self, openings):
        for val,(r,c,i),nonce in openings:
            expected = self.commitment_board[r][c][i]
            recomputed = sha256_hex(f"{val}|{nonce}")
            if recomputed != expected:
                return 0,"commitment_mismatch"
        values=[val for val,_,_ in openings]
        return (1,"ok") if sorted(values)==list(range(1,10)) else (0,"not_1_to_9")

# -----------------------------
# 執行一輪協議
# -----------------------------
def run_protocol_round(prover, verifier, row:int):
    selections = verifier.make_packet_challenge_for_row(row)
    openings = prover.open_selected(selections)
    result,reason = verifier.verify_openings(openings)
    return selections, openings, result, reason

# -----------------------------
# Demo
# -----------------------------
prover = Prover(puzzle, solution)
commit_board = prover.get_commitment_board()
verifier = Verifier(puzzle, commit_board)

selections, openings, result, reason = run_protocol_round(prover, verifier, row=0)

print("Verifier的挑戰(挑的卡):", selections)
print("Prover的回應(打亂後):", openings)
print("Verifier最終輸出:", result, reason)
