import socket
import threading
import pickle

# Configuração do servidor
HOST = '127.0.0.1'
PORT = 5555

# Estado inicial do jogo
GRID_SIZE = 5
state = {
    "horizontal_lines": [[False] * (GRID_SIZE - 1) for _ in range(GRID_SIZE)],
    "vertical_lines": [[False] * GRID_SIZE for _ in range(GRID_SIZE - 1)],
    "boxes": [[None] * (GRID_SIZE - 1) for _ in range(GRID_SIZE - 1)],
    "scores": [0, 0],
    "player_turn": 1,
    "game_over": False,
}

clients = []

# Função para verificar e completar caixas
def check_boxes():
    completed_box = False
    for r in range(GRID_SIZE - 1):
        for c in range(GRID_SIZE - 1):
            if state["boxes"][r][c] is None:
                if (state["horizontal_lines"][r][c] and state["horizontal_lines"][r + 1][c] and
                    state["vertical_lines"][r][c] and state["vertical_lines"][r][c + 1]):
                    state["boxes"][r][c] = state["player_turn"]
                    state["scores"][state["player_turn"] - 1] += 1
                    completed_box = True
    return completed_box

# Envia o estado atualizado para todos os clientes
def broadcast_state():
    data = pickle.dumps(state)
    for client in clients:
        client.sendall(data)

# Lida com cada cliente
def handle_client(client, player_id):
    global state
    client.sendall(pickle.dumps({"player_id": player_id, "state": state}))  # Envia estado inicial

    while True:
        try:
            # Recebe jogada do cliente
            data = client.recv(1024)
            move = pickle.loads(data)

            if state["player_turn"] == player_id:
                line_type, row, col = move["line_type"], move["row"], move["col"]

                # Atualiza o estado
                if line_type == "horizontal":
                    state["horizontal_lines"][row][col] = player_id
                elif line_type == "vertical":
                    state["vertical_lines"][row][col] = player_id

                # Verifica caixas completadas
                if not check_boxes():
                    state["player_turn"] = 3 - player_id  # Alterna o turno

                # Verifica fim de jogo
                if all(all(box is not None for box in row) for row in state["boxes"]):
                    state["game_over"] = is_game_over(state)

                # Atualiza todos os clientes
                broadcast_state()
        except:
            print(f"Jogador {player_id} desconectado.")
            clients.remove(client)
            break

def is_game_over(state):
    for row in state["boxes"]:
        if None in row:
            return False
    return True

# Configuração principal do servidor
def main():
    global clients
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(2)
    print("Servidor aguardando conexões...")

    player_id = 1
    while len(clients) < 2:
        client, addr = server.accept()
        print(f"Jogador {player_id} conectado: {addr}")
        clients.append(client)
        threading.Thread(target=handle_client, args=(client, player_id)).start()
        player_id += 1

    print("Dois jogadores conectados. Jogo iniciado.")

if __name__ == "__main__":
    main()
