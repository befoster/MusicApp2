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
from kivymd.uix.tab import MDTabsBase, MDTabs
from kivymd.uix.textfield import MDTextField
from kivy.core.audio import SoundLoader
import os
import random

"""
def next_song():
    global manual_stop, current_playlist, current_song
    if not manual_stop:
        current_song = (current_song + 1) % len(current_playlist)
        play_song()


def play_song():
    global current_song, current_playlist, song_labels, songs, sound, manual_stop
    v = songs[current_playlist[current_song]]
    for label in song_labels:
        label.text = v[1]
    if sound is not None and sound.state == 'play':
        manual_stop = True
        sound.stop()
        manual_stop = False
    sound = SoundLoader.load(v[0])
    sound.on_stop = next_song
    sound.play()


class PlaylistsScreen(Screen):
    def __init__(self, nav, **kwargs):
        super(PlaylistsScreen, self).__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')
        toolbar = MDToolbar(title='Playlists', pos_hint={"top": 1})
        toolbar.left_action_items.append(['menu', lambda x: nav.set_state("open")])
        toolbar.right_action_items.append(['arrow-up-down', self.reorder])
        toolbar.right_action_items.append(['shuffle', self.shuffle])
        toolbar.right_action_items.append(['play', self.play_playlist])
        toolbar.right_action_items.append(['delete', self.delete_playlist])
        layout.add_widget(toolbar)

        self.sm = ScreenManager()
        self.playlist_screen = Screen(name='playlists')
        self.song_screen = Screen(name='songs')
        self.sm.add_widget(self.playlist_screen)
        self.sm.add_widget(self.song_screen)
        self.sm.current = 'playlists'
        layout.add_widget(self.sm)

        self.playlists = MDList()
        scroll = ScrollView()
        scroll.add_widget(self.playlists)
        self.playlist_screen.add_widget(scroll)
        self.songs = MDList()
        scroll = ScrollView()
        scroll.add_widget(self.songs)
        self.song_screen.add_widget(scroll)

        global playlists
        self.reverse = False
        self.selected = None
        self.reordering = False
        self.order = list()
        self.song_list = list()

        self.refresh()
        layout.add_widget(BottomBar())
        self.add_widget(layout)

    def refresh(self):
        global playlists, temp_playlists, recents
        self.reordering = False
        while len(self.playlists.children) > 0:
            self.playlists.remove_widget(self.playlists.children[0])
        self.playlists.add_widget(OneLineListItem(text='Recent Playlists'))
        for k in recents:
            if k in playlists:
                self.playlists.add_widget(TwoLineListItem(text=k, secondary_text=(str(len(playlists[k])) + ' songs'),
                                                          on_release=self.select_playlist))
            else:
                self.playlists.add_widget(TwoLineListItem(text=('Temp playlist ' + str(k)),
                                                          secondary_text=(str(len(temp_playlists[k])) + ' songs'),
                                                          on_release=self.select_temp_playlist))
        start_letter = ''
        for k in sorted(playlists.keys(), reverse=self.reverse):
            if k[0].upper() != start_letter:
                start_letter = k[0].upper()
                self.playlists.add_widget(OneLineListItem(text=start_letter))
            self.playlists.add_widget(TwoLineListItem(text=k, secondary_text=(str(len(playlists[k]))+' songs'),
                                                      on_release=self.select_playlist))
        save_user_info()

    def select_playlist(self, btn):
        self.selected = btn.text
        self.select_any_playlist()

    def select_temp_playlist(self, btn):
        self.selected = int(btn.text[14:])
        self.select_any_playlist()

    def select_any_playlist(self):
        global songs, playlists, temp_playlists
        song_list = playlists[self.selected] if self.selected in playlists else temp_playlists[self.selected]
        while len(self.songs.children) > 0:
            self.songs.remove_widget(self.songs.children[0])
        self.song_list.clear()
        for k in song_list:
            self.song_list.append(TwoLineListItem(text=songs[k][1], secondary_text=songs[k][2],
                                                  on_release=self.song_press))
            self.songs.add_widget(self.song_list[-1])
        self.sm.current = 'songs'

    def set_reorder(self):
        global playlists, temp_playlists
        if self.selected in playlists:
            playlists[self.selected] = self.order[:]
        else:
            temp_playlists[self.selected] = self.order[:]
        self.order.clear()
        self.reordering = False
        self.select_any_playlist()

    def song_press(self, btn):
        song_list = playlists[self.selected] if self.selected in playlists else temp_playlists[self.selected]
        idx = self.song_list.index(btn)
        if self.reordering:
            if song_list[idx] in self.order:
                self.order.remove(song_list[idx])
                btn.bg_color = []
            else:
                self.order.append(song_list[idx])
                btn.bg_color = btn.theme_cls.bg_light
                if len(song_list) == len(self.order):
                    self.set_reorder()
        else:
            global current_song, current_playlist, hist_len, recents
            current_playlist = song_list
            current_song = idx
            if self.selected in recents:
                recents.remove(self.selected)
            recents.insert(0, self.selected)
            recents = recents[:hist_len]
            self.refresh()
            play_song()

    def reorder(self, btn):
        if self.sm.current == 'playlists':
            self.reverse = not self.reverse
            self.refresh()
        else:
            if self.reordering:
                self.order.clear()
                for btn in self.songs.children:
                    btn.bg_color = []
                self.reordering = False
            else:
                self.reordering = True

    def play_playlist(self, btn):
        global current_playlist, current_song, recents, hist_len
        if self.sm.current == 'songs':
            current_playlist = playlists[self.selected] if self.selected in playlists else temp_playlists[self.selected]
            current_song = 0
            if self.selected in recents:
                recents.remove(self.selected)
            recents.insert(0, self.selected)
            recents = recents[:hist_len]
            self.refresh()
            play_song()

    def shuffle(self, btn):
        global current_playlist, current_song, recents, hist_len
        if self.sm.current == 'songs':
            current_playlist = playlists[self.selected] if self.selected in playlists else temp_playlists[self.selected]
            random.shuffle(current_playlist)
            current_song = 0
            if self.selected in recents:
                recents.remove(self.selected)
            recents.insert(0, self.selected)
            recents = recents[:hist_len]
            self.refresh()
            play_song()

    def delete_playlist(self, btn):
        global playlists
        if self.sm.current == 'songs':
            if self.selected in playlists:
                del playlists[self.selected]
                if self.selected in recents:
                    recents.remove(self.selected)
                self.refresh()
                self.sm.current = 'playlists'
"""


