import pygame
import socket
import pickle
import threading
import queue
import sys

# Configuração do servidor
HOST = '127.0.0.1'
PORT = 5555

# Inicializa o cliente socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# Inicializa o Pygame
pygame.init()

# Configurações do jogo
WIDTH, HEIGHT = 600, 650
GRID_SIZE = 5
DOT_RADIUS = 10
MARGIN = 50
CELL_SIZE = (WIDTH - 2 * MARGIN) // (GRID_SIZE - 1)
LINE_WIDTH = 5

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dots and Boxes")

# Variáveis do cliente
player_id = None
state = None
message_queue = queue.Queue()

# Renderiza o tabuleiro
def draw_board():
    screen.fill((255, 255, 255))

    # Pontuação
    font = pygame.font.SysFont(None, 40)
    score_text = f"Player 1: {state['scores'][0]}  |  Player 2: {state['scores'][1]}"
    text = font.render(score_text, True, (0, 0, 0))
    screen.blit(text, (MARGIN, 10))

    # Pontos
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            pygame.draw.circle(screen, (0, 0, 0), (MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE + 50), DOT_RADIUS)

    # Linhas horizontais
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE - 1):
            if state["horizontal_lines"][row][col]:
                color = (255, 0, 0) if state["horizontal_lines"][row][col] == 1 else (0, 0, 255)
                pygame.draw.line(screen, color,
                                 (MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE + 50),
                                 (MARGIN + (col + 1) * CELL_SIZE, MARGIN + row * CELL_SIZE + 50), LINE_WIDTH)

    # Linhas verticais
    for row in range(GRID_SIZE - 1):
        for col in range(GRID_SIZE):
            if state["vertical_lines"][row][col]:
                color = (255, 0, 0) if state["vertical_lines"][row][col] == 1 else (0, 0, 255)
                pygame.draw.line(screen, color,
                                 (MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE + 50),
                                 (MARGIN + col * CELL_SIZE, MARGIN + (row + 1) * CELL_SIZE + 50), LINE_WIDTH)

    # Caixas preenchidas
    for row in range(GRID_SIZE - 1):
        for col in range(GRID_SIZE - 1):
            if state["boxes"][row][col] is not None:
                color = (255, 0, 0) if state["boxes"][row][col] == 1 else (0, 0, 255)
                pygame.draw.rect(screen, color,
                                 (MARGIN + col * CELL_SIZE + LINE_WIDTH, MARGIN + row * CELL_SIZE + LINE_WIDTH + 50,
                                  CELL_SIZE - LINE_WIDTH * 2, CELL_SIZE - LINE_WIDTH * 2))

    pygame.display.flip()

# Detecta o clique e envia ao servidor
def handle_click(pos):
    x, y = pos
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE - 1):
            line_x1 = MARGIN + col * CELL_SIZE
            line_x2 = MARGIN + (col + 1) * CELL_SIZE
            line_y = MARGIN + row * CELL_SIZE + 50
            if line_x1 <= x <= line_x2 and abs(line_y - y) <= LINE_WIDTH // 2 and not state["horizontal_lines"][row][col]:
                return {"line_type": "horizontal", "row": row, "col": col}

    for row in range(GRID_SIZE - 1):
        for col in range(GRID_SIZE):
            line_y1 = MARGIN + row * CELL_SIZE + 50
            line_y2 = MARGIN + (row + 1) * CELL_SIZE + 50
            line_x = MARGIN + col * CELL_SIZE
            if line_y1 <= y <= line_y2 and abs(line_x - x) <= LINE_WIDTH // 2 and not state["vertical_lines"][row][col]:
                return {"line_type": "vertical", "row": row, "col": col}

    return None

# Thread para gerenciar comunicação com o servidor
def socket_thread():
    global state
    while True:
        try:
            data = client.recv(4096)
            if not data:
                break
            state = pickle.loads(data)
            message_queue.put(state)
        except:
            print("Erro na comunicação com o servidor.")
            break

# Lógica principal do cliente
def game_loop():
    global state
    threading.Thread(target=socket_thread, daemon=True).start()  # Inicia thread de socket

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and state["player_turn"] == player_id:
                move = handle_click(pygame.mouse.get_pos())
                if move:
                    client.sendall(pickle.dumps(move))

        # Atualiza estado do jogo
        while not message_queue.empty():
            state = message_queue.get()

        # Verifica se o jogo acabou
        if state["game_over"]:
            show_winner()

        draw_board()

# Mostra o vencedor na tela
def show_winner():
    screen.fill((255, 255, 255))
    font = pygame.font.SysFont(None, 72)

    if state["scores"][0] > state["scores"][1]:
        text = font.render("Player 1 Wins!", True, (255, 0, 0))
    elif state["scores"][1] > state["scores"][0]:
        text = font.render("Player 2 Wins!", True, (0, 0, 255))
    else:
        text = font.render("It's a Tie!", True, (128, 128, 128))

    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()

    # Aguarda 5 segundos e fecha o jogo
    pygame.time.wait(5000)
    pygame.quit()
    sys.exit()


# Inicialização
data = client.recv(4096)
initial_data = pickle.loads(data)
player_id = initial_data["player_id"]
state = initial_data["state"]

game_loop()
