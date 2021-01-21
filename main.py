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
                        case += 1
                    elif case == 1:
                        self.hist_len = int(line.strip())
                        case += 1
                    elif case == 2:
                        if line.strip() == 'Playlists':
                            case += 1
                        else:
                            parts = line.strip().split(';')
                            self.songs[int(parts[0])] = [parts[1], parts[2], parts[3], parts[5:], float(parts[4])]
                    elif case == 3:
                        if line.strip() == 'Recent Playlists':
                            case += 1
                        else:
                            parts = line.strip().split(';')
                            self.playlists[parts[0]] = [int(k) for k in parts[1:]]
                    else:
                        parts = line.strip().split(';')
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
                if '.mp3' in file:
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
                f.write(';'.join([str(k), v[0], v[1], v[2], str(v[4])] + v[3]) + '\n')
            f.write('Playlists\n')
            for k, v in self.playlists.items():
                f.write(';'.join([k] + [str(val) for val in v]) + '\n')
            f.write('Recent Playlists')
            for k in self.recent:
                if k in self.playlists:
                    f.write('\np;' + k)
                else:
                    f.write('\nt;' + ';'.join([str(s) for s in self.temp_playlists[k]]))


class MusicApp(MDApp):
    dialog = None
    items = None
    song_label = None
    user_info = None

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.user_info = UserInfo(self.user_data_dir + '\\' + 'music_app_save.txt')

        menu_items = MDList()
        menu_items.add_widget(OneLineListItem(text='Playlists', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Songs (Title)', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Songs (Artist)', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Songs (Date)', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Songs (Tags)', on_press=self.menu_action))
        menu_items.add_widget(OneLineListItem(text='Settings', on_press=self.menu_action))
        nav_scroll = ScrollView()
        nav_scroll.add_widget(menu_items)
        nav_drawer = MDNavigationDrawer()
        nav_drawer.add_widget(nav_scroll)

        layout = MDBoxLayout(orientation='vertical')
        self.dialog = MDDialog(
            type="custom",
            content_cls=MDTextField(),
            buttons=[MDRaisedButton(text='Add to Playlist', on_release=self.dialog_action),
                     MDRaisedButton(text='Set Title', on_release=self.dialog_action),
                     MDRaisedButton(text='Set Artist', on_release=self.dialog_action),
                     MDRaisedButton(text='Add Tag', on_release=self.dialog_action)])

        toolbar = MDToolbar(title='Music App', pos_hint={'top': 1})
        toolbar.left_action_items.append(['menu', lambda x: nav_drawer.set_state('open')])
        toolbar.right_action_items.append(['cancel', self.toolbar_action])
        toolbar.right_action_items.append(['arrow-up-down', self.toolbar_action])
        toolbar.right_action_items.append(['play', self.toolbar_action])
        toolbar.right_action_items.append(['dots-vertical', lambda x: self.dialog.open()])
        layout.add_widget(toolbar)

        self.items = MDList()
        scroll = ScrollView()
        scroll.add_widget(self.items)
        layout.add_widget(scroll)
        # TODO: Add items to list
        self.items.add_widget(OneLineListItem(text='Line 1'))
        self.items.add_widget(OneLineListItem(text='Line 2'))

        bottom_bar = MDBoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.song_label = MDLabel(text='None')
        bottom_bar.add_widget(self.song_label)
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
        nav.add_widget(nav_drawer)
        return nav

    def menu_action(self, btn):
        pass

    def toolbar_action(self, btn):
        pass

    def bottom_action(self, btn):
        pass

    def dialog_action(self, btn):
        pass


MusicApp().run()
