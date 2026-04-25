import subprocess


def test_phase1_readiness_script_runs():
    proc = subprocess.run(['python', 'scripts_check_phase1_readiness.py'], capture_output=True, text=True)
    assert proc.returncode == 0
    assert 'phase1_tests_exist: PASS' in proc.stdout
