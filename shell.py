import logging
logging.basicConfig(level=logging.DEBUG)

from pathlib import Path

from lxml import etree
from rimworld.xml import load_xml
from rimworld.world import World

try:
    from pygments import highlight
    from pygments.lexers import XmlLexer
    from pygments.formatters import TerminalFormatter
    lexer = XmlLexer()
    formatter = TerminalFormatter()

    def _format(value: str) -> str:
        return highlight(value, lexer, formatter)

except ImportError:
    def _format(value: str) -> str:
        return value


PATH = 'data.xml'


def load(path: Path|str=PATH):
    global xml
    if not isinstance(path, Path):
        path = Path(path)
    if path.exists():
        xml = load_xml(path)       
    else:
        reload(path)


def reload(path: Path|str=PATH):
    global xml
    if not isinstance(path, Path):
        path = Path(path)
    world = World.from_settings(add_metadata=True)
    with path.open('wb') as f:
        world.xml.write_c14n(f)
    xml = world.xml



def xpath(path: str, xml=xml):
    results = xml.xpath(path)
    print(results)
    if not hasattr(results, '__iter__'):
        print(results)
    for node in results:  # type: ignore
        if isinstance(node, etree._Element):
            string_repr = etree.tostring(node, pretty_print=True, encoding=str)
            print(_format(string_repr))
        else:
            print(node)


