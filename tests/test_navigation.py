import ast
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('navigation_test',ROOT/'scripts/templates/navigation.py')
nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)

class NavigationTest(unittest.TestCase):
    def test_admin_is_separate_and_settings_do_not_expose_admin_operations(self):
        for language in ['zh','en']:
            for page in nav.PAGES:
                title,rows=nav.page_model(page,language,True)
                targets=[target for row in rows for _,target in row]
                self.assertEqual('nav|users' in targets,page=='home')
                self.assertEqual(len(targets),len(set(targets)))
                self.assertFalse(any('yuanbao' in value for value in targets))
            self.assertNotIn('nav|users',[v for row in nav.page_model('home',language,False)[1] for _,v in row])

    def test_all_page_targets_exist_and_command_targets_have_handlers(self):
        commands=ast.parse((ROOT/'vendor/tg-ytdlp-bot/COMMANDS/settings_cmd.py').read_text())
        callback=next(n for n in commands.body if isinstance(n,ast.FunctionDef) and n.name=='settings_cmd_callback')
        handled={n.comparators[0].value for n in ast.walk(callback) if isinstance(n,ast.Compare) and isinstance(n.left,ast.Name) and n.left.id=='data' and len(n.comparators)==1 and isinstance(n.comparators[0],ast.Constant)}
        for page in nav.PAGES:
            for row in nav.page_model(page,admin=True)[1]:
                for label,target in row:
                    if target.startswith('nav|'):
                        self.assertIn(target.split('|')[1],set(nav.PAGES)|{'cookies','users','close'})
                    elif target.startswith('settings__cmd__'):
                        self.assertIn(target.split('__')[-1],handled)

    def test_generated_settings_no_longer_render_legacy_cookie_buttons(self):
        tree=ast.parse((ROOT/'vendor/tg-ytdlp-bot/COMMANDS/settings_cmd.py').read_text())
        for name in ['settings_command','settings_menu_callback']:
            node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            body=ast.unparse(node)
            self.assertNotIn('yuanbao_cookie',body)
            self.assertNotIn('cookies_from_browser',body)
            self.assertIn('HELPERS.navigation',body)

    def test_legacy_cookie_buttons_all_redirect_to_unified_import(self):
        self.assertEqual(nav.LEGACY_COOKIES,{'yuanbao_cookie','download_cookie','cookies_from_browser','check_cookie','save_as_cookie'})
