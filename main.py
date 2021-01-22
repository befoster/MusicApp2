from kivymd.app import MDApp
from kivymd.uix.navigationdrawer import NavigationLayout, MDNavigationDrawer
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import OneLineListItem, OneLineRightIconListItem, MDList, IconRightWidget, TwoLineListItem
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.toolbar import MDToolbar
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.core.audio import SoundLoader
from kivy.utils import platform
import os
import random


class Sound:
    def __init__(self, label):
        self.sound = None
        self.pos = 0
        self.playlist = list()
        self.idx = 0
        self.keep_playing = True
        self.label = label

    def set(self, playlist, idx):
        self.playlist = playlist[:]
        self.idx = idx
        self.pos = 0
        self.play()

    def play(self):
        if self.sound is not None and self.sound.state == 'play':
            self.keep_playing = False
            self.sound.stop()
            self.keep_playing = True
        self.sound = SoundLoader.load(self.playlist[self.idx][0])
        if self.sound is None:
            print('Unable to play ' + self.playlist[self.idx][0])
            self.playlist = list()
        else:
            self.sound.on_stop = self.next_song
            self.sound.play()
            if self.pos > 0:
                self.sound.seek(self.pos)
            self.label.text = self.playlist[self.idx][1]

    def pause(self):
        if self.sound is not None:
            if self.sound.state == 'play':
                self.pos = self.sound.get_pos()
                self.keep_playing = False
                self.sound.stop()
                self.keep_playing = True
            else:
                self.play()

    def prev_song(self):
        if self.playlist:
            if self.sound.state == 'play':
                pos = self.sound.get_pos()
            else:
                pos = self.pos
            if pos <= 3:
                self.idx = (self.idx - 1 + len(self.playlist)) % len(self.playlist)
            self.pos = 0
            self.play()

    def next_song(self):
        if self.keep_playing and self.playlist:
            self.idx = (self.idx + 1) % len(self.playlist)
            self.pos = 0
            self.play()


class UserInfo:
    def __init__(self, file):
        self.file = file
        self.folders = list()
        self.hist_len = 5
        self.songs = dict()
        self.recent = list()
        self.playlists = dict()
        self.temp_playlists = dict()
        self.load()
        self.save()

    def load(self):
        try:
            with open(self.file, 'r') as f:
                case = 0
                for line in f:
                    if case == 0:
                        self.folders = line.strip().split(',')
                        while self.folders and len(self.folders[0].strip()) == 0:
                            self.folders.pop(0)
                        case += 1
                    elif case == 1:
                        self.hist_len = int(line.strip())
                        case += 1
                    elif case == 2:
                        if line.strip() == 'Playlists':
                            case += 1
                        else:
                            parts = line.strip().split(';#;')
                            self.songs[int(parts[0])] = [parts[1], parts[2], parts[3], parts[5:], float(parts[4])]
                    elif case == 3:
                        if line.strip() == 'Recent Playlists':
                            case += 1
                        else:
                            parts = line.strip().split(';#;')
                            self.playlists[parts[0]] = [int(k) for k in parts[1:]]
                    else:
                        parts = line.strip().split(';#;')
                        if parts[0] == 'p':
                            self.recent.append(parts[1])
                        else:
                            self.temp_playlists[case - 3] = [int(k) for k in parts[1:]]
                            self.recent.append(case - 3)
                            case += 1
        except FileNotFoundError:
            pass
        for folder in self.folders:
            self.load_new_songs(folder)

    def load_new_songs(self, folder):
        count = (max(self.songs.keys()) if self.songs else 0) + 1
        existing = {v[0] for v in self.songs.values()}
        try:
            for file in os.listdir(folder):
                if '.wav' in file or '.ogg' in file:
                    path = os.path.join(folder, file)
                    if path not in existing:
                        existing.add(path)
                        self.songs[count] = [path, file[:-4], 'None', list(), os.stat(path).st_ctime]
                        count += 1
        except FileNotFoundError:
            print('Could not find path "' + folder + '"')

    def save(self):
        with open(self.file, 'w+') as f:
            f.write(','.join(self.folders) + '\n' + str(self.hist_len) + '\n')
            for k, v in self.songs.items():
                f.write(';#;'.join([str(k), v[0], v[1], v[2], str(v[4])] + v[3]) + '\n')
            f.write('Playlists\n')
            for k, v in self.playlists.items():
                f.write(';#;'.join([k] + [str(val) for val in v]) + '\n')
            f.write('Recent Playlists')
            for k in self.recent:
                if k in self.playlists:
                    f.write('\np;#;' + k)
                else:
                    f.write('\nt;#;' + ';#;'.join([str(s) for s in self.temp_playlists[k]]))


