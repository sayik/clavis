def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_get_notes(client):
    response = client.get("/notes/")

    assert response.status_code == 200
