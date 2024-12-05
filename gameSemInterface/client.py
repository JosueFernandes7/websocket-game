import socket

HOST = "127.0.0.1"  # IP do servidor
PORT = 65432        # Porta do servidor

def start_client():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            print("Conectado ao servidor!")

            while True:
                server_message = receive_message(client_socket)
                if not server_message:
                    print("Conexão com o servidor perdida.")
                    break
                print(server_message)

                if requires_input(server_message):
                    user_input = input("> ")
                    send_message(client_socket, user_input)

                if game_over(server_message):
                    break
    except ConnectionError:
        print("Não foi possível conectar ao servidor.")

def receive_message(sock: socket.socket) -> str:
    try:
        return sock.recv(1024).decode()
    except socket.error:
        return ''

def send_message(sock: socket.socket, message: str):
    sock.sendall(message.encode())

def requires_input(message: str) -> bool:
    prompts = [
        "Seu turno! Adivinhe uma letra ou a palavra:",
        "Digite sua palavra secreta:",
        "Bem-vindo! Digite seu nome:"
    ]
    return any(prompt in message for prompt in prompts)

def game_over(message: str) -> bool:
    return "Parabéns, Você venceu!" in message or "Você perdeu" in message

if __name__ == "__main__":
    start_client()
