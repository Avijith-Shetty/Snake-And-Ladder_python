import wx
import random

# --------------------------
# GLOBAL GAME DATA
# --------------------------

BOARD_SIZE = 10

# Detect screen size
app = wx.App(False)
screen_width, screen_height = wx.GetDisplaySize()

# Board uses 85% of height to leave room
BOARD_PIXEL_SIZE = int(screen_height * 0.85)

# Cell size
CELL_SIZE = BOARD_PIXEL_SIZE // BOARD_SIZE
BOARD_PIXEL_SIZE = CELL_SIZE * BOARD_SIZE  # perfect square

SNAKES = {16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 98: 78}
LADDERS = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 96}

PLAYER_COLORS = [
    wx.Colour(255, 0, 0),
    wx.Colour(0, 0, 255),
    wx.Colour(0, 150, 0),
    wx.Colour(200, 100, 0),
]

# These will be set dynamically
PLAYER_NAMES = []
PLAYER_POS = []
CURRENT_PLAYER = 0
NUM_PLAYERS = 0

frame = None
board = None
dice_label = None
turn_label = None

# --------------------------
# POSITION HELPERS
# --------------------------

def pos_to_grid(pos):
    row = 9 - (pos - 1) // 10
    col = (pos - 1) % 10
    if (9 - row) % 2 == 1:
        col = 9 - col
    return row, col


def grid_to_pixel(row, col):
    return (col * CELL_SIZE + CELL_SIZE // 2,
            row * CELL_SIZE + CELL_SIZE // 2)


# --------------------------
# PAINTING BOARD
# --------------------------

def on_paint(event):
    dc = wx.PaintDC(board)

    # Gradient background
    dc.GradientFillLinear(
        (0, 0, BOARD_PIXEL_SIZE, BOARD_PIXEL_SIZE),
        wx.Colour(240, 240, 255),
        wx.Colour(210, 210, 240),
        wx.NORTH
    )

    num = 100
    left_to_right = True

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):

            # Checkerboard colors
            if (row + col) % 2 == 0:
                color = wx.Colour(255, 255, 230)
            else:
                color = wx.Colour(240, 240, 200)

            dc.SetBrush(wx.Brush(color))
            dc.SetPen(wx.Pen(wx.BLACK, 2))

            rc = col if left_to_right else (BOARD_SIZE - 1 - col)
            x, y = rc * CELL_SIZE, row * CELL_SIZE

            # Rounded cell
            dc.DrawRoundedRectangle(x, y, CELL_SIZE, CELL_SIZE, 6)

            # Number
            dc.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            dc.DrawText(str(num), x + 6, y + 6)

            num -= 1

        left_to_right = not left_to_right

    draw_arrows(dc)
    draw_players(dc)


