import random

TAPE_COUNT = 2
PAGE_SIZE = 4
RECORD_COUNT = 20

global NUM_OF_RECORD_READS, NUM_OF_PAGE_READS, NUM_OF_WRITES, NUM_OF_PHASES
NUM_OF_RECORD_READS = 0
NUM_OF_PAGE_READS = 0
NUM_OF_WRITES = 0
NUM_OF_PHASES = 0


def calculate_distance(record):
    if record is None:
        return 0
    return (record['x'] ** 2 + record['y'] ** 2) ** 0.5


def fibonacci_pair(n):
    a, b = 1, 1
    while n > (a + b):
        a, b = b, a + b
    return a, b


def generate_record():
    record = {
        # "x": random.randint(1, 1000) / 100.0,
        # "y": random.randint(1, 1000) / 100.0
        "x": random.randint(0, 4),
        "y": 0
    }
    return record


def generate_data():
    # generate up to 30 runs to be later split into 2 tapes and filled with dummy runs
    records = []
    for _ in range(RECORD_COUNT):
        records.append(generate_record())
    return records


# recounts runs in case 2 generated runs make a single run in the end
def count_runs(runs):
    count = 0


def get_run_count(runs):
    if not runs:
        return 0
    count = 1
    prev_record = runs[0]
    for record in runs[1:]:
        if calculate_distance(record) < calculate_distance(prev_record):
            count += 1
        prev_record = record
    return count


def split_records_into_tapes(records):
    def write_records_to_tape(tape_number, records_arr, records_count):
        for _ in range(records_count):
            if not records_arr:
                break
            record = records_arr.pop(0)
            tape_number.write(f"{record['x']},{record['y']}\n")
            prev_record = record
            while records_arr:
                record = records_arr[0]
                if calculate_distance(record) >= calculate_distance(prev_record):
                    tape_number.write(f"{record['x']},{record['y']}\n")
                    prev_record = record
                    records_arr.pop(0)
                else:
                    break

    run_count = get_run_count(records)
    a, b = fibonacci_pair(run_count)
    dummy_records_count = (a + b) - run_count
    print("t1: ", b, " t2: ", a, " dummy: ", dummy_records_count)
    # write a records to tape 2 and b - dummy records to tape 2
    with open("tape_1.txt", "w") as tape1, open("tape_2.txt", "w") as tape2:
        write_records_to_tape(tape2, records, a)
        write_records_to_tape(tape1, records, b)
        return b, a, dummy_records_count


def read_manual_input():
    for i in range(TAPE_COUNT):
        print(f"Tape {i + 1}/3")
        with open(f"tape_{i + 1}.txt", "w") as f:
            while True:
                x = input("Enter x: ")
                y = input("Enter y: ")
                f.write(f"{x},{y}\n")
                cont = input("To add another record press '1', to end this tape press any other key: ")
                if cont == '1':
                    continue
                else:
                    break


def generate_archive(parameter):
    if parameter == 1:
        f_name = "archive_before"
    else:
        f_name = "archive_after"
    with open(f"{f_name}.txt", "w") as archive:
        for i in range(1, TAPE_COUNT + 1):
            tape_file = f"tape_{i}.txt"
            archive.write(f"{tape_file}\n")
            with open(tape_file, "r") as tape:
                archive.write(tape.read())
            archive.write("\n")


def print_file(filename):
    print(f"Zawartość {filename}:")
    with open(filename, 'r') as f:
        for line in f:
            print(line.strip())


def read_one_record(file):
    global NUM_OF_RECORD_READS
    line = file.readline()
    if not line:
        return None
    NUM_OF_RECORD_READS += 1
    line = line.strip()
    if line == "dummy_run":
        return "dummy_run"
    if line == "":
        return None
    x, y = map(float, line.split(','))
    return {"x": x, "y": y}


