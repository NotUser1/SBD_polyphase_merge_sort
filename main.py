from data_generation import calculate_distance, generate_data, PAGE_SIZE, read_manual_input, generate_archive, \
    handle_data_from_text_file, RECORD_SIZE, handle_data_from_bin_file

import struct

global NUM_OF_PAGE_READS, NUM_OF_PAGE_WRITES


class IO:
    def __init__(self):
        self.t1 = None
        self.t2 = None
        self.t3 = None
        self.dummy_run_count = 0
        self.sorting_phases = 0

    def handle_input(self, choice):
        if choice == '1':
            read_manual_input()
            self.dummy_run_count, records, self.sorting_phases = handle_data_from_text_file("input.txt")
        elif choice == '2':
            file_type = input("Wpisz 'txt' aby wczytać z pliku tekstowego lub 'bin' aby wczytać z pliku binarnego: ")
            if file_type == 'txt':
                self.dummy_run_count, records, self.sorting_phases = handle_data_from_text_file("input.txt")
            elif file_type == 'bin':
                self.dummy_run_count, records, self.sorting_phases = handle_data_from_bin_file("input.bin")
        else:
            self.dummy_run_count, records, self.sorting_phases = generate_data()

    def prepare_tapes(self, dummy_run_count):
        open("tape_3.bin", "wb").close()

        self.t1 = Tape("tape_1.bin", dummy_run_count)
        self.t2 = Tape("tape_2.bin", 0)
        self.t3 = Tape("tape_3.bin", 0)
        self.t1.file = open(self.t1.filename, 'r+b')
        self.t2.file = open(self.t2.filename, 'r+b')
        self.t3.file = open(self.t3.filename, 'w+b')


class Tape:
    def __init__(self, filename, dummy_run_count=0):
        self.filename = filename
        self.dummy_run_count = dummy_run_count
        self.file = None
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
            self.file = None


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

    choice = input(
        "Aby wprowadzić rekordy ręcznie, naciśnij '1',\n"
        "Aby wczytać dane z plików, naciśnij '2',\n"
        "Aby wygenerować losowe dane, naciśnij dowolny inny klawisz: "
    )

    io = IO()
    io.handle_input(choice)
    io.prepare_tapes(io.dummy_run_count)
    t1, t2, t3 = io.t1, io.t2, io.t3

    sorter = Sorting(t1, t2, t3)

    for i in range(io.sorting_phases):
        print(f"Phase {i}")
        generate_archive(i, [t1, t2, t3])
        sorter.merge_sort_phase()
        sorter.t1, sorter.t2, sorter.t3 = sorter.reshuffle_tapes()
        input("Press Enter to continue to next phase...")

    generate_archive("sorted", [t1, t2, t3])

    print(f"Number of phases: {io.sorting_phases}")
    print(f"Number of page writes: {NUM_OF_PAGE_WRITES}")
    print(f"Number of page reads: {NUM_OF_PAGE_READS}")

    t1.close()
    t2.close()
    t3.close()


if __name__ == "__main__":
    main()
