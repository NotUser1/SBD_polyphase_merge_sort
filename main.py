from data_generation import calculate_distance, generate_data, PAGE_SIZE, read_manual_input, generate_archive, \
    handle_data_from_text_file, RECORD_SIZE, handle_data_from_bin_file

import struct
from abc import ABC, abstractmethod
from typing import Protocol, List, Optional

global NUM_OF_PAGE_READS, NUM_OF_PAGE_WRITES

class InputSource(ABC):
    @abstractmethod
    def load_data(self) -> tuple[int, list, int]:
        pass

class ManualInputSource(InputSource):
    def load_data(self):
        read_manual_input()
        return handle_data_from_text_file("input.txt")

class TextFileInputSource(InputSource):
    def __init__(self, filename="input.txt"):
        self.filename = filename

    def load_data(self):
        return handle_data_from_text_file(self.filename)

class BinaryFileInputSource(InputSource):
    def __init__(self, filename="input.bin"):
        self.filename = filename

    def load_data(self):
        return handle_data_from_bin_file(self.filename)

class RandomDataInputSource(InputSource):
    def load_data(self):
        return generate_data()

class InputFactory:
    @staticmethod
    def get_input_source() -> InputSource:
        choice = input(
            "Aby wprowadzić rekordy ręcznie, naciśnij '1',\n"
            "Aby wczytać dane z plików, naciśnij '2',\n"
            "Aby wygenerować losowe dane, naciśnij dowolny inny klawisz: "
        )
        
        if choice == '1':
            return ManualInputSource()
        elif choice == '2':
            file_type = input("Wpisz 'txt' aby wczytać z pliku tekstowego lub 'bin' aby wczytać z pliku binarnego: ")
            if file_type == 'txt':
                return TextFileInputSource("input.txt")
            elif file_type == 'bin':
                return BinaryFileInputSource("input.bin")
            else:
                raise ValueError(f"Nieznany typ pliku: {file_type}")
        else:
            return RandomDataInputSource()

class FileInterface(Protocol):
    def write(self, s: bytes) -> int: ...
    def read(self, size: int = -1) -> bytes: ...
    def seek(self, offset: int, whence: int = 0) -> int: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...
    def truncate(self, size: Optional[int] = None) -> int: ...
    def readlines(self, hint: int = -1) -> List[bytes]: ...

class NullFile:
    def write(self, s: bytes) -> int: return 0
    def read(self, size: int = -1) -> bytes: return b""
    def seek(self, offset: int, whence: int = 0) -> int: return 0
    def flush(self) -> None: pass
    def close(self) -> None: pass
    def truncate(self, size: Optional[int] = None) -> int: return 0
    def readlines(self, hint: int = -1) -> List[bytes]: return []

class TapeManager:
    def __init__(self):
        self.t1 = None
        self.t2 = None
        self.t3 = None

    def prepare_tapes(self, dummy_run_count):
        open("tape_3.bin", "wb").close()
        self.t1 = Tape("tape_1.bin", dummy_run_count)
        self.t2 = Tape("tape_2.bin", 0)
        self.t3 = Tape("tape_3.bin", 0)
        self.t1.file = open(self.t1.filename, 'r+b') # type: ignore
        self.t2.file = open(self.t2.filename, 'r+b') # type: ignore
        self.t3.file = open(self.t3.filename, 'w+b') # type: ignore

class FileManager:
    @staticmethod
    def close_tapes(*tapes):
        for tape in tapes:
            tape.close()

    @staticmethod
    def generate_archive(parameter, tapes):
        generate_archive(parameter, tapes)

class Tape:
    def __init__(self, filename, dummy_run_count=0):
        self.filename = filename
        self.dummy_run_count = dummy_run_count
        self.file: FileInterface = NullFile()
        self.out_page = []
        self.input_page = []
        self.input_page_index = 0

    def write_record(self, record):
        packed_record = struct.pack('<dd', record['x'], record['y'])
        self.out_page.append(packed_record)
        page_length = len(self.out_page)
        if page_length >= PAGE_SIZE:
            self.write_page()

    def write_page(self):
        global NUM_OF_PAGE_WRITES
        NUM_OF_PAGE_WRITES += 1
        for packed_record in self.out_page:
            self.file.write(packed_record)
        self.file.flush()
        self.out_page = []

    def read_record(self):
        chunk = self.file.read(RECORD_SIZE)
        if not chunk or len(chunk) < RECORD_SIZE:
            return None
        x, y = struct.unpack('<dd', chunk)
        return {"x": x, "y": y}

    def read_page(self):
        global NUM_OF_PAGE_READS
        NUM_OF_PAGE_READS += 1
        page = []
        for _ in range(PAGE_SIZE):
            record = self.read_record()
            if record is None:
                break
            page.append(record)
        return page

    def reset_tape(self):
        self.dummy_run_count = 0
        self.file.seek(0)
        self.out_page = []
        self.input_page = []
        self.input_page_index = 0

    def close(self):
        if self.file:
            self.file.close()
            self.file = NullFile()