def read_page(file):
    global NUM_OF_PAGE_READS
    NUM_OF_PAGE_READS += 1
    page = []
    for _ in range(PAGE_SIZE):
        record = read_one_record(file)
        if record is None:
            break
        page.append(record)
    return page


def write_one_record(output_file, record):
    global NUM_OF_WRITES
    NUM_OF_WRITES += 1
    if record == "dummy_run":
        output_file.write("dummy_run\n")
    else:
        output_file.write(f"{record['x']},{record['y']}\n")


class Tape:
    def __init__(self, filename, total_run_count=0, dummy_run_count=0):
        self.filename = filename
        self.total_run_count = total_run_count
        self.dummy_run_count = dummy_run_count
        self.file = None

    def close(self):
        if self.file:
            self.file.close()
            self.file = None

    def write_record(self, record):
        global NUM_OF_WRITES
        NUM_OF_WRITES += 1
        self.file.write(f"{record['x']},{record['y']}\n")

    def read_record(self):
        global NUM_OF_RECORD_READS
        line = self.file.readline()
        if not line:
            return None
        NUM_OF_RECORD_READS += 1
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

    def reset_counters(self):
        self.total_run_count = 0
        self.dummy_run_count = 0


# input1, input2, outputs
def merge_sort_phase(t1: Tape, t2: Tape, t3: Tape):
    def read_next_record(tape, current_page, current_index):
        if current_index + 1 < len(current_page):
            new_record, new_index = current_page[current_index + 1], current_index + 1
            return new_record, new_index, current_page
        else:
            new_page = tape.read_page()
            if not new_page:
                return None, -1, []
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
            print(record)
            t3.write_record(record)
            prev_record = record

    page1 = t1.read_page()
    page2 = t2.read_page()
    index1 = 0
    index2 = 0
    record_1 = page1[index1] if page1 else None
    if next_first_record is not None:
        record_2 = next_first_record
        index2 = -1
    else:
        record_2 = page2[index2] if page2 else None

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
            print(1, record_1)
            t3.write_record(record_1)
            prev_record_1 = record_1
            record_1, index1, page1 = read_next_record(t1, page1, index1)
        elif not run2_ended:
            print(2, record_2)
            t3.write_record(record_2)
            prev_record_2 = record_2
            record_2, index2, page2 = read_next_record(t2, page2, index2)
        elif record_1 is not None and record_2 is not None:
            print(record_1, record_2)
            prev_record_1 = None
            prev_record_2 = None
        else:
            break


def main():
    global NUM_OF_RECORD_READS, NUM_OF_WRITES, NUM_OF_PHASES
    NUM_OF_RECORD_READS = 0
    NUM_OF_WRITES = 0
    NUM_OF_PHASES = 0

    tape_1_run_count = 0
    tape_2_run_count = 0
    dummy_run_count = 0

    choice = input(
        "To enter records manually press '1',\nto read data from files press '2',\nto generate random data press any other key: ")
    if choice == '1':
        read_manual_input()
    elif choice == '2':
        pass
        # docelowo, czytamy plik rekordów, liczymy ile ich jest i dzielimy na taśmy. ewentualnie podełniamy dummy rekordy
    else:
        records = generate_data()
        tape_2_run_count, tape_1_run_count, dummy_run_count = split_records_into_tapes(records)

    open("tape_3.txt", "w").close()  # create empty tape 3

    generate_archive(1)

    t1 = Tape("tape_1.txt", tape_1_run_count + dummy_run_count, dummy_run_count)
    t2 = Tape("tape_2.txt", tape_2_run_count, 0)
    t3 = Tape("tape_3.txt", 0, 0)
    t1.file = open(t1.filename, 'r')
    t2.file = open(t2.filename, 'r')
    t3.file = open(t3.filename, 'w+')

    merge_sort_phase(t1, t2, t3)

    t1.close()
    t2.close()
    t3.close()


if __name__ == "__main__":
    main()
