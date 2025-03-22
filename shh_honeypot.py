#Libraries
import logging
from logging.handlers import RotatingFileHandler
import socket
import paramiko

# Constants
logging_format = logging.Formatter('%(message)s')

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
                response = b'\n' + b'\\usr\local\\' + b'\r\n'
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
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    def check_channel_exec_request(self, kind: str, chanid: int) -> int:
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        
        #return paramiko.OPEN_FAILED
        
    def get_allowed_auths(self):  #With SSH you can use basic auth with user and pass, public and private key criptography 
        return 'password'
    
    def check_auth_password(self, username, password):  #Can be improved using args to capture user input
        if self.input_username is not None and self.input_password is not None:
            if username == 'username' and password == 'password':
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED
    
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
    
    def check_channel_exec_request(seld, channel, command):
        command = str(command)
        return True

            

# Provision SSH-based Honeypot
