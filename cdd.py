import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import os
import random
import math

# Константы
CELL_SIZE = 60  # Размер одной клетки в пикселях
GRID_WIDTH, GRID_HEIGHT = 5, 6  # Размеры игрового поля
PLAYER_COLORS = ["#4287f5", "#f54242"]  # Цвета камней игроков (голубой и красный)
NUM_STONES = 6  # Количество пар камней у каждого игрока (всего 12 камней)
DATABASE_FILE = "bolotudu.db"  # Файл базы данных
SAVE_FILE = "bolotudu_save.json"  # Файл сохранения игры
BOARD_COLOR = "#8B4513"  # Темно-коричневый цвет доски
GRID_COLOR = "#D2B48C"  # Песочный цвет линий сетки
STONE_BORDER_WIDTH = 3  # Толщина обводки камней
STONE_HIGHLIGHT_COLOR = "#FFD700"  # Золотой цвет подсветки
STONE_GRADIENT_START = "#FFFFFF"  # Начальный цвет градиента камня
STONE_GRADIENT_END = "#D3D3D3"  # Конечный цвет градиента камня
STONE_SHADOW_COLOR = "#000000"  # Цвет тени камня
STONE_SHADOW_OFFSET = 3  # Смещение тени
STONE_SIZE_RATIO = 0.85  # Размер камня относительно клетки


