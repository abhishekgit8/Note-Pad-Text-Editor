import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_with_empty_reminder():
    payload = {"title":"t1","content":"c","priority":1,"status":"active","reminder_time":""}
    r = client.post('/notes', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['reminder_time'] is None
    assert data['title'] == 't1'


def test_patch_status():
    # create
    payload = {"title":"t2","content":"c2","priority":1,"status":"active","reminder_time":""}
    r = client.post('/notes', json=payload)
    assert r.status_code == 200
    nid = r.json()['id']

    # patch
    r2 = client.patch(f'/notes/{nid}', json={'status':'finished'})
    assert r2.status_code == 200
    assert r2.json()['status'] == 'finished'


def test_delete_removes():
    payload = {"title":"t3","content":"c3","priority":1,"status":"active","reminder_time":""}
    r = client.post('/notes', json=payload)
    assert r.status_code == 200
    nid = r.json()['id']

    r2 = client.delete(f'/notes/{nid}')
    assert r2.status_code == 200

    r3 = client.get('/notes')
    ids = [n['id'] for n in r3.json()]
    assert nid not in ids


def test_websocket_receives_create():
    with client.websocket_connect('/ws') as ws:
        # create a note
        payload = {"title":"ws","content":"ws","priority":1,"status":"active","reminder_time":""}
        r = client.post('/notes', json=payload)
        assert r.status_code == 200

        # receive messages until we see the create event (there may be an initial sync message)
        while True:
            msg = ws.receive_json()
            if msg.get('action') == 'create':
                assert msg['note']['title'] == 'ws'
                break
