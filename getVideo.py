"""
# 利用python爬虫(requests)进行在线视频的下载
下载类型：m3u8 and mp4

实现对在线视频的下载，具体包括：
（1）多线程下载
（2）ts视频文件合并
（3）进度条显示
（4）日志记录
（5）重复下载提示


"""


import re
import requests
import time
import os, sys
import shutil  # os.mkdir('要清空的文件夹名')
import threading
import math

time_start = time.time()


class DownloadVideo:
    def __init__(self, url_m3u8):
        self.url_m3u8 = url_m3u8
        self.url = re.split(r'[/]', self.url_m3u8)
        self.pre_url = '/'.join(self.url[:len(self.url) - 1])

        self.count_line = 0
        self.count = 0

        # 下载路径记录，写入日志中
        self.path_log = ''
        self.num = 0

        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
        }

        # 存储下载的TS文件
        if not os.path.exists('videoTS'):
            os.mkdir('videoTS')

        # 存储m3u8的8个分块文件
        if not os.path.exists('filedir'):
            os.mkdir('filedir')

        # 存储mp4文件的目录
        if not os.path.exists('videoMP4'):
            os.mkdir('videoMP4')

    # 获取视频流切片m3u8的对应网址，下载视频切片就按照文件内的网址进行下载
    def get_m3u8(self):
        global response
        try:
            response = requests.get(url=self.url_m3u8, headers=self.headers)
        except Exception as e:
            print(e)
            exit()
        response_data = response.text
        if response.status_code == 200:
            with open('data.txt', 'w', encoding='utf-8') as fp:
                fp.write(response_data)
            print('链接获取完成！')
        else:
            print('网址解析出错！')
            exit()

    # 对文件的视频流地址进行提取并划分为8个文件，方便启用八线程下载
    def spl_file(self):
        # 对m3u8文件内容的行数和下载链接数进行统计，方便后续的文件分块和计算下载进度
        with open('data.txt', 'r', encoding='utf-8') as fp:
            while True:
                self.count_line += 1
                link = fp.readline()
                if not link:
                    break
                if link[:4] != "#EXT":
                    self.count += 1

        with open('data.txt', 'r', encoding='utf-8') as fp:
            flag, num = 0, 1
            while True:
                link = fp.readline()
                if not link:
                    break
                filename = 'filedir/' + 'thread' + str(num)
                with open(filename, 'a') as fp1:
                    fp1.write(link)
                flag += 1
                n = math.ceil(self.count_line / 8)  # 分为8个文件，方便8线程下载
                if flag == n:
                    flag = 0
                    num += 1

    # 根据获取的视频切片链接下载视频切片
    def get_video_m3u8(self, *args):
        filename, num = args[0], args[1]
        try:  # 处理m3u8内容少，不够8个线程时的异常
            with open(filename, 'r', encoding='utf-8') as fp:
                while True:
                    link = fp.readline()
                    if not link:
                        break
                    if link[:4] != "#EXT":  # 提取出下载链接的行
                        if link[:4] != 'hhtp':
                            re_link = self.pre_url + '/' + link[:len(link) - 1]  # 去掉换行符
                        else:
                            re_link = link[:len(link) - 1]
                        tmp = str(time.time()).split('.', 2)  # 以下载时间对视频片段进行排序
                        # 为了保证视频切片有序，需要依照每个线程的进行变换，如线程1，编号1+下载时间.ts，线程2，编号2+下载时间.ts
                        tsName = 'videoTS/' + str(num) + '-' + ''.join(tmp) + '.ts'
                        fp_video = open(tsName, 'wb')
                        response = requests.get(url=re_link, headers=self.headers)
                        response_video = response.content
                        if response.status_code != 200:
                            print('下载出错！')
                            exit()
                        fp_video.write(response_video)
                        fp_video.close()
        except Exception as e:
            print(e)

    """
    下载进度条，用来显示下载进度
    预先在spl_file()计算下载的总文件数：self.count
    不停的监控已下载到文件夹的文件数量：progress
    下载进度：p=progress / self.count
    """

    def progress_bar(self):
        start = time.perf_counter()
        while True:
            list_ts_path = os.listdir('videoTS')
            progress = len(list_ts_path)
            p = math.ceil((progress / self.count) * 100)
            dur = time.perf_counter() - start

            print("\r", end="")
            print("下载进度: {}%: ".format(p), "▋" * (p // 2), "{:.2f}s".format(dur), end="")
            sys.stdout.flush()
            time.sleep(0.05)
            if p == 100:
                break
        print()

    # 合并所有的ts文件为一个mp4文件
    def merge_ts_video(self):
        all_ts_dir = 'videoTS'
        ran_num = ''.join(str(time.time()).split('.', 2))
        merge_ts_path = 'videoMP4\\' + 'video' + ran_num + '.mp4'

        # 列出所有的ts文件，以列表存储
        list_ts_path = os.listdir(all_ts_dir)
        with open(merge_ts_path, 'ab') as fp:
            for i in list_ts_path:
                complete_ts_path = os.path.join(all_ts_dir, i)
                fp.write(open(complete_ts_path, 'rb').read())
        self.path_log = os.path.join(os.getcwd(), merge_ts_path)
        print('视频合并完成！视频路径：{0}'.format(self.path_log))

    # 下载日志，为了对每行进行编号，每次日志记录为一行，为了得到本行的行号，需要知道上一行的行号，+1操作后即是本行行号
    # 同时，为了节省读取文件时间，每次获取上一行的行号，需要对日志文件从后向前读取最后一行，这里利用seek()方法
    """
    seek()讲解：
    1、fileObject.seek(offset[, whence])
    2、offset -- 开始的偏移量，也就是代表需要移动偏移的字节数
    3、whence：可选，默认值为 0。给offset参数一个定义，表示要从哪个位置开始偏移；
    0代表从文件开头开始算起，1代表从当前位置开始算起，2代表从文件末尾算起。
    """

    def download_log(self):
        if not os.path.exists('log.txt'):
            with open('log.txt', 'a', encoding='utf-8') as fp1:
                fp1.write('##### download log ##### \n')
                fp1.write('0: 时间\t\t路径\t\t网址\n')

        try:
            with open('log.txt', 'rb') as fp2:  # 打开文件
                off = -10  # 设置偏移量
                while True:
                    if os.path.getsize('log.txt') == 0:
                        break

                    fp2.seek(off, 2)
                    lines = fp2.readlines()  # 读取文件指针范围内所有行
                    if len(lines) >= 2:  # 判断是否最后至少有两行，这样保证了最后一行是完整的
                        last_line = lines[-1]  # 取最后一行
                        break
                    # 如果off为5时得到的readlines只有一行内容，那么不能保证最后一行是完整的
                    # 所以off翻倍重新运行，直到readlines不止一行
                    off *= 2
                try:
                    self.num = str(last_line.decode())[:1]
                    if int(self.num) >= 100:
                        with open('log.txt', 'w', encoding='utf-8') as f:
                            f.write('##### download log ##### \n')
                            f.write('0: 时间\t\t路径\t\t网址\n')
                        self.num = 0
                except Exception as e:
                    pass
        except Exception as e:
            pass

        with open('log.txt', 'a', encoding='utf-8') as fp3:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            download_url = self.url_m3u8
            line_num = str(int(self.num) + 1) + ': '
            down_log = timestamp + '  ' + self.path_log + '  ' + download_url
            fp3.write(line_num + down_log + '\n')

    # 验证视频是否重复下载
    def break_point(self):
        # 首先对链接视频是否已经存在做一下验证，若已经存在提醒用户，不存在则下载
        try:  # 处理首次使用没有日志文件的异常
            with open('log.txt', 'r', encoding='utf-8') as fp:
                fp.readline()
                fp.readline()
                while True:
                    log_info = fp.readline()
                    if not log_info:
                        break
                    list_log_info = re.split(r'[ ]', log_info[:len(log_info) - 1])
                    if self.url_m3u8 == list_log_info[-1]:
                        if os.path.exists(list_log_info[-3]):
                            print('视频存在：', list_log_info[-3])
                            choose = input('是否重新下载！(1确认/其它取消)：')
                            if choose == '1':
                                pass
                            else:
                                exit()
                            break
                        else:
                            pass
        except Exception as e:
            pass

    """以下是对直接有mp4文件地址的视频进行下载的操作"""
    # 直接针对mp4链接视频的获取
    def get_video_mp4(self):
        mp4_path = 'videoMP4\\' + 'video' + ''.join(str(time.time()).split('.', 2)) + '.mp4'
        # stream=True 意味着，当函数返回时，仅响应标头被下载，响应主体不会
        try:
            response_head = requests.get(url=self.url_m3u8, stream=True, headers=self.headers)
        except Exception as e:
            print(e)
            exit()

        # 判断是否有正确的响应，如没有正确响应则说明url出错，不能正确下载，退出程序
        if response_head.status_code != 200:
            print('下载出错！')
            exit()

        # 获取响应头中的文件大小
        length = float(response_head.headers['content-length'])

        # 下载文件，对文件进行分块下载，每次512kb，方便对文件目录实时读取获得已下载的大小
        def write_video():
            count = 0
            with open(mp4_path, 'wb') as fp:
                for chunk in response_head.iter_content(chunk_size=512):
                    if chunk:
                        fp.write(chunk)
                        count += len(chunk)

        # 计算下载进度，用已下载的文件大小/文件总的大小
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
        self.path_log = os.path.join(os.getcwd(), mp4_path)
        print('视频合并完成！视频路径：{0}'.format(self.path_log))


import time


def printer(text, delay=0.1):
    """打字机效果"""

    for ch in text:
        print(ch, end='', flush=True)
        time.sleep(delay)


if __name__ == '__main__':
    # 开始时对下载路径存储的文件夹进行清空
    try:
        shutil.rmtree('filedir')
        shutil.rmtree('videoTS')
    except Exception as error:
        pass
    time.sleep(0.02)

    print('<<=======================<Download Video>=======================>>')
    printer('>^_^<>>>>>>>>>>>>>>>>>>>^_^<<按提示操作>>^_^<<<<<<<<<<<<<<<<<<>^_^<')
    print()
    home_choose = input('选择下载类型(1、MP4 || 2、M3U8):')
    while True:
        if home_choose == '1':
            url = input('请输入URL地址(MP4):')
            down = DownloadVideo(url)
            down.break_point()

            down.get_video_mp4()

            # 下载成功，写入下载日志
            down.download_log()
            break
        elif home_choose == '2':
            url = input('请输入URL地址(m3u8):')
            down = DownloadVideo(url)

            down.break_point()
            down.get_m3u8()
            down.spl_file()
            time.sleep(0.1)

            #  创建8个下载线程进行下载
            t = []
            for i in range(1, 9):
                t.append(threading.Thread(target=down.get_video_m3u8, args=('filedir/thread' + str(i), i,)))
            for i in range(8):
                t[i].start()
            down.progress_bar()
            for i in range(8):
                t[i].join()

            # 进行ts视频合并
            time.sleep(0.5)
            down.merge_ts_video()

            # 下载成功，写入下载日志
            down.download_log()
            break
        else:
            print('！！！输入有误，请重新选择！！！')
            home_choose = input('选择下载类型(1、MP4 || 2、M3U8):')
