from shortcut import Shortcut


class Crc(object):
    """
    A base class for CRC routines.
    """

    # Class constructor
    ###############################################################################
    def __init__(
        self,
        width,
        poly,
        reflect_in,
        xor_in,
        reflect_out,
        xor_out,
        table_idx_width=None,
    ):
        """The Crc constructor.

        The parameters are as follows:
            width
            poly
            reflect_in
            xor_in
            reflect_out
            xor_out
        """
        self.Width = width
        self.Poly = poly
        self.ReflectIn = reflect_in
        self.XorIn = xor_in
        self.ReflectOut = reflect_out
        self.XorOut = xor_out
        self.TableIdxWidth = table_idx_width

        self.MSB_Mask = 0x1 << (self.Width - 1)
        self.Mask = ((self.MSB_Mask - 1) << 1) | 1
        if self.TableIdxWidth != None:
            self.TableWidth = 1 << self.TableIdxWidth
        else:
            self.TableIdxWidth = 8
            self.TableWidth = 1 << self.TableIdxWidth

        self.DirectInit = self.XorIn
        self.NonDirectInit = self.__get_nondirect_init(self.XorIn)
        if self.Width < 8:
            self.CrcShift = 8 - self.Width
        else:
            self.CrcShift = 0

    # function __get_nondirect_init
    ###############################################################################
    def __get_nondirect_init(self, init):
        """
        return the non-direct init if the direct algorithm has been selected.
        """
        crc = init
        for i in range(self.Width):
            bit = crc & 0x01
            if bit:
                crc ^= self.Poly
            crc >>= 1
            if bit:
                crc |= self.MSB_Mask
        return crc & self.Mask

    # function reflect
    ###############################################################################
    def reflect(self, data, width):
        """
        reflect a data word, i.e. reverts the bit order.
        """
        x = data & 0x01
        for i in range(width - 1):
            data >>= 1
            x = (x << 1) | (data & 0x01)
        return x

    # function bit_by_bit
    ###############################################################################
    def bit_by_bit(self, in_str):
        """
        Classic simple and slow CRC implementation.  This function iterates bit
        by bit over the augmented input message and returns the calculated CRC
        value at the end.
        """
        register = self.NonDirectInit
        for c in in_str:
            octet = c
            if self.ReflectIn:
                octet = self.reflect(octet, 8)
            for i in range(8):
                topbit = register & self.MSB_Mask
                register = ((register << 1) & self.Mask) | ((octet >> (7 - i)) & 0x01)
                if topbit:
                    register ^= self.Poly

        for i in range(self.Width):
            topbit = register & self.MSB_Mask
            register = (register << 1) & self.Mask
            if topbit:
                register ^= self.Poly

        if self.ReflectOut:
            register = self.reflect(register, self.Width)
        return register ^ self.XorOut

    # function bit_by_bit_fast
    ###############################################################################
    def bit_by_bit_fast(self, in_str):
        """
        This is a slightly modified version of the bit-by-bit algorithm: it
        does not need to loop over the augmented bits, i.e. the Width 0-bits
        wich are appended to the input message in the bit-by-bit algorithm.
        """
        register = self.DirectInit
        for c in in_str:
            octet = ord(c)
            if self.ReflectIn:
                octet = self.reflect(octet, 8)
            for i in range(8):
                topbit = register & self.MSB_Mask
                if octet & (0x80 >> i):
                    topbit ^= self.MSB_Mask
                register <<= 1
                if topbit:
                    register ^= self.Poly
            register &= self.Mask
        if self.ReflectOut:
            register = self.reflect(register, self.Width)
        return register ^ self.XorOut

    # function gen_table
    ###############################################################################
    def gen_table(self):
        """
        This function generates the CRC table used for the table_driven CRC
        algorithm.  The Python version cannot handle tables of an index width
        other than 8.  See the generated C code for tables with different sizes
        instead.
        """
        table_length = 1 << self.TableIdxWidth
        tbl = [0] * table_length
        for i in range(table_length):
            register = i
            if self.ReflectIn:
                register = self.reflect(register, self.TableIdxWidth)
            register = register << (self.Width - self.TableIdxWidth + self.CrcShift)
            for j in range(self.TableIdxWidth):
                if register & (self.MSB_Mask << self.CrcShift) != 0:
                    register = (register << 1) ^ (self.Poly << self.CrcShift)
                else:
                    register = register << 1
            if self.ReflectIn:
                register = (
                    self.reflect(register >> self.CrcShift, self.Width) << self.CrcShift
                )
            tbl[i] = register & (self.Mask << self.CrcShift)
        return tbl

    # function table_driven
    ###############################################################################
    def table_driven(self, in_str):
        """
        The Standard table_driven CRC algorithm.
        """
        tbl = self.gen_table()

        register = self.DirectInit << self.CrcShift
        if not self.ReflectIn:
            for c in in_str:
                tblidx = (
                    (register >> (self.Width - self.TableIdxWidth + self.CrcShift))
                    ^ ord(c)
                ) & 0xFF
                register = (
                    (register << (self.TableIdxWidth - self.CrcShift)) ^ tbl[tblidx]
                ) & (self.Mask << self.CrcShift)
            register = register >> self.CrcShift
        else:
            register = (
                self.reflect(register, self.Width + self.CrcShift) << self.CrcShift
            )
            for c in in_str:
                tblidx = ((register >> self.CrcShift) ^ ord(c)) & 0xFF
                register = ((register >> self.TableIdxWidth) ^ tbl[tblidx]) & (
                    self.Mask << self.CrcShift
                )
            register = self.reflect(register, self.Width + self.CrcShift) & self.Mask

        if self.ReflectOut:
            register = self.reflect(register, self.Width)
        return register ^ self.XorOut



def steam_URL(shortcut: Shortcut):
    # Comments by Scott Rice:
    """
    Calculates the filename for a given shortcut. This filename is a 64bit
    integer, where the first 32bits are a CRC32 based off of the name and
    target (with the added condition that the first bit is always high), and
    the last 32bits are 0x02000000.
    """
    # This will seem really strange (where I got all of these values), but I
    # got the xor_in and xor_out from disassembling the steamui library for
    # OSX. The reflect_in, reflect_out, and poly I figured out via trial and
    # error.
    algorithm = Crc(
        width=32,
        poly=0x04C11DB7,
        reflect_in=True,
        xor_in=0xFFFFFFFF,
        reflect_out=True,
        xor_out=0xFFFFFFFF,
    )
    input_string = shortcut["Exe"].encode("utf-8") + shortcut["AppName"].encode("utf-8")
    top_32 = algorithm.bit_by_bit(input_string) | 0x80000000
    full_64 = (top_32 << 32) | 0x02000000
    return str(full_64)

