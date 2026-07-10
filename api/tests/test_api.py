from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, 'api')

def test_health():
    os.environ['DATABASE_URL'] = 'postgresql://trialscope:test@localhost:5432/trialscope_test'
    from main import app
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
