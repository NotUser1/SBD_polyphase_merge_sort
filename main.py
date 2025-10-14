from data_generation import calculate_distance, generate_data, split_records_into_tapes, TAPE_COUNT, \
    PAGE_SIZE, read_manual_input, generate_archive

global NUM_OF_PAGE_READS, NUM_OF_WRITES, NUM_OF_PHASES
NUM_OF_PAGE_READS = 0
NUM_OF_WRITES = 0
NUM_OF_PHASES = 0


class Tape:
    def __init__(self, filename, dummy_run_count=0):
        self.filename = filename
        self.dummy_run_count = dummy_run_count
        self.file = None
        self.out_page = []
        self.input_page = []
        self.input_page_index = 0

    def write_record(self, record):
        self.out_page.append(record)
        page_length = len(self.out_page)
        if page_length >= PAGE_SIZE:
            self.write_page()
            self.out_page = []

    def write_page(self):
        global NUM_OF_WRITES
        NUM_OF_WRITES += 1
        for record in self.out_page:
            self.file.write(f"{record['x']},{record['y']}\n")
            self.file.flush()

    def read_record(self):
        line = self.file.readline()
        if not line:
            return None
        line = line.strip()
        if line == "":
            return None
        x, y = map(float, line.split(','))
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


# input1, input2, output
def merge_sort_phase(t1: Tape, t2: Tape, t3: Tape):
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

    global NUM_OF_PHASES
    NUM_OF_PHASES += 1

    # przepisz runny z krótszej taśmy do taśmy wyjściowej
    next_first_record = None
    for i in range(t1.dummy_run_count):
        prev_record = None
        while True:
            if next_first_record is not None:
                record = next_first_record
                next_first_record = None
            else:
                record = t2.read_record()
            if record is None:
                break
            if prev_record is not None and calculate_distance(record) < calculate_distance(prev_record):
                # zapamiętaj rekord na początek kolejnego runa
                next_first_record = record
                break
            # print(record)
            t3.write_record(record)
            prev_record = record

    t1.input_page = t1.read_page()
    t2.input_page = t2.read_page()
    t1.input_page_index = 0
    t2.input_page_index = 0
    record_1 = t1.input_page[t1.input_page_index] if t1.input_page else None
    if next_first_record is not None:
        record_2 = next_first_record
        next_first_record = None
        t2.input_page_index = -1
    else:
        record_2 = t2.input_page[t2.input_page_index] if t2.input_page else None

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
                run2_ended or (record_2 is not None and calculate_distance(record_1) <= calculate_distance(record_2))):
            # print(1, record_1)
            t3.write_record(record_1)
            prev_record_1 = record_1
            record_1, t1.input_page_index, t1.input_page = read_next_record(t1, t1.input_page, t1.input_page_index)
        elif not run2_ended:
            # print(2, record_2)
            t3.write_record(record_2)
            prev_record_2 = record_2
            record_2, t2.input_page_index, t2.input_page = read_next_record(t2, t2.input_page, t2.input_page_index)
        elif record_1 is not None and record_2 is not None:
            # print(record_1, record_2)
            prev_record_1 = None
            prev_record_2 = None
        else:
            break

    t3.write_page()


def reshuffle_tapes(t1: Tape, t2: Tape, t3: Tape):
    t2.file.seek(0)
    t2.file.truncate(0)
    t2.file.flush()
    t2.out_page = []

    t1_reminder = t1.file.readlines()
    t1.file.seek(0)
    t1.file.truncate(0)
    t1.file.flush()

    # 1. write t1 page onto t1
    for i in range(t1.input_page_index, len(t1.input_page)):
        t1.file.write(f"{t1.input_page[i]['x']},{t1.input_page[i]['y']}\n")
    t1.file.flush()

    # 2. write t1_reminder onto t1
    t1.file.writelines(t1_reminder)
    t1.file.flush()

    t1.reset_tape()
    t2.reset_tape()
    t3.reset_tape()

    return t3, t1, t2


def check_if_sorted(t1: Tape, t2: Tape, t3: Tape):
    tapes = [t1, t2, t3]
    data_flags = []
    for tape in tapes:
        tape.file.seek(0)
        has_data = any(tape.file)
        tape.file.seek(0)
        data_flags.append(has_data)
    return data_flags.count(True) == 1


def main():
    global NUM_OF_WRITES, NUM_OF_PHASES
    NUM_OF_WRITES = 0
    NUM_OF_PHASES = 0

    dummy_run_count = 0

    choice = input(
        "To enter records manually press '1',\nto read data from files press '2',\nto generate random data press any other key: ")
    if choice == '1':
        read_manual_input()
    elif choice == '2':
        pass
        # docelowo, czytamy plik rekordów, liczymy ile ich jest i dzielimy na taśmy. ewentualnie podełniamy dummy rekordy
    else:
        tape_1_run_count, tape_2_run_count, dummy_run_count, records = generate_data()

    open("tape_3.txt", "w").close()  # create empty tape 3

    t1 = Tape("tape_1.txt", dummy_run_count)
    t2 = Tape("tape_2.txt", 0)
    t3 = Tape("tape_3.txt", 0)
    t1.file = open(t1.filename, 'r+')
    t2.file = open(t2.filename, 'r+')
    t3.file = open(t3.filename, 'w+')

    # merge_sort_phase(t1, t2, t3)
    while True:
        print(f"Phase {NUM_OF_PHASES}")
        generate_archive(NUM_OF_PHASES, [t1, t2, t3])
        merge_sort_phase(t1, t2, t3)
        t1, t2, t3 = reshuffle_tapes(t1, t2, t3)
        if check_if_sorted(t1, t2, t3):
            print("Sorting completed.")
            break
        input("Press Enter to continue to next phase...")

    generate_archive("sorted", [t1, t2, t3])

    t1.close()
    t2.close()
    t3.close()


if __name__ == "__main__":
    main()