class Sorting:
    def __init__(self, t1, t2, t3):
        self.t1 = t1
        self.t2 = t2
        self.t3 = t3

    # input1, input2, output
    def merge_sort_phase(self):
        def read_next_record(tape: Tape, current_page, current_index):
            if current_index + 1 < len(current_page):
                new_record, new_index = current_page[current_index + 1], current_index + 1
                return new_record, new_index, current_page
            else:
                new_page = tape.read_page()
                # print("New page read:", new_page)
                if not new_page:
                    return None, 0, []
                return new_page[0], 0, new_page

        self.t2.input_page = self.t2.read_page()
        self.t2.input_page_index = 0
        record_2 = self.t2.input_page[self.t2.input_page_index] if self.t2.input_page else None
        self.t1.input_page = self.t1.read_page()
        self.t1.input_page_index = 0
        record_1 = self.t1.input_page[self.t1.input_page_index] if self.t1.input_page else None

        # obsługa dummmy runów - przepisz runny z krótszej taśmy do taśmy wyjściowej
        for i in range(self.t1.dummy_run_count):
            prev_record = None
            while True:
                if record_2 is None:
                    break
                if prev_record is not None and calculate_distance(record_2) < calculate_distance(prev_record):
                    break
                # print(record)
                self.t3.write_record(record_2)
                prev_record = record_2
                record_2, self.t2.input_page_index, self.t2.input_page = read_next_record(self.t2, self.t2.input_page,
                                                                                          self.t2.input_page_index)

        prev_record_1 = record_1
        prev_record_2 = record_2

        while record_1 is not None or record_2 is not None:
            # print(record_1, record_2)
            run1_ended = (
                    record_1 is None or
                    (prev_record_1 is not None and record_1 is not None and calculate_distance(
                        record_1) < calculate_distance(prev_record_1))
            )
            run2_ended = (
                    record_2 is None or
                    (prev_record_2 is not None and record_2 is not None and calculate_distance(
                        record_2) < calculate_distance(prev_record_2))
            )

            if not run1_ended and (
                    run2_ended or (
                    record_2 is not None and calculate_distance(record_1) <= calculate_distance(record_2))):
                self.t3.write_record(record_1)
                prev_record_1 = record_1
                record_1, self.t1.input_page_index, self.t1.input_page = read_next_record(self.t1, self.t1.input_page,
                                                                                          self.t1.input_page_index)
            elif not run2_ended:
                self.t3.write_record(record_2)
                prev_record_2 = record_2
                record_2, self.t2.input_page_index, self.t2.input_page = read_next_record(self.t2, self.t2.input_page,
                                                                                          self.t2.input_page_index)
            elif record_1 is not None and record_2 is not None:
                prev_record_1 = None
                prev_record_2 = None
            else:
                break

        self.t3.write_page()

    def reshuffle_tapes(self):
        self.t2.file.seek(0)
        self.t2.file.truncate(0)
        self.t2.file.flush()
        self.t2.out_page = []

        t1_reminder = self.t1.file.readlines()
        self.t1.file.seek(0)
        self.t1.file.truncate(0)
        self.t1.file.flush()

        # 1. write t1 page onto t1
        for i in range(self.t1.input_page_index, len(self.t1.input_page)):
            packed_record = struct.pack('<dd', self.t1.input_page[i]['x'], self.t1.input_page[i]['y'])
            self.t1.file.write(packed_record)
        self.t1.file.flush()

        # 2. write t1_reminder onto t1
        self.t1.file.writelines(t1_reminder)
        self.t1.file.flush()

        self.t1.reset_tape()
        self.t2.reset_tape()
        self.t3.reset_tape()

        return self.t3, self.t1, self.t2

def main():
    global NUM_OF_PAGE_WRITES, NUM_OF_PAGE_READS
    NUM_OF_PAGE_WRITES = 0
    NUM_OF_PAGE_READS = 0

    input_source: InputSource = InputFactory.get_input_source()

    dummy_run_count, records, sorting_phases = input_source.load_data()

    tape_manager = TapeManager()
    tape_manager.prepare_tapes(dummy_run_count)
    t1, t2, t3 = tape_manager.t1, tape_manager.t2, tape_manager.t3

    sorter = Sorting(t1, t2, t3)

    for i in range(sorting_phases):
        print(f"Phase {i}")
        FileManager.generate_archive(i, [t1, t2, t3])
        sorter.merge_sort_phase()
        sorter.t1, sorter.t2, sorter.t3 = sorter.reshuffle_tapes()
        input("Press Enter to continue to next phase...")

    FileManager.generate_archive("sorted", [t1, t2, t3])

    print(f"Number of phases: {sorting_phases}")
    print(f"Number of page writes: {NUM_OF_PAGE_WRITES}")
    print(f"Number of page reads: {NUM_OF_PAGE_READS}")

    FileManager.close_tapes(t1, t2, t3)

if __name__ == "__main__":
    main()
