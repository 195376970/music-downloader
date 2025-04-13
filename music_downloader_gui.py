#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from Crypto.Cipher import AES
import base64
import binascii
import json
import urllib.parse
from bs4 import BeautifulSoup
import random

class MusicDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("音乐下载工具")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # 初始化下载目录
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 初始化session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
        
        # 搜索引擎列表
        self.search_engines = [
            "https://www.haosou.com/s?q=",
            "https://cn.bing.com/search?q=",
            "https://www.sogou.com/web?query=",
            "https://www.so.com/s?q=",
            "https://yandex.com/search/?text=",
            "https://search.yahoo.com/search?p=",
            "https://duckduckgo.com/?q=",
            "https://www.baidu.com/s?wd="
        ]
        
        # 音乐资源站点匹配正则
        self.music_site_patterns = [
            # 常用音乐站点匹配模式
            r'(https?://[^"\'\s]+\.mp3)',
            r'(https?://[^"\'\s]+\.m4a)',
            r'(https?://[^"\'\s]+\.flac)',
            r'(https?://[^"\'\s]+\.wav)',
            r'(https?://[^"\'\s]+\.aac)',
            r'(https?://[^"\'\s]+\.ogg)',
            r'(https?://[^"\'\s]+/listen[^"\'\s]*)',
            r'(https?://[^"\'\s]+/song[^"\'\s]*)',
            r'(https?://[^"\'\s]+/track[^"\'\s]*)',
            r'(https?://[^"\'\s]+/music[^"\'\s]*)',
            r'(https?://[^"\'\s]+/download[^"\'\s]*)',
            r'(https?://[^"\'\s]+/play[^"\'\s]*)',
            r'(https?://[^"\'\s]+/audio[^"\'\s]*)'
        ]
        
        # 音乐平台网址匹配
        self.music_platforms = {
            "QQ音乐": r'y\.qq\.com/.*?/songDetail/.*?songId=(\w+)',
            "酷我音乐": r'kuwo\.cn/play_detail/(\d+)',
            "酷狗音乐": r'kugou\.com/song/#hash=([A-Za-z0-9]+)',
            "虾米音乐": r'xiami\.com/song/(\w+)',
            "千千音乐": r'music\.taihe\.com/song/(\d+)',
            "一听音乐": r'1ting\.com/player/.*?/player_(\d+)\.html',
            "咪咕音乐": r'music\.migu\.cn/.*?/song/(\d+)',
            "网易云音乐": r'music\.163\.com/.*?/song\?id=(\d+)',
            "5SING": r'5sing\.kugou\.com/\w+/(\d+)\.html',
            "Bandcamp": r'bandcamp\.com/track/(\w+)',
            "SoundCloud": r'soundcloud\.com/([^/]+)/([^/]+)',
            "街声音乐": r'streetvoice\.cn/.*?/songs/(\d+)',
            "音兔": r'yinyuetai\.com/video/(\d+)',
            "豆瓣音乐": r'music\.douban\.com/subject/(\d+)',
            "echo回声": r'app-echo\.com/sound/(\d+)',
            "听听": r'tingtingfm\.com/v/(\d+)'
        }
        
        # 增加通用音乐文件匹配正则
        self.audio_file_extensions = ['.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg', '.wma']
        
        # 创建UI
        self.create_widgets()
    
    def create_widgets(self):
        # 顶部框架
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # URL输入
        ttk.Label(top_frame, text="歌曲链接/ID:").pack(side=tk.LEFT)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(top_frame, textvariable=self.url_var, width=50)
        url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        url_entry.bind("<Return>", lambda e: self.start_download())
        
        # 下载按钮
        self.download_btn = ttk.Button(top_frame, text="下载", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        # 选择目录按钮
        self.dir_btn = ttk.Button(top_frame, text="选择目录", command=self.select_directory)
        self.dir_btn.pack(side=tk.LEFT, padx=5)
        
        # 中间框架
        mid_frame = ttk.Frame(self.root, padding="10")
        mid_frame.pack(fill=tk.X)
        
        # 当前保存目录
        ttk.Label(mid_frame, text="保存目录:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar(value=self.output_dir)
        dir_label = ttk.Label(mid_frame, textvariable=self.dir_var, foreground="blue")
        dir_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 搜索框架
        search_frame = ttk.LabelFrame(self.root, text="搜索模式", padding="10")
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 搜索模式选择
        self.search_mode = tk.IntVar(value=0)
        ttk.Radiobutton(search_frame, text="先尝试网易云，失败再全网搜索", variable=self.search_mode, value=0).pack(anchor=tk.W)
        ttk.Radiobutton(search_frame, text="直接全网搜索", variable=self.search_mode, value=1).pack(anchor=tk.W)
        
        # 下方框架
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志展示
        ttk.Label(bottom_frame, text="下载日志:").pack(anchor=tk.W)
        
        # 创建日志文本框
        self.log_text = tk.Text(bottom_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 给日志文本框添加滚动条
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=10)
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 添加初始说明信息
        self.log("欢迎使用音乐下载工具!")
        self.log("1. 输入网易云音乐链接或歌曲ID，点击'下载'")
        self.log("2. 程序会尝试从网易云下载，如果有版权限制，将自动全网搜索")
        self.log("3. 您也可以选择'直接全网搜索'模式跳过网易云音乐检查")
        self.log("4. 下载完成的歌曲将保存在'下载'目录")
        self.log("-" * 60)
    
    def log(self, message):
        """添加日志到文本框"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)  # 自动滚动到底部
    
    def select_directory(self):
        """选择保存目录"""
        dir_path = filedialog.askdirectory(initialdir=self.output_dir)
        if dir_path:
            self.output_dir = dir_path
            self.dir_var.set(self.output_dir)
            self.log(f"已更改保存目录: {self.output_dir}")
    
    def start_download(self):
        """开始下载"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入歌曲链接或ID")
            return
        
        # 禁用按钮，防止重复点击
        self.download_btn.config(state=tk.DISABLED)
        self.dir_btn.config(state=tk.DISABLED)
        
        # 重置进度条
        self.progress['value'] = 0
        
        # 更新状态
        self.status_var.set("正在处理...")
        
        # 在新线程中下载，避免UI卡顿
        threading.Thread(target=self.download_thread, args=(url,), daemon=True).start()
    
    def download_thread(self, url):
        """下载线程"""
        try:
            self.log(f"开始处理: {url}")
            
            # 获取歌曲ID
            song_id = None
            if url.startswith('http'):
                self.log("从链接中提取歌曲ID...")
                url = url.split('&uct')[0] if '&uct' in url else url
                song_id = self.extract_song_id(url)
            else:
                self.log("使用输入的歌曲ID...")
                song_id = url if url.isdigit() else None
            
            if not song_id:
                self.log("无法从输入中提取歌曲ID，请确保输入正确的网易云音乐链接或ID")
                self.status_var.set("错误: 无效的链接或ID")
                self.reset_buttons()
                return
            
            self.log(f"获取歌曲ID: {song_id}")
            
            # 获取歌曲信息
            self.log("获取歌曲信息...")
            song_info = self.get_song_info(song_id)
            if not song_info:
                self.log(f"无法获取歌曲信息，ID: {song_id}")
                self.status_var.set("错误: 无法获取歌曲信息")
                self.reset_buttons()
                return
            
            self.log(f"获取歌曲信息成功: {song_info['name']} - {song_info['artist']}")
            
            # 根据模式决定是否尝试网易云下载
            direct_search = (self.search_mode.get() == 1)
            
            if not direct_search:
                # 尝试从网易云获取下载链接
                self.log("尝试从网易云音乐获取下载链接...")
                song_url = self.get_song_url(song_id)
                
                if song_url:
                    self.log("成功获取网易云音乐下载链接")
                    self.status_var.set(f"开始下载: {song_info['name']}")
                    self.download_file(song_url, song_info)
                    return
                
                self.log("网易云音乐无法提供下载链接，可能存在版权限制")
            else:
                self.log("跳过网易云音乐检查，直接进行全网搜索")
            
            # 开始全网搜索
            self.status_var.set("正在全网搜索...")
            self.log(f"开始全网搜索: {song_info['name']} - {song_info['artist']}")
            
            # 执行搜索
            search_term = f"{song_info['name']} {song_info['artist']}"
            self.search_and_download(search_term, song_info)
        
        except Exception as e:
            import traceback
            error_msg = str(e)
            trace = traceback.format_exc()
            self.log(f"下载出错: {error_msg}")
            self.log(f"错误详情: {trace}")
            self.status_var.set(f"错误: {error_msg}")
        
        finally:
            self.reset_buttons()
    
    def extract_song_id(self, url):
        """从网易云音乐链接中提取歌曲ID"""
        if url.isdigit():
            return url
        
        # URL正则匹配
        pattern = r'song\?id=(\d+)|/song/(\d+)|song/(\d+)'
        match = re.search(pattern, url)
        if match:
            for group in match.groups():
                if group:
                    return group
        return None
    
    def get_song_info(self, song_id):
        """获取歌曲信息"""
        url = f'https://music.163.com/api/song/detail/?id={song_id}&ids=[{song_id}]'
        
        try:
            response = self.session.get(url)
            result = response.json()
            
            if 'songs' in result and result['songs']:
                song = result['songs'][0]
                
                # 处理艺术家信息
                artists = []
                if 'ar' in song:  # 新版API
                    artists = [ar['name'] for ar in song['ar']]
                elif 'artists' in song:  # 旧版API
                    artists = [ar['name'] for ar in song['artists']]
                
                artist_name = '、'.join(artists) if artists else '未知艺术家'
                
                return {
                    'name': song.get('name', '未知歌曲'),
                    'artist': artist_name,
                    'album': song.get('al', {}).get('name', song.get('album', {}).get('name', '未知专辑'))
                }
            
            return None
        except Exception as e:
            self.log(f"获取歌曲信息出错: {str(e)}")
            return None
    
    def create_secret_key(self, size):
        """生成随机密钥"""
        import random
        return ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(size))
    
    def aes_encrypt(self, text, key):
        """AES加密"""
        pad = 16 - len(text) % 16
        text = text + chr(pad) * pad
        encryptor = AES.new(key.encode('utf-8'), AES.MODE_CBC, b'0102030405060708')
        encrypt_text = encryptor.encrypt(text.encode('utf-8'))
        encrypt_text = base64.b64encode(encrypt_text).decode('utf-8')
        return encrypt_text
    
    def rsa_encrypt(self, text):
        """RSA加密"""
        text = text[::-1]
        pub_key = '010001'
        modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        rs = pow(int(binascii.hexlify(text.encode('utf-8')), 16), int(pub_key, 16), int(modulus, 16))
        return format(rs, 'x').zfill(256)
    
    def aes_rsa_encrypt(self, text):
        """网易云音乐使用的加密方法"""
        first_key = '0CoJUm6Qyw8W8jud'
        second_key = self.create_secret_key(16)
        h_encText = self.aes_encrypt(text, first_key)
        h_encText = self.aes_encrypt(h_encText, second_key)
        return {'params': h_encText, 'encSecKey': self.rsa_encrypt(second_key)}
    
    def get_song_url(self, song_id):
        """获取歌曲下载链接"""
        url = 'https://music.163.com/weapi/song/enhance/player/url/v1'
        
        data = {
            'ids': [song_id],
            'level': 'standard',
            'encodeType': 'aac',
            'csrf_token': ''
        }
        
        try:
            encrypted_data = self.aes_rsa_encrypt(json.dumps(data))
            response = self.session.post(url, data=encrypted_data)
            result = response.json()
            
            if result.get('code') == 200 and result.get('data') and len(result['data']) > 0:
                song_url = result['data'][0].get('url')
                if song_url:
                    return song_url
            
            return None
        except Exception as e:
            self.log(f"获取下载链接出错: {str(e)}")
            return None