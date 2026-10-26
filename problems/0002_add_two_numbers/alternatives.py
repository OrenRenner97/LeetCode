"""2. Add Two Numbers: альтернативные решения.

| # | Класс                  | Время       | Доп. память          | Комментарий                                     |
|---|------------------------|-------------|----------------------|-------------------------------------------------|
| 0 | Solution (solution.py) | O(max(m,n)) | O(1) + ответ         | оптимум: один проход, перенос, фиктивная голова |
| 1 | Compact                | O(max(m,n)) | O(1) + ответ         | то же, divmod + carry в условии цикла           |
| 2 | ViaInt                 | O(n^2)*     | O(n)                 | list → int → list; ломается на > 4300 цифрах    |
| 3 | Recursive              | O(max(m,n)) | O(max(m,n)) стек     | красиво, но RecursionError на ~1000 цифрах      |
| 4 | InPlace                | O(max(m,n)) | O(1) всего           | переиспользует узлы l1/l2: портит входные данные|

* int(str) и str(int) в CPython квадратичны по числу цифр.
"""
from typing import Optional

from solution import ListNode


class Compact:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        # carry в условии цикла: последний перенос обрабатывается внутри цикла, без отдельного if.
        # divmod(total, 10) заменяет ветку if total > 9 и работает для любого основания.
        dummy = tail = ListNode()
        carry = 0
        while l1 or l2 or carry:
            total = carry
            if l1:
                total += l1.val
                l1 = l1.next
            if l2:
                total += l2.val
                l2 = l2.next
            carry, digit = divmod(total, 10)
            tail.next = tail = ListNode(digit)  # присваивание слева направо: сначала tail.next, потом tail
        return dummy.next


class ViaInt:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        # «Читерский» путь: в Python int бесконечной длины, и в C++/Java (int64) это сразу переполнение.
        # Даже в Python есть потолок: int(str) с > 4300 цифрами → ValueError (защита от DoS, CVE-2020-10735, Python 3.11+).
        def to_int(node):
            digits = []
            while node:
                digits.append(str(node.val))
                node = node.next
            return int("".join(reversed(digits)))

        s = str(to_int(l1) + to_int(l2))
        dummy = tail = ListNode()
        for ch in reversed(s):
            tail.next = tail = ListNode(int(ch))
        return dummy.next


class Recursive:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode], carry: int = 0) -> Optional[ListNode]:
        # Каждый уровень рекурсии = один разряд. Стек растёт на длину числа:
        # лимит рекурсии Python ~1000, так что 100 цифр (LeetCode) ок, 10^4 уже нет.
        if not l1 and not l2 and not carry:
            return None
        total = carry + (l1.val if l1 else 0) + (l2.val if l2 else 0)
        node = ListNode(total % 10)
        node.next = self.addTwoNumbers(l1.next if l1 else None, l2.next if l2 else None, total // 10)
        return node


class InPlace:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        # Пишем сумму прямо в узлы l1. Когда l1 кончается, «пришиваем» хвост l2 и продолжаем в нём.
        # Новый узел создаётся максимум один раз: под финальный перенос.
        # Цена: входные списки испорчены. Допустимо, только если вызывающий их больше не использует.
        head = l1
        prev = None
        carry = 0
        while l1 or l2 or carry:
            if not l1:
                if l2:  # l1 кончился: продолжаем по хвосту l2
                    prev.next, l1, l2 = l2, l2, None
                else:  # остался только перенос
                    prev.next = l1 = ListNode(0)
            total = l1.val + carry
            if l2:
                total += l2.val
                l2 = l2.next
            carry, l1.val = divmod(total, 10)
            prev, l1 = l1, l1.next
        return head


ALL = {
    "Compact": Compact,
    "ViaInt": ViaInt,
    "Recursive": Recursive,
    "InPlace": InPlace,
}
