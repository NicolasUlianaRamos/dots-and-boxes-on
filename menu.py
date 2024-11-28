import pygame
import sys
import json
from client import game_loop  # Substitua pelo nome do arquivo principal, se necessário.

# Configurações do Pygame
pygame.init()
WIDTH, HEIGHT = 600, 650
BUTTON_WIDTH, BUTTON_HEIGHT = 200, 60
FONT = pygame.font.SysFont(None, 40)

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
DARK_GREEN = (0, 100, 0)

# Inicializa a tela
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu Inicial")

# Função para desenhar botões
def draw_button(text, x, y, color, hover_color, mouse_pos):
    button_rect = pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT)
    if button_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, button_rect)
    else:
        pygame.draw.rect(screen, color, button_rect)

    text_surface = FONT.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)
    return button_rect

# Função para mostrar o ranking
def show_ranking():
    try:
        with open("game_data.json", "r") as f:
            data = json.load(f)
        ranking = sorted(data["players"], key=lambda x: x["pontuacao"], reverse=True)
    except FileNotFoundError:
        ranking = []

    while True:
        screen.fill(WHITE)

        # Título
        title = FONT.render("Ranking", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        # Lista de jogadores
        small_font = pygame.font.SysFont(None, 30)
        for i, player in enumerate(ranking[:10]):  # Mostra os 10 primeiros
            rank_text = f"{i + 1}. {player['nickname']} - {player['pontuacao']} pts"
            text_surface = small_font.render(rank_text, True, BLACK)
            screen.blit(text_surface, (50, 80 + i * 30))

        # Botão de voltar
        back_button = draw_button("Voltar", WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT - 100, GREEN, DARK_GREEN, pygame.mouse.get_pos())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return  # Sai do ranking e volta ao menu principal

        pygame.display.flip()

# Função principal do menu
def main_menu():
    while True:
        screen.fill(WHITE)
        mouse_pos = pygame.mouse.get_pos()

        # Botões
        play_button = draw_button("Jogar", WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 - 80, GREEN, DARK_GREEN, mouse_pos)
        ranking_button = draw_button("Ranking", WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 + 20, GREEN, DARK_GREEN, mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    # Inicia o jogo principal
                    game_loop()
                elif ranking_button.collidepoint(event.pos):
                    # Mostra o ranking
                    show_ranking()

        pygame.display.flip()

if __name__ == "__main__":
    main_menu()
