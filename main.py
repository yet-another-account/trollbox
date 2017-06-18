# The set of clients connected to this server. It is used to distribute
# messages.
import multiset
import logging

logging.basicConfig(filename='chat.log',level=logging.INFO,format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

logging.info("started")

clients = {}  #: {websocket: name}
import asyncio
from time import sleep

import websockets

ips = multiset.Multiset()

helpmsg = """
Commands: 
/help - You're looking at it right now.
/me <action> - Third person
/online - List users online"""

@asyncio.coroutine
def client_handler(websocket: websockets.WebSocketServerProtocol, path):
    sleep(0.2)
    yield from websocket.send('Hello from server (build 5)!')
    if ips[websocket.remote_address[0]] > 6:
        sleep(1)
        yield from websocket.send('MAX 6 connections per IP.')
        return
    ips.add(websocket.remote_address[0], 1)
#    logging.info("{} joined ({})".format(name, websocket.remote_address))

    # The first line from the client is the name
    name = (yield from websocket.recv())[:64].replace("\n", "").replace(".", ".\u200b").replace(" ", "")

    if len(name) == 0:
        yield from websocket.send("Sorry, there's server side checking too. Nice try, though!")
        return
    sleep(1)
    logging.info("{} joined ({})".format(name, websocket.remote_address))

    
    
    yield from websocket.send('+ Welcome to the trollbox™, {}!'.format(name))
    yield from websocket.send('+ There are {} other users currently connected.'.format(len(clients)))
    yield from websocket.send('+ Donations (ETH): 0x0d990184334f274e835b73eb3828064cdea91ef9')
    yield from websocket.send('+ Hosted on a Raspberry Pi 3')
    yield from websocket.send('+ Use /help to list commands')
    clients[websocket] = name
    for client, _ in clients.items():
        yield from client.send(name + ' has joined.')
    try:
        # Handle messages from this client
        while True:
            message = yield from websocket.recv()
            sleep(0.075)
            if message is None:
                their_name = clients[websocket]
                del clients[websocket]
#                print('1: Client closed connection {}'.format(websocket))
                for client, _ in clients.items():
                    yield from client.send(their_name + ' has left.')
#                print("decrementing ip counter")
                ips.remove(websocket.remote_address[0], 1)
#                print("remaining from same ip: ", ips[websocket.remote_address[0]])
                logging.info("{} disconnected ({})".format(their_name, websocket.remote_address))
                break

            if len(message) == 0:
                continue

            if len(message) > 1024:
                yield from websocket.send('Sorry, max msg length is 1024!')
                continue

            logging.info('{}: `{}`'.format(name, message))

            if message.startswith("/online"):
                ret = ""
                sleep(0.2)
                for key, val in clients.items():
                    ret += val + ", "
                ret = ret[:-2] + ". "

                yield from websocket.send('{} users online: {}'.format(len(clients), ret))
            elif message.startswith("/help"):
                yield from websocket.send(helpmsg)
            elif message.startswith("/nick"):
                name = message[6:]
                if name == "":
                    continue

                clients[websocket] = name
            else:
                sleep(0.02)
                # Send message to all clients
                for client, _ in clients.items():
                    if message.startswith("/me"):
                        yield from client.send('* {} {}'.format(name, message[4:]))
                    else:
                        yield from client.send('[{}] {}'.format(name, message))
    except:
        their_name = clients[websocket]
        del clients[websocket]
  #      print('2: Client closed connection', websocket)
        for client, _ in clients.items():
            yield from client.send(their_name + ' has left.')
 #       print("decrementing ip couinter")
        ips.remove(websocket.remote_address[0], 1)
#        print("exc remaining from same ip: ", ips[websocket.remote_address[0]])
        logging.info("{} disconnected ({})".format(their_name, websocket.remote_address))


LISTEN_ADDRESS = ('', 1946)

start_server = websockets.serve(client_handler, *LISTEN_ADDRESS)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
