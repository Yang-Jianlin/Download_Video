import requests
import time
import os
import threading
import math
import sys


"""
测试链接：
http://v.cztvcloud.com//channel_new/zjstv_zbs/vod/2021/07/16/a5e2d16d8ed44088868c4aa3dff701b4/26473da3e0da4adf93db6c3264be29fc_H264_500K_MP4.mp4
http://v.cztvcloud.com//channel_new/zjstv_zbs/vod/2021/08/20/b74f5ba22a2a4a27b0b80674f76e3a3e/ee6debb6d8df49deb34482e78cfbd2a0_H264_1500K_MP4.mp4
http://v.live.hndt.com/video/20200429/fd3af33e08bf4fa79ec623247d442811/cloudv-transfer/555555550069oo3s5556626513122n8p_90251d9983624740b3c400dd5d2d7fd8_0_4.m3u8
https://dh5.cntv.myhwcdn.cn/asp/h5e/hls/1200/0303000a/3/default/6b87a64ac790470b9a187e6cea67b2b7/1200.m3u8
https://dh5.cntv.baishancdnx.cn/asp/h5e/hls/1200/0303000a/3/default/5adda44d8b5542a4a59c86bb0828fd20/1200.m3u8
https://dh5.cntv.qcloudcdn.com/asp/h5e/hls/1200/0303000a/3/default/661b9862df414a53acceef098755fed5/1200.m3u8
"""


class F:
    def __init__(self):
        self.url_m3u8 = 'http://v.cztvcloud.com//channel_new/zjstv_zbs/vod/2021/08/20/b74f5ba22a2a4a27b0b80674f76e3a3e/ee6debb6d8df49deb34482e78cfbd2a0_H264_1500K_MP4.mp4'
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
        }

    def get_video_mp4(self):
        mp4_path = 'videoMP4\\' + 'video' + ''.join(str(time.time()).split('.', 2)) + '.mp4'
        response_head = requests.get(url=self.url_m3u8, stream=True, headers=self.headers)

        if response_head.status_code != 200:
            print('下载出错！')
            exit()

        length = float(response_head.headers['content-length'])

        def write_video():
            count = 0
            with open(mp4_path, 'wb') as fp:
                for chunk in response_head.iter_content(chunk_size=512):
                    if chunk:
                        fp.write(chunk)
                        count += len(chunk)

        def progress_bar():
            start = time.perf_counter()
            while True:
                down_size = os.path.getsize(mp4_path)
                p = math.ceil((down_size / length) * 100)
                dur = time.perf_counter() - start

                print("\r", end="")
                print("下载进度: {}%: ".format(p), "▋" * (p // 2), "{:.2f}s".format(dur), end="")
                sys.stdout.flush()
                time.sleep(0.05)
                if p == 100:
                    break
            print()

        t1 = threading.Thread(target=write_video)
        t1.start()
        progress_bar()
        t1.join()


f = F()
f.get_video_mp4()
