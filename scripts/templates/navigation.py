"""A shared, role-aware navigation model for Start and Settings."""
PAGES = {
    'home': ('开始使用', 'Start', [
        [('下载工具', 'Download tools', 'page', 'tools'), ('设置', 'Settings', 'page', 'settings')],
        [('帮助', 'Help', 'cmd', 'help')],
    ]),
    'settings': ('设置', 'Settings', [
        [('下载偏好', 'Download preferences', 'page', 'download'), ('Cookie 与账号', 'Cookies & accounts', 'page', 'cookies')],
        [('界面与语言', 'Interface & language', 'page', 'interface'), ('文件与记录', 'Files & activity', 'page', 'files')],
        [('高级设置', 'Advanced settings', 'page', 'advanced')],
    ]),
    'download': ('下载偏好', 'Download preferences', [
        [('画质与格式', 'Quality & format', 'cmd', 'format'), ('字幕', 'Subtitles', 'cmd', 'subs')],
        [('文件分段', 'File splitting', 'cmd', 'split'), ('媒体信息', 'Media details', 'cmd', 'mediainfo')],
        [('媒体标签', 'Media tags', 'cmd', 'tags')],
    ]),
    'interface': ('界面与语言', 'Interface & language', [
        [('中文 / English', 'English / 中文', 'language', 'language')],
        [('快捷键盘', 'Shortcut keyboard', 'cmd', 'keyboard')],
    ]),
    'files': ('文件与记录', 'Files & activity', [
        [('清理文件与设置', 'Clean files & settings', 'cmd', 'clean'), ('使用统计', 'Usage', 'cmd', 'usage')],
    ]),
    'advanced': ('高级设置', 'Advanced settings', [
        [('下载代理', 'Download proxy', 'cmd', 'proxy'), ('下载参数', 'Download arguments', 'cmd', 'args')],
        [('敏感内容选项', 'Sensitive content', 'cmd', 'nsfw')],
    ]),
    'tools': ('下载工具', 'Download tools', [
        [('下载音频', 'Download audio', 'cmd', 'audio'), ('下载图片', 'Download images', 'cmd', 'img')],
        [('播放列表', 'Playlists', 'cmd', 'playlist'), ('获取直链', 'Direct media links', 'cmd', 'link')],
        [('搜索媒体', 'Search media', 'cmd', 'search_menu')],
    ]),
}
LEGACY_PAGES = {'back':'settings', 'media':'download', 'cookies':'cookies', 'logs':'files', 'more':'tools', 'clean':'files'}
LEGACY_COOKIES = {'yuanbao_cookie', 'download_cookie', 'cookies_from_browser', 'check_cookie', 'save_as_cookie'}


def page_model(page, language='zh', admin=False):
    if page not in PAGES:
        raise ValueError('Unknown navigation page')
    zh, en, definitions = PAGES[page]
    label_index = 0 if language == 'zh' else 1
    rows = []
    for row in definitions:
        items=[]
        for button in row:
            target = ('nav|' + button[3]) if button[2] == 'page' else ('settings__menu__language' if button[2] == 'language' else 'settings__cmd__' + button[3])
            items.append((button[label_index], target))
        rows.append(items)
    if page == 'home' and admin:
        rows.append([('用户管理' if language == 'zh' else 'User management', 'nav|users')])
    if page != 'home':
        parent = 'home' if page in ('settings','tools') else 'settings'
        label = ('返回开始页' if parent == 'home' else '返回设置') if language == 'zh' else ('Back to Start' if parent == 'home' else 'Back to Settings')
        rows.append([(label, 'nav|' + parent)])
    rows.append([('关闭' if language == 'zh' else 'Close', 'nav|close')])
    return (zh if language == 'zh' else en), rows


def _allowed(message, user_id):
    from HELPERS.limitter import is_private_user_allowed
    return message.chat.id == user_id and is_private_user_allowed(user_id)


def show_navigation(app, message, page='home', query=None):
    user_id = query.from_user.id if query else getattr(getattr(message,'from_user',None),'id', message.chat.id)
    if not _allowed(message,user_id):
        return False
    from CONFIG.config import Config
    from HELPERS.private_i18n import user_language
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    if page == 'cookies':
        from HELPERS.cookie_import_ui import show_cookie_import_menu
        if query:
            query.edit_message_reply_markup(reply_markup=None)
        show_cookie_import_menu(app,message,user_id)
        return True
    title, rows = page_model(page,user_language(user_id),int(user_id) in {int(v) for v in Config.ADMIN})
    if page == 'home':
        title += '\n\n' + ('发送视频或图文链接即可下载。下载参数和账号Cookie请在设置中管理。' if user_language(user_id)=='zh' else 'Send a video or post link to download. Manage preferences and site cookies in Settings.')
    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton(label,callback_data=target) for label,target in row] for row in rows])
    if query:
        query.edit_message_text(title,reply_markup=keyboard)
    else:
        app.send_message(message.chat.id,title,reply_markup=keyboard)
    return True


def navigation_callback(app, query):
    if not _allowed(query.message,query.from_user.id):
        query.answer('无权操作 / Access denied',show_alert=True)
        return
    page=query.data.split('|',1)[1]
    query.answer()
    if page=='close':
        query.message.delete()
    elif page=='users':
        from CONFIG.config import Config
        if int(query.from_user.id) not in {int(v) for v in Config.ADMIN}:
            return
        from COMMANDS.private_users_cmd import private_users_menu
        from HELPERS.safe_messeger import fake_message
        private_users_menu(app,fake_message('/users',query.from_user.id))
    elif page in PAGES or page=='cookies':
        show_navigation(app,query.message,page,query=query)


def legacy_settings_menu(app, query):
    page=query.data.split('__')[-1]
    if page=='language':
        if _allowed(query.message,query.from_user.id):
            from COMMANDS.lang_cmd import lang_command
            from HELPERS.safe_messeger import fake_message
            query.answer()
            lang_command(app,fake_message('/lang',query.from_user.id))
        return
    if page=='close':
        if _allowed(query.message,query.from_user.id):
            query.answer();query.message.delete()
        return
    query.answer()
    show_navigation(app,query.message,LEGACY_PAGES.get(page,'settings'),query=query)


def redirect_old_cookie_button(app, query):
    if query.data.split('__')[-1] not in LEGACY_COOKIES:
        return False
    query.answer()
    show_navigation(app,query.message,'cookies',query=query)
    return True


def register_navigation(app):
    from pyrogram import filters
    app.on_callback_query(filters.regex(r'^nav\|'))(navigation_callback)
