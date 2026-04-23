from firedm import update


def test_self_update_supported_for_source_installs():
    assert update.self_update_supported(frozen=False, is_appimage=False) is True


def test_self_update_disabled_for_packaged_windows_builds():
    assert update.self_update_supported(frozen=True, is_appimage=False) is False
    assert 'release' in update.get_update_instructions(frozen=True, is_appimage=False).lower()


def test_self_update_supported_for_appimage():
    assert update.self_update_supported(frozen=True, is_appimage=True) is True