def get_start(s):
    k = s[0].upper()
    return '#' if k.isdigit() else k


class MusicApp(MDApp):
    dialog = None
    items = None
    user_info = None
    list = None
    file_manager = None
    state = 'Playlists'
    reverse = False
    songs = None
    selected = set()
    playlist = None
    reorder = None
    sound = None
    nav_drawer = None
    ext_path = ''

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        if platform == 'win':
            self.user_info = UserInfo(os.path.join(self.user_data_dir, 'music_app_save.txt'))
            self.ext_path = '/'
        else:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            self.ext_path = os.getenv('EXTERNAL_STORAGE')
            self.user_info = UserInfo(os.path.join(self.ext_path, 'MusicApp', 'music_app_save.txt'))

        menu_items = MDList()
        menu_items.add_widget(OneLineListItem(text='Playlists', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Songs (Title)', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Songs (Artist)', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Songs (Date)', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Songs (Tags)', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Settings', on_press=self.menu_action))
        nav_scroll = ScrollView()
        nav_scroll.add_widget(menu_items)
        self.nav_drawer = MDNavigationDrawer()
        self.nav_drawer.add_widget(nav_scroll)

        layout = MDBoxLayout(orientation='vertical')
        self.dialog = MDDialog(
            type="custom",
            content_cls=MDTextField(),
            buttons=[MDRaisedButton(text='Add to Playlist', on_release=self.dialog_action),
                     MDRaisedButton(text='Set Title', on_release=self.dialog_action),
                     MDRaisedButton(text='Set Artist', on_release=self.dialog_action),
                     MDRaisedButton(text='Add Tag', on_release=self.dialog_action)])
        self.file_manager = MDFileManager(exit_manager=self.exit_manager, select_path=self.select_path,
                                          ext=['mp3', 'wav', 'ogg'])

        toolbar = MDToolbar(title='Music App', pos_hint={'top': 1})
        toolbar.left_action_items.append(['menu', lambda x: self.nav_drawer.set_state('open')])
        toolbar.right_action_items.append(['cancel', self.toolbar_action])
        toolbar.right_action_items.append(['arrow-up-down', self.toolbar_action])
        toolbar.right_action_items.append(['play', self.toolbar_action])
        toolbar.right_action_items.append(['dots-vertical', self.toolbar_action])
        layout.add_widget(toolbar)

        self.list = MDList()
        scroll = ScrollView()
        scroll.add_widget(self.list)
        layout.add_widget(scroll)
        self.items = dict()
        self.songs = dict()

        bottom_bar = MDBoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        song_label = MDLabel(text='None')
        self.sound = Sound(song_label)
        bottom_bar.add_widget(song_label)
        bottom_bar.add_widget(MDIconButton(icon='rewind', on_release=self.bottom_action))
        bottom_bar.add_widget(MDIconButton(icon='play-pause', on_release=self.bottom_action))
        bottom_bar.add_widget(MDIconButton(icon='fast-forward', on_release=self.bottom_action))
        layout.add_widget(bottom_bar)

        screen = Screen(name='screen')
        screen.add_widget(layout)
        sm = ScreenManager()
        sm.add_widget(screen)
        sm.current = 'screen'

        nav = NavigationLayout()
        nav.add_widget(sm)
        nav.add_widget(self.nav_drawer)

        self.refresh(True, True, True)

        return nav

    def refresh(self, playlists=False, selected_playlist=False, songs=False):
        # Settings
        if 'Settings' not in self.items:
            self.items['Settings'] = [OneLineRightIconListItem(text='History length = '+str(self.user_info.hist_len)),
                                      OneLineRightIconListItem(text='History length = '+str(self.user_info.hist_len))]
            self.items['Settings'][0].add_widget(IconRightWidget(icon='minus', on_release=self.change_hist_len))
            self.items['Settings'][1].add_widget(IconRightWidget(icon='plus', on_release=self.change_hist_len))
            for folder in self.user_info.folders:
                self.items['Settings'].append(OneLineRightIconListItem(text=folder))
                self.items['Settings'][-1].add_widget(IconRightWidget(icon='minus', on_release=self.remove_folder))
            self.items['Settings'].append(OneLineRightIconListItem(text='Add new folder'))
            self.items['Settings'][-1].add_widget(
                IconRightWidget(icon='plus', on_release=lambda x: self.file_manager.show(self.ext_path)))

        # Playlists
        if playlists:
            if 'Playlists' not in self.items:
                self.items['Playlists'] = list()
            else:
                self.items['Playlists'].clear()
            self.items['Playlists'].append(OneLineListItem(text='Recents'))
            for k in self.user_info.recent:
                if k in self.user_info.playlists:
                    self.items['Playlists'].append(
                        TwoLineListItem(text=k,
                                        secondary_text=(str(len(self.user_info.playlists[k])) + ' songs'),
                                        on_release=self.select_normal_playlist))
                else:
                    self.items['Playlists'].append(
                        TwoLineListItem(text=('Temp playlist '+str(k)),
                                        secondary_text=(str(len(self.user_info.temp_playlists[k]))+' songs'),
                                        on_release=self.select_temp_playlist))
            start_letter = ''
            for k in sorted(self.user_info.playlists.keys(), reverse=self.reverse):
                if get_start(k) != start_letter:
                    start_letter = get_start(k)
                    self.items['Playlists'].append(OneLineListItem(text=start_letter))
                self.items['Playlists'].append(TwoLineListItem(text=k, secondary_text=(str(len(
                    self.user_info.playlists[k])) + ' songs'), on_release=self.select_normal_playlist))

        # One playlist
        if selected_playlist:
            if self.playlist is not None:
                if 'play' not in self.items:
                    self.items['play'] = list()
                else:
                    self.items['play'].clear()
                if self.playlist in self.user_info.playlists:
                    song_list = self.user_info.playlists[self.playlist]
                    self.items['play'].append(OneLineListItem(text=self.playlist))
                else:
                    song_list = self.user_info.temp_playlists[self.playlist]
                    self.items['play'].append(OneLineListItem(text=('Temp playlist '+str(self.playlist))))
                for k in song_list:
                    self.items['play'].append((k, 0))

        # Songs
        if songs:
            # By title
            if 'Songs (Title)' not in self.items:
                self.items['Songs (Title)'] = list()
            else:
                self.items['Songs (Title)'].clear()
            start_letter = ''
            for k in sorted(self.user_info.songs.keys(), reverse=self.reverse,
                            key=lambda x: self.user_info.songs[x][1]):
                if get_start(self.user_info.songs[k][1]) != start_letter:
                    start_letter = get_start(self.user_info.songs[k][1])
                    self.items['Songs (Title)'].append(OneLineListItem(text=start_letter))
                self.items['Songs (Title)'].append((k, 0))

            # By artist
            if 'Songs (Artist)' not in self.items:
                self.items['Songs (Artist)'] = list()
            else:
                self.items['Songs (Artist)'].clear()
            start_letter = ''
            for k in sorted(self.user_info.songs.keys(), reverse=self.reverse,
                            key=lambda x: self.user_info.songs[x][2]):
                if get_start(self.user_info.songs[k][2]) != start_letter:
                    start_letter = get_start(self.user_info.songs[k][2])
                    self.items['Songs (Artist)'].append(OneLineListItem(text=start_letter))
                self.items['Songs (Artist)'].append((k, 0))

            # By date
            if 'Songs (Date)' not in self.items:
                self.items['Songs (Date)'] = list()
            else:
                self.items['Songs (Date)'].clear()
            for k in sorted(self.user_info.songs.keys(), reverse=self.reverse,
                            key=lambda x: self.user_info.songs[x][4]):
                self.items['Songs (Date)'].append((k, 0))

            # By tag
            if 'Songs (Tags)' not in self.items:
                self.items['Songs (Tags)'] = list()
            else:
                self.items['Songs (Tags)'].clear()
            tags = dict()
            for k, v in self.user_info.songs.items():
                for i in range(len(v[3])):
                    if v[3][i] not in tags:
                        tags[v[3][i]] = list()
                    tags[v[3][i]].append((k, i))
            for tag in sorted(tags.keys(), reverse=self.reverse):
                self.items['Songs (Tags)'].append(OneLineListItem(text=tag))
                for k in sorted(tags[tag], key=lambda x: self.user_info.songs[x[0]][1]):
                    self.items['Songs (Tags)'].append(k)

            # Update songs
            for k, v in self.user_info.songs.items():
                if k not in self.songs:
                    self.songs[k] = list()
                while len(self.songs[k]) < max(1, len(v[3])):
                    self.songs[k].append(TwoLineListItem(text=v[1], secondary_text=v[2], on_release=self.select_song))

        self.set_screen()

    def select_normal_playlist(self, btn):
        self.select_playlist(btn.text)

    def select_temp_playlist(self, btn):
        self.select_playlist(int(btn.text[14:]))

    def select_playlist(self, k):
        self.playlist = k
        self.state = 'play'
        self.refresh(selected_playlist=True)

    def play_playlist(self, k):
        if k in self.user_info.recent:
            self.user_info.recent.remove(k)
        self.user_info.recent.insert(0, k)
        while len(self.user_info.recent) > self.user_info.hist_len:
            k = self.user_info.recent.pop()
            if k in self.user_info.temp_playlists:
                del self.user_info.temp_playlists[k]
                if self.playlist == k:
                    self.playlist = None
        self.user_info.save()

    def select_song(self, btn):
        for k, v in self.songs.items():
            if btn in v:
                if 'Songs' in self.state:
                    if k in self.selected:
                        self.selected.remove(k)
                        for item in v:
                            item.bg_color = []
                    else:
                        self.selected.add(k)
                        for item in v:
                            item.bg_color = btn.theme_cls.bg_light
                elif self.state == 'play':
                    if self.playlist in self.user_info.playlists:
                        song_list = self.user_info.playlists[self.playlist]
                    else:
                        song_list = self.user_info.temp_playlists[self.playlist]
                    if self.reorder is not None:
                        if k in self.reorder:
                            self.reorder.remove(k)
                            for item in v:
                                item.bg_color = []
                        else:
                            self.reorder.append(k)
                            for item in v:
                                item.bg_color = btn.theme_cls.bg_light
                            if len(self.reorder) == len(song_list):
                                if self.playlist in self.user_info.playlists:
                                    self.user_info.playlists[self.playlist] = self.reorder[:]
                                else:
                                    self.user_info.temp_playlists[self.playlist] = self.reorder[:]
                                for song in self.reorder:
                                    for item in self.songs[song]:
                                        item.bg_color = []
                                self.reorder = None
                                self.user_info.save()
                                self.refresh(selected_playlist=True)
                    else:
                        self.sound.set([self.user_info.songs[x][:2] for x in song_list], song_list.index(k))
                        self.play_playlist(self.playlist)
                return

    def change_hist_len(self, btn):
        if btn.icon == 'plus':
            self.user_info.hist_len += 1
        elif btn.icon == 'minus':
            self.user_info.hist_len -= 1
        self.items['Settings'][0].text = 'History length = ' + str(self.user_info.hist_len)
        self.items['Settings'][1].text = 'History length = ' + str(self.user_info.hist_len)
        self.user_info.save()

    def remove_folder(self, btn):
        idx = -1
        for i in range(len(self.user_info.folders)):
            if btn.parent.parent == self.items['Settings'][i+2]:
                idx = i
                break
        self.list.remove_widget(self.items['Settings'][idx+2])
        self.items['Settings'].pop(idx+2)
        self.user_info.folders.pop(idx)
        self.user_info.save()

    def add_folder(self, path):
        self.list.remove_widget(self.items['Settings'][-1])
        self.items['Settings'].insert(len(self.items['Settings'])-1, OneLineRightIconListItem(text=path))
        self.items['Settings'][-2].add_widget(IconRightWidget(icon='minus', on_release=self.remove_folder))
        self.list.add_widget(self.items['Settings'][-2])
        self.list.add_widget(self.items['Settings'][-1])
        self.user_info.folders.append(path)
        self.user_info.load_new_songs(path)
        self.user_info.save()

    def select_path(self, path):
        self.exit_manager()
        self.add_folder(path.replace('\\', '/'))

    def exit_manager(self, *args):
        self.file_manager.close()

    def menu_action(self, btn):
        self.state = btn.text
        self.set_screen()
        self.nav_drawer.set_state('close')

    def set_screen(self):
        if self.reorder is not None and self.state != 'play':
            for k in self.reorder:
                for item in self.songs[k]:
                    item.bg_color = []
            self.reorder = None
        while self.list.children:
            self.list.remove_widget(self.list.children[0])
        for item in self.items[self.state]:
            if type(item) is tuple:
                self.list.add_widget(self.songs[item[0]][item[1]])
            else:
                self.list.add_widget(item)

    def toolbar_action(self, btn):
        if btn.icon == 'cancel':
            if 'Songs' in self.state:
                for k in self.selected:
                    for item in self.songs[k]:
                        item.bg_color = []
                self.selected.clear()
            elif self.state == 'play':
                if self.reorder is None:
                    if self.playlist in self.user_info.playlists:
                        del self.user_info.playlists[self.playlist]
                    else:
                        del self.user_info.temp_playlists[self.playlist]
                    if self.playlist in self.user_info.recent:
                        self.user_info.recent.remove(self.playlist)
                    self.playlist = None
                    self.state = 'Playlists'
                else:
                    if self.playlist in self.user_info.playlists:
                        for k in self.reorder:
                            self.user_info.playlists[self.playlist].remove(k)
                    else:
                        for k in self.reorder:
                            self.user_info.temp_playlists[self.playlist].remove(k)
                    for k in self.reorder:
                        for item in self.songs[k]:
                            item.bg_color = []
                    self.reorder = None
                self.refresh(True, True)
                self.user_info.save()
        elif btn.icon == 'arrow-up-down':
            if 'Songs' in self.state or self.state == 'Playlists':
                self.reverse = not self.reverse
                self.refresh(True, False, True)
            elif self.state == 'play':
                if self.reorder is None:
                    self.reorder = list()
                else:
                    for k in self.reorder:
                        for item in self.songs[k]:
                            item.bg_color = []
                    self.reorder = None
        elif btn.icon == 'play':
            if 'Songs' in self.state and len(self.selected) > 0:
                song_list = list(self.selected)
                random.shuffle(song_list)
                k = 1
                while k in self.user_info.temp_playlists:
                    k += 1
                self.user_info.temp_playlists[k] = song_list[:]
                self.sound.set([self.user_info.songs[x][:2] for x in song_list], 0)
                self.play_playlist(k)
                self.playlist = k
                self.state = 'play'
                self.refresh(True, True)
                for k in self.selected:
                    for item in self.songs[k]:
                        item.bg_color = []
                self.selected.clear()
                self.set_screen()
            elif self.state == 'play':
                if self.playlist in self.user_info.playlists:
                    song_list = self.user_info.playlists[self.playlist]
                else:
                    song_list = self.user_info.temp_playlists[self.playlist]
                random.shuffle(song_list)
                self.sound.set([self.user_info.songs[x][:2] for x in song_list], 0)
                self.play_playlist(self.playlist)
        elif btn.icon == 'dots-vertical':
            if 'Songs' in self.state:
                self.dialog.open()

    def bottom_action(self, btn):
        if btn.icon == 'rewind':
            self.sound.prev_song()
        elif btn.icon == 'play-pause':
            self.sound.pause()
        elif btn.icon == 'fast-forward':
            self.sound.next_song()

    def dialog_action(self, btn):
        if 'Songs' in self.state:
            text = self.dialog.content_cls.text
            if len(self.selected) == 0:
                print('Must select song(s) first')
            elif len(text) == 0:
                print('Must input text')
            else:
                changed = False
                if btn.text == 'Add to Playlist':
                    if text not in self.user_info.playlists:
                        self.user_info.playlists[text] = list(self.selected)
                        changed = True
                    else:
                        for k in self.selected:
                            if k not in self.user_info.playlists[text]:
                                self.user_info.playlists[text].append(k)
                                changed = True
                elif btn.text == 'Set Title':
                    if len(self.selected) > 1:
                        print('Cannot set title of more than one song at once')
                    else:
                        for k in self.selected:
                            if text != self.user_info.songs[k][1]:
                                self.user_info.songs[k][1] = text
                                for item in self.songs[k]:
                                    item.text = text
                                changed = True
                elif btn.text == 'Set Artist':
                    for k in self.selected:
                        if text != self.user_info.songs[k][2]:
                            self.user_info.songs[k][2] = text
                            for item in self.songs[k]:
                                item.secondary_text = text
                            changed = True
                elif btn.text == 'Add Tag':
                    for k in self.selected:
                        if text not in self.user_info.songs[k][3]:
                            self.user_info.songs[k][3].append(text)
                            changed = True
                if changed:
                    self.refresh(True, True, True)
                    self.user_info.save()
                self.dialog.content_cls.text = ''
                self.dialog.dismiss()


MusicApp().run()