class Tab(ScrollView, MDTabsBase):
    pass


class SongsScreen(Screen):
    def __init__(self, **kwargs):
        super(SongsScreen, self).__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')
        toolbar = MDToolbar(title='Songs', pos_hint={"top": 1})
        #toolbar.left_action_items.append(['menu', lambda x: nav.set_state("open")])
        toolbar.right_action_items.append(['cancel', self.unselect])
        toolbar.right_action_items.append(['arrow-up-down', self.reverse_order])
        toolbar.right_action_items.append(['play', self.play_playlist])
        self.dialog = MDDialog(
            type="custom",
            content_cls=MDTextField(),
            buttons=[MDRaisedButton(text="Add to Playlist", on_release=self.other_action),
                     MDRaisedButton(text="Set Title", on_release=self.other_action),
                     MDRaisedButton(text="Set Artist", on_release=self.other_action),
                     MDRaisedButton(text="Add Tag", on_release=self.other_action)])
        toolbar.right_action_items.append(['dots-vertical', lambda x: self.dialog.open()])
        layout.add_widget(toolbar)

        global songs
        self.reverse = False
        self.selected = set()
        self.lists = [MDList(), MDList(), MDList(), MDList()]
        self.songs = dict()
        for k, v in songs.items():
            self.songs[k] = [TwoLineListItem(text=v[1], secondary_text=v[2], on_release=self.select)
                             for _ in range(3 + len(v[3]))]
        self.sort_songs()

        tabs = MDTabs()
        tabs_list = [Tab(text='Date added'), Tab(text='Title'), Tab(text='Artist'), Tab(text='Tags')]
        for i in range(4):
            tabs_list[i].add_widget(self.lists[i])
            tabs.add_widget(tabs_list[i])
        layout.add_widget(tabs)

        #layout.add_widget(BottomBar())
        self.add_widget(layout)

    def unselect(self, btn):
        pass

    def reverse_order(self, btn):
        pass

    def play_playlist(self, btn):
        pass

    def other_action(self, btn):
        pass

    def sort_songs(self):
        pass


