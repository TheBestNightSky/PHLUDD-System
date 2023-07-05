from email.headerregistry import Address
from genericpath import isfile
import socket
import threading
import json
import sqlite3
import os
import uuid
import requests
import textwrap
import time

import hashlib
from getpass import getpass
from base64 import b64encode
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15 as signature
from Crypto.Hash import SHA512
from Crypto.Protocol.KDF import bcrypt, bcrypt_check
from Crypto.Random import new as Random
from Crypto.Random import get_random_bytes

from web.protocol import *

import lib.logging as Logging

Log = Logging.Log("logs/phludd_log.log")
#server constants
PORT = 5050

guest_id = "guestname"
guest_auth = "12345678-1234-1234-1234-123456789012"

server_id = "server"
server_auth = "99999999-9999-9999-9999-999999999999"

LOGIN_DB = "credentials/user.db"

class ThreadSafe:
    class list:
        def __init__(self):
            self._list = list()
            self._lock = threading.Lock()

        def append(self, val):
            self._list.append(val)

        def remove(self, val):
            with self._lock:
                self._list.remove(val)

        def length(self):
            with self._lock:
                return len(self._list)

        def get(self, index):
            with self._lock:
                return self._list[index]

        def set(self, index, val):
            with self._lock:
                self._list[index] = val

        def find(self, val):
            with self._lock:
                return self._list.index(val)

        def __iter__(self):
            with self._lock:
                return self._list.__iter__()

    print_lock = threading.Lock()
    def print(*args, **kwargs):
        with ThreadSafe.print_lock:
            print(*args, **kwargs)

ConnectionList = ThreadSafe.list()
Authorized_IDs = ThreadSafe.list()

class Command:

    class Error:
        def __init__(self, string:str):
            self.error = string

    clist = ThreadSafe.list()
    cmap = ThreadSafe.list()
    help_list = ThreadSafe.list()

    def register(command, access_level, callback, help_usage="TO_DO", help_description="TO_DO"):
        Command.clist.append(command)
        Command.cmap.append((callback, access_level))
        Command.help_list.append({"usage" : help_usage, "description" : help_description})

    def call(command, session, *args):
        try:
            access_level = session[2]
            idx = Command.clist.find(command)
            cmd = Command.cmap.get(idx)
            if cmd[1] <= access_level:
                res = cmd[0](*args)
                if res is not None:
                    return res
                else:
                    return "Success"
            else:
                Log.log(Log.WARNING, f"client ({session[0]}) tried to run a command they lack permissions for!")
                return Command.Error("Client lacks permission to run this command!")

        except ValueError as e:
            Log.log(Log.WARNING, f"[Warning] client ({session[0]}) sent an invalid command!")
            return Command.Error("Client sent an invalid command!")

        except TypeError as e:
            Log.log(Log.WARNING, f"client ({session[0]}) sent a valid command but the arguments did not match!")
            Log.log(Log.ERROR, e)
            return Command.Error("Client sent a valid command but the arguments did not match!")

#### BUILT IN COMMAND DEFINITIONS ####

## HELP COMMAND ##
usage = "help <*command>"
description = "Displays the description and usage of available commands, if command argument is given will only show help for that specific command."

def cmd_help(command=None):
    string = "---HELP---\nNote: *Astrix mean optional\n\n"
    tab = "    "
    if command is None:
        for i in range(0, Command.clist.length()):
            string += tab + Command.clist.get(i) + " | example: " + Command.help_list.get(i)["usage"] + "\n"
            string += tab*2 + ("\n" + tab*2).join(textwrap.wrap(Command.help_list.get(i)["description"], 70)) + "\n\n"
    else:
        try:
            idx = Command.clist.find(command)
            string += tab + Command.clist.get(idx) + " | example: " + Command.help_list.get(idx)["usage"] + "\n"
            string += tab*2 + ("\n" + tab*2).join(textwrap.wrap(Command.help_list.get(idx)["description"], 70)) + "\n\n"

        except ValueError:
            return Command.Error("help <*command>: Command not found!")

    string += "---END HELP---"
    Log.log(Log.INFO, string)
    return string

Command.register("help", 0, cmd_help, usage, description)

## ECHO COMMAND ##
usage = "echo <string>"
description = "Prints the given string to the server console :D"

def testCmd(*string):
    text = " ".join(string)
    Log.log(Log.ECHO, text)
    return f"[ECHO] {text}"

Command.register("echo", 0, testCmd, usage, description)

## CREATE ACCOUND COMMAND ##
usage = "createAccount <username> <email> <password> <access_level>"
description = "Creates a new account with information provided (ADMIN LEVEL COMMAND)"

