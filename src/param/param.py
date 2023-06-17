from struct import pack
from const import PARAM_HEADER
from data import (
    read_bool,
    read_byte_array,
    read_char,
    read_int,
    read_short,
    read_str,
    read_uint,
    replace_byte_array,
    string_to_bytearray,
)
from settings.settings import Settings, SettingsEntry


class Field:
    """
    Field
    """

    def __init__(self, id: int, settings: SettingsEntry, data: bytes):
        self.id = id
        self.settings = settings
        self.raw_data = data
        self.value = self.process_value(data)

    def process_value(self, data: bytes):
        type = self.settings.type
        if type == "uint":
            return read_uint(data)
        elif type == "int":
            return read_int(data)
        elif type == "short":
            return read_short(data)
        elif type == "ushort":
            return read_short(data)
        elif type == "char":
            return read_char(data)
        elif type == "uchar":
            return read_char(data)
        elif type == "bool":
            return read_bool(data)
        elif type == "str":
            return read_str(data)
        else:
            return None

    def set_value(self, new_value):
        self.value = new_value

    def to_bytes(self):
        if type == "uint":
            return pack("i", self.value)
        if type == "int":
            return pack("I", self.value)
        elif type == "ushort":
            return pack("h", self.value)
        elif type == "short":
            return pack("H", self.value)
        elif type == "uchar":
            return pack("c", self.value)
        elif type == "char":
            return pack("C", self.value)
        elif type == "str":
            return string_to_bytearray(self.value, self.settings.size)


class Entry:
    """
    Entry
    """

    def __init__(self, id: int, settings: list, data: bytes):
        self.id = id
        self.settings = settings
        self.raw_data = data

        self.fields = []
        self.process_data(data)

    def process_data(self, data: bytes):
        for setting in self.settings:
            field_data = read_byte_array(data, setting.address, setting.size)
            self.fields.append(Field(self.settings.index(setting), setting, field_data))

    def to_bytes(self):
        raw_data = self.raw_data

        for field in self.fields:
            raw_data = replace_byte_array(
                raw_data, field.settings.position, field.to_bytes
            )

        return raw_data


class Section:
    """
    Secton object
    """

    def __init__(
        self,
        id: int,
        settings: list,
        entry_size: int,
        entry_amount: int,
        data: bytes,
    ):
        # Values
        self.id = id
        self.settings = settings
        self.entry_size = entry_size
        self.entry_amount = entry_amount

        # Entry list
        self.raw_data = data
        self.entry_list = []
        self.process_data(data)

    def process_data(self, data):
        for index in range(self.entry_amount):
            raw_data = read_byte_array(data, index * self.entry_size, self.entry_size)
            self.entry_list.append(Entry(index, self.settings, raw_data))

    def to_bytes(self):
        raw_data = b""

        for entry in self.entry_list:
            raw_data += entry.to_bytes()

        return raw_data


class Param:
    """
    Param object
    """

    def __init__(self, data: bytes = b"", settings: Settings = None):
        self.settings = settings
        self.set_default_values()

        # Return if data file is not valid
        if (
            data == None
            or data == b""
            or read_byte_array(data, 0x0, 0x8) != PARAM_HEADER
        ):
            return

        # Load data from header
        self.process_header(data)

        # Load all entry data
        self.process_data(data)

    def load_from_data(self, data: bytes = b""):
        """
        Loads from data
        Args:
            data (bytes, optional): _description_. Defaults to b"".
        """

        # Return if data file is not valid
        if data == b"" or read_byte_array(data, 0x0, 0x8) != PARAM_HEADER:
            return

        self.set_default_values()

        # Load data from header
        self.process_header(data)

        # Load all entry data
        self.process_data(data)

    def set_default_values(self):
        """
        Sets default valyes
        """

        # Header values
        self.ptr = None
        self.unk = None
        self.sections = None
        self.unk2 = None
        self.id = None

        # Section list
        self.section_list = []

        # Other
        self.entry_list = []
        self.is_modified = False

    def process_header(self, data: bytes):
        """
        Get initial values from file header
        Args:
            data (bytes): File data
        """

        self.ptr = read_uint(data, 0x8)
        self.unk = read_byte_array(data, 0xC, 0x4)
        self.sections = read_uint(data, 0x10)
        self.unk2 = read_byte_array(data, 0x14, 0x8)
        self.id = read_uint(data, 0x18)

    def process_data(self, data: bytes):
        """
        Processes data from file header
        Args:
            data (bytes): raw file data
        """
        self.raw_data = data

        section_index = 0x20
        data_index = self.ptr

        for section in range(self.sections):
            section_settings = self.settings.get_entries_in_param(self.id, section)

            section_entries = read_uint(data, section_index)
            section_size = read_uint(data, section_index + 0x4)
            raw_data = read_byte_array(data, data_index, section_entries * section_size)

            self.section_list.append(
                Section(
                    section, section_settings, section_size, section_entries, raw_data
                )
            )

            section_index += 0x8
            data_index += len(raw_data)

    def to_bytes(self) -> bytes:
        file = PARAM_HEADER

        file += pack(
            "IIII",
            self.ptr,
            self.unk,
            self.sections,
        )

        file += self.unk2

        file += pack(
            "I",
            self.id,
        )

        section_data = b""

        for section in self.section_list:
            file += pack("II", section.entry_amount, section.entry_size)
            section_data += section.to_bytes()

        file += section_data

        return file