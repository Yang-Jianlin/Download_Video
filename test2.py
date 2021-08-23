# -*- coding: utf-8 -*-

import time


def printer(text, delay=0.2):
    """打字机效果"""

    for ch in text:
        print(ch, end='', flush=True)
        time.sleep(delay)


printer('玄铁重剑，是金庸小说笔下第一神剑，持之则无敌于天下。')