"""
    def select(self, btn):
        for k, v in self.songs.items():
            if btn in v:
                if k in self.selected:
                    self.selected.remove(k)
                    for item in self.songs[k]:
                        item.bg_color = []
                else:
                    self.selected.add(k)
                    for item in self.songs[k]:
                        item.bg_color = btn.theme_cls.bg_light
                return

    def unselect(self, btn):
        for k in self.selected:
            for item in self.songs[k]:
                item.bg_color = []
        self.selected.clear()

    def other_action(self, btn):
        global songs, playlists
        text = self.dialog.content_cls.text
        changed = False
        if len(self.selected) == 0:
            print('Must select song(s) first')
        elif len(text) < 1:
            print('Must input text first')
        elif btn.text == 'Add to Playlist':
            if text not in playlists:
                playlists[text] = list(self.selected)
                changed = True
            else:
                for k in self.selected:
                    if k not in playlists[text]:
                        playlists[text].append(k)
                        changed = True
        elif btn.text == 'Set Artist':
            for k in self.selected:
                if text != songs[k][2]:
                    songs[k][2] = text
                    for item in self.songs[k]:
                        item.secondary_text = text
                    changed = True
        elif btn.text == 'Add Tag':
            for k in self.selected:
                if text not in songs[k][3]:
                    songs[k][3].append(text)
                    changed = True
        elif btn.text == 'Set Title':
            if len(self.selected) > 1:
                print('Cannot set title of more than one song at once')
            else:
                for k in self.selected:
                    if text != songs[k][1]:
                        songs[k][1] = text
                        for item in self.songs[k]:
                            item.text = text
                        changed = True
        if changed:
            self.sort_songs()
            save_user_info()
        self.dialog.content_cls.text = ''
        self.dialog.dismiss()

    def play_playlist(self, btn):
        global current_playlist, current_song, recents, hist_len, temp_playlists
        k = 1 if not temp_playlists else max(temp_playlists.keys()) + 1
        temp_playlists[k] = list(self.selected)
        random.shuffle(temp_playlists[k])
        current_playlist = temp_playlists[k]
        current_song = 0
        recents.insert(0, k)
        recents = recents[:hist_len]
        save_user_info()
        play_song()

    def reverse_order(self, btn):
        self.reverse = not self.reverse
        self.sort_songs()

    def sort_songs(self):
        global songs
        for i in range(4):
            while self.lists[i].children:
                self.lists[i].remove_widget(self.lists[i].children[0])

        # Sort by date
        order = sorted(self.songs.keys(), reverse=not self.reverse)
        for k in order:
            self.lists[0].add_widget(self.songs[k][0])

        # Sort by title
        order = sorted(self.songs.keys(), reverse=self.reverse, key=lambda x: songs[x][1])
        start_letter = ''
        for k in order:
            if songs[k][1][0].upper() != start_letter:
                start_letter = songs[k][1][0].upper()
                self.lists[1].add_widget(OneLineListItem(text=start_letter))
            self.lists[1].add_widget(self.songs[k][1])

        # Sort by artist
        order = sorted(self.songs.keys(), reverse=self.reverse, key=lambda x: songs[x][2])
        start_letter = ''
        for k in order:
            if songs[k][2][0].upper() != start_letter:
                start_letter = songs[k][2][0].upper()
                self.lists[2].add_widget(OneLineListItem(text=start_letter))
            self.lists[2].add_widget(self.songs[k][2])

        # Sort by tags
        tags = dict()
        for k, v in songs.items():
            while len(self.songs[k]) < len(songs[k][3]) + 3:
                self.songs[k].append(TwoLineListItem(text=v[1], secondary_text=v[2], on_release=self.select))
                if k in self.selected:
                    self.songs[k][-1].bg_color = self.songs[k][-1].theme_cls.bg_light
            for i in range(len(songs[k][3])):
                if songs[k][3][i] not in tags:
                    tags[songs[k][3][i]] = list()
                tags[songs[k][3][i]].append(self.songs[k][3+i])
        order = sorted(tags.keys(), reverse=self.reverse)
        for tag in order:
            self.lists[3].add_widget(OneLineListItem(text=tag))
            tags[tag].sort(key=lambda x: x.text)
            for btn in tags[tag]:
                self.lists[3].add_widget(btn)


class SettingsScreen(Screen):
    def __init__(self, nav, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')
        toolbar = MDToolbar(title='Settings', pos_hint={"top": 1})
        toolbar.left_action_items.append(["menu", lambda x: nav.set_state("open")])
        layout.add_widget(toolbar)
        self.file_manager = MDFileManager(exit_manager=self.exit_manager, select_path=self.select_path, ext=['.mp3'])

        global hist_len, folders
        self.items = [OneLineRightIconListItem(text='History length = '+str(hist_len))]
        self.items[0].add_widget(IconRightWidget(icon='minus', on_release=self.change_hist_len))
        self.items.append(OneLineRightIconListItem(text='History length = ' + str(hist_len)))
        self.items[1].add_widget(IconRightWidget(icon='plus', on_release=self.change_hist_len))

        for i in range(len(folders)):
            self.items.append(OneLineRightIconListItem(text=folders[i]))
            self.items[i+2].add_widget(IconRightWidget(icon='minus', on_release=self.remove_folder))

        self.items.append(OneLineRightIconListItem(text='Add new folder'))
        self.items[-1].add_widget(IconRightWidget(icon='plus', on_release=lambda x: self.file_manager.show('/')))

        settings = ScrollView()
        lst = MDList()
        for item in self.items:
            lst.add_widget(item)
        settings.add_widget(lst)
        layout.add_widget(settings)
        layout.add_widget(BottomBar())
        self.add_widget(layout)

    def select_path(self, path):
        self.exit_manager()
        self.add_folder(path.replace('\\', '/'))

    def exit_manager(self, *args):
        self.file_manager.close()

    def remove_folder(self, btn):
        global folders
        idx = -1
        for i in range(len(folders)):
            if btn.parent.parent == self.items[i+2]:
                idx = i
                break
        self.items[idx+2].parent.remove_widget(self.items[idx+2])
        self.items.pop(idx+2)
        folders.pop(idx)
        save_user_info()

    def add_folder(self, path):
        self.items[0].parent.remove_widget(self.items[-1])
        self.items.insert(len(self.items)-1, OneLineRightIconListItem(text=path))
        self.items[-2].add_widget(IconRightWidget(icon='minus', on_release=self.remove_folder))
        self.items[0].parent.add_widget(self.items[-2])
        self.items[0].parent.add_widget(self.items[-1])
        global folders
        folders.append(path)
        save_user_info()

    def change_hist_len(self, btn):
        global hist_len
        if btn.icon == 'plus':
            hist_len += 1
        elif btn.icon == 'minus':
            hist_len -= 1
        self.items[0].text = 'History length = ' + str(hist_len)
        self.items[1].text = 'History length = ' + str(hist_len)
        save_user_info()


class BottomBar(MDBoxLayout):
    def __init__(self, **kwargs):
        super(BottomBar, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, 0.1)
        global song_labels
        label = MDLabel(text='None')
        self.add_widget(label)
        self.add_widget(MDIconButton(icon="rewind", on_release=self.do_action))
        self.add_widget(MDIconButton(icon="play-pause", on_release=self.do_action))
        self.add_widget(MDIconButton(icon="fast-forward", on_release=self.do_action))
        song_labels.append(label)

    def do_action(self, btn):
        global current_playlist, current_song, sound, songs, sound_pos, manual_stop
        if current_playlist:
            if btn.icon == 'rewind':
                if sound.state == 'play':
                    pos = sound.get_pos()
                else:
                    pos = sound_pos
                if pos <= 3:
                    current_song = (current_song - 1 + len(current_playlist)) % len(current_playlist)
                play_song()
            elif btn.icon == 'fast-forward':
                current_song = (current_song + 1) % len(current_playlist)
                play_song()
            elif sound:
                if sound.state == 'play':
                    sound_pos = sound.get_pos()
                    manual_stop = True
                    sound.stop()
                    manual_stop = False
                else:
                    sound.play()
                    print(sound_pos)
                    sound.seek(sound_pos)
"""


class MusicApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        # self.load_user_info()

        # menu_items = MDList()
        # menu_items.add_widget(OneLineListItem(text='Playlists', on_press=lambda x: self.change_screen('playlists')))
        # menu_items.add_widget(OneLineListItem(text='Songs', on_press=lambda x: self.change_screen('songs')))
        # menu_items.add_widget(OneLineListItem(text='Settings', on_press=lambda x: self.change_screen('settings')))
        # scroll = ScrollView()
        # scroll.add_widget(menu_items)
        # self.nav_drawer = MDNavigationDrawer()
        # self.nav_drawer.add_widget(scroll)

        self.sm = ScreenManager()
        # self.playlists_screen = PlaylistsScreen(self.nav_drawer, name='playlists')
        self.songs_screen = SongsScreen(name='songs')
        # settings_screen = SettingsScreen(self.nav_drawer, name='settings')
        # self.sm.add_widget(self.playlists_screen)
        self.sm.add_widget(self.songs_screen)
        # self.sm.add_widget(settings_screen)
        self.sm.current = 'songs'

        # nav = NavigationLayout()
        # nav.add_widget(self.sm)
        # nav.add_widget(self.nav_drawer)
        # screen = Screen()
        # screen.add_widget(nav)

        # return screen
        return self.sm


