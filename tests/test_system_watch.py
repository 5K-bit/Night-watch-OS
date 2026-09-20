from __future__ import annotations

from types import SimpleNamespace

from nightwatch import system_watch


def test_network_up_does_not_require_public_internet(monkeypatch) -> None:
    monkeypatch.setattr(
        system_watch.psutil,
        "net_if_stats",
        lambda: {"eth0": SimpleNamespace(isup=True)},
    )
    monkeypatch.setattr(
        system_watch.psutil,
        "net_if_addrs",
        lambda: {
            "eth0": [
                SimpleNamespace(family=system_watch.socket.AF_INET, address="192.168.1.20")
            ]
        },
    )

    assert system_watch._network_up() is True


def test_loopback_only_is_not_network_up(monkeypatch) -> None:
    monkeypatch.setattr(
        system_watch.psutil,
        "net_if_stats",
        lambda: {"lo": SimpleNamespace(isup=True)},
    )
    monkeypatch.setattr(
        system_watch.psutil,
        "net_if_addrs",
        lambda: {
            "lo": [SimpleNamespace(family=system_watch.socket.AF_INET, address="127.0.0.1")]
        },
    )

    assert system_watch._network_up() is False
