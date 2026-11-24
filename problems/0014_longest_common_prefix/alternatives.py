"""14. Longest Common Prefix: альтернативные решения.

n — число строк, m — длина ответа (общего префикса), S — суммарная длина всех строк.

| # | Класс                  | Время          | Память | Идея                                                                       |
|---|------------------------|----------------|--------|----------------------------------------------------------------------------|
| 0 | Solution (solution.py) | O(S)           | O(m)   | горизонтально: префикс сужается о каждую строку, посимвольно в Python      |
| 1 | HorizontalEarlyExit    | O(S)           | O(m)   | то же, но пустой префикс — сразу выход; сравнение срезом, а не по символам |
| 2 | VerticalZip            | O(n · m)       | O(n)   | по столбцам: zip(*strs), столбец не из одного символа — стоп                |
| 3 | MinMax                 | O(S)           | O(1)   | общий префикс всех = общий префикс лексикографических min и max            |
| 4 | StartswithShrink       | O(n · m²) худш. | O(m)  | пока строка не начинается с префикса — отрезаем по символу                 |
| 5 | BinarySearchLength     | O(S · log m)   | O(m)   | бинпоиск по длине: all(s.startswith(p)), сравнение строк на C            |
| 6 | NumpyMatrix            | O(n · L)       | O(n · L) | строки → матрица байт n × L, сравнение с первой строкой, первый «плохой» столбец |
"""
import numpy as np


class HorizontalEarlyExit:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        # Тот же горизонтальный проход, но: 1) строка уже начинается с префикса — ничего не делаем (startswith на C);
        # 2) иначе ищем расхождение; 3) префикс пуст — дальше смотреть незачем.
        prefix = strs[0]
        for word in strs:
            if word.startswith(prefix):
                continue
            k = min(len(prefix), len(word))
            i = 0
            while i < k and prefix[i] == word[i]:
                i += 1
            prefix = prefix[:i]
            if not prefix:
                break
        return prefix


class VerticalZip:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        # Столбец i — i-е символы всех строк. zip останавливается на самой короткой строке —
        # это и есть верхняя граница ответа. Первый неоднородный столбец — конец префикса.
        for i, column in enumerate(zip(*strs)):
            if len(set(column)) > 1:
                return strs[0][:i]
        return min(strs, key=len)


class MinMax:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        # Строки, отсортированные лексикографически: общий префикс всех — это общий префикс первой и последней.
        # Любая строка между ними начинается с того же, иначе нарушился бы порядок. Сортировать не нужно — min/max.
        # Так устроен os.path.commonprefix.
        lo, hi = min(strs), max(strs)
        for i, c in enumerate(lo):
            if c != hi[i]:
                return lo[:i]
        return lo


class StartswithShrink:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        # Самое короткое по коду: обрезаем префикс с конца, пока строка с него не начинается.
        # Худший случай квадратичен по длине (каждая проверка — O(m)), но startswith на C.
        prefix = strs[0]
        for word in strs:
            while not word.startswith(prefix):
                prefix = prefix[:-1]
            if not prefix:
                break
        return prefix


class BinarySearchLength:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        # «Длина L подходит» монотонно: если префикс длины L общий, то и любой короче. Бинпоиск по L,
        # проверка — all(s.startswith(p) …): само сравнение на C, цикл по строкам — в Python.
        first = min(strs, key=len)
        lo, hi = 0, len(first)          # ответ в [lo, hi]
        while lo < hi:
            mid = (lo + hi + 1) // 2
            p = first[:mid]
            if all(s.startswith(p) for s in strs):
                lo = mid
            else:
                hi = mid - 1
        return first[:lo]


class NumpyMatrix:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        # Строки фиксированной ширины 'S{L}' (короткие добиваются нулями) → матрица uint8 n × L.
        # Столбец «хороший», если совпадает с первой строкой во всех строках и это не добивка.
        # Нулевой байт добивки ≠ буква, поэтому конец любой строки тоже даст «плохой» столбец.
        arr = np.array(strs, dtype=np.bytes_)
        width = arr.dtype.itemsize
        if width == 0:
            return ""
        mat = arr.view(np.uint8).reshape(len(strs), width)
        bad = (mat != mat[0]).any(axis=0) | (mat[0] == 0)
        k = int(bad.argmax()) if bad.any() else width
        return strs[0][:k]


ALL = {
    "HorizontalEarlyExit": HorizontalEarlyExit,
    "VerticalZip": VerticalZip,
    "MinMax": MinMax,
    "StartswithShrink": StartswithShrink,
    "BinarySearchLength": BinarySearchLength,
    "NumpyMatrix": NumpyMatrix,
}