"""
    def change_screen(self, scr):
        self.nav_drawer.set_state('close')
        self.sm.current = scr
        if scr == 'playlists':
            self.playlists_screen.refresh()
            self.playlists_screen.sm.current = 'playlists'
        elif scr == 'songs':
            self.songs_screen.sort_songs()

    def load_user_info(self):
        global user_file, folders, hist_len, playlists, recents, songs, temp_playlists
        user_file = self.user_data_dir + '\\' + 'music_app_save.txt'
        try:
            with open(user_file, 'r') as f:
                case = 0
                for line in f:
                    if case == 0:
                        folders = line.strip().split(',')
                        case += 1
                    elif case == 1:
                        hist_len = int(line.strip())
                        case += 1
                    elif case == 2:
                        if line.strip() == 'Playlists':
                            case += 1
                        else:
                            parts = line.strip().split(';')
                            songs[int(parts[0])] = [parts[1], parts[2], parts[3], parts[4:]]
                    elif case == 3:
                        if line.strip() == 'Recent Playlists':
                            case += 1
                        else:
                            parts = line.strip().split(';')
                            playlists[parts[0]] = [int(k) for k in parts[1:]]
                    else:
                        parts = line.strip().split(';')
                        if parts[0] == 'p':
                            recents.append(parts[1])
                        else:
                            temp_playlists[case-3] = [int(k) for k in parts[1:]]
                            recents.append(case-3)
                            case += 1
        except FileNotFoundError:
            pass
        for folder in folders:
            load_new_songs(folder)
        save_user_info()
"""


def load_new_songs(folder):
    global songs
    if songs:
        count = max(songs.keys()) + 1
    else:
        count = 1
    existing = {v[0] for v in songs.values()}
    try:
        for file in os.listdir(folder):
            if '.mp3' in file:
                path = folder + '/' + file
                if path not in existing:
                    existing.add(path)
                    songs[count] = [path, file[:-4], 'None', list()]
                    count += 1
    except FileNotFoundError:
        print('Could not find path "' + folder + '"')


def save_user_info():
    global user_file, folders, hist_len, playlists, recents, songs, temp_playlists
    with open(user_file, 'w+') as f:
        f.write(','.join(folders) + '\n' + str(hist_len) + '\n')
        for k, v in songs.items():
            f.write(';'.join([str(k), v[0], v[1], v[2]] + v[3]) + '\n')
        f.write('Playlists\n')
        for k, v in playlists.items():
            f.write(';'.join([k] + [str(val) for val in v]) + '\n')
        f.write('Recent Playlists')
        for k in recents:
            if k in playlists:
                f.write('\np;' + k)
            else:
                f.write('\nt;' + ';'.join([str(s) for s in temp_playlists[k]]))


user_file = ''
folders = list()
playlists = dict()
temp_playlists = dict()
recents = list()
songs = dict()
hist_len = 5
current_playlist = list()
current_song = -1
manual_stop = False
song_labels = list()
sound = None
sound_pos = 0
MusicApp().run()
manual_stop = True
if sound:
    if sound.state == 'play':
        sound.stop()
    sound.unload()
