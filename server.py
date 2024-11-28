import socket
import threading
import pickle
import json
import os

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
    "players": ["", ""]
}

clients = []

# Arquivo para armazenar nicknames e status (simulação de banco de dados)
DB_FILE = "game_data.json"

# Função para carregar ou criar o arquivo JSON
def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    else:
        return {"players": []}  # Estrutura inicial do banco

# Função para salvar dados no JSON
def save_database(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Inicializa ou carrega o banco de dados
database = load_database()

# Envia o estado atualizado para todos os clientes
def broadcast_state():
    data = pickle.dumps(state)
    for client in clients:
        client.sendall(data)

# Lida com cada cliente
def handle_client(client, player_id):
    global state
    try:
        # Recebe e armazena o nickname do cliente
        nickname = client.recv(1024).decode('utf-8')
        print(f"Jogador {player_id} conectado com nickname: {nickname}")

        # Coloca nicks dos players num state 
        state["players"][player_id - 1] = nickname

        # Atualiza o banco de dados com o novo jogador
        database = load_database()
        exists = any(player["nickname"] == nickname for player in database["players"])

        if not exists:
            database["players"].append({"nickname": nickname, "pontuacao": 0})
            save_database(database)

        # Envia o estado inicial do jogo ao cliente
        client.sendall(pickle.dumps({"player_id": player_id, "state": state}))
    except:
        print(f"Erro ao enviar estado inicial para o jogador {player_id}.")
        return

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
                if is_game_over(state):
                    state["game_over"] = True

                # Atualiza todos os clientes
                broadcast_state()
        except:
            print(f"Jogador {player_id} desconectado.")
            if client in clients:  # Verifica se o cliente ainda está na lista
                clients.remove(client)
            break

# Verifica se o jogo acabou e calcula o vencedor
def is_game_over(state):
    database = load_database()
    if all(all(box is not None for box in row) for row in state["boxes"]):
        # Decide o vencedor com base na pontuação
        if state["scores"][0] > state["scores"][1]:
            state["winner"] = 1

            for player in database["players"]:
                if player["nickname"] == state["players"][0]:
                    player["pontuacao"] += 3
            
            save_database(database)

            print("Jogador " + state["players"][0] + " venceu!")
            
        elif state["scores"][1] > state["scores"][0]:
            state["winner"] = 2

            for player in database["players"]:
                if player["nickname"] == state["players"][1]:
                    player["pontuacao"] += 3
            
            save_database(database)

            print("Jogador " + state["players"][1] + " venceu!")
        else:
            state["winner"] = 0  # Empate
            print("O jogo empatou")
        return True
    return False

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

# Configuração principal do servidor com reinício
def main():
    global clients, state

    while True:
        # Resetando o estado e a lista de clientes para reiniciar o jogo
        state = {
            "horizontal_lines": [[False] * (GRID_SIZE - 1) for _ in range(GRID_SIZE)],
            "vertical_lines": [[False] * GRID_SIZE for _ in range(GRID_SIZE - 1)],
            "boxes": [[None] * (GRID_SIZE - 1) for _ in range(GRID_SIZE - 1)],
            "scores": [0, 0],
            "player_turn": 1,
            "game_over": False,
            "players": ["", ""]
        }
        clients = []

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen(2)
        print("Servidor aguardando conexões...")

        player_id = 1
        while len(clients) < 2:
            client, addr = server.accept()
            print(f"Jogador {player_id} conectado de: {addr}")
            clients.append(client)
            threading.Thread(target=handle_client, args=(client, player_id)).start()
            player_id += 1

        print("Dois jogadores conectados. Jogo iniciado.")

        # Aguarde até o jogo terminar
        while not state["game_over"]:
            pass

        print("Jogo terminado. Reiniciando servidor...")

        # Fecha todas as conexões com os clientes
        for client in clients:
            client.close()
        server.close()

if __name__ == "__main__":
    main()
