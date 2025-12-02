import datetime
import json
import signal
import socket

import daemon
import lockfile

from main import Lessons


class LessonsDaemon:
    def __init__(self, port=8001):
        self.port = port
        self.host = ""
        self.week = Lessons("days.json", "homework.json")
        self.running = True

    def main(self):
        while self.running:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, self.port))
                s.listen(1)
                conn, addr = s.accept()
                with conn:
                    data = b""
                    while True:
                        data_temp = conn.recv(1024)
                        if not data_temp:
                            break
                        data += data_temp
                data = json.loads(data.decode("utf-8"))

                if "message" not in data.keys():
                    conn.send(
                        json.dumps({"error": "Invalid data received"}).encode("utf-8")
                    )
                    return
                match data["message"]:
                    case "add_homework":
                        if "subject" not in data or "task" not in data:
                            conn.send(
                                json.dumps({"error": "Missing required fields"}).encode(
                                    "utf-8"
                                )
                            )
                        else:
                            self.week.add_homework(data["subject"], data["task"])
                    case "get_homework":
                        contains = [i in data.keys() for i in ["year", "month", "day"]]
                        if not any(contains):
                            conn.send(
                                json.dumps({"error": "Missing required fields"}).encode(
                                    "utf-8"
                                )
                            )
                        else:
                            year = int(data["year"])
                            month = int(data["month"])
                            day = int(data["day"])
                            date = datetime.date(year, month, day)
                            homework = self.week.get_homework(date)
                            conn.send(json.dumps(homework).encode("utf-8"))
                    case "get_lessons":
                        lessons = self.week.get_lessons()
                        conn.send(json.dumps(lessons).encode("utf-8"))
                    case "get_week":
                        lessons = self.week.lessons_unf
                        conn.send(json.dumps(lessons).encode("utf-8"))
                    case "get_nearest_lesson":
                        if "subject" not in data.keys():
                            conn.send(
                                json.dumps({"error": "Missing subject"}).encode("utf-8")
                            )
                        else:
                            nearest_lesson = self.week.get_nearest_lesson(
                                data["subject"]
                            )
                            conn.send(json.dumps(nearest_lesson).encode("utf-8"))
                    case _:
                        conn.send(
                            json.dumps({"error": "Invalid message"}).encode("utf-8")
                        )

    def reload(self):
        self.running = False
        self.__init__()

    def exit(self):
        self.running = False
        self.week.__exit__()


def main():
    context = daemon.DaemonContext(
        working_directory="/tmp/diary/",
        umask=0o002,
        pidfile=lockfile.FileLock("/var/run/diary.pid"),
    )

    days = open("days.json", "w")
    homework = open("homework.json", "w")
    context.files_preserve = [days, homework]

    diary_daemon = LessonsDaemon()

    context.signal_map = {
        signal.SIGTERM: diary_daemon.exit,
        signal.SIGHUP: "terminate",
        signal.SIGUSR1: diary_daemon.reload,
    }
    with context:
        diary_daemon.main()


if __name__ == "__main__":
    main()
