import keyboard
import csv
import time
from threading import Thread, Event
import psutil
from pynput import mouse

# Список отслеживаемых горячих клавиш.
HOTKEYS = ["space", "ctrl+c", "ctrl+v", "alt+tab"]
# Таймаут в секундах для записи новых данных в csv.
CSV_WRITER_DELAY = 10
# Таймаут для бездействия мыши. 
# Чем больше - тем больше секунд мышь должна находиться в покое для засчитывания бездействия.
MOUSE_IDLE_TIME_THRESHOLD = 0.5

hotkeys_using_amount = 0
mouse_using_time = 0
mouse_idle_time = 0
stop_threads_event = Event()


def update_csv():
    with open("result.csv", encoding='utf-8', mode="+a") as file:
        csv_writer = csv.writer(file, delimiter = ",", lineterminator="\r")
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        csv_writer.writerow([now, "НажатияГорячихКлавиш", hotkeys_using_amount])
        csv_writer.writerow([now, "ИспользованиеМыши(сек)", mouse_using_time])
        csv_writer.writerow([now, "ИспользованиеRAM(%)", psutil.virtual_memory().percent])
        csv_writer.writerow([now, "АктивностьПроцессора(%)", psutil.cpu_percent()])
 

def handle_hotkey():
    global hotkeys_using_amount
    hotkeys_using_amount += 1
    print("hotkeys =", hotkeys_using_amount)


def run_keyboard_handler():
    for hotkey in HOTKEYS:
        keyboard.add_hotkey(hotkey, handle_hotkey)
    keyboard.wait('esc')
    stop_threads_event.set()


def on_mouse_action(*args, **kwargs):
    global mouse_idle_time
    mouse_idle_time = 0
    if stop_threads_event.is_set():
        return False


def run_mouse_handler():
    listener = mouse.Listener(
        on_move=on_mouse_action,
        on_click=on_mouse_action,
        on_scroll=on_mouse_action)
    listener.start()
    return listener


def main():
    global hotkeys_using_amount
    global mouse_using_time
    global mouse_idle_time

    keyboard_thread = Thread(name="KeyboardHandler", target=run_keyboard_handler, daemon=True)
    print("Start KeyboardHandler")
    keyboard_thread.start()

    print("Start MouseHandler")
    mouse_thread = run_mouse_handler()

    timer = 0
    LOOP_DELAY = 0.05
    while not stop_threads_event.is_set():
        try:
            if timer >= CSV_WRITER_DELAY:
                timer = 0
                print("Update CSV")
                update_csv()
                hotkeys_using_amount = 0
                mouse_using_time = 0

            timer += LOOP_DELAY
            mouse_idle_time += LOOP_DELAY

            if mouse_idle_time < MOUSE_IDLE_TIME_THRESHOLD:
                mouse_using_time += LOOP_DELAY
            time.sleep(LOOP_DELAY)
        except KeyboardInterrupt:
            stop_threads_event.set()
            keyboard.send('esc')
            break
    print("Wait other threads")
    mouse_thread.join()
    print("MouseHandler Finished")
    keyboard_thread.join()
    print("KeyboardHandler Finished")
    print("Exit Program")

if __name__ == "__main__":
    main()
