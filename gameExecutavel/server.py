import socket
import threading
import queue
from typing import Tuple

# Configuração do servidor
HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Porta do servidor
clients_queue = queue.Queue()  # Fila de jogadores conectados
queue_lock = threading.Lock()  # Lock para sincronização

class Player:
    def __init__(self, conn: socket.socket, addr: Tuple[str, int]):
        self.conn = conn
        self.addr = addr
        self.name = ''
        self.secret_word = ''
        self.current_state = ''
        self.start_state_sent = False

    def send(self, message: str):
        self.conn.sendall(message.encode())

    def receive(self, buffer_size: int = 1024) -> str:
        return self.conn.recv(buffer_size).decode().strip().upper()

    def close(self):
        self.conn.close()
    
    def __str__(self):
        return f"{self.name} :: {self.addr} :: {self.secret_word}"

def handle_game(player1: Player, player2: Player):
    """
    Função para gerenciar o jogo entre os dois jogadores.
    """
    
    try:
        
        # Inicializa o jogo
        for player in [player1, player2]:
            player.send("Iniciando partida!")

        # Pega o nome dos jogadores
        for player in [player1, player2]:
            player.send("Bem-vindo! Digite seu nome:")
            player.name = player.receive()
        
        # Notifica os jogadores que o jogo está começando
        player1.send(f"O jogo está começando! Seu oponente será {player2.name}.")
        player2.send(f"O jogo está começando! Seu oponente será {player1.name}.")

        # Coleta as palavras secretas de ambos os jogadores
        for player in [player1, player2]:
            player.send("Digite sua palavra secreta:")
            player.secret_word = player.receive()
            player.current_state = "_" * len(player.secret_word)
            player.start_state_sent = False

        # Mensagem de início do jogo no servidor
        print(f"Iniciando o jogo entre:\n{player1.name} e {player2.name}\n{player1}\n{player2}")
        turn = 0  # 0 para o turno do jogador 1, 1 para o jogador 2
        players = [player1, player2]

        while True:
            current_player = players[turn]
            opponent_player = players[1 - turn]

            if not current_player.start_state_sent:
                # Mostrar estado inicial da palavra para o jogador atual
                current_player.send(f"{opponent_player.current_state}")
                current_player.start_state_sent = True

            current_player.send("Seu turno! Adivinhe uma letra ou a palavra:")
            opponent_player.send(f"Aguardando {current_player.name}...")
            guess = current_player.receive()

            if guess == opponent_player.secret_word:
                current_player.send("Parabéns, Você venceu!")
                opponent_player.send(f"{current_player.name} adivinhou sua palavra!")
                opponent_player.send("Você perdeu")
                break
            elif len(guess) == 1 and guess in opponent_player.secret_word:
                opponent_player.current_state = update_state(opponent_player.current_state, opponent_player.secret_word, guess)
                current_player.send(f"Correto! Progresso: {opponent_player.current_state}")
                opponent_player.send(f"{current_player.name} acertou uma letra! Progresso: {opponent_player.current_state}")
                if "_" not in opponent_player.current_state:
                    current_player.send("Parabéns, Você venceu!")
                    opponent_player.send(f"{current_player.name} adivinhou sua palavra!")
                    opponent_player.send("Você perdeu")
                    break
            else:
                current_player.send("Tentativa incorreta.")
                opponent_player.send(f"{current_player.name} perdeu a tentativa.")
                turn = 1 - turn  # Alterna o turno

        # Fecha as conexões
        player1.close()
        player2.close()
        print(f"Jogo entre {player1.name} e {player2.name} acabou.")
    except Exception as e:
        print(f"Erro: {e}")
        player1.close()
        player2.close()
        
def update_state(current_state: str, secret_word: str, guess: str) -> str:
    """
    Atualiza o estado atual da palavra com base no palpite do jogador.
    """
    return ''.join([guess if secret_word[i] == guess else current_state[i] for i in range(len(secret_word))])

def manage_connections():
    """
    Função para gerenciar conexões e atribuir jogos.
    """
    while True:
        with queue_lock:
            if clients_queue.qsize() >= 2:
                player1 = clients_queue.get()
                player2 = clients_queue.get()
                threading.Thread(target=handle_game, args=(player1, player2)).start()

def handle_client(conn: socket.socket, addr: Tuple[str, int]):
    """
    Função para lidar com uma única conexão de cliente.
    """
    print(f"Nova conexão de {addr}")
    player = Player(conn, addr)
    with queue_lock:
        clients_queue.put(player)
        position = clients_queue.qsize()
        if position <= 2:
            player.send("Esperando um outro jogador se conectar...")
        else:
            player.send(f"Você está na posição {position} na fila. Por favor, aguarde.")

def start_server():
    """
    Função principal para iniciar o servidor e aceitar conexões de clientes.
    """
    threading.Thread(target=manage_connections, daemon=True).start()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Servidor ouvindo em {HOST}:{PORT}")
        
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start_server()