def create_account(username, email, password, access_level):
    Log.log(Log.INFO, f"Creating account ({username}) with access level {access_level}")
    Log.log(Log.INFO, "Connecting to database...")
    conn = sqlite3.connect(LOGIN_DB)
    cur = conn.cursor()

    Log.log(Log.INFO, "Checking if account already exists...")
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    res = cur.fetchone()
    if res is None:
        Log.log(Log.INFO, "Generating salt...")
        salt = get_random_bytes(16)
        Log.log(Log.INFO, "Calculating password hash...")
        pwhash = b64encode(hashlib.sha256(password.encode(FORMAT)).digest())
        bcrypt_hash = bcrypt(pwhash, 15, salt=salt)

        #load forum data into database
        Log.log(Log.INFO, "Inserting data into database...")
        cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, ?)", (access_level, username, email, bcrypt_hash))

        Log.log(Log.INFO, "Commiting changes to database!")
        conn.commit()
        Log.log(Log.INFO, f"Account ({username}) created succesfully!")
        return f"[INFO] Account ({username}) created succesfully!"
    else:
        Log.log(Log.WARNING, f"Account ({username}) Already exists!")
        return Command.Error(f"Account ({username}) Already exists!")

Command.register("createAccount", 10, create_account, usage, description)

## DELETE ACCOUNT COMMAND ##
usage = "deleteAccount <username> <password>"
description = "Deletes the specified account from the login database if the password matches"
def delete_account(username, password):
    Log.log(Log.INFO, f"Attempting to delete account ({username})")
    Log.log(Log.INFO, f"Connecting to database...")
    conn = sqlite3.connect(LOGIN_DB)
    cur = conn.cursor()
    Log.log(Log.INFO, f"Searching for user ({username})")
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    res = cur.fetchone()
    try:
        if res is not None:
            id, access_level, username, email, psw = res
            Log.log(Log.INFO, f"Validating password...")
            pwhash = b64encode(hashlib.sha256(password.encode(FORMAT)).digest())
            bcrypt_check(pwhash, psw) #raises an error if result dosnt match

            Log.log(Log.INFO, f"Password verified, Deleting user ({username})")
            cur.execute("DELETE FROM users WHERE username=?", (username,))

            Log.log(Log.INFO, "Commiting changes to database!")
            conn.commit()
            Log.log(Log.INFO, f"Account ({username}) deleted succesfully!")
            return f"[INFO] Account ({username}) deleted succesfully!"


    except ValueError:
        Log.log(Log.WARNING, f"Failed to verify password for account deletion!")
        return Command.Error("Failed to verify password for account deletion!")

Command.register("deleteAccount", 1, delete_account, usage, description)

#### END BUILT IN COMMAND DEFINITIONS ####

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def create_login_db():
    if not os.path.isfile(LOGIN_DB):
        Log.log(Log.WARNING, "User database missing, creating new database...")
        conn = sqlite3.connect(LOGIN_DB)
        cur = conn.cursor()
        Log.log(Log.INFO, f"Created database at {LOGIN_DB}")

        Log.log(Log.INFO, "Creating new table users...")
        cur.execute("""CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            access_level INTEGER NOT NULL,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
            )""")

        Log.log(Log.INFO, "Please create the first admin level user")
        access_level = 10
        username = Log.input("[INPUT] please enter the admin username:\n")

        email = ''
        while True:
            email = Log.input("[INPUT] please enter an email to use for this account:\n")
            email_verify = Log.input("[INPUT] enter the same email again to verify:\n")
            if email == email_verify:
                break
            Log.log(Log.NOTICE, "Emails did not match, please try again!")

        password = ''
        while True:
            password = Log.getpass("[INPUT] enter the password to use for this account:\n")
            pass_verify = Log.getpass("[INPUT] enter the password again:\n")
            if password == pass_verify:
                break
            Log.log(Log.NOTICE, "Passwords did not match, please try again!")

        Log.log(Log.INFO, "Generating salt...")
        salt = get_random_bytes(16)
        Log.log(Log.INFO, "Calculating password hash...")
        pwhash = b64encode(hashlib.sha256(password.encode(FORMAT)).digest())
        bcrypt_hash = bcrypt(pwhash, 15, salt=salt)

        #load forum data into database
        Log.log(Log.INFO, "Inserting data into database...")
        cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, ?)", (access_level, username, email, bcrypt_hash))

        Log.log(Log.INFO, "Commiting changes to database!")
        conn.commit()