def draw_arrows(dc):

    # SNAKES – red curved lines
    dc.SetPen(wx.Pen(wx.Colour(220, 0, 0), 5))

    for start, end in SNAKES.items():
        sr, sc = pos_to_grid(start)
        er, ec = pos_to_grid(end)
        sx, sy = grid_to_pixel(sr, sc)
        ex, ey = grid_to_pixel(er, ec)

        dc.DrawSpline([wx.Point(sx, sy), wx.Point((sx+ex)//2, (sy+ey)//2 + 20), wx.Point(ex, ey)])
        dc.DrawCircle(ex, ey, 7)

    # LADDERS – thicker green
    dc.SetPen(wx.Pen(wx.Colour(0, 200, 0), 6))

    for start, end in LADDERS.items():
        sr, sc = pos_to_grid(start)
        er, ec = pos_to_grid(end)

        sx, sy = grid_to_pixel(sr, sc)
        ex, ey = grid_to_pixel(er, ec)

        dc.DrawLine(sx, sy, ex, ey)
        dc.DrawCircle(ex, ey, 7)


def draw_players(dc):
    for i in range(NUM_PLAYERS):
        pos = PLAYER_POS[i]
        row, col = pos_to_grid(pos)
        x = col * CELL_SIZE + CELL_SIZE // 2
        y = row * CELL_SIZE + CELL_SIZE // 2

        x += (i % 2) * 12 - 6
        y += (i // 2) * 12 - 6

        dc.SetBrush(wx.Brush(PLAYER_COLORS[i]))
        dc.DrawCircle(x, y, 10)


# --------------------------
# GAME LOGIC
# --------------------------

def roll_dice(event):
    global CURRENT_PLAYER

    dice = random.randint(1, 6)
    dice_label.SetLabel(f"Dice: {dice}")

    new_pos = PLAYER_POS[CURRENT_PLAYER] + dice
    if new_pos <= 100:
        PLAYER_POS[CURRENT_PLAYER] = new_pos

    if new_pos in LADDERS:
        PLAYER_POS[CURRENT_PLAYER] = LADDERS[new_pos]

    if new_pos in SNAKES:
        PLAYER_POS[CURRENT_PLAYER] = SNAKES[new_pos]

    board.Refresh()

    if PLAYER_POS[CURRENT_PLAYER] == 100:
        dlg = wx.MessageDialog(None, f"🎉 {PLAYER_NAMES[CURRENT_PLAYER]} won!\n\nDo you want to restart the game?",
                               "Winner", wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            restart_game(None)  # Call restart without event
        dlg.Destroy()
        return

    CURRENT_PLAYER = (CURRENT_PLAYER + 1) % NUM_PLAYERS
    turn_label.SetLabel(f"Turn: {PLAYER_NAMES[CURRENT_PLAYER]}")


# --------------------------
# GET NUMBER OF PLAYERS
# --------------------------

def get_num_players():
    dlg = wx.NumberEntryDialog(None, "Enter number of players (2-4):", "Number of Players", "", 2, 2, 4)
    if dlg.ShowModal() == wx.ID_OK:
        num = dlg.GetValue()
        dlg.Destroy()
        return num
    dlg.Destroy()
    return None  # Indicate cancellation

# --------------------------
# NAME INPUT
# --------------------------

def get_player_names(num_players):
    dlg = wx.TextEntryDialog(None, f"Enter {num_players} player names (comma separated):",
                             "Player Names", "")
    if dlg.ShowModal() == wx.ID_OK:
        text = dlg.GetValue()
        names = [n.strip() for n in text.split(",")]
        player_names = []
        for i in range(num_players):
            if i < len(names) and names[i] != "":
                player_names.append(names[i])
            else:
                player_names.append(f"Player {i+1}")
        dlg.Destroy()
        return player_names
    dlg.Destroy()
    return None  # Indicate cancellation


# --------------------------
# RESTART GAME
# --------------------------

def restart_game(event):
    global PLAYER_POS, CURRENT_PLAYER

    PLAYER_POS = [1] * NUM_PLAYERS
    CURRENT_PLAYER = 0

    dice_label.SetLabel("Dice: -")
    turn_label.SetLabel(f"Turn: {PLAYER_NAMES[0]}")

    board.Refresh()


# --------------------------
# BUILD UI
# --------------------------

def build_ui():
    global frame, board, dice_label, turn_label, NUM_PLAYERS, PLAYER_NAMES, PLAYER_POS, CURRENT_PLAYER

    NUM_PLAYERS = get_num_players()
    if NUM_PLAYERS is None:
        return  # Exit if canceled

    PLAYER_NAMES = get_player_names(NUM_PLAYERS)
    if PLAYER_NAMES is None:
        return  # Exit if canceled

    PLAYER_POS = [1] * NUM_PLAYERS
    CURRENT_PLAYER = 0

    app = wx.App()
    frame = wx.Frame(
        None,
        title="Snake & Ladder (Beautiful UI)",
        size=(BOARD_PIXEL_SIZE + 350, BOARD_PIXEL_SIZE + 100)
    )

    panel = wx.Panel(frame)
    panel.SetBackgroundColour(wx.Colour(173, 216, 230))  # Light blue
    
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    # LEFT SIDE = BOARD
    global board
    board = wx.Panel(panel, size=(BOARD_PIXEL_SIZE, BOARD_PIXEL_SIZE))
    board.Bind(wx.EVT_PAINT, on_paint)
    hbox.Add(board, 0, wx.ALL, 10)

    # RIGHT SIDE = PLAYER INFO + BUTTONS
    right_side = wx.BoxSizer(wx.VERTICAL)

    # Big Roll Dice button
    dice_btn = wx.Button(panel, label="ROLL DICE", size=(180, 60))
    dice_btn.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    dice_btn.SetBackgroundColour(wx.Colour(0, 120, 255))
    dice_btn.SetForegroundColour(wx.WHITE)
    dice_btn.Bind(wx.EVT_BUTTON, roll_dice)
    right_side.Add(dice_btn, 0, wx.ALIGN_CENTER | wx.TOP, 100)

    # Restart button
    restart_btn = wx.Button(panel, label="RESTART GAME", size=(180, 40))
    restart_btn.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    restart_btn.SetBackgroundColour(wx.Colour(255, 100, 100))
    restart_btn.SetForegroundColour(wx.WHITE)
    restart_btn.Bind(wx.EVT_BUTTON, restart_game)
    right_side.Add(restart_btn, 0, wx.ALIGN_CENTER | wx.TOP, 10)

    # Dice label
    dice_label = wx.StaticText(panel, label="Dice: -")
    dice_label.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
    right_side.Add(dice_label, 0, wx.ALIGN_CENTER | wx.TOP, 20)

    # Turn label
    turn_label = wx.StaticText(panel, label=f"Turn: {PLAYER_NAMES[0]}")
    turn_label.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
    right_side.Add(turn_label, 0, wx.ALIGN_CENTER | wx.TOP, 10)

    # Player legend
    right_side.Add(wx.StaticText(panel, label="Players:"), 0, wx.TOP, 20)
    for i in range(NUM_PLAYERS):
        row = wx.BoxSizer(wx.HORIZONTAL)
        box = wx.Panel(panel, size=(25, 25))
        box.SetBackgroundColour(PLAYER_COLORS[i])
        label = wx.StaticText(panel, label=f"  {PLAYER_NAMES[i]}")
        row.Add(box, 0, wx.ALL, 5)
        row.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
        right_side.Add(row, 0, wx.TOP, 5)

    # Snake & Ladder Legend
    right_side.Add(wx.StaticText(panel, label="\nBoard Legend:"), 0, wx.TOP, 20)

    snake_row = wx.BoxSizer(wx.HORIZONTAL)
    snake_box = wx.Panel(panel, size=(25, 25))
    snake_box.SetBackgroundColour(wx.RED)
    snake_row.Add(snake_box, 0, wx.ALL, 5)
    snake_row.Add(wx.StaticText(panel, label="  Snakes (Red)"))
    right_side.Add(snake_row, 0, wx.TOP, 5)

    ladder_row = wx.BoxSizer(wx.HORIZONTAL)
    ladder_box = wx.Panel(panel, size=(25, 25))
    ladder_box.SetBackgroundColour(wx.GREEN)
    ladder_row.Add(ladder_box, 0, wx.ALL, 5)
    ladder_row.Add(wx.StaticText(panel, label="  Ladders (Green)"))
    right_side.Add(ladder_row, 0, wx.TOP, 5)

    hbox.Add(right_side, 0, wx.LEFT, 30)
    panel.SetSizer(hbox)
    frame.Show()
    app.MainLoop()


# --------------------------
# RUN GAME
# --------------------------
if __name__ == "__main__":
    build_ui()