import calendar
import os
import time
import datetime
import tabulate
import json

day = datetime.datetime.today().weekday()
DAY = list(calendar.day_name)[day]
text = """
1 - вывести неделю
2 - добавить дз
3 - вывести дз
4 - выйти
"""


class LessonNotFoundError(Exception):
    def __init__(self, *args, **kargs) -> None:
        super().__init__(*args, **kargs)


class Lessons:
    def __init__(self, lessons_filename: str, homework_filename: str) -> None:
        lessons = open(lessons_filename).read()
        if lessons == "":
            lessons = "[]"
        self.lessons_unf = json.loads(lessons)
        self.lessons = []
        for i in range(7):
            self.lessons.append(
                [self.lessons_unf[k][i] for k in range(5)])
        self.homework = {}
        if homework_filename in os.listdir():
            homework = open(lessons_filename).read()
            if homework == "":
                homework = "{}"
            self.homework = json.loads(open(homework_filename).read())
        self.homework_filename = homework_filename
        self.lessons_filename = lessons_filename

    def __enter__(self):
        return self

    def __exit__(self, *args, **kargs) -> None:
        with open(self.homework_filename, "w") as f:
            f.write(json.dumps(self.homework, ensure_ascii= False))

        with open(self.lessons_filename, "w") as f:
            f.write(json.dumps(self.lessons_unf))
        return

    def get_nearest_lesson(self, lesson: str) -> datetime.date:
        date: None | datetime.date = None
        for weekday in range(day+1, 7):
            if lesson in self.lessons_unf[weekday]:
                date = datetime.date.fromtimestamp(
                    time.time()+24*(weekday-day+1))
                break

        for weekday in range(day):
            if lesson in self.lessons_unf[weekday]:
                date = datetime.date.fromtimestamp(
                    time.time()+24*(weekday-day+1)*60*60+24*3600*(7+weekday-day))
                break
        if date is not None:
            return date
        raise LessonNotFoundError(f"Lesson {lesson} is not found!")

    def add_homework(self, lesson: str, task: str) -> None:
        date = self.get_nearest_lesson(lesson)
        if date not in self.homework.keys():
            self.homework[str(date)] = {}
        self.homework[str(date)][lesson] = task

    def get_homework_day(self, date: datetime.date = datetime.date.fromtimestamp(time.time()+24*3600)) -> dict[str]:
        if str(date) in self.homework.keys():
            return self.homework[str(date)]
        return {}

    def get_lessons(self):
        uniq_lessons = []
        for les in range(len(self.lessons)):
            for day in range(5):
                l = self.lessons[les][day]
                if l not in uniq_lessons:
                    uniq_lessons.append(l)
        uniq_lessons.sort()
        return uniq_lessons

    def print(self) -> None:
        print(tabulate.tabulate(self.lessons, tuple(
            calendar.day_name)[:-2], "grid"))


class UI:
    def __init__(self):
        self.week = Lessons("days.json", "homework.json")
        try:
            self.main_loop()
        except Exception as e:
            print(e)
            self.week.__exit__()

    def main_loop(self):
        while True:
            print(text)
            inp = int(input(">> "))
            match inp:
                case 1:
                    self.week.print()
                case 2:
                    lesson = input("урок >> ")
                    task = input("задание >> ")
                    self.week.add_homework(lesson, task)
                case 3:
                    month = int(input("месяц >> "))
                    day = int(input("день >> "))
                    year = datetime.datetime.now().year
                    date = datetime.date(year, month, day)
                    print(self.week.get_homework_day(date))
                case 4:
                    self.week.__exit__()
                    break


def main():
    ui = UI()


if __name__ == "__main__":
    main()
