import sys
sys.path.insert(0, 'pipeline/extractors')

def test_import():
    import clinicaltrials
    assert hasattr(clinicaltrials, 'fetch_trials')

def test_fetch_trials_signature():
    from clinicaltrials import fetch_trials
    import inspect
    params = inspect.signature(fetch_trials).parameters
    assert 'condition' in params
    assert 'max_trials' in params

def test_load_raw_exists():
    from pathlib import Path
    assert Path('pipeline/extractors/clinicaltrials.py').exists()
