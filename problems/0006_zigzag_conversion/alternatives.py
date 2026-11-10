"""6. Zigzag Conversion: альтернативные решения.

n = длина строки, r = numRows, T = 2(r - 1) — период зигзага (вниз r - 1 шагов, вверх r - 1).

| # | Класс                  | Время      | Память  | Идея                                                          |
|---|------------------------|------------|---------|---------------------------------------------------------------|
| 0 | Solution (solution.py) | O(n²/r)*   | O(n)    | строки в dict, `+=` по символу, знак шага меняется на краях   |
| 1 | Matrix                 | Θ(n·r)     | Θ(n·r)  | честно рисуем зигзаг в сетке r × столбцы, читаем построчно    |
| 2 | RowsList               | O(n)       | O(n)    | та же симуляция, но список списков + один join                |
| 3 | CycleIndex             | O(n)       | O(n)    | без симуляции: в строке i символы j·T + i и j·T + T - i       |
| 4 | SortByRow              | O(n log n) | O(n)    | номер строки — функция индекса; стабильная сортировка по нему |
| 5 | SliceInterleave        | O(n)       | O(n)    | строка i = два среза с шагом T, перемежаем их — всё на C      |

* `d[k] += ch` копирует строку: значение держат и dict, и стек, поэтому CPython
  не может дописать на месте. Каждая строка длины ~n/r собирается за ~(n/r)²/2.
"""


class Matrix:
    def convert(self, s: str, numRows: int) -> str:
        # Буквально как на картинке: r строк, столбцов ≤ n. Пустые клетки — None.
        # Память и время Θ(n·r): при r = 1000 и n = 1000 это миллион клеток ради 1000 букв.
        if numRows == 1:
            return s
        grid = [[None] * len(s) for _ in range(numRows)]
        row = col = 0
        down = True
        for ch in s:
            grid[row][col] = ch
            if down:
                if row == numRows - 1:
                    down = False
                    row -= 1
                    col += 1
                else:
                    row += 1
            elif row == 0:
                down = True
                row += 1
            else:
                row -= 1
                col += 1
        return "".join(ch for line in grid for ch in line if ch is not None)


class RowsList:
    def convert(self, s: str, numRows: int) -> str:
        # Та же симуляция, что у Solution, но: списки вместо строк (append — O(1)),
        # и края проверяются заранее, а не через «случайно сработавший» else.
        if numRows == 1 or numRows >= len(s):
            return s
        rows = [[] for _ in range(numRows)]
        row, step = 0, 1
        for ch in s:
            rows[row].append(ch)
            if row == 0:
                step = 1
            elif row == numRows - 1:
                step = -1
            row += step
        return "".join("".join(r) for r in rows)


class CycleIndex:
    def convert(self, s: str, numRows: int) -> str:
        # Период T = 2(r - 1). В строке i лежат индексы j·T + i («вертикаль»)
        # и, для средних строк, j·T + T - i («диагональ»). Идём по строкам и собираем.
        n = len(s)
        if numRows == 1 or numRows >= n:
            return s
        cycle = 2 * (numRows - 1)
        out = []
        for i in range(numRows):
            for j in range(i, n, cycle):
                out.append(s[j])
                diag = j + cycle - 2 * i
                if 0 < i < numRows - 1 and diag < n:
                    out.append(s[diag])
        return "".join(out)


class SortByRow:
    def convert(self, s: str, numRows: int) -> str:
        # Строка символа k: m = k mod T, row = min(m, T - m). Порядок вывода —
        # по строке, внутри строки — по индексу, а это ровно стабильная сортировка по row.
        n = len(s)
        if numRows == 1 or numRows >= n:
            return s
        cycle = 2 * (numRows - 1)
        order = sorted(range(n), key=lambda k: min(k % cycle, cycle - k % cycle))
        return "".join(s[k] for k in order)


class SliceInterleave:
    def convert(self, s: str, numRows: int) -> str:
        # Строка 0 — s[::T], последняя — s[r-1::T]. Средняя строка i — это два среза
        # s[i::T] и s[T-i::T], перемежающихся через один (вертикаль, диагональ, вертикаль...).
        # Вертикальный срез начинается раньше, поэтому он длиннее диагонального на 0 или 1.
        # Перемежаем присваиванием в срезы списка: Python-цикла по символам нет вообще.
        if numRows == 1 or numRows >= len(s):
            return s
        cycle = 2 * (numRows - 1)
        parts = [s[::cycle]]
        for i in range(1, numRows - 1):
            vert, diag = s[i::cycle], s[cycle - i::cycle]
            merged = [""] * (len(vert) + len(diag))
            merged[::2] = vert
            merged[1::2] = diag
            parts.append("".join(merged))
        parts.append(s[numRows - 1::cycle])
        return "".join(parts)


ALL = {
    "Matrix": Matrix,
    "RowsList": RowsList,
    "CycleIndex": CycleIndex,
    "SortByRow": SortByRow,
    "SliceInterleave": SliceInterleave,
}