def client_handshake(connection, address):
    global ConnectionList
    client_public = ""
    server_side_complete = False
    secure = False
    Log.log(Log.INFO, f"({address}) Attempting to connect, begining handshake!")
    try:
        while not secure:
            packed = recv_message(connection) if not server_side_complete else recv_encrypted_message(connection, RSAkey)
            if packed:
                header, msg = packed.values()
                
                if header["type"] == HTYPE_HS_REQUEST_CERT:
                    with open("credentials/sig.cert", "rb") as file:
                        message = file.read()
                        send_message(connection, (HTYPE_HS_REQUEST_CERT, server_id, server_auth), message)

                #recieve public key from client
                elif header["type"] == HTYPE_HS_KEYTRADE:
                    split = msg.split(b":")
                    pdata = split[0] + str(HEADER_TYPE).encode(FORMAT) + str(HEADER_ID).encode(FORMAT) + str(HEADER_AUTH).encode(FORMAT) + str(HEADER_DATA).encode(FORMAT) + str(HEADER_SIZE).encode(FORMAT)
                    phash = hashlib.sha512(pdata).hexdigest()
                    if phash == split[1].decode(FORMAT):
                        client_public = RSA.importKey(split[0])

                        message = public + b"\n--SIGNATURE--\n" + sig
                        send_encrypted_message(connection, (HTYPE_HS_KEYTRADE, server_id, server_auth), client_public, message)
                        server_side_complete = True
                    else:
                       break

                elif header["type"] == HTYPE_HS_CONFIRM and server_side_complete:
                    if msg.decode(FORMAT) == "Confirm Handshake":
                        Log.log(Log.INFO, f"({address}) Hand shake successfull! client connection is now secure.")
                        secure = True

        if secure:
            idx = ConnectionList.find((connection, address))
            ConnectionList.set(idx, (connection, address, client_public) )
            handle_client(connection, address, client_public)
        else:
            Log.log(Log.SECURITY, f"({address}) Hand shake failed! Aborting client connection")
            message = "Access Denied!"
            send_encrypted_message(connection, (HTYPE_HS_ACCESS_DENIED, server_id, server_auth), client_public, message)
            connection.close()
            ConnectionList.remove((connection, address))
    
    except ConnectionResetError as e:
        Log.log(Log.WARNING, f"({address}) Diconnected without warning. (Client Connection Reset)")
        ConnectionList.remove((connection, address))

    except socket.timeout as e:
        Log.log(Log.WARNING, f"({address}) Diconnected without warning. (Client Timed Out)")
        ConnectionList.remove((connection, address))


def handle_client(connection, address, client_key):
    global running
    connected = True
    session = (guest_id, guest_auth, 0)
    last_json = ""
    try:
        while connected and running:
            packed = recv_encrypted_message(connection, RSAkey)
            if packed:
                header, dmsg = packed.values()

                if header["type"] == HTYPE_DISCONNECT and dmsg.decode(FORMAT) == DISCONNECT:
                    Log.log(Log.INFO, f"({address}) Diconnected")
                    connected = False
                    ConnectionList.remove((connection, address, client_key))

                elif header["type"] == HTYPE_PING:
                    if dmsg.decode(FORMAT) == "PING":
                        pong(connection, (server_id, server_auth))
                    elif dmsg.decode(FORMAT) == "PONG":
                        pass

                elif header["type"] == HTYPE_COMMAND:
                    Log.log(Log.INFO, f"Client ({address} | {session[0]}) has sent a command, ({dmsg.decode(FORMAT)}) attempting to execute...")
                    split = dmsg.decode(FORMAT).split(" ")
                    cmd = split[0]
                    args = split[1:]
                    res = Command.call(cmd, session, *args)

                    if type(res) == Command.Error:
                        send_encrypted_message(connection, (HTYPE_ERROR, server_id, server_auth), client_key, res.error)
                    else:
                        send_encrypted_message(connection, (HTYPE_COMMAND, server_id, server_auth), client_key, str(res))

                elif header["type"] == HTYPE_JSON:
                    Log.log(Log.INFO, f"({address}) client has sent a json object, saving and waiting for further instruction...")
                    last_json = json.loads(dmsg)

                elif header["type"] == HTYPE_AUTHORIZE:
                    conn = None
                    split = dmsg.split(b":")
                    usr = split[0].decode(FORMAT)
                    psw = split[1]
                    try:
                        conn = sqlite3.connect(LOGIN_DB)
                        cur = conn.cursor()
                        
                        cur.execute("SELECT * FROM users WHERE username=?", (usr,))
                        res = cur.fetchone()
                        if res is not None:
                            id, access_level, username, email, password = res

                            pwhash = b64encode(hashlib.sha256(psw).digest())
                            bcrypt_check(pwhash, password) #raises an error if result dosnt match

                            session_uuid = str(uuid.uuid4())
                            session = (username, session_uuid, access_level)
                            Authorized_IDs.append(session)

                            message = username.encode(FORMAT) + b":" + uuid_encode(session_uuid)
                            send_encrypted_message(connection, (HTYPE_AUTHORIZE, server_id, server_auth), client_key, message)
                        else:
                            Log.log(Log.SECURITY, f"({address}) Login attempted with invalid username!")
                            message = "Access Denied!"
                            send_encrypted_message(connection, (HTYPE_ACCESS_DENIED, server_id, server_auth), client_key, message)

                    except ValueError as e:
                        Log.log(Log.SECURITY, f"({address}) Login attempted with invalid password")
                        message = "Access Denied!"
                        send_encrypted_message(connection, (HTYPE_ACCESS_DENIED, server_id, server_auth), client_key, message)
                            

        connection.close()

    except ConnectionResetError as e:
        connected = False
        Log.log(Log.WARNING, f"({address}) Diconnected without warning. (Client Connection Reset)")
        ConnectionList.remove((connection, address, client_key))
        try:
            Authorized_IDs.remove(session)
        except ValueError:
            pass

    except socket.timeout as e:
        connected = False
        Log.log(Log.WARNING, f"({address}) Diconnected without warning. (Client Timed Out)")
        ConnectionList.remove((connection, address, client_key))
        try:
            Authorized_IDs.remove(session)
        except ValueError:
            pass

