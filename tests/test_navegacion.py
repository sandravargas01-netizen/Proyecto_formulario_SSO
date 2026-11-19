import unittest
from html.parser import HTMLParser

from flask import render_template, session

from app import create_app


class NavigationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_sidebar = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'nav' and 'sidebar' in attributes.get('class', '').split():
            self.in_sidebar = True
        elif tag == 'a' and self.in_sidebar:
            self.links.append(attributes.get('href'))

    def handle_endtag(self, tag):
        if tag == 'nav':
            self.in_sidebar = False


class SidebarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()

    def sidebar_links(self, role):
        with self.app.test_request_context('/'):
            if role:
                session['usuario'] = 'Prueba'
                session['rol'] = role
            page = render_template('base.html')
        parser = NavigationParser()
        parser.feed(page)
        return parser.links

    def test_admin_links_are_inside_sidebar(self):
        self.assertEqual(self.sidebar_links('admin'), [
            '/empleados/', '/reportes/', '/usuarios/', '/auth/logout',
        ])

    def test_auxiliar_links_are_inside_sidebar(self):
        self.assertEqual(self.sidebar_links('auxiliar'), [
            '/empleados/', '/empleados/crear', '/reportes/', '/auth/logout',
        ])

    def test_logged_out_has_no_sidebar(self):
        self.assertEqual(self.sidebar_links(None), [])


if __name__ == '__main__':
    unittest.main()
