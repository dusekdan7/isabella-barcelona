from decimal import Decimal, ROUND_HALF_UP
from django import template

register = template.Library()

CURRENCIES = {
    'EUR': {'rate': Decimal('1'),     'symbol': '€',   'after': False, 'dec': 2},
    'USD': {'rate': Decimal('1.08'),  'symbol': '$',   'after': False, 'dec': 2},
    'GBP': {'rate': Decimal('0.85'),  'symbol': '£',   'after': False, 'dec': 2},
    'CHF': {'rate': Decimal('0.96'),  'symbol': 'Fr.', 'after': False, 'dec': 2},
    'PLN': {'rate': Decimal('4.28'),  'symbol': 'zł',  'after': True,  'dec': 2},
    'CZK': {'rate': Decimal('25.2'),  'symbol': 'Kč',  'after': True,  'dec': 0},
    'SEK': {'rate': Decimal('11.4'),  'symbol': 'kr',  'after': True,  'dec': 0},
    'NOK': {'rate': Decimal('11.7'),  'symbol': 'kr',  'after': True,  'dec': 0},
    'DKK': {'rate': Decimal('7.46'),  'symbol': 'kr',  'after': True,  'dec': 0},
    'AUD': {'rate': Decimal('1.65'),  'symbol': 'A$',  'after': False, 'dec': 2},
    'CAD': {'rate': Decimal('1.47'),  'symbol': 'C$',  'after': False, 'dec': 2},
    'JPY': {'rate': Decimal('162'),   'symbol': '¥',   'after': False, 'dec': 0},
}

_LANG_FLAGS = {'es': '🇪🇸', 'en': '🇬🇧', 'fr': '🇫🇷', 'de': '🇩🇪', 'it': '🇮🇹', 'cs': '🇨🇿'}


@register.filter
def product_name(product, lang):
    if lang in ('en', 'fr', 'de', 'it', 'cs'):
        return getattr(product, 'name_en', '') or product.name_es
    return product.name_es


@register.filter
def price_display(price, currency):
    if price is None:
        return ''
    price = Decimal(str(price))
    cfg = CURRENCIES.get(currency) or CURRENCIES['EUR']
    converted = price * cfg['rate']
    if cfg['dec'] == 0:
        amount = str(int(converted.quantize(Decimal('1'), rounding=ROUND_HALF_UP)))
    else:
        amount = str(converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    if cfg['after']:
        return f"{amount} {cfg['symbol']}"
    return f"{cfg['symbol']}{amount}"


@register.filter
def lang_flag(lang):
    return _LANG_FLAGS.get(lang, '🌐')
