from cartocrisp.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, _load, translate


def test_all_locales_have_matching_keys():
    reference_keys = set(_load(DEFAULT_LOCALE).keys())
    for locale in SUPPORTED_LOCALES:
        assert set(_load(locale).keys()) == reference_keys, f"{locale} has mismatched keys"


def test_translate_formats_placeholders():
    message = translate("en", "generate.success", path="/tmp/out.svg")
    assert message == "Saved /tmp/out.svg"


def test_translate_falls_back_to_default_for_unknown_locale():
    message = translate("xx", "generate.success", path="/tmp/out.svg")
    assert message == "Saved /tmp/out.svg"
