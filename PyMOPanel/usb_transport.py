"""USB bulk transport for Matrix Orbital panels.

Used on macOS (and any system where the panel doesn't enumerate as a serial
port) to talk directly to the USB bulk endpoints via libusb/pyusb.
"""

import usb.core
import usb.util


class USBSerial:
    """Minimal pyserial-compatible interface over USB bulk endpoints.

    serial.threaded.ReaderThread works with this class because:
      - it sets self.serial.timeout = 1 (we accept it via the property)
      - it loops on self.serial.read(self.serial.in_waiting or 1)
        (in_waiting=0 → read(1), which returns b'' on USB timeout)
      - it checks self.serial.is_open to keep the loop alive
    """

    MATRIX_ORBITAL_VID = 0x1B3D
    GLK19264_PID       = 0x0127
    EP_OUT             = 0x02
    EP_IN              = 0x81

    def __init__(self, vid=MATRIX_ORBITAL_VID, pid=GLK19264_PID, timeout=1):
        self._baudrate        = 19200          # nominal; unused for USB
        self._read_timeout_ms = int(timeout * 1000)
        self._buffer          = bytearray()   # internal read buffer

        self._dev = usb.core.find(idVendor=vid, idProduct=pid)
        if self._dev is None:
            raise IOError(f"USB device {vid:04X}:{pid:04X} not found. "
                          "Is the panel connected?")
        try:
            if self._dev.is_kernel_driver_active(0):
                self._dev.detach_kernel_driver(0)
        except usb.core.USBError:
            pass  # not supported on all platforms / already detached
        self._dev.set_configuration()

    # --- pyserial-compatible properties ---

    @property
    def is_open(self) -> bool:
        return self._dev is not None

    @property
    def baudrate(self) -> int:
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value: int):
        self._baudrate = value  # no-op; USB speed is fixed

    @property
    def timeout(self) -> float:
        return self._read_timeout_ms / 1000

    @timeout.setter
    def timeout(self, value: float):
        # serial.threaded.ReaderThread sets this to 1 when cancel_read is absent
        if value is not None:
            self._read_timeout_ms = int(value * 1000)

    @property
    def in_waiting(self) -> int:
        return 0  # USB bulk can't peek; returning 0 makes callers do read(1)

    # --- pyserial-compatible methods ---

    def _clear_halt(self, endpoint):
        try:
            usb.util.clear_halt(self._dev, endpoint)
        except usb.core.USBError:
            pass

    def write(self, data) -> int:
        try:
            return self._dev.write(self.EP_OUT, data, timeout=1000)
        except usb.core.USBError as e:
            if e.errno == 32:  # EPIPE / endpoint STALL
                self._clear_halt(self.EP_OUT)
                return self._dev.write(self.EP_OUT, data, timeout=1000)
            raise

    def read(self, size: int) -> bytes:
        """Read exactly `size` bytes, buffering full USB packets internally.

        The panel sends USB bulk packets of up to 64 bytes. We must always
        receive the full packet to avoid EOVERFLOW; excess bytes are kept in
        an internal buffer for the next read() call.
        """
        while len(self._buffer) < size:
            try:
                chunk = self._dev.read(self.EP_IN, 64,
                                       timeout=self._read_timeout_ms)
                self._buffer.extend(chunk)
            except usb.core.USBTimeoutError:
                break  # return whatever we have
            except usb.core.USBError as e:
                if e.errno == 32:  # EPIPE / endpoint STALL
                    self._clear_halt(self.EP_IN)
                break

        result = bytes(self._buffer[:size])
        self._buffer = self._buffer[size:]
        return result

    def reset_input_buffer(self):
        """Drain any pending bytes from the USB IN endpoint and internal buffer."""
        self._buffer.clear()
        try:
            while True:
                data = self._dev.read(self.EP_IN, 64, timeout=30)
                if not data:
                    break
        except (usb.core.USBTimeoutError, usb.core.USBError):
            pass
