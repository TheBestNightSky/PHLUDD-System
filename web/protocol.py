from Crypto.Cipher import PKCS1_OAEP as Cipher
import time

#header message byte structure Constants
HEADER_TYPE = 2
HEADER_ID = 16
HEADER_AUTH = 16
HEADER_DATA = 32

HEADER_SIZE = HEADER_TYPE + HEADER_ID + HEADER_AUTH + HEADER_DATA

#header type Constants
HTYPE_DISCONNECT = 0
HTYPE_PING = 1
HTYPE_ALERT = 101 #May be sent by server at anytime
HTYPE_ACKNOWLEDGE = 200
HTYPE_AUTHORIZE = 299
HTYPE_COMMAND = 300
HTYPE_JSON = 301
HTYPE_ERROR = 400
HTYPE_ACCESS_DENIED = 401
HTYPE_HS_REQUEST_CERT = 504
HTYPE_HS_KEYTRADE = 505
HTYPE_HS_CONFIRM = 506
HTYPE_HS_ACCESS_DENIED = 507
HTYPE_SERIAL_MESSAGE = 600

#MiscCosntants
SOCKET_TIMEOUT = 10
FORMAT = 'utf-8'
DISCONNECT = "!DISCONNECT"
IDENT = b"PHLUDD"
BCAST_SIZE = len(IDENT) + 6

## common functions for encoding/decoding headers
def uuid_encode(uuid):
    string = "".join(uuid.split("-"))
    encode = bytes.fromhex(string)
    return encode

def uuid_decode(uuid_bytes : bytes):
    hex_string = uuid_bytes.hex()
    hex_seg = [hex_string[0:8], hex_string[8:12], hex_string[12:16], hex_string[16:20], hex_string[20:]]
    return "-".join(hex_seg)

def server_broadcast_encode(host_ip : str, port : int):
    ip_data = [int(i) for i in host_ip.split(".")]
    data = b""
    data += IDENT
    for num in ip_data:
        data += num.to_bytes(1, "big", signed=False)

    data += port.to_bytes(2, "big", signed=False)

    return data

def server_broadcast_decode(data : bytes):
    ident_data = data[0:len(IDENT)]
    ip_data = data[len(IDENT): len(IDENT) + 4]
    port_data = data[len(IDENT) + 4:]
    ip = ""
    port = int.from_bytes(port_data, "big")
    for byte in ip_data:
        ip += str(byte) + "."
    ip = ip[:-1]

    return (ident_data, ip, port)

def create_header(ctype : int, id : str, auth : str, data : int):
    padded = (" " * (HEADER_ID - len(id))) + id
    type_bytes = ctype.to_bytes(HEADER_TYPE, "big", signed=False)
    id_bytes = bytes.fromhex("".join(["{:02x}".format(ord(char)) for char in padded]))
    auth_bytes = uuid_encode(auth)
    data_bytes = data.to_bytes(HEADER_DATA, "big", signed=False)

    header = bytearray(type_bytes + id_bytes + auth_bytes + data_bytes)
    return header

def header_decode(header):
    type_bytes = header[0 : HEADER_TYPE]
    id_bytes = header[HEADER_TYPE : HEADER_TYPE + HEADER_ID]
    auth_bytes = header[HEADER_TYPE + HEADER_ID : HEADER_TYPE + HEADER_ID + HEADER_AUTH]
    data_bytes = header[HEADER_TYPE + HEADER_ID + HEADER_AUTH : HEADER_SIZE]
    return {
        "type": int.from_bytes(type_bytes, "big"),
        "id": id_bytes.decode(FORMAT).strip(),
        "auth": uuid_decode(auth_bytes),
        "data": int.from_bytes(data_bytes, "big")
        }

def send_message(connection, header_data:tuple, message):
    header_type, user_id, user_auth = header_data
    if type(message) == str:
        msg = message.encode(FORMAT)
    elif type(message) == bytes:
        msg = message

    header = create_header(header_type, user_id, user_auth, len(msg))

    connection.send(header)
    connection.send(msg)

def recv_message(connection):
    header = connection.recv(HEADER_SIZE)
    if header:
        header = header_decode(header)
        msg = connection.recv(header["data"])

        return {"header": header, "message": msg}


def ping(connection, auth: tuple): #used by client
    header_type, user_id, user_auth = HTYPE_PING, *auth
    message = "PING".encode(FORMAT)
    header = create_header(header_type, user_id, user_auth, len(message))
    connection.send(header)
    connection.send(message)


def pong(connection, auth: tuple): #used by server to respond
    header_type, user_id, user_auth = HTYPE_PING, *auth
    message = "PONG".encode(FORMAT)
    header = create_header(header_type, user_id, user_auth, len(message))
    connection.send(header)
    connection.send(message)

def send_encrypted_message(connection, header_data:tuple, cryptKey, message:str or bytes):
    header_type, user_id, user_auth = header_data
    if type(message) == str:
        buffer = message.encode(FORMAT)
    elif type(message) == bytes:
        buffer = message
    msg_list = []

    max_size = (cryptKey.size_in_bytes() - 2) - 40
    for i in range(0, len(buffer), max_size):
        msg_list.append(buffer[i : i + max_size])
    
    if len(msg_list) > 1:
        msg = str(len(msg_list)).encode(FORMAT)
        header = create_header(HTYPE_SERIAL_MESSAGE, user_id, user_auth, len(msg))
        connection.send(header)
        connection.send(msg)

    for i in msg_list:
        msg = i
        msg = Cipher.new(cryptKey).encrypt(msg)
        header = create_header(header_type, user_id, user_auth, len(msg))
        connection.send(header)
        connection.send(msg)

def recv_encrypted_message(connection, cryptKey):
    header = connection.recv(HEADER_SIZE)
    if header:
        header = header_decode(header)
        msg = connection.recv(header["data"])

        try:
            if header["type"] == HTYPE_SERIAL_MESSAGE:
                blocks = int(msg.decode(FORMAT))
                data = b""
        
                for i in range(0, blocks):
                    header = connection.recv(HEADER_SIZE)
                    header = header_decode(header)

                    msg = connection.recv(header["data"])
                    dmsg = Cipher.new(cryptKey).decrypt(msg)
                    data += dmsg

                return {"header" : header, "message" : data}

            else:
                dmsg = Cipher.new(cryptKey).decrypt(msg)
                return {"header" : header, "message" : dmsg}
        
        except ValueError:
            return {"header": header, "message" : msg}