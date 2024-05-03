import json, csv


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


def clear(string):
    if string.find(":mtm") != -1:
        string = string[:-4]
    if string.find("✓") != -1:
        string = string[:-1]
    if string.find("\n") != -1:
        string = string.replace("\n", "")
    return string


def lang_setup_phrase(lang:bool):
    if lang:
        return "ОТПРАВИТЬ", "Друг", "Напишите, пожалуйста, Ваш вариант", ["Нет", "Знают мои помощники", "Профилем занимаются помощники", "Нет, но собираюсь", "Не доверяю"]
    return "SEND", "Other", "Write your answer, please", ["No", "Ask my assistants", "No, but I'm going to", "I don't trust SM", "This is done by assistants"]


def setup():
    with open('resources/users_answers.csv', 'w', newline='') as file:
        replics, questions = language_setup("resources/replics.txt", "resources/question.txt")
        writer = csv.writer(file)
        write_data = []
        for index in range(len(replics)):
            write_data.append(replics[index][:-1])
        writer.writerow(write_data)


class User:
    def __init__(self, id: int, username: str):
        self.id = id
        self.username = username
        self.answers = []
        self.pos = 0
        self.lang = False
        self.writing_status = 0
        self.temp_ans = []
        self.end_bool = False
        self.skip_status = 0
        self.skip_scenario = {
            7: 10,
            11: 14,
            14: 17,
            17: 19,
            19: 21,
            21: 23
        }

    def check_end(self, length):
        if self.pos == length:
            return True
        return False

    def skip_position(self):
        return self.pos in self.skip_scenario

    def skip(self):
        return self.skip_scenario[self.pos]

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


