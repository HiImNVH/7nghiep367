import pytest
from visign_ai import cpu_runtime


def test_performance_policy_is_limited_to_windows(monkeypatch):
    monkeypatch.setattr(cpu_runtime.sys, "platform", "linux")
    assert cpu_runtime.configure_cpu_runtime() == {
        "mode": "system-default",
        "applied": False,
    }


def test_windows_performance_mode_can_be_disabled(monkeypatch):
    monkeypatch.setenv("VISIGN_CPU_PERFORMANCE_MODE", "0")
    monkeypatch.setattr(
        cpu_runtime,
        "_set_windows_performance_mode",
        lambda: pytest.fail("Policy must not be changed"),
    )
    assert cpu_runtime.configure_cpu_runtime()["applied"] is False


def test_windows_policy_failure_is_reported_and_inference_can_continue(monkeypatch):
    monkeypatch.setattr(cpu_runtime.sys, "platform", "win32")
    monkeypatch.setenv("VISIGN_CPU_PERFORMANCE_MODE", "1")

    def unsupported():
        raise OSError("unsupported")

    monkeypatch.setattr(cpu_runtime, "_set_windows_performance_mode", unsupported)
    result = cpu_runtime.configure_cpu_runtime()
    assert result["applied"] is False and result["error"] == "OSError"


def test_successful_windows_policy_is_visible_in_report(monkeypatch):
    monkeypatch.setattr(cpu_runtime.sys, "platform", "win32")
    monkeypatch.setenv("VISIGN_CPU_PERFORMANCE_MODE", "1")
    monkeypatch.setattr(cpu_runtime, "_set_windows_performance_mode", lambda: None)
    assert cpu_runtime.configure_cpu_runtime() == {
        "mode": "windows-high-qos",
        "applied": True,
    }
