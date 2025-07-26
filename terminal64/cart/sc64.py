import asyncio
from sys import stderr
from serial_asyncio import create_serial_connection

class SummerCart64(asyncio.Protocol):
    def __init__(self):
        self.connected = asyncio.Event()

    def connection_made(self, transport):
        self.transport = transport
        self._buffer = bytearray()
        self._cmd_pending = []
        asyncio.create_task(self.reset())

    def connection_lost(self):
        self.connected.clear()

    def data_received(self, data):
        self._buffer.extend(data)
        while len(self._buffer) > 8:
            pkt_type = self._buffer[0:3]
            if pkt_type not in (b'CMP', b'ERR', b'PKT'):
                asyncio.create_task(self.reset())
                return

            pkt_id = chr(self._buffer[3])
            data_length = int.from_bytes(self._buffer[4:8])
            if len(self._buffer) + 8 < data_length:
                return

            data = self._buffer[8:8 + data_length]
            if pkt_type == b'PKT':
                self.recv_pkt(pkt_id, data)
            elif pkt_type in (b'CMP', b'ERR'):
                for pending in self._cmd_pending:
                    if pending['pkt_id'] == pkt_id:
                        self._cmd_pending.remove(pending)
                        pending['status'] = pkt_type == b'CMP'
                        pending['data'] = data
                        pending['event'].set()
                        break
            del self._buffer[:8 + data_length]

    async def reset(self):
        self._buffer.clear()
        self._cmd_pending.clear()

        count = 0
        self.transport.serial.dtr = True
        while not self.transport.serial.dsr and count < 10:
            await asyncio.sleep(0.01)
            count += 1
        self.transport.serial.dtr = False
        if count == 10:
            return False

        count = 0
        while self.transport.serial.dsr and count < 10:
            await asyncio.sleep(0.01)
            count += 1
        if count == 10:
            return False

        self.connected.set()
        return True

    def recv_pkt(self, pkt_id, data):
        if pkt_id == 'X':
            value = int.from_bytes(data)
            self.recv_aux_pkt(value)
        elif pkt_id == 'B':
            self.recv_button_pkt()
        elif pkt_id == 'U':
            pkt_type = data[0]
            length = int.from_bytes(data[1:4])
            assert(length == len(data) - 4)
            self.recv_usb_pkt(pkt_type, data[4:])
        elif pkt_id == 'G':
            self.recv_usb_flushed_pkt()
        elif pkt_id == 'D':
            command = int.from_bytes(data[0:4])
            address = int.from_bytes(data[4:8])
            geometry = int.from_bytes(data[8:12])
            self.recv_disk_req_pkt(command, address, geometry, data[12:])
        elif pkt_id == 'I':
            text = data.decode()
            self.recv_printf_pkt(text)
        elif pkt_id == 'S':
            save_type = int.from_bytes(data[0:4])
            self.recv_save_wb_pkt(save_type, data[4:])
        elif pkt_id == 'F':
            progress = int.from_bytss(data[0:4])
            self.recv_update_status_pkt(progress)
        else:
            print(f'PKT{pkt_id} unknown', file=stderr)

    """User function expected to be monkey patched"""
    def recv_aux_pkt(self, value):
        pass

    """User function expected to be monkey patched"""
    def recv_button_pkt(self):
        pass

    """User function expected to be monkey patched"""
    def recv_usb_pkt(self, pkt_type, data):
        pass

    """User function expected to be monkey patched"""
    def recv_usb_flushed_pkt(self):
        pass

    """User function expected to be monkey patched"""
    def recv_disk_req_pkt(self, command, address, geometry, data):
        pass

    """User function expected to be monkey patched"""
    def recv_printf_pkt(self, text):
        print('PRINTF:', text)

    """User function expected to be monkey patched"""
    def recv_save_wb_pkt(self, save_type, data):
        pass

    """User function expected to be monkey patched"""
    def recv_update_status_pkt(self, progress):
        pass

    async def send_cmd(self, pkt_id, arg0=0, arg1=0, data=b''):
        if pkt_id in 'MU':
            arg1 = len(data)

        cmd = 'CMD' + pkt_id
        pkt = cmd.encode() + arg0.to_bytes(4) + arg1.to_bytes(4) + data
        self.transport.write(pkt)

        if pkt_id == 'U': # USB_WRITE has no response, fake one
            return True, bytearray()

        event = asyncio.Event()
        pending = {
            'pkt_id': pkt_id,
            'status': None,
            'data': bytearray(),
            'event': event,
        }
        self._cmd_pending.append(pending)
        try:
            await asyncio.wait_for(event.wait(), 0.5)
        except TimeoutError:
            await self.reset()

        return pending['status'], pending['data']

    def send_usb_cmd(self, pkt_type, data):
        asyncio.create_task(self.send_cmd('U', pkt_type, 0, data))

    @classmethod
    async def connect(cls, port):
        loop = asyncio.get_event_loop()
        _, protocol = await create_serial_connection(loop, cls, port)
        await asyncio.wait_for(protocol.connected.wait(), 1)
        return protocol

    async def get_version(self):
        _, name = await self.send_cmd('v')
        name = name.decode()

        _, version = await self.send_cmd('V')
        major = int.from_bytes(version[0:2])
        minor = int.from_bytes(version[2:4])
        revision = int.from_bytes(version[4:8])

        return f'{name} {major}.{minor}.{revision}'
