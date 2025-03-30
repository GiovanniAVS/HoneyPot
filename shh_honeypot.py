#Libraries
import logging
from logging.handlers import RotatingFileHandler
import socket
import paramiko
import threading

# Constants
logging_format = logging.Formatter('%(message)s')
SSH_BANNER = "SSH-2.0-MySSHServer_1.0"
#host_key = 'server.key'
host_key = paramiko.RSAKey(filename='server.key')

# Loggers & Logging Files
funnel_logger = logging.getLogger('FunnelLogger')
funnel_logger.setLevel(logging.INFO)
funnel_handler = RotatingFileHandler('audits.log', maxBytes=2000, backupCount=5)
funnel_handler.setFormatter(logging_format)
funnel_logger.addHandler(funnel_handler)

creds_logger = logging.getLogger('FunnelLogger')
creds_logger.setLevel(logging.INFO)
creds_handler = RotatingFileHandler('cmd_audits.log', maxBytes=2000, backupCount=5)
creds_handler.setFormatter(logging_format)
creds_logger.addHandler(creds_handler)

# Emulated Shell
def emulated_shell(channel, client_ip):
    channel.send(b'corporate-jumpbox2$ ')
    command = b""   # Listenning to user input
    while True:
        char = channel.recv(1)
        channel.send(char)
        if not char:
            channel.close()

        command += char

        if char == b'\r':   # Everytime you press ENTER the programm will evaluete this commands
            if command.strip() == b'exit':
                response = b'\n Goodbye!\n'
                channel.close()
            elif command.strip() == b'pwd':
                response = b'\n' + b'\\usr\\local\\' + b'\r\n'
            elif command.strip() == b'whoami':
                response = b'\n' + b'corpuser1' + b'\r\n'
            elif command.strip() == b'ls':
                response = b'\n' + b'jumpbox1.conf' + b'\r\n'
            elif command.strip() == b'cat jumpbox1.conf':
                response = b'\n' + b'Go to Sunday Mass' + b'\r\n'
            # You can continue to add more commands
            else:
                response = b'\n' + bytes(command.strip()) + b'\r\n'
            channel.send(response)
            channel.send(b'corporate-jumpbox2$ ')
            command = b""


# SSH Server + Socket

class Server(paramiko.ServerInterface):

    def __init__(self, client_ip, input_username=None, input_password=None):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    def check_channel_exec_request(self, kind: str, chanid: int) -> int:
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        
        #return paramiko.OPEN_FAILED
        
    def get_allowed_auths(self, username):  #With SSH you can use basic auth with user and pass, public and private key criptography 
        return 'password'
    
    def check_auth_password(self, username, password):  #Can be improved using args to capture user input
        print(f"Login attempt - Username: {username}, Password: {password}")
        if self.input_username is not None and self.input_password is not None:
            if username == self.input_username and password == self.input_password:
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED
        else:
            return paramiko.AUTH_SUCCESSFUL
    
    def check_channel_shell_request(self, channel):
        print("Shell request received")
        self.event.set()
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
    
    def check_channel_exec_request(self, kind: str, chanid: int) -> int:
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED

    
def client_handle(client, addr, username, password):
    client_ip = addr[0]
    print(f'{client_ip} has connected to the server.')

    try:
        transport = paramiko.Transport(client)
        transport.local_version == SSH_BANNER
        server = Server(client_ip=client_ip, input_username=username, input_password=password)

        transport.add_server_key(host_key)
        transport.start_server(server=server)

        channel = transport.accept(100)
        print(f"Channel object: {channel}")
        if channel is None:
            print("No channel was opened.")

        standard_banner = "Welcome to Ubuntu 22.04 LTS (Jammy Jellyfish)!\r\n\r\n"
        channel.send(standard_banner)
        emulated_shell(channel, client_ip=client_ip)
    except Exception as error:
        print("Something went wrong!")
        print(error)
    finally:
        try:
            transport.close()
        except Exception as error:
            print("Something went wrong!")
            print(error)


            

# Provision SSH-based Honeypot

def honeypot(address, port, username, password):
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #Listening to IPV4 using TCP port
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address, port))

    socks.listen(100) # How many connections we can handle
    print(f"SSH server is listening on port {port}.")

    while True:
        try:
            client, addr = socks.accept()
            ssh_honeypot_thread = threading.Thread(target=client_handle, args=(client, addr, username, password))
            ssh_honeypot_thread.start()
        except Exception as error:
            print(error)

honeypot('127.0.0.1', 2223, 'username', 'password')