from .util import vlq_pack, vlq_unpack

USB_HEARTBEAT   = 5
USB_MESSAGES    = 255

class Terminal64:
    def __init__(self, cartridge):
        self.cart = cartridge
        self.cart.recv_usb_pkt = self.recv_usb_pkt
        self.message_buffer = bytearray()
        self.usb_pkt_handlers = {
            USB_MESSAGES: self.handle_usb_messages,
        }

    def recv_usb_pkt(self, packet_type, data):
        handler = self.usb_pkt_handlers.get(packet_type, lambda _: None)
        handler(data)

    def handle_usb_messages(self, data):
        while data:
            message_type, length = vlq_unpack(data)
            del data[:length]
            message_length, length = vlq_unpack(data)
            del data[:length]
            message_data = data[:message_length]
            self.handle_usb_message(message_type, message_data)
            del data[:message_length]

    def queue_usb_message(self, message_type, data=b''):
        message_header = vlq_pack(message_type) + vlq_pack(len(data))
        self.message_buffer.extend(message_header + data)

    def send_usb_messages(self):
        self.cart.send_usb_cmd(USB_MESSAGES, self.message_buffer)
        self.message_buffer = bytearray()

    """User function expected to be monkey patched"""
    def handle_usb_message(self, message_type, data):
        pass
