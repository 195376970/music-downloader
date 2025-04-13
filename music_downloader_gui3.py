    def try_new_api_search(self, search_term, song_info):
        """尝试使用几个专业音乐解析API搜索"""
        try:
            self.log(f"尝试使用音乐解析API搜索: {search_term}")
            
            # 音乐解析API列表
            api_endpoints = [
                {
                    "url": f"https://api.yueliangjx.com/api/song/search?keywords={urllib.parse.quote(search_term)}&type=cloudmusic",
                    "json_path": ["data", "songs", 0, "url"],
                    "name_path": ["data", "songs", 0, "name"],
                    "artist_path": ["data", "songs", 0, "artist"]
                },
                {
                    "url": f"https://api.vvhan.com/api/music?type=song&name={urllib.parse.quote(search_term)}",
                    "json_path": ["url"],
                    "name_path": ["name"],
                    "artist_path": ["artist"]
                },
                {
                    "url": f"https://api.xingzhige.com/API/QQmusicVIP/?name={urllib.parse.quote(search_term)}",
                    "json_path": ["data", "url"],
                    "name_path": ["data", "name"],
                    "artist_path": ["data", "author"]
                },
                {
                    "url": f"https://api.injahow.cn/meting/?type=search&id={urllib.parse.quote(search_term)}",
                    "json_path": [0, "url"],
                    "name_path": [0, "title"],
                    "artist_path": [0, "author"]
                }
            ]
            
            # 尝试各个API
            for api in api_endpoints:
                try:
                    self.log(f"尝试API: {api['url'].split('?')[0]}")
                    
                    # 设置请求头
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'application/json, text/plain, */*',
                        'Referer': 'https://music.163.com/'
                    }
                    
                    # 发起请求
                    response = self.session.get(api['url'], headers=headers, timeout=10)
                    
                    # 检查响应
                    if response.status_code == 200:
                        try:
                            # 解析JSON
                            result = response.json()
                            
                            # 递归获取JSON路径
                            def get_json_path(json_obj, path):
                                if not path or not json_obj:
                                    return json_obj
                                if isinstance(path[0], int) and isinstance(json_obj, list) and len(json_obj) > path[0]:
                                    return get_json_path(json_obj[path[0]], path[1:])
                                if isinstance(json_obj, dict) and path[0] in json_obj:
                                    return get_json_path(json_obj[path[0]], path[1:])
                                return None
                            
                            # 获取歌曲信息
                            song_url = get_json_path(result, api['json_path'])
                            
                            if song_url:
                                # 获取名称和艺术家信息 (可能为空，使用搜索参数作为备选)
                                name = get_json_path(result, api['name_path']) or song_info['name']
                                artist = get_json_path(result, api['artist_path']) or song_info['artist']
                                
                                self.log(f"API返回音乐链接: {song_url}")
                                
                                # 准备下载信息
                                found_song_info = {
                                    'name': name,
                                    'artist': artist,
                                    'album': song_info['album'],
                                    'source': '音乐API解析'
                                }
                                
                                self.log(f"找到匹配歌曲: {found_song_info['name']} - {found_song_info['artist']} [来源: 音乐API解析]")
                                self.status_var.set(f"开始下载: {found_song_info['name']}")
                                
                                # 下载找到的歌曲
                                if self.download_file(song_url, found_song_info):
                                    return True
                        except Exception as e:
                            self.log(f"解析API响应出错: {str(e)}")
                            continue
                except Exception as e:
                    self.log(f"API请求出错: {str(e)}")
                    continue
            
            # 所有API尝试失败
            self.log("所有音乐解析API尝试失败")
            return False
            
        except Exception as e:
            self.log(f"音乐API解析搜索出错: {str(e)}")
            return False
    
    def try_find_douyin_music(self, search_term, song_info):
        """尝试抖音和其他短视频平台搜索歌曲"""
        try:
            self.log(f"尝试短视频平台搜索: {search_term}")
            
            # 构建搜索关键词
            search_keywords = [
                f"{search_term} 抖音",
                f"{search_term} tiktok",
                f"{search_term} 短视频BGM",
                f"{search_term} 歌曲音频",
                f"{song_info['name']} {song_info['artist']} 完整版"
            ]
            
            search_keyword = random.choice(search_keywords)
            self.log(f"使用关键词: {search_keyword}")
            
            # 使用特定搜索引擎搜索
            search_url = f"https://www.baidu.com/s?wd={urllib.parse.quote(search_keyword)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.baidu.com/'
            }
            
            self.log(f"搜索短视频平台资源...")
            
            response = self.session.get(search_url, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log(f"搜索请求失败: {response.status_code}")
                return False
            
            # 解析搜索结果
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取所有视频链接
            video_links = []
            
            # 查找抖音、快手等短视频平台链接
            for a in soup.find_all('a', href=True):
                href = a['href']
                if any(platform in href for platform in ['douyin.com', 'kuaishou.com', 'ixigua.com', 'bilibili.com']):
                    video_links.append(href)
            
            if not video_links:
                self.log("未找到短视频平台链接")
                return False
            
            self.log(f"找到 {len(video_links)} 个短视频平台链接")
            
            # 访问前三个视频链接尝试提取音频
            for video_link in video_links[:3]:
                try:
                    self.log(f"访问视频链接: {video_link}")
                    
                    # 访问视频页面
                    video_response = self.session.get(video_link, headers=headers, timeout=10)
                    if video_response.status_code != 200:
                        continue
                    
                    # 在视频页面中查找音频链接
                    music_urls = []
                    
                    # 查找JSON数据中的音频链接
                    json_matches = re.findall(r'"playAddr":"([^"]+)"', video_response.text)
                    music_urls.extend(json_matches)
                    
                    json_matches = re.findall(r'"playUrl":"([^"]+)"', video_response.text)
                    music_urls.extend(json_matches)
                    
                    json_matches = re.findall(r'"musicUrl":"([^"]+)"', video_response.text)
                    music_urls.extend(json_matches)
                    
                    # 查找m3u8链接
                    m3u8_matches = re.findall(r'(https?://[^"\'>\s]+\.m3u8[^"\'>\s]*)', video_response.text)
                    music_urls.extend(m3u8_matches)
                    
                    # 查找mp4链接
                    mp4_matches = re.findall(r'(https?://[^"\'>\s]+\.mp4[^"\'>\s]*)', video_response.text)
                    music_urls.extend(mp4_matches)
                    
                    # 查找mp3链接
                    mp3_matches = re.findall(r'(https?://[^"\'>\s]+\.mp3[^"\'>\s]*)', video_response.text)
                    music_urls.extend(mp3_matches)
                    
                    if not music_urls:
                        self.log("在视频页面中未找到音频链接")
                        continue
                    
                    # 去除重复项
                    music_urls = list(set(music_urls))
                    self.log(f"找到 {len(music_urls)} 个可能的音频链接")
                    
                    # 处理链接 (替换转义字符)
                    processed_urls = []
                    for url in music_urls:
                        url = url.replace('\\u002F', '/').replace('\\/', '/')
                        if url.startswith('//'):
                            url = 'https:' + url
                        processed_urls.append(url)
                    
                    # 尝试下载音频
                    for music_url in processed_urls:
                        try:
                            self.log(f"尝试下载音频: {music_url}")
                            
                            # 准备下载信息
                            found_song_info = {
                                'name': song_info['name'],
                                'artist': song_info['artist'],
                                'album': song_info['album'],
                                'source': '短视频平台'
                            }
                            
                            # 尝试下载
                            if self.download_file(music_url, found_song_info):
                                return True
                        except Exception as e:
                            self.log(f"下载音频失败: {str(e)}")
                            continue
                
                except Exception as e:
                    self.log(f"处理视频链接时出错: {str(e)}")
                    continue
            
            self.log("未能从短视频平台找到有效音频")
            return False
        
        except Exception as e:
            self.log(f"短视频平台搜索过程出错: {str(e)}")
            return False