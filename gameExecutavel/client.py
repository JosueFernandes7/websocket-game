import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

HOST = "127.0.0.1"  # IP do servidor
PORT = 65432        # Porta do servidor

class ClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Cliente do Jogo")
        self.master.resizable(False, False)

        self.create_widgets()
        self.client_socket = None
        self.connected = False

        # Inicia a conexão com o servidor
        self.start_client()

    def create_widgets(self):
        # Área de exibição de mensagens
        self.text_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, state='disabled', width=60, height=20)
        self.text_area.grid(row=0, column=0, padx=10, pady=10, columnspan=3)

        # Campo de entrada de texto
        self.input_field = tk.Entry(self.master, width=50)
        self.input_field.grid(row=1, column=0, padx=10, pady=5)

        # Botão de enviar
        self.send_button = tk.Button(self.master, text="Enviar", command=self.send_input)
        self.send_button.grid(row=1, column=1, padx=5, pady=5)

        # Botão de jogar novamente
        self.restart_button = tk.Button(self.master, text="Jogar Novamente", command=self.restart_game)
        self.restart_button.grid(row=1, column=2, padx=5, pady=5)

        # Desabilita o campo de entrada e o botão até a conexão ser estabelecida
        self.input_field.config(state='disabled')
        self.send_button.config(state='disabled')
        self.restart_button.config(state='disabled')

    def start_client(self):
        self.append_message("Conectando ao servidor...")
        threading.Thread(target=self.connect_to_server, daemon=True).start()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            self.connected = True
            self.append_message("Conectado ao servidor!")

            # Habilita o campo de entrada e o botão enviar
            self.input_field.config(state='normal')
            self.send_button.config(state='normal')

            # Inicia a thread para receber mensagens
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except ConnectionError:
            self.append_message("Não foi possível conectar ao servidor.")
            self.connected = False
            self.restart_button.config(state='normal')

    def receive_messages(self):
        try:
            while self.connected:
                server_message = self.client_socket.recv(1024).decode()
                if not server_message:
                    self.append_message("Conexão com o servidor perdida.")
                    break
                self.append_message(server_message)

                if self.requires_input(server_message):
                    # Habilita o campo de entrada e o botão enviar
                    self.input_field.config(state='normal')
                    self.send_button.config(state='normal')
                else:
                    # Desabilita o campo de entrada e o botão enviar
                    self.input_field.config(state='disabled')
                    self.send_button.config(state='disabled')

                if self.game_over(server_message):
                    self.connected = False
                    self.client_socket.close()
                    self.restart_button.config(state='normal')
                    messagebox.showinfo("Fim de Jogo", server_message)
                    break
        except Exception as e:
            self.append_message(f"Erro: {e}")
            self.connected = False
            self.restart_button.config(state='normal')

    def send_input(self):
        user_input = self.input_field.get()
        if user_input and self.connected:
            try:
                self.client_socket.sendall(user_input.encode())
                self.input_field.delete(0, tk.END)
                self.input_field.config(state='disabled')
                self.send_button.config(state='disabled')
            except Exception as e:
                self.append_message(f"Erro ao enviar mensagem: {e}")
                self.connected = False
                self.restart_button.config(state='normal')

    def append_message(self, message):
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.see(tk.END)
        self.text_area.config(state='disabled')

    def requires_input(self, message):
        prompts = [
            "Seu turno! Adivinhe uma letra ou a palavra:",
            "Digite sua palavra secreta:",
            "Bem-vindo! Digite seu nome:"
        ]
        return any(prompt in message for prompt in prompts)

    def game_over(self, message):
        return "Parabéns, Você venceu!" in message or "Você perdeu" in message

    def restart_game(self):
        # Fecha a conexão atual se ainda estiver aberta
        if self.connected:
            try:
                self.client_socket.close()
            except:
                pass
            self.connected = False

        # Limpa a área de texto
        self.text_area.config(state='normal')
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state='disabled')

        # Desabilita os botões enviar e jogar novamente até reconectar
        self.input_field.config(state='disabled')
        self.send_button.config(state='disabled')
        self.restart_button.config(state='disabled')

        # Reinicia a conexão com o servidor
        self.start_client()

def main():
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
