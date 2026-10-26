# 2. Add Two Numbers — https://leetcode.com/problems/add-two-numbers/
#
# Даны два непустых связных списка, представляющих неотрицательные целые числа.
# Цифры хранятся в ОБРАТНОМ порядке, в каждом узле одна цифра.
# Сложить два числа и вернуть сумму тоже в виде связного списка (в том же формате).
# Ведущих нулей нет, кроме самого числа 0.
#
# Example 1: l1 = [2,4,3], l2 = [5,6,4]          -> [7,0,8]           (342 + 465 = 807)
# Example 2: l1 = [0], l2 = [0]                  -> [0]
# Example 3: l1 = [9,9,9,9,9,9,9], l2 = [9,9,9,9] -> [8,9,9,9,0,0,0,1]
#
# Constraints: в каждом списке 1..100 узлов, 0 <= Node.val <= 9, ведущих нулей нет.
from typing import List, Optional


# Definition for singly-linked list (как на LeetCode).
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode()
        tail = dummy
        carry = 0
        while l1 or l2:
            total = carry
            if l1:
                total += l1.val
                l1 = l1.next
            if l2:
                total += l2.val
                l2 = l2.next
            if total > 9:
                digit = total - 10
                carry = 1
            else:
                digit = total
                carry = 0
            tail.next = ListNode(digit)
            tail = tail.next
        if carry > 0:
            tail.next = ListNode(carry)
        return dummy.next


# ---------- хелперы для проверки (на LeetCode их нет) ----------
def build(digits: List[int]) -> Optional[ListNode]:
    head = None
    for d in reversed(digits):
        head = ListNode(d, head)
    return head


def to_list(node: Optional[ListNode]) -> List[int]:
    out = []
    while node:
        out.append(node.val)
        node = node.next
    return out


if __name__ == "__main__":
    s = Solution()
    assert to_list(s.addTwoNumbers(build([2, 4, 3]), build([5, 6, 4]))) == [7, 0, 8]
    assert to_list(s.addTwoNumbers(build([0]), build([0]))) == [0]
    assert to_list(s.addTwoNumbers(build([9, 9, 9, 9, 9, 9, 9]), build([9, 9, 9, 9]))) == [8, 9, 9, 9, 0, 0, 0, 1]
    print("OK")
