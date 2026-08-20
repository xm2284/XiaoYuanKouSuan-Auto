# -*- coding: utf-8 -*-
"""
连续自动答题循环（提速版）：
一次截图同时识别【当前题（上方）】和【下一道题（下方灰色）】，
下一题的答案提前算好，题目一更新立刻作答，减少等待。
自动跳过未更新的题目，连续 15 次识别不到新题则自动结束。
"""
import time

import xiaoyuan_auto as auto

if __name__ == '__main__':
    answered = 0
    idle = 0                 # 连续没识别到新题的次数（结束条件）
    last_top = None          # 最近一次已作答的当前题
    pending = None           # 预计算的下一题 (数字, 答案)
    print('开始连续自动答题（提速版，按 Ctrl+C 可手动停止）')
    while idle < 15:
        try:
            img = auto.take_screenshot()
            if img is None:
                idle += 1
                time.sleep(0.5)
                continue

            # 一次识别当前题 + 下一道题
            cur, nxt = auto.recognize_both_rows(img)

            if cur and cur != last_top:
                # 当前题是新的：优先用预计算答案，避免重新比较等待
                if pending and cur == pending[0]:
                    ans = pending[1]
                    print(f'当前题命中预计算: {cur} -> {ans}')
                else:
                    ans = auto.calculate_comparison(cur)
                auto.input_answer(ans)
                answered += 1
                print(f'已答 {answered} 题: {cur} -> {ans}', flush=True)
                last_top = cur
                idle = 0

            if nxt:
                # 预计算下一道题的答案
                pending = (nxt, auto.calculate_comparison(nxt))

            time.sleep(0.15)
        except KeyboardInterrupt:
            print('手动停止')
            break
    print(f'循环结束：连续 {idle} 次未识别到新题目，共作答 {answered} 题')