def broadcast_service(ADDRESS):
    global running
    host, port = ADDRESS
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server.settimeout(180)

    msg = server_broadcast_encode(host, port)
    Log.log(Log.INFO, "Starting host location broadcast")
    while running:
        server.sendto(msg, ("255.255.255.255", 5595))
        time.sleep(1.5)

    server.close()
    Log.log(Log.INFO, "Host location broadcast stopped ")

def server_start():
    global running
    global sig
    global RSAkey
    global public
    global ConnectionList
    global Authorized_IDs

    #Socket server
    Log.log(Log.INFO, "Server verifying network connectivity...")
    network = False
    while not network:
        try:
            HOST_EXTERNAL = requests.get('https://api.ipify.org').content.decode('utf8')
            network = True
        except requests.exceptions.ConnectionError as e:
            time.sleep(1)
            continue

    HOST = get_local_ip()
    ADDRESS = (HOST, PORT)

    #crypto
    random = Random().read
    if not os.path.isfile('credentials/sig.key'):
        RSAsig = RSA.generate(2048, random)
        sig_private = RSAsig.exportKey()
        sig_public = RSAsig.publickey().exportKey()
        with open('credentials/sig.key', 'wb') as file:
            file.write(sig_private)
            file.close()

        with open('credentials/sig.cert', 'wb') as file:
            cert = {"public_key": sig_public.decode(FORMAT), "valid_adress": [HOST, HOST_EXTERNAL]}
            data = json.dumps(cert, sort_keys=True, indent=4).encode(FORMAT)
            dhash = SHA512.new()
            dhash.update(data)
            sig = signature.new(RSAsig)
            data += b"\n--SIGNATURE--\n" + sig.sign(dhash)
            file.write(data)
            file.close()

    RSAkey = RSA.generate(1024, random)
    public = RSAkey.publickey().exportKey()

    with open("credentials/sig.key", 'rb') as file:
        pub_data = public + str(HEADER_TYPE).encode(FORMAT) + str(HEADER_ID).encode(FORMAT) + str(HEADER_AUTH).encode(FORMAT) + str(HEADER_DATA).encode(FORMAT) + str(HEADER_SIZE).encode(FORMAT)
        public_hash = SHA512.new()
        public_hash.update(pub_data)
        key = RSA.importKey(file.read())

        sig = signature.new(key).sign(public_hash)

    private = RSAkey.exportKey()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.settimeout(SOCKET_TIMEOUT)
    server.bind(ADDRESS)
    server.listen()
    Log.log(Log.INFO, f"Server is now listening on port {PORT} at {HOST}")

    bcast_thread = threading.Thread(target=broadcast_service, args=(ADDRESS,))
    bcast_thread.start()
    while running:
        try:
            conn, addr = server.accept()
            conn.settimeout(SOCKET_TIMEOUT)
            ConnectionList.append((conn, addr))
            thread = threading.Thread(target=client_handshake, args=(conn, addr), daemon=True)
            thread.start()
            Log.log(Log.INFO, f"(ACTIVE SERVER CONNECTIONS) {ConnectionList.length()}")
        except socket.timeout:
            pass

def server_stop():
    Log.log(Log.INFO, f"Stopping server...")
    global running
    for i in ConnectionList:
        if len(i) == 3:
            conn, addr, key = i
        elif len(i) == 2:
            conn, addr = i
        send_message(conn, (HTYPE_DISCONNECT, server_id, server_auth), "Server shutting down")

    running = False
    time.sleep(5)

def alert_all(message):
    for i in ConnectionList:
        if len(i) == 3:
            conn, addr, key = i
            Log.log(Log.INFO, f"Server sending alert to {addr}")
            send_encrypted_message(conn, (HTYPE_ALERT, server_id, server_auth), key, message)

create_login_db()
Log.log(Log.INFO, f"Starting server on port {PORT}...")
running = True
thread = threading.Thread(target=server_start, daemon=True)
thread.start()