class BolotuduGame:
    def __init__(self):
        # Инициализация основного окна
        self.window = tk.Tk()
        self.window.title("Болотуду")
        self.window.geometry("800x600")
        self.window.configure(bg="#2C3E50")

        # Создание базы данных
        self.create_database()

        # Загрузка и установка иконки
        try:
            self.window.iconbitmap("icon.ico")
        except:
            pass

        # Инициализация состояния игры
        self.board = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        self.current_player = 0
        self.stage = 1  # 1 - расстановка, 2 - перемещение
        self.stones_count = [0, 0]  # Количество камней на поле для каждого игрока
        self.remaining_pairs = [NUM_STONES, NUM_STONES]  # Оставшиеся пары камней для размещения
        self.stones_to_place = 2  # Сколько камней нужно разместить в текущем ходу
        self.selected_stone = None  # Выбранный камень для перемещения
        self.current_user = None

        # Создание холста для рисования
        self.canvas = None
        self.info_label = None

        # Показываем окно входа
        self.show_login_screen()

        # Запуск главного цикла
        self.window.mainloop()

    def draw_board(self):
        """Отрисовывает текущее состояние игрового поля"""
        self.canvas.delete("all")

        # Рисуем сетку
        for i in range(GRID_WIDTH + 1):
            x = i * CELL_SIZE
            self.canvas.create_line(x, 0, x, GRID_HEIGHT * CELL_SIZE, fill=GRID_COLOR, width=2)

        for i in range(GRID_HEIGHT + 1):
            y = i * CELL_SIZE
            self.canvas.create_line(0, y, GRID_WIDTH * CELL_SIZE, y, fill=GRID_COLOR, width=2)

        # Рисуем камни
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                if self.board[row][col] is not None:
                    x = col * CELL_SIZE + CELL_SIZE // 2
                    y = row * CELL_SIZE + CELL_SIZE // 2
                    color = PLAYER_COLORS[self.board[row][col]]

                    # Выделяем выбранный камень
                    outline_color = "yellow" if (row, col) == self.selected_stone else "black"
                    outline_width = 3 if (row, col) == self.selected_stone else 1

                    self.canvas.create_oval(x - CELL_SIZE // 3, y - CELL_SIZE // 3,
                                            x + CELL_SIZE // 3, y + CELL_SIZE // 3,
                                            fill=color, outline=outline_color, width=outline_width)

        # Обновляем информационную метку
        player_text = f"игрока {self.current_player + 1}"
        stones_text = f" (осталось камней: {self.stones_count[self.current_player]})"
        self.info_label.config(text=f"Ход {player_text} ({PLAYER_COLORS[self.current_player]} камни){stones_text}")

    def create_database(self):
        """Создает базу данных и таблицу пользователей"""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0
        )
        ''')
        conn.commit()
        conn.close()

    def show_login_screen(self):
        """Показывает экран входа"""
        for widget in self.window.winfo_children():
            widget.destroy()

        login_frame = tk.Frame(self.window, bg="#ffffff", padx=40, pady=40)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_label = tk.Label(login_frame, text="Вход в игру", font=("Arial", 24, "bold"), bg="#ffffff")
        title_label.pack(pady=(0, 30))

        # Поля ввода
        username_label = tk.Label(login_frame, text="Имя пользователя:", bg="#ffffff", font=("Arial", 12))
        username_label.pack()
        username_entry = tk.Entry(login_frame, font=("Arial", 12))
        username_entry.pack(pady=(0, 10))

        password_label = tk.Label(login_frame, text="Пароль:", bg="#ffffff", font=("Arial", 12))
        password_label.pack()
        password_entry = tk.Entry(login_frame, show="*", font=("Arial", 12))
        password_entry.pack(pady=(0, 20))

        button_style = {"font": ("Arial", 12), "width": 20, "pady": 8}

        def login():
            username = username_entry.get()
            password = password_entry.get()

            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                self.current_user = username
                messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
                self.show_main_menu()
            else:
                messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

        tk.Button(login_frame, text="Войти", command=login,
                  bg="#4CAF50", fg="white", **button_style).pack(pady=5)

        tk.Button(login_frame, text="Регистрация", command=self.show_register_screen,
                  bg="#2196F3", fg="white", **button_style).pack(pady=5)

    def show_register_screen(self):
        """Показывает экран регистрации"""
        for widget in self.window.winfo_children():
            widget.destroy()

        register_frame = tk.Frame(self.window, bg="#ffffff", padx=40, pady=40)
        register_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_label = tk.Label(register_frame, text="Регистрация", font=("Arial", 24, "bold"), bg="#ffffff")
        title_label.pack(pady=(0, 30))

        # Поля ввода
        username_label = tk.Label(register_frame, text="Придумайте имя пользователя:", bg="#ffffff", font=("Arial", 12))
        username_label.pack()
        username_entry = tk.Entry(register_frame, font=("Arial", 12))
        username_entry.pack(pady=(0, 10))

        password_label = tk.Label(register_frame, text="Придумайте пароль:", bg="#ffffff", font=("Arial", 12))
        password_label.pack()
        password_entry = tk.Entry(register_frame, show="*", font=("Arial", 12))
        password_entry.pack(pady=(0, 10))

        confirm_label = tk.Label(register_frame, text="Подтвердите пароль:", bg="#ffffff", font=("Arial", 12))
        confirm_label.pack()
        confirm_entry = tk.Entry(register_frame, show="*", font=("Arial", 12))
        confirm_entry.pack(pady=(0, 20))

        button_style = {"font": ("Arial", 12), "width": 20, "pady": 8}

        def register():
            username = username_entry.get()
            password = password_entry.get()
            confirm = confirm_entry.get()

            if not username or not password:
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены")
                return

            if password != confirm:
                messagebox.showerror("Ошибка", "Пароли не совпадают")
                return

            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                messagebox.showinfo("Успех", "Регистрация успешна!")
                self.show_login_screen()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Такое имя пользователя уже существует")
            finally:
                conn.close()

        tk.Button(register_frame, text="Зарегистрироваться", command=register,
                  bg="#4CAF50", fg="white", **button_style).pack(pady=5)

        tk.Button(register_frame, text="Назад", command=self.show_login_screen,
                  bg="#f44336", fg="white", **button_style).pack(pady=5)

    def setup_game_board(self):
        """Настраивает игровое поле"""
        for widget in self.window.winfo_children():
            widget.destroy()

        # Создаем холст для рисования
        self.canvas = tk.Canvas(self.window, width=GRID_WIDTH * CELL_SIZE,
                                height=GRID_HEIGHT * CELL_SIZE, bg=BOARD_COLOR)
        self.canvas.pack(pady=20)

        # Рисуем сетку
        for i in range(GRID_WIDTH + 1):
            x = i * CELL_SIZE
            self.canvas.create_line(x, 0, x, GRID_HEIGHT * CELL_SIZE, fill=GRID_COLOR, width=2)

        for i in range(GRID_HEIGHT + 1):
            y = i * CELL_SIZE
            self.canvas.create_line(0, y, GRID_WIDTH * CELL_SIZE, y, fill=GRID_COLOR, width=2)

        # Создаем информационную метку
        self.info_label = tk.Label(self.window, text="", font=("Arial", 12))
        self.info_label.pack(pady=10)

        # Кнопка "Назад"
        back_button = tk.Button(self.window, text="Назад", command=self.show_main_menu,
                                bg="#f44336", fg="white", font=("Arial", 12))
        back_button.pack(pady=10)

        # Привязываем обработчик кликов
        def handle_click(event):
            col = event.x // CELL_SIZE
            row = event.y // CELL_SIZE

            if 0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH:
                if self.stage == 1:  # Фаза расстановки
                    self.place_stone(row, col)
                else:  # Фаза перемещения
                    self.handle_move(row, col)

        self.canvas.bind("<Button-1>", handle_click)

        # Отрисовываем начальное состояние
        self.draw_board()

    def show_main_menu(self):
        # Сброс состояния игры
        self.board = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        self.current_player = 0
        self.stage = 1
        self.stones_count = [0, 0]
        self.remaining_pairs = [NUM_STONES, NUM_STONES]
        self.stones_to_place = 2
        self.selected_stone = None

        for widget in self.window.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.window, bg="#f0f0f0")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Создание стильного меню
        menu_frame = tk.Frame(main_frame, bg="#ffffff", padx=40, pady=40)
        menu_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_label = tk.Label(menu_frame, text="Болотуду", font=("Arial", 24, "bold"), bg="#ffffff")
        title_label.pack(pady=(0, 30))

        button_style = {"font": ("Arial", 12), "width": 25, "pady": 10}

        tk.Button(menu_frame, text="Начать игру", command=self.setup_game_board,
                  bg="#4CAF50", fg="white", **button_style).pack(pady=5)

        tk.Button(menu_frame, text="Выход", command=self.window.quit,
                  bg="#f44336", fg="white", **button_style).pack(pady=5)

    def remove_stone(self, row, col):
        """Анимация удаления камня"""
        x = col * CELL_SIZE + CELL_SIZE // 2
        y = row * CELL_SIZE + CELL_SIZE // 2
        stone_color = PLAYER_COLORS[self.board[row][col]]

        # Анимация мигания
        for _ in range(3):
            # Мигание красным
            self.canvas.create_oval(x - CELL_SIZE // 3, y - CELL_SIZE // 3,
                                    x + CELL_SIZE // 3, y + CELL_SIZE // 3,
                                    fill="red", outline="yellow", width=3)
            self.window.update()
            self.window.after(100)  # Задержка 100мс

            # Возврат к исходному цвету
            self.canvas.create_oval(x - CELL_SIZE // 3, y - CELL_SIZE // 3,
                                    x + CELL_SIZE // 3, y + CELL_SIZE // 3,
                                    fill=stone_color, outline="black", width=1)
            self.window.update()
            self.window.after(100)  # Задержка 100мс

        # Анимация исчезновения с вращением
        for i in range(10):
            size = CELL_SIZE // 3 * (10 - i) // 10
            angle = i * 36  # 360 градусов / 10 шагов = 36 градусов на шаг

            # Создаем эффект вращения с помощью смещения
            offset_x = size * 0.2 * math.cos(math.radians(angle))
            offset_y = size * 0.2 * math.sin(math.radians(angle))

            self.canvas.create_oval(x - size + offset_x, y - size + offset_y,
                                    x + size + offset_x, y + size + offset_y,
                                    fill=stone_color, outline="black", width=1)

            # Добавляем эффект затухания цвета
            alpha = (10 - i) / 10
            fade_color = self.blend_colors(stone_color, BOARD_COLOR, alpha)

            self.canvas.create_oval(x - size + offset_x, y - size + offset_y,
                                    x + size + offset_x, y + size + offset_y,
                                    fill=fade_color, outline="black", width=1)

            self.window.update()
            self.window.after(50)  # Задержка 50мс

        # Удаляем камень
        self.board[row][col] = None
        self.stones_count[1 - self.current_player] -= 1
        self.draw_board()

    def blend_colors(self, color1, color2, alpha):
        """Смешивает два цвета с заданной прозрачностью"""
        # Преобразуем hex в RGB
        r1 = int(color1[1:3], 16)
        g1 = int(color1[3:5], 16)
        b1 = int(color1[5:7], 16)

        r2 = int(color2[1:3], 16)
        g2 = int(color2[3:5], 16)
        b2 = int(color2[5:7], 16)

        # Смешиваем цвета
        r = int(r1 * alpha + r2 * (1 - alpha))
        g = int(g1 * alpha + g2 * (1 - alpha))
        b = int(b1 * alpha + b2 * (1 - alpha))

        # Возвращаем hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def place_stone(self, row, col):
        # Размещение камня на поле
        if self.board[row][col] is None and self.remaining_pairs[self.current_player] > 0:
            if self.check_no_three_in_row(row, col):
                self.board[row][col] = self.current_player
                self.stones_count[self.current_player] += 1
                self.stones_to_place -= 1

                if self.stones_to_place == 0:
                    self.remaining_pairs[self.current_player] -= 1
                    self.stones_to_place = 2
                    self.next_turn()

                # Проверяем, закончилась ли фаза расстановки
                if sum(self.remaining_pairs) == 0:
                    self.stage = 2
                    messagebox.showinfo("Информация", "Начинается фаза перемещения камней!")

                self.draw_board()
        else:
            messagebox.showerror("Ошибка", "Недопустимый ход!")

    def handle_move(self, row, col):
        if self.selected_stone is None:
            # Выбор камня для перемещения
            if self.board[row][col] is not None and self.board[row][col] == self.current_player:
                self.selected_stone = (row, col)
                self.draw_board()
        else:
            # Перемещение выбранного камня
            if self.is_valid_move(self.selected_stone[0], self.selected_stone[1], row, col):
                old_row, old_col = self.selected_stone

                # Сохраняем старое состояние доски
                old_board = [row[:] for row in self.board]

                # Выполняем ход
                self.board[row][col] = self.board[old_row][old_col]
                self.board[old_row][old_col] = None
                self.selected_stone = None

                # Проверяем наличие тройки или четверки
                line_info = self.check_for_line(row, col)
                if line_info[0]:  # Если есть линия
                    adjacent_stones = self.get_adjacent_opponent_stones(row, col, line_info[1])
                    if adjacent_stones:
                        # Проверяем, что линия только что создана
                        old_line = self.check_for_line_at_position(row, col, old_board)
                        if not old_line[0]:  # Если линия новая
                            # Снимаем только один камень противника с анимацией
                            remove_row, remove_col = adjacent_stones[0]
                            self.remove_stone(remove_row, remove_col)

                # Проверяем условие окончания игры
                if self.stones_count[1 - self.current_player] <= 2:
                    winner = "Первый игрок" if self.current_player == 0 else "Второй игрок"
                    messagebox.showinfo("Конец игры", f"{winner} победил!")
                    self.show_main_menu()
                    return

                self.next_turn()
            else:
                self.selected_stone = None
                self.draw_board()
                messagebox.showerror("Ошибка", "Недопустимый ход!")

    def check_for_line_at_position(self, row, col, board):
        """Проверяет наличие линии на заданной доске"""
        player = board[row][col]
        if player is None:
            return (False, None)

        # Проверка по горизонтали
        count = 1
        # Влево
        c = col - 1
        while c >= 0 and board[row][c] == player:
            count += 1
            c -= 1
        # Вправо
        c = col + 1
        while c < GRID_WIDTH and board[row][c] == player:
            count += 1
            c += 1

        if count >= 3:
            return (True, "horizontal")

        # Проверка по вертикали
        count = 1
        # Вверх
        r = row - 1
        while r >= 0 and board[r][col] == player:
            count += 1
            r -= 1
        # Вниз
        r = row + 1
        while r < GRID_HEIGHT and board[r][col] == player:
            count += 1
            r += 1

        if count >= 3:
            return (True, "vertical")

        return (False, None)

    def check_for_line(self, row, col):
        """Проверяет наличие линии из 3 или 4 камней и возвращает (bool, direction)"""
        player = self.board[row][col]

        # Проверка по горизонтали
        count = 1
        # Влево
        c = col - 1
        while c >= 0 and self.board[row][c] == player:
            count += 1
            c -= 1
        # Вправо
        c = col + 1
        while c < GRID_WIDTH and self.board[row][c] == player:
            count += 1
            c += 1

        if count >= 3:
            return (True, "horizontal")

        # Проверка по вертикали
        count = 1
        # Вверх
        r = row - 1
        while r >= 0 and self.board[r][col] == player:
            count += 1
            r -= 1
        # Вниз
        r = row + 1
        while r < GRID_HEIGHT and self.board[r][col] == player:
            count += 1
            r += 1

        if count >= 3:
            return (True, "vertical")

        return (False, None)

    def is_valid_move(self, from_row, from_col, to_row, to_col):
        # Проверка возможности перемещения
        if self.board[to_row][to_col] is not None:
            return False

        # Проверка, что перемещение происходит на соседнюю клетку
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        return (row_diff == 1 and col_diff == 0) or (row_diff == 0 and col_diff == 1)

    def check_no_three_in_row(self, row, col):
        # Временно размещаем камень для проверки
        self.board[row][col] = self.current_player

        # Проверка по горизонтали
        count = 1
        # Влево
        c = col - 1
        while c >= 0 and self.board[row][c] == self.current_player:
            count += 1
            c -= 1
        # Вправо
        c = col + 1
        while c < GRID_WIDTH and self.board[row][c] == self.current_player:
            count += 1
            c += 1

        # Проверка по вертикали
        count_vert = 1
        # Вверх
        r = row - 1
        while r >= 0 and self.board[r][col] == self.current_player:
            count_vert += 1
            r -= 1
        # Вниз
        r = row + 1
        while r < GRID_HEIGHT and self.board[r][col] == self.current_player:
            count_vert += 1
            r += 1

        # Убираем временно размещенный камень
        self.board[row][col] = None

        return count < 3 and count_vert < 3

    def get_adjacent_opponent_stones(self, row, col, direction):
        """Получает список вражеских камней, примыкающих к линии"""
        player = self.board[row][col]
        opponent = 1 - player
        adjacent_stones = []

        if direction == "horizontal":
            # Находим начало и конец линии
            left = col
            while left > 0 and self.board[row][left - 1] == player:
                left -= 1
            right = col
            while right < GRID_WIDTH - 1 and self.board[row][right + 1] == player:
                right += 1

            # Проверяем камни слева и справа от линии
            if left > 0 and self.board[row][left - 1] == opponent:
                adjacent_stones.append((row, left - 1))
            if right < GRID_WIDTH - 1 and self.board[row][right + 1] == opponent:
                adjacent_stones.append((row, right + 1))

        elif direction == "vertical":
            # Находим верх и низ линии
            top = row
            while top > 0 and self.board[top - 1][col] == player:
                top -= 1
            bottom = row
            while bottom < GRID_HEIGHT - 1 and self.board[bottom + 1][col] == player:
                bottom += 1

            # Проверяем камни сверху и снизу от линии
            if top > 0 and self.board[top - 1][col] == opponent:
                adjacent_stones.append((top - 1, col))
            if bottom < GRID_HEIGHT - 1 and self.board[bottom + 1][col] == opponent:
                adjacent_stones.append((bottom + 1, col))

        return adjacent_stones

    def next_turn(self):
        """Переход хода к следующему игроку"""
        self.current_player = 1 - self.current_player
        self.draw_board()


if __name__ == "__main__":
    BolotuduGame()