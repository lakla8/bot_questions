import json, csv, time


#while True:
#    start_time = time.perf_counter()
#    check_connection('5619008532:AAF5-948zWVF86Mpa0EcNM6WLQoeeaIgZZI')
#    end_time = time.perf_counter()
#    elapsed_time = end_time - start_time
#    print(f"Elapsed time: {elapsed_time} seconds")


def create_json_file(input_data, output_file):
    output_dict = {'users_list': input_data}
    output_dict = json.dumps(output_dict, indent=2)

    with open(output_file, 'w') as f:
        f.write(output_dict)


def check_user_new(user_id: id, user_list: list) -> int | bool:
    for index in range(len(user_list)):
        if user_list[index].id == user_id:
            return index
    return False


def language_setup(input_file1: str, input_file2: str):
    questions, buttons = [], []
    with open(input_file1) as f:
        for _ in range(32):
            questions.append(f.readline())
    with open(input_file2) as f:
        for _ in range(29):
            buttons.append([i for i in f.readline().split(":")])

    return questions, buttons


def setup():
    with open('resources/users_answers.csv', 'w', newline='') as file:
        replics, questions = language_setup("resources/replics.txt", "resources/question.txt")
        writer = csv.writer(file)
        write_data = []
        for index in range(len(replics)):
            write_data.append(replics[index][:-1])
        writer.writerow(write_data)


class User:
    def __init__(self, id: int, username: str, lang="rus"):
        self.id = id
        self.username = username
        self.answers = []
        self.pos = 0
        self.lang = lang
        self.writing_status = 0
        self.temp_ans = []
        self.end_bool = False

    def check_end(self, length):
        if self.pos == length:
            return True
        return False

    def save(self, questions):
        with open('resources/users_answers.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            write_data = [str("@" + str(self.username))]
            for index in range(len(self.answers)):
                write_data.append(self.answers[index])
            writer.writerow(write_data)
        self.pos = 0
        self.answers = []
        self.temp_ans = []
        self.end_bool = False