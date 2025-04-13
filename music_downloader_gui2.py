    def search_and_download(self, search_term, song_info):
        """全网搜索和下载"""
        try:
            self.log(f"开始全网搜索: {search_term}")
            
            # 尝试专用平台搜索
            self.log("尝试从音乐平台搜索...")
            
            # 1. 先尝试新歌热门平台搜索 (针对最新流行歌曲)
            hot_platforms_success = self.try_hot_music_platforms(search_term, song_info)
            if hot_platforms_success:
                return True
            
            # 2. 尝试音乐解析API搜索
            new_api_success = self.try_new_api_search(search_term, song_info)
            if new_api_success:
                return True
            
            # 3. 尝试酷狗搜索
            kugou_success = self.try_kugou_search(search_term, song_info)
            if kugou_success:
                return True
            
            # 4. 尝试咪咕搜索
            migu_success = self.try_migu_search(search_term, song_info)
            if migu_success:
                return True
            
            # 5. 尝试5SING搜索
            sing5_success = self.try_5sing_search(search_term, song_info)
            if sing5_success:
                return True
            
            # 6. 尝试QQ音乐搜索
            qq_success = self.try_qq_music_search(search_term, song_info)
            if qq_success:
                return True
            
            # 7. 尝试抖音短视频平台搜索
            douyin_success = self.try_find_douyin_music(search_term, song_info)
            if douyin_success:
                return True
            
            # 8. 专用平台搜索失败，尝试全网爬取
            self.log("专用音乐平台搜索未找到结果，开始全网爬取...")
            web_success = self.try_web_crawl_search(search_term, song_info)
            if web_success:
                return True
            
            # 所有搜索源都失败
            self.log("所有搜索源均未找到匹配结果")
            self.status_var.set("搜索失败: 未找到匹配结果")
            return False
            
        except Exception as e:
            self.log(f"全网搜索出错: {str(e)}")
            self.status_var.set("搜索失败: 处理过程出错")
            return False
    
    def try_hot_music_platforms(self, search_term, song_info):
        """尝试从热门社交平台和专业音乐下载网站搜索最新流行歌曲"""
        try:
            self.log(f"尝试从热门平台搜索最新歌曲: {search_term}")
            
            # 构建不同的搜索关键词变体
            search_keywords = [
                f"{song_info['name']} {song_info['artist']} 完整版",
                f"{search_term} 高音质",
                f"{search_term} 首发",
                f"{search_term} 新歌",
                f"{song_info['artist']}新歌{song_info['name']}"
            ]
            
            # 1. 哔哩哔哩搜索
            self.log("尝试哔哩哔哩音频资源...")
            bili_search_success = False
            
            for keyword in search_keywords[:2]:  # 只尝试前两个关键词
                try:
                    bili_search_url = f"https://search.bilibili.com/all?keyword={urllib.parse.quote(keyword)}"
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                        'Referer': 'https://www.bilibili.com/'
                    }
                    
                    response = self.session.get(bili_search_url, headers=headers, timeout=10)
                    
                    if response.status_code != 200:
                        continue
                    
                    # 查找视频链接
                    video_links = re.findall(r'(https?://www\.bilibili\.com/video/[A-Za-z0-9]+)', response.text)
                    
                    if not video_links:
                        continue
                    
                    self.log(f"找到 {len(video_links)} 个哔哩哔哩视频")
                    
                    # 访问前三个视频
                    for video_url in video_links[:3]:
                        try:
                            self.log(f"访问哔哩哔哩视频: {video_url}")
                            video_response = self.session.get(video_url, headers=headers, timeout=10)
                            
                            # 提取音频URL
                            audio_urls = re.findall(r'"baseUrl":"(https?://[^"]+\.(?:mp3|m4a)(?:\\u002F|/)[^"]*)"', video_response.text)
                            audio_urls = [url.replace('\\u002F', '/') for url in audio_urls]
                            
                            if not audio_urls:
                                continue
                            
                            self.log(f"从哔哩哔哩提取到 {len(audio_urls)} 个音频链接")
                            
                            for audio_url in audio_urls:
                                try:
                                    # 准备下载信息
                                    found_song_info = {
                                        'name': song_info['name'],
                                        'artist': song_info['artist'],
                                        'album': song_info['album'],
                                        'source': '哔哩哔哩'
                                    }
                                    
                                    if self.download_file(audio_url, found_song_info):
                                        bili_search_success = True
                                        return True
                                except Exception as e:
                                    self.log(f"下载哔哩哔哩音频失败: {str(e)}")
                                    continue
                        except Exception as e:
                            self.log(f"处理哔哩哔哩视频出错: {str(e)}")
                            continue
                except Exception as e:
                    self.log(f"哔哩哔哩搜索出错: {str(e)}")
                    continue
            
            # 2. 微博音频搜索
            if not bili_search_success:
                self.log("尝试微博音频资源...")
                
                for keyword in search_keywords[:2]:
                    try:
                        weibo_search_url = f"https://s.weibo.com/weibo?q={urllib.parse.quote(keyword)}"
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Referer': 'https://weibo.com/'
                        }
                        
                        response = self.session.get(weibo_search_url, headers=headers, timeout=10)
                        
                        if response.status_code != 200:
                            continue
                        
                        # 查找分享页面链接
                        share_links = re.findall(r'(https?://(?:weibo|m)\.com/(?:[^/]+/)*[A-Za-z0-9]+)', response.text)
                        
                        if not share_links:
                            continue
                        
                        self.log(f"找到 {len(share_links)} 个微博分享页面")
                        
                        # 访问前三个分享页面
                        for share_url in share_links[:3]:
                            try:
                                self.log(f"访问微博分享: {share_url}")
                                share_response = self.session.get(share_url, headers=headers, timeout=10)
                                
                                # 提取音频URL
                                audio_urls = re.findall(r'(https?://(?:miaopai|f|audio)\.weibo\.(?:com|cn)/[^"\'>\s]+\.(?:mp3|m4a)[^"\'>\s]*)', share_response.text)
                                
                                if not audio_urls:
                                    continue
                                
                                self.log(f"从微博提取到 {len(audio_urls)} 个音频链接")
                                
                                for audio_url in audio_urls:
                                    try:
                                        # 准备下载信息
                                        found_song_info = {
                                            'name': song_info['name'],
                                            'artist': song_info['artist'],
                                            'album': song_info['album'],
                                            'source': '微博'
                                        }
                                        
                                        if self.download_file(audio_url, found_song_info):
                                            return True
                                    except Exception as e:
                                        self.log(f"下载微博音频失败: {str(e)}")
                                        continue
                            except Exception as e:
                                self.log(f"处理微博分享出错: {str(e)}")
                                continue
                    except Exception as e:
                        self.log(f"微博搜索出错: {str(e)}")
                        continue
            
            # 3. 最后尝试一些专业音乐下载网站
            self.log("尝试专业音乐下载网站...")
            
            # 专业音乐网站
            music_sites = [
                f"https://www.9ku.com/search.htm?key={urllib.parse.quote(search_term)}",  # 九酷音乐
                f"https://www.hifini.com/search-{urllib.parse.quote(search_term)}.htm",   # HiFiNi
                f"https://www.cdbao.net/search?kw={urllib.parse.quote(search_term)}",     # CD包音乐网
                f"https://tonzhon.com/search?keyword={urllib.parse.quote(search_term)}"   # 铜钟音乐
            ]
            
            for site_url in music_sites:
                try:
                    self.log(f"尝试音乐网站: {site_url.split('?')[0]}")
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                    }
                    
                    response = self.session.get(site_url, headers=headers, timeout=15)
                    
                    if response.status_code != 200:
                        continue
                    
                    # 查找可能的音乐详情页面
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 提取所有可能的详情页链接
                    detail_links = []
                    
                    # 查找包含歌曲名和歌手名的链接
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        text = a.get_text().lower()
                        
                        # 检查链接文本是否包含歌曲名或歌手名
                        if song_info['name'].lower() in text or song_info['artist'].lower() in text:
                            # 确保是相对链接
                            if not href.startswith('http'):
                                base_url = '/'.join(site_url.split('/')[:3])
                                if href.startswith('/'):
                                    href = base_url + href
                                else:
                                    href = base_url + '/' + href
                            
                            detail_links.append(href)
                    
                    if not detail_links:
                        continue
                    
                    self.log(f"找到 {len(detail_links)} 个可能的音乐详情页面")
                    
                    # 访问前三个详情页面
                    for detail_url in detail_links[:3]:
                        try:
                            self.log(f"访问详情页: {detail_url}")
                            detail_response = self.session.get(detail_url, headers=headers, timeout=10)
                            
                            if detail_response.status_code != 200:
                                continue
                            
                            # 提取音频URL
                            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                            
                            # 查找音频标签
                            audio_tags = detail_soup.find_all('audio')
                            for audio in audio_tags:
                                src = audio.get('src')
                                if src:
                                    if src.startswith('//'):
                                        src = 'https:' + src
                                    elif not src.startswith('http'):
                                        base_url = '/'.join(detail_url.split('/')[:3])
                                        src = base_url + ('/' if not src.startswith('/') else '') + src
                                    
                                    self.log(f"找到音频标签: {src}")
                                    
                                    # 准备下载信息
                                    found_song_info = {
                                        'name': song_info['name'],
                                        'artist': song_info['artist'],
                                        'album': song_info['album'],
                                        'source': '专业音乐网站'
                                    }
                                    
                                    if self.download_file(src, found_song_info):
                                        return True
                        
                            # 查找可能的播放链接或下载链接
                            audio_urls = []
                            
                            # 正则匹配
                            audio_urls.extend(re.findall(r'(https?://[^"\'>\s]+\.(?:mp3|m4a|flac)[^"\'>\s]*)', detail_response.text))
                            audio_urls.extend(re.findall(r'url\s*:\s*[\'"]([^"\']+\.(?:mp3|m4a|flac)[^"\']*)[\'"]', detail_response.text))
                            audio_urls.extend(re.findall(r'src\s*:\s*[\'"]([^"\']+\.(?:mp3|m4a|flac)[^"\']*)[\'"]', detail_response.text))
                            
                            # 如果找到音频URL，尝试下载
                            for audio_url in audio_urls:
                                if audio_url.startswith('//'):
                                    audio_url = 'https:' + audio_url
                                elif not audio_url.startswith('http'):
                                    base_url = '/'.join(detail_url.split('/')[:3])
                                    audio_url = base_url + ('/' if not audio_url.startswith('/') else '') + audio_url
                                
                                try:
                                    self.log(f"尝试下载音频: {audio_url}")
                                    
                                    # 准备下载信息
                                    found_song_info = {
                                        'name': song_info['name'],
                                        'artist': song_info['artist'],
                                        'album': song_info['album'],
                                        'source': '专业音乐网站'
                                    }
                                    
                                    if self.download_file(audio_url, found_song_info):
                                        return True
                                except Exception as e:
                                    self.log(f"下载音频失败: {str(e)}")
                                    continue
                        except Exception as e:
                            self.log(f"处理详情页面出错: {str(e)}")
                            continue
                except Exception as e:
                    self.log(f"音乐网站搜索出错: {str(e)}")
                    continue
            
            self.log("所有热门平台搜索均未找到匹配歌曲")
            return False
            
        except Exception as e:
            self.log(f"热门平台搜索过程出错: {str(e)}")
            return False